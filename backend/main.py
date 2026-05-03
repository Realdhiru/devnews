from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.config import ALLOWED_ORIGINS
from backend.database import init_db
from backend.scheduler import start_scheduler
from backend.api import feed, health, ingest
from contextlib import asynccontextmanager
from backend.pipeline.deduplicator import get_model

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    try:
        get_model()
        print("Embedding model loaded successfully")
    except Exception as e:
        print(f"Model pre-warm failed: {e}")
    global scheduler
    scheduler = start_scheduler()
    yield
    # Shutdown
    if scheduler:
        scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*", "X-API-KEY"],
)

app.include_router(feed.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)
