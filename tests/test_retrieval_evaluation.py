from app.services.evaluation_service import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

from app.services.hybrid_retrieval_service import HybridRetrievalService
from tests.evaluation_dataset import EVALUATION_DATASET

def test_hybrid_retrieval_evaluation():
    service = HybridRetrievalService()
    k = 3

    precision_scores = []
    recall_scores = []
    reciprocal_ranks = []

    for case in EVALUATION_DATASET:
        results = service.retrieve(
            query = case["query"],
            limit = k,
            document_id = None,
        )

        retrieved_ids = [
            f"{result.document_id}::{result.chunk_index}"
            for result in results
        ]

        relevant_ids = case["relevant_ids"]

        precision = precision_at_k(
            retrieved_ids, relevant_ids, k
        )

        recall = recall_at_k(
            retrieved_ids, relevant_ids, k
        )

        rr = reciprocal_rank(
            retrieved_ids, relevant_ids
        )

        precision_scores.append(precision)
        recall_scores.append(recall)
        reciprocal_ranks.append(rr)

        print(f"\nQuery: {case['query']}")
        print(f"Retrieved IDs: {retrieved_ids}")
        print(f"Relevant IDs: {relevant_ids}")
        print(f"Precision@{k}: {precision:.3f}")
        print(f"Recall@{k}: {recall:.3f}")
        print(f"Reciprocal Rank: {rr:.3f}")

    count = len(EVALUATION_DATASET)

    mean_precision = sum(precision_scores) / count
    mean_recall = sum(recall_scores) / count
    mrr = sum(reciprocal_ranks) / count

    print("\n=== Retrieval Evaluation Summary ===")
    print(f"Mean Precision@{k}: {mean_precision:.3f}")
    print(f"Mean Recall@{k}: {mean_recall:.3f}")
    print(f"MRR: {mrr:.3f}")    