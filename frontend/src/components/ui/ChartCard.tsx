import React from 'react';
import { clsx } from 'clsx';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  actions,
  children,
  className,
}) => {
  return (
    <div className={clsx('bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col', className)}>
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 tracking-tight">{title}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <div className="flex-1 w-full min-h-[260px] relative">{children}</div>
    </div>
  );
};

export default ChartCard;
