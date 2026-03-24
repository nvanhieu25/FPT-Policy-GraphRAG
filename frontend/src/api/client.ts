import type { ChatRequest, ChatResponse, HistoryResponse, DeleteResponse } from '../types';

const BASE_URL = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(error.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

export const api = {
  chat(payload: ChatRequest): Promise<ChatResponse> {
    return request('/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getHistory(sessionId: string): Promise<HistoryResponse> {
    return request(`/history/${sessionId}`);
  },

  deleteHistory(sessionId: string): Promise<DeleteResponse> {
    return request(`/history/${sessionId}`, { method: 'DELETE' });
  },

  getConversations(): Promise<{ conversations: import('../types').SessionMeta[] }> {
    return request('/conversations');
  },

  healthCheck(): Promise<{ status: string }> {
    return fetch('/health').then(r => r.json()).catch(() => ({ status: 'offline' }));
  },
};
