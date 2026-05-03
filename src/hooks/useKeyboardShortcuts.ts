import { useEffect, RefObject } from 'react';
import { useFeedStore } from '../store/feedStore';

export const useKeyboardShortcuts = (searchInputRef: RefObject<HTMLInputElement>) => {
  const toggleCard = useFeedStore(state => state.toggleCard);
  const articles = useFeedStore(state => state.articles);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== searchInputRef.current) {
        e.preventDefault();
        searchInputRef.current?.focus();
        return;
      }

      if (document.activeElement?.tagName === 'INPUT') {
        if (e.key === 'Escape') {
          (document.activeElement as HTMLElement).blur();
        }
        return; // Don't process j/k/Enter if typing in input
      }

      const activeElement = document.activeElement as HTMLElement;
      const isCard = activeElement.dataset.cardId;
      
      if (e.key === 'j') {
        if (!isCard) {
          const firstCard = document.querySelector('[data-card-id]') as HTMLElement;
          firstCard?.focus();
        } else {
          const parent = activeElement.parentElement;
          const next = parent?.nextElementSibling?.firstElementChild as HTMLElement;
          next?.focus();
        }
      } else if (e.key === 'k') {
        if (isCard) {
          const parent = activeElement.parentElement;
          const prev = parent?.previousElementSibling?.firstElementChild as HTMLElement;
          prev?.focus();
        }
      } else if (e.key === 'Enter' && isCard) {
        toggleCard(parseInt(activeElement.dataset.cardId as string, 10));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [searchInputRef, toggleCard, articles]);
};
