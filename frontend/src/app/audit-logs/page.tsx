'use client';

export default function AuditLogsPage() {
  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Audit Logs</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Immutable security and administrative actions log for compliance auditing.
          </p>
        </div>
      </div>
      <div className="bg-surface card-border rounded-lg p-lg text-on-surface-variant font-mono-table text-body-md">
        Audit trail active. All model promotions and rollbacks are cryptographically logged.
      </div>
    </main>
  );
}
