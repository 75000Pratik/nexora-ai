import pytest
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentStatus

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
    connection = test_engine.connect()
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection)

    try:
        yield db

    finally:
        db.close()
        transaction.rollback()
        connection.close()


def create_test_user(db_session: Session):
    user = User(
        id=uuid4(),
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()

    return user


def test_get_by_id_returns_document(db_session: Session):
    document_id = uuid4()
    user = create_test_user(db_session)

    document = Document(
        id=document_id,
        user_id=user.id,
        filename="sample.pdf",
        content_type="application/pdf",
        project_id=None,
        status="ready",
    )

    db_session.add(document)
    db_session.commit()

    repository = DocumentRepository(db_session)

    result = repository.get_by_id(
        document_id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == document_id
    assert result.filename == "sample.pdf"
    assert result.status == "ready"


def test_get_by_id_returns_none_when_document_not_found(
        db_session: Session,
):
    user = create_test_user(db_session)
    repository = DocumentRepository(db_session)

    result = repository.get_by_id(
        uuid4(),
        user_id=user.id,
    )

    assert result is None


def test_list_documents_returns_all_documents(db_session):
    user = create_test_user(db_session)
    documents = [
        Document(
            id=uuid4(),
            user_id=user.id,
            filename="first.pdf",
            content_type="application/pdf",
            project_id=None,
            status="ready",
        ),
        Document(
            id=uuid4(),
            user_id=user.id,
            filename="second.pdf",
            content_type="application/pdf",
            project_id=None,
            status="failed",
        ),
    ]

    db_session.add_all(documents)
    db_session.commit()

    repository = DocumentRepository(db_session)

    result, total = repository.list_documents(
        user_id=user.id,
    )

    assert total == 2
    assert len(result) == 2


def test_list_documents_filters_by_status(db_session):
    user = create_test_user(db_session)
    documents = [
        Document(
            id=uuid4(),
            user_id=user.id,
            filename="ready.pdf",
            content_type="application/pdf",
            project_id=None,
            status="ready",
        ),
        Document(
            id=uuid4(),
            user_id=user.id,
            filename="failed.pdf",
            content_type="application/pdf",
            project_id=None,
            status="failed",
        ),
    ]

    db_session.add_all(documents)
    db_session.commit()

    repository = DocumentRepository(db_session)

    result, total = repository.list_documents(
        user_id=user.id,
        status=DocumentStatus.ready,
    )

    assert total == 1
    assert len(result) == 1
    assert result[0].filename == "ready.pdf"


def test_list_documents_supports_pagination(db_session):
    user = create_test_user(db_session)
    documents = [
        Document(
            id=uuid4(),
            user_id=user.id,
            filename=f"document-{i}.pdf",
            content_type="application/pdf",
            project_id=None,
            status="ready",
        )
        for i in range(5)
    ]

    db_session.add_all(documents)
    db_session.commit()

    repository = DocumentRepository(db_session)

    result, total = repository.list_documents(
        user_id=user.id,
        skip=1,
        limit=2,
    )

    assert total == 5
    assert len(result) == 2


def test_delete_removes_document(db_session: Session):
    user = create_test_user(db_session)
    document = Document(
        id=uuid4(),
        user_id=user.id,
        filename="delete-me.pdf",
        content_type="application/pdf",
        project_id=None,
        status="ready",
    )

    db_session.add(document)
    db_session.commit()

    repository = DocumentRepository(db_session)
    repository.delete(document)

    result = repository.get_by_id(
        document.id,
        user_id=user.id,
    )

    assert result is None


def test_delete_does_not_affect_other_documents(db_session: Session):
    user = create_test_user(db_session)
    document_to_delete = Document(
        id=uuid4(),
        user_id=user.id,
        filename="delete-me.pdf",
        content_type="application/pdf",
        project_id=None,
        status="ready",
    )

    document_to_keep = Document(
        id=uuid4(),
        user_id=user.id,
        filename="keep-me.pdf",
        content_type="application/pdf",
        project_id=None,
        status="ready",
    )

    db_session.add_all([document_to_delete, document_to_keep])
    db_session.commit()

    repository = DocumentRepository(db_session)
    repository.delete(document_to_delete)

    result = repository.get_by_id(
        document_to_keep.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.filename == "keep-me.pdf"


def test_get_by_id_does_not_return_another_users_document(
    db_session: Session,
):
    owner = create_test_user(db_session)
    another_user = create_test_user(db_session)

    document = Document(
        id=uuid4(),
        user_id=owner.id,
        filename="private.pdf",
        content_type="application/pdf",
        status=DocumentStatus.ready,
    )

    db_session.add(document)
    db_session.commit()

    repository = DocumentRepository(db_session)

    result = repository.get_by_id(
        document.id,
        user_id=another_user.id,
    )

    assert result is None
