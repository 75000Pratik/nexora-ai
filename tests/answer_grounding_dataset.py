
ANSWER_GROUNDING_DATASET = [
    {
        "name": "supported_claim",
        "query": "Which service did the RAG pipeline use?",
        "context": (
            "The RAG pipeline used Amazon Bedrock."
        ),
        "answer": (
            "The RAG pipeline used Amazon Bedrock."
        ),
        "expected_supported": True,
    },
    {
        "name": "unsupported_service",
        "query": "Which service did the RAG pipeline use?",
        "context": (
            "The RAG pipeline used Amazon Bedrock."
        ),
        "answer": (
            "The RAG pipeline used Amazon Bedrock and Amazon EKS."
        ),
        "expected_supported": False,
    },
    {
        "name": "unrelated_project_fact",
        "query": "Which service did the RAG pipeline use?",
        "context": (
            "The RAG pipeline used Amazon Bedrock. "
            "A separate project used Amazon EMR."
        ),
        "answer": (
            "The RAG pipeline used Amazon Bedrock and Amazon EMR."
        ),
        "expected_supported": False,
    },
    {
        "name": "unsupported_detail",
        "query": "Which embedding model was used?",
        "context": (
            "The project uses vector search for document retrieval."
        ),
        "answer": (
            "The project uses the all-MiniLM-L6-v2 embedding model."
        ),
        "expected_supported": False,
    },
    {
        "name": "insufficient_context",
        "query": "When was the system deployed?",
        "context": (
            "The system uses FastAPI and Qdrant."
        ),
        "answer": (
            "The system was deployed in October 2026."
        ),
        "expected_supported": False,
    },
]
