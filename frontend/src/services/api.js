import axios from 'axios';

// Detect API base: when accessing via Vite dev server or Docker proxy, use relative /api
// If needed, falls back to direct http://localhost:5000
const API_BASE = window.location.port === '3000' && window.location.hostname !== 'localhost'
  ? `http://${window.location.hostname}:5000/api`
  : '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  getHealth: async () => {
    try {
      const res = await apiClient.get('/health');
      return res.data;
    } catch (err) {
      // Direct localhost fallback if proxy is bypassed
      try {
        const directRes = await axios.get('http://localhost:5000/api/health', { timeout: 3000 });
        return directRes.data;
      } catch {
        return { status: 'offline', redis_connected: false, error: err.message };
      }
    }
  },

  simulate: async (params) => {
    try {
      const res = await apiClient.post('/simulate', params);
      return res.data;
    } catch (err) {
      try {
        const directRes = await axios.post('http://localhost:5000/api/simulate', params);
        return directRes.data;
      } catch (e) {
        throw new Error(e.response?.data?.error || e.message || 'Simulation request failed');
      }
    }
  },

  listExperiments: async () => {
    try {
      const res = await apiClient.get('/experiments/list');
      return res.data.experiments;
    } catch (err) {
      try {
        const directRes = await axios.get('http://localhost:5000/api/experiments/list');
        return directRes.data.experiments;
      } catch (e) {
        throw new Error(e.message || 'Failed to list experiments');
      }
    }
  },

  runExperiment: async (experimentId, params = {}) => {
    try {
      const res = await apiClient.post('/experiments/run', {
        experiment_id: experimentId,
        params,
      });
      return res.data;
    } catch (err) {
      try {
        const directRes = await axios.post('http://localhost:5000/api/experiments/run', {
          experiment_id: experimentId,
          params,
        });
        return directRes.data;
      } catch (e) {
        throw new Error(e.response?.data?.error || e.message || 'Experiment execution failed');
      }
    }
  },
};
