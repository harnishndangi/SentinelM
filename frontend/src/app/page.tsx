'use client';

import { useEffect, useState } from 'react';
import { checkBackendHealth } from '@/services/api';
import { SystemHealth } from '@/types';
import { Activity, ShieldCheck, Cpu, Database, Server, Terminal, Zap, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function Home() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkBackendHealth()
      .then((data) => setHealth(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-[#090d16] text-slate-100 p-6 md:p-12">
      {/* Header Bar */}
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-8 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
              Sentinel<span className="text-cyan-400">ML</span>
            </h1>
            <p className="text-sm text-slate-400">
              Autonomous ML Reliability & Self-Healing Platform
            </p>
          </div>
        </div>

        {/* Backend Status Indicator Badge */}
        <div className="flex items-center gap-3 glass-panel px-4 py-2 rounded-xl border border-slate-800">
          <div className="text-xs text-slate-400 font-mono">Backend Status:</div>
          {loading ? (
            <div className="flex items-center gap-2 text-xs text-yellow-400">
              <Activity className="w-4 h-4 animate-spin" /> Checking...
            </div>
          ) : health?.status === 'healthy' ? (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> ONLINE ({health.service} v{health.version})
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs font-semibold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">
              <AlertTriangle className="w-4 h-4 text-rose-400" /> DISCONNECTED
            </div>
          )}
        </div>
      </header>

      {/* Main Grid Section */}
      <div className="max-w-7xl mx-auto mt-10 space-y-8">
        {/* Status Metrics Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <div className="flex justify-between items-center text-slate-400 mb-2">
              <span className="text-xs uppercase font-semibold tracking-wider">Active Models</span>
              <Cpu className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-white">0 Ready</div>
            <p className="text-xs text-slate-500 mt-1">Skeleton initialized</p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <div className="flex justify-between items-center text-slate-400 mb-2">
              <span className="text-xs uppercase font-semibold tracking-wider">Drift Detection</span>
              <Activity className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">KS / PSI Engines</div>
            <p className="text-xs text-slate-500 mt-1">Modules structured</p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <div className="flex justify-between items-center text-slate-400 mb-2">
              <span className="text-xs uppercase font-semibold tracking-wider">Database & Cache</span>
              <Database className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white">SQLAlchemy & Redis</div>
            <p className="text-xs text-slate-500 mt-1">Configured in app/config.py</p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <div className="flex justify-between items-center text-slate-400 mb-2">
              <span className="text-xs uppercase font-semibold tracking-wider">API Health</span>
              <Server className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">/api/v1/health</div>
            <p className="text-xs text-slate-500 mt-1">{health?.status || 'checking...'}</p>
          </div>
        </div>

        {/* Architecture & Verification Guide */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Architecture Modules Box */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-cyan-400" /> Monorepo Module Architecture
            </h2>
            <div className="space-y-3 text-sm text-slate-300">
              <div className="flex items-start gap-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="px-2 py-0.5 text-xs font-mono bg-cyan-500/20 text-cyan-300 rounded border border-cyan-500/30">backend/</span>
                <div>
                  <div className="font-medium text-slate-200">FastAPI Application</div>
                  <div className="text-xs text-slate-400">Structured logic, database ORM, Redis client, Pydantic configuration, & health routes.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="px-2 py-0.5 text-xs font-mono bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30">frontend/</span>
                <div>
                  <div className="font-medium text-slate-200">Next.js App Router</div>
                  <div className="text-xs text-slate-400">Tailwind CSS, TypeScript interfaces, and API service layer integration.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="px-2 py-0.5 text-xs font-mono bg-purple-500/20 text-purple-300 rounded border border-purple-500/30">ml/</span>
                <div>
                  <div className="font-medium text-slate-200">ML Engine Skeleton</div>
                  <div className="text-xs text-slate-400">Training, drift detection, preprocessing, evaluation, explainability & model definitions.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <span className="px-2 py-0.5 text-xs font-mono bg-amber-500/20 text-amber-300 rounded border border-amber-500/30">tests/</span>
                <div>
                  <div className="font-medium text-slate-200">Test Suite</div>
                  <div className="text-xs text-slate-400">Pytest unit and integration testing framework with TestClient fixtures.</div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Start Commands Box */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Terminal className="w-5 h-5 text-emerald-400" /> Platform Execution Commands
            </h2>

            <div className="space-y-4 text-xs font-mono">
              <div>
                <div className="text-slate-400 mb-1 font-sans text-xs">Backend Execution:</div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-cyan-300">
                  python -m uvicorn backend.app.main:app --reload --port 8000
                </div>
              </div>

              <div>
                <div className="text-slate-400 mb-1 font-sans text-xs">Frontend Execution:</div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-emerald-300">
                  cd frontend &amp;&amp; npm run dev
                </div>
              </div>

              <div>
                <div className="text-slate-400 mb-1 font-sans text-xs">Automated Pytest Verification:</div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-purple-300">
                  pytest tests/
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
