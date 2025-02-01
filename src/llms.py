import os
import openai
import time
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import Optional

load_dotenv()

PROMPT = '''
    You are an expert in information extraction. Your task is to extract company information from the provided webpage content and return the data strictly in the following Python dictionary format:

    {
        "url": "<company_website_url>",
        "name": "<company_name>",
        "description": "<company_description>",
        "country": "<country>",
        "city": "<city>",
        "email": "<email_address>"
    }

    ### Important Rules:
    1. **Strictly follow the Python dictionary format shown above.** Do NOT include any explanations, comments, or extra text outside the dictionary.
    2. **If any information is missing, set the value to `None`** (e.g., `"email": None`).
    3. **Ensure all string values are enclosed in double quotes ("").**
    4. **Do NOT invent or assume information**—only extract data that is explicitly available in the content.
    5. **If a company has multiple pieces of information for the same field** (e.g., multiple countries or cities), **combine them into a single string separated by commas** (e.g., `"country": "USA, UK"`).
    6. **The above rule DOES NOT apply to the `url` field.**
    - Only extract **one valid URL** that represents the company's official website.
    - If multiple URLs are found, choose the one that best matches the company’s primary website.
    7. **For email addresses,** if there are multiple emails, combine them using commas (e.g., `"email": "info@example.com, contact@example.com"`).

    ### Example Output:
    {
        "url": "https://www.amphista.com",
        "name": "Amphista Therapeutics",
        "description": "A biotech company focused on targeted protein degradation.",
        "country": "United Kingdom, Switzerland",
        "city": "Cambridge, Zurich",
        "email": "info@amphista.com, contact@amphista.com"
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

    def get_company_info(self, text: str) -> Optional[str]:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": f"{PROMPT}\n{text}"}]
            )
            return completion.choices[0].message.content
        except openai.RateLimitError:
            print("Rate limit exceeded.")
            time.sleep(5) # may cause loop
            return self.get_company_info(text)
        except openai.APITimeoutError as e:
            print(f"Timeout Error: {e}")
        except openai.AuthenticationError as e:
            print(f"Authentication Error: {e}")
        except Exception as e:
            print(f"General LLM Error: {e}")


def get_llm(provider_name: str) -> LLMAPI:
    if provider_name == "openai":
        return OpenAIAPI()
    else:
        raise ValueError("Unsupported LLM")