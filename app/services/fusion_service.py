from collections import defaultdict


def reciprocal_rank_fusion(
    ranking_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    scores: dict[str, float] = defaultdict(float)

    for ranking in ranking_lists:
        for position, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] += 1 / (k + position)

    return sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    )