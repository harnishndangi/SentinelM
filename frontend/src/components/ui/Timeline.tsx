import React from 'react';
import { clsx } from 'clsx';
import { CheckCircle2, Clock, AlertOctagon, Activity } from 'lucide-react';

export interface TimelineEvent {
  id: string;
  title: string;
  timestamp: string;
  description?: string;
  status?: 'completed' | 'running' | 'failed' | 'queued';
  tag?: string;
}

interface TimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ events, className }) => {
  if (!events || events.length === 0) {
    return <div className="text-xs text-slate-500 font-mono italic p-3">No activity recorded.</div>;
  }

  const renderStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'failed':
        return <AlertOctagon className="w-4 h-4 text-rose-400" />;
      case 'running':
        return <Activity className="w-4 h-4 text-sky-400 animate-spin" />;
      case 'queued':
      default:
        return <Clock className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className={clsx('relative border-l border-slate-800 ml-3 space-y-6 py-2', className)}>
      {events.map((evt, idx) => (
        <div key={evt.id || idx} className="relative pl-6">
          <div className="absolute -left-2.5 top-0.5 bg-slate-900 border border-slate-800 p-0.5 rounded-full">
            {renderStatusIcon(evt.status)}
          </div>
          <div className="flex flex-col">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-mono font-medium text-slate-200">{evt.title}</span>
              <span className="text-[11px] font-mono text-slate-500 shrink-0">{evt.timestamp}</span>
            </div>
            {evt.description && (
              <p className="text-xs text-slate-400 mt-1 font-mono">{evt.description}</p>
            )}
            {evt.tag && (
              <span className="mt-1.5 self-start text-[10px] font-mono px-2 py-0.5 bg-purple-950/40 text-purple-300 border border-purple-800/40 rounded">
                {evt.tag}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Timeline;
