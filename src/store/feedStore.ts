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

const DEMO_DATA: ArticleCard[] = [
  {
    id: 1,
    title: "Understanding React Compiler and the Future of UI Patterns",
    summary_short: "A deep dive into how the new React Compiler works under the hood and how it optimizes your code automatically.",
    summary_full: "A deep dive into how the new React Compiler works under the hood and how it optimizes your code automatically without memo or useMemo. We will explore the compilation steps and what it means for the future.",
    published_at: new Date().toISOString(),
    source_count: 1,
    sources: [{ name: "React Blog", url: "#", favicon_url: "" }],
    categories: ["Web Dev", "React"]
  },
  {
    id: 2,
    title: "Critical zero-day vulnerability in widely used infrastructure tool",
    summary_short: "Security researchers have disclosed a new high-severity vulnerability affecting millions of deployed instances.",
    summary_full: "Security researchers have disclosed a new high-severity vulnerability affecting millions of deployed instances. The bug allows unauthorized RCE if the service is exposed to the internet. Patch immediately.",
    published_at: new Date(Date.now() - 3600000).toISOString(),
    source_count: 4,
    sources: [
      { name: "KrebsOnSecurity", url: "#", favicon_url: "" },
      { name: "HackerNews", url: "#", favicon_url: "" }
    ],
    categories: ["Security"]
  },
  {
    id: 3,
    title: "Rust 1.76 brings new language features and performance boosts",
    summary_short: "The latest Rust release adds important standard library stabilization and improves compile times.",
    summary_full: "The latest Rust release adds important standard library stabilization and improves compile times. Among the features are improvements to the borrow checker and smaller binary sizes.",
    published_at: new Date(Date.now() - 7200000).toISOString(),
    source_count: 2,
    sources: [
      { name: "Rust Blog", url: "#", favicon_url: "" }
    ],
    categories: ["Open Source", "Tech"]
  }
];

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
      // Don't clear articles if we have cached data, just report error
      if (get().articles.length === 0) {
        set({ articles: [], availableFilters: [] });
      }
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
      // Initial cache load for instant visibility
      const cached = localStorage.getItem('devfeed_cache');
      if (cached) {
        const parsed = JSON.parse(cached);
        
        if (parsed.feed_data && parsed.feed_data.length > 0) {
          const UNWANTED_FILTERS = ["React", "Tech", "web dev", "Web Dev", "General", "GitHub Trending"];
          const rawFilters = Array.from(new Set(parsed.feed_data.flatMap((a: ArticleCard) => a.categories))) as string[];
          const newFilters = rawFilters.filter(f => f && f.length > 0 && !UNWANTED_FILTERS.includes(f)).sort();
          
          const cleanCached = (parsed.feed_data as ArticleCard[]).filter(a => 
            !a.categories.some(c => c === "GitHub Trending") && 
            a.source_name !== "GitHub Trending"
          );

          set({
            articles: cleanCached,
            isCached: true,
            cachedAt: parsed.timestamp || null,
            availableFilters: newFilters,
          });
        }
      }

      // Important: Always refresh from network on page load as requested
      set({ isLoading: true });
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
