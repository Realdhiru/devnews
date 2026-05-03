import React from 'react';

export const SkeletonCard: React.FC = () => {
  return (
    <div className="bg-[#0a0a0a] border border-white/[0.08] rounded-2xl p-6 md:p-8 h-[160px] flex flex-col justify-between">
      <div>
        <div className="h-6 md:h-8 bg-white/[0.04] rounded w-3/4 mb-3 animate-pulse"></div>
        <div className="h-6 md:h-8 bg-white/[0.04] rounded w-1/2 animate-pulse"></div>
      </div>
      <div className="flex gap-3">
        <div className="h-4 bg-white/[0.04] rounded w-16 animate-pulse"></div>
        <div className="h-4 bg-white/[0.04] rounded w-20 animate-pulse"></div>
      </div>
    </div>
  );
};
