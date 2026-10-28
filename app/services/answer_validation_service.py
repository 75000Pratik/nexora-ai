from app.services.llm_service import LLMService


class AnswerValidationService:
    def __init__(self) -> None:
        self.llm_service = LLMService()

    def is_supported(
            self,
            query: str,
            answer: str,
            context: str,
    ) -> bool:
        system_prompt = (
            "You are a strict answer-grounding validator. "
            "Check whether every factual claim in the proposed "
            "answer is supported by the supplied context and "
            "answers the question without combining unrelated "
            "project facts. "
            "Reply with exactly SUPPORTED if every factual claim "
            "is supported. Otherwise reply with exactly "
            "UNSUPPORTED. Do not explain your decision."
        )

        prompt = (
            f"Question:\n{query}\n\n"
            f"Context:\n\n{context}\n\n"
            f"Proposed answer:\n\n{answer}\n\n"
            "Is every factual claim supported by the context?"
        )

        try:
            verdict = self.llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )

        except Exception:
            return False

        return verdict.strip().upper() == "SUPPORTED"
