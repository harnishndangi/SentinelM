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
    <div className="w-full overflow-x-auto border border-slate-800 rounded-xl bg-slate-900/80 shadow-md">
      <table className="w-full text-left text-sm text-slate-300 border-collapse">
        <thead className="bg-slate-950/80 text-xs font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={clsx('py-3.5 px-4 font-semibold', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick && onRowClick(row)}
              className={clsx(
                'transition-colors hover:bg-slate-800/50',
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
