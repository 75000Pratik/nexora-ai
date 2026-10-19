
from app.schemas.retrieval import RetrievalResult
from app.services.bm25_service import BM25Service
from app.services.fusion_service import reciprocal_rank_fusion
from app.services.retrieval_service import RetrievalService


class HybridRetrievalService:
    def __init__(self) -> None:
        self.dense_retrieval = RetrievalService()
        self.vector_store = self.dense_retrieval.vector_store

    def retrieve(
        self,
        query: str,
        limit: int = 3,
        document_id: str | None = None,
    ) -> list[RetrievalResult]:
        records = self.vector_store.get_chunks(
            document_id=document_id
        )

        if not records:
            return []

        chunk_ids = []
        documents = []
        results_by_id: dict[str, RetrievalResult] = {}

        for record in records:
            payload = record.payload

            chunk_id = (
                f"{payload['document_id']}::{payload['chunk_index']}"
            )

            chunk_ids.append(chunk_id)
            documents.append(payload["text"])

            results_by_id[chunk_id] = RetrievalResult(
                document_id=payload["document_id"],
                chunk_index=payload["chunk_index"],
                text=payload["text"],
                score=0.0,
                start_char=payload["start_char"],
                end_char=payload["end_char"],
            )

        candidate_limit = min(max(limit * 3, 10), len(records))

        bm25_service = BM25Service(documents)

        bm25_results = bm25_service.search_with_indices(
            query=query,
            limit=candidate_limit,
        )

        bm25_ranking = [
            chunk_ids[index]
            for index, score in bm25_results
            if score != 0.0
        ]

        dense_results = self.dense_retrieval.retrieve(
            query=query,
            limit=candidate_limit,
            document_id=document_id,
        )

        dense_ranking = [
            f"{result.document_id}::{result.chunk_index}"
            for result in dense_results
        ]

        fused_results = reciprocal_rank_fusion(
            ranking_lists=[bm25_ranking, dense_ranking],
            k=60,
        )

        final_results = []

        for chunk_id, fusion_score in fused_results[:limit]:
            original = results_by_id[chunk_id]

            final_results.append(
                RetrievalResult(
                    document_id=original.document_id,
                    chunk_index=original.chunk_index,
                    text=original.text,
                    score=fusion_score,
                    start_char=original.start_char,
                    end_char=original.end_char,
                )
            )

        return final_results
