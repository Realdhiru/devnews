from apscheduler.schedulers.background import BackgroundScheduler
import time
import random
from backend.database import get_db
from backend.scrapers import scrape_rss, scrape_html
from backend.pipeline import normalize_article, process_article, generate_tags
from backend.pipeline.deduplicator import get_embedding_bytes
import json
from datetime import datetime, timezone
import numpy as np

def job_wrapper(source_id, name, url, s_type, interval_minutes):
    scraped_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    source = {"name": name, "url": url}
    
    # Step 1: Scrape (no DB connection open during this)
    try:
        if s_type == "rss":
            raw_articles = scrape_rss(source)
        else:
            raw_articles = scrape_html(source)
    except Exception as e:
        print(f"Error scraping {name}: {e}")
        conn = get_db()
        try:
            conn.execute("""
            UPDATE scraper_status 
            SET last_scraped_at = CURRENT_TIMESTAMP, fail_count = fail_count + 1, last_error = ?
            WHERE source_id = ?
            """, (str(e), source_id))
            conn.commit()
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return

    # Step 2: Process articles in memory (no DB connection)
    from urllib.parse import urlparse
    processed = []
    for raw in raw_articles:
        normalized = normalize_article(raw, scraped_at)
        if not normalized:
            continue
        tags_info = generate_tags(normalized["title"], normalized["summary"])
        emb_bytes = get_embedding_bytes(normalized["title"])
        parsed = urlparse(normalized["original_url"])
        favicon_url = f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=32"
        processed.append({
            "normalized": normalized,
            "tags_info": tags_info,
            "emb_bytes": emb_bytes,
            "favicon_url": favicon_url
        })
    # Step 3: Open fresh DB connection and write everything
    conn = get_db()
    try:
        for item in processed:
            normalized = item["normalized"]
            tags_info = item["tags_info"]
            emb_bytes = item["emb_bytes"]
            favicon_url = item["favicon_url"]

            emb = np.frombuffer(emb_bytes, dtype=np.float32) if emb_bytes else None
            status = process_article(conn, normalized, embedding=emb)
            if status in ["duplicate", "discarded"]:
                continue

            cur = conn.execute("""
            INSERT INTO articles (source_id, title, summary, original_url, url_hash, embedding, primary_category, categories, tags, published_at, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                normalized["title"],
                normalized["summary"],
                normalized["original_url"],
                normalized["url_hash"],
                emb_bytes,
                tags_info["primary_category"],
                json.dumps(tags_info["categories"]),
                json.dumps(tags_info["tags"]),
                normalized["published_at"],
                normalized["scraped_at"]
            ))
            article_id = cur.lastrowid

            conn.execute(
                "INSERT INTO articles_fts (rowid, title, summary) VALUES (?, ?, ?)",
                (article_id, normalized["title"], normalized["summary"])
            )

            if status == "new":
                cur = conn.execute("""
                INSERT INTO grouped_stories (root_article_id, primary_category, categories, published_at, source_count)
                VALUES (?, ?, ?, ?, ?)
                """, (article_id, tags_info["primary_category"], json.dumps(tags_info["categories"]), normalized["published_at"], 1))
                group_id = cur.lastrowid
            else:
                group_id = int(status)
                conn.execute(
                    "UPDATE grouped_stories SET source_count = source_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (group_id,)
                )

            conn.execute("""
            INSERT INTO article_sources (group_id, article_id, source_name, source_url, favicon_url)
            VALUES (?, ?, ?, ?, ?)
            """, (group_id, article_id, name, normalized["original_url"], favicon_url))

        conn.execute("""
        UPDATE scraper_status 
        SET last_scraped_at = CURRENT_TIMESTAMP, last_success_at = CURRENT_TIMESTAMP, fail_count = 0
        WHERE source_id = ?
        """, (source_id,))
        conn.commit()

    except Exception as e:
        print(f"Error writing {name} to DB: {e}")
        try:
            conn.execute("""
            UPDATE scraper_status 
            SET last_scraped_at = CURRENT_TIMESTAMP, fail_count = fail_count + 1, last_error = ?
            WHERE source_id = ?
            """, (str(e), source_id))
            conn.commit()
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

def start_scheduler():
    scheduler = BackgroundScheduler()
    conn = get_db()
    try:
        cursor = conn.execute("""
            SELECT f.id, f.name, f.url, f.type, f.interval_minutes, s.last_scraped_at
            FROM feed_sources f
            LEFT JOIN scraper_status s ON f.id = s.source_id
            WHERE f.enabled = 1
        """)
        sources = cursor.fetchall()
        
        now_ts = time.time()
        
        for row in sources:
            sid, name, url, s_type, interval, last_scraped = row
            delay = 0
            if last_scraped:
                try:
                    last_dt = datetime.strptime(last_scraped, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
                    delay = max(0, (last_dt + interval * 60) - now_ts)
                except:
                    pass
                    
            delay += random.uniform(5, 10)
            
            scheduler.add_job(
                job_wrapper, 
                'interval', 
                minutes=interval, 
                kwargs={"source_id": sid, "name": name, "url": url, "s_type": s_type, "interval_minutes": interval},
                max_instances=1,
                next_run_time=datetime.fromtimestamp(now_ts + delay, timezone.utc)
            )
    finally:
        conn.close()
    
    scheduler.start()
    return scheduler
