
from app.schemas.answer import (
    AnswerSource,
    AskResponse,
)
from app.services.hybrid_retrieval_service import (
    HybridRetrievalService,
)
from app.services.llm_service import LLMService

from app.core.config import settings

from app.services.answer_validation_service import (
    AnswerValidationService,
)


class AnswerService:
    def __init__(self) -> None:
        self.retrieval_service = HybridRetrievalService()
        self.llm_service = LLMService()
        self.validation_service = AnswerValidationService()

    def answer(
        self,
        query: str,
        limit: int = 3,
        document_id: str | None = None,
    ) -> AskResponse:
        results = self.retrieval_service.retrieve(
            query=query,
            limit=limit,
            document_id=document_id,
        )

        results = [
            result
            for result in results
            if result.score >= settings.reranking_min_score
        ]

        if not results:
            return AskResponse(
                query=query,
                answer=(
                    "I couldn't find sufficiently relevant "
                    "information in the available documents "
                    "to answer your question reliably."
                ),
                sources=[],
            )
        context_parts = []

        for index, result in enumerate(results, start=1):
            context_parts.append(
                f"[Source {index}]\n"
                f"Document ID: {result.document_id}\n"
                f"Chunk index: {result.chunk_index}\n"
                f"Content: {result.text}"
            )

        context = "\n\n".join(context_parts)

        system_prompt = (
            "You are Nexora AI, a document-grounded assistant. "
            "Answer using only facts explicitly supported by the "
            "provided context. Do not combine facts from separate "
            "projects or unrelated passages to infer an answer. "
            "Distinguish information explicitly stated in the "
            "documents from information that is not stated. "
            "If the context does not directly answer the question, "
            "say that the documents do not provide enough evidence. "
            "Do not invent facts, explanations, or citations. "
            "Cite supporting evidence using [Source 1], "
            "[Source 2], and so on, matching the supplied context."
        )

        prompt = (
            f"Question:\n{query}\n\n"
            f"Retrieved document context:\n{context}\n\n"
            "Answer the question using the context above. "
            "Include source markers for claims when possible."
        )

        generated_answer = self.llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        is_supported = self.validation_service.is_supported(
            query=query,
            answer=generated_answer,
            context=context,
        )

        if not is_supported:
            generated_answer = (
                "I couldn't verify that the generated answer is fully "
                "supported by the available documents, so I can't "
                "provide a reliable answer."
            )

        sources = [
            AnswerSource(
                document_id=result.document_id,
                chunk_index=result.chunk_index,
                text=result.text,
            )
            for result in results
        ]

        return AskResponse(
            query=query,
            answer=generated_answer,
            sources=sources,
        )
