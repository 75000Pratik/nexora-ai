import re

from rank_bm25 import BM25Okapi

def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())

class BM25Service:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.tokenized_documents = [
            tokenize(document) for document in documents
        ]

        self.bm25 = BM25Okapi(self.tokenized_documents)

    def search(
            self,
            query: str,
            limit: int = 3,
    ) -> list[tuple[str, float]]:
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )    

        return [
            (self.documents[index], float(scores[index]))
            for index in ranked_indices[:limit]
        ]