'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  Zap,
  Clock,
  Server,
  Terminal,
  Pause,
  Play,
  Filter,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Layers,
} from 'lucide-react';
import { StatusBadge, MetricCard, ChartCard } from '@/components/ui';
import { useSentinelStore } from '@/store/useSentinelStore';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const TELEMETRY_TIME_SERIES = [
  { time: '15:00', throughput: 1250, latencyP95: 14.2, cpu: 32, ram: 44 },
  { time: '15:05', throughput: 1380, latencyP95: 15.1, cpu: 36, ram: 46 },
  { time: '15:10', throughput: 1420, latencyP95: 14.8, cpu: 35, ram: 45 },
  { time: '15:15', throughput: 1650, latencyP95: 18.2, cpu: 48, ram: 52 },
  { time: '15:20', throughput: 1510, latencyP95: 15.9, cpu: 41, ram: 48 },
  { time: '15:25', throughput: 1490, latencyP95: 14.5, cpu: 38, ram: 47 },
  { time: '15:30', throughput: 1420, latencyP95: 14.2, cpu: 34, ram: 45 },
];

const INITIAL_LOG_STREAM = [
  '[15:30:01] [METRIC] p99_latency: 14.2ms | throughput: 1,420 req/s | status: 200 OK',
  '[15:30:05] [HEALTH] FastAPI worker pool #04 report: 0 failed tasks, 420 requests processed',
  '[15:30:10] [PREDICT] Batch inference model FraudDetector v18: 250 predictions (avg score: 0.14)',
  '[15:30:15] [DRIFT] Feature transaction_amount rolling PSI score: 0.12 (within 0.20 SLA limit)',
  '[15:30:20] [REDIS] Celery task queue depth: 0 pending, worker heartbeat: 100% HEALTHY',
];

export default function MonitoringPage() {
  const store = useSentinelStore();
  const [isStreaming, setIsStreaming] = useState(true);
  const [logs, setLogs] = useState<string[]>(INITIAL_LOG_STREAM);

  // Simulated live log stream updates
  useEffect(() => {
    if (!isStreaming) return;
    const interval = setInterval(() => {
      const time = new Date().toLocaleTimeString();
      const randomLatency = (13.5 + Math.random() * 2).toFixed(1);
      const randomTps = Math.floor(1400 + Math.random() * 100);
      const newLog = `[${time}] [METRIC] p99_latency: ${randomLatency}ms | throughput: ${randomTps.toLocaleString()} req/s | status: 200 OK`;

      setLogs((prev) => [newLog, ...prev.slice(0, 20)]);
    }, 4000);

    return () => clearInterval(interval);
  }, [isStreaming]);

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Activity className="w-7 h-7 text-purple-400" />
              Live Telemetry & Resource Monitor
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-emerald-300 border border-[#252E3B] font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Telemetry Active
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Real-time inference latency, throughput req/s, error rate, hardware utilization, and stream event logs
          </p>
        </div>

        <button
          onClick={() => setIsStreaming(!isStreaming)}
          className={`px-4 py-2 bg-[#101417] border border-[#252E3B] font-mono text-xs font-semibold rounded-lg flex items-center gap-2 transition-all ${
            isStreaming ? 'text-emerald-400 border-emerald-800/40' : 'text-[#94a3b8]'
          }`}
        >
          {isStreaming ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          {isStreaming ? 'Pause Telemetry Stream' : 'Resume Telemetry Stream'}
        </button>
      </div>

      {/* Top Hardware & Performance Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard title="p99 Latency" value="14.2 ms" subValue="Target < 50ms SLA" status="good" highlight />
        <MetricCard title="Inference Rate" value="1,420 req/s" change={3.8} subValue="85.2k req/min" status="neutral" />
        <MetricCard title="Error Rate" value="0.01%" subValue="HTTP 500 errors" status="good" />
        <MetricCard title="CPU Utilization" value="34%" subValue="8 Cores Allocated" status="good" />
        <MetricCard title="Memory Usage" value="4.2 GB" subValue="16 GB Limit" status="good" />
        <MetricCard title="Celery Queue Depth" value="0" subValue="Tasks pending" status="good" />
      </div>

      {/* Active Model Performance Card */}
      <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
          <h2 className="text-lg font-bold font-mono text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            Active Production Model Telemetry Metrics
          </h2>
          <StatusBadge status="HEALTHY" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
          <div className="p-4 bg-[#101417] rounded-lg border border-[#252E3B]">
            <span className="text-[#94a3b8] block mb-1">Model & Version:</span>
            <span className="text-base font-bold text-white">{store.activeModelName} {store.activeModelVersion}</span>
          </div>

          <div className="p-4 bg-[#101417] rounded-lg border border-[#252E3B]">
            <span className="text-[#94a3b8] block mb-1">PR-AUC / Recall:</span>
            <span className="text-base font-bold text-emerald-400">{store.prAuc} / {store.recall}%</span>
          </div>

          <div className="p-4 bg-[#101417] rounded-lg border border-[#252E3B]">
            <span className="text-[#94a3b8] block mb-1">Precision / F1-Score:</span>
            <span className="text-base font-bold text-white">0.942 / 0.938</span>
          </div>

          <div className="p-4 bg-[#101417] rounded-lg border border-[#252E3B]">
            <span className="text-[#94a3b8] block mb-1">Health Score:</span>
            <span className="text-base font-bold text-emerald-400">{store.modelHealth}% (Optimal)</span>
          </div>
        </div>
      </div>

      {/* Real-time Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Throughput vs Latency */}
        <ChartCard
          title="Inference Throughput & P95 Latency"
          subtitle="Real-time request volume (req/s) vs 95th percentile latency (ms)"
        >
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={TELEMETRY_TIME_SERIES}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Area yAxisId="left" type="monotone" dataKey="throughput" name="Throughput (req/s)" fill="#a855f7" fillOpacity={0.2} stroke="#a855f7" strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="latencyP95" name="P95 Latency (ms)" stroke="#38bdf8" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 2: CPU & Memory Utilization */}
        <ChartCard
          title="Compute Cluster Hardware Utilization"
          subtitle="CPU and RAM resource consumption across worker nodes"
        >
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={TELEMETRY_TIME_SERIES}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Line type="monotone" dataKey="cpu" name="CPU Usage (%)" stroke="#34d399" strokeWidth={2.5} />
              <Line type="monotone" dataKey="ram" name="Memory Usage (%)" stroke="#f59e0b" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Live Stream Terminal Logs Container */}
      <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-4 font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-[#252E3B] pb-2">
          <div className="flex items-center gap-2 text-white font-bold">
            <Terminal className="w-4 h-4 text-purple-400" />
            Live Telemetry Event Log Stream
          </div>
          <span className="text-[11px] text-emerald-400 font-semibold">
            {isStreaming ? '● Streaming Live (4s interval)' : '|| Stream Paused'}
          </span>
        </div>

        <div className="max-h-60 overflow-y-auto space-y-1.5 pr-2">
          {logs.map((log, idx) => (
            <div key={idx} className="text-slate-300 text-[11px] font-mono leading-relaxed border-b border-[#252E3B]/30 pb-1">
              {log}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
