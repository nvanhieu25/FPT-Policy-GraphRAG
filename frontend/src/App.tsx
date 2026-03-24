import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { Header } from './components/Header/Header';
import { ChatArea } from './components/Chat/ChatArea';
import { ChatInput } from './components/Input/ChatInput';
import { LoginPage } from './components/Auth/LoginPage';
import { useChat } from './hooks/useChat';
import { auth } from './api/client';
import styles from './App.module.css';

// Separate component so useChat hooks only run when authenticated
function ChatApp({ onLogout }: { onLogout: () => void }) {
  const {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    isLoadingHistory,
    sendMessage,
    switchSession,
    newConversation,
    deleteSession,
  } = useChat();

  return (
    <div className={styles.app}>
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewConversation={newConversation}
        onSwitchSession={switchSession}
        onDeleteSession={deleteSession}
      />
      <div className={styles.main}>
        <Header onLogout={onLogout} />
        <ChatArea
          messages={messages}
          isLoading={isLoading}
          isLoadingHistory={isLoadingHistory}
          onSend={sendMessage}
        />
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!auth.getToken());

  useEffect(() => {
    const handleAuthLogout = () => setIsAuthenticated(false);
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, []);

  const handleLogout = () => {
    auth.clearToken();
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  return <ChatApp onLogout={handleLogout} />;
}
