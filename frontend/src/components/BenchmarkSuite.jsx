import React, { useState } from 'react';
import { Award, Play, RefreshCw, BookOpen, Layers, GitCompare, Zap, ShieldAlert, Cpu } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell
} from 'recharts';

const EXPERIMENTS = [
  {
    id: 'lru_vs_lfu',
    num: '01',
    title: 'LRU vs LFU Eviction',
    icon: GitCompare,
    subtitle: 'Evaluate recency bias against frequency counting under hot-key Zipfian loads.',
  },
  {
    id: 'workload_patterns',
    num: '02',
    title: 'Workload Access Patterns',
    icon: Layers,
    subtitle: 'Measure cache hits under Hot-Keys, Uniform Random, and Sequential scans.',
  },
  {
    id: 'node_scaling',
    num: '03',
    title: 'Horizontal Node Scaling',
    icon: Cpu,
    subtitle: 'Benchmark hit rates and memory load as cluster scales from 1 to 4 nodes.',
  },
  {
    id: 'consistent_vs_modulo',
    num: '04',
    title: 'Consistent vs Modulo Hashing',
    icon: Award,
    subtitle: 'Measure key churn on scale-out to prove why consistent hashing avoids cache stampedes.',
  },
  {
    id: 'node_failure',
    num: '05',
    title: 'Node Crash & Successor Failover',
    icon: ShieldAlert,
    subtitle: 'Simulate mid-stream node crash to observe clockwise failover and DB cold miss bursts.',
  },
  {
    id: 'simulator_vs_redis',
    num: '06',
    title: 'Simulator vs Production Redis',
    icon: Zap,
    subtitle: 'Direct side-by-side performance comparison against a live Redis instance.',
  },
];

export default function BenchmarkSuite({ onRunExperiment, loading, experimentResults }) {
  const [selectedExp, setSelectedExp] = useState('lru_vs_lfu');

  const currentResult = experimentResults[selectedExp];

  const handleRun = () => {
    onRunExperiment(selectedExp);
  };

  return (
    <div className="space-y-8">
      {/* Benchmark Selector Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {EXPERIMENTS.map((exp) => {
          const Icon = exp.icon;
          const isSelected = selectedExp === exp.id;
          const hasResult = Boolean(experimentResults[exp.id]);

          return (
            <button
              key={exp.id}
              onClick={() => setSelectedExp(exp.id)}
              className={`p-5 rounded-2xl border text-left transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-900 border-sky-500 ring-1 ring-sky-500/50 shadow-lg shadow-sky-500/10'
                  : 'bg-[#111622] border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    EXP {exp.num}
                  </span>
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-sky-500/20 text-sky-400' : 'bg-slate-800 text-slate-400'}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <h3 className="text-sm font-bold text-white mb-1">{exp.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-2">{exp.subtitle}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                {hasResult ? (
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    Results Ready
                  </span>
                ) : (
                  <span className="text-slate-500">Ready to run</span>
                )}
                <span className="text-sky-400 font-medium">Select →</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Benchmark Detail and Action Card */}
      <div className="bg-[#111622] border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
                Canonical Experiment Suite
              </span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1">
              {EXPERIMENTS.find((e) => e.id === selectedExp)?.title}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {EXPERIMENTS.find((e) => e.id === selectedExp)?.subtitle}
            </p>
          </div>

          <button
            onClick={handleRun}
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-slate-950 font-bold px-6 py-2.5 rounded-lg shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-xs uppercase tracking-wider"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Executing Lab...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Run Benchmark
              </>
            )}
          </button>
        </div>

        {/* Experiment Results Rendering */}
        {currentResult ? (
          <div className="pt-6 space-y-6">
            {/* Render based on experiment type */}
            {selectedExp === 'lru_vs_lfu' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
                  <h4 className="text-sm font-bold text-slate-200 mb-4">LRU Performance</h4>
                  <div className="space-y-3 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Hit Rate:</span>
                      <span className="font-bold text-emerald-400">{currentResult.lru.hit_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Miss Rate:</span>
                      <span className="font-bold text-rose-400">{currentResult.lru.miss_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Evictions:</span>
                      <span className="font-bold text-white">{currentResult.lru.evictions.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between py-1.5">
                      <span className="text-slate-400">Avg / P95 Latency:</span>
                      <span className="font-bold text-sky-400">{currentResult.lru.avg_latency_ms}ms / {currentResult.lru.p95_latency_ms}ms</span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
                  <h4 className="text-sm font-bold text-slate-200 mb-4">LFU Performance</h4>
                  <div className="space-y-3 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Hit Rate:</span>
                      <span className="font-bold text-emerald-400">{currentResult.lfu.hit_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Miss Rate:</span>
                      <span className="font-bold text-rose-400">{currentResult.lfu.miss_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Evictions:</span>
                      <span className="font-bold text-white">{currentResult.lfu.evictions.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between py-1.5">
                      <span className="text-slate-400">Avg / P95 Latency:</span>
                      <span className="font-bold text-sky-400">{currentResult.lfu.avg_latency_ms}ms / {currentResult.lfu.p95_latency_ms}ms</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedExp === 'workload_patterns' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(currentResult.patterns || {}).map(([pat, pData]) => (
                  <div key={pat} className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
                    <h4 className="text-sm font-bold text-slate-200 mb-4 capitalize">{pat.replace('_', ' ')}</h4>
                    <div className="space-y-3 text-xs">
                      <div className="flex justify-between py-1.5 border-b border-slate-800">
                        <span className="text-slate-400">Hit Rate:</span>
                        <span className="font-bold text-emerald-400">{pData.hit_rate_pct}%</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-slate-800">
                        <span className="text-slate-400">Evictions:</span>
                        <span className="font-bold text-white">{pData.evictions.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-slate-400">Avg Latency:</span>
                        <span className="font-bold text-sky-400">{pData.avg_latency_ms} ms</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedExp === 'node_scaling' && (
              <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-800">
                      <th className="pb-3">Cluster Size</th>
                      <th className="pb-3">Total Capacity</th>
                      <th className="pb-3">Hit Rate</th>
                      <th className="pb-3">Evictions</th>
                      <th className="pb-3">Avg Latency</th>
                      <th className="pb-3">Load Std Dev</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {currentResult.scaling.map((row) => (
                      <tr key={row.nodes}>
                        <td className="py-2.5 font-bold text-white">{row.nodes} Node(s)</td>
                        <td className="py-2.5 text-slate-300">{row.total_capacity} keys</td>
                        <td className="py-2.5 font-bold text-emerald-400">{row.hit_rate_pct}%</td>
                        <td className="py-2.5 text-amber-400">{row.evictions.toLocaleString()}</td>
                        <td className="py-2.5 text-sky-400">{row.avg_latency_ms} ms</td>
                        <td className="py-2.5 text-slate-400">{row.load_std_dev}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {selectedExp === 'consistent_vs_modulo' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-rose-500/10 border border-rose-500/30 p-5 rounded-xl">
                  <h4 className="text-sm font-bold text-rose-300 mb-2">Naive Modulo Hashing: hash(key) % N</h4>
                  <p className="text-xs text-slate-400 mb-4">Keys moved when scaling {currentResult.initial_nodes} → {currentResult.final_nodes} nodes:</p>
                  <div className="text-3xl font-bold text-rose-400">
                    {currentResult.naive_modulo.churn_pct}%
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {currentResult.naive_modulo.keys_moved.toLocaleString()} of {currentResult.keys_tested.toLocaleString()} keys invalidated!
                  </div>
                </div>

                <div className="bg-emerald-500/10 border border-emerald-500/30 p-5 rounded-xl">
                  <h4 className="text-sm font-bold text-emerald-300 mb-2">Consistent Hashing with Virtual Nodes</h4>
                  <p className="text-xs text-slate-400 mb-4">Keys moved when scaling {currentResult.initial_nodes} → {currentResult.final_nodes} nodes:</p>
                  <div className="text-3xl font-bold text-emerald-400">
                    {currentResult.consistent_hashing.churn_pct}%
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Only {currentResult.consistent_hashing.keys_moved.toLocaleString()} of {currentResult.keys_tested.toLocaleString()} keys moved (~1/N+1).
                  </div>
                </div>
              </div>
            )}

            {selectedExp === 'node_failure' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
                  <h4 className="text-sm font-bold text-emerald-400 mb-3">Healthy Cluster (3 Nodes Active)</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">Hit Rate:</span>
                      <span className="font-bold text-emerald-400">{currentResult.healthy_cluster.hit_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">DB Reads:</span>
                      <span className="font-bold text-white">{currentResult.healthy_cluster.db_reads}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Avg Latency:</span>
                      <span className="font-bold text-sky-400">{currentResult.healthy_cluster.avg_latency_ms} ms</span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-5 rounded-xl border border-rose-500/30">
                  <h4 className="text-sm font-bold text-rose-400 mb-3">After Node 1 Failure (Clockwise Failover)</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">Hit Rate:</span>
                      <span className="font-bold text-amber-400">{currentResult.failed_cluster.hit_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">DB Reads (Surge):</span>
                      <span className="font-bold text-rose-400">{currentResult.failed_cluster.db_reads}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Avg Latency:</span>
                      <span className="font-bold text-sky-400">{currentResult.failed_cluster.avg_latency_ms} ms</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedExp === 'simulator_vs_redis' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900/60 p-5 rounded-xl border border-sky-500/30">
                  <h4 className="text-sm font-bold text-sky-400 mb-3">Our Custom Simulator (Python Engine)</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">Hit Rate:</span>
                      <span className="font-bold text-emerald-400">{currentResult.simulator.hit_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">Evictions:</span>
                      <span className="font-bold text-white">{currentResult.simulator.evictions}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Avg Latency:</span>
                      <span className="font-bold text-sky-400">{currentResult.simulator.avg_latency_ms} ms</span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-5 rounded-xl border border-red-500/30">
                  <h4 className="text-sm font-bold text-red-400 mb-3">Production Redis (C Engine Baseline)</h4>
                  {currentResult.redis?.available ? (
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between py-1 border-b border-slate-800">
                        <span className="text-slate-400">Hit Rate:</span>
                        <span className="font-bold text-emerald-400">{currentResult.redis.hit_rate_pct}%</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-800">
                        <span className="text-slate-400">Evictions:</span>
                        <span className="font-bold text-white">{currentResult.redis.evictions}</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-slate-400">Avg Latency (Socket):</span>
                        <span className="font-bold text-sky-400">{currentResult.redis.latency?.avg_ms} ms</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-amber-400 p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                      {currentResult.redis?.message || 'Redis container is offline. Start docker compose to connect live Redis.'}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Interview Insights Box */}
            <div className="p-5 rounded-xl bg-gradient-to-r from-sky-950/40 to-slate-900/80 border border-sky-500/30 text-xs">
              <div className="flex items-center gap-2 text-sky-400 font-bold mb-2">
                <BookOpen className="w-4 h-4" />
                <span>INTERVIEW INSIGHTS & ARCHITECTURAL TAKEAWAYS</span>
              </div>
              <p className="text-slate-300 leading-relaxed font-sans">
                {currentResult.interview_insights}
              </p>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 text-xs">
            Click <span className="text-sky-400 font-semibold">"Run Benchmark"</span> above to execute this canonical experiment and generate comparative telemetry.
          </div>
        )}
      </div>
    </div>
  );
}
