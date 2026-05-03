import React from 'react';
import { useFeedStore } from '../store/feedStore';
import { Card } from './Card';
import { SkeletonCard } from './SkeletonCard';
import { useInfiniteScroll } from '../hooks/useInfiniteScroll';

export const Feed: React.FC = () => {
  const { articles, isLoading, isLoadingMore, hasMore, error, isCached, expandedCardId, toggleCard, fetchMore } = useFeedStore();
  
  const sentinelRef = useInfiniteScroll(fetchMore, hasMore, isLoadingMore);

  const showSkeletons = isLoading && !isCached && articles.length === 0;

  // Group articles into columns manually to isolate expansion
  const col1 = articles.filter((_, i) => i % 3 === 0);
  const col2 = articles.filter((_, i) => i % 3 === 1);
  const col3 = articles.filter((_, i) => i % 3 === 2);

  const renderColumn = (colArticles: typeof articles) => (
    <div className="flex flex-col gap-6">
      {colArticles.map((article) => (
        <Card 
          key={article.id}
          card={article} 
          isExpanded={expandedCardId === article.id} 
          onToggle={() => toggleCard(article.id)} 
        />
      ))}
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto pb-20 min-h-screen bg-[#0a0a0a] w-full pt-8">
      <div className="px-4 sm:px-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
        {showSkeletons ? (
          <>
            <div className="flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
            <div className="hidden md:flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
            <div className="hidden lg:flex flex-col gap-6"><SkeletonCard /><SkeletonCard /></div>
          </>
        ) : (
          <>
            {/* On mobile (default), show all articles in one column but distributed into col1 for grouping stability if needed. 
                Wait, if I use grid-cols-1, then col2 and col3 are hidden. That's bad. 
                I need to handle the distribution differently based on the number of columns.
            */}
            <div className="flex flex-col gap-6">
               {[...col1, ...col2, ...col3].sort((a,b) => articles.indexOf(a) - articles.indexOf(b)).map(article => (
                  <div key={article.id} className="md:hidden">
                    <Card card={article} isExpanded={expandedCardId === article.id} onToggle={() => toggleCard(article.id)} />
                  </div>
               ))}
               {col1.map(article => (
                  <div key={article.id} className="hidden md:block">
                    <Card card={article} isExpanded={expandedCardId === article.id} onToggle={() => toggleCard(article.id)} />
                  </div>
               ))}
            </div>
            <div className="hidden md:flex flex-col gap-6">
               {col2.map(article => (
                  <div key={article.id}>
                    <Card card={article} isExpanded={expandedCardId === article.id} onToggle={() => toggleCard(article.id)} />
                  </div>
               ))}
            </div>
            <div className="hidden lg:flex flex-col gap-6">
               {col3.map(article => (
                  <div key={article.id}>
                    <Card card={article} isExpanded={expandedCardId === article.id} onToggle={() => toggleCard(article.id)} />
                  </div>
               ))}
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
