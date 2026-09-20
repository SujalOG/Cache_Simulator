import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import CustomPlayground from './components/CustomPlayground';
import BenchmarkSuite from './components/BenchmarkSuite';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('playground');
  const [health, setHealth] = useState({ status: 'checking', redis_connected: false });
  const [loading, setLoading] = useState(false);
  const [playgroundResults, setPlaygroundResults] = useState(null);
  const [experimentResults, setExperimentResults] = useState({});
  const [error, setError] = useState(null);

  // Poll health on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await api.getHealth();
        setHealth(res);
      } catch (err) {
        setHealth({ status: 'offline', redis_connected: false });
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  // Run custom simulation
  const handleRunSimulation = async (params) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.simulate(params);
      setPlaygroundResults(data);
    } catch (err) {
      setError(err.message || 'Simulation execution failed');
    } finally {
      setLoading(false);
    }
  };

  // Run canonical benchmark experiment
  const handleRunExperiment = async (expId, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runExperiment(expId, params);
      setExperimentResults((prev) => ({
        ...prev,
        [expId]: data,
      }));
    } catch (err) {
      setError(err.message || 'Benchmark execution failed');
    } finally {
      setLoading(false);
    }
  };

  // Run initial default simulation on first load if empty
  useEffect(() => {
    if (!playgroundResults && health.status === 'healthy') {
      handleRunSimulation({
        policy: 'lru',
        nodes: 3,
        capacity_per_node: 500,
        vnodes: 100,
        requests: 10000,
        unique_keys: 1000,
        workload_pattern: 'hot_keys',
        read_ratio: 0.8,
        zipf_alpha: 0.99,
      });
    }
  }, [health.status]);

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col font-mono selection:bg-sky-500 selection:text-slate-950">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex justify-between items-center">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-rose-300 font-bold ml-4"
            >
              ✕
            </button>
          </div>
        )}

        {activeTab === 'playground' ? (
          <CustomPlayground
            onRunSimulation={handleRunSimulation}
            loading={loading}
            results={playgroundResults}
          />
        ) : (
          <BenchmarkSuite
            onRunExperiment={handleRunExperiment}
            loading={loading}
            experimentResults={experimentResults}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 py-6 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Distributed Caching System Performance Lab & Architecture Simulator</span>
          <span>Zero-Dependency Python Engine • Consistent Hash Ring • O(1) LRU / LFU</span>
        </div>
      </footer>
    </div>
  );
}
