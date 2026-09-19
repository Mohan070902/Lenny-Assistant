import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  X,
  Copy,
  Check,
  Download,
  Maximize2,
  Minimize2,
  Code,
  Eye,
  FileText,
} from 'lucide-react';
import { ArtifactItem } from '../../types';
import { SandboxedIframe } from './SandboxedIframe';

interface ArtifactViewerProps {
  artifact: ArtifactItem | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose }) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [copied, setCopied] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  if (!artifact) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = artifact.artifact_type === 'html' ? 'html' : 'md';
    const mime = artifact.artifact_type === 'html' ? 'text/html' : 'text/markdown';
    const blob = new Blob([artifact.content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.identifier || 'artifact'}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={`border-l border-slate-800 bg-slate-900 flex flex-col h-full transition-all duration-200 z-20 ${
        isMaximized
          ? 'fixed inset-0 w-full z-50 bg-slate-950'
          : 'w-full lg:w-[50%] xl:w-[48%]'
      }`}
    >
      {/* Top Header & Toolbar */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
        <div className="flex items-center gap-2.5 truncate mr-2">
          <div className="w-6 h-6 rounded bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
            {artifact.artifact_type === 'html' ? (
              <Code className="w-3.5 h-3.5" />
            ) : (
              <FileText className="w-3.5 h-3.5" />
            )}
          </div>
          <div className="truncate">
            <h2 className="text-xs font-semibold text-white truncate">{artifact.title}</h2>
            <span className="text-[10px] text-slate-400 font-mono">{artifact.identifier}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Tab Switcher */}
          <div className="inline-flex bg-slate-900 border border-slate-800 rounded-lg p-0.5 mr-2">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-all ${
                activeTab === 'preview'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3 h-3" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-all ${
                activeTab === 'code'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="w-3 h-3" />
              <span>Code</span>
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title="Copy content"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={handleDownload}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsMaximized(!isMaximized)}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title={isMaximized ? 'Restore view' : 'Maximize viewer'}
          >
            {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors ml-1"
            title="Close viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'preview' ? (
          artifact.artifact_type === 'html' ? (
            <SandboxedIframe content={artifact.content} title={artifact.title} />
          ) : (
            <div className="h-full overflow-y-auto p-6 bg-slate-950 text-slate-200 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {artifact.content}
              </ReactMarkdown>
            </div>
          )
        ) : (
          <div className="h-full overflow-y-auto p-4 bg-slate-950 font-mono text-xs text-slate-300 leading-relaxed select-text">
            <pre className="whitespace-pre-wrap break-words">
              <code>{artifact.content}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
