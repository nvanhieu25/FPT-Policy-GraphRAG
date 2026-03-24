import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { api } from '../api/client';
import type { Message, SessionMeta } from '../types';

const CURRENT_KEY = 'fpt_current_session';

function getCurrentSessionId(): string {
  const existing = localStorage.getItem(CURRENT_KEY);
  if (existing) return existing;
  const id = uuidv4();
  localStorage.setItem(CURRENT_KEY, id);
  return id;
}

export function useChat() {
  const [sessions, setSessions]         = useState<SessionMeta[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>(getCurrentSessionId);
  const [messages, setMessages]         = useState<Message[]>([]);
  const [isLoading, setIsLoading]       = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // ── Fetch conversation list from API ──────────────────────────────────────
  const fetchSessions = useCallback(async () => {
    try {
      const data = await api.getConversations();
      setSessions(data.conversations);
    } catch {
      // server offline — keep empty list
    }
  }, []);

  // Load sessions on mount
  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  // ── Load message history for a session ───────────────────────────────────
  const loadHistory = useCallback(async (sid: string) => {
    setIsLoadingHistory(true);
    setMessages([]);
    try {
      const data = await api.getHistory(sid);
      const loaded: Message[] = data.messages
        .filter(m => m.role === 'human' || m.role === 'ai')
        .map(m => ({
          id: uuidv4(),
          role: m.role === 'human' ? 'user' : 'ai',
          content: m.content,
          timestamp: new Date(),
        }));
      setMessages(loaded);
    } catch {
      // silent
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  // Load current session history on mount
  useEffect(() => { loadHistory(currentSessionId); }, []); // eslint-disable-line

  // ── Send message ──────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return;

    const userMsg: Message = { id: uuidv4(), role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await api.chat({ session_id: currentSessionId, query });
      const aiMsg: Message = { id: uuidv4(), role: 'ai', content: data.answer, timestamp: new Date() };
      setMessages(prev => [...prev, aiMsg]);
      // Refresh session list so title + count update
      await fetchSessions();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Lỗi không xác định';
      setMessages(prev => [
        ...prev,
        { id: uuidv4(), role: 'ai', content: `**Không thể kết nối đến máy chủ.**\n\n${msg}`, timestamp: new Date(), isError: true },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, isLoading, fetchSessions]);

  // ── Switch to an existing session ────────────────────────────────────────
  const switchSession = useCallback(async (sid: string) => {
    if (sid === currentSessionId) return;
    localStorage.setItem(CURRENT_KEY, sid);
    setCurrentSessionId(sid);
    await loadHistory(sid);
  }, [currentSessionId, loadHistory]);

  // ── Create a new (empty) session ─────────────────────────────────────────
  const newConversation = useCallback(() => {
    const id = uuidv4();
    localStorage.setItem(CURRENT_KEY, id);
    setCurrentSessionId(id);
    setMessages([]);
    // Session will appear in list after first message is sent
  }, []);

  // ── Delete a session ──────────────────────────────────────────────────────
  const deleteSession = useCallback(async (sid: string) => {
    try { await api.deleteHistory(sid); } catch { /* best-effort */ }
    await fetchSessions();

    if (sid === currentSessionId) {
      const remaining = sessions.filter(s => s.id !== sid);
      if (remaining.length > 0) {
        await switchSession(remaining[0].id);
      } else {
        newConversation();
      }
    }
  }, [currentSessionId, sessions, fetchSessions, switchSession, newConversation]);

  return {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    isLoadingHistory,
    sendMessage,
    loadHistory,
    switchSession,
    newConversation,
    deleteSession,
  };
}
