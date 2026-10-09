from app.schemas.chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.text_service import normalize_text
from app.services.chunking_service import chunk_text

embedding_service = EmbeddingService()

def process_document_text(extracted_text: str,) -> tuple[list[DocumentChunk], list[list[float]]]:
    
    cleaned_text = normalize_text(extracted_text)

    chunks = chunk_text(
        cleaned_text,
        chunk_size=1000,
        overlap=150,
    )

    chunk_texts = [chunk.text for chunk in chunks]
    embeddings = embedding_service.embed_texts(chunk_texts)

    return chunks, embeddings