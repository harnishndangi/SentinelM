import React from 'react';
import { clsx } from 'clsx';
import { AlertTriangle, CheckCircle, Info, XCircle, X } from 'lucide-react';

export type AlertType = 'info' | 'warning' | 'error' | 'success';

interface AlertBannerProps {
  type?: AlertType;
  title: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
  onClose?: () => void;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'info',
  title,
  message,
  actionText,
  onAction,
  onClose,
  className,
}) => {
  const getStyle = () => {
    switch (type) {
      case 'success':
        return 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300';
      case 'warning':
        return 'bg-amber-950/40 border-amber-500/40 text-amber-300';
      case 'error':
        return 'bg-rose-950/40 border-rose-500/40 text-rose-300';
      case 'info':
      default:
        return 'bg-sky-950/40 border-sky-500/40 text-sky-300';
    }
  };

  const renderIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-rose-400 shrink-0" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-sky-400 shrink-0" />;
    }
  };

  return (
    <div
      className={clsx(
        'w-full border rounded-xl p-4 flex items-start justify-between gap-3 shadow-md backdrop-blur-sm',
        getStyle(),
        className
      )}
    >
      <div className="flex items-start gap-3">
        {renderIcon()}
        <div>
          <h4 className="text-sm font-semibold tracking-tight">{title}</h4>
          {message && <p className="text-xs opacity-90 mt-0.5">{message}</p>}
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        {actionText && onAction && (
          <button
            onClick={onAction}
            className="text-xs font-mono font-semibold px-3 py-1 rounded-md bg-white/10 hover:bg-white/20 transition-colors"
          >
            {actionText}
          </button>
        )}
        {onClose && (
          <button onClick={onClose} className="p-1 rounded-md hover:bg-white/10 opacity-70 hover:opacity-100">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default AlertBanner;
