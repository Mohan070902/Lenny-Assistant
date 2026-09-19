import React from 'react';
import { Cpu, Cloud, Sparkles } from 'lucide-react';

interface ModelSelectorProps {
  currentProvider: string;
  onProviderChange: (provider: string) => void;
  currentMode: 'default' | 'ship30';
  onModeChange: (mode: 'default' | 'ship30') => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  currentProvider,
  onProviderChange,
  currentMode,
  onModeChange,
}) => {
  return (
    <div className="flex items-center gap-2 text-xs">
      {/* Provider Selector */}
      <div className="relative inline-flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
        <button
          type="button"
          onClick={() => onProviderChange('ollama')}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
            currentProvider === 'ollama'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          title="Run inference locally via Ollama"
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>Local (Ollama)</span>
        </button>

        <button
          type="button"
          onClick={() => onProviderChange('cloud')}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
            currentProvider === 'cloud'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          title="Run inference via Cloud (Claude/OpenAI)"
        >
          <Cloud className="w-3.5 h-3.5" />
          <span>Cloud LLM</span>
        </button>
      </div>

      {/* Mode Selector (Default RAG vs Ship 30 for 30) */}
      <div className="relative inline-flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
        <button
          type="button"
          onClick={() => onModeChange('default')}
          className={`px-2.5 py-1 rounded-md font-medium transition-all ${
            currentMode === 'default'
              ? 'bg-slate-800 text-slate-100 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Standard Q&A
        </button>

        <button
          type="button"
          onClick={() => onModeChange('ship30')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
            currentMode === 'ship30'
              ? 'bg-amber-600/90 text-white shadow-sm'
              : 'text-amber-400/80 hover:text-amber-300'
          }`}
          title="Format responses as Ship 30 for 30 style essays (~1,250 words)"
        >
          <Sparkles className="w-3 h-3" />
          <span>Ship 30 for 30</span>
        </button>
      </div>
    </div>
  );
};
