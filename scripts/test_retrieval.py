from app.services.retrieval_service import RetrievalService


retrieval_service = RetrievalService()

query = "What machine learning projects has this person worked on?"

results = retrieval_service.retrieve(
    query=query,
    limit=3,
)

for index, result in enumerate(results, start=1):
    print(f"\nResult {index}")
    print(f"Score: {result.score}")
    print(f"Document ID: {result.document_id}")
    print(f"Chunk index: {result.chunk_index}")
    print(f"Characters: {result.start_char}-{result.end_char}")
    print(f"Text: {result.text}")