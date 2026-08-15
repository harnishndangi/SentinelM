'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  Shield,
  ArrowRight,
  Terminal,
  Copy,
  Check,
  CheckCircle2,
  ExternalLink,
  Activity,
  Zap,
  RotateCcw,
  Star,
  Lock,
  Cloud,
  Cpu,
  Layers,
  Sparkles,
  Sliders,
  ChevronRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

const TICKER_TEXTS = [
  "SentinelML v2.4 Released: Autonomous Concept Drift Engine & DVC 3.0 Integration →",
  "Real-time Self-Healing: Retraining Worker #3 Active",
  "Zero SLA Breach: 99.98% Prediction Accuracy Maintained",
  "New Integration: DVC 3.0 & MLflow Support",
];

const HERO_CHART_DATA = [
  { time: '01', precision: 0.95, recall: 0.92, prAuc: 0.97 },
  { time: '02', precision: 0.96, recall: 0.93, prAuc: 0.96 },
  { time: '03', precision: 0.94, recall: 0.91, prAuc: 0.95 },
  { time: '04', precision: 0.97, recall: 0.94, prAuc: 0.98 },
  { time: '05', precision: 0.95, recall: 0.93, prAuc: 0.96 },
  { time: '06', precision: 0.98, recall: 0.95, prAuc: 0.98 },
  { time: '07', precision: 0.96, recall: 0.92, prAuc: 0.97 },
  { time: '08', precision: 0.97, recall: 0.94, prAuc: 0.98 },
  { time: '09', precision: 0.95, recall: 0.93, prAuc: 0.96 },
  { time: '10', precision: 0.98, recall: 0.95, prAuc: 0.99 },
];

export default function LandingPage() {
  // Ticker animation state
  const [tickerIndex, setTickerIndex] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % TICKER_TEXTS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Copy command state
  const [copied, setCopied] = useState(false);
  const handleCopyCommand = () => {
    navigator.clipboard.writeText('pip install sentinel-ml');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Comparison slider interactive state
  const [sliderPercentage, setSliderPercentage] = useState(50);
  const sliderRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);

  const handleSliderMove = (clientX: number) => {
    if (!sliderRef.current) return;
    const rect = sliderRef.current.getBoundingClientRect();
    let percentage = ((clientX - rect.left) / rect.width) * 100;
    percentage = Math.max(0, Math.min(100, percentage));
    setSliderPercentage(percentage);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    handleSliderMove(e.clientX);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDraggingRef.current) {
      handleSliderMove(e.clientX);
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length > 0) {
      handleSliderMove(e.touches[0].clientX);
    }
  };

  return (
    <div
      className="bg-[#0B0E14] text-[#E2E8F0] font-sans antialiased min-h-screen selection:bg-purple-500 selection:text-white"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 flex items-center justify-between bg-[#0B0E14]/80 backdrop-blur-md border-b border-[#232D3F]">
        <div className="flex items-center space-x-8">
          <Link href="/" className="flex items-center space-x-2 group">
            <Shield className="w-6 h-6 text-[#A855F7] group-hover:scale-110 transition-transform" />
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-[#A855F7] to-[#10B981] bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(168,85,247,0.5)]">
              SentinelML
            </span>
          </Link>
          <div className="hidden md:flex items-center space-x-6 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">
              Features
            </a>
            <a href="#architecture" className="hover:text-white transition-colors">
              Architecture
            </a>
            <a href="#demo" className="hover:text-white transition-colors">
              Demo
            </a>
            <a href="#docs" className="hover:text-white transition-colors">
              Docs
            </a>
            <a
              href="https://github.com/harnishndangi/sentinal-ai"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors flex items-center space-x-1.5"
            >
              <span>GitHub</span>
              <span className="bg-white/10 px-1.5 py-0.5 rounded text-xs text-amber-300 font-mono">
                ★ 4.8k
              </span>
            </a>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <Link
            href="/dashboard"
            className="hidden md:block text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/dashboard"
            className="bg-gradient-to-r from-[#A855F7] to-[#10B981] hover:opacity-90 text-white px-5 py-2.5 rounded-lg text-sm font-bold transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(168,85,247,0.4)] flex items-center gap-2"
          >
            <span>Launch Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="pt-32 pb-20 px-6 relative min-h-[900px] flex flex-col justify-center bg-[radial-gradient(#232D3F_1px,transparent_1px)] [background-size:40px_40px]">
        {/* Radial Glow Overlays */}
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-[#A855F7]/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-[#10B981]/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 items-center relative z-10">
          <div className="space-y-8">
            <div className="flex items-center space-x-3 text-[10px] font-mono text-slate-400 uppercase tracking-[0.2em]">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#A855F7] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#A855F7]" />
              </span>
              <span className="font-bold border-r-2 border-[#A855F7] pr-1.5 text-slate-200">
                {TICKER_TEXTS[tickerIndex]}
              </span>
            </div>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[0.95] tracking-tight text-white">
              Autonomous
              <br />
              ML Reliability
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#A855F7] via-purple-400 to-[#10B981] drop-shadow-[0_0_30px_rgba(168,85,247,0.3)]">
                AI Engine
              </span>
            </h1>
            <p className="text-lg text-slate-400 max-w-xl leading-relaxed">
              Stop silent model degradation. SentinelML continuously monitors production features, detects data drift in milliseconds, and automatically retrains & hot-swaps degraded models before SLAs fail.
            </p>

            <div className="flex flex-wrap items-center gap-4">
              <Link
                href="/dashboard"
                className="bg-gradient-to-r from-[#A855F7] to-[#10B981] text-white px-6 py-3.5 rounded-lg font-medium hover:opacity-90 transition-all flex items-center space-x-2 shadow-[0_0_20px_rgba(16,185,129,0.3)]"
              >
                <span>Launch Live Sandbox</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              {/* Pip Install Command Box */}
              <div className="flex items-center space-x-3 bg-[#131822] border border-[#232D3F] rounded-lg p-1.5 pl-4 font-mono text-sm text-slate-300">
                <span className="text-[#10B981] font-bold">$</span>
                <span>pip install sentinel-ml</span>
                <button
                  onClick={handleCopyCommand}
                  className="bg-white/5 hover:bg-white/10 p-2 rounded transition-colors text-slate-300 hover:text-white"
                  title="Copy command"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* Hero Widget: Live Telemetry Dashboard */}
          <div className="relative">
            <div className="bg-[#131822]/80 backdrop-blur-xl border border-[#232D3F] rounded-2xl p-6 shadow-2xl relative z-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex flex-col">
                  <h3 className="font-bold text-lg text-white">FraudDetector-v2.4</h3>
                  <div className="text-[10px] font-mono text-slate-500 uppercase">
                    Production Cluster: us-east-1
                  </div>
                </div>
                <div className="flex items-center space-x-2 px-3 py-1 bg-[#10B981]/10 border border-[#10B981]/20 rounded-full text-xs text-[#10B981]">
                  <span className="w-1.5 h-1.5 bg-[#10B981] rounded-full animate-pulse" />
                  <span className="font-bold">HEALTHY 98.4%</span>
                </div>
              </div>

              {/* Recharts Hero Chart */}
              <div className="h-48 bg-[#0B0E14]/50 rounded-xl mb-6 relative overflow-hidden border border-[#232D3F] p-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={HERO_CHART_DATA}>
                    <defs>
                      <linearGradient id="heroGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#A855F7" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#A855F7" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0.85, 1.05]} hide />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0B0E14',
                        borderColor: '#232D3F',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="precision"
                      stroke="#A855F7"
                      fill="url(#heroGradient)"
                      strokeWidth={2}
                    />
                    <Line type="monotone" dataKey="recall" stroke="#10B981" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="prAuc" stroke="#F59E0B" strokeWidth={1} strokeDasharray="3 3" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
                <div className="absolute top-2 right-2 bg-[#0B0E14]/80 backdrop-blur px-2 py-1 rounded text-[10px] font-mono text-slate-400 border border-[#232D3F]">
                  Precision / Recall / PR-AUC
                </div>
              </div>

              {/* Telemetry Readouts */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0B0E14] rounded-lg p-4 border border-[#232D3F] relative overflow-hidden">
                  <div className="text-[10px] font-mono text-slate-500 uppercase mb-1">
                    KS-Test Drift
                  </div>
                  <div className="text-2xl font-bold text-[#F59E0B] font-mono">0.04</div>
                  <div className="mt-2 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#F59E0B] w-[15%] shadow-[0_0_10px_#F59E0B]" />
                  </div>
                </div>
                <div className="bg-[#0B0E14] rounded-lg p-4 border border-[#232D3F] relative overflow-hidden">
                  <div className="text-[10px] font-mono text-slate-500 uppercase mb-1">
                    PSI Index
                  </div>
                  <div className="text-2xl font-bold text-[#10B981] font-mono">0.08</div>
                  <div className="mt-2 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#10B981] w-[20%] shadow-[0_0_10px_#10B981]" />
                  </div>
                </div>
              </div>

              {/* System Event Stream */}
              <div className="mt-4 bg-black/40 rounded-lg p-3 border border-[#232D3F] font-mono text-[10px] h-28 overflow-hidden">
                <div className="flex justify-between text-slate-600 mb-2 border-b border-[#232D3F] pb-1">
                  <span>SYSTEM EVENT LOG</span>
                  <span className="text-emerald-400 animate-pulse">REC ●</span>
                </div>
                <div className="text-[#10B981] mb-1">04:11:45 AM - Checking threshold drift: OK (0.04)</div>
                <div className="text-[#F59E0B] mb-1">04:12:01 AM - Concept Drift Detected in `transaction_amount`</div>
                <div className="text-slate-200 mb-1">04:12:02 AM - Retraining Worker #3 Triggered (via DVC/MLflow)</div>
                <div className="text-[#10B981] opacity-70">04:12:05 AM - Syncing weights to production cluster...</div>
              </div>
            </div>

            {/* Ambient Glow */}
            <div className="absolute -inset-10 bg-[#A855F7]/20 rounded-full blur-[100px] -z-10" />
          </div>
        </div>
      </main>

      {/* Trust Band */}
      <section className="py-20 px-6 border-t border-[#232D3F] bg-[#131822]">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
            <div>
              <div className="text-5xl font-bold tracking-tight text-white font-mono">99.99%</div>
              <div className="text-xs text-slate-500 mt-2 uppercase tracking-widest font-mono">Uptime SLA</div>
            </div>
            <div>
              <div className="text-5xl font-bold tracking-tight text-white font-mono">&lt;50ms</div>
              <div className="text-xs text-slate-500 mt-2 uppercase tracking-widest font-mono">Drift Latency</div>
            </div>
            <div>
              <div className="text-5xl font-bold tracking-tight text-white font-mono">10x</div>
              <div className="text-xs text-slate-500 mt-2 uppercase tracking-widest font-mono">MTTR Speedup</div>
            </div>
            <div>
              <div className="text-5xl font-bold tracking-tight text-white font-mono">5M+</div>
              <div className="text-xs text-slate-500 mt-2 uppercase tracking-widest font-mono">Daily Inferences</div>
            </div>
          </div>

          <div className="flex flex-wrap justify-center items-center gap-12 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
            <img
              src="https://storage.googleapis.com/uxpilot-dev.appspot.com/default-org-id-2/91e93f07-4c1b-403d-975a-706229658199/1759152047298.png"
              alt="Client Logo 1"
              className="h-8 object-contain"
            />
            <img
              src="https://storage.googleapis.com/uxpilot-dev.appspot.com/default-org-id-2/91e93f07-4c1b-403d-975a-706229658199/1759152047299.png"
              alt="Client Logo 2"
              className="h-8 object-contain"
            />
            <img
              src="https://storage.googleapis.com/uxpilot-dev.appspot.com/default-org-id-2/91e93f07-4c1b-403d-975a-706229658199/1759152047300.png"
              alt="Client Logo 3"
              className="h-8 object-contain"
            />
            <img
              src="https://storage.googleapis.com/uxpilot-dev.appspot.com/default-org-id-2/91e93f07-4c1b-403d-975a-706229658199/1759152047301.png"
              alt="Client Logo 4"
              className="h-8 object-contain"
            />
            <img
              src="https://storage.googleapis.com/uxpilot-dev.appspot.com/default-org-id-2/91e93f07-4c1b-403d-975a-706229658199/1759152047302.png"
              alt="Client Logo 5"
              className="h-8 object-contain"
            />
          </div>
        </div>
      </section>

      {/* Core Architecture Grid */}
      <section id="features" className="py-24 px-6 border-t border-[#232D3F]">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <h2 className="text-4xl font-bold tracking-tight text-white mb-4">
              The 4 Pillars of
              <br />
              Autonomous Reliability
            </h2>
            <p className="text-slate-400 max-w-2xl text-base">
              A closed-loop system that observes, diagnoses, and repairs your ML infrastructure without human intervention.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="group cursor-pointer">
              <div className="h-64 rounded-2xl overflow-hidden mb-4 bg-[#131822] border border-[#232D3F]">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 group-hover:scale-105"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_f9a1d1f37d_90e18a71d7d75d8a.png"
                  alt="Real-time Drift Engine"
                />
              </div>
              <h3 className="font-bold text-lg text-white mb-2">Real-Time Drift Engine</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Statistical KS-tests and PSI monitors running at inference speed.
              </p>
            </div>

            <div className="group cursor-pointer">
              <div className="h-64 rounded-2xl overflow-hidden mb-4 bg-[#131822] border border-[#232D3F]">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 group-hover:scale-105"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_2f0c10a19b_42ca58fc8ef32323.png"
                  alt="Self-Healing Pipelines"
                />
              </div>
              <h3 className="font-bold text-lg text-white mb-2">Self-Healing Pipelines</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Automated rollback and retraining triggered by anomaly thresholds.
              </p>
            </div>

            <div className="group cursor-pointer">
              <div className="h-64 rounded-2xl overflow-hidden mb-4 bg-[#131822] border border-[#232D3F]">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 group-hover:scale-105"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_8ee26f2f1b_d99357250d05d778.png"
                  alt="Root Cause Analysis"
                />
              </div>
              <h3 className="font-bold text-lg text-white mb-2">Root Cause Analysis</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Feature-attribution pinpoints exactly which input caused degradation.
              </p>
            </div>

            <div className="group cursor-pointer">
              <div className="h-64 rounded-2xl overflow-hidden mb-4 bg-[#131822] border border-[#232D3F]">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500 group-hover:scale-105"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_2f936216c4_bbf06d6d41d24cb3.png"
                  alt="Zero-Downtime Hot-Swapping"
                />
              </div>
              <h3 className="font-bold text-lg text-white mb-2">Zero-Downtime Hot-Swapping</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Seamless model promotion with canary validation and shadow traffic.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Before vs After Comparison */}
      <section id="demo" className="py-24 px-6 bg-[#131822] border-y border-[#232D3F]">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <h2 className="text-4xl font-bold tracking-tight text-white">
                From Silent Failure
                <br />
                to <span className="text-[#A855F7]">Automated Recovery</span>
              </h2>
              <p className="text-slate-400 leading-relaxed text-base">
                Without SentinelML, a drifting model degrades silently until customers notice. With it, the same event triggers instant detection, diagnosis, and a fresh model deployment—all before a single user is impacted.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-[#10B981] mt-0.5 shrink-0" />
                  <span className="text-sm text-slate-300">Detect concept drift within seconds of occurrence</span>
                </li>
                <li className="flex items-start space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-[#10B981] mt-0.5 shrink-0" />
                  <span className="text-sm text-slate-300">Auto-trigger retraining pipelines on degraded metrics</span>
                </li>
                <li className="flex items-start space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-[#10B981] mt-0.5 shrink-0" />
                  <span className="text-sm text-slate-300">Roll back to last known-good model if validation fails</span>
                </li>
              </ul>
            </div>

            {/* Interactive Before vs After Slider */}
            <div className="relative">
              <div
                ref={sliderRef}
                onMouseDown={handleMouseDown}
                onTouchMove={handleTouchMove}
                className="relative h-[400px] bg-[#0B0E14] rounded-xl border border-[#232D3F] overflow-hidden select-none cursor-ew-resize"
              >
                {/* WITHOUT SENTINEL IMAGE */}
                <div className="absolute inset-0">
                  <img
                    className="w-full h-full object-cover"
                    src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_20dace3303_343ae31ee89b4a81.png"
                    alt="Without SentinelML"
                  />
                </div>

                {/* WITH SENTINEL OVERLAY */}
                <div
                  className="absolute inset-0 overflow-hidden border-r border-white/30"
                  style={{ width: `${sliderPercentage}%` }}
                >
                  <img
                    className="w-full h-full object-cover"
                    src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_128d81122e_754ced87117d97a3.png"
                    alt="With SentinelML"
                  />
                </div>

                <div className="absolute top-4 left-4 bg-rose-600 text-white px-3 py-1 rounded text-[10px] font-bold shadow-lg">
                  WITHOUT SENTINEL
                </div>
                <div className="absolute top-4 right-4 bg-emerald-600 text-white px-3 py-1 rounded text-[10px] font-bold shadow-lg">
                  WITH SENTINEL
                </div>

                {/* SLIDER HANDLE */}
                <div
                  className="absolute top-0 bottom-0 w-1 bg-white z-20"
                  style={{ left: `${sliderPercentage}%` }}
                >
                  <div className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-[#0B0E14] border-2 border-white rounded-full flex items-center justify-center text-white shadow-xl">
                    <Sliders className="w-4 h-4 text-white" />
                  </div>
                </div>
              </div>

              <div className="mt-4 flex justify-between text-xs text-slate-400 font-mono">
                <span>Accuracy collapse (silent)</span>
                <span className="text-[#10B981]">Auto-recovered in &lt; 500ms</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Implementation Code Section */}
      <section id="docs" className="py-24 px-6 border-b border-[#232D3F]">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <div className="order-2 lg:order-1 relative">
            <div className="bg-[#131822] border border-[#232D3F] rounded-2xl p-8 font-mono text-sm overflow-x-auto shadow-2xl">
              <div className="flex items-center justify-between mb-6 border-b border-[#232D3F] pb-4">
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-3 rounded-full bg-rose-500/50" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/50" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/50" />
                  <span className="ml-2 text-xs text-slate-500">production_monitoring.py</span>
                </div>
                <Check className="text-[#10B981] w-4 h-4" />
              </div>
              <pre className="text-slate-300 leading-relaxed">
                <code>
                  <span className="text-[#A855F7]">from</span> sentinel_ml{' '}
                  <span className="text-[#A855F7]">import</span>{' '}
                  <span className="text-[#10B981]">SentinelMonitor</span>
                  {'\n\n'}
                  <span className="text-slate-500"># Autonomous watchdog for fraud model</span>
                  {'\n'}
                  monitor = <span className="text-[#10B981]">SentinelMonitor</span>({'\n'}
                  {'  '}model_id=<span className="text-[#F59E0B]">&quot;fraud-classifier-v2&quot;</span>,{'\n'}
                  {'  '}env=<span className="text-[#F59E0B]">&quot;production&quot;</span>
                  {'\n'}){'\n\n'}
                  <span className="text-slate-500"># Log predictions &amp; features</span>
                  {'\n'}
                  monitor.<span className="text-[#A855F7]">log_prediction</span>({'\n'}
                  {'  '}features=inputs,{'\n'}
                  {'  '}prediction=pred,{'\n'}
                  {'  '}latency_ms=<span className="text-[#F59E0B]">18.4</span>
                  {'\n'}){'\n\n'}
                  <span className="text-slate-500">
                    # SentinelML automatically computes KS-Drift
                  </span>
                  {'\n'}
                  <span className="text-slate-500">
                    # &amp; triggers self-healing if threshold &gt; 0.20
                  </span>
                </code>
              </pre>
            </div>
            <div className="absolute -inset-10 bg-[#A855F7]/5 rounded-full blur-[80px] -z-10" />
          </div>

          <div className="order-1 lg:order-2 space-y-6">
            <h2 className="text-4xl font-bold tracking-tight text-white">
              3-Line Code Integration
            </h2>
            <p className="text-slate-400 leading-relaxed text-lg">
              Developer experience focused monitoring. Wrap any model with our lightweight SDK and get production-grade observability and autonomous recovery instantly.
            </p>
            <div className="flex flex-wrap gap-3">
              <span className="px-3 py-1 bg-white/5 rounded-full text-[10px] border border-[#232D3F] uppercase tracking-widest text-slate-400 font-bold font-mono">
                Python SDK
              </span>
              <span className="px-3 py-1 bg-white/5 rounded-full text-[10px] border border-[#232D3F] uppercase tracking-widest text-slate-400 font-bold font-mono">
                DVC 3.0
              </span>
              <span className="px-3 py-1 bg-white/5 rounded-full text-[10px] border border-[#232D3F] uppercase tracking-widest text-slate-400 font-bold font-mono">
                MLflow
              </span>
            </div>
            <Link
              href="/dashboard"
              className="inline-flex items-center space-x-2 bg-[#A855F7]/10 text-[#A855F7] border border-[#A855F7]/20 px-6 py-3 rounded-lg font-medium hover:bg-[#A855F7] hover:text-white transition-all"
            >
              <span>Explore Control Center</span>
              <ExternalLink className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Ecosystem Bento Grid */}
      <section id="architecture" className="py-24 px-6 bg-[#131822]">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <h2 className="text-4xl font-bold tracking-tight text-white mb-4">
              Architecture &amp; Tech Stack
              <br />
              Ecosystem
            </h2>
            <p className="text-slate-400 max-w-2xl text-lg">
              Seamless integrations across your entire MLOps lifecycle from ingestion to serving.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2 bg-[#0B0E14] border border-[#232D3F] rounded-2xl p-8 relative overflow-hidden group min-h-[400px]">
              <div className="relative z-10">
                <h3 className="font-bold text-2xl text-white mb-4">
                  Control Plane Orchestration
                </h3>
                <p className="text-slate-400 text-sm max-w-md leading-relaxed">
                  Centralized management of drift thresholds, retraining triggers, and hot-swap policies across globally distributed model clusters.
                </p>
              </div>
              <div className="absolute right-0 bottom-0 w-full h-full">
                <img
                  className="w-full h-full object-cover opacity-40 group-hover:opacity-60 transition-opacity duration-700"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_5f07116716_26436f4a7490324a.png"
                  alt="Architecture Diagram"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0B0E14] via-[#0B0E14]/20 to-transparent" />
              </div>
            </div>

            <div className="bg-[#0B0E14] border border-[#232D3F] rounded-2xl p-8 flex flex-col justify-between group">
              <div className="space-y-6">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center border border-[#232D3F]">
                    <Cpu className="w-6 h-6 text-[#A855F7]" />
                  </div>
                  <span className="font-bold text-lg text-white">Python Core</span>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center border border-[#232D3F]">
                    <Zap className="w-6 h-6 text-[#10B981]" />
                  </div>
                  <span className="font-bold text-lg text-white">FastAPI Core</span>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center border border-[#232D3F]">
                    <Layers className="w-6 h-6 text-[#F59E0B]" />
                  </div>
                  <span className="font-bold text-lg text-white">Redis Cache</span>
                </div>
              </div>
              <div className="mt-8 h-48 rounded-xl overflow-hidden border border-[#232D3F]">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_7a6e4a3475_5d0b595776bab111.png"
                  alt="Processing stack"
                />
              </div>
            </div>

            <div className="bg-[#0B0E14] border border-[#232D3F] rounded-2xl p-6 flex flex-col justify-between group">
              <div className="aspect-square rounded-xl overflow-hidden mb-4">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_11246aade6_b4d446a7a6efd9cd.png"
                  alt="PyTorch Native"
                />
              </div>
              <div>
                <h4 className="font-bold text-white mb-1">PyTorch Native</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Hooks into the autograd loop for per-batch monitoring and zero-latency drift detection.
                </p>
              </div>
            </div>

            <div className="bg-[#0B0E14] border border-[#232D3F] rounded-2xl p-6 flex flex-col justify-between group">
              <div className="aspect-square rounded-xl overflow-hidden mb-4">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_435ae3696f_7799d3683b819c25.png"
                  alt="Cloud Agnostic"
                />
              </div>
              <div>
                <h4 className="font-bold text-white mb-1">Cloud Agnostic</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  AWS, GCP, Azure—deploy anywhere, observe everywhere with unified control plane.
                </p>
              </div>
            </div>

            <div className="bg-[#0B0E14] border border-[#232D3F] rounded-2xl p-6 flex flex-col justify-between group">
              <div className="aspect-square rounded-xl overflow-hidden mb-4">
                <img
                  className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700"
                  src="https://storage.googleapis.com/uxpilot-auth.appspot.com/gen_dcca43d7e8_0d78689e2c3960b7.png"
                  alt="SOC 2 Compliant"
                />
              </div>
              <div>
                <h4 className="font-bold text-white mb-1">SOC 2 Compliant</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Enterprise-grade audit trails, role-based access, and encrypted model telemetry.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0B0E14] border-t border-[#232D3F] pt-20 pb-10 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="space-y-6">
              <div className="flex items-center space-x-2">
                <Shield className="w-6 h-6 text-[#A855F7]" />
                <span className="font-bold text-lg text-white tracking-tight">SentinelML</span>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">
                Autonomous reliability for machine learning systems. Built for engineers who ship models to millions.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-sm uppercase tracking-widest text-slate-200 mb-6 font-mono">
                Product
              </h4>
              <ul className="space-y-3 text-sm text-slate-400">
                <li>
                  <a href="#features" className="hover:text-white transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#architecture" className="hover:text-white transition-colors">
                    Integrations
                  </a>
                </li>
                <li>
                  <Link href="/dashboard" className="hover:text-white transition-colors">
                    Control Center
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-sm uppercase tracking-widest text-slate-200 mb-6 font-mono">
                Resources
              </h4>
              <ul className="space-y-3 text-sm text-slate-400">
                <li>
                  <a href="#docs" className="hover:text-white transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#docs" className="hover:text-white transition-colors">
                    API Reference
                  </a>
                </li>
                <li>
                  <Link href="/incidents" className="hover:text-white transition-colors">
                    System Incidents
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-sm uppercase tracking-widest text-slate-200 mb-6 font-mono">
                Platform
              </h4>
              <ul className="space-y-3 text-sm text-slate-400">
                <li>
                  <Link href="/models" className="hover:text-white transition-colors">
                    Models Registry
                  </Link>
                </li>
                <li>
                  <Link href="/retraining" className="hover:text-white transition-colors">
                    Retraining Pipelines
                  </Link>
                </li>
                <li>
                  <Link href="/settings" className="hover:text-white transition-colors">
                    Settings &amp; Keys
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-[#232D3F] pt-10 flex flex-col md:flex-row justify-between items-center space-y-6 md:space-y-0">
            <div className="flex items-center space-x-6 text-slate-400">
              <a
                href="https://github.com/harnishndangi/sentinal-ai"
                target="_blank"
                rel="noreferrer"
                className="hover:text-white transition-colors font-mono text-xs flex items-center gap-1.5"
              >
                <Star className="w-4 h-4 text-amber-400" />
                <span>GitHub Repository</span>
              </a>
            </div>
            <div className="flex items-center space-x-4">
              <input
                type="email"
                placeholder="Developer Newsletter"
                className="bg-white/5 border border-[#232D3F] rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-[#A855F7] transition-colors"
              />
              <button className="bg-[#A855F7] hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                Subscribe
              </button>
            </div>
          </div>

          <div className="mt-10 flex justify-between items-center text-xs text-slate-600">
            <span>© 2026 SentinelML. All rights reserved.</span>
            <div className="flex space-x-6">
              <Link href="/dashboard" className="hover:text-slate-400">
                Control Panel
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
