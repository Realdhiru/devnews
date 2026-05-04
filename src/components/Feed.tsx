import React from 'react';
import { useFeedStore } from '../store/feedStore';
import { Card } from './Card';
import { SkeletonCard } from './SkeletonCard';
import { useInfiniteScroll } from '../hooks/useInfiniteScroll';

export const Feed: React.FC = () => {
  const { articles, isLoading, isLoadingMore, hasMore, error, isCached, expandedCardId, toggleCard, fetchMore } = useFeedStore();
  
  const sentinelRef = useInfiniteScroll(fetchMore, hasMore, isLoadingMore);

  const showSkeletons = isLoading && !isCached && articles.length === 0;

  // To maintain vertical isolation, we need to distribute items into columns.
  // For simplicity and total stability, we'll use 3 column containers.
  // On mobile (<768px): 1 column (all articles)
  // On tablet (>=768px && <1024px): 2 columns (even/odd)
  // On desktop (>=1024px): 3 columns (0, 1, 2 distribution)
  
  const col1_3 = articles.filter((_, i) => i % 3 === 0);
  const col2_3 = articles.filter((_, i) => i % 3 === 1);
  const col3_3 = articles.filter((_, i) => i % 3 === 2);

  const col1_2 = articles.filter((_, i) => i % 2 === 0);
  const col2_2 = articles.filter((_, i) => i % 2 === 1);

  return (
    <div className="max-w-7xl mx-auto pb-20 min-h-screen bg-[#0a0a0a] w-full pt-20 md:pt-8">
      {/* Mobile Feed: Single Column */}
      <div className="px-4 md:hidden flex flex-col gap-6">
        {showSkeletons ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : articles.map(a => (
          <Card key={a.id} card={a} isExpanded={expandedCardId === a.id} onToggle={() => toggleCard(a.id)} />
        ))}
      </div>

      {/* Tablet Feed: 2 Columns */}
      <div className="px-8 hidden md:grid lg:hidden grid-cols-2 gap-6 items-start">
        {showSkeletons ? (
          <>
            <div className="flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
            <div className="flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
          </>
        ) : (
          <>
            <div className="flex flex-col gap-6">
              {col1_2.map(a => <Card key={a.id} card={a} isExpanded={expandedCardId === a.id} onToggle={() => toggleCard(a.id)} />)}
            </div>
            <div className="flex flex-col gap-6">
              {col2_2.map(a => <Card key={a.id} card={a} isExpanded={expandedCardId === a.id} onToggle={() => toggleCard(a.id)} />)}
            </div>
          </>
        )}
      </div>

      {/* Desktop Feed: 3 Columns */}
      <div className="px-8 hidden lg:grid grid-cols-3 gap-6 items-start">
        {showSkeletons ? (
          <>
            <div className="flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
            <div className="flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
            <div className="flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
          </>
        ) : (
          <>
            <div className="flex flex-col gap-6">
              {col1_3.map(a => <Card key={a.id} card={a} isExpanded={expandedCardId === a.id} onToggle={() => toggleCard(a.id)} />)}
            </div>
            <div className="flex flex-col gap-6">
              {col2_3.map(a => <Card key={a.id} card={a} isExpanded={expandedCardId === a.id} onToggle={() => toggleCard(a.id)} />)}
            </div>
            <div className="flex flex-col gap-6">
              {col3_3.map(a => <Card key={a.id} card={a} isExpanded={expandedCardId === a.id} onToggle={() => toggleCard(a.id)} />)}
            </div>
          </>
        )}
      </div>

      {isLoadingMore && (
        <div className="flex justify-center py-8">
          <div className="animate-pulse flex items-center justify-center p-2">
             <div className="w-2 h-2 bg-gray-500 rounded-full animate-[bounce_1s_infinite] [animation-delay:-0.3s] mr-1.5"></div>
             <div className="w-2 h-2 bg-gray-500 rounded-full animate-[bounce_1s_infinite] [animation-delay:-0.15s] mr-1.5"></div>
             <div className="w-2 h-2 bg-gray-500 rounded-full animate-[bounce_1s_infinite]"></div>
          </div>
        </div>
      )}
      
      <div ref={sentinelRef} className="h-4 w-full" />
    </div>
  );
};
