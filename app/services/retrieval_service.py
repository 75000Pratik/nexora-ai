from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.schemas.retrieval import RetrievalResult

class RetrievalService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

    def retrieve(
            self,
            query: str,
            limit: int = 3,
    ) -> list[RetrievalResult]:
        query_vector = self.embedding_service.embed_text(query)

        results = self.vector_store.search(
            query_vector = query_vector,
            limit = limit
        )

        retrieval_results = []

        for result in results:
            retrieval_results.append(
                RetrievalResult(
                    document_id = result.payload["document_id"],
                    chunk_index = result.payload["chunk_index"],
                    text = result.payload["text"],
                    score = result.score,
                    start_char = result.payload["start_char"],
                    end_char = result.payload["end_char"],
                )
            )

        return retrieval_results
