import React, { useState } from 'react';
import { ArticleSource } from '../types';

export const SourceBadge: React.FC<{ source: ArticleSource }> = ({ source }) => {
  const [imgError, setImgError] = useState(false);

  return (
    <a 
      href={source.url} 
      target="_blank" 
      rel="noopener noreferrer"
      className="flex items-center gap-3 px-4 py-3 bg-white/[0.02] border border-white/[0.06] rounded-xl hover:bg-white/[0.04] transition-colors group/source"
      onClick={e => e.stopPropagation()}
    >
      {!imgError && source.favicon_url ? (
        <img 
          src={source.favicon_url} 
          alt="" 
          className="w-4 h-4 rounded-sm object-contain" 
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="w-4 h-4 rounded-sm bg-blue-500/20 text-blue-500 flex items-center justify-center text-[10px] font-bold font-mono">
          {source.name.charAt(0).toUpperCase()}
        </div>
      )}
      <span className="text-xs text-gray-400 group-hover/source:text-gray-200 transition-colors w-full truncate font-mono">
        {source.name}
      </span>
    </a>
  );
};
