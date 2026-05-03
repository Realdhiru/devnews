import { useEffect, useRef } from 'react';

export const useInfiniteScroll = (
  callback: () => Promise<void>,
  hasMore: boolean,
  isLoadingMore: boolean
) => {
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (observerRef.current) observerRef.current.disconnect();

    observerRef.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !isLoadingMore && hasMore) {
        callback();
      }
    });

    if (sentinelRef.current) observerRef.current.observe(sentinelRef.current);

    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [callback, hasMore, isLoadingMore]);

  return sentinelRef;
};
