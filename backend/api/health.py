from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
def healthz():
    return {"status": "ok"}

@router.get("/admin/health")
def admin_health():
    from backend.database import get_db
    conn = get_db()
    cursor = conn.execute("""
        SELECT f.name, s.last_scraped_at, s.last_success_at, s.fail_count, s.last_error
        FROM feed_sources f
        LEFT JOIN scraper_status s ON f.id = s.source_id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append({
            "name": r[0],
            "last_scraped_at": r[1],
            "last_success_at": r[2],
            "fail_count": r[3] if r[3] is not None else 0,
            "last_error": r[4],
            "status": "healthy" if (r[3] is None or r[3] < 5) else "degraded"
        })
    return results
