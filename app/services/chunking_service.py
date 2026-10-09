from app.schemas.chunk import DocumentChunk

def chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 150,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    if not text:
        return []

    chunks: list[DocumentChunk] = []

    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = DocumentChunk(
            chunk_index=chunk_index,
            text=text[start:end],
            start_char=start,
            end_char=end,
        )

        chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap
        chunk_index += 1

    return chunks
