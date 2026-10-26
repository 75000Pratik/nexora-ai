import httpx

from app.core.config import settings


class LLMService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_url
        self.model = settings.llm_model

    def generate(self, prompt: str, system_prompt: str = (
            "You are Nexora AI, a helpful knowledge assistant."
        ),
    ) -> str:
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
            },
            timeout=120.0,
        )

        response.raise_for_status()
        data = response.json()

        return data["message"]["content"].strip()
