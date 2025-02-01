import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

EXCLUDE_KEYWORDS = [
    "page", "about-us", "careers", "contact", "team", "news", "blog", "events",
    "jobs", "press", "leadership", "story", "media", "insights", "updates"
]

def should_exclude_url(url, portfolio_url):
    # Exclude if it's the same as the portfolio URL
    if url.rstrip("/") == portfolio_url.rstrip("/"):
        return True

    # Exclude vc.com/portfolio/?sector=20
    if urlparse(url).query:
        return True

    # Exclude URLs with unwanted keywords in the path
    path = urlparse(url).path.lower()
    if any(keyword in path for keyword in EXCLUDE_KEYWORDS):
        return True

    return False

def extract_internal_links(portfolio_url):
    keyword = portfolio_url.split('/')[-2]

    try:
        response = requests.get(portfolio_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        vc_domain = urlparse(portfolio_url).netloc  # Extract the VC domain

        internal_links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag['href'].strip()

            # Skip modals and JavaScript-based links
            if ("#" in href) or href.startswith("javascript:"):
                continue
            full_url = urljoin(portfolio_url, href)
            if should_exclude_url(full_url, portfolio_url):
                continue

            # Check if the link stays within the same VC domain
            if (urlparse(full_url).netloc == vc_domain) and (f"/{keyword}/" in full_url):
                internal_links.append(full_url)

        return list(set(internal_links))  # Remove duplicates

    except requests.exceptions.RequestException as e:
        print(f"Error accessing {portfolio_url}: {e}")
        return []

def process_portfolio(portfolio_url):
    internal_links = extract_internal_links(portfolio_url)
    return {portfolio_url: internal_links} if len(internal_links) > 1 else None

def parallel_crawl(portfolio_urls, max_workers=20):
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all portfolio URLs to be processed in parallel
        future_to_url = {executor.submit(process_portfolio, url): url for url in portfolio_urls}

        # As each thread completes, process the result
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                if data:
                    results.update(data)
            except Exception as e:
                print(f"Error processing {url}: {e}")

    return results

if __name__ == '__main__':

    with open('vcs_urls_portfolio.csv', 'r') as file:
        portfolio_urls = [line.strip().split(',')[-1] for line in file if not line.endswith(',\n')]

    # Run the parallel crawler
    results = parallel_crawl(portfolio_urls, max_workers=10)

    with open("startups.csv", "w") as f:
        f.write("vc,startup\n")
        for portfolio, companies in results.items():
            for company in companies:
                f.write(f"{portfolio},{company}\n")

# ['http://www.crv.com/companies/classpass', 'http://www.signalfire.com/portfolio/alchemy', 'http://www.flybridge.com/portfolio/www.aiera.com', 'http://streamlined.vc/companies/acquired', 'https://craftventures.com/portfolio/neuralink', 'https://www.dcvc.com/companies/paperspace', 'https://thirdsphere.com/portfolio/pre-seed/', 'http://tenoneten.net/portfolio/linker-finance', 'https://twosigmaventures.com/portfolio/company/hexagon-bio/', 'https://www.atoneventures.com/portfolio/puna-bio', 'http://www.congruentvc.com/portfolio/Omnidian', 'http://hyperplane.vc/companies/nwo.ai', 'http://www.linkventures.com/portfolio/smartertravel', 'http://www.qedinvestors.com/companies/coru', 'http://www.rre.com/portfolio/merlin', 'https://www.7pc.vc/portfolio/plotbox', 'http://www.406ventures.com/portfolio/ableto', 'http://wing.vc/companies/overt', 'https://avalanche.vc/portfolio/boundless-life', 'https://www.celesta.vc/portfolio/boom', 'http://www.draper.vc/companies/skybox', 'https://flourishventures.com/portfolio/frontier/', 'https://cake.vc/companies/shop-mcmullen', 'https://headline.com/portfolio/raisin', 'https://www.kaporcapital.com/portfolio/airprotein/', 'http://www.maveron.com/portfolio/allbirds', 'https://www.moonshotscapital.com/portfolio/threatcare/', 'https://www.scout.vc/companies/civitech', 'https://www.preludeventures.com/portfolio/encycle', 'https://type1ventures.com/portfolio/lunar-outpost', 'https://alleycorp.com/companies/gilt-groupe/', 'https://www.aera.vc/portfolio/climate/', 'https://buildingventures.com/companies/mezo/', 'http://www.differential.vc/portfolio/metafold', 'https://crossbeam.vc/portfolio/theambrgroup', 'http://goldengate.vc/portfolio/laku6', 'https://beepartners.vc/portfolio/florence-healthcare', 'https://femalefoundersfund.com/portfolio/rockets-of-awesome/', 'https://konvoy.vc/portfolio/stealth0922', 'https://www.panache.vc/portfolio/green-eye-technologies', 'https://seraphim.vc/portfolio/spire/', 'https://btn.vc/portfolio/', 'https://script.capital/portfolio/formx/', 'https://osageventurepartners.com/portfolio/rediq/', 'https://northzone.com/portfolio/trolltech/', 'https://www.wavemaker360.com/portfolio/giblib', 'https://www.wocstar.com/portfolio/project-five-jkmzy-3zf3l', 'https://www.wndrco.com/portfolio/twingate', 'https://ardent.vc/portfolio/method', 'https://www.bonfirevc.com/companies/honk', 'https://amplify.la/portfolio/carpay/', 'https://dynamo.vc/portfolio/starsky-robotics', 'http://www.corevc.com/portfolio/articles', 'https://www.equal.vc/portfolio/mvmnt', 'https://emerging.vc/portfolio/vectra', 'https://www.ivp.com/portfolio/mulesoft/', 'https://www.flexport.com/company/customers/', 'http://www.inspiredcapital.com/companies/niural', 'https://www.matchstick.vc/companies/liminal', 'https://www.longtermimpact.fund/companies/hilight', 'https://newmarketsvp.com/portfolio/censia/', 'https://OSS.Capital/portfolio/Bluesky', 'https://www.paleblue.vc/portfolio/phytoform', 'https://www.progression.fund/companies/appa', 'https://www.nextfrontiercapital.com/portfolio/about', 'https://www.questvp.com/portfolio/testmunk/', 'https://www.sequoiacap.com/companies/zoom/', 'http://longevity.vc/portfolio/about', 'https://www.truebeautyventures.com/portfolio/youthforia', 'https://www.worldfund.vc/portfolio/cylib', 'http://www.valorcapitalgroup.com/portfolio/companies', 'http://www.e14fund.com/companies/sourcemap', 'https://vvus.com/portfolio/cyberhaven/', 'https://www.energyfoundry.com/portfolio/3e-nano/', 'https://www.ylventures.com/portfolio/acceloweb/', 'http://www.nea.com/portfolio/perplexity', 'https://embedded.capital/portfolio/cais', 'https://www.khoslaventures.com/portfolio/square/', 'https://www.luxcapital.com/companies/maven', 'http://www.cowboy.vc/portfolio/area1', 'http://www.8vc.com/companies/hc-bioscience', 'http://www.indexventures.com/companies/backed/seed/', 'http://www.nfx.com/companies/gaming', 'https://www.sequoiacap.com/companies/zoom/', 'https://aifund.ai/portfolio/viavia/', 'https://www.cervin.com/portfolio/stackshare', 'https://www.dimensioncap.com/portfolio/kaleidoscope-bio', 'https://www.exceptionalcap.com/portfolio/portfolio/pixeltable', 'https://elevate.vc/portfolio/carpedm/', 'http://agfunder.com/portfolio/ai-palette/', 'https://kokopelli.vc/portfolio/advicepay/', 'http://kickstartfund.com/portfolio/keap', 'https://partechpartners.com/companies/akeneo', 'http://www.canaan.com/companies/truveris', 'https://www.paladincapgroup.com/portfolio/acalvio/', 'https://bigideaventures.com/portfolio/optimized-foods/', 'https://www.1011vc.com/portfolio/device-authority/', 'https://straydogcapital.com/portfolio/clever-carnivore/', 'https://wavemaker.vc/portfolio/portfolio-platform-pods-food-beverage/']
