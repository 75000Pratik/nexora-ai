from pydantic import BaseModel

class DocumentChunk(BaseModel):
    chunk_index: int
    text: str
    start_char: int
    end_char: int