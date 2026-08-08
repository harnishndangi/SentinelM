'use client';

import { useState } from 'react';
import { useSentinelStore } from '@/store/useSentinelStore';

export default function ModelsPage() {
  const { models, promoteModel, rollbackModel, archiveModel, registerModel } = useSentinelStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [algorithmFilter, setAlgorithmFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

  // Form state for Register Model
  const [newModelName, setNewModelName] = useState('FraudDetector');
  const [newModelVersion, setNewModelVersion] = useState('v19');
  const [newModelAlgorithm, setNewModelAlgorithm] = useState('LightGBM');
  const [newModelPrAuc, setNewModelPrAuc] = useState('0.97');
  const [newModelStatus, setNewModelStatus] = useState<'CANDIDATE' | 'PRODUCTION'>('CANDIDATE');

  // Filter models list
  const filteredModels = models.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.version.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAlgo = algorithmFilter === 'All' || m.algorithm === algorithmFilter;
    const matchesStatus = statusFilter === 'All' || m.status === statusFilter;
    return matchesSearch && matchesAlgo && matchesStatus;
  });

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    registerModel({
      name: newModelName,
      version: newModelVersion,
      algorithm: newModelAlgorithm,
      status: newModelStatus,
      prAuc: parseFloat(newModelPrAuc) || 0.95,
      f1Score: 0.92,
      recall: 94.0,
    });
    setIsRegisterModalOpen(false);
  };

  const toggleMenu = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setActiveMenuId((prev) => (prev === id ? null : id));
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-xl gap-md">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Models</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Manage trained models, versions, metrics and production state.
          </p>
        </div>
        <button
          onClick={() => setIsRegisterModalOpen(true)}
          className="bg-primary text-on-primary px-lg py-sm rounded-DEFAULT text-mono-label font-mono-label hover:bg-primary-fixed transition-colors flex items-center gap-sm shadow-[0px_4px_20px_rgba(208,188,255,0.1)]"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          Register Model
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-surface-container-low border border-outline-variant rounded-lg p-md mb-lg flex flex-wrap gap-md items-center">
        <div className="flex items-center gap-sm bg-surface-dim px-md py-sm rounded-DEFAULT border border-outline-variant flex-1 min-w-[200px]">
          <span className="material-symbols-outlined text-on-surface-variant text-sm">filter_list</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter models by name or version..."
            className="bg-transparent border-none outline-none text-body-md font-body-md text-on-surface placeholder-on-surface-variant w-full focus:ring-0"
          />
        </div>

        <select
          value={algorithmFilter}
          onChange={(e) => setAlgorithmFilter(e.target.value)}
          className="bg-surface-dim border border-outline-variant rounded-DEFAULT text-body-md font-body-md text-on-surface px-md py-sm focus:ring-primary focus:border-primary"
        >
          <option value="All">All Algorithms</option>
          <option value="XGBoost">XGBoost</option>
          <option value="LightGBM">LightGBM</option>
          <option value="RandomForest">RandomForest</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surface-dim border border-outline-variant rounded-DEFAULT text-body-md font-body-md text-on-surface px-md py-sm focus:ring-primary focus:border-primary"
        >
          <option value="All">All Statuses</option>
          <option value="PRODUCTION">PRODUCTION</option>
          <option value="CANDIDATE">CANDIDATE</option>
          <option value="ARCHIVED">ARCHIVED</option>
        </select>

        <button
          onClick={() => {
            setSearchQuery('');
            setAlgorithmFilter('All');
            setStatusFilter('All');
          }}
          className="text-on-surface-variant hover:text-on-surface px-md py-sm rounded-DEFAULT border border-transparent hover:bg-surface-container transition-colors text-mono-label font-mono-label"
        >
          Clear Filters
        </button>
      </div>

      {/* Models Table */}
      <div className="bg-surface border border-outline-variant rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low text-mono-table font-mono-table text-on-surface-variant">
                <th className="table-cell-padding font-medium">MODEL</th>
                <th className="table-cell-padding font-medium">VERSION</th>
                <th className="table-cell-padding font-medium">ALGORITHM</th>
                <th className="table-cell-padding font-medium">STATUS</th>
                <th className="table-cell-padding font-medium text-right">PR-AUC</th>
                <th className="table-cell-padding font-medium text-center w-12"></th>
              </tr>
            </thead>
            <tbody className="text-body-md font-body-md divide-y divide-outline-variant">
              {filteredModels.map((m) => (
                <tr
                  key={m.id}
                  className={`hover:bg-surface-container transition-colors group ${
                    m.status === 'ARCHIVED' ? 'opacity-70 hover:opacity-100' : ''
                  }`}
                >
                  <td className="table-cell-padding text-on-surface font-medium flex items-center gap-sm">
                    <span className="material-symbols-outlined text-on-surface-variant text-sm">deployed_code</span>
                    {m.name}
                  </td>
                  <td className="table-cell-padding text-mono-table font-mono-table text-on-surface-variant">
                    {m.version}
                  </td>
                  <td className="table-cell-padding text-on-surface-variant">{m.algorithm}</td>
                  <td className="table-cell-padding">
                    {m.status === 'PRODUCTION' && (
                      <span className="inline-flex items-center px-sm py-xs rounded-full text-mono-table font-mono-table bg-green-500/10 text-green-400 border border-green-500/20">
                        PRODUCTION
                      </span>
                    )}
                    {m.status === 'CANDIDATE' && (
                      <span className="inline-flex items-center px-sm py-xs rounded-full text-mono-table font-mono-table bg-primary/10 text-primary border border-primary/20">
                        CANDIDATE
                      </span>
                    )}
                    {m.status === 'ARCHIVED' && (
                      <span className="inline-flex items-center px-sm py-xs rounded-full text-mono-table font-mono-table bg-surface-variant text-on-surface-variant border border-outline-variant">
                        ARCHIVED
                      </span>
                    )}
                  </td>
                  <td className="table-cell-padding text-mono-metric font-mono-metric text-on-surface text-right">
                    {m.prAuc}
                  </td>
                  <td className="table-cell-padding text-center relative">
                    <button
                      onClick={(e) => toggleMenu(m.id, e)}
                      className="text-on-surface-variant hover:text-primary p-xs rounded-DEFAULT opacity-80 group-hover:opacity-100 transition-opacity"
                    >
                      <span className="material-symbols-outlined">more_vert</span>
                    </button>

                    {/* Action Dropdown Menu */}
                    {activeMenuId === m.id && (
                      <div className="absolute right-md top-10 w-48 bg-surface-container-high border border-outline-variant rounded-DEFAULT shadow-[0px_4px_20px_rgba(0,0,0,0.5)] z-20 py-sm text-left">
                        <button
                          onClick={() => {
                            alert(`Details for ${m.name} ${m.version}:\nFramework: ${m.algorithm}\nPR-AUC: ${m.prAuc}\nRecall: ${m.recall || 90}%`);
                            setActiveMenuId(null);
                          }}
                          className="w-full text-left px-md py-sm text-body-sm font-body-sm text-on-surface hover:bg-surface-container block"
                        >
                          View Details
                        </button>
                        {m.status === 'CANDIDATE' && (
                          <button
                            onClick={() => {
                              promoteModel(m.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-md py-sm text-body-sm font-body-sm text-primary font-semibold hover:bg-surface-container block"
                          >
                            Promote to Production
                          </button>
                        )}
                        {m.status === 'PRODUCTION' && (
                          <button
                            onClick={() => {
                              rollbackModel(m.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-md py-sm text-body-sm font-body-sm text-status-warning-text hover:bg-surface-container block"
                          >
                            Rollback Model
                          </button>
                        )}
                        {m.status !== 'ARCHIVED' && (
                          <button
                            onClick={() => {
                              archiveModel(m.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-md py-sm text-body-sm font-body-sm text-status-error-text hover:bg-surface-container block"
                          >
                            Archive Version
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Table Footer Pagination */}
        <div className="border-t border-outline-variant p-md flex items-center justify-between text-body-sm font-body-sm text-on-surface-variant bg-surface-container-low">
          <span>Showing 1-{filteredModels.length} of {models.length} registered models</span>
          <div className="flex items-center gap-sm">
            <button className="p-xs rounded-DEFAULT hover:bg-surface-container hover:text-on-surface transition-colors disabled:opacity-50" disabled>
              <span className="material-symbols-outlined text-sm">chevron_left</span>
            </button>
            <span className="px-sm">Page 1 of 1</span>
            <button className="p-xs rounded-DEFAULT hover:bg-surface-container hover:text-on-surface transition-colors">
              <span className="material-symbols-outlined text-sm">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      {/* Register Model Modal */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-high border border-outline-variant rounded-xl p-lg max-w-lg w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-outline-variant">
              <h3 className="text-display-md text-[20px] text-on-surface font-semibold flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">add_box</span>
                Register New Model Version
              </h3>
              <button onClick={() => setIsRegisterModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                ✕
              </button>
            </div>
            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              <div>
                <label className="block text-mono-label text-body-sm text-on-surface mb-1">Model Name</label>
                <input
                  type="text"
                  value={newModelName}
                  onChange={(e) => setNewModelName(e.target.value)}
                  className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-mono-label text-body-sm text-on-surface mb-1">Version</label>
                  <input
                    type="text"
                    value={newModelVersion}
                    onChange={(e) => setNewModelVersion(e.target.value)}
                    className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
                    placeholder="e.g. v19"
                    required
                  />
                </div>

                <div>
                  <label className="block text-mono-label text-body-sm text-on-surface mb-1">Algorithm</label>
                  <select
                    value={newModelAlgorithm}
                    onChange={(e) => setNewModelAlgorithm(e.target.value)}
                    className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
                  >
                    <option value="XGBoost">XGBoost</option>
                    <option value="LightGBM">LightGBM</option>
                    <option value="CatBoost">CatBoost</option>
                    <option value="RandomForest">RandomForest</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-mono-label text-body-sm text-on-surface mb-1">PR-AUC Target</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newModelPrAuc}
                    onChange={(e) => setNewModelPrAuc(e.target.value)}
                    className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
                    required
                  />
                </div>

                <div>
                  <label className="block text-mono-label text-body-sm text-on-surface mb-1">Initial Status</label>
                  <select
                    value={newModelStatus}
                    onChange={(e) => setNewModelStatus(e.target.value as any)}
                    className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
                  >
                    <option value="CANDIDATE">CANDIDATE</option>
                    <option value="PRODUCTION">PRODUCTION</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-outline-variant">
                <button
                  type="button"
                  onClick={() => setIsRegisterModalOpen(false)}
                  className="px-4 py-2 rounded text-on-surface-variant hover:bg-surface-container font-mono-label"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-primary text-on-primary font-mono-label font-bold px-4 py-2 rounded hover:bg-primary-fixed transition-colors"
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
