'use client';

import React, { useState } from 'react';
import {
  Database,
  Search,
  Filter,
  Plus,
  Download,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  X,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Table,
  Check,
  Zap,
} from 'lucide-react';
import { StatusBadge, MetricCard, DataTable, AlertBanner } from '@/components/ui';

export interface SchemaColumn {
  name: string;
  type: string;
  nullable: boolean;
  nullPercentage: number;
  min?: number | string;
  max?: number | string;
  mean?: number | string;
}

export interface DatasetSnapshot {
  id: string;
  versionTag: string;
  name: string;
  type: 'REFERENCE_BASELINE' | 'LIVE_INFERENCE' | 'GOLDEN_EVALUATION' | 'CANARY_SPLIT';
  recordsCount: number;
  featuresCount: number;
  storageSize: string;
  createdAt: string;
  status: 'HEALTHY' | 'DRIFTED' | 'VALIDATING';
  schemaHash: string;
  assertionsPassed: string;
  isBaseline?: boolean;
}

const INITIAL_SNAPSHOTS: DatasetSnapshot[] = [
  {
    id: 'ds-snap-001',
    versionTag: 'ds_v1.4',
    name: 'Production Reference Baseline v1.4',
    type: 'REFERENCE_BASELINE',
    recordsCount: 250000,
    featuresCount: 34,
    storageSize: '142.8 MB',
    createdAt: '2026-08-10 14:20',
    status: 'HEALTHY',
    schemaHash: 'sha256:f4e892c0',
    assertionsPassed: '42/42 Passed',
    isBaseline: true,
  },
  {
    id: 'ds-snap-002',
    versionTag: 'ds_v1.4_live',
    name: 'Live Inference Partition (Aug 15)',
    type: 'LIVE_INFERENCE',
    recordsCount: 45200,
    featuresCount: 34,
    storageSize: '28.4 MB',
    createdAt: '2026-08-15 12:00',
    status: 'DRIFTED',
    schemaHash: 'sha256:f4e892c0',
    assertionsPassed: '40/42 Passed',
  },
  {
    id: 'ds-snap-003',
    versionTag: 'ds_v1.3',
    name: 'Historical Training Baseline v1.3',
    type: 'REFERENCE_BASELINE',
    recordsCount: 210000,
    featuresCount: 32,
    storageSize: '118.2 MB',
    createdAt: '2026-08-01 09:15',
    status: 'HEALTHY',
    schemaHash: 'sha256:a1b2c3d4',
    assertionsPassed: '42/42 Passed',
  },
  {
    id: 'ds-snap-004',
    versionTag: 'ds_golden_eval_v2',
    name: 'Golden Evaluation Benchmark Test Set',
    type: 'GOLDEN_EVALUATION',
    recordsCount: 15000,
    featuresCount: 34,
    storageSize: '9.6 MB',
    createdAt: '2026-08-05 16:45',
    status: 'HEALTHY',
    schemaHash: 'sha256:f4e892c0',
    assertionsPassed: '42/42 Passed',
  },
  {
    id: 'ds-snap-005',
    versionTag: 'ds_canary_v18',
    name: 'Canary Partition FraudDetector v18',
    type: 'CANARY_SPLIT',
    recordsCount: 12500,
    featuresCount: 34,
    storageSize: '7.8 MB',
    createdAt: '2026-08-15 15:30',
    status: 'HEALTHY',
    schemaHash: 'sha256:f4e892c0',
    assertionsPassed: '42/42 Passed',
  },
];

const SAMPLE_SCHEMA_COLUMNS: SchemaColumn[] = [
  { name: 'transaction_amount', type: 'FLOAT64', nullable: false, nullPercentage: 0.0, min: 0.5, max: 12450.0, mean: 284.12 },
  { name: 'device_type', type: 'INT32', nullable: false, nullPercentage: 0.02, min: 0, max: 3, mean: 1.15 },
  { name: 'ip_risk_score', type: 'FLOAT34', nullable: true, nullPercentage: 0.15, min: 0.0, max: 0.99, mean: 0.24 },
  { name: 'merchant_category', type: 'STRING', nullable: false, nullPercentage: 0.0, min: 'cat_01', max: 'cat_99', mean: 'N/A' },
  { name: 'billing_zip_mismatch', type: 'BOOLEAN', nullable: false, nullPercentage: 0.0, min: 0, max: 1, mean: 0.08 },
  { name: 'user_account_age_days', type: 'INT32', nullable: false, nullPercentage: 0.0, min: 1, max: 4500, mean: 684.5 },
  { name: 'failed_login_attempts', type: 'INT32', nullable: false, nullPercentage: 0.0, min: 0, max: 12, mean: 0.32 },
  { name: 'session_duration_sec', type: 'FLOAT64', nullable: false, nullPercentage: 0.05, min: 0.2, max: 3600.0, mean: 184.2 },
];

export default function DatasetSnapshotsPage() {
  const [snapshots, setSnapshots] = useState<DatasetSnapshot[]>(INITIAL_SNAPSHOTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [selectedSnapshot, setSelectedSnapshot] = useState<DatasetSnapshot | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // New snapshot form state
  const [newVersionTag, setNewVersionTag] = useState('ds_v1.5_draft');
  const [newName, setNewName] = useState('Inference Snapshot Aug 15');
  const [newType, setNewType] = useState<'REFERENCE_BASELINE' | 'LIVE_INFERENCE' | 'GOLDEN_EVALUATION' | 'CANARY_SPLIT'>('LIVE_INFERENCE');
  const [newRecords, setNewRecords] = useState(50000);

  const filteredSnapshots = snapshots.filter((snap) => {
    const matchesSearch =
      snap.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      snap.versionTag.toLowerCase().includes(searchQuery.toLowerCase()) ||
      snap.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'All' || snap.type === typeFilter;
    const matchesStatus = statusFilter === 'All' || snap.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const handleSetBaseline = (id: string) => {
    setSnapshots((prev) =>
      prev.map((s) => ({
        ...s,
        isBaseline: s.id === id,
        type: s.id === id ? 'REFERENCE_BASELINE' : s.type === 'REFERENCE_BASELINE' && s.id !== id ? 'LIVE_INFERENCE' : s.type,
      }))
    );
    const updated = snapshots.find((s) => s.id === id);
    setNotification(`Dataset '${updated?.name || id}' set as active Production Reference Baseline!`);
    setTimeout(() => setNotification(null), 5000);
  };

  const handleCreateSnapshot = (e: React.FormEvent) => {
    e.preventDefault();
    const created: DatasetSnapshot = {
      id: `ds-snap-00${snapshots.length + 1}`,
      versionTag: newVersionTag,
      name: newName,
      type: newType,
      recordsCount: newRecords,
      featuresCount: 34,
      storageSize: `${(newRecords * 0.0006).toFixed(1)} MB`,
      createdAt: new Date().toISOString().replace('T', ' ').substring(0, 16),
      status: 'HEALTHY',
      schemaHash: 'sha256:f4e892c0',
      assertionsPassed: '42/42 Passed',
      isBaseline: false,
    };
    setSnapshots([created, ...snapshots]);
    setIsCreateModalOpen(false);
    setNotification(`Dataset snapshot '${newName}' created successfully!`);
    setTimeout(() => setNotification(null), 5000);
  };

  const baselineSnapshot = snapshots.find((s) => s.isBaseline);

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Database className="w-7 h-7 text-purple-400" />
              Dataset Snapshots & Reference Payloads
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-purple-300 border border-[#252E3B] font-semibold">
              {snapshots.length} Snapshots Managed
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Manage training reference data baselines, live inference data partitions, schema versions, and Great Expectations assertions
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold font-mono text-xs rounded-lg shadow-md flex items-center gap-2 transition-all"
          >
            <Plus className="w-4 h-4" />
            CREATE NEW SNAPSHOT
          </button>
        </div>
      </div>

      {notification && (
        <AlertBanner type="success" title="Dataset Operations Notice" message={notification} onClose={() => setNotification(null)} />
      )}

      {/* Summary Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Dataset Snapshots"
          value={snapshots.length}
          subValue="Reference + Live partitions"
          status="neutral"
        />
        <MetricCard
          title="Active Reference Baseline"
          value={baselineSnapshot?.versionTag || 'ds_v1.4'}
          subValue={`${(baselineSnapshot?.recordsCount || 250000).toLocaleString()} records`}
          status="good"
          highlight
        />
        <MetricCard
          title="Schema Integrity Score"
          value="100%"
          subValue="34 features strictly matched"
          status="good"
        />
        <MetricCard
          title="Great Expectations Gate"
          value="42/42"
          subValue="Assertions passed"
          status="good"
        />
      </div>

      {/* Search & Filter Toolbar */}
      <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-[240px] bg-[#101417] border border-[#252E3B] px-3.5 py-2 rounded-lg focus-within:border-purple-500 transition-colors">
          <Search className="w-4 h-4 text-[#94a3b8]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search snapshots by version tag, name, or hash..."
            className="bg-transparent border-none outline-none text-xs font-mono text-slate-200 placeholder-slate-500 w-full focus:ring-0"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Partition Types</option>
            <option value="REFERENCE_BASELINE">REFERENCE_BASELINE</option>
            <option value="LIVE_INFERENCE">LIVE_INFERENCE</option>
            <option value="GOLDEN_EVALUATION">GOLDEN_EVALUATION</option>
            <option value="CANARY_SPLIT">CANARY_SPLIT</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Statuses</option>
            <option value="HEALTHY">HEALTHY</option>
            <option value="DRIFTED">DRIFTED</option>
            <option value="VALIDATING">VALIDATING</option>
          </select>
        </div>
      </div>

      {/* Main Datasets Table */}
      <DataTable
        columns={[
          {
            key: 'versionTag',
            header: 'Version Tag',
            render: (snap: DatasetSnapshot) => (
              <div className="flex items-center gap-2 font-mono font-bold text-white">
                <span className="text-purple-400">{snap.versionTag}</span>
                {snap.isBaseline && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 font-semibold">
                    ★ ACTIVE BASELINE
                  </span>
                )}
              </div>
            ),
          },
          {
            key: 'name',
            header: 'Snapshot Name',
            render: (snap: DatasetSnapshot) => (
              <button
                onClick={() => setSelectedSnapshot(snap)}
                className="text-left group block max-w-xs hover:underline"
              >
                <p className="font-semibold text-slate-200 group-hover:text-purple-300 transition-colors truncate">
                  {snap.name}
                </p>
                <p className="text-[11px] font-mono text-[#94a3b8]">{snap.id}</p>
              </button>
            ),
          },
          {
            key: 'type',
            header: 'Partition Type',
            render: (snap: DatasetSnapshot) => (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#101417] border border-[#252E3B] text-slate-300">
                {snap.type}
              </span>
            ),
          },
          {
            key: 'recordsCount',
            header: 'Records',
            render: (snap: DatasetSnapshot) => (
              <span className="font-mono text-white font-semibold">
                {snap.recordsCount.toLocaleString()}
              </span>
            ),
          },
          {
            key: 'featuresCount',
            header: 'Features',
            render: (snap: DatasetSnapshot) => (
              <span className="font-mono text-slate-300">{snap.featuresCount} cols</span>
            ),
          },
          {
            key: 'storageSize',
            header: 'Size',
            render: (snap: DatasetSnapshot) => (
              <span className="font-mono text-xs text-[#94a3b8]">{snap.storageSize}</span>
            ),
          },
          {
            key: 'status',
            header: 'Status',
            render: (snap: DatasetSnapshot) => <StatusBadge status={snap.status} size="sm" />,
          },
          {
            key: 'assertionsPassed',
            header: 'Quality Gate',
            render: (snap: DatasetSnapshot) => (
              <span className="text-xs font-mono text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {snap.assertionsPassed}
              </span>
            ),
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (snap: DatasetSnapshot) => (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedSnapshot(snap)}
                  className="px-2 py-1 text-[11px] font-mono font-semibold bg-purple-950/40 text-purple-300 hover:bg-purple-900/50 border border-purple-800/40 rounded transition-colors"
                  title="Inspect Schema & Distributions"
                >
                  Inspect Schema
                </button>

                {!snap.isBaseline && (
                  <button
                    onClick={() => handleSetBaseline(snap.id)}
                    className="px-2 py-1 text-[11px] font-mono font-semibold bg-emerald-950/30 text-emerald-300 hover:bg-emerald-900/40 border border-emerald-800/30 rounded transition-colors"
                    title="Set as Production Baseline"
                  >
                    Set Baseline
                  </button>
                )}
              </div>
            ),
          },
        ]}
        data={filteredSnapshots}
        keyExtractor={(snap: DatasetSnapshot) => snap.id}
      />

      {/* Schema Inspector Drawer / Modal */}
      {selectedSnapshot && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#101417] border-l border-[#252E3B] w-full max-w-2xl h-full rounded-2xl p-6 shadow-2xl overflow-y-auto space-y-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-[#252E3B]">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold font-mono text-white">{selectedSnapshot.versionTag}</h3>
                  <StatusBadge status={selectedSnapshot.status} size="sm" />
                </div>
                <p className="text-xs font-mono text-[#94a3b8] mt-1">{selectedSnapshot.name} • {selectedSnapshot.schemaHash}</p>
              </div>

              <button onClick={() => setSelectedSnapshot(null)} className="p-1 rounded-lg text-[#94a3b8] hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quality Assertions Summary Box */}
            <div className="bg-[#101417] border border-emerald-500/30 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Great Expectations Data Suite: PASSED
                </span>
                <span className="text-slate-300 font-semibold">{selectedSnapshot.assertionsPassed}</span>
              </div>
              <p className="text-[11px] font-mono text-[#94a3b8]">
                Schema enforcement, non-null guarantees, domain bound checks, and type validations passed with zero critical violations.
              </p>
            </div>

            {/* Schema Column Table */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold font-mono text-white flex items-center gap-2">
                <Table className="w-4 h-4 text-purple-400" />
                Feature Schema Definitions ({SAMPLE_SCHEMA_COLUMNS.length} Sample Columns)
              </h4>

              <div className="overflow-x-auto border border-[#252E3B] rounded-lg">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-[#252E3B] bg-[#101417] text-[#94a3b8]">
                      <th className="p-2.5">Feature Name</th>
                      <th className="p-2.5">Type</th>
                      <th className="p-2.5">Null %</th>
                      <th className="p-2.5">Min / Max</th>
                      <th className="p-2.5">Mean</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#252E3B] bg-[#101417]">
                    {SAMPLE_SCHEMA_COLUMNS.map((col) => (
                      <tr key={col.name} className="hover:bg-slate-900/50">
                        <td className="p-2.5 font-bold text-purple-300">{col.name}</td>
                        <td className="p-2.5 text-slate-300 text-[11px]">{col.type}</td>
                        <td className="p-2.5 text-slate-300">{(col.nullPercentage * 100).toFixed(1)}%</td>
                        <td className="p-2.5 text-slate-400 text-[11px]">{col.min} → {col.max}</td>
                        <td className="p-2.5 text-slate-300">{col.mean}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="pt-4 border-t border-[#252E3B] flex justify-between items-center text-xs font-mono">
              <span className="text-[#94a3b8]">Total Storage: {selectedSnapshot.storageSize}</span>
              <button
                onClick={() => {
                  alert(`Exporting sample CSV for ${selectedSnapshot.versionTag}...`);
                }}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download Sample CSV
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create New Snapshot Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#101417] border border-[#252E3B] rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
                <Database className="w-5 h-5 text-purple-400" />
                Create New Dataset Snapshot
              </h3>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-[#94a3b8] hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSnapshot} className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Version Tag</label>
                <input
                  type="text"
                  value={newVersionTag}
                  onChange={(e) => setNewVersionTag(e.target.value)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white focus:border-purple-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Snapshot Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white focus:border-purple-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Partition Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as any)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white focus:border-purple-500 outline-none"
                >
                  <option value="LIVE_INFERENCE">LIVE_INFERENCE</option>
                  <option value="REFERENCE_BASELINE">REFERENCE_BASELINE</option>
                  <option value="GOLDEN_EVALUATION">GOLDEN_EVALUATION</option>
                  <option value="CANARY_SPLIT">CANARY_SPLIT</option>
                </select>
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Estimated Records Count</label>
                <input
                  type="number"
                  value={newRecords}
                  onChange={(e) => setNewRecords(Number(e.target.value))}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white focus:border-purple-500 outline-none"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-[#252E3B]">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 bg-[#101417] border border-[#252E3B] text-[#94a3b8] hover:text-white rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg shadow-md"
                >
                  Create Snapshot
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
