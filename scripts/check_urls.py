import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to check if a URL exists
def check_url_exists(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }
    try:
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
        if response.status_code in [403, 405]:  # Fallback if HEAD is blocked
            response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to process each company
def process_company(company, url):
    for path in ['portfolio/', 'companies/', 'company/']:
        if check_url_exists(url + path):
            return f"{company},{url},{url + path}"
    return f"{company},{url},,"

# Read URLs from file
res = []
with open('vcs_urls.csv', 'r') as file:
    lines = [line.strip() for line in file if not line.startswith('company')]

# Multithreading with ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(process_company, *line.split(',')) for line in lines]
    for future in as_completed(futures):
        result = future.result()
        res.append(result)
        if result.split(',')[-1]:
            print(result.split(',')[-1])

# Saving the results
with open('vcs_urls_portfolio.csv', 'w') as out_file:
    for entry in res:
        out_file.write(f"{entry}\n")
