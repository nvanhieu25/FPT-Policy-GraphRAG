import { Sparkles } from 'lucide-react';
import styles from './WelcomeScreen.module.css';

const SUGGESTIONS = [
  { icon: '🏢', text: 'Tôi có được phép kiêm nhiệm ở công ty khác không?' },
  { icon: '📅', text: 'Quy trình xin nghỉ phép năm như thế nào?' },
  { icon: '🔒', text: 'Chính sách bảo mật thông tin của FPT Software là gì?' },
  { icon: '⏰', text: 'Quy định về làm thêm giờ và phụ cấp OT?' },
  { icon: '📋', text: 'Quy trình phê duyệt hợp đồng với đối tác bên ngoài?' },
  { icon: '🎓', text: 'Chính sách đào tạo và phát triển nghề nghiệp?' },
];

interface WelcomeScreenProps {
  onSend: (text: string) => void;
}

export function WelcomeScreen({ onSend }: WelcomeScreenProps) {
  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <div className={styles.iconWrap}>
          <Sparkles size={32} strokeWidth={1.5} />
        </div>
        <h1 className={styles.title}>
          Xin chào! Tôi là{' '}
          <span className={styles.accent}>FPT Policy AI</span>
        </h1>
        <p className={styles.desc}>
          Tôi có thể giải đáp các câu hỏi về chính sách nội bộ của FPT Software.
          Hệ thống sử dụng công nghệ{' '}
          <strong>Hybrid GraphRAG</strong> — kết hợp tìm kiếm ngữ nghĩa (Qdrant)
          và đồ thị tri thức (Neo4j) để đưa ra câu trả lời chính xác nhất.
        </p>
      </div>

      <div className={styles.suggestionsGrid}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s.text}
            className={styles.chip}
            onClick={() => onSend(s.text)}
          >
            <span className={styles.chipIcon}>{s.icon}</span>
            <span className={styles.chipText}>{s.text}</span>
          </button>
        ))}
      </div>

      <p className={styles.hint}>
        Chọn một câu hỏi gợi ý hoặc nhập câu hỏi của bạn bên dưới
      </p>
    </div>
  );
}
