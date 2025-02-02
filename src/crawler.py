import requests
import ast
import csv
import os
import pydantic
import time
from company import Company
from bs4 import BeautifulSoup
from llms import get_llm
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict
from logger import get_logger

logger = get_logger(__name__)

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
        logger.error(f"HTTP Error: {errh} for URL: {url}")
    except requests.exceptions.ConnectionError as errc:
        logger.error(f"Connection Error: {errc} for URL: {url}")
    except requests.exceptions.Timeout as errt:
        logger.error(f"Timeout Error: {errt} for URL: {url}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Unexpected Error: {err} for URL: {url}")

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

    return f"Texts:\n{general_text}\n\nHyperlinks:\n" + "\n".join(links)

def parse_llm_output(llm_output: str) -> Optional[Dict]:
    try:
        return ast.literal_eval(llm_output)
    except (SyntaxError, ValueError) as e:
        logger.debug(llm_output)
        logger.error("Error parsing LLM output:", e)
    except Exception as e:
        logger.debug(llm_output)
        logger.error(f"Unexpected Error while parsing LLM output: {e}")

def validate_url_email(data_dict: Dict, source_url: str) -> Dict:
    data_dict['source'] = source_url

    # vc and startup has the same domain, that means llm extracted wrong info
    # "https://www.dcvc.com/companies/platfora/"
    parsed_url = urlparse(source_url)
    if parsed_url.netloc == urlparse(data_dict['url']).netloc:
        logger.warning(f'No valid url for company from {source_url}')
        data_dict['url'] = None

    # vc and startup email has the same domain, that means llm extracted wrong info
    # "https://btn.vc/portfolio/hivewealth-2/"
    # "https://www.preludeventures.com/portfolio/atom-computing"
    if data_dict['email'] is not None:
        source_domain = parsed_url.netloc or parsed_url.path # no http
        if source_domain.startswith('www.'): # remove www. to compare with email domain
            source_domain = source_domain[4:]
        good_emails = [x for x in data_dict['email'].split(',') if x.split('@')[-1].strip() != source_domain]
        if good_emails:
            data_dict['email'] = ','.join(good_emails)
        else:
            data_dict['email'] = None


def validate_data(data: Dict) -> Optional[Company]:
    try:
        company = Company(**data)
        return company
    except pydantic.ValidationError as e:
        logger.error(f"Validation Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")

def save_to_csv(company: Company, filename: str):
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=company.model_dump().keys(), extrasaction='ignore')

        # Write headers only if file is new
        if not file_exists:
            writer.writeheader()

        writer.writerow(company.model_dump())

def process_company(url: str, llm_client, output_filename="output.csv"):
    logger.info(f"Processing: {url}")

    # get raw html contents
    raw_html_content = get_html(url)
    if not raw_html_content:
        return

    # extract only texts and urls from html
    clean_content = extract_html(raw_html_content)
    logger.debug(clean_content)

    # LLM extraction
    llm_output = llm_client.get_company_info(clean_content)
    if not llm_output:
        return

    # convert to dict
    data_dict = parse_llm_output(llm_output)
    if not data_dict:
        return

    # check on source url, startup url and startup email
    validate_url_email(data_dict, url)

    # pydantic validation
    company = validate_data(data_dict)
    if not company:
        return

    # save to csv
    save_to_csv(company, output_filename)
    logger.info(f"Successfully processed: {url}")


if __name__ == '__main__':
    urls = ["https://www.nvfund.com/portfolio/anokion"]
    llm_client = get_llm('openai')
    for url in urls:
        process_company(url, llm_client)
        time.sleep(1)
