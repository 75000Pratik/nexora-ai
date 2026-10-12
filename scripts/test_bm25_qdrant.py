from app.services.bm25_service import BM25Service
from app.services.vector_store_service import VectorStoreService

vector_store = VectorStoreService()

points, _ = vector_store.client.scroll(
    collection_name = vector_store.collection_name,
    limit = 100,
    with_payload = True,
    with_vectors = False,
)

documents = [
    point.payload["text"]
    for point in points
]

bm25_service = BM25Service(documents)

query = "AWS Glue ETL pipelines"

results = bm25_service.search(
    query = query,
    limit = 3,
)

print(f"Loaded chunks: {len(documents)}")
print(f"Query: {query}")

for index, (text, score) in enumerate(results, start=1):
    print(f"\nResult {index}")
    print(f"BM25 Score: {score:.4f}")
    print(f"Text: {text[:400]}")