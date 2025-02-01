import requests
import ast
import csv
import os
import pydantic
from company import Company
from bs4 import BeautifulSoup
from llms import get_llm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict

def get_html(url: str) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
    }
    try:
        adapter = HTTPAdapter(max_retries=Retry(
            total=3,
            backoff_factor=1,      # Wait 1s, 2s, 4s between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        ))
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise error for bad status codes (4xx/5xx)
        return response.text

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh} for URL: {url}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Connection Error: {errc} for URL: {url}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt} for URL: {url}")
    except requests.exceptions.RequestException as err:
        print(f"Unexpected Error: {err} for URL: {url}")

def extract_html(input_html: str) -> str:
    soup = BeautifulSoup(input_html, "html.parser")

    # Remove unnecessary tags
    for tag in soup(["script", "style", "noscript", "meta", "header", "footer"]):
        tag.extract()

    general_text = soup.get_text(separator=" ", strip=True)

    links = []
    for link in soup.find_all("a", href=True):  # Only <a> tags with href attribute
        href = link["href"]
        link_text = link.get_text(strip=True)

        # Skip empty links
        if href and link_text:
            links.append(f"{link_text}: {href}")

    cleaned_content = f"Texts:\n{general_text}\n\nHyperlinks:\n" + "\n".join(links)

    return cleaned_content

def parse_llm_output(llm_output: str) -> Optional[Dict]:
    try:
        return ast.literal_eval(llm_output)
    except (SyntaxError, ValueError) as e:
        print(llm_output)
        print("Error parsing LLM output:", e)
    except Exception as e:
        print(llm_output)
        print(f"Unexpected Error while parsing LLM output: {e}")

def validate_data(data: Dict) -> Optional[Company]:
    try:
        company = Company(**data)
        return company
    except pydantic.ValidationError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

def save_to_csv(company: Company, filename: str):
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=company.model_dump().keys(), extrasaction='ignore')

        # Write headers only if file is new
        if not file_exists:
            writer.writeheader()

        writer.writerow(company.model_dump())

def process_company(url: str, llm_client, output_filename="output.csv"):
    print(f"Processing: {url}", end='\n\n')

    # get raw html contents
    raw_html_content = get_html(url)
    if not raw_html_content:
        return

    # extract only texts and urls from html
    clean_content = extract_html(raw_html_content)
    print(clean_content, end='\n\n')

    # LLM extraction
    llm_output = llm_client.get_company_info(clean_content)
    if not llm_output:
        return

    # convert to dict
    data_dict = parse_llm_output(llm_output)
    if not data_dict:
        return
    data_dict['source'] = url

    # pydantic validation
    company = validate_data(data_dict)
    if not company:
        return

    # save to csv
    save_to_csv(company, output_filename)
    print(f"Successfully processed: {url}")


if __name__ == '__main__':
    url = "https://www.nvfund.com/portfolio/anokion"
    llm_client = get_llm('openai')
    process_company(url, llm_client)
