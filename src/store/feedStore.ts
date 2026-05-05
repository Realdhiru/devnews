import { create } from 'zustand';
import { ArticleCard, FeedState } from '../types';
import { fetchArticles } from '../api/feedApi';

interface FeedActions {
  fetchFeed: (reset?: boolean) => Promise<void>;
  fetchMore: () => Promise<void>;
  setFilter: (filter: string | null) => void;
  setSearch: (query: string) => void;
  resetHome: () => void;
  toggleCard: (id: number) => void;
  loadFromCache: () => void;
  saveToCache: (articles: ArticleCard[]) => void;
}

export const useFeedStore = create<FeedState & FeedActions>((set, get) => ({
  articles: [],
  nextCursor: null,
  hasMore: true,
  isLoading: true,
  isLoadingMore: false,
  error: null,
  isCached: false,
  cachedAt: null,
  activeFilter: null,
  searchQuery: '',
  expandedCardId: null,
  availableFilters: [],

  fetchFeed: async (reset = false) => {
    if (reset) {
      set({ articles: [], nextCursor: null, hasMore: true, isLoading: true, error: null });
    } else {
      set({ isLoading: true, error: null });
    }
    
    try {
      const { activeFilter, searchQuery } = get();
      const response = await fetchArticles({
        filter: activeFilter,
        search: searchQuery
      });
      
      let fetchedArticles = response.articles;
      
      // Safety filter: ensure local filtering matches in case API is loose
      if (searchQuery) {
        const lowerSearch = searchQuery.toLowerCase();
        fetchedArticles = fetchedArticles.filter(a => 
          a.title.toLowerCase().includes(lowerSearch) || 
          (a.summary_short && a.summary_short.toLowerCase().includes(lowerSearch)) ||
          (a.summary_full && a.summary_full.toLowerCase().includes(lowerSearch))
        );
      }
      if (activeFilter) {
        fetchedArticles = fetchedArticles.filter(a => a.categories.includes(activeFilter));
      }

      // Gather unique categories from current results
      const currentResultFilters = Array.from(new Set(fetchedArticles.flatMap(a => a.categories)));
      
      // Filter out specifically requested 'unnecessary' or empty filters
      const UNWANTED_FILTERS = ["React", "Tech", "web dev", "Web Dev", "General", "GitHub Trending"];
      const filteredFilters = currentResultFilters.filter(f => 
        f && f.length > 0 && !UNWANTED_FILTERS.includes(f)
      );

      // Merge with existing filters
      const combinedFilters = Array.from(new Set([...get().availableFilters, ...filteredFilters]))
        .filter(f => f && f.length > 0 && !UNWANTED_FILTERS.includes(f))
        .sort();
      
      const filtersChanged = JSON.stringify(combinedFilters) !== JSON.stringify(get().availableFilters.sort());
      
      const cleanArticles = fetchedArticles.filter(a => 
        !a.categories.some(c => c === "GitHub Trending") && 
        a.source_name !== "GitHub Trending"
      );

      set({
        articles: cleanArticles,
        nextCursor: response.next_cursor,
        hasMore: response.has_more,
        isLoading: false,
        error: null,
        availableFilters: filtersChanged ? combinedFilters : get().availableFilters
      });
      get().saveToCache(fetchedArticles);
    } catch (e: any) {
      // If network fails, we keep showing whatever is in state (cached or empty)
      set({ isLoading: false, error: e.message || 'Failed to fetch feed' });
    }
  },

  fetchMore: async () => {
    const { nextCursor, hasMore, isLoadingMore, activeFilter, searchQuery, articles, error } = get();
    if (!hasMore || isLoadingMore || !nextCursor || error) return;

    set({ isLoadingMore: true });
    try {
      const response = await fetchArticles({
        cursor: nextCursor,
        filter: activeFilter,
        search: searchQuery
      });
      
      set({
        articles: [...articles, ...response.articles],
        nextCursor: response.next_cursor,
        hasMore: response.has_more,
        isLoadingMore: false
      });
    } catch (e: any) {
      set({ isLoadingMore: false });
    }
  },

  setFilter: (filter: string | null) => {
    set({ activeFilter: filter });
    get().fetchFeed(true);
  },

  setSearch: (query: string) => {
    set({ searchQuery: query });
    get().fetchFeed(true);
  },

  resetHome: () => {
    set({ activeFilter: null, searchQuery: '', expandedCardId: null });
    get().fetchFeed(true);
  },

  toggleCard: (id: number) => {
    // If clicking a new card, set it directly. If clicking the same card, toggle it.
    set({ expandedCardId: get().expandedCardId === id ? null : id });
  },

  loadFromCache: () => {
    try {
      // 1. Instantly show cached data if available for zero-wait startup
      const cached = localStorage.getItem('devfeed_cache');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed.feed_data && parsed.feed_data.length > 0) {
          const rawFilters = Array.from(new Set(parsed.feed_data.flatMap((a: ArticleCard) => a.categories))) as string[];
          const newFilters = rawFilters.filter(f => f && f !== "Other").sort();
          
          set({
            articles: parsed.feed_data,
            isCached: true,
            cachedAt: parsed.timestamp || null,
            availableFilters: newFilters,
            isLoading: false // Optimization: Hide skeletons if we have cache
          });
        }
      }

      // 2. ALWAYS trigger fresh fetch immediately
      get().fetchFeed(true);
    } catch (e) {
      set({ isLoading: true });
      get().fetchFeed(true);
    }
  },

  saveToCache: (articles: ArticleCard[]) => {
    try {
      if (articles.length > 0) {
        localStorage.setItem('devfeed_cache', JSON.stringify({
          feed_data: articles.slice(0, 50),
          timestamp: new Date().toISOString()
        }));
      }
    } catch (e) {
      // ignore quota exceeded etc
    }
  }
}));
