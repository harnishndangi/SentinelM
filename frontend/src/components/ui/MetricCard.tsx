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
        return 'border-l-2 border-l-emerald-500';
      case 'warning':
        return 'border-l-2 border-l-amber-500';
      case 'bad':
        return 'border-l-2 border-l-rose-500';
      default:
        return '';
    }
  };

  return (
    <div
      className={clsx(
        'relative bg-[#101417] border border-[#252E3B] rounded-lg p-4 transition-all hover:border-[#384659]',
        highlight && 'border-purple-500/40 bg-gradient-to-br from-[#101417] to-purple-950/20',
        getStatusBorder()
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono font-medium text-[#94a3b8] tracking-tight">{title}</span>
        {icon && <div className="text-purple-400 bg-purple-500/10 p-1.5 rounded">{icon}</div>}
      </div>

      <div className="flex items-baseline justify-between">
        <div className="text-2xl md:text-3xl font-bold font-mono text-white tracking-tight">
          {value}
        </div>
        {change !== undefined && (
          <div
            className={clsx(
              'flex items-center text-xs font-mono font-medium px-2 py-0.5 rounded',
              isPositive && 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
              isNegative && 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
              !isPositive && !isNegative && 'bg-[#181d22] text-slate-400 border border-[#252E3B]'
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
        <div className="mt-2 text-[11px] text-[#94a3b8] font-mono flex items-center justify-between">
          {subValue && <span>{subValue}</span>}
          {changeLabel && <span className="text-slate-500">{changeLabel}</span>}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
