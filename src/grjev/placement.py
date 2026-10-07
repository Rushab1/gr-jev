"""The orders of an example's tool list: the released order, and the correct tools placed at fixed positions."""

import random
from collections.abc import Iterable
from fractions import Fraction
from math import ceil

from grjev.constants import (
    OWN_LIST,
    PLACEMENT_MAX_CORRECT,
    PLACEMENT_MIN_TOOLS,
    PLACEMENTS,
    RELEASED_ORDER,
    SEPARATED_PLACEMENTS,
)
from grjev.examples import Example, Option


def start_positions(tools: int, block: int = 1) -> dict[str, int]:
    """Return, for each placement, the position counted from 1 where a block of correct tools starts."""
    free = tools - block
    # 1 + share x free, rounded to the nearest position, with a half rounded down.
    return {name: 1 + ceil(share * free - Fraction(1, 2)) for name, share in PLACEMENTS.items()}


def place(distractors: list[Option], correct: dict[int, Option]) -> list[Option]:
    """Return the list with each correct tool at its position, counted from 1, and the distractors in their order."""
    rest = iter(distractors)
    positions = range(1, len(distractors) + len(correct) + 1)
    return [correct[position] if position in correct else next(rest) for position in positions]


def one_tool_orders(distractors: list[Option], correct: Option) -> dict[str, list[Option]]:
    """Return the list with the correct tool at each placement."""
    starts = start_positions(len(distractors) + 1)
    return {name: place(distractors, {start: correct}) for name, start in starts.items()}


def two_tool_orders(distractors: list[Option], first: Option, second: Option) -> dict[str, list[Option]]:
    """Return the list with the two correct tools adjacent at each placement, then with distractors between them."""
    tools = len(distractors) + 2
    adjacent = {
        f"adjacent_{name}": place(distractors, {start: first, start + 1: second})
        for name, start in start_positions(tools, block=2).items()
    }
    single = start_positions(tools)
    separated = {
        f"separated_{early}_{late}": place(distractors, {single[early]: first, single[late]: second})
        for early, late in SEPARATED_PLACEMENTS
    }
    return adjacent | separated


def orders_of(example: Example, seed: int) -> dict[str, list[Option]]:
    """Return every order of the example's tool list that is sent, by name. The released order comes first."""
    orders = {RELEASED_ORDER: example.options}
    labels = example.labels or []
    correct = [option for option in example.options if option.name in labels]
    if not correct:
        return orders
    if len(correct) > PLACEMENT_MAX_CORRECT or len(example.options) < PLACEMENT_MIN_TOOLS:
        raise ValueError(f"No placement rule for {example.id}: {len(correct)} correct of {len(example.options)} tools")
    # Seeding with text gives the same order on every machine. The distractors keep one order in every placement.
    rng = random.Random(f"{seed}/{example.id}")
    distractors = [option for option in example.options if option.name not in labels]
    rng.shuffle(distractors)
    rng.shuffle(correct)
    if len(correct) == 1:
        return orders | one_tool_orders(distractors, correct[0])
    return orders | two_tool_orders(distractors, correct[0], correct[1])


def padded_order(example: Example, tools: list[Option], size: int, seed: int) -> list[Option]:
    """Return the example's tools in a seeded order, with random other tools of the dataset added up to `size` tools."""
    rng = random.Random(f"{seed}/{example.id}")
    listed = {option.name for option in example.options}
    others = [tool for tool in tools if tool.name not in listed]
    order = example.options + rng.sample(others, max(0, size - len(example.options)))
    rng.shuffle(order)
    return order


def reworded_tool(example: Example, seed: int) -> str:
    """Return the name of the correct tool of the example that is reworded, chosen with the seed."""
    return random.Random(f"{seed}/{example.id}/reworded").choice(example.labels or [])


def reworded_order(order: list[Option], original: str, rewordings: list[Option]) -> list[Option]:
    """Return the tool list with the tool named `original` taken out and its rewordings in its place."""
    return [tool for listed in order for tool in (rewordings if listed.name == original else [listed])]


def grown_orders(
    example: Example, tools: list[Option], size: int, lengths: Iterable[int], seed: int
) -> dict[str, list[Option]]:
    """Return the example's padded list, and that list grown to each length with random other tools, by name.

    Each grown list is in a seeded order of its own and contains every shorter list of the example.
    """
    own = padded_order(example, tools, size, seed)
    listed = {tool.name for tool in own}
    others = [tool for tool in tools if tool.name not in listed]
    rng = random.Random(f"{seed}/{example.id}/grown")
    rng.shuffle(others)
    orders = {OWN_LIST: own}
    for length in lengths:
        if not len(own) <= length <= len(tools):
            raise ValueError(f"{example.id}: a list of {len(own)} tools cannot grow to {length} of {len(tools)} tools")
        orders[str(length)] = own + others[: length - len(own)]
        rng.shuffle(orders[str(length)])
    return orders


def length_orders(example: Example, tools: list[Option], lengths: Iterable[int], seed: int) -> dict[str, list[Option]]:
    """Return, for each list length and placement, the example's one correct tool among other tools of the dataset.

    The other tools are shuffled once. A list of n tools holds the first n - 1 of them, so it contains each shorter one.
    """
    (label,) = example.labels or []
    correct = next(tool for tool in tools if tool.name == label)
    others = [tool for tool in tools if tool.name != label]
    random.Random(f"{seed}/{example.id}").shuffle(others)
    orders = {}
    for length in lengths:
        if length > len(tools):
            raise ValueError(f"A list of {length} tools needs more than the {len(tools)} tools of the dataset")
        for name, start in start_positions(length).items():
            orders[f"{length}_{name}"] = place(others[: length - 1], {start: correct})
    return orders
