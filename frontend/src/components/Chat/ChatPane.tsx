import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Loader2, PanelRightOpen, Compass } from 'lucide-react';
import { Message, ArtifactItem } from '../../types';
import { MessageItem } from './MessageItem';
import { ModelSelector } from './ModelSelector';

interface ChatPaneProps {
  sessionTitle: string;
  messages: Message[];
  isStreaming: boolean;
  statusText: string | null;
  currentProvider: string;
  onProviderChange: (p: string) => void;
  currentMode: 'default' | 'ship30';
  onModeChange: (m: 'default' | 'ship30') => void;
  onSendMessage: (text: string) => void;
  onOpenArtifact: (artifact: ArtifactItem) => void;
  hasActiveArtifact: boolean;
  onToggleArtifactViewer: () => void;
}

const SAMPLE_PROMPTS = [
  {
    title: "AI & Taste in Products",
    prompt: "What did Adam Mosseri say about taste and AI being a tailwind for authenticity?",
  },
  {
    title: "Ship 30 for 30: Finding PMF",
    prompt: "Write a Ship 30 for 30 essay on finding product-market fit using insights from Lenny's guests.",
    mode: "ship30" as const,
  },
  {
    title: "Interactive ROI Calculator",
    prompt: "Generate an interactive HTML/CSS ROI calculator for growth experiments with sliders for conversion rate and traffic.",
  },
  {
    title: "B2B Growth Loops",
    prompt: "How does Elena Verna define product-led growth loops versus sales-led motions?",
  },
];

export const ChatPane: React.FC<ChatPaneProps> = ({
  sessionTitle,
  messages,
  isStreaming,
  statusText,
  currentProvider,
  onProviderChange,
  currentMode,
  onModeChange,
  onSendMessage,
  onOpenArtifact,
  hasActiveArtifact,
  onToggleArtifactViewer,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, statusText]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText);
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-slate-950">
      {/* Top Header */}
      <div className="h-14 border-b border-slate-800 px-4 flex items-center justify-between bg-slate-950/80 backdrop-blur shrink-0">
        <div className="flex items-center gap-2 truncate mr-3">
          <h2 className="text-xs font-semibold text-white truncate">{sessionTitle}</h2>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <ModelSelector
            currentProvider={currentProvider}
            onProviderChange={onProviderChange}
            currentMode={currentMode}
            onModeChange={onModeChange}
          />

          {hasActiveArtifact && (
            <button
              onClick={onToggleArtifactViewer}
              className="flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-medium transition-colors border border-slate-700"
              title="Toggle Artifact Viewer"
            >
              <PanelRightOpen className="w-3.5 h-3.5 text-indigo-400" />
              <span>Artifact</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-xl mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-4 shadow-lg shadow-indigo-600/10">
              <Compass className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-white mb-2">The Lenny Growth Assistant</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Ask any product management or growth strategy question. Every answer is strictly grounded in 50+ Lenny’s Podcast transcripts with guest citations, Ship 30 for 30 syntheses, and interactive artifacts.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
              {SAMPLE_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (item.mode) onModeChange(item.mode);
                    onSendMessage(item.prompt);
                  }}
                  className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-850 text-xs transition-all group"
                >
                  <div className="font-semibold text-slate-200 group-hover:text-indigo-300 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-indigo-400" />
                    {item.title}
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-2 mt-1">
                    {item.prompt}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-900/60 pb-4">
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onOpenArtifact={onOpenArtifact}
              />
            ))}
          </div>
        )}

        {/* Live Status Pill */}
        {statusText && (
          <div className="px-6 py-2 flex items-center gap-2 text-xs text-indigo-400 animate-pulse bg-indigo-950/20 border-y border-indigo-900/30">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>{statusText}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-950 shrink-0">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative">
          <div className="relative flex items-end bg-slate-900 border border-slate-800 focus-within:border-indigo-500 rounded-xl p-2 transition-all shadow-inner">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={handleInputResize}
              onKeyDown={handleKeyDown}
              placeholder={
                currentMode === 'ship30'
                  ? "Enter a topic to generate a Ship 30 for 30 essay grounded in Lenny's podcast..."
                  : "Ask a growth or product question (e.g., 'What did Adam Mosseri say about AI?')..."
              }
              className="w-full bg-transparent resize-none text-xs text-slate-100 placeholder-slate-500 focus:outline-none max-h-36 py-1.5 px-2 leading-relaxed"
            />

            <button
              type="submit"
              disabled={!inputText.trim() || isStreaming}
              className={`p-2 rounded-lg font-medium transition-all shrink-0 ml-2 ${
                inputText.trim() && !isStreaming
                  ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm active:scale-95'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1.5 px-1">
            <span>
              Press <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">Shift+Enter</kbd> for new line
            </span>
            <span>
              Grounding: Strictly Lenny's Podcast Transcripts
            </span>
          </div>
        </form>
      </div>
    </div>
  );
};
