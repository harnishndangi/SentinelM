'use client';

import React, { useState } from 'react';
import { Zap, X, AlertTriangle, Loader2 } from 'lucide-react';
import { apiClient } from '@/services/api';
import { useSentinelStore } from '@/store/useSentinelStore';

interface InjectDriftModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (details: any) => void;
}

export const InjectDriftModal: React.FC<InjectDriftModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [scenario, setScenario] = useState<string>('MULTI_FEATURE_DRIFT');
  const [intensity, setIntensity] = useState<number>(0.85);
  const [numRecords, setNumRecords] = useState<number>(2000);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const injectStoreDrift = useSentinelStore((state) => state.injectDrift);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      // Call backend API endpoint to simulate and inject real drift
      const response = await apiClient.post('/simulator/scenario', {
        scenario,
        intensity,
        num_records: numRecords,
      });

      // Update Zustand store
      injectStoreDrift(scenario);

      if (onSuccess) {
        onSuccess(response.data || { scenario, intensity, numRecords });
      }
      onClose();
    } catch (err: any) {
      console.warn('Backend API error on drift injection, applying store fallback:', err);
      // Fallback: update store locally
      injectStoreDrift(scenario);
      if (onSuccess) {
        onSuccess({ scenario, intensity, numRecords, status: 'fallback_applied' });
      }
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2 text-amber-400">
            <Zap className="w-5 h-5 fill-amber-400/20" />
            <h3 className="text-lg font-bold text-slate-100">Inject Synthetic Data Drift</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Warning Banner */}
        <div className="my-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
          <div>
            <p className="font-semibold">Simulate Real Production Anomalies</p>
            <p className="opacity-90 font-mono text-[11px] mt-0.5">
              This triggers statistical feature distribution shift in the DriftEngine and executes background Celery workers.
            </p>
          </div>
        </div>

        {/* Form Inputs */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5 uppercase tracking-wider">
              Drift Scenario
            </label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm font-mono text-slate-200 focus:outline-none focus:border-amber-400 transition-colors"
            >
              <option value="MULTI_FEATURE_DRIFT">Multi-Feature Covariate Shift</option>
              <option value="HIGH_TRANSACTION_AMOUNT">High Transaction Amount Spike</option>
              <option value="MOBILE_DEVICE_SHIFT">Mobile OS & Device Type Shift</option>
              <option value="CONCEPT_DRIFT">Abrupt Concept & Label Drift</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-mono text-slate-300 uppercase tracking-wider">
                Drift Intensity Level
              </label>
              <span className="text-xs font-mono font-bold text-amber-400">
                {(intensity * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={intensity}
              onChange={(e) => setIntensity(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
              <span>Mild (10%)</span>
              <span>Moderate (50%)</span>
              <span>Severe (100%)</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5 uppercase tracking-wider">
              Number of Synthetic Records
            </label>
            <input
              type="number"
              min="100"
              max="10000"
              step="100"
              value={numRecords}
              onChange={(e) => setNumRecords(parseInt(e.target.value) || 1000)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-sm font-mono text-slate-200 focus:outline-none focus:border-amber-400 transition-colors"
            />
          </div>

          {errorMsg && (
            <p className="text-xs text-rose-400 font-mono bg-rose-950/30 p-2 rounded border border-rose-500/30">
              {errorMsg}
            </p>
          )}

          {/* Action Buttons */}
          <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-mono text-slate-400 hover:text-slate-200 rounded-xl hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 font-bold font-mono text-xs rounded-xl shadow-lg flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Injecting Drift...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 fill-slate-950" />
                  INJECT DRIFT NOW
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InjectDriftModal;
