import React from 'react';
import { Server, Database, Activity, Cpu, Sliders, Award } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, health }) {
  return (
    <header className="border-b border-slate-800 bg-[#0d121d]/90 backdrop-blur sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                DISTRIBUTED CACHE LAB
              </h1>
              <span className="px-2 py-0.5 text-[10px] uppercase tracking-wider rounded bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Consistent Hashing • O(1) LRU/LFU • Failover • Redis Baseline
            </p>
          </div>
        </div>

        {/* View Switcher */}
        <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('playground')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'playground'
                ? 'bg-sky-500 text-slate-950 shadow-lg shadow-sky-500/25'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Custom Playground
          </button>
          <button
            onClick={() => setActiveTab('benchmarks')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'benchmarks'
                ? 'bg-sky-500 text-slate-950 shadow-lg shadow-sky-500/25'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            6 Canonical Benchmarks
          </button>
        </div>

        {/* System & Redis Status */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Flask API:</span>
            {health?.status === 'healthy' ? (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Online
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                Offline
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Redis:</span>
            {health?.redis_connected ? (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Active
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-amber-400 font-medium" title="Run Docker to connect real Redis">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                Standby
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
