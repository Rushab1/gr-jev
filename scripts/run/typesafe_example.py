"""Send the example request of TypeSafe's documentation of the Choice question, and print the documented answer
next to the answer of the model.

The request is in src/grjev/stimuli/tickets.json. The response is saved like every response, so a second run of the
command calls nothing. A call to Jev counts towards JEV_CALL_LIMIT.
"""

import argparse

from dotenv import load_dotenv

from grjev.constants import GATEWAY_MODELS, JEV_MODEL, TICKETS_FILE
from grjev.jev import ChoiceAnswer, JevRequest, ask, check_call_limit, response_path
from grjev.tickets import read_stimuli


def parse_args() -> argparse.Namespace:
    """Read the model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=JEV_MODEL, choices=[JEV_MODEL, *GATEWAY_MODELS])
    return parser.parse_args()


def main() -> None:
    """Ask the model TypeSafe's example request and print each answer of a choice, with the documented team answer."""
    args = parse_args()
    load_dotenv()
    stimuli = read_stimuli(TICKETS_FILE)
    request = JevRequest.model_validate(stimuli.typesafe_request | {"model": args.model})
    check_call_limit(not response_path(request).exists(), args.model)
    response = ask(request)
    if response is None:
        raise RuntimeError(f"{args.model} rejected the request")
    print(f"state: {request.state}")
    print(f"documented department: {stimuli.typesafe_documented_answer['department']}")
    for name, answer in response.answers.items():
        if isinstance(answer, ChoiceAnswer):
            print(f"{args.model} {name}: {answer.choice}, confidence {answer.confidence}, {answer.probabilities}")
        else:
            print(f"{args.model} {name}: {answer.type}")
    print(f"input tokens: {response.usage.input_tokens}, saved under {response_path(request).parent.name}")


if __name__ == "__main__":
    main()
