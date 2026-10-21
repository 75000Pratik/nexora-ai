def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than 0")

    top_k = retrieved_ids[:k]

    if not top_k:
        return 0.0

    relevant_count = sum(
        item_id in relevant_ids
        for item_id in top_k
    )

    return relevant_count / len(top_k)


def recall_at_k(
        retrieved_ids: list[str],
        relevant_ids: set[str],
        k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than 0")

    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]

    relevant_count = sum(
        item_id in relevant_ids
        for item_id in top_k
    )

    return relevant_count / len(relevant_ids)


def reciprocal_rank(
        retrieved_ids: list[str],
        relevant_ids: set[str],
) -> float:
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
        query_results: list[list[str]],
        relevant_by_query: list[set[str]],
) -> float:
    if len(query_results) != len(relevant_by_query):
        raise ValueError(
            "Each query must have a corresponding relevant ID set"
        )

    if not query_results:
        return 0.0

    reciprocal_ranks = [
        reciprocal_rank(retrieved, relevant)
        for retrieved, relevant in zip(
            query_results,
            relevant_by_query,
        )
    ]

    return sum(reciprocal_ranks) / len(reciprocal_ranks)
