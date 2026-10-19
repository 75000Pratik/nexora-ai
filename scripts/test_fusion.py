from app.services.fusion_service import reciprocal_rank_fusion


bm25_ranking = [
    "chunk_5",
    "chunk_6",
    "chunk_2",
]

dense_ranking = [
    "chunk_2",
    "chunk_5",
    "chunk_4",
]

results = reciprocal_rank_fusion(
    ranking_lists=[bm25_ranking, dense_ranking],
    k=60,
)

print("Hybrid RRF Results")

for position, (chunk_id, score) in enumerate(results, start=1):
    print(f"{position}. {chunk_id}: {score:.6f}")
