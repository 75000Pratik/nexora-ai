from app.services.vector_store_service import VectorStoreService

vector_store = VectorStoreService()

points, _ = vector_store.client.scroll(
    collection_name=vector_store.collection_name,
    limit=1,
    with_payload=True,
    with_vectors=False,
)

for point in points:
    print(f"Point ID: {point.id}")
    print(f"Payload: {point.payload}")