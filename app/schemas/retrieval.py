from pydantic import BaseModel

class RetrievalResult(BaseModel):
    document_id: str
    chunk_index: int
    text: str
    score: float
    start_char: int 
    end_char: int