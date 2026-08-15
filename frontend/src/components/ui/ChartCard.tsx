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
    <div className={clsx('bg-[#101417] border border-[#252E3B] rounded-lg p-5 flex flex-col', className)}>
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#252E3B]">
        <div>
          <h3 className="text-sm font-bold text-white tracking-tight">{title}</h3>
          {subtitle && <p className="text-xs font-mono text-[#94a3b8] mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <div className="flex-1 w-full min-h-[260px] relative">{children}</div>
    </div>
  );
};

export default ChartCard;
