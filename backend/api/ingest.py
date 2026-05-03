from fastapi import APIRouter, Header, HTTPException
from backend.config import API_KEY
from backend.models import IngestPayload
from backend.database import get_db
from backend.pipeline import normalize_article, process_article, generate_tags
from backend.pipeline.deduplicator import get_embedding_bytes
import time
import json

router = APIRouter()

@router.post("/ingest")
def ingest_articles(payload: IngestPayload, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    conn = get_db()
    scraped_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    
    try:
        source_id_cur = conn.execute("SELECT id FROM feed_sources WHERE name = ?", (payload.source_name,))
        row = source_id_cur.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Unknown source")
        source_id = row[0]
            
        for raw in payload.articles:
            raw['source_name'] = payload.source_name
            normalized = normalize_article(raw, scraped_at)
            if not normalized:
                continue
                
            status = process_article(conn, normalized)
            if status in ["duplicate", "discarded"]:
                continue
                
            tags_info = generate_tags(normalized["title"], normalized["summary"])
            emb_bytes = get_embedding_bytes(normalized["title"])
            
            cur = conn.execute("""
            INSERT INTO articles (source_id, title, summary, original_url, url_hash, embedding, primary_category, categories, tags, published_at, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (source_id, normalized["title"], normalized["summary"], normalized["original_url"], normalized["url_hash"], emb_bytes, tags_info["primary_category"], json.dumps(tags_info["categories"]), json.dumps(tags_info["tags"]), normalized["published_at"], normalized["scraped_at"]))
            
            article_id = cur.lastrowid
            conn.execute("INSERT INTO articles_fts (rowid, title, summary) VALUES (?, ?, ?)", (article_id, normalized["title"], normalized["summary"]))
            
            from urllib.parse import urlparse
            parsed = urlparse(normalized["original_url"])
            favicon_url = f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=32"
            
            if status == "new":
                cur = conn.execute("""
                INSERT INTO grouped_stories (root_article_id, primary_category, categories, published_at, source_count)
                VALUES (?, ?, ?, ?, ?)
                """, (article_id, tags_info["primary_category"], json.dumps(tags_info["categories"]), normalized["published_at"], 1))
                group_id = cur.lastrowid
            else:
                group_id = int(status)
                conn.execute("UPDATE grouped_stories SET source_count = source_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (group_id,))
                
            conn.execute("""
            INSERT INTO article_sources (group_id, article_id, source_name, source_url, favicon_url)
            VALUES (?, ?, ?, ?, ?)
            """, (group_id, article_id, payload.source_name, normalized["original_url"], favicon_url))
            
        return {"status": "success"}
    finally:
        conn.commit()
        conn.close()
