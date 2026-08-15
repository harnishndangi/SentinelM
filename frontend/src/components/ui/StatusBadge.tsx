import React from 'react';
import { clsx } from 'clsx';
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw, Clock } from 'lucide-react';

export type StatusType = 
  | 'HEALTHY' 
  | 'DEGRADED' 
  | 'CRITICAL' 
  | 'RUNNING' 
  | 'SUCCESS' 
  | 'QUEUED' 
  | 'FAILED'
  | 'OPEN'
  | 'INVESTIGATING'
  | 'RESOLVED';

interface StatusBadgeProps {
  status: StatusType | string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const normStatus = (status || '').toUpperCase();

  const getStyle = () => {
    switch (normStatus) {
      case 'HEALTHY':
      case 'SUCCESS':
      case 'RESOLVED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'DEGRADED':
      case 'INVESTIGATING':
      case 'QUEUED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'CRITICAL':
      case 'FAILED':
      case 'OPEN':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'RUNNING':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const renderIcon = () => {
    if (!showIcon) return null;
    switch (normStatus) {
      case 'HEALTHY':
      case 'SUCCESS':
      case 'RESOLVED':
        return <CheckCircle2 className="w-3.5 h-3.5 mr-1" />;
      case 'DEGRADED':
      case 'INVESTIGATING':
        return <AlertTriangle className="w-3.5 h-3.5 mr-1" />;
      case 'CRITICAL':
      case 'FAILED':
      case 'OPEN':
        return <XCircle className="w-3.5 h-3.5 mr-1" />;
      case 'RUNNING':
        return <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" />;
      case 'QUEUED':
        return <Clock className="w-3.5 h-3.5 mr-1" />;
      default:
        return null;
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center font-mono font-medium border rounded-full uppercase tracking-wider',
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        getStyle()
      )}
    >
      {renderIcon()}
      {normStatus}
    </span>
  );
};

export default StatusBadge;
