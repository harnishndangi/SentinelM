import React from 'react';
import { clsx } from 'clsx';
import { Cpu } from 'lucide-react';

interface ModelBadgeProps {
  modelName: string;
  version?: string;
  isActive?: boolean;
}

export const ModelBadge: React.FC<ModelBadgeProps> = ({
  modelName,
  version,
  isActive = true,
}) => {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-200 font-mono text-xs shadow-sm">
      <Cpu className="w-3.5 h-3.5 text-purple-400" />
      <span className="font-semibold text-slate-100">{modelName}</span>
      {version && (
        <span className="text-purple-300 bg-purple-900/40 px-1.5 py-0.5 rounded text-[11px] font-bold border border-purple-500/30">
          {version}
        </span>
      )}
      {isActive && (
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-0.5" title="Active Model Version" />
      )}
    </div>
  );
};

export default ModelBadge;
