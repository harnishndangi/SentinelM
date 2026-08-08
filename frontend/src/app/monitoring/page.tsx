'use client';

import { useSentinelStore } from '@/store/useSentinelStore';

export default function MonitoringPage() {
  const { activeModelName, activeModelVersion, prAuc, recall } = useSentinelStore();

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Telemetry & Monitoring</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Live latency, throughput, prediction distribution, and hardware metrics.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-md mb-margin">
        <div className="bg-surface card-border rounded-lg p-md">
          <span className="text-body-sm text-on-surface-variant mb-1 block">p99 Latency</span>
          <span className="font-mono-metric text-[26px] text-on-surface">14.2 ms</span>
        </div>
        <div className="bg-surface card-border rounded-lg p-md">
          <span className="text-body-sm text-on-surface-variant mb-1 block">Inference Rate</span>
          <span className="font-mono-metric text-[26px] text-on-surface">1,420 req/s</span>
        </div>
        <div className="bg-surface card-border rounded-lg p-md">
          <span className="text-body-sm text-on-surface-variant mb-1 block">Error Rate</span>
          <span className="font-mono-metric text-[26px] text-status-success-text">0.01%</span>
        </div>
      </div>

      <div className="bg-surface card-border rounded-lg p-lg">
        <h3 className="text-display-md text-on-surface text-[18px] mb-4">Active Model Performance Metrics</h3>
        <div className="grid grid-cols-2 gap-4 font-mono-table text-body-md">
          <div className="p-4 bg-surface-container-low rounded border border-outline-variant">
            <span className="text-on-surface-variant">Model:</span>
            <div className="text-on-surface font-semibold text-[16px]">{activeModelName} {activeModelVersion}</div>
          </div>
          <div className="p-4 bg-surface-container-low rounded border border-outline-variant">
            <span className="text-on-surface-variant">PR-AUC / Recall:</span>
            <div className="text-on-surface font-semibold text-[16px]">{prAuc} / {recall}%</div>
          </div>
        </div>
      </div>
    </main>
  );
}
