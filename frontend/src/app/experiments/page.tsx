'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FlaskConical,
  ExternalLink,
  Check,
  Search,
  Filter,
  BarChart2,
  Award,
  Layers,
  Sparkles,
  ArrowUpDown,
  Zap,
} from 'lucide-react';
import { StatusBadge, ModelBadge, MetricCard, DataTable } from '@/components/ui';
import { apiClient } from '@/services/api';

export interface MLflowRunItem {
  id: string;
  runName: string;
  model: string;
  dataset: string;
  parameters: {
    n_estimators: number;
    max_depth: number;
    learning_rate: number;
    subsample: number;
    colsample_bytree: number;
  };
  prAuc: number;
  recall: number;
  precision: number;
  f1: number;
  rocAuc: number;
  trainingTime: string; // in seconds or formatted string
  trainingTimeSeconds: number;
  createdAt: string;
  mlflowUrl: string;
}

const EXPERIMENT_RUNS_DATA: MLflowRunItem[] = [
  {
    id: 'run-7f8a9b01',
    runName: 'optuna-trial-v18-20',
    model: 'FraudDetector v18',
    dataset: 'ds_v1.4',
    parameters: {
      n_estimators: 350,
      max_depth: 8,
      learning_rate: 0.03,
      subsample: 0.85,
      colsample_bytree: 0.8,
    },
    prAuc: 0.965,
    recall: 0.951,
    precision: 0.942,
    f1: 0.938,
    rocAuc: 0.984,
    trainingTime: '04m 15s',
    trainingTimeSeconds: 255,
    createdAt: '15m ago',
    mlflowUrl: 'http://localhost:5000/#/experiments/1/runs/7f8a9b01',
  },
  {
    id: 'run-5c4d3e21',
    runName: 'optuna-trial-v18-19',
    model: 'FraudDetector v18',
    dataset: 'ds_v1.4',
    parameters: {
      n_estimators: 250,
      max_depth: 6,
      learning_rate: 0.05,
      subsample: 0.8,
      colsample_bytree: 0.75,
    },
    prAuc: 0.952,
    recall: 0.940,
    precision: 0.931,
    f1: 0.925,
    rocAuc: 0.976,
    trainingTime: '03m 40s',
    trainingTimeSeconds: 220,
    createdAt: '45m ago',
    mlflowUrl: 'http://localhost:5000/#/experiments/1/runs/5c4d3e21',
  },
  {
    id: 'run-1a2b3c4d',
    runName: 'xgboost-baseline-v17',
    model: 'FraudDetector v17',
    dataset: 'ds_v1.3',
    parameters: {
      n_estimators: 200,
      max_depth: 6,
      learning_rate: 0.1,
      subsample: 0.8,
      colsample_bytree: 0.8,
    },
    prAuc: 0.940,
    recall: 0.932,
    precision: 0.915,
    f1: 0.912,
    rocAuc: 0.968,
    trainingTime: '03m 10s',
    trainingTimeSeconds: 190,
    createdAt: '3d ago',
    mlflowUrl: 'http://localhost:5000/#/experiments/1/runs/1a2b3c4d',
  },
  {
    id: 'run-9e8d7c6b',
    runName: 'lightgbm-speed-bench',
    model: 'FraudDetector v17-fast',
    dataset: 'ds_v1.3',
    parameters: {
      n_estimators: 150,
      max_depth: 5,
      learning_rate: 0.12,
      subsample: 0.75,
      colsample_bytree: 0.7,
    },
    prAuc: 0.928,
    recall: 0.918,
    precision: 0.902,
    f1: 0.898,
    rocAuc: 0.955,
    trainingTime: '01m 55s',
    trainingTimeSeconds: 115,
    createdAt: '4d ago',
    mlflowUrl: 'http://localhost:5000/#/experiments/1/runs/9e8d7c6b',
  },
  {
    id: 'run-3f2e1d0c',
    runName: 'random-forest-ab-test',
    model: 'FraudDetector v16',
    dataset: 'ds_v1.2',
    parameters: {
      n_estimators: 100,
      max_depth: 10,
      learning_rate: 0.05,
      subsample: 0.9,
      colsample_bytree: 0.85,
    },
    prAuc: 0.918,
    recall: 0.904,
    precision: 0.890,
    f1: 0.895,
    rocAuc: 0.942,
    trainingTime: '05m 20s',
    trainingTimeSeconds: 320,
    createdAt: '7d ago',
    mlflowUrl: 'http://localhost:5000/#/experiments/1/runs/3f2e1d0c',
  },
];

export default function ExperimentsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>(['run-7f8a9b01', 'run-1a2b3c4d']);

  // TanStack Query for experiment runs from backend API
  const { data: experimentRuns = EXPERIMENT_RUNS_DATA } = useQuery({
    queryKey: ['experimentRuns'],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/experiments');
        if (Array.isArray(res.data) && res.data.length > 0) {
          return res.data;
        }
        return EXPERIMENT_RUNS_DATA;
      } catch (err) {
        return EXPERIMENT_RUNS_DATA;
      }
    },
  });

  const filteredRuns = experimentRuns.filter(
    (run) =>
      run.runName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      run.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      run.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleSelectRun = (id: string) => {
    setSelectedRunIds((prev) =>
      prev.includes(id) ? prev.filter((rId) => rId !== id) : [...prev, id]
    );
  };

  const selectedRuns = experimentRuns.filter((r) => selectedRunIds.includes(r.id));

  // Determine best metric values across selected runs to highlight in green!
  const bestPrAuc = Math.max(...selectedRuns.map((r) => r.prAuc), 0);
  const bestRecall = Math.max(...selectedRuns.map((r) => r.recall), 0);
  const bestPrecision = Math.max(...selectedRuns.map((r) => r.precision), 0);
  const bestF1 = Math.max(...selectedRuns.map((r) => r.f1), 0);
  const bestRocAuc = Math.max(...selectedRuns.map((r) => r.rocAuc), 0);
  const bestTimeSec = Math.min(...selectedRuns.map((r) => r.trainingTimeSeconds), Infinity);

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Top Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              MLflow Experiments & Hyperparameter Runs
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-purple-300 border border-[#252E3B] font-semibold flex items-center gap-1.5">
              <FlaskConical className="w-3.5 h-3.5 text-purple-400" />
              {experimentRuns.length} Runs Tracked
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Optuna trials, parameter lineage, metric comparisons, and MLflow run artifact references
          </p>
        </div>

        <a
          href="http://localhost:5000"
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-200 font-mono text-xs font-semibold rounded-lg flex items-center gap-2 transition-all"
        >
          <ExternalLink className="w-4 h-4 text-purple-400" />
          Open MLflow UI (Port 5000)
        </a>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-[240px] bg-[#101417] border border-[#252E3B] px-3.5 py-2 rounded-lg focus-within:border-purple-500 transition-colors">
          <Search className="w-4 h-4 text-[#94a3b8]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter experiment runs by name, model, or parameters..."
            className="bg-transparent border-none outline-none text-xs font-mono text-slate-200 placeholder-slate-500 w-full focus:ring-0"
          />
        </div>

        <div className="text-xs font-mono text-[#94a3b8]">
          <span className="text-purple-300 font-bold">{selectedRunIds.length}</span> runs selected for benchmark comparison
        </div>
      </div>

      {/* Multi-Run Benchmark Comparison UI (when 2+ runs selected) */}
      {selectedRuns.length >= 2 && (
        <div className="bg-[#101417] border border-purple-500/50 rounded-lg p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-400" />
              <h2 className="text-base font-bold font-mono text-white">Side-by-Side Experiment Comparison Matrix</h2>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-semibold bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/40">
              ● Best Metric Values Highlighted
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#252E3B] bg-[#101417] text-[#94a3b8]">
                  <th className="p-3">Run Attribute</th>
                  {selectedRuns.map((run) => (
                    <th key={run.id} className="p-3 font-bold text-white min-w-[180px]">
                      {run.runName}
                      <span className="block text-[10px] text-[#94a3b8] font-normal">{run.model}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#252E3B]">
                {/* PR-AUC */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">PR-AUC</td>
                  {selectedRuns.map((run) => {
                    const isBest = run.prAuc === bestPrAuc;
                    return (
                      <td key={run.id} className={`p-3 font-bold ${isBest ? 'text-[#4ade80] bg-emerald-950/30' : 'text-slate-200'}`}>
                        {run.prAuc.toFixed(3)} {isBest ? '🏆' : ''}
                      </td>
                    );
                  })}
                </tr>

                {/* Recall */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">Recall</td>
                  {selectedRuns.map((run) => {
                    const isBest = run.recall === bestRecall;
                    return (
                      <td key={run.id} className={`p-3 font-bold ${isBest ? 'text-[#4ade80] bg-emerald-950/30' : 'text-slate-200'}`}>
                        {(run.recall * 100).toFixed(1)}% {isBest ? '🏆' : ''}
                      </td>
                    );
                  })}
                </tr>

                {/* Precision */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">Precision</td>
                  {selectedRuns.map((run) => {
                    const isBest = run.precision === bestPrecision;
                    return (
                      <td key={run.id} className={`p-3 font-bold ${isBest ? 'text-[#4ade80] bg-emerald-950/30' : 'text-slate-200'}`}>
                        {run.precision.toFixed(3)} {isBest ? '🏆' : ''}
                      </td>
                    );
                  })}
                </tr>

                {/* F1-Score */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">F1-Score</td>
                  {selectedRuns.map((run) => {
                    const isBest = run.f1 === bestF1;
                    return (
                      <td key={run.id} className={`p-3 font-bold ${isBest ? 'text-[#4ade80] bg-emerald-950/30' : 'text-slate-200'}`}>
                        {run.f1.toFixed(3)} {isBest ? '🏆' : ''}
                      </td>
                    );
                  })}
                </tr>

                {/* ROC-AUC */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">ROC-AUC</td>
                  {selectedRuns.map((run) => {
                    const isBest = run.rocAuc === bestRocAuc;
                    return (
                      <td key={run.id} className={`p-3 font-bold ${isBest ? 'text-[#4ade80] bg-emerald-950/30' : 'text-slate-200'}`}>
                        {run.rocAuc.toFixed(3)} {isBest ? '🏆' : ''}
                      </td>
                    );
                  })}
                </tr>

                {/* Training Time */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">Training Time</td>
                  {selectedRuns.map((run) => {
                    const isBest = run.trainingTimeSeconds === bestTimeSec;
                    return (
                      <td key={run.id} className={`p-3 font-bold ${isBest ? 'text-[#4ade80] bg-emerald-950/30' : 'text-slate-200'}`}>
                        {run.trainingTime} {isBest ? '⚡' : ''}
                      </td>
                    );
                  })}
                </tr>

                {/* Hyperparameters */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">Parameters</td>
                  {selectedRuns.map((run) => (
                    <td key={run.id} className="p-3 text-[11px] text-purple-300">
                      n_est: {run.parameters.n_estimators}, depth: {run.parameters.max_depth}, lr: {run.parameters.learning_rate}
                    </td>
                  ))}
                </tr>

                {/* MLflow Link */}
                <tr className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-300">MLflow Reference</td>
                  {selectedRuns.map((run) => (
                    <td key={run.id} className="p-3">
                      <a
                        href={run.mlflowUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-purple-400 hover:text-purple-300 font-semibold"
                      >
                        MLflow Run <ExternalLink className="w-3 h-3" />
                      </a>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Main Experiment Runs Data Table */}
      <DataTable
        columns={[
          {
            key: 'select',
            header: 'Compare',
            render: (run: MLflowRunItem) => (
              <input
                type="checkbox"
                checked={selectedRunIds.includes(run.id)}
                onChange={() => toggleSelectRun(run.id)}
                className="rounded border-[#252E3B] bg-[#101417] text-purple-600 focus:ring-purple-500 w-4 h-4 cursor-pointer"
              />
            ),
          },
          {
            key: 'runName',
            header: 'Run Name / ID',
            render: (run: MLflowRunItem) => (
              <div>
                <span className="font-mono font-bold text-white block">{run.runName}</span>
                <span className="text-[11px] font-mono text-[#94a3b8]">{run.id}</span>
              </div>
            ),
          },
          {
            key: 'model',
            header: 'Target Model',
            render: (run: MLflowRunItem) => <ModelBadge modelName={run.model.split(' ')[0]} version={run.model.split(' ')[1] || 'v1.0'} />,
          },
          {
            key: 'dataset',
            header: 'Dataset Snapshot',
            render: (run: MLflowRunItem) => <span className="font-mono text-xs text-slate-300">{run.dataset}</span>,
          },
          {
            key: 'parameters',
            header: 'Hyperparameters',
            render: (run: MLflowRunItem) => (
              <span className="font-mono text-[11px] text-purple-300 bg-[#101417] border border-[#252E3B] px-2 py-1 rounded block truncate max-w-xs">
                n_est={run.parameters.n_estimators}, depth={run.parameters.max_depth}, lr={run.parameters.learning_rate}
              </span>
            ),
          },
          {
            key: 'prAuc',
            header: 'PR-AUC',
            render: (run: MLflowRunItem) => <span className="font-mono font-bold text-emerald-400">{run.prAuc.toFixed(3)}</span>,
          },
          {
            key: 'recall',
            header: 'Recall',
            render: (run: MLflowRunItem) => <span className="font-mono text-white font-semibold">{(run.recall * 100).toFixed(1)}%</span>,
          },
          {
            key: 'f1',
            header: 'F1',
            render: (run: MLflowRunItem) => <span className="font-mono text-slate-200">{run.f1.toFixed(3)}</span>,
          },
          {
            key: 'rocAuc',
            header: 'ROC-AUC',
            render: (run: MLflowRunItem) => <span className="font-mono text-slate-200">{run.rocAuc.toFixed(3)}</span>,
          },
          {
            key: 'trainingTime',
            header: 'Training Time',
            render: (run: MLflowRunItem) => <span className="font-mono text-xs text-[#94a3b8]">{run.trainingTime}</span>,
          },
          {
            key: 'createdAt',
            header: 'Created',
            render: (run: MLflowRunItem) => <span className="font-mono text-xs text-[#94a3b8]">{run.createdAt}</span>,
          },
          {
            key: 'actions',
            header: 'MLflow Link',
            render: (run: MLflowRunItem) => (
              <a
                href={run.mlflowUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-mono text-purple-400 hover:text-purple-300 font-semibold"
              >
                MLflow <ExternalLink className="w-3.5 h-3.5" />
              </a>
            ),
          },
        ]}
        data={filteredRuns}
        keyExtractor={(run: MLflowRunItem) => run.id}
      />
    </main>
  );
}
