import urllib.parse
from fastapi import APIRouter, Query
from backend.database import get_db
from backend.models import FeedResponse, ArticleCard, ArticleSource
from backend.cache import TTLCache
import base64
import json
import hashlib

router = APIRouter()
cache = TTLCache(300)

def encode_cursor(published_at, doc_id):
    raw = f"{published_at}|{doc_id}"
    return base64.b64encode(raw.encode()).decode()

def decode_cursor(cursor):
    if not cursor:
        return None, None
    try:
        raw = base64.b64decode(cursor.encode()).decode()
        timestamp, doc_id = raw.rsplit("|", 1)
        return timestamp, int(doc_id)
    except:
        return None, None

@router.get("/articles", response_model=FeedResponse)
def get_articles(
    cursor: str = None, 
    limit: int = Query(20, le=50), 
    filter: str = None, 
    search: str = Query(None, max_length=100)
):
    cache_key = hashlib.md5(f"{cursor}-{limit}-{filter}-{search}".encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return cached

    conn = get_db()
    ts, c_id = decode_cursor(cursor)
    
    params = []
    where_clauses = []
    
    if search:
        query = """
            SELECT g.id, g.root_article_id, g.published_at, g.primary_category, g.categories, g.source_count,
                   a.title, a.summary
            FROM grouped_stories g
            JOIN articles a ON g.root_article_id = a.id
        """
        where_clauses.append("(LOWER(a.title) LIKE ? OR LOWER(COALESCE(a.summary, '')) LIKE ?)")
        params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
    else:
        query = """
            SELECT g.id, g.root_article_id, g.published_at, g.primary_category, g.categories, g.source_count,
                   a.title, a.summary
            FROM grouped_stories g
            JOIN articles a ON g.root_article_id = a.id
        """
        
    if filter:
        where_clauses.append("(g.primary_category = ? OR g.categories LIKE ?)")
        params.extend([filter, f'%"{filter}"%'])
        
    if ts and c_id:
        where_clauses.append("(g.published_at < ? OR (g.published_at = ? AND g.id < ?))")
        params.extend([ts, ts, c_id])
        
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    query += " ORDER BY g.published_at DESC, g.id DESC LIMIT ?"
    params.append(limit)
    
    try:
        cursor_db = conn.execute(query, tuple(params))
        rows = cursor_db.fetchall()
        
        articles = []
        for row in rows:
            g_id = row[0]
            cat_list = json.loads(row[4]) if row[4] else []
            
            src_cur = conn.execute("SELECT source_name, source_url, favicon_url FROM article_sources WHERE group_id = ?", (g_id,))
            sources = [ArticleSource(name=s[0], url=s[1], favicon_url=s[2] or "") for s in src_cur.fetchall()]
            
            summary = row[7] or ""
            # Runtime cleanup for messy summaries
            import re
            
            # 1. Remove Reddit junk
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
            
            # 3. Clean HTML and URLs
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = re.sub(r'https?://\S+', '', summary)
            
            # 4. Normalize whitespace
            summary = re.sub(r'\s+', ' ', summary)
            summary = summary.strip()
            
            # 5. Cap and fallback
            if len(summary) > 400:
                summary = summary[:397] + "..."
            
            if not summary or summary.isspace() or len(summary) < 5:
                summary = "Detailed story available at the source links below."

            articles.append(ArticleCard(
                id=g_id,
                title=row[6],
                summary_short=summary,
                summary_full=summary,
                published_at=row[2],
                source_count=row[5],
                sources=sources,
                categories=cat_list
            ))
            
        has_more = len(articles) == limit
        next_cursor = encode_cursor(articles[-1].published_at, articles[-1].id) if articles else None
        
        resp = dict(articles=articles, next_cursor=next_cursor, has_more=has_more)
        cache.set(cache_key, resp)
        return resp
        
    finally:
        conn.close()
