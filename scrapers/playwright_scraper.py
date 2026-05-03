from playwright.sync_api import sync_playwright
import os
import requests
import time

def scrape_devfolio(page):
    page.goto("https://devfolio.co/hackathons")
    page.wait_for_timeout(3000)
    articles = []
    elements = page.query_selector_all("a[href*='/hackathons/']")
    for el in elements:
        title = el.text_content().strip()
        link = "https://devfolio.co" + el.get_attribute("href")
        if title:
            articles.append({
                "title": title,
                "link": link,
                "summary": "Hackathon on Devfolio",
                "published": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            })
    return {"source_name": "Devfolio", "articles": articles}

def scrape_unstop(page):
    page.goto("https://unstop.com/hackathons")
    page.wait_for_timeout(3000)
    articles = []
    return {"source_name": "Unstop", "articles": articles}

def scrape_luma(page):
    page.goto("https://lu.ma/explore")
    page.wait_for_timeout(3000)
    articles = []
    return {"source_name": "Luma Events", "articles": articles}

def main():
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    api_key = os.environ.get("API_KEY", "")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        sites = [scrape_devfolio, scrape_unstop, scrape_luma]
        for scraper_fn in sites:
            try:
                data = scraper_fn(page)
                if data["articles"]:
                    res = requests.post(
                        f"{api_url}/api/v1/ingest",
                        json=data,
                        headers={"X-API-KEY": api_key}
                    )
                    print(f"Posted {data['source_name']}: {res.status_code}")
            except Exception as e:
                print(f"Error scraping: {e}")
                
        browser.close()

if __name__ == "__main__":
    main()
