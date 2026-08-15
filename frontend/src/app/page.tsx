'use client';

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  Zap,
  Shield,
  Cpu,
  AlertTriangle,
  Clock,
  TrendingUp,
  BarChart3,
  GitCommit,
  RotateCcw,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

import {
  MetricCard,
  StatusBadge,
  SeverityBadge,
  ModelBadge,
  ChartCard,
  DataTable,
  Timeline,
  AlertBanner,
} from '@/components/ui';
import { InjectDriftModal } from '@/components/dashboard/InjectDriftModal';
import { useSentinelStore } from '@/store/useSentinelStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiClient } from '@/services/api';

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

// Mock historical time series data for Recharts
const PERFORMANCE_TIME_SERIES = [
  { time: '00:00', prAuc: 0.96, recall: 0.94, f1: 0.93, precision: 0.95 },
  { time: '04:00', prAuc: 0.95, recall: 0.93, f1: 0.92, precision: 0.94 },
  { time: '08:00', prAuc: 0.96, recall: 0.95, f1: 0.94, precision: 0.96 },
  { time: '12:00', prAuc: 0.91, recall: 0.88, f1: 0.86, precision: 0.89 },
  { time: '16:00', prAuc: 0.88, recall: 0.85, f1: 0.83, precision: 0.86 },
  { time: '20:00', prAuc: 0.93, recall: 0.91, f1: 0.90, precision: 0.92 },
  { time: '24:00', prAuc: 0.95, recall: 0.94, f1: 0.93, precision: 0.95 },
];

const DRIFT_SCORE_SERIES = [
  { time: '00:00', transaction_amount: 0.08, device_type: 0.05, ip_risk: 0.04, threshold: 0.2 },
  { time: '04:00', transaction_amount: 0.11, device_type: 0.07, ip_risk: 0.05, threshold: 0.2 },
  { time: '08:00', transaction_amount: 0.14, device_type: 0.09, ip_risk: 0.06, threshold: 0.2 },
  { time: '12:00', transaction_amount: 0.29, device_type: 0.18, ip_risk: 0.11, threshold: 0.2 },
  { time: '16:00', transaction_amount: 0.36, device_type: 0.22, ip_risk: 0.14, threshold: 0.2 },
  { time: '20:00', transaction_amount: 0.21, device_type: 0.14, ip_risk: 0.08, threshold: 0.2 },
  { time: '24:00', transaction_amount: 0.12, device_type: 0.08, ip_risk: 0.05, threshold: 0.2 },
];

const PREDICTION_DISTRIBUTION_DATA = [
  { bin: '0.0-0.2 (Legit)', count: 12450, color: '#10b981' },
  { bin: '0.2-0.4 (Low Risk)', count: 3200, color: '#0ea5e9' },
  { bin: '0.4-0.6 (Medium)', count: 850, color: '#f59e0b' },
  { bin: '0.6-0.8 (High Risk)', count: 420, color: '#f97316' },
  { bin: '0.8-1.0 (Fraud)', count: 180, color: '#ef4444' },
];

const VOLUME_LATENCY_SERIES = [
  { time: '00:00', volume: 14200, latencyP95: 16.2 },
  { time: '04:00', volume: 11800, latencyP95: 15.8 },
  { time: '08:00', volume: 18900, latencyP95: 19.4 },
  { time: '12:00', volume: 24500, latencyP95: 24.1 },
  { time: '16:00', volume: 22100, latencyP95: 21.5 },
  { time: '20:00', volume: 17600, latencyP95: 18.0 },
  { time: '24:00', volume: 15400, latencyP95: 16.9 },
];

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [timeRange, setTimeRange] = useState('Last 24h');
  const [isDriftModalOpen, setIsDriftModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const { isConnected, lastEvent } = useWebSocket();
  const store = useSentinelStore();

  // Fetch real-time health data using TanStack Query
  const { data: healthData, refetch: refetchHealth } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/health');
        return res.data;
      } catch (err) {
        return { status: 'healthy', version: '1.0.0' };
      }
    },
    refetchInterval: 10000,
  });

  // Fetch active models using TanStack Query
  const { data: modelsData } = useQuery({
    queryKey: ['modelsList'],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/models');
        return res.data;
      } catch (err) {
        return store.models;
      }
    },
  });

  // Handle WebSocket event broadcasts
  React.useEffect(() => {
    if (lastEvent) {
      console.log('[Dashboard] WebSocket event received:', lastEvent);
      if (lastEvent.event_type === 'DRIFT_DETECTED') {
        setToastMessage(`DRIFT DETECTED: ${lastEvent.payload?.drift_type || 'Data drift'} threshold exceeded!`);
        queryClient.invalidateQueries({ queryKey: ['systemHealth'] });
      } else if (lastEvent.event_type === 'RETRAINING_STARTED') {
        setToastMessage(`RETRAINING STARTED: Self-healing pipeline initiated for run ${lastEvent.payload?.run_id}`);
      } else if (lastEvent.event_type === 'MODEL_PROMOTED') {
        setToastMessage(`MODEL PROMOTED: Version ${lastEvent.payload?.version_str} is now PRODUCTION.`);
        queryClient.invalidateQueries({ queryKey: ['modelsList'] });
      }
    }
  }, [lastEvent, queryClient]);

  const handleDriftSuccess = (details: any) => {
    setToastMessage(`Synthetic drift scenario '${details.scenario || 'MULTI_FEATURE_DRIFT'}' injected successfully!`);
    queryClient.invalidateQueries({ queryKey: ['systemHealth'] });
    setTimeout(() => setToastMessage(null), 6000);
  };

  const isSystemHealthy = store.modelHealth > 75;

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-slate-950 text-slate-100 w-full h-full space-y-6">
      {/* Top Header & Action Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold font-mono tracking-tight text-white">
              SentinelML Control Center
            </h1>
            <StatusBadge status={isSystemHealthy ? 'HEALTHY' : 'DEGRADED'} />
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time Machine Learning Reliability, Feature Drift & Autonomous Recovery Engine
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Real-time WebSocket connection status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs text-slate-400">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span>{isConnected ? 'WS Stream Active' : 'WS Reconnecting'}</span>
          </div>

          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="Last 1h">Last 1h</option>
            <option value="Last 24h">Last 24h</option>
            <option value="Last 7d">Last 7d</option>
            <option value="Last 30d">Last 30d</option>
          </select>

          {/* INJECT DRIFT BUTTON */}
          <button
            onClick={() => setIsDriftModalOpen(true)}
            className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 font-bold font-mono text-xs rounded-xl shadow-lg flex items-center gap-2 transition-all"
          >
            <Zap className="w-4 h-4 fill-slate-950" />
            INJECT DRIFT
          </button>
        </div>
      </div>

      {/* Toast Alert Banner */}
      {toastMessage && (
        <AlertBanner
          type="warning"
          title="Operational Telemetry Notice"
          message={toastMessage}
          onClose={() => setToastMessage(null)}
        />
      )}

      {/* Top Banner: Active Production Model & High-level Status */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-center">
        {/* Production Model */}
        <div className="flex items-center gap-3 border-r border-slate-800/80 pr-4">
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400 border border-purple-500/20">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Active Production Model</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-base font-bold font-mono text-white">{store.activeModelName}</span>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40">
                {store.activeModelVersion}
              </span>
            </div>
          </div>
        </div>

        {/* Model Health Score */}
        <div className="border-r border-slate-800/80 pr-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Model Health Score</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span
              className={`text-2xl font-bold font-mono ${
                store.modelHealth > 80 ? 'text-emerald-400' : 'text-amber-400'
              }`}
            >
              {store.modelHealth}%
            </span>
            <span className="text-xs font-mono text-slate-400">
              {store.healthTrend > 0 ? `+${store.healthTrend}%` : `${store.healthTrend}%`}
            </span>
          </div>
        </div>

        {/* Data Drift Status */}
        <div className="border-r border-slate-800/80 pr-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Data Drift Status</span>
          <div className="mt-1">
            <StatusBadge status={store.dataDriftLevel === 'High' ? 'DEGRADED' : 'HEALTHY'} />
          </div>
        </div>

        {/* Concept Drift Status */}
        <div className="border-r border-slate-800/80 pr-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Concept Drift Status</span>
          <div className="mt-1">
            <StatusBadge status={store.predictionDriftLevel === 'High' ? 'CRITICAL' : 'HEALTHY'} />
          </div>
        </div>

        {/* Open Incidents */}
        <div>
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Open Incidents</span>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xl font-bold font-mono text-rose-400">{store.openIncidentsCount}</span>
            <span className="text-xs font-mono text-slate-400">Active RCA Alerts</span>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Precision"
          value="0.942"
          change={1.2}
          subValue="Threshold > 0.90"
          status="good"
        />
        <MetricCard
          title="Recall"
          value={`${store.recall}%`}
          change={-2.4}
          subValue="SLA Target 95%"
          status="warning"
        />
        <MetricCard
          title="F1-Score"
          value="0.940"
          change={0.8}
          subValue="Macro Average"
          status="good"
        />
        <MetricCard
          title="PR-AUC"
          value={store.prAuc}
          change={store.prAucTrend}
          subValue="Area under PR curve"
          highlight
          status="good"
        />
        <MetricCard
          title="Prediction Vol."
          value="14.2k/m"
          change={5.4}
          subValue="Total 1.2M requests"
          status="neutral"
        />
        <MetricCard
          title="P95 Latency"
          value="18.4ms"
          change={-1.1}
          subValue="SLA < 50ms"
          status="good"
        />
      </div>

      {/* Recharts Row 1: Model Performance Over Time & Prediction Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Model Performance Over Time */}
        <ChartCard
          title="Model Performance Over Time"
          subtitle="Real-time precision, recall, F1, and PR-AUC metric trajectories"
          actions={
            <span className="text-xs font-mono text-purple-400 bg-purple-950/40 px-2 py-1 rounded border border-purple-800/40">
              PR-AUC Target: 0.95
            </span>
          }
        >
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={PERFORMANCE_TIME_SERIES}>
              <defs>
                <linearGradient id="prAucGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="recallGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <YAxis domain={[0.8, 1.0]} stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Area type="monotone" dataKey="prAuc" name="PR-AUC" stroke="#a855f7" fillOpacity={1} fill="url(#prAucGradient)" strokeWidth={2} />
              <Area type="monotone" dataKey="recall" name="Recall" stroke="#38bdf8" fillOpacity={1} fill="url(#recallGradient)" strokeWidth={2} />
              <Line type="monotone" dataKey="f1" name="F1-Score" stroke="#34d399" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 2: Prediction Probability Distribution */}
        <ChartCard
          title="Prediction Probability Distribution"
          subtitle="Inference score distribution across probability buckets"
          actions={
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-800/40">
              Fraud Ratio: 1.2%
            </span>
          }
        >
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={PREDICTION_DISTRIBUTION_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="bin" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="count" name="Transaction Count" fill="#a855f7" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Recharts Row 2: Drift Score Over Time & Prediction Volume/Latency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 3: Drift Score Over Time */}
        <ChartCard
          title="Feature & Concept Drift Score Over Time"
          subtitle="Kolmogorov-Smirnov & PSI statistical drift distance metrics"
          actions={
            <span className="text-xs font-mono text-amber-400 bg-amber-950/40 px-2 py-1 rounded border border-amber-800/40">
              PSI Threshold: 0.20
            </span>
          }
        >
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={DRIFT_SCORE_SERIES}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <YAxis domain={[0.0, 0.5]} stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <ReferenceLine y={0.2} label={{ value: 'Drift Threshold (0.2)', fill: '#f59e0b', fontSize: 10 }} stroke="#f59e0b" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="transaction_amount" name="transaction_amount" stroke="#f59e0b" strokeWidth={2.5} />
              <Line type="monotone" dataKey="device_type" name="device_type" stroke="#38bdf8" strokeWidth={2} />
              <Line type="monotone" dataKey="ip_risk" name="ip_risk_score" stroke="#34d399" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 4: Prediction Volume & Latency */}
        <ChartCard
          title="Prediction Volume & P95 Latency"
          subtitle="Throughput volume and 95th percentile inference latency"
          actions={
            <span className="text-xs font-mono text-sky-400 bg-sky-950/40 px-2 py-1 rounded border border-sky-800/40">
              Avg Latency: 18.2ms
            </span>
          }
        >
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={VOLUME_LATENCY_SERIES}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Area yAxisId="left" type="monotone" dataKey="volume" name="Volume (req/h)" fill="#3b82f6" fillOpacity={0.2} stroke="#3b82f6" strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="latencyP95" name="P95 Latency (ms)" stroke="#f43f5e" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Operations Row: Recent Incidents & Retraining/Deployment Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1 & 2: Recent Incidents Table */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-tight">Recent Operational Incidents</h3>
              <p className="text-xs text-slate-400 mt-0.5">Active drift and performance alerts requiring root cause analysis</p>
            </div>
            <a href="/incidents" className="text-xs font-mono text-purple-400 hover:text-purple-300 font-semibold">
              View All Incidents →
            </a>
          </div>

          <DataTable
            columns={[
              {
                key: 'title',
                header: 'Incident Title',
                render: (inc: any) => (
                  <div className="max-w-xs">
                    <p className="font-semibold text-slate-200 truncate">{inc.title}</p>
                    <p className="text-[11px] text-slate-500 font-mono">{inc.id} • {inc.createdAt}</p>
                  </div>
                ),
              },
              {
                key: 'affectedModel',
                header: 'Model Version',
                render: (inc: any) => <ModelBadge modelName="FraudDetector" version={inc.affectedModel?.split(' ')[1] || 'v1.0.0'} />,
              },
              {
                key: 'severity',
                header: 'Severity',
                render: (inc: any) => <SeverityBadge severity={inc.severity} size="sm" />,
              },
              {
                key: 'status',
                header: 'Status',
                render: (inc: any) => <StatusBadge status={inc.status} size="sm" />,
              },
            ]}
            data={store.incidents}
            keyExtractor={(inc: any) => inc.id}
          />
        </div>

        {/* Column 3: Self-Healing & Deployment Timeline */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-tight">Self-Healing Activity Feed</h3>
              <p className="text-xs text-slate-400 mt-0.5">Automated retraining & canary deployment timeline</p>
            </div>
            <RotateCcw className="w-4 h-4 text-purple-400" />
          </div>

          <Timeline
            events={store.recoveryActivities.map((act) => ({
              id: act.id,
              title: act.title,
              timestamp: act.timeAgo,
              status: act.status as any,
              tag: act.isCurrent ? 'ACTIVE FLOW' : undefined,
            }))}
          />
        </div>
      </div>

      {/* Inject Drift Modal */}
      <InjectDriftModal
        isOpen={isDriftModalOpen}
        onClose={() => setIsDriftModalOpen(false)}
        onSuccess={handleDriftSuccess}
      />
    </main>
  );
}
