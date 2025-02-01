from company import Company
from bs4 import BeautifulSoup
from llms import get_llm
import requests
import ast
import csv
import os

def extract_html(url: str) -> str:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

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

    combined_content = f"{general_text}\n\nHyperlinks:\n" + "\n".join(links)

    return combined_content


def save_to_csv(company: Company, filename="output.csv"):
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=company.model_dump().keys(), extrasaction='ignore')

        # Write headers only if file is new
        if not file_exists:
            writer.writeheader()

        writer.writerow(company.model_dump())

if __name__ == '__main__':
    llm = get_llm('openai')
    url = "https://www.nvfund.com/portfolio/amphista"
    clean_content = extract_html(url)
    # print(clean_content)
    # print()
    llm_output = llm.get_company_info(clean_content)
    try:
        data_dict = ast.literal_eval(llm_output)
    except (SyntaxError, ValueError) as e:
        print("Error parsing LLM output:", e)
    else:
        data_dict['source'] = url
        company = Company(**data_dict)
        save_to_csv(company)