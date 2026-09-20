import React from 'react';
import { Target, Zap, Clock, Trash2, ArrowUpRight, Database } from 'lucide-react';

export default function MetricsCards({ summary }) {
  if (!summary) return null;

  const hitRate = summary.hit_rate_pct ?? 0;
  const isHealthyHit = hitRate >= 70;
  const isModerateHit = hitRate >= 40 && hitRate < 70;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {/* 1. Hit Rate */}
      <div className="bg-[#111622] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Hit Rate</span>
          <Target className="w-4 h-4 text-sky-400" />
        </div>
        <div>
          <div className={`text-2xl font-bold ${
            isHealthyHit ? 'text-emerald-400' : isModerateHit ? 'text-amber-400' : 'text-rose-400'
          }`}>
            {hitRate.toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
            <span>Hits: {summary.hits?.toLocaleString()}</span>
            <span>Miss: {summary.misses?.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* 2. Total Requests */}
      <div className="bg-[#111622] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Requests</span>
          <Zap className="w-4 h-4 text-amber-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-white">
            {summary.total_requests?.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
            <span>GET: {summary.get_operations?.toLocaleString()}</span>
            <span>SET: {summary.set_operations?.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* 3. Average Latency */}
      <div className="bg-[#111622] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Avg Latency</span>
          <Clock className="w-4 h-4 text-sky-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-sky-300">
            {summary.latency?.avg_ms?.toFixed(2) || '0.00'} <span className="text-xs text-slate-400 font-normal">ms</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Min: {summary.latency?.min_ms?.toFixed(1)}ms • Max: {summary.latency?.max_ms?.toFixed(1)}ms
          </div>
        </div>
      </div>

      {/* 4. P95 Latency */}
      <div className="bg-[#111622] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">P95 Latency</span>
          <ArrowUpRight className="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-purple-300">
            {summary.latency?.p95_ms?.toFixed(2) || '0.00'} <span className="text-xs text-slate-400 font-normal">ms</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            P50: {summary.latency?.p50_ms?.toFixed(1)}ms • P99: {summary.latency?.p99_ms?.toFixed(1)}ms
          </div>
        </div>
      </div>

      {/* 5. Evictions */}
      <div className="bg-[#111622] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">Evictions</span>
          <Trash2 className="w-4 h-4 text-rose-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-rose-300">
            {summary.evictions?.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            TTL Expired: {summary.expired || 0} keys
          </div>
        </div>
      </div>

      {/* 6. DB Activity */}
      <div className="bg-[#111622] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs uppercase tracking-wider font-semibold">DB Reads (Misses)</span>
          <Database className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-emerald-300">
            {summary.db_reads?.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            DB Writes: {summary.db_writes?.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
