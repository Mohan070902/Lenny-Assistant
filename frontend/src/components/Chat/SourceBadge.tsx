import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, Clock, User } from 'lucide-react';
import { SourceItem } from '../../types';

interface SourceBadgeProps {
  sources: SourceItem[];
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ sources }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 border border-emerald-900/40 bg-emerald-950/20 rounded-lg overflow-hidden text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 flex items-center justify-between text-emerald-400 hover:bg-emerald-900/30 transition-colors"
      >
        <span className="flex items-center gap-1.5 font-medium">
          <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
          Grounded in {sources.length} Podcast Source{sources.length > 1 ? 's' : ''}
        </span>
        <span className="flex items-center gap-1 text-emerald-500">
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </span>
      </button>

      {isOpen && (
        <div className="p-3 border-t border-emerald-900/30 space-y-2 bg-slate-900/50">
          {sources.map((src, idx) => (
            <div
              key={idx}
              className="p-2 rounded bg-slate-900/80 border border-slate-800 flex flex-col gap-1 text-slate-300"
            >
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span className="flex items-center gap-1.5 truncate">
                  <User className="w-3 h-3 text-indigo-400 shrink-0" />
                  {src.guest}
                </span>
                {src.timestamp && (
                  <span className="flex items-center gap-1 text-slate-400 text-[10px] bg-slate-800 px-1.5 py-0.5 rounded">
                    <Clock className="w-2.5 h-2.5" />
                    {src.timestamp}
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-400 truncate">{src.episode}</div>
              {src.text && (
                <div className="text-[11px] text-slate-400 italic bg-slate-950/50 p-1.5 rounded border border-slate-800/60 mt-0.5 line-clamp-2">
                  "{src.text}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
