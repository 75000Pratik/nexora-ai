from sentence_transformers import CrossEncoder

class RerankingService:
    def __init__(self) -> None:
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )


    def rerank(
            self,
            query: str,
            documents: list[str],
    ) -> list[tuple[int, float]]:
        if not documents:
            return []

        pairs = [
            (query, document)
            for document in documents
        ]    

        scores = self.model.predict(pairs)

        ranked_results = [
            (index, float(score))
            for index, score in enumerate(scores)
        ]

        return sorted(
            ranked_results,
            key=lambda item : (-item[1], item[0]),
        )