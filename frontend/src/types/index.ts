export interface SessionMeta {
  id: string;
  title: string;       // first user message (truncated)
  messageCount: number;
  createdAt: string;   // ISO string
}

export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
  isError?: boolean;
}

export interface ChatRequest {
  session_id: string;
  query: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
}

export interface MessageItem {
  role: 'human' | 'ai' | 'system';
  content: string;
}

export interface HistoryResponse {
  session_id: string;
  messages: MessageItem[];
}

export interface DeleteResponse {
  session_id: string;
  message: string;
}
