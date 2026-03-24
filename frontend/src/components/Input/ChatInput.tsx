import { useRef, useState, useEffect } from 'react';
import { SendHorizonal } from 'lucide-react';
import styles from './ChatInput.module.css';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={`${styles.container} ${disabled ? styles.containerDisabled : ''}`}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Hỏi về chính sách FPT… (Enter gửi · Shift+Enter xuống dòng)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />
        <div className={styles.actions}>
          <button
            className={`${styles.btnSend} ${!value.trim() || disabled ? styles.btnSendDisabled : ''}`}
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            title="Gửi (Enter)"
          >
            <SendHorizonal size={16} strokeWidth={2.2} />
          </button>
        </div>
      </div>
      <p className={styles.hint}>
        FPT Policy AI có thể mắc lỗi — hãy xác minh thông tin quan trọng với bộ phận HR.
      </p>
    </div>
  );
}
