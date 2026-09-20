# Distributed Cache Simulator — Project Progress & Engineering Log

This document serves as the single source of truth for the architecture, implementation phases, workflow details, verification outputs, and progress tracking throughout the development of the Distributed Cache Simulator.

---

## 1. Project High-Level Architecture

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

## 2. Master Implementation Phases

| Phase | Description | Status | Verification Target |
|---|---|---|---|
| **Phase 1** | **Project Setup, Environment, Dependencies & Skeleton** | 🟢 Completed | Environment active, dependencies installed, smoke tests pass |
| **Phase 2** | **Core Caching Engine (LRU, LFU, TTL, CacheNode)** | 🟢 Completed | Custom DLL, $O(1)$ LRU & LFU, TTL unit tests 100% pass (27/27) |
| **Phase 3** | **Distributed Layer (Consistent Hashing, Virtual Nodes, Failover)** | ⚪ Pending | Uniform ring distribution, binary search, failover re-routing |
| **Phase 4** | **Simulation Engine & Experiment Lab (Workloads, DB, Redis, 6 Experiments)** | ⚪ Pending | Zipfian skew verified, latency percentiles, Redis comparative runs |
| **Phase 5** | **Flask REST API Layer** | ⚪ Pending | REST endpoints responding with JSON simulation data |
| **Phase 6** | **React Dashboard (Playground & 6 Benchmark Suites)** | ⚪ Pending | Responsive dark-mode UI with live charts and failure injection |
| **Phase 7** | **Docker Orchestration & Interview Deep-Dive Guide** | ⚪ Pending | Single `docker compose up`, complete interview preparation guide |

---

## 3. Phase Details & Technical Specifications

### Phase 1: Project Setup & Skeleton (Current)
- **Goal**: Set up isolated Python virtual environment, install production and test dependencies, establish clean modular package structure, configure version control exclusions, and ensure the test harness is operational.
- **Directory Structure**:
  - `backend/core/`: Custom data structures and cache primitives.
  - `backend/distributed/`: Consistent hash ring, modulo ring, cluster coordinator.
  - `backend/simulator/`: Workload generator, database simulation, metrics engine, Redis benchmark client, experiments.
  - `backend/tests/`: Automated pytest test suites.
  - `docs/`: Technical logs and interview documentation.
- **Dependencies**: Flask, flask-cors, redis, pytest, requests.

### Phase 2: Core Caching Engine (Next)
- **Doubly Linked List (`dll.py`)**: Custom node pointers (`prev`, `next`), constant-time insertion at head, constant-time removal of arbitrary node, and tail eviction.
- **$O(1)$ LRU Cache (`lru_cache.py`)**:
  - `get(key)`: HashMap lookup $O(1)$ + move node to head $O(1)$.
  - `put(key, value, ttl)`: Insert/update node at head $O(1)$. On overflow, evict node at tail $O(1)$.
- **$O(1)$ LFU Cache (`lfu_cache.py`)**:
  - Frequency buckets (`dict[int, DoublyLinkedList]`).
  - Key-to-node map + `min_freq` tracker.
  - When frequency increases, node moves from bucket $F$ to $F+1$. If bucket $F$ becomes empty and was `min_freq`, increment `min_freq`.
  - On eviction: Pop tail of `min_freq` bucket $O(1)$ (breaks ties using LRU).
- **TTL Expiration (`cache_node.py`)**:
  - Timestamps evaluated lazily upon `get()`. Expired keys trigger eviction and count towards `expired` metrics.

### Phase 3: Distributed Routing Layer
- **Consistent Hash Ring (`hash_ring.py`)**:
  - 32-bit MD5 hash space $[0, 2^{32}-1]$.
  - Virtual nodes: Each physical node mapped to $V$ positions (`f"{node_id}#vnode_{i}"`).
  - Lookup: Clockwise binary search (`bisect.bisect_right`).
- **Clockwise Successor Failover**:
  - When a node is marked dead, key lookups bypass the dead node and route to the next healthy successor on the ring.
- **Naive Modulo Ring (`modulo_ring.py`)**:
  - `hash(key) % N` to benchmark and prove the high key-churn problem of naive hashing during scale-up/scale-down.

### Phase 4: Experiment Lab & Simulation Engine
- **Workload Generator (`workload.py`)**:
  - **Random**: Uniform distribution across key domain.
  - **Hot-Keys**: Zipfian / Power Law distribution (configurable $\alpha \approx 0.8$ to $1.2$), replicating production web/database access skew.
  - **Sequential**: Monotonic sequential scans to simulate cache pollution.
- **Simulated DB (`db.py`)**: Backing store simulating database read latency (15–30ms).
- **Hybrid Latency Engine (`engine.py`)**:
  - Fast, deterministic in-memory execution.
  - Cache hit: sampled from $0.5$–$1.2\text{ ms}$.
  - Cache miss: sampled from $15$–$30\text{ ms}$ (DB fetch) $+$ insertion overhead.
  - Metrics: Total requests, hit rate, miss rate, evictions, latency percentiles ($P50, P90, P95, P99$).
- **Redis Comparative Runner (`redis_client.py`)**:
  - Connection pool issuing operations to real Redis instance, tracking real network round-trip latencies and `INFO stats`.
- **6 Canonical Experiments**:
  1. LRU vs LFU under hot-key and sequential workloads.
  2. Access pattern comparison (Random vs Hot-Key vs Sequential).
  3. Horizontal node scaling (1, 2, 3, 4 nodes).
  4. Consistent hashing vs Naive Modulo rebalancing churn.
  5. Node failure & load surge on healthy nodes.
  6. Simulator vs Redis side-by-side performance baseline.

---

## 4. Test & Verification Log

| Test File | Description | Results |
|---|---|---|
| `backend/tests/test_smoke.py` | Package structure & test runner validation | ✅ **PASSED** (2/2 tests in 0.14s) |
| `backend/tests/test_dll.py` | Handcrafted Doubly Linked List & Node primitives | ✅ **PASSED** (4/4 tests in 0.03s) |
| `backend/tests/test_lru.py` | $O(1)$ LRU Cache (eviction, recency updates, overwrite) | ✅ **PASSED** (7/7 tests in 0.04s) |
| `backend/tests/test_lfu.py` | $O(1)$ LFU Cache (frequency promotion, LRU tie-breaking) | ✅ **PASSED** (7/7 tests in 0.04s) |
| `backend/tests/test_ttl.py` | TTL expiration & lazy eviction verification | ✅ **PASSED** (3/3 tests in 0.02s) |
| `backend/tests/test_cache_node.py` | CacheNode stats tracking, utilization, failure/recovery | ✅ **PASSED** (4/4 tests in 0.02s) |
| **Total Phase 2 Test Suite** | **All core engine primitives & eviction algorithms** | ✅ **27/27 PASSED (0.19s)** |

---

## 5. Next Immediate Steps
1. **Commit & Push Phase 2 to GitHub**:
   - Push stable Phase 2 implementation to `origin/main`.
2. **Phase 3: Distributed Routing Layer Implementation**:
   - Build `hash_ring.py`: Consistent Hash Ring with 32-bit MD5 hashing, virtual node replication, and clockwise `bisect` search.
   - Build `modulo_ring.py`: Naive Modulo hashing ring for rebalancing churn comparison.
   - Build `cluster.py`: CacheCluster managing physical nodes, ring routing, and clockwise successor failover when nodes fail.
   - Write comprehensive unit tests in `backend/tests/test_hash_ring.py` and `backend/tests/test_cluster.py`.
   - Run pytest and verify 100% test pass rate.
