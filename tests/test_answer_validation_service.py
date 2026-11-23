from unittest.mock import Mock

from app.services.answer_validation_service import (
    AnswerValidationService,
)


def test_validator_accepts_supported_answer():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is True


def test_validator_rejects_unsupported_answer():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="UNSUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer=(
            "The RAG pipeline used Amazon Bedrock "
            "and Amazon EKS."
        ),
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_unexpected_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="The answer seems correct."
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_fails_closed_on_llm_error():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=RuntimeError("Ollama unavailable")
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_answer_with_unsupported_service():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer=(
            "The RAG pipeline used Amazon Bedrock "
            "and Amazon EKS."
        ),
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_service_from_unrelated_project():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer=(
            "The RAG pipeline used Amazon Bedrock "
            "and Amazon EMR."
        ),
        context=(
            "The RAG pipeline used Amazon Bedrock. "
            "A separate project used Amazon EMR."
        ),
    )

    assert result is False


def test_validator_accepts_sentence_starting_with_the():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.is_supported(
        query="What does the system use?",
        answer="The system uses FastAPI.",
        context="the system uses FastAPI.",
    )

    assert result is True


def test_validator_rejects_unsupported_entity_without_calling_llm():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=AssertionError(
            "LLM should not be called."
        )
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock and Amazon EKS.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_unrelated_project_entity_without_llm_call():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=AssertionError(
            "LLM should not be called."
        )
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock and Amazon EMR.",
        context=(
            "The RAG pipeline used Amazon Bedrock. "
            "A separate project used Amazon EMR."
        ),
    )

    assert result is False


def test_validator_accepts_supported_verdict_with_whitespace():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="  supported  \n"
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is True


def test_validator_rejects_empty_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value=""
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_rejects_whitespace_only_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="   \n\t  "
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is False


def test_validator_sends_question_context_and_answer_to_llm():
    service = AnswerValidationService()
    captured = {}

    def fake_generate(prompt, system_prompt):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        return "SUPPORTED"

    service.llm_service.generate = Mock(
        side_effect=fake_generate
    )

    result = service.is_supported(
        query="Which service did the RAG pipeline use?",
        answer="The RAG pipeline used Amazon Bedrock.",
        context="The RAG pipeline used Amazon Bedrock.",
    )

    assert result is True
    assert "Which service did the RAG pipeline use?" in captured["prompt"]
    assert "Evidence context:" in captured["prompt"]
    assert "The RAG pipeline used Amazon Bedrock." in captured["prompt"]
    assert "Answer to verify:" in captured["prompt"]
    assert "strict factual claim verifier" in captured["system_prompt"]


def test_extract_cited_claims_keeps_citation_after_punctuation():
    result = AnswerValidationService._extract_cited_claims(
        answer=(
            "The RAG pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The RAG pipeline used Amazon Bedrock."
        ],
    )

    assert result == [
        (
            "The RAG pipeline used Amazon Bedrock.",
            ["The RAG pipeline used Amazon Bedrock."],
        )
    ]


def test_extract_cited_claims_maps_multiple_sentences():
    result = AnswerValidationService._extract_cited_claims(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1] "
            "It stored embeddings in ChromaDB. [Source 2]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock.",
            "The system stored embeddings in ChromaDB.",
        ],
    )

    assert result == [
        (
            "The pipeline used Amazon Bedrock.",
            ["The pipeline used Amazon Bedrock."],
        ),
        (
            "It stored embeddings in ChromaDB.",
            ["The system stored embeddings in ChromaDB."],
        ),
    ]


def test_extract_cited_claims_rejects_missing_citation():
    result = AnswerValidationService._extract_cited_claims(
        answer="The pipeline used Amazon Bedrock.",
        sources=[
            "The pipeline used Amazon Bedrock.",
        ],
    )

    assert result is None


def test_extract_cited_claims_rejects_out_of_range_source():
    result = AnswerValidationService._extract_cited_claims(
        answer="The pipeline used Amazon Bedrock. [Source 2]",
        sources=[
            "The pipeline used Amazon Bedrock.",
        ],
    )

    assert result is None


def test_extract_cited_claims_rejects_malformed_citation():
    result = AnswerValidationService._extract_cited_claims(
        answer="The pipeline used Amazon Bedrock. [Source abc]",
        sources=[
            "The pipeline used Amazon Bedrock.",
        ],
    )

    assert result is None


def test_extract_cited_claims_rejects_unclosed_citation():
    result = AnswerValidationService._extract_cited_claims(
        answer="The pipeline used Amazon Bedrock. [Source 1",
        sources=[
            "The pipeline used Amazon Bedrock.",
        ],
    )

    assert result is None


def test_extract_cited_claims_rejects_empty_claim():
    result = AnswerValidationService._extract_cited_claims(
        answer="[Source 1]",
        sources=[
            "The pipeline used Amazon Bedrock.",
        ],
    )

    assert result is None


def test_are_citations_supported_accepts_supported_claim():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    assert result is True
    service.llm_service.generate.assert_called_once()


def test_are_citations_supported_rejects_unsupported_claim():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="UNSUPPORTED"
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon SageMaker."
        ],
    )

    assert result is False
    service.llm_service.generate.assert_called_once()


def test_are_citations_supported_fails_closed_on_llm_error():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=RuntimeError("LLM unavailable")
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    assert result is False
    service.llm_service.generate.assert_called_once()


def test_are_citations_supported_checks_every_claim():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=["SUPPORTED", "SUPPORTED"]
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1] "
            "It stored embeddings in ChromaDB. [Source 2]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock.",
            "The system stored embeddings in ChromaDB.",
        ],
    )

    assert result is True
    assert service.llm_service.generate.call_count == 2


def test_are_citations_supported_stops_after_unsupported_claim():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=["UNSUPPORTED", "SUPPORTED"]
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1] "
            "It stored embeddings in ChromaDB. [Source 2]"
        ),
        sources=[
            "The pipeline used Amazon SageMaker.",
            "The system stored embeddings in ChromaDB.",
        ],
    )

    assert result is False
    service.llm_service.generate.assert_called_once()


def test_are_citations_supported_sends_claim_and_cited_evidence():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="SUPPORTED"
    )

    service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    prompt = service.llm_service.generate.call_args.kwargs[
        "prompt"
    ]

    assert (
        "The pipeline used Amazon Bedrock."
        in prompt
    )
    assert "Cited evidence:" in prompt


def test_extract_cited_claims_maps_multiple_sources_to_one_claim():
    result = AnswerValidationService._extract_cited_claims(
        answer=(
            "The system uses FastAPI and ChromaDB. "
            "[Source 1] [Source 2]"
        ),
        sources=[
            "The backend uses FastAPI.",
            "The vector database is ChromaDB.",
        ],
    )

    assert result == [
        (
            "The system uses FastAPI and ChromaDB.",
            [
                "The backend uses FastAPI.",
                "The vector database is ChromaDB.",
            ],
        )
    ]


def test_extract_cited_claims_rejects_one_invalid_source_among_multiple():
    result = AnswerValidationService._extract_cited_claims(
        answer=(
            "The system uses FastAPI and ChromaDB. "
            "[Source 1] [Source 3]"
        ),
        sources=[
            "The backend uses FastAPI.",
            "The vector database is ChromaDB.",
        ],
    )

    assert result is None


def test_are_citations_supported_rejects_unsupported_second_claim():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        side_effect=["SUPPORTED", "UNSUPPORTED"]
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1] "
            "It stored embeddings in ChromaDB. [Source 2]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock.",
            "The system stored embeddings in FAISS.",
        ],
    )

    assert result is False
    assert service.llm_service.generate.call_count == 2


def test_extract_cited_claims_handles_duplicate_sources():
    result = AnswerValidationService._extract_cited_claims(
        answer=(
            "The pipeline uses Amazon Bedrock. "
            "[Source 1] [Source 1]"
        ),
        sources=[
            "The pipeline uses Amazon Bedrock.",
        ],
    )

    assert result == [
        (
            "The pipeline uses Amazon Bedrock.",
            [
                "The pipeline uses Amazon Bedrock.",
                "The pipeline uses Amazon Bedrock.",
            ],
        )
    ]


def test_are_citations_supported_rejects_unexpected_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="MAYBE"
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    assert result is False
    service.llm_service.generate.assert_called_once()


def test_are_citations_supported_accepts_whitespace_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="  SUPPORTED\n"
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    assert result is True


def test_are_citations_supported_rejects_empty_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value=""
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    assert result is False


def test_are_citations_supported_rejects_whitespace_verdict():
    service = AnswerValidationService()
    service.llm_service.generate = Mock(
        return_value="   \n\t  "
    )

    result = service.are_citations_supported(
        answer=(
            "The pipeline used Amazon Bedrock. [Source 1]"
        ),
        sources=[
            "The pipeline used Amazon Bedrock."
        ],
    )

    assert result is False
