from qdrant_client import QdrantClient
from qdrant_client.models import(
    Distance,
    PointStruct,
    VectorParams,

)

from app.core.config import settings
from uuid import uuid5, NAMESPACE_URL
from app.schemas.chunk import DocumentChunk

Vector_Size = 384

class VectorStoreService:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=Vector_Size,
                distance=Distance.COSINE,

            ),
        )    

    def store_document_chunks(
            self,
            document_id: str,
            chunks: list[DocumentChunk],
            embeddings: list[list[float]],
    ) -> None:

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings"
            )        

        points = []

        for chunk, embedding in zip(chunks, embeddings):
            point = PointStruct(
                id=str(
                    uuid5(
                        NAMESPACE_URL,
                        f"{document_id}:{chunk.chunk_index}",
                    )
                ),
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char
                },
            )

            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )    
