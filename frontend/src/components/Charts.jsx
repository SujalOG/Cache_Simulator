import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const COLORS = ['#38bdf8', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'];

export default function Charts({ summary }) {
  if (!summary) return null;

  // 1. Prepare Node Distribution data
  const nodeDistData = Object.entries(summary.node_distribution || {}).map(([nodeId, data], index) => ({
    name: nodeId,
    requests: data.requests,
    percentage: data.percentage,
    hitRate: data.hit_rate_pct,
    fill: COLORS[index % COLORS.length]
  }));

  // 2. Prepare Hit vs Miss data
  const hitMissData = [
    { name: 'Cache Hits', value: summary.hits, color: '#10b981' },
    { name: 'Cache Misses', value: summary.misses, color: '#f43f5e' },
  ];

  // 3. Prepare Latency Percentile data
  const latencyData = [
    { name: 'Min', latency: summary.latency?.min_ms || 0 },
    { name: 'Avg', latency: summary.latency?.avg_ms || 0 },
    { name: 'P50', latency: summary.latency?.p50_ms || 0 },
    { name: 'P90', latency: summary.latency?.p90_ms || 0 },
    { name: 'P95', latency: summary.latency?.p95_ms || 0 },
    { name: 'P99', latency: summary.latency?.p99_ms || 0 },
    { name: 'Max', latency: summary.latency?.max_ms || 0 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Chart 1: Node Traffic Distribution */}
      <div className="bg-[#111622] border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            Cluster Node Distribution
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Request balance across physical nodes via Consistent Hash Ring (Std Dev: {summary.load_std_dev ?? 0})
          </p>
        </div>
        <div className="h-64 w-full">
          {nodeDistData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={nodeDistData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(value, name) => [`${value}% of total traffic`, 'Traffic Share']}
                />
                <Bar dataKey="percentage" radius={[6, 6, 0, 0]}>
                  {nodeDistData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No node distribution data
            </div>
          )}
        </div>
      </div>

      {/* Chart 2: Hit vs Miss Breakdown */}
      <div className="bg-[#111622] border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            Hit vs Miss Ratio
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Cache-aside lookup efficiency ({summary.hit_rate_pct}% Hit Rate)
          </p>
        </div>
        <div className="h-64 w-full flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={hitMissData}
                innerRadius={60}
                outerRadius={85}
                paddingAngle={4}
                dataKey="value"
              >
                {hitMissData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(value) => [value.toLocaleString(), 'Requests']}
              />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 3: Latency Percentiles */}
      <div className="bg-[#111622] border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            Latency Distribution (ms)
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Response times across cache hits (~0.8ms) & DB misses (~20ms)
          </p>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={latencyData}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} unit="ms" />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val) => [`${val} ms`, 'Latency']}
              />
              <Bar dataKey="latency" fill="#818cf8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
