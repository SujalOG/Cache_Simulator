# Distributed Caching System Performance Lab & Simulator

A Python-based distributed caching system simulator that implements core distributed caching algorithms from scratch, routes keys across a cluster using Consistent Hashing with Virtual Nodes, models realistic Zipfian workloads, and measures how eviction policies, scaling, and node failures affect performance—benchmarked against production Redis.

---

## 🏛️ System Architecture

```
                    ┌───────────────────────────────┐
                    │      React Web Dashboard      │
                    │ (Vite + Tailwind + Recharts)  │
                    └───────────────┬───────────────┘
                                    │ HTTP / REST
                                    ▼
                    ┌───────────────────────────────┐
                    │        Flask REST API         │
                    │       (backend/app.py)        │
                    └───────┬───────────────┬───────┘
                            │               │
                            ▼               ▼
         ┌───────────────────────────┐   ┌───────────────────────────┐
         │     Simulation Engine     │   │      Redis Baseline       │
         │   (backend/simulator/)    │   │      (Live Instance)      │
         └─────────────┬─────────────┘   └───────────────────────────┘
                       │
                       ▼
         ┌───────────────────────────┐
         │    Distributed Router     │
         │   (backend/distributed/)  │
         │    Consistent Hash Ring   │
         └─────────────┬─────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌───────────┐ ┌───────────┐ ┌───────────┐
   │  Node 1   │ │  Node 2   │ │  Node 3   │
   │  (LRU)    │ │  (LFU)    │ │  (LRU)    │
   └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
         │             │             │
         └─────────────┼─────────────┘
                       ▼
         ┌───────────────────────────┐
         │    Simulated Database     │
         │  (Backing store + latency)│
         └───────────────────────────┘
```

---

## ✨ Key Features

- **Handcrafted Eviction Engines (Zero External Cache Libraries)**:
  - **$O(1)$ LRU Cache**: Doubly Linked List + HashMap.
  - **$O(1)$ LFU Cache**: Frequency Buckets (Doubly Linked Lists) + HashMap + `min_freq` tracker with LRU tie-breaking.
  - **TTL Expiration**: Lazy eviction on access with metrics tracking.
- **Consistent Hashing & Virtual Nodes**:
  - Deterministic 32-bit MD5 integer ring $[0, 2^{32}-1]$.
  - Interleaved virtual nodes (default: 100 vnodes per physical node) eliminating distribution hotspots.
  - $O(\log(V \cdot N))$ lookups via binary search (`bisect`).
  - **Clockwise Successor Failover**: When a node fails, traffic automatically reroutes to the next healthy node clockwise.
- **Realistic Workload Generation**:
  - **Hot-Keys (Zipfian)**: Models power-law web traffic ($80/20$ rule) via precomputed CDFs.
  - **Random (Uniform)**: Uniform key access.
  - **Sequential**: Monotonic key scanning (cache sweep / pollution).
- **Comprehensive Telemetry**:
  - Hit Rate %, Miss Rate %, Total Evictions, TTL Expired.
  - High-resolution Latencies: Min, Max, Avg, P50, P90, P95, P99.
  - Per-node load and key distribution standard deviations.
- **Production Redis Comparison**:
  - Direct side-by-side benchmarking against a live Redis instance.
- **Dual-Mode Interactive UI**:
  - **Custom Playground**: Interactive sliders for nodes, capacity, policies, requests, and failure injection.
  - **6 Canonical System Design Experiments**: 1-click execution with automated comparative charts and interview takeaways.

---

## 🔬 The 6 Canonical Benchmark Experiments

1. **LRU vs. LFU Eviction**: Compares frequency bias vs recency bias under skewed Zipfian workloads.
2. **Access Pattern Dynamics**: Contrasts Hot-Keys against Uniform Random and Sequential cache thrashing.
3. **Horizontal Node Scaling**: Measures capacity growth and hit rate scaling from 1 to 4 nodes.
4. **Consistent vs. Modulo Hashing**: Quantifies key churn when adding a node ($\approx 25\%$ churn in Consistent Hashing vs $\approx 75\%$ churn in Naive Modulo).
5. **Node Crash Simulation**: Injects mid-stream node failure to observe clockwise failover and database cold miss cascades.
6. **Simulator vs. Redis**: Benchmarks custom Python algorithms against compiled C-based production Redis.

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Run the entire stack (React frontend, Flask API, and Redis) with a single command:

```bash
docker compose up --build
```

- **Frontend Dashboard**: Open `http://localhost:3000`
- **Flask REST API**: Responding at `http://localhost:5000/api/health`
- **Redis Server**: Running at `localhost:6379`

### Option 2: Local Development

#### 1. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

#### 2. Run Tests
```bash
cd backend
pytest -v
```

#### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---
