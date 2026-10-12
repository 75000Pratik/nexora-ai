from app.services.bm25_service import BM25Service

documents = [
    "Developed machine learning models using Python.",
    "Implemented AWS Glue ETL pipelines using PySpark.",
    "Build a real-time voice assistant using WebSockets.",
    "Created an image classifier using TensorFlow.",
    "Deployed cloud infrastructure using Docker.",
]

bm25_service = BM25Service(documents)

query = "AWS Glue ETL pipelines"

results = bm25_service.search(query=query, limit=3)

print(f"Query: {query}")

for index, (text,score) in enumerate(results, start=1):
    print(f"\nResult {index}")
    print(f"BM25 score: {score:.4f}")
    print(f"Text: {text}")

