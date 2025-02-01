import os
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from openai import OpenAI

load_dotenv()

PROMPT = '''
    You are an expert in information extraction. Your task is to extract company information from the provided webpage content and return the data strictly in the following Python dictionary format:

    {
        "url": "<company_website_url>",
        "name": "<company_name>",
        "description": "<company_description>",
        "source": "<source_page_url>",
        "country": "<country>",
        "city": "<city>",
        "email": "<email_address>"
    }

    ### Important Rules:
    1. **Strictly follow the Python dictionary format shown above.** Do NOT include any explanations, comments, or extra text outside the dictionary.
    2. **If any information is missing, set the value to `None`** (e.g., `"email": None`).
    3. **Ensure all string values are enclosed in double quotes ("").**
    4. The `"source"` field must always contain the source URL from which the data was extracted.
    5. **Do NOT invent or assume information**—only extract data that is explicitly available in the content.

    ### Example Output:
    {
        "url": "https://www.amphista.com",
        "name": "Amphista Therapeutics",
        "description": "A biotech company focused on targeted protein degradation.",
        "source": "https://www.nvfund.com/portfolio/amphista",
        "country": "United Kingdom",
        "city": "Cambridge",
        "email": None
    }

    Now, extract the information from the following content and return the output strictly in the same Python dictionary format:
    ---
'''


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
            messages=[{"role": "user", "content": f"{PROMPT}\n{text}"}]
        )
        return completion.choices[0].message.content


def get_llm(provider_name: str) -> LLMAPI:
    if provider_name == "openai":
        return OpenAIAPI()
    else:
        raise ValueError("Unsupported LLM")