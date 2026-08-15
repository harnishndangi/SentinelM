import React from 'react';
import { clsx } from 'clsx';
import { AlertCircle, AlertOctagon, ShieldAlert, Info } from 'lucide-react';

export type SeverityType = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

interface SeverityBadgeProps {
  severity: SeverityType | string;
  size?: 'sm' | 'md';
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  size = 'md',
}) => {
  const normSeverity = (severity || 'MEDIUM').toUpperCase();

  const getStyle = () => {
    switch (normSeverity) {
      case 'CRITICAL':
        return 'bg-red-500/15 text-red-400 border-red-500/40 font-bold';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/40 font-semibold';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'LOW':
      case 'INFO':
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
      default:
        return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
    }
  };

  const renderIcon = () => {
    switch (normSeverity) {
      case 'CRITICAL':
        return <AlertOctagon className="w-3.5 h-3.5 mr-1 text-red-400" />;
      case 'HIGH':
        return <ShieldAlert className="w-3.5 h-3.5 mr-1 text-orange-400" />;
      case 'MEDIUM':
        return <AlertCircle className="w-3.5 h-3.5 mr-1 text-amber-400" />;
      default:
        return <Info className="w-3.5 h-3.5 mr-1 text-blue-400" />;
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center font-mono border rounded-md uppercase tracking-wider',
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        getStyle()
      )}
    >
      {renderIcon()}
      {normSeverity}
    </span>
  );
};

export default SeverityBadge;
