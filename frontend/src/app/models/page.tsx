'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Cpu, Plus, Search, Filter, ArrowUpRight, ShieldCheck, RotateCcw, Archive, Play, AlertOctagon } from 'lucide-react';
import { StatusBadge, ModelBadge, DataTable, AlertBanner } from '@/components/ui';
import { useSentinelStore } from '@/store/useSentinelStore';
import { apiClient } from '@/services/api';

export default function ModelsPage() {
  const store = useSentinelStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [algorithmFilter, setAlgorithmFilter] = useState('All');
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

  // Form state
  const [modelName, setModelName] = useState('FraudDetector');
  const [version, setVersion] = useState('v19');
  const [algorithm, setAlgorithm] = useState('LightGBM');
  const [datasetVersion, setDatasetVersion] = useState('ds_snapshot_20260815');
  const [prAuc, setPrAuc] = useState('0.965');
  const [recall, setRecall] = useState('94.5');
  const [f1Score, setF1Score] = useState('0.938');

  // Fetch registered models from backend with store fallback
  const { data: modelsList = [] } = useQuery({
    queryKey: ['modelsList'],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/models');
        if (Array.isArray(res.data) && res.data.length > 0) {
          return res.data;
        }
        return store.models;
      } catch (err) {
        return store.models;
      }
    },
  });

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    store.registerModel({
      name: modelName,
      version: version,
      algorithm: algorithm,
      status: 'CANDIDATE',
      prAuc: parseFloat(prAuc) || 0.95,
      recall: parseFloat(recall) || 94.0,
      f1Score: parseFloat(f1Score) || 0.93,
    });
    setIsRegisterModalOpen(false);
  };

  // Ensure extended mock attributes exist for table rendering
  const enrichedModels = modelsList.map((m: any, idx: number) => ({
    id: m.id || `m-${idx}`,
    name: m.name || 'FraudDetector',
    version: m.version || `v${16 + idx}`,
    algorithm: m.algorithm || 'XGBoost',
    status: m.status || (idx === 0 ? 'PRODUCTION' : idx === 1 ? 'CANDIDATE' : 'ARCHIVED'),
    datasetVersion: m.datasetVersion || `ds_v1.${idx}`,
    prAuc: m.prAuc ?? 0.94,
    recall: m.recall ? `${m.recall}%` : '93.2%',
    f1Score: m.f1Score ?? 0.91,
    createdAt: m.updatedAt || '2026-08-15 12:30',
  }));

  const filteredModels = enrichedModels.filter((m: any) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.version.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || m.status === statusFilter;
    const matchesAlgo = algorithmFilter === 'All' || m.algorithm === algorithmFilter;
    return matchesSearch && matchesStatus && matchesAlgo;
  });

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-slate-950 text-slate-100 w-full h-full space-y-6">
      {/* Top Title & Register Model Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold font-mono tracking-tight text-white">
              Registered Model Registry
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-purple-950/60 text-purple-300 border border-purple-800/40 font-semibold">
              {filteredModels.length} Versions Registered
            </span>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Manage model lineage, artifacts, production promotion, candidate benchmarks, and rollbacks.
          </p>
        </div>

        <button
          onClick={() => setIsRegisterModalOpen(true)}
          className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold font-mono text-xs rounded-xl shadow-lg flex items-center gap-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          Register New Model
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between shadow-md">
        <div className="flex items-center gap-3 flex-1 min-w-[240px] bg-slate-950 border border-slate-800 px-3.5 py-2 rounded-xl focus-within:border-purple-500 transition-colors">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by model name or version tag (e.g. v18)..."
            className="bg-transparent border-none outline-none text-xs font-mono text-slate-200 placeholder-slate-500 w-full focus:ring-0"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Statuses</option>
            <option value="PRODUCTION">PRODUCTION</option>
            <option value="CANDIDATE">CANDIDATE</option>
            <option value="STAGING">STAGING</option>
            <option value="ARCHIVED">ARCHIVED</option>
            <option value="FAILED">FAILED</option>
          </select>

          <select
            value={algorithmFilter}
            onChange={(e) => setAlgorithmFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="All">All Algorithms</option>
            <option value="XGBoost">XGBoost</option>
            <option value="LightGBM">LightGBM</option>
            <option value="RandomForest">RandomForest</option>
          </select>
        </div>
      </div>

      {/* Models Data Table */}
      <DataTable
        columns={[
          {
            key: 'name',
            header: 'Model Name',
            render: (row: any) => (
              <Link href={`/models/${row.id}`} className="group flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
                <span className="font-semibold text-white group-hover:text-purple-300 transition-colors">
                  {row.name}
                </span>
              </Link>
            ),
          },
          {
            key: 'version',
            header: 'Version',
            render: (row: any) => <ModelBadge modelName="" version={row.version} isActive={row.status === 'PRODUCTION'} />,
          },
          {
            key: 'algorithm',
            header: 'Algorithm',
            render: (row: any) => <span className="font-mono text-slate-300 font-medium">{row.algorithm}</span>,
          },
          {
            key: 'status',
            header: 'Status',
            render: (row: any) => <StatusBadge status={row.status} size="sm" />,
          },
          {
            key: 'datasetVersion',
            header: 'Dataset Version',
            render: (row: any) => (
              <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {row.datasetVersion}
              </span>
            ),
          },
          {
            key: 'prAuc',
            header: 'PR-AUC',
            render: (row: any) => (
              <span className="font-mono font-bold text-purple-300">
                {typeof row.prAuc === 'number' ? row.prAuc.toFixed(3) : row.prAuc}
              </span>
            ),
          },
          {
            key: 'recall',
            header: 'Recall',
            render: (row: any) => <span className="font-mono text-slate-200">{row.recall}</span>,
          },
          {
            key: 'f1Score',
            header: 'F1 Score',
            render: (row: any) => (
              <span className="font-mono text-slate-200">
                {typeof row.f1Score === 'number' ? row.f1Score.toFixed(3) : row.f1Score}
              </span>
            ),
          },
          {
            key: 'createdAt',
            header: 'Created At',
            render: (row: any) => <span className="text-slate-400 text-xs font-mono">{row.createdAt}</span>,
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (row: any) => (
              <div className="flex items-center gap-2">
                <Link
                  href={`/models/${row.id}`}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-purple-900/50 text-slate-300 hover:text-purple-300 transition-colors"
                  title="View Model Details"
                >
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
                {row.status === 'CANDIDATE' && (
                  <button
                    onClick={() => store.promoteModel(row.id)}
                    className="px-2 py-1 text-[11px] font-mono font-semibold bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30 rounded transition-colors"
                    title="Promote to Production"
                  >
                    Promote
                  </button>
                )}
                {row.status === 'PRODUCTION' && (
                  <button
                    onClick={() => store.rollbackModel(row.id)}
                    className="px-2 py-1 text-[11px] font-mono font-semibold bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 rounded transition-colors"
                    title="Rollback Model"
                  >
                    Rollback
                  </button>
                )}
              </div>
            ),
          },
        ]}
        data={filteredModels}
        keyExtractor={(row: any) => row.id}
      />

      {/* Register Model Modal */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white font-mono">Register New Model Version</h3>
            <form onSubmit={handleRegisterSubmit} className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Model Name</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Version Tag</label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Algorithm</label>
                <select
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                >
                  <option value="LightGBM">LightGBM</option>
                  <option value="XGBoost">XGBoost</option>
                  <option value="RandomForest">RandomForest</option>
                  <option value="CatBoost">CatBoost</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">PR-AUC Score</label>
                  <input
                    type="text"
                    value={prAuc}
                    onChange={(e) => setPrAuc(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Recall (%)</label>
                  <input
                    type="text"
                    value={recall}
                    onChange={(e) => setRecall(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsRegisterModalOpen(false)}
                  className="px-4 py-2 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl"
                >
                  Register Model
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
