import feedparser
import time

def scrape_rss(source: dict) -> list:
    """Scrape RSS feeds and parse entries."""
    parsed = feedparser.parse(source['url'])
    articles = []
    
    if parsed.bozo and getattr(parsed.bozo_exception, 'getMessage', lambda: '')() != '':
        pass # bozo flag can be true for valid feeds with minor issues
        
    for entry in parsed.entries:
        try:
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', entry.get('description', ''))
            published = entry.get('published', entry.get('pubDate', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
            
            articles.append({
                "source_name": source['name'],
                "title": title,
                "link": link,
                "summary": summary,
                "published": published
            })
        except Exception as e:
            print(f"Error parsing RSS entry from {source['name']}: {e}")
            
    time.sleep(2)
    return articles
