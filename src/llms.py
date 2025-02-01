from abc import ABC, abstractmethod
from openai import OpenAI

class LLMAPI(ABC):
    """Abstract class for LLM providers"""

    @abstractmethod
    def get_company_info(self, text: str) -> dict:
        """Takes all text from html and extracts company info"""
        pass

class OpenAIAPI(LLMAPI):
    """Implementation using OpenAI API"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def get_company_info(self, text: str) -> dict:
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[
                {"role": "user", "content": f"""I will give you some contents from a webscraping result, can you extract company name, locations, company url, company introduction from it?\n\n
                 {text}"""}
            ]
            )
        return completion.choices[0].message["content"]