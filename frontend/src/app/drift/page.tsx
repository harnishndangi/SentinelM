'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  Zap,
  Filter,
  BarChart2,
  TrendingUp,
  TrendingDown,
  Minus,
  X,
  Sliders,
  CheckCircle2,
  AlertOctagon,
  Layers,
  Sparkles,
} from 'lucide-react';
import { StatusBadge, SeverityBadge, MetricCard, ChartCard, DataTable, AlertBanner } from '@/components/ui';
import { useSentinelStore } from '@/store/useSentinelStore';
import { apiClient } from '@/services/api';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

export interface ExtendedDriftFeature {
  featureName: string;
  psi: number;
  ks: number;
  pValue: number;
  jsDivergence: number;
  wasserstein: number;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  trend: 'up' | 'down' | 'stable';
  refMean: number;
  curMean: number;
  nullCount: number;
}

const FEATURE_DRIFT_DATA: ExtendedDriftFeature[] = [
  {
    featureName: 'transaction_amount',
    psi: 0.284,
    ks: 0.312,
    pValue: 0.001,
    jsDivergence: 0.198,
    wasserstein: 42.85,
    severity: 'CRITICAL',
    trend: 'up',
    refMean: 124.5,
    curMean: 310.2,
    nullCount: 0,
  },
  {
    featureName: 'device_type',
    psi: 0.192,
    ks: 0.215,
    pValue: 0.024,
    jsDivergence: 0.142,
    wasserstein: 1.84,
    severity: 'HIGH',
    trend: 'up',
    refMean: 0.72,
    curMean: 0.45,
    nullCount: 12,
  },
  {
    featureName: 'ip_risk_score',
    psi: 0.125,
    ks: 0.141,
    pValue: 0.082,
    jsDivergence: 0.088,
    wasserstein: 0.12,
    severity: 'MEDIUM',
    trend: 'stable',
    refMean: 0.24,
    curMean: 0.31,
    nullCount: 2,
  },
  {
    featureName: 'merchant_category',
    psi: 0.082,
    ks: 0.095,
    pValue: 0.145,
    jsDivergence: 0.054,
    wasserstein: 0.65,
    severity: 'LOW',
    trend: 'down',
    refMean: 14.2,
    curMean: 14.8,
    nullCount: 0,
  },
  {
    featureName: 'billing_zip_mismatch',
    psi: 0.045,
    ks: 0.052,
    pValue: 0.320,
    jsDivergence: 0.028,
    wasserstein: 0.05,
    severity: 'LOW',
    trend: 'stable',
    refMean: 0.08,
    curMean: 0.09,
    nullCount: 0,
  },
];

// Distribution Histogram for Drawer Component
const DISTRIBUTION_HISTOGRAM = [
  { bin: '0-100', ref: 450, cur: 180 },
  { bin: '100-200', ref: 380, cur: 220 },
  { bin: '200-300', ref: 120, cur: 390 },
  { bin: '300-400', ref: 40, cur: 310 },
  { bin: '400-500+', ref: 10, cur: 150 },
];

const HISTORICAL_DRIFT_TIMELINE = [
  { time: '00:00', psi: 0.08, threshold: 0.2 },
  { time: '04:00', psi: 0.11, threshold: 0.2 },
  { time: '08:00', psi: 0.14, threshold: 0.2 },
  { time: '12:00', psi: 0.29, threshold: 0.2 },
  { time: '16:00', psi: 0.36, threshold: 0.2 },
  { time: '20:00', psi: 0.284, threshold: 0.2 },
];

export default function DriftPage() {
  const store = useSentinelStore();
  const [timeWindow, setTimeWindow] = useState('24h');
  const [severityFilter, setSeverityFilter] = useState('All');
  const [selectedFeature, setSelectedFeature] = useState<ExtendedDriftFeature | null>(null);

  // TanStack Query for drift telemetry from backend
  const { data: driftData = FEATURE_DRIFT_DATA } = useQuery({
    queryKey: ['driftTelemetry', timeWindow],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/drift');
        if (Array.isArray(res.data) && res.data.length > 0) {
          return res.data;
        }
        return FEATURE_DRIFT_DATA;
      } catch (err) {
        return FEATURE_DRIFT_DATA;
      }
    },
  });

  const filteredFeatures = driftData.filter(
    (f) => severityFilter === 'All' || f.severity === severityFilter
  );

  const hasCriticalDrift = driftData.some((f) => f.severity === 'CRITICAL' || f.severity === 'HIGH');

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Feature & Concept Drift Analyzer
            </h1>
            <StatusBadge status={hasCriticalDrift ? 'DEGRADED' : 'HEALTHY'} />
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Statistical covariate shift detection using Kolmogorov-Smirnov, PSI, Wasserstein, & JS Divergence tests
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Time-Window Selection */}
          <div className="flex items-center gap-2 bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-1.5 font-mono text-xs text-slate-300">
            <span className="text-[#94a3b8]">Time Window:</span>
            {['1h', '24h', '7d', '30d'].map((tw) => (
              <button
                key={tw}
                onClick={() => setTimeWindow(tw)}
                className={`px-2.5 py-1 rounded transition-colors font-semibold ${
                  timeWindow === tw ? 'bg-purple-600 text-white shadow-sm' : 'hover:bg-slate-800 text-[#94a3b8]'
                }`}
              >
                {tw}
              </button>
            ))}
          </div>
        </div>
      </div>


      {/* Top Drift Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Overall Drift Status"
          value={hasCriticalDrift ? 'DRIFT DETECTED' : 'NO DRIFT'}
          subValue="2 features > 0.20 threshold"
          status={hasCriticalDrift ? 'bad' : 'good'}
          highlight
        />
        <MetricCard
          title="Data Drift Score (PSI)"
          value="0.284"
          change={12.4}
          subValue="max PSI (transaction_amount)"
          status="bad"
        />
        <MetricCard
          title="Prediction Drift (PSI)"
          value="0.142"
          change={4.2}
          subValue="Output probability shift"
          status="warning"
        />
        <MetricCard
          title="Concept Drift (PR-AUC Loss)"
          value="0.038"
          change={-1.5}
          subValue="PR-AUC degradation rate"
          status="good"
        />
      </div>

      {/* Feature Drift Heatmap & Filter Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold font-mono text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" />
              Feature Drift Distribution Heatmap & Statistical Distance Table
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Click any feature row to inspect baseline vs current distributions</p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 font-mono text-xs text-purple-300 focus:outline-none focus:border-purple-500"
            >
              <option value="All">All Severities</option>
              <option value="CRITICAL">CRITICAL (&gt; 0.25)</option>
              <option value="HIGH">HIGH (0.18 - 0.25)</option>
              <option value="MEDIUM">MEDIUM (0.10 - 0.18)</option>
              <option value="LOW">LOW (&lt; 0.10)</option>
            </select>
          </div>
        </div>

        <DataTable
          columns={[
            {
              key: 'featureName',
              header: 'Feature Name',
              render: (f: ExtendedDriftFeature) => (
                <div className="flex items-center gap-2 font-bold text-white">
                  <span className="text-purple-400">{f.featureName}</span>
                  {f.severity === 'CRITICAL' && (
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" title="Critical Drift Alert" />
                  )}
                </div>
              ),
            },
            {
              key: 'psi',
              header: 'PSI Score',
              render: (f: ExtendedDriftFeature) => (
                <span className={`font-mono font-bold ${f.psi > 0.2 ? 'text-rose-400' : 'text-slate-200'}`}>
                  {f.psi.toFixed(3)}
                </span>
              ),
            },
            {
              key: 'ks',
              header: 'KS Statistic (p-val)',
              render: (f: ExtendedDriftFeature) => (
                <span className="font-mono text-slate-300">
                  {f.ks.toFixed(3)} <span className="text-slate-500 text-[11px]">(p={f.pValue})</span>
                </span>
              ),
            },
            {
              key: 'jsDivergence',
              header: 'JS Divergence',
              render: (f: ExtendedDriftFeature) => <span className="font-mono text-slate-300">{f.jsDivergence.toFixed(3)}</span>,
            },
            {
              key: 'wasserstein',
              header: 'Wasserstein Dist.',
              render: (f: ExtendedDriftFeature) => <span className="font-mono text-slate-300">{f.wasserstein.toFixed(2)}</span>,
            },
            {
              key: 'severity',
              header: 'Severity',
              render: (f: ExtendedDriftFeature) => <SeverityBadge severity={f.severity} size="sm" />,
            },
            {
              key: 'trend',
              header: 'Trend',
              render: (f: ExtendedDriftFeature) => (
                <div className="flex items-center gap-1 font-mono text-xs">
                  {f.trend === 'up' && <TrendingUp className="w-3.5 h-3.5 text-rose-400" />}
                  {f.trend === 'down' && <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />}
                  {f.trend === 'stable' && <Minus className="w-3.5 h-3.5 text-slate-400" />}
                  <span className="uppercase text-[11px]">{f.trend}</span>
                </div>
              ),
            },
          ]}
          data={filteredFeatures}
          keyExtractor={(f: ExtendedDriftFeature) => f.featureName}
          onRowClick={(f: ExtendedDriftFeature) => setSelectedFeature(f)}
        />
      </div>

      {/* Feature Detail Drawer / Modal */}
      {selectedFeature && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border-l border-slate-700 w-full max-w-2xl h-full rounded-2xl p-6 shadow-2xl overflow-y-auto space-y-6 relative">
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold font-mono text-white">{selectedFeature.featureName}</h3>
                  <SeverityBadge severity={selectedFeature.severity} />
                </div>
                <p className="text-xs font-mono text-slate-400 mt-1">Detailed Reference vs Live Inference Distribution Shift</p>
              </div>

              <button
                onClick={() => setSelectedFeature(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Distribution Comparison Chart */}
            <ChartCard
              title="Reference vs Current Distribution"
              subtitle="Baseline training data vs live production inference data buckets"
            >
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={DISTRIBUTION_HISTOGRAM}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="bin" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
                  <Bar dataKey="ref" name="Baseline Reference Data" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="cur" name="Current Live Production Data" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Drift Score History Chart */}
            <ChartCard
              title="Drift Trajectory History"
              subtitle="PSI distance score trajectory over time vs 0.20 threshold"
            >
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={HISTORICAL_DRIFT_TIMELINE}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                  <YAxis domain={[0, 0.5]} stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
                  <ReferenceLine y={0.2} label={{ value: 'PSI Threshold (0.2)', fill: '#f59e0b', fontSize: 10 }} stroke="#f59e0b" strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="psi" name="PSI Score" stroke="#a855f7" strokeWidth={2.5} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Statistics Table */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Summary Statistics & Test Metadata</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Reference Mean</span>
                  <span className="text-sky-300 font-bold">{selectedFeature.refMean}</span>
                </div>
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Current Live Mean</span>
                  <span className="text-rose-300 font-bold">{selectedFeature.curMean}</span>
                </div>
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 text-[10px] block">Null Count</span>
                  <span className="text-slate-200 font-bold">{selectedFeature.nullCount}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
