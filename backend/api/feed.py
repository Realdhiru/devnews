import urllib.parse
from fastapi import APIRouter, Query, HTTPException
from backend.database import get_db
from backend.models import FeedResponse, ArticleCard, ArticleSource
from backend.cache import TTLCache
import base64
import json
import hashlib
import re

router = APIRouter()
cache = TTLCache(300)

# Pre-compiled regex for performance
JUNK_PATTERNS = [
    re.compile(r'Article URL:.*?(?=Comments URL:|$)', re.IGNORECASE | re.DOTALL),
    re.compile(r'Comments URL:.*?(?=Points:|$)', re.IGNORECASE | re.DOTALL),
    re.compile(r'Points: \d+.*?(?=# Comments:|$)', re.IGNORECASE | re.DOTALL),
    re.compile(r'# Comments: \d+.*', re.IGNORECASE | re.DOTALL),
    re.compile(r'\[link\].*$', re.IGNORECASE | re.MULTILINE),
    re.compile(r'\[comments\].*$', re.IGNORECASE | re.MULTILINE),
    re.compile(r'https?://\S+', re.IGNORECASE)
]
HTML_REGEX = re.compile(r'<[^>]+>')
WS_REGEX = re.compile(r'\s+')

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
            JOIN articles_fts f ON a.id = f.rowid
        """
        where_clauses.append("articles_fts MATCH ?")
        params.append(search)
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
        
        if not rows:
            return dict(articles=[], next_cursor=None, has_more=False)

        # Optimization: Fetch all sources for these groups in ONE query
        group_ids = [row[0] for row in rows]
        placeholders = ",".join(["?"] * len(group_ids))
        sources_cur = conn.execute(
            f"SELECT group_id, source_name, source_url, favicon_url FROM article_sources WHERE group_id IN ({placeholders})",
            tuple(group_ids)
        )
        
        sources_map = {}
        for s in sources_cur.fetchall():
            g_id = s[0]
            if g_id not in sources_map:
                sources_map[g_id] = []
            sources_map[g_id].append(ArticleSource(name=s[1], url=s[2], favicon_url=s[3] or ""))

        articles = []
        for row in rows:
            g_id = row[0]
            cat_list = json.loads(row[4]) if row[4] else []
            sources = sources_map.get(g_id, [])
            
            summary = row[7] or ""
            
            # Runtime cleanup for messy summaries (still needed for existing records)
            if "submitted by /u/" in summary:
                parts = summary.split(" [link] ")
                summary = parts[0]
                summary = summary.split("submitted by /u/")[0]
            
            for pattern in JUNK_PATTERNS:
                summary = pattern.sub('', summary)
            
            summary = HTML_REGEX.sub('', summary)
            summary = WS_REGEX.sub(' ', summary)
            summary = summary.strip()
            
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
