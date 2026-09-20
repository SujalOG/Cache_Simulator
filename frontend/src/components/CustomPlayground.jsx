import React, { useState } from 'react';
import { Play, RotateCcw, AlertTriangle, CheckCircle, Server, RefreshCw } from 'lucide-react';
import MetricsCards from './MetricsCards';
import Charts from './Charts';

export default function CustomPlayground({ onRunSimulation, loading, results }) {
  // Form parameters
  const [policy, setPolicy] = useState('lru');
  const [nodes, setNodes] = useState(3);
  const [capacity, setCapacity] = useState(500);
  const [vnodes, setVnodes] = useState(100);
  const [requests, setRequests] = useState(10000);
  const [uniqueKeys, setUniqueKeys] = useState(1000);
  const [pattern, setPattern] = useState('hot_keys');
  const [readRatio, setReadRatio] = useState(0.8);
  const [zipfAlpha, setZipfAlpha] = useState(0.99);

  // Failure simulation toggle
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [failedNodeId, setFailedNodeId] = useState('node_1');
  const [failAtRequest, setFailAtRequest] = useState(5000);

  const handleSubmit = (e) => {
    e.preventDefault();
    onRunSimulation({
      policy,
      nodes: Number(nodes),
      capacity_per_node: Number(capacity),
      vnodes: Number(vnodes),
      requests: Number(requests),
      unique_keys: Number(uniqueKeys),
      workload_pattern: pattern,
      read_ratio: Number(readRatio),
      zipf_alpha: Number(zipfAlpha),
      failed_node_id: simulateFailure ? failedNodeId : null,
      fail_at_request: simulateFailure ? Number(failAtRequest) : null,
    });
  };

  return (
    <div className="space-y-8">
      {/* Control Panel Card */}
      <form onSubmit={handleSubmit} className="bg-[#111622] border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <span>SIMULATION PARAMETERS</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Configure distributed cache topology, eviction policies, and workload access dynamics.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-slate-950 font-bold px-6 py-2.5 rounded-lg shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-xs uppercase tracking-wider"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Simulating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Run Simulation
              </>
            )}
          </button>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-6 text-xs">
          {/* Policy */}
          <div>
            <label className="block text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              Eviction Policy
            </label>
            <select
              value={policy}
              onChange={(e) => setPolicy(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            >
              <option value="lru">LRU (Least Recently Used)</option>
              <option value="lfu">LFU (Least Frequently Used)</option>
            </select>
          </div>

          {/* Workload Pattern */}
          <div>
            <label className="block text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              Workload Pattern
            </label>
            <select
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            >
              <option value="hot_keys">Hot Keys (Zipfian Skew)</option>
              <option value="random">Random (Uniform)</option>
              <option value="sequential">Sequential (Cache Scan)</option>
            </select>
          </div>

          {/* Nodes count */}
          <div>
            <div className="flex justify-between text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              <span>Cluster Nodes</span>
              <span className="text-sky-400 font-bold">{nodes}</span>
            </div>
            <input
              type="range"
              min="1"
              max="6"
              value={nodes}
              onChange={(e) => setNodes(e.target.value)}
              className="w-full accent-sky-400 cursor-pointer"
            />
          </div>

          {/* Capacity per node */}
          <div>
            <label className="block text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              Capacity Per Node (Keys)
            </label>
            <input
              type="number"
              min="50"
              max="5000"
              step="50"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Requests Volume */}
          <div>
            <label className="block text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              Total Requests
            </label>
            <select
              value={requests}
              onChange={(e) => {
                const val = Number(e.target.value);
                setRequests(val);
                setFailAtRequest(Math.floor(val / 2));
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            >
              <option value="1000">1,000 requests</option>
              <option value="5000">5,000 requests</option>
              <option value="10000">10,000 requests</option>
              <option value="50000">50,000 requests</option>
              <option value="100000">100,000 requests</option>
            </select>
          </div>

          {/* Unique Keys */}
          <div>
            <label className="block text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              Unique Keys Pool
            </label>
            <input
              type="number"
              min="100"
              max="10000"
              step="100"
              value={uniqueKeys}
              onChange={(e) => setUniqueKeys(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Read/Write Ratio */}
          <div>
            <div className="flex justify-between text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              <span>Read / Write Ratio</span>
              <span className="text-sky-400 font-bold">{Math.round(readRatio * 100)}% GET</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={readRatio}
              onChange={(e) => setReadRatio(e.target.value)}
              className="w-full accent-sky-400 cursor-pointer"
            />
          </div>

          {/* Virtual Nodes */}
          <div>
            <label className="block text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
              Virtual Nodes / Node (Ring)
            </label>
            <input
              type="number"
              min="10"
              max="200"
              step="10"
              value={vnodes}
              onChange={(e) => setVnodes(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            />
          </div>
        </div>

        {/* Node Failure Injection Toggle */}
        <div className="mt-6 pt-6 border-t border-slate-800/80">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="failToggle"
                checked={simulateFailure}
                onChange={(e) => setSimulateFailure(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-0 cursor-pointer"
              />
              <label htmlFor="failToggle" className="text-xs font-bold text-slate-200 cursor-pointer flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Simulate Mid-Workload Node Crash & Clockwise Successor Failover
              </label>
            </div>
          </div>

          {simulateFailure && (
            <div className="mt-4 p-4 rounded-xl bg-slate-900/60 border border-amber-500/20 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Target Node to Crash</label>
                <select
                  value={failedNodeId}
                  onChange={(e) => setFailedNodeId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white"
                >
                  {Array.from({ length: Number(nodes) }, (_, i) => `node_${i}`).map((id) => (
                    <option key={id} value={id}>
                      {id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  Crash At Request: <span className="text-amber-400 font-bold">{failedNodeId} @ req #{failAtRequest}</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max={requests - 1}
                  value={failAtRequest}
                  onChange={(e) => setFailAtRequest(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white"
                />
              </div>
            </div>
          )}
        </div>
      </form>

      {/* Results Dashboard */}
      {results && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Live Simulation Telemetry
            </h3>
            <span className="text-xs text-slate-400">
              {results.simulation_config?.workload_pattern} workload • {results.simulation_config?.policy.toUpperCase()} • {results.simulation_config?.num_nodes} nodes
            </span>
          </div>

          <MetricsCards summary={results} />
          <Charts summary={results} />

          {/* Node Health and Capacity Table */}
          {results.cluster_state?.nodes && (
            <div className="bg-[#111622] border border-slate-800 rounded-xl p-5 overflow-x-auto">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
                Cluster Node Memory & Health State
              </h4>
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-800">
                    <th className="pb-2">Node ID</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Policy</th>
                    <th className="pb-2">Keys Stored</th>
                    <th className="pb-2">Memory Utilization</th>
                    <th className="pb-2">Lookups</th>
                    <th className="pb-2">Hits / Misses</th>
                    <th className="pb-2">Evictions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {results.cluster_state.nodes.map((n) => (
                    <tr key={n.node_id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 font-bold text-white flex items-center gap-2">
                        <Server className="w-3.5 h-3.5 text-slate-400" />
                        {n.node_id}
                      </td>
                      <td className="py-2.5">
                        {n.status === 'active' ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold uppercase">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-semibold uppercase">
                            Failed
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 uppercase text-slate-300">{n.policy}</td>
                      <td className="py-2.5 text-slate-300">
                        {n.keys_count} / {n.capacity}
                      </td>
                      <td className="py-2.5">
                        <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full ${n.utilization_pct > 85 ? 'bg-rose-500' : 'bg-sky-500'}`}
                            style={{ width: `${n.utilization_pct}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-slate-400 mt-0.5 block">{n.utilization_pct}%</span>
                      </td>
                      <td className="py-2.5 text-slate-300">{n.total_lookups}</td>
                      <td className="py-2.5 text-slate-300">
                        <span className="text-emerald-400">{n.hits}</span> / <span className="text-rose-400">{n.misses}</span>
                      </td>
                      <td className="py-2.5 text-amber-400">{n.evictions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
