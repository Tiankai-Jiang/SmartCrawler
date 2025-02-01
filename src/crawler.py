from bs4 import BeautifulSoup
import requests

def extract_html(url):
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

url = "https://www.nvfund.com/portfolio/amphista"
clean_content = extract_html(url)
print(clean_content)