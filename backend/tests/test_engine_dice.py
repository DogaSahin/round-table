from __future__ import annotations

import random

import pytest

from app.engine.dice import DiceError, evaluate


def test_flat_modifier() -> None:
    result = evaluate("5")
    assert result.total == 5
    assert result.terms[0].is_dice is False


def test_single_die_deterministic_with_seeded_rng() -> None:
    result = evaluate("1d20", rng=random.Random(1))
    assert 1 <= result.total <= 20
    assert result.terms[0].is_dice is True


def test_multiple_dice_plus_modifier() -> None:
    result = evaluate("2d6+3", rng=random.Random(1))
    dice_term, flat_term = result.terms
    assert dice_term.is_dice is True
    assert len(dice_term.kept) == 2
    assert flat_term.total == 3
    assert result.total == dice_term.total + 3


def test_keep_highest() -> None:
    result = evaluate("4d6kh3", rng=random.Random(1))
    assert len(result.terms[0].kept) == 3
    assert len(result.terms[0].discarded) == 1


def test_advantage_rolls_two_keeps_one() -> None:
    result = evaluate("1d20adv", rng=random.Random(1))
    assert len(result.terms[0].kept) == 1
    assert len(result.terms[0].discarded) == 1


def test_subtraction() -> None:
    result = evaluate("10-1d4", rng=random.Random(1))
    assert result.total == 10 - result.terms[1].total


def test_empty_expression_raises() -> None:
    with pytest.raises(DiceError):
        evaluate("")


def test_too_many_sides_raises() -> None:
    with pytest.raises(DiceError):
        evaluate("1d20000")


def test_zero_sided_die_raises() -> None:
    with pytest.raises(DiceError):
        evaluate("1d1")
