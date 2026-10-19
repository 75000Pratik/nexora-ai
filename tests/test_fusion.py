import pytest

from app.services.fusion_service import reciprocal_rank_fusion


def test_rrf_combines_rankings():
    bm25 = ["chunk_5", "chunk_6", "chunk_2"]
    dense = ["chunk_2", "chunk_5", "chunk_4"]

    results = reciprocal_rank_fusion(
        ranking_lists=[bm25, dense],
        k=60,
    )

    ranked_ids = [chunk_id for chunk_id, score in results]

    assert ranked_ids == [
        "chunk_5",
        "chunk_2",
        "chunk_6",
        "chunk_4",
    ]


def test_rrf_empty_rankings():
    results = reciprocal_rank_fusion(
        ranking_lists=[[], []],
    )

    assert results == []


def test_rrf_rejects_invalid_k():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(
            ranking_lists=[["chunk_1"]],
            k=0,
        )