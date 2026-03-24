import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { Header } from './components/Header/Header';
import { ChatArea } from './components/Chat/ChatArea';
import { ChatInput } from './components/Input/ChatInput';
import { LoginPage } from './components/Auth/LoginPage';
import { useChat } from './hooks/useChat';
import { auth } from './api/client';
import styles from './App.module.css';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!auth.getToken());

  const {
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
  } = useChat();

  useEffect(() => {
    if (isAuthenticated) {
      loadHistory(currentSessionId);
    }
  }, [isAuthenticated]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

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
        <Header onLogout={() => { auth.clearToken(); setIsAuthenticated(false); }} />
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
