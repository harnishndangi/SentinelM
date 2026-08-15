'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  Search,
  Filter,
  ArrowUpRight,
  ShieldAlert,
  RotateCcw,
  CheckCircle2,
  Clock,
  Activity,
  Cpu,
  Layers,
} from 'lucide-react';
import { StatusBadge, SeverityBadge, ModelBadge, MetricCard, DataTable } from '@/components/ui';
import { useSentinelStore } from '@/store/useSentinelStore';
import { apiClient } from '@/services/api';

export interface ExtendedIncidentItem {
  id: string;
  title: string;
  model: string;
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'AUTO_RECOVERED';
  detectedAt: string;
  duration: string;
}

const INCIDENTS_DATA: ExtendedIncidentItem[] = [
  {
    id: 'inc-101',
    title: 'Feature Drift Anomaly: transaction_amount threshold exceeded (> 0.20 PSI)',
    model: 'FraudDetector v17',
    type: 'FEATURE_DRIFT',
    severity: 'CRITICAL',
    status: 'INVESTIGATING',
    detectedAt: '15m ago',
    duration: '12m 45s',
  },
  {
    id: 'inc-102',
    title: 'Model Recall dropped below target SLA (95% -> 88.2%)',
    model: 'FraudDetector v17',
    type: 'PERFORMANCE_DEGRADATION',
    severity: 'HIGH',
    status: 'OPEN',
    detectedAt: '1h ago',
    duration: '48m 10s',
  },
  {
    id: 'inc-103',
    title: 'High P95 Latency spike in prediction pipeline (64.2ms)',
    model: 'FraudDetector v17',
    type: 'LATENCY_SPIKE',
    severity: 'MEDIUM',
    status: 'AUTO_RECOVERED',
    detectedAt: '3h ago',
    duration: '04m 12s',
  },
  {
    id: 'inc-104',
    title: 'Covariate Shift in Mobile OS Device distribution',
    model: 'FraudDetector v16',
    type: 'COVARIATE_SHIFT',
    severity: 'LOW',
    status: 'RESOLVED',
    detectedAt: '1d ago',
    duration: '18m 30s',
  },
];

export default function IncidentsPage() {
  const store = useSentinelStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [severityFilter, setSeverityFilter] = useState('All');

  // Fetch real incidents from backend API with fallback
  const { data: incidentsList = INCIDENTS_DATA } = useQuery({
    queryKey: ['incidentsList'],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/incidents');
        if (Array.isArray(res.data) && res.data.length > 0) {
          return res.data;
        }
        return INCIDENTS_DATA;
      } catch (err) {
        return INCIDENTS_DATA;
      }
    },
  });

  const filteredIncidents = incidentsList.filter((inc) => {
    const matchesSearch =
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.model.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || inc.status === statusFilter;
    const matchesSeverity = severityFilter === 'All' || inc.severity === severityFilter;
    return matchesSearch && matchesStatus && matchesSeverity;
  });

  const openCount = incidentsList.filter((i) => i.status === 'OPEN' || i.status === 'INVESTIGATING').length;
  const criticalCount = incidentsList.filter((i) => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length;

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Top Title Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Operational Incident Control Center
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-rose-400 border border-[#252E3B] font-semibold">
              {openCount} Active Alerts
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Real-time Root Cause Analysis (RCA), drift alerts, and automated self-healing recovery tracking
          </p>
        </div>
      </div>

      {/* Summary Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Total Incidents" value={incidentsList.length} subValue="Last 30 days" status="neutral" />
        <MetricCard title="Active Critical RCA Alerts" value={criticalCount} subValue="SLA Breach Risk" status={criticalCount > 0 ? 'bad' : 'good'} highlight />
        <MetricCard title="Auto-Recovered" value="12" subValue="Self-healing retraining" status="good" />
        <MetricCard title="Avg Recovery Time" value="14m 20s" subValue="Target < 30m SLA" status="good" />
      </div>

      {/* Filter Bar */}
      <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-[240px] bg-[#101417] border border-[#252E3B] px-3.5 py-2 rounded-lg focus-within:border-purple-500 transition-colors">
          <Search className="w-4 h-4 text-[#94a3b8]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter incidents by title, ID, or model name..."
            className="bg-transparent border-none outline-none text-xs font-mono text-slate-200 placeholder-slate-500 w-full focus:ring-0"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="AUTO_RECOVERED">AUTO_RECOVERED</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      {/* Incidents Data Table */}
      <DataTable
        columns={[
          {
            key: 'id',
            header: 'ID',
            render: (inc: ExtendedIncidentItem) => (
              <Link href={`/incidents/${inc.id}`} className="font-mono font-bold text-purple-400 hover:text-purple-300">
                {inc.id}
              </Link>
            ),
          },
          {
            key: 'title',
            header: 'Incident Title',
            render: (inc: ExtendedIncidentItem) => (
              <Link href={`/incidents/${inc.id}`} className="group block max-w-md">
                <p className="font-semibold text-slate-200 group-hover:text-purple-300 transition-colors truncate">
                  {inc.title}
                </p>
              </Link>
            ),
          },
          {
            key: 'model',
            header: 'Affected Model',
            render: (inc: ExtendedIncidentItem) => <ModelBadge modelName={inc.model.split(' ')[0]} version={inc.model.split(' ')[1] || 'v1.0'} />,
          },
          {
            key: 'type',
            header: 'Type',
            render: (inc: ExtendedIncidentItem) => (
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#101417] border border-[#252E3B] text-slate-300">
                {inc.type}
              </span>
            ),
          },
          {
            key: 'severity',
            header: 'Severity',
            render: (inc: ExtendedIncidentItem) => <SeverityBadge severity={inc.severity} size="sm" />,
          },
          {
            key: 'status',
            header: 'Status',
            render: (inc: ExtendedIncidentItem) => <StatusBadge status={inc.status} size="sm" />,
          },
          {
            key: 'detectedAt',
            header: 'Detected',
            render: (inc: ExtendedIncidentItem) => <span className="text-xs font-mono text-[#94a3b8]">{inc.detectedAt}</span>,
          },
          {
            key: 'duration',
            header: 'Duration',
            render: (inc: ExtendedIncidentItem) => <span className="text-xs font-mono text-slate-300">{inc.duration}</span>,
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (inc: ExtendedIncidentItem) => (
              <Link
                href={`/incidents/${inc.id}`}
                className="inline-flex items-center gap-1 text-xs font-mono text-purple-400 hover:text-purple-300 font-semibold"
              >
                RCA Flow <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            ),
          },
        ]}
        data={filteredIncidents}
        keyExtractor={(inc: ExtendedIncidentItem) => inc.id}
      />
    </main>
  );
}
