import React, { useState, useEffect, useCallback } from 'react';
import { SessionListItem, ArtifactItem, HealthStatus, Message } from './types';
import { fetchSessions, createSession, fetchSession, deleteSession, checkHealth } from './lib/api';
import { SessionSidebar } from './components/Chat/SessionSidebar';
import { ChatPane } from './components/Chat/ChatPane';
import { ArtifactViewer } from './components/Artifact/ArtifactViewer';
import { useChatStream } from './hooks/useChatStream';

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string>('New Conversation');
  const [currentProvider, setCurrentProvider] = useState<string>('ollama');
  const [currentMode, setCurrentMode] = useState<'default' | 'ship30'>('default');
  const [activeArtifact, setActiveArtifact] = useState<ArtifactItem | null>(null);
  const [isArtifactOpen, setIsArtifactOpen] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  // Load initial sessions & system health
  useEffect(() => {
    async function init() {
      try {
        const h = await checkHealth();
        setHealth(h);
      } catch (err) {
        console.warn('Initial health check notice:', err);
      }

      try {
        const sessList = await fetchSessions();
        setSessions(sessList);
        if (sessList.length > 0) {
          setActiveSessionId(sessList[0].id);
          setSessionTitle(sessList[0].title);
        } else {
          // Create initial session
          const newSess = await createSession('New Conversation', 'ollama');
          const item: SessionListItem = {
            id: newSess.id,
            title: newSess.title,
            provider: newSess.provider,
            created_at: newSess.created_at,
            updated_at: newSess.updated_at,
            message_count: 0,
          };
          setSessions([item]);
          setActiveSessionId(newSess.id);
        }

      } catch (err) {
        console.error('Failed to load sessions:', err);
      }
    }
    init();
  }, []);

  const handleArtifactReceived = useCallback((artifact: ArtifactItem) => {
    setActiveArtifact(artifact);
    setIsArtifactOpen(true);
  }, []);

  // Use chat streaming hook
  const {
    messages,
    setMessages,
    isStreaming,
    statusText,
    sendMessage,
  } = useChatStream({
    sessionId: activeSessionId || '',
    provider: currentProvider,
    mode: currentMode,
    onArtifactReceived: handleArtifactReceived,
  });

  // Fetch messages when active session changes
  useEffect(() => {
    if (!activeSessionId) return;
    async function loadActiveSession() {
      try {
        const fullSession = await fetchSession(activeSessionId!);
        setSessionTitle(fullSession.title);
        setCurrentProvider(fullSession.provider || 'ollama');
        setMessages(fullSession.messages || []);

        // If session has artifacts, select the latest one
        const latestMsgWithArtifact = fullSession.messages
          .slice()
          .reverse()
          .find((m: Message) => m.artifacts && m.artifacts.length > 0);
        if (latestMsgWithArtifact && latestMsgWithArtifact.artifacts?.length) {
          setActiveArtifact(latestMsgWithArtifact.artifacts[latestMsgWithArtifact.artifacts.length - 1]);
        }
      } catch (err) {
        console.error('Error fetching session messages:', err);
      }
    }
    loadActiveSession();
  }, [activeSessionId, setMessages]);

  const handleNewSession = async () => {
    try {
      const newSess = await createSession('New Conversation', currentProvider);
      const item: SessionListItem = {
        id: newSess.id,
        title: newSess.title,
        provider: newSess.provider,
        created_at: newSess.created_at,
        updated_at: newSess.updated_at,
        message_count: 0,
      };
      setSessions((prev) => [item, ...prev]);
      setActiveSessionId(newSess.id);
      setSessionTitle(newSess.title);
      setMessages([]);
      setActiveArtifact(null);
      setIsArtifactOpen(false);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  };


  const handleDeleteSession = async (id: string) => {
    try {
      await deleteSession(id);
      const remaining = sessions.filter((s) => s.id !== id);
      setSessions(remaining);
      if (activeSessionId === id) {
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          handleNewSession();
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleOpenArtifact = (art: ArtifactItem) => {
    setActiveArtifact(art);
    setIsArtifactOpen(true);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans antialiased text-slate-100">
      {/* Sessions Navigation Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        health={health}
      />

      {/* Main Dual-Pane Workspace */}
      <div className="flex-1 flex h-full overflow-hidden relative">
        <ChatPane
          sessionTitle={sessionTitle}
          messages={messages}
          isStreaming={isStreaming}
          statusText={statusText}
          currentProvider={currentProvider}
          onProviderChange={setCurrentProvider}
          currentMode={currentMode}
          onModeChange={setCurrentMode}
          onSendMessage={sendMessage}
          onOpenArtifact={handleOpenArtifact}
          hasActiveArtifact={!!activeArtifact}
          onToggleArtifactViewer={() => setIsArtifactOpen(!isArtifactOpen)}
        />

        {/* Side-by-side Sandboxed Artifact Viewer */}
        {isArtifactOpen && activeArtifact && (
          <ArtifactViewer
            artifact={activeArtifact}
            onClose={() => setIsArtifactOpen(false)}
          />
        )}
      </div>
    </div>
  );
};

export default App;
