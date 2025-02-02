from bs4 import BeautifulSoup

with open('VCs.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Extract company names and websites from https://www.vcsheet.com/funds
companies = []

for item in soup.find_all('div', class_='list-card'):
    name_tag = item.find('h3', class_='list-heading')
    website_tag = item.find('a', class_='site-link')

    if name_tag and website_tag:
        name = name_tag.get_text(strip=True)
        website = website_tag['href'].strip()
        if 'http' not in website:
            continue
        if not website.endswith('/'):
            website += '/'
        companies.append((name, website))

with open("company_details_vcsheet.csv", "w") as f:
    f.write("company,url\n")
    for company in companies:
        f.write(f"{company[0]},{company[1]}\n")
        print(f'{company[0]} -- {company[1]}')