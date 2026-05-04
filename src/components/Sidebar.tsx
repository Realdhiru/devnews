import React, { useState, useEffect, useRef } from 'react';
import { useFeedStore } from '../store/feedStore';
import { Menu, X, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

export const Sidebar: React.FC = () => {
  const { availableFilters, activeFilter, setFilter, resetHome, searchQuery, setSearch, isCached, cachedAt } = useFeedStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [localQuery, setLocalQuery] = useState(searchQuery);
  const inputRef = useRef<HTMLInputElement>(null);

  useKeyboardShortcuts(inputRef);

  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.matchMedia('(max-width: 767px)').matches);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (localQuery !== searchQuery) {
        setSearch(localQuery);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localQuery, setSearch, searchQuery]);

  const getRelativeTime = (dateString: string | null) => {
    if (!dateString) return '';
    try {
      const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
      const diff = new Date(dateString).getTime() - new Date().getTime();
      const minDiff = Math.round(diff / (1000 * 60));
      
      if (Math.abs(minDiff) < 1) return 'just now';
      if (Math.abs(minDiff) < 60) return `${Math.abs(minDiff)} min ago`;
      
      const hoursDiff = Math.round(diff / (1000 * 60 * 60));
      return rtf.format(hoursDiff, 'hour');
    } catch {
      return '';
    }
  };

  const renderFilterButton = ({ label, isActive, onClick, key }: { label: string, isActive: boolean, onClick: () => void, key?: string }) => (
    <button
      key={key}
      onClick={onClick}
      className={`w-full flex items-center justify-start px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-200 ${
        isActive 
          ? 'bg-white/[0.04] text-gray-100 shadow-sm border border-white/[0.08]' 
          : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.02] border border-transparent'
      }`}
      style={{ fontFamily: 'monospace' }}
    >
      <span>{label}</span>
    </button>
  );

  return (
    <>
      {!isOpen && (
        <button 
          className="md:hidden fixed top-0 left-[12px] h-[56px] w-[40px] z-50 flex items-center justify-center text-gray-400 hover:text-gray-200 transition-colors"
          onClick={() => setIsOpen(true)}
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>
      )}

      {isOpen && (
        <div className="md:hidden fixed inset-0 bg-black/60 z-30" onClick={() => setIsOpen(false)} />
      )}

      <aside className={`
        fixed md:relative inset-y-0 left-0 z-40 bg-[#0a0a0a] border-r border-white/[0.08] transition-all duration-300 ease-in-out flex flex-col
        ${isOpen ? 'translate-x-0 w-[240px]' : '-translate-x-full md:translate-x-0'}
        ${isCollapsed ? 'md:w-[40px] items-center' : 'md:w-[200px]'}
      `}>
        {!isCollapsed && (
          <>
            <div className="w-full pt-12 pb-10 flex flex-col items-center border-b border-white/[0.04] mb-6">
              <div className="relative flex items-center justify-center w-full px-4">
                <h1 
                  className="text-3xl font-black italic tracking-tighter text-gray-100 uppercase cursor-pointer hover:scale-105 transition-all duration-300 transform-gpu active:scale-95 text-center w-full"
                  style={{ fontFamily: 'Times New Roman' }}
                  onClick={() => { 
                    setLocalQuery('');
                    resetHome(); 
                    setIsOpen(false); 
                  }}
                >
                  DevNews<span className="text-blue-500">.</span>
                </h1>
                <button className="md:hidden absolute right-4 p-2 text-gray-400 hover:text-gray-200 transition-colors" onClick={() => setIsOpen(false)}>
                   <X size={24} />
                </button>
              </div>
            </div>

            <div className="px-3 mb-6">
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  ref={inputRef}
                  type="text"
                  placeholder={isMobile ? "Search..." : "Search... (press /)"}
                  value={localQuery}
                  onChange={(e) => setLocalQuery(e.target.value)}
                  className="w-full bg-white/[0.02] border border-white/[0.06] rounded-lg pl-9 pr-8 py-2 text-[13px] text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-white/[0.12] transition-all font-mono"
                />
                {localQuery && (
                  <button 
                    onClick={() => setLocalQuery('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            </div>

            <div className={`flex-1 overflow-y-auto px-4`}>
              <h2 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-1 font-mono">Categories</h2>
              <div className="flex flex-col gap-1">
                {renderFilterButton({
                  label: "All",
                  isActive: activeFilter === null,
                  onClick: () => { setFilter(null); setIsOpen(false); }
                })}
                {availableFilters.map(f => (
                  renderFilterButton({
                    key: f,
                    label: f,
                    isActive: activeFilter === f,
                    onClick: () => { setFilter(f); setIsOpen(false); }
                  })
                ))}
              </div>
            </div>
            
            <div className={`mt-auto p-4 border-t border-white/[0.04]`}>
              {isCached && cachedAt && (
                <div className="text-[10px] text-gray-600 mb-2 font-mono text-center">
                  Cached · {getRelativeTime(cachedAt)}
                </div>
              )}
              <div className="flex items-center justify-between gap-2">
                <div className="text-[11px] text-gray-500 font-sans tracking-wide leading-tight" style={{ fontFamily: 'Times New Roman', fontStyle: 'italic' }}>
                  A curated dev news aggregator.
                </div>
                <button 
                  onClick={() => setIsCollapsed(true)}
                  className="hidden md:flex p-1.5 text-gray-500 hover:text-gray-200 hover:bg-white/[0.04] rounded-md transition-colors shrink-0"
                >
                  <ChevronLeft size={16} />
                </button>
              </div>
            </div>
          </>
        )}

        {isCollapsed && (
          <div className="flex flex-col h-full py-4 items-center">
             <div className="flex-1" />
             <button 
                onClick={() => setIsCollapsed(false)}
                className="p-1.5 text-gray-500 hover:text-gray-200 hover:bg-white/[0.04] rounded-md transition-colors"
              >
                <ChevronRight size={16} />
              </button>
          </div>
        )}
      </aside>

    </>
  );
};
