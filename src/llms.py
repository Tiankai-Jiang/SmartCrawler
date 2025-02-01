import os
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from openai import OpenAI

load_dotenv()

class LLMAPI(ABC):
    """Abstract class for LLM providers"""

    @abstractmethod
    def get_company_info(self, text: str) -> dict:
        """Takes all text from html and extracts company info"""
        pass


class OpenAIAPI(LLMAPI):
    """Implementation using OpenAI API"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini
        self.client = OpenAI(api_key=self.api_key)

    def get_company_info(self, text: str) -> dict:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": f"""I will give you some contents from a webscraping result, can you extract company name, locations, company url, company introduction from it?\n\n
                 {text}"""}
            ]
        )
        return completion.choices[0].message.content


def get_llm(provider_name: str) -> LLMAPI:
    if provider_name == "openai":
        return OpenAIAPI()
    else:
        raise ValueError("Unsupported LLM")