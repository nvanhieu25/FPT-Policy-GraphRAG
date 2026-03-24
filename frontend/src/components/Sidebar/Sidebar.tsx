import { useState, useEffect } from 'react';
import {
  Plus,
  Trash2,
  Cpu,
  Database,
  GitBranch,
  HardDrive,
  CheckCircle2,
  XCircle,
  MessageSquare,
} from 'lucide-react';
import { api } from '../../api/client';
import type { SessionMeta } from '../../types';
import styles from './Sidebar.module.css';

interface SidebarProps {
  sessions: SessionMeta[];
  currentSessionId: string;
  onNewConversation: () => void;
  onSwitchSession: (sid: string) => void;
  onDeleteSession: (sid: string) => void;
}

type ServerStatus = 'checking' | 'online' | 'offline';

export function Sidebar({
  sessions,
  currentSessionId,
  onNewConversation,
  onSwitchSession,
  onDeleteSession,
}: SidebarProps) {
  const [serverStatus, setServerStatus] = useState<ServerStatus>('checking');
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      const result = await api.healthCheck();
      setServerStatus(result.status === 'ok' ? 'online' : 'offline');
    };
    check();
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className={styles.sidebar}>
      {/* Logo */}
      <div className={styles.logoArea}>
        <img src="/fpt-logo.svg?v=2" alt="FPT" className={styles.logo} />
        <div className={styles.logoMeta}>
          <span className={styles.logoTitle}>Policy Assistant</span>
          <span className={styles.logoSub}>GraphRAG · AI</span>
        </div>
      </div>

      {/* New conversation */}
      <div className={styles.actions}>
        <button className={styles.btnNew} onClick={onNewConversation}>
          <Plus size={15} strokeWidth={2.5} />
          Cuộc trò chuyện mới
        </button>
      </div>

      {/* Session list */}
      <section className={styles.section} style={{ flex: 1, minHeight: 0 }}>
        <p className={styles.sectionLabel}>Lịch sử trò chuyện</p>
        <div className={styles.sessionList}>
          {sessions.length === 0 && (
            <p className={styles.emptyHint}>Chưa có cuộc trò chuyện nào</p>
          )}
          {sessions.map(session => (
            <div
              key={session.id}
              className={`${styles.sessionItem} ${session.id === currentSessionId ? styles.sessionItemActive : ''}`}
              onClick={() => onSwitchSession(session.id)}
              onMouseEnter={() => setHoveredId(session.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <MessageSquare size={13} className={styles.sessionItemIcon} />
              <div className={styles.sessionItemBody}>
                <span className={styles.sessionItemTitle}>{session.title}</span>
                <span className={styles.sessionItemMeta}>{session.messageCount} tin nhắn</span>
              </div>
              {hoveredId === session.id && (
                <button
                  className={styles.btnDeleteSession}
                  onClick={e => { e.stopPropagation(); onDeleteSession(session.id); }}
                  title="Xóa cuộc trò chuyện"
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* System status */}
      <section className={styles.section}>
        <p className={styles.sectionLabel}>Trạng thái hệ thống</p>
        <div className={styles.statusCard}>
          <StatusRow icon={<Cpu size={13} />} label="API Server" status={serverStatus} />
          <StatusRow icon={<Database size={13} />} label="Qdrant (Vector)" status="online" />
          <StatusRow icon={<GitBranch size={13} />} label="Neo4j (Graph)" status="online" />
          <StatusRow icon={<HardDrive size={13} />} label="Redis (Cache)" status="online" />
        </div>
      </section>

      {/* Models */}
      <section className={styles.section} style={{ paddingBottom: 14 }}>
        <p className={styles.sectionLabel}>Mô hình AI</p>
        <div className={styles.modelCard}>
          <div className={styles.modelRow}>
            <span className={styles.modelBadge}>Gen</span>
            <span className={styles.modelName}>GPT-4o</span>
          </div>
          <div className={styles.modelRow}>
            <span className={`${styles.modelBadge} ${styles.modelBadgeMini}`}>Route</span>
            <span className={styles.modelName}>GPT-4o-mini</span>
          </div>
        </div>
      </section>
    </aside>
  );
}

function StatusRow({
  icon,
  label,
  status,
}: {
  icon: React.ReactNode;
  label: string;
  status: ServerStatus;
}) {
  return (
    <div className={styles.statusRow}>
      <span className={styles.statusIcon}>{icon}</span>
      <span className={styles.statusLabel}>{label}</span>
      <span className={styles.statusIndicator}>
        {status === 'checking' && <span className={`${styles.dot} ${styles.dotChecking}`} />}
        {status === 'online' && <CheckCircle2 size={13} className={styles.dotOnline} />}
        {status === 'offline' && <XCircle size={13} className={styles.dotOffline} />}
      </span>
    </div>
  );
}
