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
        where_clauses.append("(LOWER(a.title) LIKE ? OR LOWER(a.summary) LIKE ?)")
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
            
            articles.append(ArticleCard(
                id=g_id,
                title=row[6],
                summary_short=row[7],
                summary_full=row[7],
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
