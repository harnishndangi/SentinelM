'use client';

import { useState } from 'react';
import { useSentinelStore } from '@/store/useSentinelStore';

export default function DriftPage() {
  const { driftingFeatures, injectDrift, recoveryActivities } = useSentinelStore();
  const [notification, setNotification] = useState<string | null>(null);

  const handleRetrain = (featureName: string) => {
    injectDrift(featureName);
    setNotification(`Retraining pipeline scheduled for feature '${featureName}'. Model candidate v19 initializing...`);
    setTimeout(() => setNotification(null), 5000);
  };

  const handleQuarantine = (featureName: string) => {
    setNotification(`Feature '${featureName}' quarantined! Dynamic schema fallback activated.`);
    setTimeout(() => setNotification(null), 5000);
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-xl gap-md">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Drift Monitoring</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Real-time feature drift, concept drift, Kolmogorov-Smirnov test scores, & PSI metrics.
          </p>
        </div>
        <button
          onClick={() => handleRetrain('transaction_amount')}
          className="bg-primary text-on-primary px-lg py-sm rounded-DEFAULT text-mono-label font-mono-label hover:bg-primary-fixed transition-colors flex items-center gap-sm shadow-[0px_4px_20px_rgba(208,188,255,0.1)]"
        >
          <span className="material-symbols-outlined text-sm">bolt</span>
          Inject Test Drift
        </button>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div className="mb-6 p-4 bg-status-success/20 border border-status-success-text/40 rounded-lg text-status-success-text text-body-md font-mono-label flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined">auto_mode</span>
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-status-success-text hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* Statistical Drift Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md mb-margin">
        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">KS Statistic (Max)</span>
          <div className="flex items-end justify-between">
            <span className="font-mono-metric text-[24px] font-semibold text-status-error-text">0.28</span>
            <span className="bg-status-error text-status-error-text px-2 py-0.5 rounded text-[11px] font-mono-label font-bold">
              CRITICAL
            </span>
          </div>
        </div>

        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">Population Stability Index (PSI)</span>
          <div className="flex items-end justify-between">
            <span className="font-mono-metric text-[24px] font-semibold text-status-warning-text">0.19</span>
            <span className="bg-status-warning text-status-warning-text px-2 py-0.5 rounded text-[11px] font-mono-label font-bold">
              MODERATE
            </span>
          </div>
        </div>

        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">Wasserstein Distance</span>
          <div className="flex items-end justify-between">
            <span className="font-mono-metric text-[24px] font-semibold text-on-surface">0.12</span>
            <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded text-[11px] font-mono-label font-bold">
              NORMAL
            </span>
          </div>
        </div>

        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">Concept Drift Index</span>
          <div className="flex items-end justify-between">
            <span className="font-mono-metric text-[24px] font-semibold text-status-success-text">0.04</span>
            <span className="bg-status-success text-status-success-text px-2 py-0.5 rounded text-[11px] font-mono-label font-bold">
              STABLE
            </span>
          </div>
        </div>
      </div>

      {/* Feature Drift Analysis Table */}
      <div className="bg-surface border border-outline-variant rounded-lg overflow-hidden mb-margin">
        <div className="p-md border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
          <h3 className="text-display-md font-display-md text-on-surface text-[18px]">
            Feature-Level Drift Breakdown
          </h3>
          <span className="text-mono-label font-mono-label text-on-surface-variant text-body-sm">
            Refreshed 2m ago
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low text-mono-table font-mono-table text-on-surface-variant">
                <th className="table-cell-padding font-medium">FEATURE</th>
                <th className="table-cell-padding font-medium">STATISTICAL TEST</th>
                <th className="table-cell-padding font-medium">DRIFT SCORE</th>
                <th className="table-cell-padding font-medium">P-VALUE</th>
                <th className="table-cell-padding font-medium">STATUS</th>
                <th className="table-cell-padding font-medium text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="text-body-md font-body-md divide-y divide-outline-variant">
              {driftingFeatures.map((item) => (
                <tr key={item.featureName} className="hover:bg-surface-container transition-colors">
                  <td className="table-cell-padding font-mono-table text-on-surface font-semibold">
                    {item.featureName}
                  </td>
                  <td className="table-cell-padding text-on-surface-variant">{item.testType}</td>
                  <td className="table-cell-padding text-mono-metric font-mono-metric text-on-surface">
                    {item.driftScore}
                  </td>
                  <td className="table-cell-padding text-mono-table font-mono-table text-on-surface-variant">
                    {item.pValue}
                  </td>
                  <td className="table-cell-padding">
                    {item.status === 'High' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-mono-table font-mono-table bg-status-error text-status-error-text border border-status-error-text/30">
                        HIGH DRIFT
                      </span>
                    )}
                    {item.status === 'Medium' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-mono-table font-mono-table bg-status-warning text-status-warning-text border border-status-warning-text/30">
                        MEDIUM DRIFT
                      </span>
                    )}
                    {item.status === 'Low' && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-mono-table font-mono-table bg-surface-variant text-on-surface-variant border border-outline-variant">
                        LOW
                      </span>
                    )}
                  </td>
                  <td className="table-cell-padding text-right space-x-2">
                    <button
                      onClick={() => handleRetrain(item.featureName)}
                      className="px-3 py-1 rounded bg-primary/10 text-primary border border-primary/30 text-mono-label font-mono-label hover:bg-primary hover:text-on-primary transition-colors"
                    >
                      Trigger Retraining
                    </button>
                    <button
                      onClick={() => handleQuarantine(item.featureName)}
                      className="px-3 py-1 rounded bg-surface-container-high text-on-surface-variant hover:text-status-error-text hover:bg-status-error transition-colors text-mono-label font-mono-label"
                    >
                      Quarantine
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recovery Log Snapshot */}
      <div className="bg-surface card-border rounded-lg p-lg">
        <h3 className="text-display-md text-on-surface text-[18px] mb-4">
          Self-Healing Recovery Log
        </h3>
        <div className="space-y-3">
          {recoveryActivities.map((act) => (
            <div
              key={act.id}
              className="flex items-center justify-between p-3 rounded bg-surface-container-low border border-outline-variant/50 text-body-sm"
            >
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-[18px]">
                  {act.isCurrent ? 'sync' : 'check_circle'}
                </span>
                <span className="text-on-surface font-mono-label">{act.title}</span>
              </div>
              <span className="text-on-surface-variant font-mono-table text-[11px]">{act.timeAgo}</span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
