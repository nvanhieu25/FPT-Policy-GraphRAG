import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User } from 'lucide-react';
import type { Message } from '../../types';
import styles from './MessageBubble.module.css';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const timeStr = message.timestamp.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`${styles.row} ${isUser ? styles.rowUser : styles.rowAi}`}>
      {/* Avatar */}
      <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAi}`}>
        {isUser ? <User size={16} strokeWidth={2} /> : <Bot size={16} strokeWidth={1.8} />}
      </div>

      {/* Content */}
      <div className={styles.content}>
        <span className={styles.sender}>{isUser ? 'Bạn' : 'FPT Policy AI'}</span>

        <div
          className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${
            message.isError ? styles.bubbleError : ''
          }`}
        >
          {isUser ? (
            <p className={styles.userText}>{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Open links in new tab
                a: ({ ...props }) => (
                  <a target="_blank" rel="noopener noreferrer" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        <span className={styles.time}>{timeStr}</span>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className={`${styles.row} ${styles.rowAi}`}>
      <div className={`${styles.avatar} ${styles.avatarAi}`}>
        <Bot size={16} strokeWidth={1.8} />
      </div>
      <div className={styles.content}>
        <span className={styles.sender}>FPT Policy AI</span>
        <div className={`${styles.bubble} ${styles.bubbleAi} ${styles.typingBubble}`}>
          <span className={styles.dot} />
          <span className={styles.dot} />
          <span className={styles.dot} />
        </div>
      </div>
    </div>
  );
}
