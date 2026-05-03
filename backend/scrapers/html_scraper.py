import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "DevNewsBot/1.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def scrape_html(source: dict) -> list:
    name = source.get("name", "")
    url = source.get("url", "")

    if "github.com/trending" in url:
        return scrape_github_trending(url, name)
    elif "summerofcode.withgoogle.com" in url:
        return scrape_gsoc(url, name)
    else:
        return scrape_generic(url, name)


def scrape_github_trending(url: str, source_name: str) -> list:
    try:
        resp = requests.get(
            "https://github.com/trending",
            headers=HEADERS,
            timeout=30
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for repo in soup.select("article.Box-row"):
            try:
                # Repo name
                h2 = repo.select_one("h2.h3 a")
                if not h2:
                    continue
                repo_path = h2.get("href", "").strip("/")
                if not repo_path or repo_path.count("/") != 1:
                    continue
                title = repo_path

                # Description
                desc_el = repo.select_one("p.col-9")
                description = desc_el.get_text(strip=True) if desc_el else ""

                # Language
                lang_el = repo.select_one("[itemprop='programmingLanguage']")
                language = lang_el.get_text(strip=True) if lang_el else ""

                # Stars
                stars_el = repo.select_one("a[href$='/stargazers']")
                stars = stars_el.get_text(strip=True) if stars_el else ""

                summary = description
                if not summary:
                    parts = []
                    if language:
                        parts.append(f"Language: {language}")
                    if stars:
                        parts.append(f"Stars: {stars}")
                    summary = " · ".join(parts) if parts else "Trending on GitHub today"

                articles.append({
                    "title": title,
                    "summary": summary,
                    "url": f"https://github.com/{repo_path}",
                    "source_name": source_name,
                    "published": None
                })
            except Exception:
                continue

        time.sleep(2)
        return articles

    except Exception as e:
        print(f"GitHub Trending scrape error: {e}")
        return []


def scrape_gsoc(url: str, source_name: str) -> list:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for el in soup.select("a[href*='/programs/']")[:10]:
            title = el.get_text(strip=True)
            href = el.get("href", "")
            if not title or not href:
                continue
            full_url = href if href.startswith("http") else f"https://summerofcode.withgoogle.com{href}"
            articles.append({
                "title": f"GSoC: {title}",
                "summary": "Google Summer of Code program announcement",
                "url": full_url,
                "source_name": source_name,
                "published": None
            })

        return articles
    except Exception as e:
        print(f"GSoC scrape error: {e}")
        return []


def scrape_generic(url: str, source_name: str) -> list:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for a in soup.select("a[href]")[:20]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if len(title) < 20 or not href.startswith("http"):
                continue
            articles.append({
                "title": title,
                "summary": "",
                "url": href,
                "source_name": source_name,
                "published": None
            })

        return articles
    except Exception as e:
        print(f"Generic scrape error: {e}")
        return []