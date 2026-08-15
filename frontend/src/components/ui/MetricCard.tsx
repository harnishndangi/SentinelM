import React from 'react';
import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  subValue?: string;
  icon?: React.ReactNode;
  status?: 'good' | 'warning' | 'bad' | 'neutral';
  highlight?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel = 'vs last period',
  subValue,
  icon,
  status = 'neutral',
  highlight = false,
}) => {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;

  const getStatusBorder = () => {
    switch (status) {
      case 'good':
        return 'border-l-4 border-l-emerald-500';
      case 'warning':
        return 'border-l-4 border-l-amber-500';
      case 'bad':
        return 'border-l-4 border-l-rose-500';
      default:
        return '';
    }
  };

  return (
    <div
      className={clsx(
        'relative bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg transition-all hover:border-slate-700',
        highlight && 'bg-gradient-to-br from-purple-950/30 to-slate-900 border-purple-500/30',
        getStatusBorder()
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-400 tracking-wider uppercase">{title}</span>
        {icon && <div className="text-purple-400 bg-purple-500/10 p-2 rounded-lg">{icon}</div>}
      </div>

      <div className="flex items-baseline justify-between">
        <div className="text-2xl md:text-3xl font-bold font-mono text-slate-100 tracking-tight">
          {value}
        </div>
        {change !== undefined && (
          <div
            className={clsx(
              'flex items-center text-xs font-mono font-medium px-2 py-0.5 rounded-md',
              isPositive && 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
              isNegative && 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
              !isPositive && !isNegative && 'bg-slate-800 text-slate-400'
            )}
          >
            {isPositive && <TrendingUp className="w-3 h-3 mr-1" />}
            {isNegative && <TrendingDown className="w-3 h-3 mr-1" />}
            {!isPositive && !isNegative && <Minus className="w-3 h-3 mr-1" />}
            {change > 0 ? `+${change}%` : `${change}%`}
          </div>
        )}
      </div>

      {(subValue || changeLabel) && (
        <div className="mt-2 text-[11px] text-slate-400 font-mono flex items-center justify-between">
          {subValue && <span>{subValue}</span>}
          {changeLabel && <span className="text-slate-500">{changeLabel}</span>}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
