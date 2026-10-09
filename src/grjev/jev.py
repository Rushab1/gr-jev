"""Client for Jev, TypeSafe AI's decision model, and for the decision models that Vercel AI Gateway serves.

Every response is saved under the request's hash and a run number.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from pydantic import BaseModel, Field

from grjev.constants import (
    GATEWAY_CACHE_DIR,
    GATEWAY_KEY_ENV,
    GATEWAY_MODELS,
    GATEWAY_URL,
    HTTP_TIMEOUT_SECONDS,
    JEV_BACKOFF_SECONDS,
    JEV_CACHE_DIR,
    JEV_CALL_LIMIT,
    JEV_KEY_ENV,
    JEV_MAX_ATTEMPTS,
    JEV_MAX_OPTIONS,
    JEV_MODEL,
    JEV_RETRY_STATUSES,
    JEV_URL,
    ONE_LIST_MODELS,
    REJECTED_STATUSES,
)
from grjev.store import load_or_compute, run_path

logger = logging.getLogger(__name__)


class ChoiceQuestion(BaseModel):
    """Pick one option. `criteria` maps each option to its description, in the order sent to Jev."""

    type: Literal["choice"] = "choice"
    instructions: str
    criteria: dict[str, str | None] = Field(max_length=JEV_MAX_OPTIONS)


class NoulQuestion(BaseModel):
    """A yes or no question."""

    type: Literal["noul"] = "noul"
    instructions: str


class JevRequest(BaseModel):
    """One request: a state and the named questions asked about it."""

    state: str
    model: str = JEV_MODEL
    questions: dict[str, Annotated[ChoiceQuestion | NoulQuestion, Field(discriminator="type")]]


class ChoiceAnswer(BaseModel):
    """The selected option, with the probability of every option."""

    type: Literal["choice"]
    choice: str
    probabilities: dict[str, float]
    confidence: float


class NoulAnswer(BaseModel):
    """The probability that the answer is yes."""

    type: Literal["noul"]
    noul: float


class RefusalAnswer(BaseModel):
    """The model declined to answer the question. GPT-6 Luna Decisions returns it."""

    type: Literal["refusal"]


class Usage(BaseModel):
    """Token counts reported by the API."""

    input_tokens: int
    output_tokens: int


class JevResponse(BaseModel):
    """One response: the model that answered, an answer for each question, and the token usage."""

    model: str
    answers: dict[str, Annotated[ChoiceAnswer | NoulAnswer | RefusalAnswer, Field(discriminator="type")]]
    usage: Usage


def request_body(request: JevRequest) -> bytes:
    """Return the exact bytes sent to Jev. Option order is kept, because it is part of the request."""
    return json.dumps(request.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")).encode()


def api_key(model: str = JEV_MODEL) -> str:
    """Read the key of the API that serves the model from the environment."""
    name = GATEWAY_KEY_ENV if model in GATEWAY_MODELS else JEV_KEY_ENV
    key = os.environ.get(name)
    if not key:
        raise RuntimeError(f"{name} is not set")
    return key


def post(body: bytes, model: str = JEV_MODEL) -> dict[str, Any]:
    """Send one request to the model's API, retrying with backoff while the server is overloaded or rate limiting.

    A model that takes one tool list per request can reject the list. The rejection is returned and not raised.
    """
    url = GATEWAY_URL if model in GATEWAY_MODELS else JEV_URL
    headers = {"Authorization": f"Bearer {api_key(model)}", "Content-Type": "application/json"}
    for attempt in range(1, JEV_MAX_ATTEMPTS + 1):
        response = httpx.post(url, content=body, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        if response.status_code not in JEV_RETRY_STATUSES or attempt == JEV_MAX_ATTEMPTS:
            break
        logger.warning("%s returned %d on attempt %d of %d", model, response.status_code, attempt, JEV_MAX_ATTEMPTS)
        time.sleep(JEV_BACKOFF_SECONDS * 2 ** (attempt - 1))
    if model in ONE_LIST_MODELS and response.status_code in REJECTED_STATUSES:
        return {"rejected": response.status_code, "error": response.text}
    if response.status_code != httpx.codes.OK:
        raise RuntimeError(f"{model} returned {response.status_code}: {response.text}")
    return response.json()


def ask(request: JevRequest, run: int = 1) -> JevResponse | None:
    """Return the model's response for this request and run number, or None when the model rejected the request.

    The API is called only if that run is not saved.
    """
    body = request_body(request)

    def call() -> dict[str, Any]:
        response = post(body, request.model)
        # A response that does not validate is not saved, so the next call with this request asks the model again.
        if "rejected" not in response:
            JevResponse.model_validate(response)
        return {"request": json.loads(body), "run": run, "response": response}

    record = load_or_compute(response_path(request, run), call)
    return None if "rejected" in record["response"] else JevResponse.model_validate(record["response"])


def response_path(request: JevRequest, run: int = 1) -> Path:
    """Return where the response to this request and run number is saved. Gateway models have their own folder."""
    root = GATEWAY_CACHE_DIR if request.model in GATEWAY_MODELS else JEV_CACHE_DIR
    return run_path(root / request.model, request_body(request), run)


def calls_saved() -> int:
    """Return the number of saved Jev responses. Each call that returned an answer saved one."""
    return sum(1 for _ in JEV_CACHE_DIR.rglob("run-*.json"))


def check_call_limit(new_calls: int, model: str = JEV_MODEL) -> None:
    """Raise if this many new Jev calls would take the number of saved responses past the limit.

    Calls to a gateway model do not count.
    """
    if model in GATEWAY_MODELS:
        return
    saved = calls_saved()
    if saved + new_calls > JEV_CALL_LIMIT:
        raise RuntimeError(f"{new_calls} new Jev calls and {saved} saved ones pass the limit of {JEV_CALL_LIMIT}")
