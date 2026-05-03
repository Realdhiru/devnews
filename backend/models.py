from pydantic import BaseModel
from typing import List, Optional

class ArticleSource(BaseModel):
    name: str
    url: str
    favicon_url: str

class ArticleCard(BaseModel):
    id: int
    title: str
    summary_short: str
    summary_full: str
    published_at: str
    source_count: int
    sources: List[ArticleSource]
    categories: List[str]

class FeedResponse(BaseModel):
    articles: List[ArticleCard]
    next_cursor: Optional[str]
    has_more: bool

class IngestPayload(BaseModel):
    articles: List[dict]
    source_name: str
