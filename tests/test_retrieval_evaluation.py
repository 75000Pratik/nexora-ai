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

    baseline_metrics = {
        "precision": [],
        "recall": [],
        "rr": [],
    }
    reranked_metrics = {
        "precision": [],
        "recall": [],
        "rr": [],
    }

    for case in EVALUATION_DATASET:
        print(f"\nQuery: {case['query']}")
        relevant_ids = case["relevant_ids"]

        for apply_reranking, metrics, label in [
            (False, baseline_metrics, "RRF Baseline"),
            (True, reranked_metrics, "Cross-Encoder Reranked"),
        ]:
            results = service.retrieve(
                query=case["query"],
                limit=k,
                document_id=None,
                apply_reranking=apply_reranking,
            )

            retrieved_ids = [
                f"{result.document_id}::{result.chunk_index}"
                for result in results
            ]

            precision = precision_at_k(
                retrieved_ids, relevant_ids, k
            )
            recall = recall_at_k(
                retrieved_ids, relevant_ids, k
            )
            rr = reciprocal_rank(
                retrieved_ids, relevant_ids
            )

            metrics["precision"].append(precision)
            metrics["recall"].append(recall)
            metrics["rr"].append(rr)

            print(f"\n{label}")
            print(f"Retrieved IDs: {retrieved_ids}")
            print(f"Precision@{k}: {precision:.3f}")
            print(f"Recall@{k}: {recall:.3f}")
            print(f"Reciprocal Rank: {rr:.3f}")

    count = len(EVALUATION_DATASET)

    print("\n=== Evaluation Comparison ===")
    for label, metrics in [
        ("RRF Baseline", baseline_metrics),
        ("Cross-Encoder Reranked", reranked_metrics),
    ]:
        mean_precision = sum(metrics["precision"]) / count
        mean_recall = sum(metrics["recall"]) / count
        mrr = sum(metrics["rr"]) / count

        print(f"\n{label}")
        print(f"Mean Precision@{k}: {mean_precision:.3f}")
        print(f"Mean Recall@{k}: {mean_recall:.3f}")
        print(f"MRR: {mrr:.3f}")
