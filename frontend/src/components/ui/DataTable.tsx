import React from 'react';
import { clsx } from 'clsx';
import { EmptyState } from './EmptyState';
import { LoadingSkeleton } from './LoadingSkeleton';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  isLoading?: boolean;
  emptyMessage?: string;
  emptyTitle?: string;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyTitle = 'No data available',
  emptyMessage = 'There are no records to display at this time.',
  onRowClick,
}: DataTableProps<T>) {
  if (isLoading) {
    return <LoadingSkeleton count={5} height="h-12" className="my-2" />;
  }

  if (!data || data.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyMessage} />;
  }

  return (
    <div className="w-full overflow-x-auto border border-[#252E3B] rounded-lg bg-[#101417]">
      <table className="w-full text-left text-sm text-slate-300 border-collapse">
        <thead className="bg-[#101417] text-xs font-mono uppercase tracking-wider text-[#94a3b8] border-b border-[#252E3B]">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={clsx('py-3 px-4 font-semibold', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#252E3B] font-mono text-xs">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick && onRowClick(row)}
              className={clsx(
                'transition-colors hover:bg-[#181d23]',
                onRowClick && 'cursor-pointer'
              )}
            >
              {columns.map((col) => (
                <td key={col.key} className={clsx('py-3 px-4 text-slate-200', col.className)}>
                  {col.render ? col.render(row) : (row as any)[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
