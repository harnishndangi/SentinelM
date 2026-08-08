'use client';

import { useSentinelStore } from '@/store/useSentinelStore';

export default function IncidentsPage() {
  const incidents = useSentinelStore((state) => state.incidents);

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Active Incidents</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Track and resolve automated ML reliability incidents and SLA breaches.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {incidents.map((inc) => (
          <div key={inc.id} className="bg-surface card-border rounded-lg p-lg flex items-center justify-between">
            <div className="flex items-start gap-4">
              <span className="material-symbols-outlined text-status-error-text text-[28px]">warning</span>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-display-md text-on-surface text-[16px] font-semibold">{inc.title}</h3>
                  <span className="bg-status-error text-status-error-text px-2 py-0.5 rounded text-[10px] font-mono-label uppercase">
                    {inc.severity}
                  </span>
                </div>
                <p className="text-body-sm text-on-surface-variant font-mono-label">
                  Affected: {inc.affectedModel} • Created {inc.createdAt}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="px-3 py-1 rounded bg-surface-container-high text-primary border border-primary/20 text-mono-label font-mono-label">
                {inc.status}
              </span>
              <button
                onClick={() => alert(`Investigating incident ${inc.id}...`)}
                className="px-4 py-2 rounded bg-primary text-on-primary font-mono-label hover:bg-primary-fixed transition-colors"
              >
                Resolve Incident
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
