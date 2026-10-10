from app.services.vector_store_service import VectorStoreService

vector_store = VectorStoreService()

count = vector_store.client.count(
    collection_name=vector_store.collection_name,
    exact=True,
)

print(f"Stored points: {count.count}")
