from app.schemas.answer import AskResponse
from app.services.llm_service import LLMService


class GeneralAnswerService:
    def __init__(self) -> None:
        self.llm_service = LLMService()

    def answer(self, query: str) -> AskResponse:
        system_prompt = (
            "You are Nexora AI, a helpful general-purpose "
            "knowledge assistant. "
            "Answer questions accurately and clearly. "
            "If you are uncertain, acknowledge the uncertainty. "
            "Do not invent facts or present assumptions as facts."
        )

        generated_answer = self.llm_service.generate(
            prompt=query,
            system_prompt=system_prompt,
        )

        return AskResponse(
            query=query,
            answer=generated_answer,
            sources=[],
        )
