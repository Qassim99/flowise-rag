import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

llm_api_key = os.getenv("OPENROUTER_API_KEY")
llm_base_url: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")


class LLMProvider:
    def __init__(self, model=None):
        self.client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)

    def is_available(self) -> bool:
        return self.client is not None

    def generate_chat_completion(
        self,
        messages: list,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        if not self.client:
            raise RuntimeError("LLM Client is not initialized (missing API key).")

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response
