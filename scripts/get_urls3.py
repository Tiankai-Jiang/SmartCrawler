import requests
from bs4 import BeautifulSoup
import time

# Function to get company details from the company page
def get_company_details(company_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(company_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve company details from {company_url}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    company_name_elem = soup.select_one('[id^="w-node-_1743f616-1944-660a-f988-fd98c0b7d554-"]')
    company_website_elem = soup.select_one('[id^="w-node-_917adf07-6cee-48b6-1f05-21810668e981-"] a')

    company_name = company_name_elem.get_text(strip=True) if company_name_elem else "N/A"
    company_website = company_website_elem['href'] if company_website_elem else "N/A"
    if not company_website.endswith('/'):
        company_website += '/'
    return company_name, company_website

# Read company URLs from file
with open("company_urls_uk.txt", "r") as file:
    all_company_urls = [line.strip() for line in file.readlines()]

# Collect company details
company_details = []
for url in all_company_urls:
    print(f"Scraping company details from {url}...")
    name, website = get_company_details(url)
    company_details.append({"Company Name": name, "Company URL": website})
    time.sleep(1)  # Be polite and avoid overloading the server

# Save the company details to a file
with open("company_details_uk.csv", "w") as file:
    for detail in company_details:
        file.write(f"{detail['Company Name']},{detail['Company URL']}\n")

print(f"Scraped details of {len(company_details)} companies.")
