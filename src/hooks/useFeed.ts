import { useEffect } from 'react';
import { useFeedStore } from '../store/feedStore';

export const useFeed = () => {
  const fetchFeed = useFeedStore(state => state.fetchFeed);
  const loadFromCache = useFeedStore(state => state.loadFromCache);

  useEffect(() => {
    loadFromCache();
    fetchFeed();
  }, [fetchFeed, loadFromCache]);
};
