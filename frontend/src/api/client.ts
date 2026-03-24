import type { ChatRequest, ChatResponse, HistoryResponse, DeleteResponse } from '../types';

const BASE_URL = '/api/v1';

const TOKEN_KEY = 'fpt_access_token';

export const auth = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clearToken: () => localStorage.removeItem(TOKEN_KEY),

  async login(email: string, password: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Email hoặc mật khẩu không đúng');
    }
    const data = await res.json();
    auth.setToken(data.access_token);
  },

  async register(email: string, username: string, password: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Đăng ký thất bại');
    }
  },
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = auth.getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });

  if (res.status === 401) {
    auth.clearToken();
    window.location.reload();
    throw new Error('Phiên đăng nhập hết hạn');
  }

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
