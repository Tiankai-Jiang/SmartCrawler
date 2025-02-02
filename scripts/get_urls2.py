# https://vc-mapping.gilion.com/venture-capital-firms/united-states?bbfb7c17_page=1
# https://vc-mapping.gilion.com/venture-capital-firms/united-kingdom?6747233f_page=1
import requests
from bs4 import BeautifulSoup
import time

# Base URL for listing pages
# base_url = "https://vc-mapping.gilion.com/venture-capital-firms/united-states"
base_url = "https://vc-mapping.gilion.com/venture-capital-firms/united-kingdom"
# URL pattern for company details
detail_url_pattern = "https://vc-mapping.gilion.com/vc-firms/"

# Function to get company URLs from a single page
def get_company_urls(page_number):
    # page_url = f"{base_url}?bbfb7c17_page={page_number}"
    page_url = f"{base_url}?6747233f_page={page_number}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve page {page_number}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)

    company_urls = []
    for link in links:
        href = link['href']
        if href.startswith("/vc-firms/"):
            company_urls.append(f"https://vc-mapping.gilion.com{href}")

    return list(set(company_urls))  # Remove duplicates

# Collect company URLs from multiple pages
all_company_urls = []
page = 1

while page<5:
    print(f"Scraping page {page}...")
    urls = get_company_urls(page)
    if not urls:  # Stop if no companies are found on the page
        break
    all_company_urls.extend(urls)
    page += 1
    time.sleep(1)

# Remove duplicates from the final list
all_company_urls = list(set(all_company_urls))

# Save the URLs to a file
with open("company_urls_uk.txt", "w") as file:
    for url in all_company_urls:
        file.write(f"{url}\n")

print(f"Scraped {len(all_company_urls)} company URLs.")
