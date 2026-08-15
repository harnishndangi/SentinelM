import React from 'react';
import { clsx } from 'clsx';

interface LoadingSkeletonProps {
  count?: number;
  height?: string;
  className?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 3,
  height = 'h-10',
  className,
}) => {
  return (
    <div className="w-full space-y-3">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className={clsx(
            'w-full bg-slate-800/60 animate-pulse rounded-lg border border-slate-800',
            height,
            className
          )}
        />
      ))}
    </div>
  );
};

export default LoadingSkeleton;
