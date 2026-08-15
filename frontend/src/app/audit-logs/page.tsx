'use client';

import React, { useState } from 'react';
import {
  FileText,
  Search,
  Filter,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Download,
  X,
  ExternalLink,
  Code,
  Key,
  Layers,
  Terminal,
  RotateCcw,
} from 'lucide-react';
import { StatusBadge, MetricCard, DataTable, AlertBanner } from '@/components/ui';

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  eventType: 'MODEL_PROMOTION' | 'MODEL_ROLLBACK' | 'CANARY_SCALE' | 'DRIFT_INJECTION' | 'CONFIG_CHANGE' | 'RETRAINING_TRIGGER';
  actor: string;
  actorRole: string;
  targetResource: string;
  summary: string;
  severity: 'INFO' | 'WARN' | 'CRITICAL';
  ipAddress: string;
  signatureHash: string;
  payloadJson: Record<string, any>;
}

const AUDIT_LOGS_DATA: AuditLogEntry[] = [
  {
    id: 'log-8f92a101',
    timestamp: '2026-08-15 15:42:12',
    eventType: 'MODEL_PROMOTION',
    actor: 'alex.mlops@sentinelml.io',
    actorRole: 'Lead MLOps Engineer',
    targetResource: 'FraudDetector v18',
    summary: 'Promoted candidate model version v18 to 100% PRODUCTION following canary SLA validation.',
    severity: 'INFO',
    ipAddress: '192.168.1.140',
    signatureHash: 'sha256:8f3c...9a01',
    payloadJson: {
      action: 'PROMOTE_MODEL',
      model_name: 'FraudDetector',
      from_version: 'v17',
      to_version: 'v18',
      traffic_allocation: 100,
      validation_metrics: { pr_auc: 0.965, recall: 0.951, f1: 0.938 },
      approved_by: 'alex.mlops@sentinelml.io',
    },
  },
  {
    id: 'log-8f92a102',
    timestamp: '2026-08-15 15:15:00',
    eventType: 'CANARY_SCALE',
    actor: 'alex.mlops@sentinelml.io',
    actorRole: 'Lead MLOps Engineer',
    targetResource: 'FraudDetector v18',
    summary: 'Scaled canary traffic allocation from 10% to 25% for candidate v18.',
    severity: 'INFO',
    ipAddress: '192.168.1.140',
    signatureHash: 'sha256:7b2d...1c4e',
    payloadJson: {
      action: 'SCALE_CANARY',
      model_name: 'FraudDetector',
      version: 'v18',
      previous_percent: 10,
      new_percent: 25,
    },
  },
  {
    id: 'log-8f92a103',
    timestamp: '2026-08-15 14:05:33',
    eventType: 'DRIFT_INJECTION',
    actor: 'system.test@sentinelml.io',
    actorRole: 'Automated Test Runner',
    targetResource: 'transaction_amount',
    summary: 'Injected synthetic multi-feature drift scenario (PSI: +0.28) for resiliency validation.',
    severity: 'WARN',
    ipAddress: '10.0.4.12',
    signatureHash: 'sha256:5e1f...4d89',
    payloadJson: {
      action: 'INJECT_DRIFT_SCENARIO',
      scenario: 'MULTI_FEATURE_DRIFT',
      features_affected: ['transaction_amount', 'device_type'],
      target_psi: 0.284,
    },
  },
  {
    id: 'log-8f92a104',
    timestamp: '2026-08-15 11:30:19',
    eventType: 'RETRAINING_TRIGGER',
    actor: 'Celery-Worker-01',
    actorRole: 'Automated Pipeline Task',
    targetResource: 'FraudDetector v18 Pipeline',
    summary: 'Automated retraining flow triggered by drift anomaly detection policy.',
    severity: 'INFO',
    ipAddress: '10.0.2.88',
    signatureHash: 'sha256:3a9b...7c22',
    payloadJson: {
      action: 'TRIGGER_RETRAINING',
      trigger_source: 'AUTOMATED_DRIFT_RCA',
      run_id: 'run-cc4a64a5',
      dataset: 'ds_v1.4',
    },
  },
  {
    id: 'log-8f92a105',
    timestamp: '2026-08-12 09:12:45',
    eventType: 'MODEL_ROLLBACK',
    actor: 'Prefect-Safety-Guard',
    actorRole: 'Automated SLA Circuit Breaker',
    targetResource: 'FraudDetector v15',
    summary: 'Automated rollback triggered for FraudDetector v15 to v14 due to P99 latency SLA breach (> 50ms).',
    severity: 'CRITICAL',
    ipAddress: '10.0.1.5',
    signatureHash: 'sha256:9c1a...8e00',
    payloadJson: {
      action: 'CIRCUIT_BREAKER_ROLLBACK',
      model_name: 'FraudDetector',
      failed_version: 'v15',
      fallback_version: 'v14',
      breach_reason: 'P99_LATENCY_EXCEEDED',
      measured_latency: '64.2ms',
      sla_limit: '50.0ms',
    },
  },
  {
    id: 'log-8f92a106',
    timestamp: '2026-08-10 18:00:00',
    eventType: 'CONFIG_CHANGE',
    actor: 'sarah.security@sentinelml.io',
    actorRole: 'Security Administrator',
    targetResource: 'Platform Drift Policy',
    summary: 'Updated statistical test algorithm policy from KS-Test to Population Stability Index (PSI).',
    severity: 'INFO',
    ipAddress: '192.168.1.188',
    signatureHash: 'sha256:11bb...44ff',
    payloadJson: {
      action: 'UPDATE_SETTINGS',
      key: 'statistical_algorithm',
      old_value: 'KS_TEST',
      new_value: 'PSI',
    },
  },
];

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>(AUDIT_LOGS_DATA);
  const [searchQuery, setSearchQuery] = useState('');
  const [eventFilter, setEventFilter] = useState('All');
  const [severityFilter, setSeverityFilter] = useState('All');
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.targetResource.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesEvent = eventFilter === 'All' || log.eventType === eventFilter;
    const matchesSeverity = severityFilter === 'All' || log.severity === severityFilter;
    return matchesSearch && matchesEvent && matchesSeverity;
  });

  const downloadAuditLogs = () => {
    const jsonStr = JSON.stringify(logs, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sentinelml_audit_trail_${new Date().toISOString().substring(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <ShieldCheck className="w-7 h-7 text-purple-400" />
              Cryptographic Compliance Audit Logs
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-emerald-300 border border-[#252E3B] font-semibold flex items-center gap-1">
              <Lock className="w-3 h-3 text-emerald-400" />
              SHA-256 Chain Signed
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Immutable security and administrative actions trail for model promotions, rollbacks, configuration updates, and SOC2 compliance auditing
          </p>
        </div>

        <button
          onClick={downloadAuditLogs}
          className="px-4 py-2 bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-200 font-mono text-xs font-semibold rounded-lg flex items-center gap-2 transition-all"
        >
          <Download className="w-4 h-4 text-purple-400" />
          Export Audit Trail JSON
        </button>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Total Audit Entries" value={logs.length} subValue="Cryptographically logged" status="neutral" />
        <MetricCard title="Model Promotions" value="14" subValue="Approved production promotions" status="good" />
        <MetricCard title="Automated Rollbacks" value="2" subValue="SLA safety breaches caught" status="warning" />
        <MetricCard title="Hash Integrity Gate" value="VERIFIED" subValue="SHA-256 tamper-proof" status="good" highlight />
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-[240px] bg-[#101417] border border-[#252E3B] px-3.5 py-2 rounded-lg focus-within:border-purple-500 transition-colors">
          <Search className="w-4 h-4 text-[#94a3b8]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search audit logs by actor, action summary, resource, or log ID..."
            className="bg-transparent border-none outline-none text-xs font-mono text-slate-200 placeholder-slate-500 w-full focus:ring-0"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Event Types</option>
            <option value="MODEL_PROMOTION">MODEL_PROMOTION</option>
            <option value="MODEL_ROLLBACK">MODEL_ROLLBACK</option>
            <option value="CANARY_SCALE">CANARY_SCALE</option>
            <option value="DRIFT_INJECTION">DRIFT_INJECTION</option>
            <option value="RETRAINING_TRIGGER">RETRAINING_TRIGGER</option>
            <option value="CONFIG_CHANGE">CONFIG_CHANGE</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      {/* Main Audit Log Table */}
      <DataTable
        columns={[
          {
            key: 'timestamp',
            header: 'Timestamp',
            render: (log: AuditLogEntry) => (
              <span className="font-mono text-xs text-[#94a3b8] whitespace-nowrap">{log.timestamp}</span>
            ),
          },
          {
            key: 'eventType',
            header: 'Event Type',
            render: (log: AuditLogEntry) => (
              <span
                className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${
                  log.eventType === 'MODEL_PROMOTION'
                    ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/40'
                    : log.eventType === 'MODEL_ROLLBACK'
                    ? 'bg-rose-950/60 text-rose-400 border-rose-800/40'
                    : log.eventType === 'DRIFT_INJECTION'
                    ? 'bg-amber-950/60 text-amber-400 border-amber-800/40'
                    : 'bg-purple-950/60 text-purple-300 border-purple-800/40'
                }`}
              >
                {log.eventType}
              </span>
            ),
          },
          {
            key: 'actor',
            header: 'Performed By / Actor',
            render: (log: AuditLogEntry) => (
              <div>
                <p className="font-mono font-bold text-white text-xs truncate max-w-[160px]">{log.actor}</p>
                <p className="text-[10px] font-mono text-[#94a3b8]">{log.actorRole}</p>
              </div>
            ),
          },
          {
            key: 'targetResource',
            header: 'Target Resource',
            render: (log: AuditLogEntry) => (
              <span className="font-mono text-xs font-bold text-purple-400">{log.targetResource}</span>
            ),
          },
          {
            key: 'summary',
            header: 'Audit Action Summary',
            render: (log: AuditLogEntry) => (
              <p className="font-semibold text-slate-200 text-xs truncate max-w-md" title={log.summary}>
                {log.summary}
              </p>
            ),
          },
          {
            key: 'ipAddress',
            header: 'Origin IP',
            render: (log: AuditLogEntry) => (
              <span className="font-mono text-[11px] text-[#94a3b8]">{log.ipAddress}</span>
            ),
          },
          {
            key: 'actions',
            header: 'Signature & Payload',
            render: (log: AuditLogEntry) => (
              <button
                onClick={() => setSelectedLog(log)}
                className="px-2.5 py-1 text-[11px] font-mono font-semibold bg-purple-950/40 text-purple-300 hover:bg-purple-900/50 border border-purple-800/40 rounded transition-colors flex items-center gap-1"
              >
                <Code className="w-3 h-3" />
                View Payload
              </button>
            ),
          },
        ]}
        data={filteredLogs}
        keyExtractor={(log: AuditLogEntry) => log.id}
      />

      {/* JSON Payload Inspector Drawer */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#101417] border-l border-[#252E3B] w-full max-w-2xl h-full rounded-2xl p-6 shadow-2xl overflow-y-auto space-y-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-[#252E3B]">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold font-mono text-white">{selectedLog.id}</h3>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40 font-semibold">
                    {selectedLog.eventType}
                  </span>
                </div>
                <p className="text-xs font-mono text-[#94a3b8] mt-1">{selectedLog.timestamp} • IP: {selectedLog.ipAddress}</p>
              </div>

              <button onClick={() => setSelectedLog(null)} className="p-1 rounded-lg text-[#94a3b8] hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Cryptographic Proof Verification Card */}
            <div className="bg-[#101417] border border-emerald-500/40 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  SHA-256 Cryptographic Chain Signature
                </span>
                <span className="text-emerald-300 font-semibold">VERIFIED</span>
              </div>
              <p className="text-[11px] font-mono text-slate-300 break-all bg-[#101417] p-2 rounded border border-[#252E3B]">
                {selectedLog.signatureHash}
              </p>
            </div>

            {/* Detailed Description */}
            <div className="space-y-1">
              <span className="text-xs font-mono text-[#94a3b8] font-bold">Action Description:</span>
              <p className="text-xs font-mono text-slate-200 bg-[#101417] border border-[#252E3B] p-3 rounded-lg leading-relaxed">
                {selectedLog.summary}
              </p>
            </div>

            {/* Raw JSON Payload */}
            <div className="space-y-2">
              <span className="text-xs font-mono text-white font-bold flex items-center gap-2">
                <Terminal className="w-4 h-4 text-purple-400" />
                Raw Audited Event JSON Payload
              </span>
              <pre className="bg-[#101417] border border-[#252E3B] p-4 rounded-lg font-mono text-xs text-purple-300 overflow-x-auto">
                {JSON.stringify(selectedLog.payloadJson, null, 2)}
              </pre>
            </div>

            <div className="pt-4 border-t border-[#252E3B] flex justify-between items-center text-xs font-mono">
              <span className="text-[#94a3b8]">Actor: {selectedLog.actor}</span>
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(selectedLog.payloadJson, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${selectedLog.id}_payload.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export Payload
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
