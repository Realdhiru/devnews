import React from 'react';

interface ErrorBannerProps {
  error: string;
  isWarning?: boolean;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, isWarning = false }) => {
  return (
    <div className="w-full flex justify-center py-6 border-b border-white/[0.04] mb-6 mt-0 bg-[#0a0a0a]">
      <div className="flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/[0.02] border border-white/[0.08] text-[11px] text-gray-500 font-medium tracking-wide" style={{ fontFamily: 'Times New Roman' }}>
        <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${isWarning ? 'bg-amber-500/80' : 'bg-red-500/80'}`}></span>
        {isWarning ? error : 'Backend offline — showing demo data'}
      </div>
    </div>
  );
};
