import pytest
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)

Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def db_session() -> Session:
    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


def test_get_by_id_returns_document(db_session):
    document_id = uuid4()

    document = Document(
        id=document_id,
        filename="sample.pdf",
        content_type="application/pdf",
        project_id=None,
        status="ready",
    )

    db_session.add(document)
    db_session.commit()

    repository = DocumentRepository(db_session)

    result = repository.get_by_id(document_id)

    assert result is not None
    assert result.id == document_id
    assert result.filename == "sample.pdf"
    assert result.status == "ready"


def test_get_by_id_returns_none_when_document_not_found(db_session):
    repository = DocumentRepository(db_session)

    result = repository.get_by_id(uuid4())

    assert result is None
