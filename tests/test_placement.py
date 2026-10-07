"""Tests for grjev.placement."""

import pytest

from grjev.constants import OWN_LIST, PLACEMENTS, RELEASED_ORDER
from grjev.examples import Example, Option
from grjev.placement import (
    grown_orders,
    length_orders,
    orders_of,
    padded_order,
    reworded_tool,
    start_positions,
)

SEED = 7


def example(tools: int, labels: list[str]) -> Example:
    options = [Option(name=f"tool_{number}", description=f"Does thing {number}.") for number in range(1, tools + 1)]
    return Example(id="set/file/0", query="Do the thing.", options=options, labels=labels, raw={})


def names(tools: list[Option]) -> list[str]:
    return [tool.name for tool in tools]


def positions(tools: list[Option], labels: list[str]) -> list[int]:
    """The positions, counted from 1, of the labelled tools in the list."""
    return [position for position, tool in enumerate(tools, start=1) if tool.name in labels]


@pytest.mark.parametrize(
    ("tools", "one_tool", "two_tools"),
    [
        (5, [1, 2, 3, 4, 5], [1, 2, 2, 3, 4]),
        (10, [1, 3, 5, 8, 10], [1, 3, 5, 7, 9]),
        (15, [1, 4, 8, 11, 15], [1, 4, 7, 11, 14]),
        (20, [1, 6, 10, 15, 20], [1, 5, 10, 14, 19]),
        (50, [1, 13, 25, 38, 50], [1, 13, 25, 37, 49]),
        (100, [1, 26, 50, 75, 100], [1, 25, 50, 74, 99]),
        (199, [1, 50, 100, 149, 199], [1, 50, 99, 149, 198]),
    ],
)
def test_start_positions_are_first_quarter_middle_three_quarters_and_last(
    tools: int, one_tool: list[int], two_tools: list[int]
) -> None:
    assert list(start_positions(tools)) == list(PLACEMENTS)
    assert list(start_positions(tools).values()) == one_tool
    assert list(start_positions(tools, block=2).values()) == two_tools


def test_one_correct_tool_is_placed_at_five_positions_among_the_same_distractors() -> None:
    labels = ["tool_4"]
    released, *placed = orders_of(example(10, labels), SEED).items()
    assert released == (RELEASED_ORDER, example(10, labels).options)
    assert [name for name, _ in placed] == list(PLACEMENTS)
    assert [positions(tools, labels) for _, tools in placed] == [[1], [3], [5], [8], [10]]
    distractor_orders = {tuple(name for name in names(tools) if name not in labels) for _, tools in placed}
    assert len(distractor_orders) == 1
    assert all(sorted(names(tools)) == sorted(names(example(10, labels).options)) for _, tools in placed)


def test_two_correct_tools_are_placed_adjacent_and_then_separated() -> None:
    labels = ["tool_7", "tool_8"]
    orders = orders_of(example(10, labels), SEED)
    assert list(orders) == [
        RELEASED_ORDER,
        "adjacent_first",
        "adjacent_quarter",
        "adjacent_middle",
        "adjacent_three_quarters",
        "adjacent_last",
        "separated_first_last",
        "separated_first_middle",
        "separated_middle_last",
    ]
    placed = [tools for name, tools in orders.items() if name != RELEASED_ORDER]
    assert [positions(tools, labels) for tools in placed] == [
        [1, 2],
        [3, 4],
        [5, 6],
        [7, 8],
        [9, 10],
        [1, 10],
        [1, 5],
        [5, 10],
    ]
    # The same correct tool comes first in every order, and the distractors keep one order.
    assert len({next(name for name in names(tools) if name in labels) for tools in placed}) == 1
    assert len({tuple(name for name in names(tools) if name not in labels) for tools in placed}) == 1


def test_a_list_without_a_correct_tool_keeps_only_the_released_order() -> None:
    assert list(orders_of(example(10, []), SEED)) == [RELEASED_ORDER]


def test_orders_depend_only_on_the_seed_and_the_example() -> None:
    labels = ["tool_4"]
    assert orders_of(example(10, labels), SEED) == orders_of(example(10, labels), SEED)
    assert orders_of(example(10, labels), SEED)["first"] != orders_of(example(10, labels), SEED + 1)["first"]
    other = example(10, labels).model_copy(update={"id": "set/file/1"})
    assert names(orders_of(example(10, labels), SEED)["first"]) != names(orders_of(other, SEED)["first"])


def test_three_correct_tools_or_a_list_under_five_tools_have_no_rule() -> None:
    with pytest.raises(ValueError, match="No placement rule"):
        orders_of(example(10, ["tool_1", "tool_2", "tool_3"]), SEED)
    with pytest.raises(ValueError, match="No placement rule"):
        orders_of(example(4, ["tool_1"]), SEED)


def test_a_short_list_is_padded_with_other_tools_of_the_dataset_and_every_list_is_shuffled() -> None:
    dataset = example(30, []).options
    short = example(3, ["tool_1", "tool_2"])
    padded = padded_order(short, dataset, 5, SEED)
    assert len(padded) == 5 and len(set(names(padded))) == 5
    assert set(names(short.options)) < set(names(padded)) <= set(names(dataset))
    assert padded == padded_order(short, dataset, 5, SEED)
    assert names(padded) != names(padded_order(short, dataset, 5, SEED + 1))
    long = example(8, ["tool_1"])
    shuffled = padded_order(long, dataset, 5, SEED)
    assert sorted(names(shuffled)) == sorted(names(long.options)) and names(shuffled) != names(long.options)
    assert names(long.options) == [f"tool_{number}" for number in range(1, 9)]


def test_a_grown_list_holds_the_padded_list_and_every_shorter_list_in_an_order_of_its_own() -> None:
    dataset = example(60, []).options
    short = example(3, ["tool_1", "tool_2"])
    orders = grown_orders(short, dataset, 5, [10, 20, 60], SEED)
    assert list(orders) == [OWN_LIST, "10", "20", "60"]
    assert orders[OWN_LIST] == padded_order(short, dataset, 5, SEED)
    assert [len(tools) for tools in orders.values()] == [5, 10, 20, 60]
    sets = [set(names(tools)) for tools in orders.values()]
    assert all(smaller < larger for smaller, larger in zip(sets, sets[1:], strict=False))
    assert all(len(set(names(tools))) == len(tools) for tools in orders.values())
    assert orders == grown_orders(short, dataset, 5, [10, 20, 60], SEED)
    assert names(orders["20"])[:10] != names(orders["10"])


def test_the_reworded_tool_is_a_correct_tool_chosen_with_the_seed() -> None:
    three_correct = example(6, ["tool_2", "tool_4", "tool_5"])
    assert {reworded_tool(three_correct, seed) for seed in range(20)} == {"tool_2", "tool_4", "tool_5"}
    assert reworded_tool(three_correct, SEED) == reworded_tool(three_correct, SEED)


def test_a_list_cannot_grow_to_fewer_tools_than_it_has_or_to_more_than_the_dataset_has() -> None:
    dataset = example(60, []).options
    for length in (4, 61):
        with pytest.raises(ValueError, match="cannot grow"):
            grown_orders(example(3, ["tool_1"]), dataset, 5, [length], SEED)


def test_length_orders_place_the_correct_tool_in_lists_that_contain_the_shorter_ones() -> None:
    one_tool = example(30, ["tool_4"])
    orders = length_orders(one_tool, one_tool.options, [5, 10, 30], SEED)
    assert list(orders) == [f"{length}_{name}" for length in (5, 10, 30) for name in PLACEMENTS]
    assert [len(tools) for tools in orders.values()] == [5] * 5 + [10] * 5 + [30] * 5
    assert [positions(orders[f"10_{name}"], ["tool_4"]) for name in PLACEMENTS] == [[1], [3], [5], [8], [10]]
    short, long, every = (names(orders[f"{length}_first"])[1:] for length in (5, 10, 30))
    assert long[:4] == short and every[:9] == long
    assert sorted(names(orders["30_last"])) == sorted(names(one_tool.options))
    assert orders == length_orders(one_tool, one_tool.options, [5, 10, 30], SEED)


def test_length_orders_need_one_correct_tool_and_enough_tools() -> None:
    with pytest.raises(ValueError, match="needs more than the 10 tools"):
        length_orders(example(10, ["tool_4"]), example(10, []).options, [20], SEED)
    with pytest.raises(ValueError):
        length_orders(example(10, ["tool_4", "tool_5"]), example(10, []).options, [5], SEED)
