import pytest

from app.services.evaluation_service import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
)


def test_precision_at_k():
    retrieved = ["A", "B", "C"]
    relevant = {"B", "C"}

    assert precision_at_k(retrieved, relevant, 2) == 0.5


def test_recall_at_k():
    retrieved = ["A", "B", "C"]
    relevant = {"B", "C"}

    assert recall_at_k(retrieved, relevant, 2) == 0.5


def test_reciprocal_rank():
    retrieved = ["A", "B", "C"]
    relevant = {"B", "C"}

    assert reciprocal_rank(retrieved, relevant) == 0.5


def test_reciprocal_rank_returns_zero_when_no_match():
    retrieved = ["A", "B", "C"]
    relevant = {"D"}

    assert reciprocal_rank(retrieved, relevant) == 0.0


@pytest.mark.parametrize("k", [0, -1])
def test_precision_at_k_rejects_invalid_k(k):
    with pytest.raises(ValueError):
        precision_at_k(["A"], {"A"}, k)


@pytest.mark.parametrize("k", [0, -1])
def test_recall_at_k_rejects_invalid_k(k):
    with pytest.raises(ValueError):
        recall_at_k(["A"], {"A"}, k)


def test_mean_reciprocal_rank():
    query_results = [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "I"],
    ]

    relevant_by_query = [
        {"A"},
        {"E"},
        {"I"}
    ]

    expected = (1.0 + 0.5 + (1.0 / 3.0)) / 3

    assert mean_reciprocal_rank(
        query_results,
        relevant_by_query,
    ) == pytest.approx(expected)


def test_mean_reciprocal_rank_empty_input():
    assert mean_reciprocal_rank([], []) == 0.0


def test_mean_reciprocal_rank_rejects_mismatched_inputs():
    with pytest.raises(ValueError):
        mean_reciprocal_rank(
            [["A", "B"]],
            [],
        )
