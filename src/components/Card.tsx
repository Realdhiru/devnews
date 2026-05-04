import React, { useRef } from 'react';
import DOMPurify from 'dompurify';
import { ArticleCard } from '../types';
import { SourceBadge } from './SourceBadge';

interface CardProps {
  card: ArticleCard;
  isExpanded: boolean;
  onToggle: () => void;
}

export const Card: React.FC<CardProps> = ({ card, isExpanded, onToggle }) => {
  const contentRef = useRef<HTMLDivElement>(null);

  const getRelativeTime = (dateString: string) => {
    try {
      const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
      const daysDifference = Math.round((new Date(dateString).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
      if (daysDifference === 0) {
        const hoursDiff = Math.round((new Date(dateString).getTime() - new Date().getTime()) / (1000 * 60 * 60));
        if (hoursDiff === 0) {
          const minDiff = Math.round((new Date(dateString).getTime() - new Date().getTime()) / (1000 * 60));
          return rtf.format(minDiff, 'minute');
        }
        return rtf.format(hoursDiff, 'hour');
      }
      return rtf.format(daysDifference, 'day');
    } catch {
      return dateString.split('T')[0];
    }
  };

  const getCategoryColor = (cat: string) => {
    switch(cat.toLowerCase()) {
      case 'security': return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'events': return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      case 'open source': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'ai': return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
      default: return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
  };

  const primaryCategory = card.categories[0] || 'General';

  return (
    <div 
      className={`group relative bg-[#0a0a0a] border border-white/[0.08] rounded-2xl p-6 md:p-8 cursor-pointer hover:border-white/[0.15] hover:bg-white/[0.02] hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)] transition-all duration-300 focus:outline-none focus:ring-1 focus:ring-gray-500`}
      onClick={onToggle}
      onKeyDown={(e) => {
        if(e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onToggle();
        }
      }}
      tabIndex={0}
      data-card-id={card.id}
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <h2 className="text-xl md:text-2xl font-semibold tracking-[-0.015em] text-gray-50 leading-snug line-clamp-2" style={{ fontFamily: 'Times New Roman' }} dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(card.title)}} />
          
          <div className="mt-4 flex items-center gap-3 text-xs font-mono text-gray-400 uppercase tracking-widest font-bold">
            <span>{getRelativeTime(card.published_at)}</span>
            <span className="text-gray-700">/</span>
            <span className={`px-2 py-1 rounded text-[10px] ${getCategoryColor(primaryCategory)} font-mono`}>{primaryCategory}</span>
            {card.source_count > 1 && (
              <>
                <span className="text-gray-700">/</span>
                <span className="text-gray-400 bg-white/[0.04] border border-white/[0.08] px-2 py-1 rounded text-[10px] drop-shadow-sm font-mono">{card.source_count} SOURCES</span>
              </>
            )}
          </div>
        </div>
      </div>

      {(isExpanded ? card.summary_full : card.summary_short) ? (
        <div className="mt-5">
          <div 
            className={`text-[15px] md:text-[16px] text-gray-400 leading-relaxed break-words whitespace-pre-wrap ${!isExpanded ? 'line-clamp-2 overflow-hidden' : ''}`}
            style={{ 
              fontFamily: 'Inter, system-ui, sans-serif',
              fontStyle: 'italic',
              display: !isExpanded ? '-webkit-box' : 'block',
              WebkitLineClamp: !isExpanded ? 2 : 'none',
              WebkitBoxOrient: 'vertical',
            }}
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(isExpanded ? card.summary_full : card.summary_short) }}
          />
        </div>
      ) : null}

      <div className="mt-0">
        {isExpanded && card.sources && card.sources.length > 0 && (
          <div className="mt-6 pt-6 border-t border-white/[0.08] flex flex-col gap-3 animate-in fade-in duration-500">
            <h3 className="text-[10px] font-black font-mono text-gray-500 uppercase tracking-widest mb-1">Sources</h3>
            {card.sources.map((src, i) => (
              <SourceBadge key={i} source={src} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
