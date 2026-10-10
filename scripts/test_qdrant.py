from app.services.vector_store_service import VectorStoreService

vector_store = VectorStoreService()

vector_store.ensure_collection()

print("Qdrant collection is ready.")