import React from 'react';
import { Plus, MessageSquare, Trash2, Database, Sparkles } from 'lucide-react';
import { SessionListItem, HealthStatus } from '../../types';

interface SessionSidebarProps {
  sessions: SessionListItem[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  health: HealthStatus | null;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  health,
}) => {
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-600/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-tight text-white">Lenny Assistant</h1>
            <p className="text-[11px] text-slate-400">Growth & PM Advisor</p>
          </div>
        </div>

        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-all shadow-sm active:scale-[0.98]"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <div className="px-2 py-1 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
          Conversations
        </div>

        {sessions.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-xs italic">
            No conversations yet.
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`group flex items-center justify-between px-2.5 py-2 rounded-lg cursor-pointer text-xs transition-all ${
                  isActive
                    ? 'bg-slate-800 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1 mr-2">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                  <span className="truncate">{s.title || 'Untitled Chat'}</span>
                </div>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 text-slate-400 transition-opacity"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* System Health Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400">
        <div className="flex items-center justify-between mb-1">
          <span className="flex items-center gap-1.5">
            <Database className="w-3 h-3 text-emerald-400" />
            Knowledge Base
          </span>
          <span className="text-emerald-400 font-medium">
            {health?.chunks_indexed || 50} episodes
          </span>
        </div>
        <div className="flex items-center justify-between text-[10px] text-slate-400">
          <span>System Status:</span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Operational
          </span>
        </div>
      </div>
    </div>
  );
};
