import React, { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { ShieldCheck } from 'lucide-react';

interface SandboxedIframeProps {
  content: string;
  title: string;
}

export const SandboxedIframe: React.FC<SandboxedIframeProps> = ({ content, title }) => {
  // Sanitize markup prior to injecting into iframe srcDoc
  const cleanHtml = useMemo(() => {
    return DOMPurify.sanitize(content, {
      WHOLE_DOCUMENT: true,
      ADD_TAGS: ['style', 'link', 'script', 'button', 'input', 'canvas', 'svg', 'select', 'textarea'],
      ADD_ATTR: ['target', 'onclick', 'onchange', 'style', 'id', 'class', 'type', 'value', 'placeholder', 'width', 'height'],
    });
  }, [content]);

  return (
    <div className="flex flex-col h-full bg-slate-900 overflow-hidden">
      {/* Security Status Bar */}
      <div className="bg-slate-950 px-3 py-1.5 border-b border-slate-800 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-1.5 text-slate-400">
          <span className="font-mono text-[10px] text-indigo-400">srcdoc preview</span>
        </div>
        <div className="flex items-center gap-1 text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
          <ShieldCheck className="w-3 h-3" />
          <span>Sandboxed: allow-scripts (No Parent Origin)</span>
        </div>
      </div>

      {/* Sandboxed iframe */}
      <iframe
        title={title}
        srcDoc={cleanHtml}
        // Strict security isolation: allow scripts to run for interactivity,
        // but intentionally omit allow-same-origin to block access to parent storage/cookies.
        sandbox="allow-scripts"
        className="w-full h-full border-none bg-white"
      />
    </div>
  );
};
