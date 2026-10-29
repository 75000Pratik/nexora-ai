from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
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
            project_id: str | None = None,
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
                    "project_id": project_id,
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

    def search(
            self,
            query_vector: list[float],
            limit: int = 3,
            document_id: str | None = None,
            project_id: str | None = None,
    ):
        conditions = []

        if document_id is not None:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            )
        if project_id is not None:
            conditions.append(
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=project_id),
                )
            )

        query_filter = Filter(must=conditions) if conditions else None

        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            with_payload=True,
            limit=limit
        )

        return result.points

    def get_chunks(
        self,
        document_id: str | None = None,
        project_id: str | None = None,
        batch_size: int = 256,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        conditions = []

        if document_id is not None:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            )

        if project_id is not None:
            conditions.append(
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=project_id),
                )
            )

        query_filter = Filter(must=conditions) if conditions else None

        records = []
        next_page_offset = None

        while True:
            batch, next_page_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=batch_size,
                offset=next_page_offset,
                with_payload=True,
                with_vectors=False,
            )

            records.extend(batch)

            if next_page_offset is None:
                break

        records.sort(
            key=lambda point: (
                str(point.payload.get("document_id", "")),
                int(point.payload.get("chunk_index", 0)),
            )
        )

        return records
