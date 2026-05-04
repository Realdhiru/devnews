import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import bleach
from dateutil.parser import parse as parse_date
import time
from datetime import datetime, timezone

def normalize_article(raw: dict, scraped_at: str) -> dict:
    title = raw.get('title', '')
    title = bleach.clean(title, tags=[], strip=True).strip()[:300]
    
    if not title:
        return None
        
    summary = raw.get('summary', '')
    
    import re
    # 1. Reddit cleanup
    if "submitted by /u/" in summary:
        if " [link] " in summary:
            summary = summary.split(" [link] ")[0]
        if "submitted by /u/" in summary:
            summary = summary.split("submitted by /u/")[0]
            
    # 2. Remove Hacker News / RSS metadata junk
    junk_patterns = [
        r'Article URL:.*$',
        r'Comments URL:.*$',
        r'Points: \d+.*$',
        r'# Comments: \d+.*$',
        r'\[link\].*$',
        r'\[comments\].*$'
    ]
    for pattern in junk_patterns:
        summary = re.sub(pattern, '', summary, flags=re.IGNORECASE | re.MULTILINE)

    # 3. Re-clean HTML
    summary = bleach.clean(summary, tags=[], strip=True)
    
    # 4. Strip URLs
    summary = re.sub(r'https?://\S+', '', summary)
    
    # 5. Normalize whitespace
    summary = re.sub(r'\s+', ' ', summary)
    
    summary = summary.strip()[:400]
    
    # Fallback
    if not summary or summary.isspace() or len(summary) < 5:
        summary = "Story published. See sources for details."
    
    url = raw.get('link', '')
    if not url:
        return None
        
    try:
        parsed = urlparse(url)
        # remove utm params
        query = parse_qs(parsed.query)
        query = {k: v for k, v in query.items() if not k.startswith('utm_')}
        clean_query = urlencode(query, doseq=True)
        # normalize
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/')
        url = urlunparse((parsed.scheme, netloc, path, parsed.params, clean_query, ''))
    except:
        return None
        
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    
    pub_date_str = raw.get('published', scraped_at)
    try:
        dt = parse_date(pub_date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        now = datetime.now(timezone.utc)
        if dt > now:
            dt = now
            
        published_at = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except:
        published_at = scraped_at

    return {
        "title": title,
        "summary": summary,
        "original_url": url,
        "url_hash": url_hash,
        "source_name": raw.get('source_name', 'Unknown'),
        "published_at": published_at,
        "scraped_at": scraped_at
    }
