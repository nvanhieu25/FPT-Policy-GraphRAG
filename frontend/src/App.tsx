import { useEffect } from 'react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { Header } from './components/Header/Header';
import { ChatArea } from './components/Chat/ChatArea';
import { ChatInput } from './components/Input/ChatInput';
import { useChat } from './hooks/useChat';
import styles from './App.module.css';

export default function App() {
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

  // Load history of current session on mount
  useEffect(() => {
    loadHistory(currentSessionId);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
        <Header />
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
