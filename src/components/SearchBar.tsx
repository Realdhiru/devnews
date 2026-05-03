import React, { useState, useEffect, useRef } from 'react';
import { useFeedStore } from '../store/feedStore';
import { Search, X } from 'lucide-react';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

export const SearchBar: React.FC = () => {
  const { searchQuery, setSearch } = useFeedStore();
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

  return (
    <div className="sticky top-0 z-20 bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-white/[0.08] h-[56px] flex items-center">
      <div className="max-w-7xl w-full mx-auto flex items-center px-[12px] sm:px-8 gap-[12px] sm:gap-4 h-full">
        {/* On mobile we add a spacer for the hamburger icon. On desktop it is hidden */}
        <div className="w-[40px] shrink-0 md:hidden"></div>
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search size={16} className="text-gray-500" />
          </div>
          <input
            ref={inputRef}
            type="text"
            className="block w-full pl-10 pr-10 py-2.5 border border-white/[0.06] rounded-xl leading-5 bg-white/[0.02] text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-white/[0.12] focus:border-white/[0.12] hover:bg-white/[0.04] text-[15px] sm:text-sm transition-all font-mono"
            placeholder={isMobile ? "Search articles..." : "Search articles... (press / to focus)"}
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
          />
          {localQuery && (
            <button 
              className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-gray-300 transition-colors"
              onClick={() => setLocalQuery('')}
              tabIndex={-1}
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
