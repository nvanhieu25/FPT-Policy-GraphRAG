import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import { MessageBubble, TypingIndicator } from './MessageBubble';
import { WelcomeScreen } from './WelcomeScreen';
import type { Message } from '../../types';
import styles from './ChatArea.module.css';

interface ChatAreaProps {
  messages: Message[];
  isLoading: boolean;
  isLoadingHistory: boolean;
  onSend: (text: string) => void;
}

export function ChatArea({ messages, isLoading, isLoadingHistory, onSend }: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (isLoadingHistory) {
    return (
      <div className={styles.loadingScreen}>
        <Loader2 size={24} className={styles.spinner} />
        <span>Đang tải lịch sử hội thoại…</span>
      </div>
    );
  }

  if (messages.length === 0 && !isLoading) {
    return (
      <div className={styles.area}>
        <WelcomeScreen onSend={onSend} />
      </div>
    );
  }

  return (
    <div className={styles.area}>
      <div className={styles.messages}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
