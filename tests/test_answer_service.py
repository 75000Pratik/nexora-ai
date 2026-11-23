from uuid import uuid4
from unittest.mock import Mock

from app.schemas.retrieval import RetrievalResult
from app.services.answer_service import AnswerService

TEST_USER_ID = uuid4()


def test_answer_filters_low_scoring_results(monkeypatch):
    service = AnswerService()

    results = [
        RetrievalResult(
            document_id="doc-1",
            chunk_index=2,
            text="The RAG pipeline used Amazon Bedrock.",
            score=5.7,
            start_char=0,
            end_char=40,
        ),
        RetrievalResult(
            document_id="doc-1",
            chunk_index=5,
            text="A separate project used Amazon EMR.",
            score=-3.2,
            start_char=100,
            end_char=135,
        ),
    ]

    service.retrieval_service.retrieve = Mock(
        return_value=results
    )
    service.llm_service.generate = Mock(
        return_value="The RAG pipeline used Amazon Bedrock. [Source 1]"
    )

    service.validation_service.is_supported = Mock(
        return_value=True
    )

    service.validation_service.are_citations_supported = Mock(
        return_value=True
    )

    monkeypatch.setattr(
        "app.services.answer_service.settings.reranking_min_score",
        0.0,
    )

    response = service.answer(
        user_id=TEST_USER_ID,
        query="Which service did the RAG pipeline use?"
    )

    assert len(response.sources) == 1
    assert response.sources[0].chunk_index == 2

    prompt = service.llm_service.generate.call_args.kwargs["prompt"]

    assert "Amazon Bedrock" in prompt
    assert "A separate project used Amazon EMR." not in prompt


def test_answer_does_not_claim_unsupported_project_details(monkeypatch):
    service = AnswerService()

    results = [
        RetrievalResult(
            document_id="doc-1",
            chunk_index=2,
            text=(
                "The RAG pipeline used Amazon Bedrock. "
                "A separate project used Amazon EMR and Amazon EKS."
            ),
            score=5.7,
            start_char=0,
            end_char=100,
        ),
    ]

    service.retrieval_service.retrieve = Mock(return_value=results)
    service.llm_service.generate = Mock(
        return_value=(
            "The RAG pipeline used Amazon Bedrock, "
            "Amazon EMR, and Amazon EKS. [Source 1]"
        )
    )
    service.validation_service.is_supported = Mock(
        return_value=False
    )

    monkeypatch.setattr(
        "app.services.answer_service.settings.reranking_min_score",
        0.0,
    )

    response = service.answer(
        user_id=TEST_USER_ID,
        query="Which service did the RAG pipeline use?"
    )

    assert "Amazon Bedrock" not in response.answer
    assert "Amazon EMR" not in response.answer
    assert "Amazon EKS" not in response.answer
    assert "couldn't verify" in response.answer


def test_answer_passes_project_id_to_retrieval():
    service = AnswerService()

    service.retrieval_service.retrieve = Mock(
        return_value=[]
    )

    service.answer(
        user_id=TEST_USER_ID,
        query="What does this project contain?",
        project_id="project-123",
    )

    service.retrieval_service.retrieve.assert_called_once_with(
        user_id=TEST_USER_ID,
        query="What does this project contain?",
        limit=3,
        document_id=None,
        project_id="project-123",
    )


def test_has_valid_citations_accepts_existing_sources():
    assert AnswerService._has_valid_citations(
        answer="The project uses RAG. [Source 1] [Source 2]",
        source_count=2,
    )


def test_has_valid_citations_rejects_nonexistent_source():
    assert not AnswerService._has_valid_citations(
        answer="The project uses RAG. [Source 3]",
        source_count=2,
    )


def test_has_valid_citations_rejects_source_zero():
    assert not AnswerService._has_valid_citations(
        answer="The project uses RAG. [Source 0]",
        source_count=2,
    )


def test_has_valid_citations_rejects_malformed_source():
    assert not AnswerService._has_valid_citations(
        answer="The project uses RAG. [Source abc]",
        source_count=2,
    )


def test_has_valid_citations_rejects_missing_citations():
    assert not AnswerService._has_valid_citations(
        answer="The project uses RAG.",
        source_count=2,
    )


def test_has_valid_citations_rejects_unclosed_source():
    assert not AnswerService._has_valid_citations(
        answer="The project uses RAG. [Source 1",
        source_count=2,
    )
