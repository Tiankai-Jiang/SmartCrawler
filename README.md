# SmartCrawler

A startup company info crawler using LLM.



## Introduction

This Python project is built to scrape information about startup companies from venture capital websites. It extracts and processes key details such as company name, URL, location, and description using a large language model (LLM), then stores the data in a CSV file. Currently, the scraper is limited to startups that have dedicated pages on VC websites, such as [Amphista](https://www.nvfund.com/portfolio/amphista). It does not yet support scraping VC websites with extensive startup listings that rely heavily on JavaScript for content loading.

## Reqirements

- Python 3.10+
- Required libraries:
  - beautifulsoup4
  - openai
  - urllib3
  - requests

You can install the required libraries using the following command:

`pip install -r requirements.txt`

## Setup

After setting up the Python environment and installing the required dependencies, create a .env file in the project’s root directory. In this file, define the following parameters (currently only support openai api):

```
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=<openai-model-name> # e.g., gpt-4o-mini
```

Run the application:

```
cd src
python crawler.py
```

Add urls to the list in crawler.py as you wish. 

## Results

Tested on 254 **unique** VC websites, the scraper successfully generated 162 results. The list of websites can be found in the urls variable within crawler.py. Since these VC websites were initially gathered through web scraping, many were not suitable for testing from the start. Examples include: http://www.socialstarts.com/portfolio/everymove.org, http://www.valorcapitalgroup.com/portfolio/companies, http://www.techsquareventures.com/portfolio/privacy-policy, http://www.differential.vc/portfolio/category/Acquired, https://playfair.vc/companies/approach.php. By refining the list and removing such ineligible URLs in future iterations, the results are expected to improve.
