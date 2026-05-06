import libsql_experimental as libsql
import yaml
from .config import DATABASE_URL, DATABASE_AUTH_TOKEN
import os

def get_db():
    conn = libsql.connect(DATABASE_URL, auth_token=DATABASE_AUTH_TOKEN)
    return conn

def init_db():
    conn = get_db()
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS feed_sources (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      url TEXT NOT NULL,
      type TEXT NOT NULL,
      category TEXT NOT NULL,
      interval_minutes INTEGER NOT NULL,
      enabled INTEGER DEFAULT 1,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_id INTEGER,
      title TEXT NOT NULL,
      summary TEXT,
      original_url TEXT NOT NULL,
      url_hash TEXT UNIQUE NOT NULL,
      embedding BLOB,
      primary_category TEXT,
      categories TEXT,
      tags TEXT,
      published_at TIMESTAMP,
      scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (source_id) REFERENCES feed_sources(id)
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS grouped_stories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      root_article_id INTEGER,
      primary_category TEXT,
      categories TEXT,
      published_at TIMESTAMP,
      source_count INTEGER DEFAULT 1,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (root_article_id) REFERENCES articles(id)
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS article_sources (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      group_id INTEGER,
      article_id INTEGER,
      source_name TEXT,
      source_url TEXT,
      favicon_url TEXT,
      FOREIGN KEY (group_id) REFERENCES grouped_stories(id),
      FOREIGN KEY (article_id) REFERENCES articles(id)
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS scraper_status (
      source_id INTEGER PRIMARY KEY,
      last_scraped_at TIMESTAMP,
      last_success_at TIMESTAMP,
      fail_count INTEGER DEFAULT 0,
      last_error TEXT,
      FOREIGN KEY (source_id) REFERENCES feed_sources(id)
    );
    """)

    conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
      title,
      summary,
      content='articles',
      content_rowid='id'
    );
    """)

    # Triggers to keep FTS table in sync
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
      INSERT INTO articles_fts(rowid, title, summary) VALUES (new.id, new.title, new.summary);
    END;
    """)
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
      INSERT INTO articles_fts(articles_fts, rowid, title, summary) VALUES('delete', old.id, old.title, old.summary);
    END;
    """)
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
      INSERT INTO articles_fts(articles_fts, rowid, title, summary) VALUES('delete', old.id, old.title, old.summary);
      INSERT INTO articles_fts(rowid, title, summary) VALUES (new.id, new.title, new.summary);
    END;
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_grouped_published_at ON grouped_stories(published_at DESC);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_article_sources_group_id ON article_sources(group_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_primary_category ON articles(primary_category);")

    sources_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sources.yaml")
    if os.path.exists(sources_path):
        try:
            with open(sources_path, "r") as f:
                data = yaml.safe_load(f)
                for source in data.get("sources", []):
                    # We use standard string formatting as libsql might not support full named params depending on bindings
                    conn.execute("""
                    INSERT INTO feed_sources (name, url, type, category, interval_minutes, enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        url=excluded.url,
                        type=excluded.type,
                        category=excluded.category,
                        interval_minutes=excluded.interval_minutes,
                        enabled=excluded.enabled,
                        updated_at=CURRENT_TIMESTAMP;
                    """, (source["name"], source["url"], source["type"], source["category"], source["interval_minutes"], 1 if source.get("enabled", True) else 0))
                    
                    conn.execute("""
                    INSERT OR IGNORE INTO scraper_status (source_id)
                    SELECT id FROM feed_sources WHERE name = ?;
                    """, (source["name"],))
        except Exception as e:
            print(f"Error seeding sources: {e}")
            
    conn.execute("""
    INSERT INTO articles_fts(rowid, title, summary) 
    SELECT id, title, summary FROM articles 
    WHERE id NOT IN (SELECT rowid FROM articles_fts);
    """)

    conn.commit()
    conn.close()
