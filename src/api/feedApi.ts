/// <reference types="vite/client" />
import { FeedResponse } from '../types';

export const fetchArticles = async (params: { cursor?: string, limit?: number, filter?: string | null, search?: string }): Promise<FeedResponse> => {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 10000);
  
  try {
    const url = new URL('/api/v1/articles', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
    if (params.cursor) url.searchParams.append('cursor', params.cursor);
    if (params.limit) url.searchParams.append('limit', params.limit.toString());
    if (params.filter) url.searchParams.append('filter', params.filter);
    if (params.search) url.searchParams.append('search', params.search);

    const response = await fetch(url.toString(), {
      signal: controller.signal
    });
    
    clearTimeout(id);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error: any) {
    clearTimeout(id);
    throw error;
  }
};
