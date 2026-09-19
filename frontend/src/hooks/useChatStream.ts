import { useState, useCallback } from 'react';
import { Message, SourceItem, ArtifactItem } from '../types';
import { API_BASE } from '../lib/api';

interface UseChatStreamOptions {
  sessionId: string;
  provider: string;
  mode: 'default' | 'ship30';
  onArtifactReceived?: (artifact: ArtifactItem) => void;
}

export function useChatStream({ sessionId, provider, mode, onArtifactReceived }: UseChatStreamOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return;

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `asst-${Date.now()}`;

    const userMessage: Message = {
      id: userMessageId,
      session_id: sessionId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      session_id: sessionId,
      role: 'assistant',
      content: '',
      sources: [],
      artifacts: [],
      created_at: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setIsStreaming(true);
    setStatusText('Initiating conversation...');

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId && sessionId.trim() !== '' ? sessionId : undefined,
          message: text,
          provider,
          mode,
        }),

      });

      if (!response.ok || !response.body) {
        throw new Error(`Failed to stream chat: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;

          const dataStr = trimmed.slice(6).trim();
          if (dataStr === '[DONE]') {
            setIsStreaming(false);
            setStatusText(null);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
              )
            );
            break;
          }

          try {
            const event = JSON.parse(dataStr);

            if (event.type === 'status') {
              setStatusText(event.content);
            } else if (event.type === 'sources') {
              const incomingSources: SourceItem[] = event.sources || [];
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId ? { ...msg, sources: incomingSources } : msg
                )
              );
            } else if (event.type === 'token') {
              const tokenContent = event.content || '';
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: msg.content + tokenContent }
                    : msg
                )
              );
            } else if (event.type === 'artifact') {
              const artifact: ArtifactItem = event.artifact;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, artifacts: [...(msg.artifacts || []), artifact] }
                    : msg
                )
              );
              if (onArtifactReceived) {
                onArtifactReceived(artifact);
              }
            } else if (event.type === 'error') {
              setStatusText(`Error: ${event.content}`);
            }
          } catch (err) {
            // Non-JSON SSE line, ignore
          }
        }
      }
    } catch (err: any) {
      console.error('Streaming error:', err);
      setStatusText(`Connection error: ${err.message}`);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: msg.content + `\n\n⚠️ **Error:** Failed to stream response (${err.message}).`,
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
      setStatusText(null);
    }
  }, [sessionId, provider, mode, isStreaming, onArtifactReceived]);

  return {
    messages,
    setMessages,
    isStreaming,
    statusText,
    sendMessage,
  };
}
