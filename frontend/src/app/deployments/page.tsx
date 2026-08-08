'use client';

import { useSentinelStore } from '@/store/useSentinelStore';

export default function DeploymentsPage() {
  const { activeModelName, activeModelVersion, models } = useSentinelStore();

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Deployments & Canary Routes</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Production release channels, traffic split, and shadow evaluation.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-margin mb-margin">
        <div className="bg-surface card-border rounded-lg p-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-display-md text-on-surface text-[18px]">Production Traffic (90%)</h3>
            <span className="bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded text-mono-label text-xs">
              LIVE
            </span>
          </div>
          <div className="font-mono-metric text-[22px] text-on-surface mb-2">
            {activeModelName} {activeModelVersion}
          </div>
          <p className="text-body-sm text-on-surface-variant">
            Serving primary inference API traffic with 0.94 PR-AUC target.
          </p>
        </div>

        <div className="bg-surface card-border rounded-lg p-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-display-md text-on-surface text-[18px]">Canary Channel (10%)</h3>
            <span className="bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-mono-label text-xs">
              EVALUATING
            </span>
          </div>
          <div className="font-mono-metric text-[22px] text-on-surface mb-2">
            {activeModelName} v18 (LightGBM)
          </div>
          <p className="text-body-sm text-on-surface-variant">
            Shadow candidate evaluating real-time production inference payloads.
          </p>
        </div>
      </div>

      <div className="bg-surface card-border rounded-lg p-lg">
        <h3 className="text-display-md text-on-surface text-[18px] mb-4">Registered Target Artifacts</h3>
        <div className="space-y-3">
          {models.map((m) => (
            <div key={m.id} className="flex justify-between items-center p-3 rounded bg-surface-container-low border border-outline-variant">
              <div>
                <span className="font-mono-label text-on-surface font-semibold">{m.name} {m.version}</span>
                <span className="ml-3 text-body-sm text-on-surface-variant">({m.algorithm})</span>
              </div>
              <span className="font-mono-table text-on-surface-variant">PR-AUC: {m.prAuc}</span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
