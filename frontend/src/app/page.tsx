'use client';

import { useState } from 'react';
import { useSentinelStore } from '@/store/useSentinelStore';

export default function Home() {
  const {
    activeModelName,
    activeModelVersion,
    activeModelAlgorithm,
    modelHealth,
    healthTrend,
    prAuc,
    prAucTrend,
    recall,
    openIncidentsCount,
    dataDriftPercentage,
    dataDriftLevel,
    predictionDriftPercentage,
    predictionDriftLevel,
    driftingFeatures,
    recoveryActivities,
    injectDrift,
  } = useSentinelStore();

  const [activeMetric, setActiveMetric] = useState<'PR-AUC' | 'Recall'>('PR-AUC');
  const [timeRange, setTimeRange] = useState('Last 24h');
  const [isDriftModalOpen, setIsDriftModalOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState('transaction_amount');
  const [driftNotification, setDriftNotification] = useState<string | null>(null);

  const handleInjectDrift = () => {
    injectDrift(selectedFeature);
    setIsDriftModalOpen(false);
    setDriftNotification(`Drift simulation injected for feature '${selectedFeature}'. Self-healing workflow triggered!`);
    setTimeout(() => setDriftNotification(null), 5000);
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      {/* Header Actions */}
      <div className="flex items-end justify-between mb-margin">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface mb-1">Control Center</h2>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Monitor and recover your production ML systems.
          </p>
        </div>
        <div className="flex items-center gap-md">
          {/* Time Filter Select */}
          <div className="flex items-center bg-surface-container-low card-border rounded px-3 py-2 text-on-surface-variant cursor-pointer hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-[18px] mr-2">calendar_today</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-transparent font-mono-label text-mono-label border-none outline-none cursor-pointer text-on-surface pr-2 focus:ring-0"
            >
              <option value="Last 1h">Last 1h</option>
              <option value="Last 24h">Last 24h</option>
              <option value="Last 7d">Last 7d</option>
              <option value="Last 30d">Last 30d</option>
            </select>
          </div>

          {/* Inject Drift Action Button */}
          <button
            onClick={() => setIsDriftModalOpen(true)}
            className="bg-primary text-on-primary font-mono-label text-mono-label px-4 py-2 rounded flex items-center gap-2 hover:bg-primary-fixed-dim transition-colors shadow-sm"
          >
            <span className="material-symbols-outlined text-[18px]">bolt</span>
            Inject Drift
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {driftNotification && (
        <div className="mb-4 p-3 bg-status-warning/20 border border-status-warning-text/40 rounded-lg text-status-warning-text text-body-sm font-mono-label flex items-center justify-between animate-bounce">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">warning</span>
            <span>{driftNotification}</span>
          </div>
          <button onClick={() => setDriftNotification(null)} className="text-status-warning-text hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* System Health Banner */}
      <div className="w-full bg-status-success card-border rounded-lg p-md mb-margin flex items-center gap-3">
        <span className="material-symbols-outlined text-status-success-text">check_circle</span>
        <span className="font-mono-label text-mono-label font-bold text-status-success-text tracking-wider uppercase">
          ● SYSTEM OPERATIONAL
        </span>
      </div>

      {/* Metric Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-md mb-margin">
        {/* Card 1: Production Model */}
        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between col-span-2">
          <div className="flex justify-between items-start mb-2">
            <span className="text-body-sm font-body-sm text-on-surface-variant">Production Model</span>
            <span className="bg-surface-container-high text-primary px-2 py-0.5 rounded text-[10px] font-mono-label uppercase tracking-widest border border-primary/20">
              Active
            </span>
          </div>
          <div className="font-mono-metric text-mono-metric text-on-surface">
            {activeModelName} {activeModelVersion}
          </div>
          <div className="text-body-sm font-body-sm text-on-surface-variant mt-1">
            ({activeModelAlgorithm})
          </div>
        </div>

        {/* Card 2: Model Health */}
        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">Model Health</span>
          <div className="flex items-end gap-2">
            <span className="font-mono-metric text-[24px] font-semibold text-on-surface leading-none">
              {modelHealth}%
            </span>
            <span className="text-mono-label font-mono-label metric-trend-down flex items-center leading-none pb-0.5">
              <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
              {Math.abs(healthTrend)}%
            </span>
          </div>
        </div>

        {/* Card 3: PR-AUC */}
        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">PR-AUC</span>
          <div className="flex items-end gap-2">
            <span className="font-mono-metric text-[24px] font-semibold text-on-surface leading-none">
              {prAuc}
            </span>
            <span className="text-mono-label font-mono-label metric-trend-up flex items-center leading-none pb-0.5">
              <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
              {prAucTrend}%
            </span>
          </div>
        </div>

        {/* Card 4: Recall */}
        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">Recall</span>
          <div className="flex items-end gap-2">
            <span className="font-mono-metric text-[24px] font-semibold text-on-surface leading-none">
              {recall}%
            </span>
          </div>
        </div>

        {/* Card 5: Open Incidents */}
        <div className="bg-surface card-border rounded-lg p-md flex flex-col justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant mb-2">Open Incidents</span>
          <div className="flex items-end gap-2">
            <span className="font-mono-metric text-[24px] font-semibold text-status-error-text leading-none">
              {openIncidentsCount}
            </span>
          </div>
        </div>
      </div>

      {/* Bento Grid Bottom */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-margin">
        {/* Main Chart Area */}
        <div className="lg:col-span-2 bg-surface card-border rounded-lg p-lg flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-display-md font-display-md text-on-surface text-[18px]">
              Model Performance
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveMetric('PR-AUC')}
                className={`px-2 py-1 rounded text-mono-label font-mono-label transition-colors ${
                  activeMetric === 'PR-AUC'
                    ? 'bg-surface-container-high text-on-surface border border-outline-variant'
                    : 'text-on-surface-variant hover:bg-surface-container'
                }`}
              >
                PR-AUC
              </button>
              <button
                onClick={() => setActiveMetric('Recall')}
                className={`px-2 py-1 rounded text-mono-label font-mono-label transition-colors ${
                  activeMetric === 'Recall'
                    ? 'bg-surface-container-high text-on-surface border border-outline-variant'
                    : 'text-on-surface-variant hover:bg-surface-container'
                }`}
              >
                Recall
              </button>
            </div>
          </div>

          {/* SVG Chart Mockup */}
          <div className="flex-1 w-full relative min-h-[200px]">
            <svg className="w-full h-full preserve-aspect-ratio-none" viewBox="0 0 1000 300">
              {/* Grid */}
              <line className="chart-grid" x1="0" x2="1000" y1="50" y2="50"></line>
              <line className="chart-grid" x1="0" x2="1000" y1="150" y2="150"></line>
              <line className="chart-grid" x1="0" x2="1000" y1="250" y2="250"></line>

              {/* Dynamic Line Curve */}
              {activeMetric === 'PR-AUC' ? (
                <path
                  className="chart-line"
                  d="M0,200 L100,190 L200,210 L300,180 L400,190 L500,150 L600,160 L700,120 L800,100 L900,90 L1000,95"
                ></path>
              ) : (
                <path
                  className="chart-line"
                  stroke="#7bd0ff"
                  d="M0,150 L100,140 L200,160 L300,130 L400,140 L500,110 L600,120 L700,80 L800,70 L900,60 L1000,65"
                ></path>
              )}

              {/* Promotion Annotation Line */}
              <line stroke="#4ade80" strokeDasharray="4" strokeWidth="1" x1="700" x2="700" y1="0" y2="300"></line>
            </svg>

            {/* Annotation Label */}
            <div className="absolute top-[20px] left-[610px] bg-surface-container-high border border-[#4ade80]/30 px-2 py-1 rounded text-[10px] font-mono-label text-[#4ade80]">
              v17 promoted
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-margin">
          {/* Drift Overview */}
          <div className="bg-surface card-border rounded-lg p-lg">
            <h3 className="text-display-md font-display-md text-on-surface text-[18px] mb-4">
              Drift Overview
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-body-md font-body-md text-on-surface">Data Drift</span>
                  <span className="text-mono-label font-mono-label text-status-error-text bg-status-error px-2 py-0.5 rounded">
                    {dataDriftLevel}
                  </span>
                </div>
                <div className="w-full bg-surface-container-highest rounded-full h-1.5">
                  <div
                    className="bg-status-error-text h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${dataDriftPercentage}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-body-md font-body-md text-on-surface">Prediction Drift</span>
                  <span className="text-mono-label font-mono-label text-status-warning-text bg-status-warning px-2 py-0.5 rounded">
                    {predictionDriftLevel}
                  </span>
                </div>
                <div className="w-full bg-surface-container-highest rounded-full h-1.5">
                  <div
                    className="bg-status-warning-text h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${predictionDriftPercentage}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <span className="text-body-sm font-body-sm text-on-surface-variant mb-2 block">
                Top Drifting Features
              </span>
              <div className="space-y-2">
                {driftingFeatures.map((feat) => (
                  <div
                    key={feat.featureName}
                    className="flex justify-between items-center p-2 rounded bg-surface-container-low border border-outline-variant/50"
                  >
                    <span className="font-mono-table text-mono-table text-on-surface">
                      {feat.featureName}
                    </span>
                    <span
                      className={`material-symbols-outlined text-[16px] ${
                        feat.status === 'High' ? 'text-status-error-text' : 'text-status-warning-text'
                      }`}
                    >
                      trending_up
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recovery Activity */}
          <div className="bg-surface card-border rounded-lg p-lg flex-1">
            <h3 className="text-display-md font-display-md text-on-surface text-[18px] mb-4">
              Recovery Activity
            </h3>
            <div className="relative border-l border-outline-variant ml-3 space-y-6">
              {recoveryActivities.map((act) => (
                <div key={act.id} className="relative pl-6">
                  {act.isCurrent ? (
                    <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-primary flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                    </div>
                  ) : (
                    <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-[#4ade80] flex items-center justify-center">
                      <span className="material-symbols-outlined text-[10px] text-[#4ade80]">check</span>
                    </div>
                  )}
                  <p
                    className={`text-body-md font-body-md ${
                      act.isCurrent
                        ? 'text-on-surface font-medium'
                        : 'text-on-surface-variant line-through opacity-70'
                    }`}
                  >
                    {act.title}
                  </p>
                  <span className="text-body-sm font-body-sm text-on-surface-variant opacity-70">
                    {act.timeAgo}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Drift Injection Modal */}
      {isDriftModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-high border border-outline-variant rounded-xl p-lg max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-display-md text-[20px] text-on-surface font-semibold flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">bolt</span>
                Inject Drift Simulation
              </h3>
              <button
                onClick={() => setIsDriftModalOpen(false)}
                className="text-on-surface-variant hover:text-on-surface"
              >
                ✕
              </button>
            </div>
            <p className="text-body-md text-on-surface-variant mb-4">
              Simulate statistical feature drift on your active production model to test automated self-healing triggers.
            </p>
            <div className="mb-6">
              <label className="block text-mono-label text-mono-label text-on-surface mb-2">
                Target Feature:
              </label>
              <select
                value={selectedFeature}
                onChange={(e) => setSelectedFeature(e.target.value)}
                className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
              >
                <option value="transaction_amount">transaction_amount (Numerical)</option>
                <option value="device_type">device_type (Categorical)</option>
                <option value="user_age">user_age (Numerical)</option>
                <option value="ip_risk_score">ip_risk_score (Probability)</option>
              </select>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setIsDriftModalOpen(false)}
                className="px-4 py-2 rounded text-on-surface-variant hover:bg-surface-container font-mono-label"
              >
                Cancel
              </button>
              <button
                onClick={handleInjectDrift}
                className="bg-primary text-on-primary font-mono-label font-bold px-4 py-2 rounded hover:bg-primary-fixed-dim transition-colors"
              >
                Inject Drift Now
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
