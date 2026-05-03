import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./devfeed.db")
DATABASE_AUTH_TOKEN = os.environ.get("DATABASE_AUTH_TOKEN", "")
API_KEY = os.environ.get("API_KEY", "dev-secret-key")
ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")]
ENV = os.environ.get("ENV", "development")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
