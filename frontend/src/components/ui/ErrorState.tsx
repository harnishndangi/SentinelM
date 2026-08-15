import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  error?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load telemetry data',
  error = 'An error occurred while connecting to SentinelML API backend.',
  onRetry,
}) => {
  return (
    <div className="w-full p-6 border border-rose-500/30 rounded-xl bg-rose-950/20 text-center flex flex-col items-center justify-center">
      <AlertOctagon className="w-8 h-8 text-rose-400 mb-2" />
      <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
      <p className="text-xs text-rose-300/80 font-mono max-w-md mt-1 mb-4">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 text-xs font-mono font-medium px-4 py-2 bg-rose-900/60 hover:bg-rose-800 text-rose-100 rounded-lg border border-rose-500/40 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
};

export default ErrorState;
