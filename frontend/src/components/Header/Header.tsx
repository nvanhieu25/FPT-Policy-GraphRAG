import { BotMessageSquare } from 'lucide-react';
import styles from './Header.module.css';

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.iconWrap}>
        <BotMessageSquare size={20} strokeWidth={1.8} />
      </div>
      <div className={styles.info}>
        <span className={styles.title}>FPT Policy Assistant</span>
        <span className={styles.subtitle}>
          Trợ lý chính sách nội bộ · Hybrid GraphRAG (Vector + Graph)
        </span>
      </div>
      <div className={styles.statusBadge}>
        <span className={styles.statusDot} />
        Trực tuyến
      </div>
    </header>
  );
}
