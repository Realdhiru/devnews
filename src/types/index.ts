export interface ArticleSource {
  name: string;
  url: string;
  favicon_url: string;
}

export interface ArticleCard {
  id: number;
  title: string;
  summary_short: string;
  summary_full: string;
  published_at: string;
  source_count: number;
  sources: ArticleSource[];
  categories: string[];
}

export interface FeedResponse {
  articles: ArticleCard[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface FeedState {
  articles: ArticleCard[];
  nextCursor: string | null;
  hasMore: boolean;
  isLoading: boolean;
  isLoadingMore: boolean;
  error: string | null;
  isCached: boolean;
  cachedAt: string | null;
  activeFilter: string | null;
  searchQuery: string;
  expandedCardId: number | null;
  availableFilters: string[];
}
