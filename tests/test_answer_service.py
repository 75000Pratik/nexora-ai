
from unittest.mock import Mock

from app.schemas.retrieval import RetrievalResult
from app.services.answer_service import AnswerService


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
        return_value = True
    )

    monkeypatch.setattr(
        "app.services.answer_service.settings.reranking_min_score",
        0.0,
    )

    response = service.answer(
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
            score = 5.7,
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
        query = "Which service did the RAG pipeline use?"
    )

    assert "Amazon Bedrock" not in response.answer
    assert "Amazon EMR" not in response.answer
    assert "Amazon EKS" not in response.answer
    assert "couldn't verify" in response.answer