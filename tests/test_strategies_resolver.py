import pytest

from el_psy_quant.strategies import (
    MovingAverageCrossoverStrategy,
    Strategy,
    resolve_strategy,
    supported_strategy_names,
)


def test_supported_strategy_names_are_deterministic() -> None:
    assert supported_strategy_names() == ("moving_average_crossover",)
    assert supported_strategy_names() == supported_strategy_names()


def test_resolves_moving_average_crossover() -> None:
    strategy = resolve_strategy("moving_average_crossover")

    assert isinstance(strategy, MovingAverageCrossoverStrategy)
    assert isinstance(strategy, Strategy)
    assert strategy.name == "moving_average_crossover"


def test_resolver_returns_independent_instances() -> None:
    first = resolve_strategy("moving_average_crossover")
    second = resolve_strategy("moving_average_crossover")

    assert first is not second


@pytest.mark.parametrize(
    "name",
    ["unknown", "Moving_Average_Crossover", "moving_average"],
)
def test_rejects_unknown_names_without_mutating_supported_names(name: str) -> None:
    before = supported_strategy_names()

    with pytest.raises(ValueError) as error:
        resolve_strategy(name)

    message = str(error.value)
    assert name in message
    assert "moving_average_crossover" in message
    assert supported_strategy_names() == before
