"""Where the correct parameter values of BFCL's single-turn examples come from.

A model that only selects can produce a value that is written in the query or in the function's definition, or that
may be left out. It cannot produce a value that has to be rewritten.
"""

import re
from collections import Counter
from typing import Any

from grjev.constants import (
    BFCL_ANY_CALL_FILES,
    BFCL_BOOLEAN_TYPES,
    BFCL_NO_CALL_FILES,
    BFCL_SINGLE_TURN_FILES,
    BFCL_VALUE_SOURCES,
)
from grjev.examples import Example


def number_in_text(text: str, number: float) -> bool:
    """Say whether the text holds the number in digits, on its own and not as part of a longer number."""
    forms = {str(number)}
    if isinstance(number, float):
        forms.add(f"{number:f}".rstrip("0").rstrip("."))
    plain = text.replace(",", "")
    return any(re.search(rf"(?<![\d.]){re.escape(form)}(?!\.?\d)", plain) for form in forms)


def nested_in_text(text: str, accepted: Any) -> bool:
    """Say whether one key of a nested parameter has an accepted value that is in the text or may be left out."""
    alternatives = accepted if isinstance(accepted, list) else [accepted]
    return any(alternative == "" or value_in_text(text, alternative) for alternative in alternatives)


def value_in_text(text: str, value: Any) -> bool:
    """Say whether a value can be read off the text.

    Text matches in any case and a number in digits. A list needs every element, and a nested parameter every key.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return number_in_text(text, value)
    if isinstance(value, str):
        return bool(value.strip()) and value.lower() in text.lower()
    if isinstance(value, list):
        return bool(value) and all(value_in_text(text, element) for element in value)
    if isinstance(value, dict):
        return bool(value) and all(nested_in_text(text, accepted) for accepted in value.values())
    return False


def descriptions_in(schema: Any) -> list[str]:
    """Return every description inside a parameter's schema, those of its nested parameters included."""
    if isinstance(schema, dict):
        own = [schema["description"]] if isinstance(schema.get("description"), str) else []
        return own + [text for value in schema.values() for text in descriptions_in(value)]
    if isinstance(schema, list):
        return [text for value in schema for text in descriptions_in(value)]
    return []


def is_default(schema: dict[str, Any], value: Any) -> bool:
    """Say whether the value is the default that the parameter's schema gives, with the same type."""
    return "default" in schema and type(value) is type(schema["default"]) and value == schema["default"]


def value_source(query: str, accepted: list[Any], schema: dict[str, Any], description: str) -> str:
    """Return where a selecting model could take a parameter's value from: one of BFCL_VALUE_SOURCES.

    `accepted` is the ground truth's list of accepted values, where "" means the parameter may be left out.
    `schema` is the parameter's entry in the function definition and `description` the function's description.
    """
    given = [value for value in accepted if value != ""]
    if any(value_in_text(query, value) for value in given):
        return "query"
    if str(schema.get("type", "")).lower() in BFCL_BOOLEAN_TYPES or any(isinstance(value, bool) for value in given):
        return "boolean"
    if any(value in schema.get("enum", []) for value in given if isinstance(value, str | int | float)):
        return "schema"
    if len(given) < len(accepted):
        return "left_out"
    written = " ".join([description, *descriptions_in(schema)])
    if any(value_in_text(written, value) or is_default(schema, value) for value in given):
        return "description"
    return "other"


def example_sources(example: Example) -> list[str]:
    """Return the source of every parameter value in the ground truth of a single-turn example."""
    functions = {function["name"]: function for function in example.raw["function"]}
    return [
        value_source(
            example.query,
            accepted,
            functions[name]["parameters"].get("properties", {}).get(parameter, {}),
            functions[name]["description"],
        )
        for call in example.raw["ground_truth"]
        for name, parameters in call.items()
        for parameter, accepted in parameters.items()
    ]


def value_stats(dataset: dict[str, list[Example]]) -> dict[str, Any]:
    """Count the parameter values by source in each single-turn file that has a ground truth.

    An example is selectable when none of its values has the source "other".
    """
    files = {}
    for name in BFCL_SINGLE_TURN_FILES:
        if name in BFCL_NO_CALL_FILES + BFCL_ANY_CALL_FILES:
            continue
        sources = [example_sources(example) for example in dataset[name]]
        counts = Counter(source for one in sources for source in one)
        files[name] = {
            "examples": len(sources),
            "selectable": sum(1 for one in sources if "other" not in one),
            "values": {source: counts[source] for source in BFCL_VALUE_SOURCES},
        }
    return {"sources": BFCL_VALUE_SOURCES, "files": files}
