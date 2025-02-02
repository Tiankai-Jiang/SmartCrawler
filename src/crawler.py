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
    soup = BeautifulSoup(input_html, "html.parser") # lxml, html5lib

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
    #urls = ['https://www.foresitecapital.com/portfolio/myome-inc/', 'http://www.socialstarts.com/portfolio/everymove.org', 'https://www.1011vc.com/portfolio/axis-security/', 'http://www.wrvi.vc/portfolio/mojo-networks', 'https://www.kaporcapital.com/portfolio/adeptid/', 'http://www.TEXOventures.com/portfolio/www.sensentia.com', 'http://www.thirdpointventures.com/companies/kumu-networks', 'https://www.silvertonpartners.com/portfolio/vtel/', 'http://tenoneten.net/portfolio/locu', 'https://ardent.vc/portfolio/ecue', 'http://www.nvc.vc/portfolio/human-interest', 'https://www.momentventures.com/portfolio/stylar/', 'http://www.congruentvc.com/portfolio/Thrilling', 'http://www.alsop-louie.com/portfolio/socialcam', 'https://www.synventures.com/portfolio/revic/', 'http://www.maveron.com/portfolio/two-chairs', 'http://www.hwvp.com/companies/aria-systems', 'http://www.pivotinvestment.com/companies/card-com', 'http://www.starvestpartners.com/portfolio/portfolio', 'https://www.usvp.com/portfolio/nuance-communications-nuan/', 'http://www.aperturevp.com/portfolio/www.endotronix.com', 'https://www.cambridgespg.com/portfolio/lifeaid/', 'http://www.valorcapitalgroup.com/portfolio/companies', 'https://www.lyticalventures.com/companies/wand.ai', 'https://www.moonshotscapital.com/portfolio/threatcare/', 'https://parkway.vc/portfolio/sandbox-aq', 'https://www.137ventures.com/portfolio/workrise', 'https://www.wocstar.com/portfolio/project-one-ephnc-ge944', 'http://www.mercatopartners.com/portfolio/beam-benefits', 'http://www.heavybit.com/portfolio/runscope', 'https://tidemarkcap.com/portfolio/karbon', 'http://www.ethos.vc/portfolio/fantasmo', 'http://www.contrary.com/companies/anduril', 'https://www.levelonefund.com/portfolio/genies/', 'https://OSS.Capital/portfolio/spacedrive', 'https://www.pappas-capital.com/portfolio/bioatla/', 'https://www.truebeautyventures.com/portfolio/cay-skin', 'https://energytransitionventures.com/portfolio/dandelion-energy-launches-worlds-most-efficient-geothermal-heat-pump-nationwide/', 'http://www.ewhealthcare.com/portfolio/detail/velcera_inc', 'https://counterpart.vc/portfolio/oxide/', 'https://www.sequoiacap.com/companies/stripe/', 'http://www.techoperators.com/portfolio/scytale', 'http://www.techsquareventures.com/portfolio/privacy-policy', 'https://beliade.com/portfolio/ceremonia', 'https://gsquared.com/portfolio/meituan-dianping/', 'https://www.beechwoodcap.com/portfolio/shani-darden-skincare/', 'https://flyerone.vc/portfolio/competera', 'http://www.nextfrontiercapital.com/portfolio/pitch-us', 'https://www.paladincapgroup.com/portfolio/crossbow/', 'http://www.indexventures.com/companies/clumio/', 'http://www.camdenpartners.com/portfolio/medplus-inc', 'http://www.parafi.capital/portfolio/privacy-notice', 'http://www.scoutventures.com/companies/gelsight', 'https://www.ylventures.com/portfolio/hexadite/', 'http://www.blackbird.vc/portfolio/gilmour-space-technologies', 'http://www.translinkcapital.com/portfolio/klaytn', 'https://www.morgenthaler.com/information-technology/portfolio/software-services/', 'http://www.expertdojo.com/portfolio/www.mogiio.com', 'https://www.7wireventures.com/portfolio/caraway/', 'http://www.beringea.com/portfolio/atlas', 'https://www.fintopcapital.com/portfolio/qohash', 'https://www.silversmith.com/portfolio/mediquant', 'https://www.salesforce.com/company/sustainability/', 'http://www.emcap.com/portfolio/ironclad', 'https://elsewhere.partners/portfolio/upland', 'https://www.8vc.com/companies/branch', 'http://www.buildingventures.com/companies/join-digital/', 'http://www.meritechcapital.com/companies/category/healthcare', 'https://www.edisonpartners.com/portfolio/fingercheck', 'http://www.ascentvp.com/portfolio/sensitech/', 'http://matchstickventures.com/companies/two-boxes', 'http://www.vertexventures.com/portfolio/ambi-robotics/', 'http://www.e14fund.com/companies/payflow-digital', 'http://www.canaan.com/companies/alterego-networks', 'https://www.moltenventures.com/portfolio/focalpoint', 'http://www.armorysv.com/companies/qualifi', 'http://www.bfgpartners.com/portfolio/about', 'https://elevate.vc/portfolio/onboard-dynamics/', 'https://psl.com/companies/dropzone-ai', 'http://www.keiretsuforum.com/portfolio/www.exergyn.com', 'http://www.montageventures.com/companies/carefull', 'https://nrgvc.com/portfolio/inspace-1/', 'https://www.lrvhealth.com/portfolio/intelycare/', 'https://www.dallasvc.com/portfolio/blusapphire', 'https://emerging.vc/portfolio/kanari-ai', 'http://www.signalfire.com/portfolio/motion', 'http://www.wing.vc/companies/cumulus-networks', 'https://www.automotiveventures.com/portfolio/robotire', 'http://www.iacapgroup.com/portfolio/thezebra', 'http://dormroomfund.com/companies/www.sunrisehealth.co', 'http://www.differential.vc/portfolio/category/Acquired', 'https://www.agfunder.com/portfolio/Supplant/', 'http://p5hv.com/portfolio/cohero-health/', 'http://www.courtsidevc.com/portfolio/tap', 'http://www.leadedge.com/portfolio/nucleus/', 'https://unreasonablecapital.com/portfolio/o-list/', 'http://www.linkventures.com/portfolio/fountai-co', 'http://www.capitalg.com/portfolio/multiplan/', 'https://www.cotacapital.com/companies/orchestro-ai/', 'https://www.acm.com/portfolio/networking.html', 'https://www.406ventures.com/portfolio/cloudhealth_technologies', 'http://www.cataliocapital.com/portfolio/insightec', 'http://www.GrandBanksCapital.com/portfolio/software-and-services/', 'http://www.craftventures.com/portfolio/replit', 'https://www.flagshippioneering.com/companies/moderna', 'https://www.questvp.com/portfolio/dogvacay/', 'http://www.exeloncorp.com/companies/peco', 'http://www.mosaikpartners.com/companies/kor', 'http://www.crimsonseedcapital.com/portfolio/crashed-and-burned/', 'https://www.panache.vc/portfolio/dfuse-now-streaming-fast', 'https://goodai.capital/portfolio/portfolio', 'https://www.docusign.com/company/modern-slavery-act-statement', 'http://www.crv.com/companies/3t-biosciences', 'http://www.corevc.com/portfolio/impact-articles', 'https://www.progression.fund/companies/wavexr', 'http://www.equal.vc/portfolio/bikky', 'https://golden.ventures/portfolio/applyboard', 'http://www.bonfirevc.com/companies/archer-education', 'https://www.siliconbadia.com/portfolio/transcriptic/', 'https://www.volitioncapital.com/portfolio/automatiq/', 'http://www.streamlined.vc/companies/ipo', 'http://www.capitalfactory.com/portfolio/hawkdefense.com', 'http://www.interplay.vc/portfolio/acquire', 'https://www.wrvcapital.com/portfolio/healofy', 'http://www.xg-ventures.com/portfolio/exited/', 'https://www.bluestartups.com/portfolio/biteslice/', 'https://www.cervin.com/portfolio/celona', 'http://www.type1ventures.com/portfolio/space-forge', 'http://www.ivp.com/portfolio/lyra-health/', 'http://www.nfx.com/companies/proptech', 'http://www.flybridge.com/portfolio/www.dataxu.com', 'http://www.luxcapital.com/companies/auris-health', 'https://riceparkcapital.com/portfolio/blue-water/', 'https://www.uncommonvc.com/portfolio/dollar-shave-club/', 'https://www.arboretumvc.com/portfolio/convergent-dental/', 'https://www.floridafunders.com/portfolio/enrichly/', 'https://www.yashgodiwala.com/portfolio/Portfolio', 'https://www.anzupartners.com/portfolio/south-8-technologies/', 'https://higgrowth.com/portfolio/avi-spl/', 'http://www.gilead.com/company/board-of-directors/jacqueline-barton', 'https://www.freshtrackscap.com/portfolio/suncommon/', 'http://www.varanacapital.com/portfolio/portfolio', 'https://www.scalevp.com/portfolio/agari/', 'https://www.wavemaker360.com/portfolio/marigold-health', 'http://www.wndrco.com/portfolio/airtable', 'https://www.amfamventures.com/portfolio/hover/', 'https://www.augustcap.com/portfolio/active-funds/', 'https://www.founderscircle.com/companies/', 'http://www.alter.vc/portfolio/portfolio/cities/lahore', 'https://www.preludeventures.com/portfolio/sense', 'http://www.deltavcapital.com/portfolio/chownow', 'https://www.sageviewcapital.com/portfolio/loanstar/', 'http://www.headline.com/portfolio/pismo', 'https://twobearcapital.com/portfolio/fyr-diagnostics', 'http://www.scv.vc/portfolio/portfolio/', 'https://curate.capital/portfolio/to-the-market', 'https://www.clear-sky.com/portfolio/systems-control/', 'https://www.khoslaventures.com/portfolio/stripe/', 'http://www.kickstartfund.com/portfolio/keap', 'http://hyperplane.vc/companies/nwo.ai', 'http://www.qedinvestors.com/companies/aplazo', 'https://www.trinityventures.com/portfolio/property-capsule', 'https://www.heartlandvc.com/portfolio/strongarm-tech/', 'https://raphacap.com/portfolio/controlrad-inc/', 'http://www.cowboy.vc/portfolio/uplimit', 'https://www.atoneventures.com/portfolio/ascend-elements', 'https://ventures.rga.com/portfolio/freewire/', 'http://www.bullpencap.com/companies/enterprise/discover-more', 'http://www.inspiredcapital.com/companies/finix', 'http://www.nea.com/portfolio/patreon', 'http://www.rre.com/portfolio/rubric', 'https://www.orbimed.com/portfolio/', 'https://smartfinvc.com/portfolio/divitel/', 'https://www.ascension.vc/portfolio/qur8/', 'https://www.oxx.vc/portfolio/kodiak-hub/', 'http://www.eternacapital.com/portfolio/legal/terms-and-conditions', 'http://www.true.global/portfolio/mishipay/', 'https://openocean.vc/portfolio/oppex', 'http://www.dawncapital.com/portfolio/privacy-policy', 'http://www.connectventures.co/companies/colossal', 'https://www.conceptventures.vc/portfolio/chatterbox', 'https://www.activantcapital.com/companies/deuna', 'https://seraphim.vc/portfolio/astrosale/', 'https://playfair.vc/companies/approach.php', 'http://www.blossomcap.com/portfolio/theydo', 'https://rlc.ventures/portfolio/gendo', 'http://www.localglobe.vc/localglobe/companies/travelperk', 'https://notion.vc/portfolio/shutl', 'https://www.dcvc.com/companies/dronedeploy', 'https://www.mourocapital.com/portfolio/clikalia/', 'https://www.fabric.vc/portfolio/ntropy-network', 'https://craftventures.com/portfolio/cloud9', 'http://streamlined.vc/companies/ipo', 'https://www.ahreninnovationcapital.com/companies/bitfount/', 'https://twosigmaventures.com/portfolio/company/glide/', 'https://avalanche.vc/portfolio/boundless-life', 'http://www.406ventures.com/portfolio/ableto', 'http://wing.vc/companies/deepsight', 'https://www.7pc.vc/portfolio/volta', 'https://www.celesta.vc/portfolio/crescendo', 'https://cake.vc/companies/guaranteed', 'http://www.draper.vc/companies/cytotronics', 'https://headline.com/portfolio/honeycomb', 'https://www.scout.vc/companies/encharge-ai', 'https://flourishventures.com/portfolio/insurtech/', 'https://alleycorp.com/companies/stepful/', 'https://type1ventures.com/portfolio/active-surfaces', 'https://www.heavybit.com/portfolio/mobot', 'https://www.preludeventures.com/portfolio/sense', 'https://buildingventures.com/companies/blokable/', 'https://www.aera.vc/portfolio/climate/', 'http://goldengate.vc/portfolio/ninjavan', 'https://crossbeam.vc/portfolio/common-trust', 'https://konvoy.vc/portfolio/pok-pok', 'https://femalefoundersfund.com/portfolio/entrypoint/', 'https://beepartners.vc/portfolio/tensorstax', 'https://osageventurepartners.com/portfolio/rackware/', 'https://script.capital/portfolio/sqreen/', 'https://northzone.com/portfolio/sellersfunding/', 'https://btn.vc/portfolio/hivewealth-2-2/', 'https://www.wavemaker360.com/portfolio/marigold-health', 'https://www.wndrco.com/portfolio/aura', 'https://www.bonfirevc.com/companies/boulevard', 'https://www.equal.vc/portfolio/ghost', 'https://dynamo.vc/portfolio/seeva', 'https://amplify.la/portfolio/upwards/', 'https://www.flexport.com/company/global-network/', 'https://www.ivp.com/portfolio/dataai/', 'https://www.matchstick.vc/companies/optera', 'https://www.longtermimpact.fund/companies/hilight', 'https://www.nextfrontiercapital.com/portfolio/about', 'https://newmarketsvp.com/portfolio/datapeople/', 'https://www.paleblue.vc/portfolio/phytoform', 'https://www.sequoiacap.com/companies/stripe/', 'http://longevity.vc/portfolio/portfolio', 'https://vvus.com/portfolio/Vividly/', 'https://www.luxcapital.com/companies/chronosphere', 'https://www.ylventures.com/portfolio/hexadite/', 'http://www.8vc.com/companies/epirus', 'https://www.worldfund.vc/portfolio/sunroof', 'https://aifund.ai/portfolio/jivi-ai/', 'https://www.cervin.com/portfolio/celona', 'https://www.dimensioncap.com/portfolio/kaleidoscope-bio', 'https://embedded.capital/portfolio/wilshire', 'https://elevate.vc/portfolio/onboard-dynamics/', 'https://www.exceptionalcap.com/portfolio/portfolio/lumu', 'https://kokopelli.vc/portfolio/comsero/', 'http://kickstartfund.com/portfolio/peoplekeep', 'http://agfunder.com/portfolio/eion/', 'https://partechpartners.com/companies/brevo', 'https://bigideaventures.com/portfolio/the-frauxmagerie/', 'https://www.1011vc.com/portfolio/axis-security/', 'https://straydogcapital.com/portfolio/4ag/', 'https://wavemaker.vc/portfolio/portfolio-location-pods-wavemaker-portfolio-headquarter-hong-kong/']
    llm_client = get_llm('openai')
    for url in urls:
        process_company(url, llm_client)
        time.sleep(1)
