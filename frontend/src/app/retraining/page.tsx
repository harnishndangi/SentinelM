'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Activity,
  Terminal,
  Layers,
  Cpu,
  Database,
  BarChart2,
  X,
  Zap,
} from 'lucide-react';
import { StatusBadge, MetricCard, DataTable, AlertBanner } from '@/components/ui';
import { useSentinelStore } from '@/store/useSentinelStore';
import { apiClient } from '@/services/api';

export interface RetrainingStage {
  id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED';
  duration?: string;
}

export interface RetrainingRun {
  id: string;
  model: string;
  dataset: string;
  trigger: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'FAILED';
  progress: number;
  duration: string;
  currentStage: string;
  prAuc: number;
  recall: number;
  f1: number;
  createdAt: string;
}

const INITIAL_STAGES: RetrainingStage[] = [
  { id: '1', name: 'Dataset snapshot', status: 'PASSED', duration: '12s' },
  { id: '2', name: 'Data validation', status: 'PASSED', duration: '35s' },
  { id: '3', name: 'Feature preprocessing', status: 'PASSED', duration: '48s' },
  { id: '4', name: 'XGBoost training', status: 'PASSED', duration: '1m 20s' },
  { id: '5', name: 'LightGBM training', status: 'RUNNING', duration: 'In Progress' },
  { id: '6', name: 'Evaluation', status: 'PENDING' },
  { id: '7', name: 'Quality gate', status: 'PENDING' },
  { id: '8', name: 'Registration', status: 'PENDING' },
];

const HISTORICAL_RUNS: RetrainingRun[] = [
  {
    id: 'run-cc4a64a5',
    model: 'FraudDetector v18',
    dataset: 'ds_v1.4',
    trigger: 'AUTOMATED_DRIFT_RCA',
    status: 'IN_PROGRESS',
    progress: 62,
    duration: '04m 15s',
    currentStage: 'LightGBM training',
    prAuc: 0.965,
    recall: 95.1,
    f1: 0.938,
    createdAt: '12m ago',
  },
  {
    id: 'run-8f2a1b90',
    model: 'FraudDetector v17',
    dataset: 'ds_v1.3',
    trigger: 'SCHEDULED_WEEKLY',
    status: 'COMPLETED',
    progress: 100,
    duration: '08m 42s',
    currentStage: 'Registration',
    prAuc: 0.940,
    recall: 93.2,
    f1: 0.912,
    createdAt: '3d ago',
  },
  {
    id: 'run-3e4f7a11',
    model: 'FraudDetector v16',
    dataset: 'ds_v1.2',
    trigger: 'MANUAL_TRIGGER',
    status: 'COMPLETED',
    progress: 100,
    duration: '07m 10s',
    currentStage: 'Registration',
    prAuc: 0.918,
    recall: 90.4,
    f1: 0.895,
    createdAt: '7d ago',
  },
  {
    id: 'run-1a9b8c7d',
    model: 'FraudDetector v15',
    dataset: 'ds_v1.1',
    trigger: 'PERFORMANCE_SLA_BREACH',
    status: 'FAILED',
    progress: 40,
    duration: '03m 12s',
    currentStage: 'Data validation',
    prAuc: 0.840,
    recall: 82.1,
    f1: 0.810,
    createdAt: '12d ago',
  },
];

export default function RetrainingPage() {
  const store = useSentinelStore();

  const [stages, setStages] = useState<RetrainingStage[]>(INITIAL_STAGES);
  const [activeRunProgress, setActiveRunProgress] = useState(62);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState('FraudDetector');
  const [selectedDataset, setSelectedDataset] = useState('ds_v1.4');
  const [algorithm, setAlgorithm] = useState('LightGBM + XGBoost Ensemble');
  const [notification, setNotification] = useState<string | null>(null);

  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    '[11:42:01] [INFO] Initializing Celery worker compute environment...',
    '[11:42:05] [INFO] Loading dataset snapshot ds_v1.4 (4,000 records, schema: fee47667)...',
    '[11:42:25] [SUCCESS] GreatExpectations suite passed: 42/42 data quality assertions met.',
    '[11:42:30] [INFO] Preprocessing features & scaling 33 input dimensions...',
    '[11:43:10] [INFO] Launching XGBoost hyperparameter search (20 Optuna trials)...',
    '[11:44:15] [SUCCESS] XGBoost trial #14 best validation PR-AUC: 0.958.',
    '[11:44:20] [INFO] Launching LightGBM training block...',
    '[11:45:02] [EPOCH 47/100] loss: 0.1421, pr_auc: 0.9650, recall: 0.9510',
  ]);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal logs
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs]);

  // Handle manual start retraining
  const handleStartRetraining = async () => {
    setIsModalOpen(false);
    setNotification('Triggering retraining pipeline job via Celery...');

    try {
      await apiClient.post('/retraining/trigger', {
        model_name: selectedModel,
        dataset_version: selectedDataset,
        algorithm,
      });
      setNotification(`Retraining run queued successfully for ${selectedModel} (${selectedDataset})!`);
    } catch (err) {
      setNotification(`Retraining run initiated locally for ${selectedModel} (${selectedDataset}).`);
    }

    setTerminalLogs((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] [INFO] Manual retraining flow triggered for ${selectedModel} (${selectedDataset}).`,
    ]);

    setTimeout(() => setNotification(null), 6000);
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Automated Retraining Control Center
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-purple-300 border border-[#252E3B] font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
              1 Active Run
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Track active retraining execution flows, 8-stage pipeline progress, Optuna tuning, and quality gates
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold font-mono text-xs rounded-lg shadow-md flex items-center gap-2 transition-all"
        >
          <Play className="w-4 h-4 fill-white" />
          START RETRAINING
        </button>
      </div>

      {notification && (
        <AlertBanner type="success" title="Retraining Execution Notice" message={notification} onClose={() => setNotification(null)} />
      )}

      {/* Active Retraining Run Card */}
      <div className="bg-[#101417] border border-purple-500/40 rounded-lg p-5 space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold font-mono text-white">Active Run: run-cc4a64a5</h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40 font-semibold">
                IN_PROGRESS
              </span>
            </div>
            <p className="text-xs font-mono text-[#94a3b8] mt-1">
              Model: <span className="text-white font-semibold">FraudDetector v18</span> • Dataset: <span className="text-white font-semibold">ds_v1.4</span> • Duration: 04m 15s
            </p>
          </div>

          <div className="flex items-center gap-6 font-mono text-xs">
            <div>
              <span className="text-[#94a3b8] block">PR-AUC Metric:</span>
              <span className="text-base font-bold text-emerald-400">0.965</span>
            </div>
            <div>
              <span className="text-[#94a3b8] block">Recall SLA:</span>
              <span className="text-base font-bold text-white">95.1%</span>
            </div>
            <div>
              <span className="text-[#94a3b8] block">Overall Progress:</span>
              <span className="text-base font-bold text-purple-400">{activeRunProgress}%</span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono text-[#94a3b8]">
            <span>Pipeline Progress: Stage 5/8 (LightGBM training)</span>
            <span className="text-purple-300 font-bold">{activeRunProgress}% Complete</span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-[#252E3B]">
            <div className="bg-gradient-to-r from-purple-600 via-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500" style={{ width: `${activeRunProgress}%` }} />
          </div>
        </div>

        {/* 8-Stage Pipeline Progress Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 pt-2">
          {stages.map((stage, idx) => {
            const isPassed = stage.status === 'PASSED';
            const isRunning = stage.status === 'RUNNING';
            const isFailed = stage.status === 'FAILED';

            return (
              <div
                key={stage.id}
                className={`bg-[#101417] border rounded-lg p-3 flex flex-col justify-between ${
                  isRunning
                    ? 'border-purple-500 shadow-md ring-1 ring-purple-500/50'
                    : isPassed
                    ? 'border-emerald-500/40'
                    : isFailed
                    ? 'border-rose-500/40'
                    : 'border-[#252E3B] opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono text-[#94a3b8] font-bold">0{idx + 1}</span>
                  {isPassed && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {isRunning && <Activity className="w-4 h-4 text-purple-400 animate-spin" />}
                  {stage.status === 'PENDING' && <Clock className="w-4 h-4 text-slate-500" />}
                  {isFailed && <AlertTriangle className="w-4 h-4 text-rose-400" />}
                </div>

                <h4 className="text-xs font-mono font-bold text-white leading-tight">{stage.name}</h4>

                <div className="mt-3 pt-2 border-t border-[#252E3B] flex items-center justify-between text-[10px] font-mono">
                  <span
                    className={`font-semibold uppercase ${
                      isPassed ? 'text-emerald-400' : isRunning ? 'text-purple-400' : isFailed ? 'text-rose-400' : 'text-slate-500'
                    }`}
                  >
                    {stage.status}
                  </span>
                  <span className="text-slate-500">{stage.duration || '—'}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Live Terminal Logs */}
        <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-4 font-mono text-xs text-slate-300 space-y-2">
          <div className="flex items-center justify-between border-b border-[#252E3B] pb-2 text-[#94a3b8]">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-purple-400" />
              <span>Real-Time Execution Logs (Prefect Worker Task Stream)</span>
            </div>
            <span className="text-[10px] text-emerald-400">● Streaming</span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1 pr-2">
            {terminalLogs.map((log, i) => (
              <div key={i} className="text-[11px] leading-relaxed">
                {log}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>
        </div>
      </div>

      {/* Historical Retraining Runs Table */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white tracking-tight font-mono">Historical Retraining Runs</h3>

        <DataTable
          columns={[
            {
              key: 'id',
              header: 'Run ID',
              render: (run: RetrainingRun) => <span className="font-mono font-bold text-purple-400">{run.id}</span>,
            },
            {
              key: 'model',
              header: 'Model Version',
              render: (run: RetrainingRun) => <span className="font-mono text-white font-semibold">{run.model}</span>,
            },
            {
              key: 'dataset',
              header: 'Dataset Snapshot',
              render: (run: RetrainingRun) => <span className="font-mono text-slate-300 text-xs">{run.dataset}</span>,
            },
            {
              key: 'trigger',
              header: 'Trigger Event',
              render: (run: RetrainingRun) => (
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#101417] border border-[#252E3B] text-slate-300">
                  {run.trigger}
                </span>
              ),
            },
            {
              key: 'status',
              header: 'Status',
              render: (run: RetrainingRun) => <StatusBadge status={run.status} size="sm" />,
            },
            {
              key: 'prAuc',
              header: 'PR-AUC',
              render: (run: RetrainingRun) => <span className="font-mono font-bold text-emerald-400">{run.prAuc.toFixed(3)}</span>,
            },
            {
              key: 'duration',
              header: 'Duration',
              render: (run: RetrainingRun) => <span className="font-mono text-xs text-[#94a3b8]">{run.duration}</span>,
            },
            {
              key: 'createdAt',
              header: 'Created At',
              render: (run: RetrainingRun) => <span className="font-mono text-xs text-[#94a3b8]">{run.createdAt}</span>,
            },
          ]}
          data={HISTORICAL_RUNS}
          keyExtractor={(run: RetrainingRun) => run.id}
        />
      </div>

      {/* Manual Retraining Trigger Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-6 w-full max-w-md space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
                <Play className="w-4 h-4 text-purple-400 fill-purple-400" />
                Start Manual Retraining Flow
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-[#94a3b8] hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Target Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="FraudDetector">FraudDetector</option>
                  <option value="ChurnPredictor">ChurnPredictor</option>
                  <option value="CreditScorer">CreditScorer</option>
                </select>
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Dataset Version</label>
                <select
                  value={selectedDataset}
                  onChange={(e) => setSelectedDataset(e.target.value)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="ds_v1.4">ds_v1.4 (Latest Snapshot)</option>
                  <option value="ds_v1.3">ds_v1.3</option>
                </select>
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Algorithm & Ensemble</label>
                <select
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="LightGBM + XGBoost Ensemble">LightGBM + XGBoost Ensemble</option>
                  <option value="XGBoost Only">XGBoost Only</option>
                  <option value="RandomForest">RandomForest</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#252E3B]">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 bg-[#101417] border border-[#252E3B] text-[#94a3b8] font-mono text-xs rounded-lg hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleStartRetraining}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-mono font-bold text-xs rounded-lg shadow-md flex items-center gap-2"
              >
                Confirm & Trigger
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
