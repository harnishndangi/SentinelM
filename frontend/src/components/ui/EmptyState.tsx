import React from 'react';
import { Database, Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Found',
  description = 'No records match the active filters or system criteria.',
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div className="w-full flex flex-col items-center justify-center p-8 border border-dashed border-slate-800 rounded-xl bg-slate-900/40 text-center">
      <div className="p-3 bg-slate-800/80 text-purple-400 rounded-full mb-3 shadow-inner">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-sm font-semibold text-slate-200 tracking-tight">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4 font-mono">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="text-xs font-mono font-medium px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors shadow-sm"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
