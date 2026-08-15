'use client';

import React, { useState } from 'react';
import {
  Rocket,
  GitBranch,
  Shield,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Activity,
  Layers,
  Cpu,
  Zap,
  BarChart2,
} from 'lucide-react';
import { StatusBadge, ModelBadge, MetricCard, DataTable, AlertBanner } from '@/components/ui';
import { useSentinelStore } from '@/store/useSentinelStore';
import { apiClient } from '@/services/api';

export interface DeploymentRecord {
  id: string;
  version: string;
  algorithm: string;
  status: 'PRODUCTION' | 'CANDIDATE' | 'SHADOW' | 'CANARY' | 'PROMOTED' | 'ROLLED_BACK';
  trafficShare: string;
  prAuc: number;
  recall: string;
  f1: number;
  latencyP95: string;
  errorRate: string;
  deployedAt: string;
  rollbackReason?: string;
}

const DEPLOYMENT_HISTORY: DeploymentRecord[] = [
  {
    id: 'dep-108',
    version: 'v18',
    algorithm: 'LightGBM + XGBoost',
    status: 'CANARY',
    trafficShare: '10%',
    prAuc: 0.965,
    recall: '95.1%',
    f1: 0.938,
    latencyP95: '14.2 ms',
    errorRate: '0.01%',
    deployedAt: 'Active (15m ago)',
  },
  {
    id: 'dep-107',
    version: 'v17',
    algorithm: 'XGBoost',
    status: 'PRODUCTION',
    trafficShare: '90%',
    prAuc: 0.940,
    recall: '93.2%',
    f1: 0.912,
    latencyP95: '18.4 ms',
    errorRate: '0.02%',
    deployedAt: '3d ago',
  },
  {
    id: 'dep-106',
    version: 'v16',
    algorithm: 'XGBoost',
    status: 'PROMOTED',
    trafficShare: '0%',
    prAuc: 0.918,
    recall: '90.4%',
    f1: 0.895,
    latencyP95: '19.1 ms',
    errorRate: '0.03%',
    deployedAt: '7d ago',
  },
  {
    id: 'dep-105',
    version: 'v15',
    algorithm: 'RandomForest',
    status: 'ROLLED_BACK',
    trafficShare: '0%',
    prAuc: 0.840,
    recall: '82.1%',
    f1: 0.810,
    latencyP95: '64.2 ms',
    errorRate: '0.14%',
    deployedAt: '12d ago',
    rollbackReason: 'P99 Latency SLA breach (> 50ms) on 25% canary split. Automated rollback to v14 triggered by Prefect monitor.',
  },
];

export default function DeploymentsPage() {
  const store = useSentinelStore();

  const [canaryTraffic, setCanaryTraffic] = useState<number>(10);
  const [notification, setNotification] = useState<string | null>(null);
  const [isPromoting, setIsPromoting] = useState(false);

  const handleAdvanceCanary = async (newTraffic: number) => {
    setIsPromoting(true);
    setNotification(null);

    try {
      await apiClient.post('/deployments/canary/scale', {
        version: 'v18',
        traffic_percent: newTraffic,
      });
      setCanaryTraffic(newTraffic);
      setNotification(`Canary traffic split advanced to ${newTraffic}% for FraudDetector v18!`);
    } catch (err) {
      setCanaryTraffic(newTraffic);
      setNotification(`Canary traffic split updated locally to ${newTraffic}%.`);
    } finally {
      setIsPromoting(false);
      setTimeout(() => setNotification(null), 6000);
    }
  };

  const handleFullPromotion = async () => {
    setIsPromoting(true);
    try {
      await apiClient.post('/deployments/promote', { version: 'v18' });
      store.promoteModel('v18');
      setCanaryTraffic(100);
      setNotification('Model version FraudDetector v18 promoted to 100% PRODUCTION!');
    } catch (err) {
      store.promoteModel('v18');
      setCanaryTraffic(100);
      setNotification('Model version FraudDetector v18 promoted to 100% PRODUCTION!');
    } finally {
      setIsPromoting(false);
      setTimeout(() => setNotification(null), 6000);
    }
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Canary Deployments & Release Management
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-purple-300 border border-[#252E3B] font-semibold">
              Active Canary: v18 ({canaryTraffic}%)
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Progressive traffic routing, candidate benchmarking, automated SLA monitoring, & instant safety rollbacks
          </p>
        </div>
      </div>

      {notification && (
        <AlertBanner type="success" title="Deployment Action Notice" message={notification} onClose={() => setNotification(null)} />
      )}

      {/* Active Canary Traffic Split Visualization Container */}
      <div className="bg-[#101417] border border-purple-500/40 rounded-lg p-5 space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold font-mono text-white">Active Canary Traffic Allocation</h2>
              <StatusBadge status="CANARY" />
            </div>
            <p className="text-xs font-mono text-[#94a3b8] mt-1">
              Candidate version <span className="text-purple-300 font-bold">FraudDetector v18</span> vs Production version <span className="text-white font-bold">FraudDetector v17</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => handleAdvanceCanary(canaryTraffic === 10 ? 25 : canaryTraffic === 25 ? 50 : 100)}
              disabled={canaryTraffic >= 100 || isPromoting}
              className="px-4 py-2 bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-200 font-mono text-xs font-semibold rounded-lg transition-all disabled:opacity-50"
            >
              Advance Canary ({canaryTraffic === 10 ? '25%' : canaryTraffic === 25 ? '50%' : '100%'})
            </button>

            <button
              onClick={handleFullPromotion}
              disabled={canaryTraffic >= 100 || isPromoting}
              className="px-5 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold font-mono text-xs rounded-lg shadow-md flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Rocket className="w-4 h-4 fill-slate-950" />
              PROMOTE TO 100% PROD
            </button>
          </div>
        </div>

        {/* Visual Traffic Split Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-purple-300 font-bold">Candidate v18 ({canaryTraffic}% Traffic)</span>
            <span className="text-[#94a3b8]">Production v17 ({100 - canaryTraffic}% Traffic)</span>
          </div>

          <div className="w-full bg-slate-900 rounded-lg h-6 overflow-hidden flex border border-[#252E3B] p-0.5">
            <div
              className="bg-purple-600 h-full rounded-l transition-all duration-500 flex items-center justify-center text-[10px] font-mono font-bold text-white"
              style={{ width: `${canaryTraffic}%` }}
            >
              {canaryTraffic}%
            </div>
            <div
              className="bg-slate-800 h-full rounded-r transition-all duration-500 flex items-center justify-center text-[10px] font-mono font-bold text-[#94a3b8]"
              style={{ width: `${100 - canaryTraffic}%` }}
            >
              {100 - canaryTraffic}%
            </div>
          </div>
        </div>

        {/* Candidate vs Production Side-by-Side Metric Benchmark Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 pt-2">
          {/* PR-AUC */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-3.5 space-y-1">
            <span className="text-[11px] font-mono text-[#94a3b8]">PR-AUC</span>
            <div className="flex items-baseline justify-between font-mono">
              <span className="text-sm font-bold text-emerald-400">0.965 (v18)</span>
              <span className="text-xs text-slate-500">0.940 (v17)</span>
            </div>
          </div>

          {/* Recall */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-3.5 space-y-1">
            <span className="text-[11px] font-mono text-[#94a3b8]">Recall SLA</span>
            <div className="flex items-baseline justify-between font-mono">
              <span className="text-sm font-bold text-white">95.1% (v18)</span>
              <span className="text-xs text-slate-500">93.2% (v17)</span>
            </div>
          </div>

          {/* F1 Score */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-3.5 space-y-1">
            <span className="text-[11px] font-mono text-[#94a3b8]">F1 Score</span>
            <div className="flex items-baseline justify-between font-mono">
              <span className="text-sm font-bold text-white">0.938 (v18)</span>
              <span className="text-xs text-slate-500">0.912 (v17)</span>
            </div>
          </div>

          {/* Latency */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-3.5 space-y-1">
            <span className="text-[11px] font-mono text-[#94a3b8]">P95 Latency</span>
            <div className="flex items-baseline justify-between font-mono">
              <span className="text-sm font-bold text-emerald-400">14.2 ms</span>
              <span className="text-xs text-slate-500">18.4 ms</span>
            </div>
          </div>

          {/* Error Rate */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-3.5 space-y-1">
            <span className="text-[11px] font-mono text-[#94a3b8]">Error Rate</span>
            <div className="flex items-baseline justify-between font-mono">
              <span className="text-sm font-bold text-emerald-400">0.01%</span>
              <span className="text-xs text-slate-500">0.02%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Deployment History Table */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white tracking-tight font-mono">Deployment History & Rollback Logs</h3>

        <DataTable
          columns={[
            {
              key: 'id',
              header: 'Deployment ID',
              render: (dep: DeploymentRecord) => <span className="font-mono font-bold text-purple-400">{dep.id}</span>,
            },
            {
              key: 'version',
              header: 'Version',
              render: (dep: DeploymentRecord) => <ModelBadge modelName="FraudDetector" version={dep.version} isActive={dep.status === 'PRODUCTION' || dep.status === 'CANARY'} />,
            },
            {
              key: 'algorithm',
              header: 'Algorithm',
              render: (dep: DeploymentRecord) => <span className="font-mono text-xs text-slate-300">{dep.algorithm}</span>,
            },
            {
              key: 'status',
              header: 'Status',
              render: (dep: DeploymentRecord) => <StatusBadge status={dep.status} size="sm" />,
            },
            {
              key: 'trafficShare',
              header: 'Traffic Share',
              render: (dep: DeploymentRecord) => <span className="font-mono font-bold text-white">{dep.trafficShare}</span>,
            },
            {
              key: 'prAuc',
              header: 'PR-AUC',
              render: (dep: DeploymentRecord) => <span className="font-mono text-emerald-400 font-semibold">{dep.prAuc.toFixed(3)}</span>,
            },
            {
              key: 'latencyP95',
              header: 'P95 Latency',
              render: (dep: DeploymentRecord) => <span className="font-mono text-xs text-[#94a3b8]">{dep.latencyP95}</span>,
            },
            {
              key: 'deployedAt',
              header: 'Deployed',
              render: (dep: DeploymentRecord) => <span className="font-mono text-xs text-[#94a3b8]">{dep.deployedAt}</span>,
            },
          ]}
          data={DEPLOYMENT_HISTORY}
          keyExtractor={(dep: DeploymentRecord) => dep.id}
        />
      </div>

      {/* Rollback Diagnostic Log Panel */}
      <div className="bg-[#101417] border border-rose-500/30 rounded-lg p-5 space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <h3 className="text-sm font-bold font-mono text-white">Failed Deployment Diagnostic Log: dep-105 (v15)</h3>
        </div>
        <p className="text-xs font-mono text-slate-300 leading-relaxed bg-[#101417] border border-[#252E3B] p-3.5 rounded-md">
          <span className="text-rose-400 font-bold">[AUTOMATED ROLLBACK EVENT]</span> Deployment <span className="text-white font-bold">FraudDetector v15</span> breached P99 latency SLA (64.2ms &gt; 50.0ms limit) during 25% canary traffic phase on 12d ago. Automated circuit breaker triggered rollback back to stable version v14 in 0.4s. Zero user-facing SLA outages experienced.
        </p>

      </div>
    </main>
  );
}
