import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Code, FileText, ArrowUpRight } from 'lucide-react';
import { Message, ArtifactItem } from '../../types';
import { SourceBadge } from './SourceBadge';

interface MessageItemProps {
  message: Message;
  onOpenArtifact?: (artifact: ArtifactItem) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, onOpenArtifact }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? 'bg-slate-950' : 'bg-slate-900/60'}`}>
      {/* Avatar */}
      <div className="shrink-0 mt-0.5">
        {isUser ? (
          <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <User className="w-4 h-4" />
          </div>
        ) : (
          <div className="w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Bot className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-200">
            {isUser ? 'You' : 'Lenny Assistant'}
          </span>
          <span className="text-[10px] text-slate-400">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Message Text with Markdown */}
        <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ node, ...props }) => <h1 className="text-base font-bold text-white mt-4 mb-2 border-b border-slate-800 pb-1" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-sm font-bold text-slate-100 mt-3 mb-1.5" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-xs font-bold text-indigo-300 mt-2 mb-1 uppercase tracking-wide" {...props} />,
              p: ({ node, ...props }) => <p className="text-xs mb-2 text-slate-200" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-inside text-xs space-y-1 mb-2 text-slate-300 pl-1" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside text-xs space-y-1 mb-2 text-slate-300 pl-1" {...props} />,
              li: ({ node, ...props }) => <li className="text-xs text-slate-300" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-semibold text-white" {...props} />,
              blockquote: ({ node, ...props }) => (
                <blockquote className="border-l-2 border-indigo-500 bg-indigo-950/20 pl-3 py-1 my-2 rounded-r text-xs text-indigo-200 italic" {...props} />
              ),
              code: ({ node, className, children, ...props }: any) => {
                const match = /language-(\w+)/.exec(className || '');
                const isInline = !match;
                return isInline ? (
                  <code className="bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded text-[11px] font-mono" {...props}>
                    {children}
                  </code>
                ) : (
                  <div className="my-2 rounded-lg bg-slate-950 border border-slate-800 p-3 overflow-x-auto text-[11px] font-mono text-slate-200">
                    <pre {...props}><code>{children}</code></pre>
                  </div>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>

          {message.isStreaming && (
            <span className="inline-block w-1.5 h-3.5 bg-indigo-400 animate-pulse ml-0.5 align-middle" />
          )}
        </div>

        {/* Render Artifact Cards if any */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div className="pt-2 space-y-2">
            {message.artifacts.map((art, aIdx) => (
              <div
                key={aIdx}
                className="flex items-center justify-between p-3 rounded-lg border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 to-slate-900 shadow-sm"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    {art.artifact_type === 'html' ? (
                      <Code className="w-4 h-4" />
                    ) : (
                      <FileText className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                      {art.title}
                      <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 uppercase">
                        {art.artifact_type}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Generated artifact ready for live side-by-side inspection
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onOpenArtifact && onOpenArtifact(art)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-medium transition-all shadow-sm active:scale-95"
                >
                  <span>Open Preview</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Source Citations */}
        {message.sources && message.sources.length > 0 && (
          <SourceBadge sources={message.sources} />
        )}
      </div>
    </div>
  );
};
