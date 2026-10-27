
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
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            boundary = text.rfind("\n\n", start, end)

            if boundary > start:
                end = boundary

        if end <= start:
            end = min(start + chunk_size, text_length)

        chunks.append(
            DocumentChunk(
                chunk_index=chunk_index,
                text=text[start:end],
                start_char=start,
                end_char=end,
            )
        )

        if end == text_length:
            break

        if text[end:end + 2] == "\n\n":
            next_start = end + 2
        else:
            next_start = max(start, end - overlap)

            if next_start <= start:
                next_start = end

        start = next_start
        chunk_index += 1

    return chunks
