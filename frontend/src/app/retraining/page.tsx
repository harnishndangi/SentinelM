'use client';

import { useState, useEffect, useRef } from 'react';
import { useSentinelStore } from '@/store/useSentinelStore';

interface LogLine {
  id: string;
  time: string;
  level: 'INFO' | 'SUCCESS' | 'WARN' | 'EPOCH';
  message: string;
}

export default function RetrainingPage() {
  const { promoteModel, models } = useSentinelStore();

  const [status, setStatus] = useState<'IN PROGRESS' | 'COMPLETED' | 'CANCELLED'>('IN PROGRESS');
  const [currentEpoch, setCurrentEpoch] = useState(47);
  const [prAucMetric, setPrAucMetric] = useState(0.9108);
  const [recallMetric, setRecallMetric] = useState(0.769);
  const [notification, setNotification] = useState<string | null>(null);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  const initialLogs: LogLine[] = [
    { id: '1', time: '11:42:01', level: 'INFO', message: 'Initializing execution environment...' },
    { id: '2', time: '11:42:05', level: 'INFO', message: 'Provisioning compute cluster (n_workers=8, instance=ml.c5.4xlarge)...' },
    { id: '3', time: '11:42:11', level: 'INFO', message: 'Loading dataset fraud-v13 from s3://sentinel-data-prod/...' },
    { id: '4', time: '11:42:25', level: 'SUCCESS', message: 'Dataset loaded. 14,284,591 rows, 128 features.' },
    { id: '5', time: '11:42:26', level: 'INFO', message: 'Running data validation expectations (GreatExpectations suite)...' },
    { id: '6', time: '11:43:30', level: 'WARN', message: "Feature 'tx_amount_rolling_24h' has 0.05% nulls. Applying median imputation." },
    { id: '7', time: '11:43:38', level: 'SUCCESS', message: 'Validation passed. 42/42 expectations met.' },
    { id: '8', time: '11:43:40', level: 'INFO', message: 'Starting Feature Engineering block...' },
    { id: '9', time: '11:52:15', level: 'SUCCESS', message: 'Feature matrix constructed. Dimensionality: 412.' },
    { id: '10', time: '11:52:20', level: 'INFO', message: 'Starting XGBoost Model Training...' },
    { id: '11', time: '11:52:25', level: 'EPOCH', message: '[1/100] loss: 0.8412, pr_auc: 0.6510' },
    { id: '12', time: '11:53:10', level: 'EPOCH', message: '[10/100] loss: 0.4128, pr_auc: 0.7812' },
    { id: '13', time: '11:55:40', level: 'EPOCH', message: '[20/100] loss: 0.3185, pr_auc: 0.8245' },
    { id: '14', time: '11:56:30', level: 'EPOCH', message: '[30/100] loss: 0.2514, pr_auc: 0.8651' },
    { id: '15', time: '11:57:15', level: 'EPOCH', message: '[40/100] loss: 0.2101, pr_auc: 0.8870' },
    { id: '16', time: '11:57:17', level: 'EPOCH', message: '[47/100] loss: 0.1868, pr_auc: 0.8988' },
    { id: '17', time: '11:57:20', level: 'EPOCH', message: '[48/100] loss: 0.1841, pr_auc: 0.9000' },
  ];

  const [logs, setLogs] = useState<LogLine[]>(initialLogs);

  // Auto-scroll terminal log to bottom
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Live training progress simulation
  useEffect(() => {
    if (status !== 'IN PROGRESS') return;

    const interval = setInterval(() => {
      setCurrentEpoch((prev) => {
        if (prev >= 100) {
          setStatus('COMPLETED');
          clearInterval(interval);
          return 100;
        }
        const nextEpoch = prev + 1;
        const loss = (0.1841 * Math.exp(-0.012 * (nextEpoch - 48))).toFixed(4);
        const auc = (0.9000 + (nextEpoch - 48) * 0.0011).toFixed(4);
        setPrAucMetric(parseFloat(auc));
        setRecallMetric((r) => parseFloat((r + 0.001).toFixed(3)));

        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];

        setLogs((existingLogs) => [
          ...existingLogs,
          {
            id: `log-${Date.now()}`,
            time: timeStr,
            level: 'EPOCH',
            message: `[${nextEpoch}/100] loss: ${loss}, pr_auc: ${auc}`,
          },
        ]);

        return nextEpoch;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [status]);

  const handleCancel = () => {
    setStatus('CANCELLED');
    const now = new Date().toTimeString().split(' ')[0];
    setLogs((prev) => [
      ...prev,
      { id: `log-${Date.now()}`, time: now, level: 'WARN', message: 'Training run cancelled by administrator.' },
    ]);
    setNotification('Retraining execution run cancelled.');
    setTimeout(() => setNotification(null), 5000);
  };

  const handleDeployCandidate = () => {
    const candidate = models.find((m) => m.version === 'v18');
    if (candidate) {
      promoteModel(candidate.id);
    }
    setStatus('COMPLETED');
    setNotification('Candidate FraudDetector v18 successfully deployed to PRODUCTION!');
    setTimeout(() => setNotification(null), 6000);
  };

  return (
    <main className="flex-1 p-6 overflow-y-auto bg-background w-full h-full flex flex-col">
      {/* Top Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-display-lg text-2xl md:text-3xl font-display-lg text-on-surface font-bold tracking-tight">
              Retraining - FraudDetector v18
            </h1>
            {status === 'IN PROGRESS' && (
              <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs px-2.5 py-1 rounded-full flex items-center gap-1.5 font-mono-label font-bold uppercase tracking-wider animate-pulse">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                IN PROGRESS
              </span>
            )}
            {status === 'COMPLETED' && (
              <span className="bg-green-500/10 text-green-400 border border-green-500/30 text-xs px-2.5 py-1 rounded-full flex items-center gap-1 font-mono-label font-bold uppercase tracking-wider">
                ✓ COMPLETED
              </span>
            )}
            {status === 'CANCELLED' && (
              <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 text-xs px-2.5 py-1 rounded-full flex items-center gap-1 font-mono-label font-bold uppercase tracking-wider">
                ✕ CANCELLED
              </span>
            )}
          </div>

          <p className="text-body-sm font-mono-table text-on-surface-variant">
            Run ID: <span className="text-on-surface font-semibold">trn-8f9a2b1c-4e5d</span> • Triggered by:{' '}
            <span className="text-primary font-semibold">Model Drift Alert (Recall drop)</span>
          </p>
        </div>

        {/* Right Top Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleCancel}
            disabled={status !== 'IN PROGRESS'}
            className="px-4 py-2 rounded text-body-sm font-mono-label font-semibold border border-outline-variant hover:bg-surface-container text-on-surface-variant transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            CANCEL RUN
          </button>
          <button
            onClick={handleDeployCandidate}
            className={`px-4 py-2 rounded text-body-sm font-mono-label font-bold flex items-center gap-2 transition-all ${
              status === 'IN PROGRESS' || status === 'COMPLETED'
                ? 'bg-primary text-on-primary hover:bg-primary-fixed cursor-pointer shadow-[0px_4px_20px_rgba(208,188,255,0.2)]'
                : 'bg-surface-container-high text-on-surface-variant opacity-60 cursor-not-allowed border border-outline-variant'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
            DEPLOY CANDIDATE
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div className="mb-4 p-3.5 bg-status-success/20 border border-status-success-text/40 rounded-lg text-status-success-text text-body-sm font-mono-label flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px]">task_alt</span>
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-status-success-text hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 items-start">
        {/* Left Column (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Live Training Metrics */}
          <div className="bg-surface card-border rounded-lg p-5">
            <h3 className="text-xs font-mono-label text-on-surface-variant tracking-wider uppercase font-semibold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">show_chart</span>
              Live Training Metrics
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface-container-low border border-outline-variant/60 rounded-lg p-3">
                <span className="text-[11px] font-mono-label text-on-surface-variant block mb-1">PR AUC</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="font-mono-metric text-[22px] font-semibold text-on-surface leading-none">
                    {prAucMetric}
                  </span>
                  <span className="text-[11px] font-mono-label text-status-success-text font-bold">↑2.1%</span>
                </div>
              </div>

              <div className="bg-surface-container-low border border-outline-variant/60 rounded-lg p-3">
                <span className="text-[11px] font-mono-label text-on-surface-variant block mb-1">Recall @ 5% FPR</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="font-mono-metric text-[22px] font-semibold text-on-surface leading-none">
                    {recallMetric}
                  </span>
                  <span className="text-[11px] font-mono-label text-status-success-text font-bold">↑4.5%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Execution Pipeline Stepper */}
          <div className="bg-surface card-border rounded-lg p-5">
            <h3 className="text-xs font-mono-label text-on-surface-variant tracking-wider uppercase font-semibold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">schema</span>
              Execution Pipeline
            </h3>

            <div className="relative border-l border-outline-variant ml-3 space-y-5">
              {/* Step 1 */}
              <div className="relative pl-6">
                <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-[#4ade80] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[10px] text-[#4ade80]">check</span>
                </div>
                <p className="text-body-md font-body-md font-semibold text-on-surface">Dataset Snapshot</p>
                <span className="text-body-sm font-mono-table text-on-surface-variant">Completed in 42s</span>
              </div>

              {/* Step 2 */}
              <div className="relative pl-6">
                <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-[#4ade80] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[10px] text-[#4ade80]">check</span>
                </div>
                <p className="text-body-md font-body-md font-semibold text-on-surface">Data Validation</p>
                <span className="text-body-sm font-mono-table text-on-surface-variant">Completed in 1m 12s</span>
              </div>

              {/* Step 3 */}
              <div className="relative pl-6">
                <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-[#4ade80] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[10px] text-[#4ade80]">check</span>
                </div>
                <p className="text-body-md font-body-md font-semibold text-on-surface">Feature Engineering</p>
                <span className="text-body-sm font-mono-table text-on-surface-variant">Completed in 8m 45s</span>
              </div>

              {/* Step 4 (Active Running) */}
              <div className="relative pl-6">
                {status === 'IN PROGRESS' ? (
                  <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-primary flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></div>
                  </div>
                ) : (
                  <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-[#4ade80] flex items-center justify-center">
                    <span className="material-symbols-outlined text-[10px] text-[#4ade80]">check</span>
                  </div>
                )}
                <p className="text-body-md font-body-md font-semibold text-on-surface">XGBoost Training</p>
                <span className="text-body-sm font-mono-table text-primary">
                  {status === 'IN PROGRESS' ? `Running (Epoch ${currentEpoch}/100)...` : 'Completed in 14m 20s'}
                </span>
              </div>

              {/* Step 5 */}
              <div className="relative pl-6">
                <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border border-outline-variant flex items-center justify-center"></div>
                <p className="text-body-md font-body-md text-on-surface-variant">LightGBM Training</p>
                <span className="text-body-sm font-mono-table text-on-surface-variant/60">Pending</span>
              </div>

              {/* Step 6 */}
              <div className="relative pl-6">
                <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border border-outline-variant flex items-center justify-center"></div>
                <p className="text-body-md font-body-md text-on-surface-variant">Evaluation</p>
                <span className="text-body-sm font-mono-table text-on-surface-variant/60">Pending</span>
              </div>

              {/* Step 7 */}
              <div className="relative pl-6">
                <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-surface border border-outline-variant flex items-center justify-center"></div>
                <p className="text-body-md font-body-md text-on-surface-variant">Quality Gate</p>
                <span className="text-body-sm font-mono-table text-on-surface-variant/60">Pending</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Worker Terminal Logs (8 cols) */}
        <div className="lg:col-span-8 flex flex-col h-full min-h-[500px]">
          <div className="bg-[#0b0f12] border border-outline-variant/60 rounded-lg overflow-hidden shadow-2xl flex flex-col h-full max-h-[calc(100vh-190px)]">
            {/* Terminal Title Bar */}
            <div className="bg-surface-container-high px-4 py-2.5 border-b border-outline-variant flex justify-between items-center select-none">
              <div className="flex items-center gap-2 text-on-surface-variant font-mono-table text-xs">
                <span className="material-symbols-outlined text-[16px] text-primary">terminal</span>
                <span className="text-on-surface font-semibold">worker-node-x86-04</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block"></span>
              </div>
            </div>

            {/* Terminal Log Output Stream */}
            <div className="p-4 font-mono-table text-[12px] leading-relaxed space-y-1.5 overflow-y-auto flex-1 bg-[#090d12] text-slate-300">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 hover:bg-white/[0.02] px-1 rounded transition-colors">
                  <span className="text-slate-500 select-none font-mono">[{log.time}]</span>
                  {log.level === 'INFO' && (
                    <span className="text-cyan-400 font-bold tracking-wide w-16 select-none">INFO</span>
                  )}
                  {log.level === 'SUCCESS' && (
                    <span className="text-emerald-400 font-bold tracking-wide w-16 select-none">SUCCESS</span>
                  )}
                  {log.level === 'WARN' && (
                    <span className="text-amber-400 font-bold tracking-wide w-16 select-none">WARN</span>
                  )}
                  {log.level === 'EPOCH' && (
                    <span className="text-purple-300 font-semibold tracking-wide w-16 select-none">Epoch</span>
                  )}
                  <span className="text-slate-200 flex-1 break-all">{log.message}</span>
                </div>
              ))}
              <div ref={terminalEndRef} />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
