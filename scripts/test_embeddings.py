from app.services.embedding_service import EmbeddingService


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


embedding_service = EmbeddingService()

text_1 = "I work as an AI engineer."
text_2 = "I build machine learning systems."
text_3 = "I bought vegetables from the market."

embedding_1 = embedding_service.embed_text(text_1)
embedding_2 = embedding_service.embed_text(text_2)
embedding_3 = embedding_service.embed_text(text_3)

similar_score = cosine_similarity(embedding_1, embedding_2)
unrelated_score = cosine_similarity(embedding_1, embedding_3)

print(f"AI vs ML similarity: {similar_score:.4f}")
print(f"AI vs vegetables similarity: {unrelated_score:.4f}")