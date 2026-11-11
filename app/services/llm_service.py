import httpx

from app.core.config import settings
from app.core.exceptions import (
    LLMServiceError,
    LLMServiceTimeoutError,
)


class LLMService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_url
        self.model = settings.llm_model

    def generate(self, prompt: str, system_prompt: str = (
            "You are Nexora AI, a helpful knowledge assistant."
        ),
    ) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0,
                    },
                },
                timeout=120.0,
            )

            response.raise_for_status()

            data = response.json()
            answer = data["message"]["content"]

            if not isinstance(answer, str) or not answer.strip():
                raise LLMServiceError(
                    "LLM provider returned an empty or invalid answer."
                )
            return answer.strip()

        except httpx.TimeoutException as exc:
            raise LLMServiceTimeoutError(
                "LLM provider request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise LLMServiceError(
                "Unable to communicate with the LLM provider."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise LLMServiceError(
                "LLM provider returned an unsuccessful HTTP response."
            ) from exc

        except (
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            raise LLMServiceError(
                "LLM provider returned an invalid response."
            ) from exc
