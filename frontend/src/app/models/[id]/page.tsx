'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useSentinelStore } from '@/store/useSentinelStore';
import {
  Cpu,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Rocket,
  Sliders,
  Database,
  FileCode,
  LineChart as LineChartIcon,
  TrendingUp,
  Layers,
} from 'lucide-react';
import { StatusBadge, ModelBadge, MetricCard, ChartCard, Timeline, DataTable } from '@/components/ui';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const METRIC_HISTORY = [
  { epoch: 'Epoch 1', prAuc: 0.88, recall: 0.86, f1: 0.84 },
  { epoch: 'Epoch 2', prAuc: 0.91, recall: 0.89, f1: 0.88 },
  { epoch: 'Epoch 3', prAuc: 0.93, recall: 0.92, f1: 0.90 },
  { epoch: 'Epoch 4', prAuc: 0.95, recall: 0.94, f1: 0.92 },
  { epoch: 'Epoch 5', prAuc: 0.965, recall: 0.951, f1: 0.938 },
];

const FEATURE_IMPORTANCES = [
  { feature: 'transaction_amount', importance: 0.384 },
  { feature: 'ip_risk_score', importance: 0.221 },
  { feature: 'device_type', importance: 0.185 },
  { feature: 'merchant_category', importance: 0.120 },
  { feature: 'billing_zip_mismatch', importance: 0.090 },
];

export default function ModelDetailPage() {
  const params = useParams();
  const modelId = (params?.id as string) || 'm-18';
  const store = useSentinelStore();

  const model = store.models.find((m) => m.id === modelId) || store.models[1] || store.models[0];
  const prodModel = store.models.find((m) => m.status === 'PRODUCTION') || store.models[0];

  const [compareTargetId, setCompareTargetId] = useState<string>(prodModel.id);
  const compareModel = store.models.find((m) => m.id === compareTargetId) || prodModel;

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-slate-950 text-slate-100 w-full h-full space-y-6">
      {/* Navigation & Header */}
      <div className="space-y-3">
        <Link
          href="/models"
          className="inline-flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Model Registry
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400 border border-purple-500/20">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold font-mono tracking-tight text-white">{model.name}</h1>
                <ModelBadge modelName="" version={model.version} isActive={model.status === 'PRODUCTION'} />
                <StatusBadge status={model.status} />
              </div>
              <p className="text-xs font-mono text-slate-400 mt-1">
                Model ID: <span className="text-slate-300 font-semibold">{model.id}</span> • Algorithm:{' '}
                <span className="text-purple-300">{model.algorithm}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {model.status === 'CANDIDATE' && (
              <button
                onClick={() => store.promoteModel(model.id)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold font-mono text-xs rounded-xl shadow-md flex items-center gap-2 transition-all"
              >
                <Rocket className="w-4 h-4" />
                PROMOTE TO PRODUCTION
              </button>
            )}
            {model.status === 'PRODUCTION' && (
              <button
                onClick={() => store.rollbackModel(model.id)}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold font-mono text-xs rounded-xl shadow-md flex items-center gap-2 transition-all"
              >
                <RotateCcw className="w-4 h-4" />
                EXECUTE ROLLBACK
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard title="PR-AUC Score" value={model.prAuc} change={1.8} highlight status="good" />
        <MetricCard title="Recall" value={model.recall ? `${model.recall}%` : '95.1%'} change={1.4} status="good" />
        <MetricCard title="F1-Score" value={model.f1Score || '0.938'} change={0.9} status="good" />
        <MetricCard title="Training Duration" value="45.2s" subValue="Optuna 20 trials" status="neutral" />
      </div>

      {/* Grid Section 1: Model Metadata & Feature Importances */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Metadata Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold font-mono text-white flex items-center gap-2">
              <FileCode className="w-4 h-4 text-purple-400" />
              Model Metadata & Lineage
            </h3>
            <span className="text-[11px] font-mono text-slate-400">Version {model.version}</span>
          </div>

          <div className="grid grid-cols-2 gap-4 font-mono text-xs">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Framework</span>
              <span className="text-slate-200 font-semibold">{model.algorithm} 2.4.1</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Dataset Snapshot</span>
              <span className="text-purple-300 font-semibold">ds_snapshot_20260815</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Artifact Path</span>
              <span className="text-slate-300 truncate block text-[11px]">s3://sentinelml-artifacts/{model.name}_{model.version}.pkl</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Schema Hash</span>
              <span className="text-slate-300 font-semibold">fee47667a901</span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800">
            <span className="text-xs font-mono text-slate-400 block mb-2 font-semibold">Optuna Hyperparameters</span>
            <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-purple-300 overflow-x-auto">
{JSON.stringify(
  {
    n_estimators: 150,
    max_depth: 6,
    learning_rate: 0.035,
    subsample: 0.85,
    colsample_bytree: 0.8,
    scale_pos_weight: 29.62,
  },
  null,
  2
)}
            </pre>
          </div>
        </div>

        {/* Feature Importance Chart */}
        <ChartCard title="Feature Importance Breakdown" subtitle="Gini impurity attribution score per input feature">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart layout="vertical" data={FEATURE_IMPORTANCES}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <YAxis dataKey="feature" type="category" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} width={130} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="importance" name="Gini Weight" fill="#a855f7" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Grid Section 2: Metric History & Deployment History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Training & Validation Metric History" subtitle="Epoch performance trajectory during retraining flow">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={METRIC_HISTORY}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <YAxis domain={[0.8, 1.0]} stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Line type="monotone" dataKey="prAuc" name="PR-AUC" stroke="#a855f7" strokeWidth={2.5} />
              <Line type="monotone" dataKey="recall" name="Recall" stroke="#38bdf8" strokeWidth={2} />
              <Line type="monotone" dataKey="f1" name="F1-Score" stroke="#34d399" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Deployment History Timeline */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold font-mono text-white flex items-center gap-2">
              <Rocket className="w-4 h-4 text-purple-400" />
              Deployment & Release History
            </h3>
            <span className="text-xs font-mono text-slate-400">Release Pipeline</span>
          </div>

          <Timeline
            events={[
              {
                id: '1',
                title: `Model ${model.version} evaluated in Canary split (10%)`,
                timestamp: '1 hour ago',
                status: 'completed',
                tag: 'CANARY 10%',
              },
              {
                id: '2',
                title: `Quality Gate passed (PR-AUC 0.965 > Prod 0.940)`,
                timestamp: '45 mins ago',
                status: 'completed',
                tag: 'GATE PASSED',
              },
              {
                id: '3',
                title: model.status === 'PRODUCTION' ? 'Promoted to PRODUCTION (100% Traffic)' : 'Registered as CANDIDATE',
                timestamp: '12 mins ago',
                status: 'completed',
                tag: model.status,
              },
            ]}
          />
        </div>
      </div>

      {/* Production vs Candidate Comparison Tool */}
      <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-purple-400" />
              Production vs Candidate Model Benchmark Comparison
            </h2>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Side-by-side metric breakdown between active production model and candidate versions
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400">Compare Against:</span>
            <select
              value={compareTargetId}
              onChange={(e) => setCompareTargetId(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 font-mono text-xs text-purple-300 focus:outline-none focus:border-purple-500"
            >
              {store.models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.version} ({m.algorithm}) - {m.status}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Active Model Card */}
          <div className="bg-slate-950 border border-purple-500/40 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold font-mono text-white">{model.name}</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/40">
                  {model.version} (Selected)
                </span>
              </div>
              <StatusBadge status={model.status} size="sm" />
            </div>

            <div className="grid grid-cols-3 gap-2 font-mono text-xs text-center">
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">PR-AUC</span>
                <span className="text-purple-400 font-bold text-base">{model.prAuc}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">Recall</span>
                <span className="text-sky-400 font-bold text-base">{model.recall ? `${model.recall}%` : '95.1%'}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">F1-Score</span>
                <span className="text-emerald-400 font-bold text-base">{model.f1Score || '0.938'}</span>
              </div>
            </div>
          </div>

          {/* Compare Model Card */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold font-mono text-white">{compareModel.name}</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {compareModel.version} (Baseline)
                </span>
              </div>
              <StatusBadge status={compareModel.status} size="sm" />
            </div>

            <div className="grid grid-cols-3 gap-2 font-mono text-xs text-center">
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">PR-AUC</span>
                <span className="text-slate-200 font-bold text-base">{compareModel.prAuc}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">Recall</span>
                <span className="text-slate-200 font-bold text-base">{compareModel.recall ? `${compareModel.recall}%` : '93.2%'}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">F1-Score</span>
                <span className="text-slate-200 font-bold text-base">{compareModel.f1Score || '0.910'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
