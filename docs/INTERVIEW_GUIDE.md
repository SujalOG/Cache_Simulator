# Distributed Caching System — Systems Design & Interview Guide

This guide is designed to help you ace technical and system design interviews when presenting this project. It details the theoretical foundations, algorithmic complexities, failure modes, trade-offs, and real-world considerations of distributed caching.

---

## 1. High-Level Elevator Pitch

> *"I designed and built a distributed caching system simulator in Python to analyze key distribution, eviction algorithms, and node failure dynamics under realistic workloads. To truly understand the internal mechanics, I implemented $O(1)$ LRU and $O(1)$ LFU caches from scratch using custom doubly linked lists and frequency buckets, routed keys using a Consistent Hash Ring with 100 virtual nodes per instance, simulated clockwise successor failover, and benchmarked our performance directly against Redis."*

---

## 2. Core Architectural Pillars

### 2.1 Why Not Just Use Naive Modulo Hashing (`hash(key) % N`)?
- **The Problem**: In a naive distributed cache with $N$ nodes, adding or removing a node changes the modulo base to $N \pm 1$.
- **The Math**: The probability that a key remains mapped to the same node when transitioning from $N$ to $N+1$ nodes is only:
  $$\text{Fraction of keys preserved} \approx \frac{1}{N+1}$$
  $$\text{Fraction of keys invalidated} \approx \frac{N}{N+1} \approx 70\% - 80\%$$
- **System Impact**: Almost all cached entries simultaneously miss, triggering a massive **Cache Stampede (Thundering Herd)** that cascades directly to the persistent database, causing catastrophic latency spikes or database outages.
- **The Consistent Hashing Solution**:
  - Maps both nodes and keys to an integer ring $[0, 2^{32}-1]$.
  - Keys route clockwise to the first node on the ring.
  - When scaling from $N$ to $N+1$ nodes, only keys between the new node and its predecessor move:
  $$\text{Fraction of keys moved} \approx \frac{1}{N+1}$$
  For example, adding a 4th node only moves $\approx 25\%$ of keys, keeping $\approx 75\%$ of cache entries valid!

### 2.2 Why Are Virtual Nodes Essential?
- With standard consistent hashing, placing only 3 or 4 physical nodes on the ring creates non-uniform arc lengths, causing "hotspots" where one node receives $60\%$ of traffic while another receives only $10\%$.
- By assigning **$V$ virtual nodes** (default: 100) per physical node (e.g., `f"{node_id}#vnode_{i}"`), physical nodes are interleaved across the ring.
- By the Law of Large Numbers, the standard deviation of key distribution drops substantially:
  $$\sigma \propto \frac{1}{\sqrt{V}}$$
  yielding an even $\approx 33.3\%$ traffic split on a 3-node cluster.

---

## 3. Eviction Algorithms: LRU vs. LFU

| Dimension | Least Recently Used (LRU) | Least Frequently Used (LFU) |
|---|---|---|
| **Underlying Data Structures** | HashMap + Single Doubly Linked List | HashMap + Frequency Buckets (Doubly Linked Lists) + `min_freq` pointer |
| **Time Complexity** | $O(1)$ `get`, $O(1)$ `put`, $O(1)$ evict | Strict $O(1)$ `get`, $O(1)$ `put`, $O(1)$ evict |
| **Tie-Breaking** | Natural (head = MRU, tail = LRU) | LRU recency within the `min_freq` bucket |
| **Best Used For** | Temporal locality, streaming data, sliding windows | Skewed long-tail data (Zipfian / Hot Products) |
| **Failure Mode** | **Cache Thrashing / Pollution**: A sequential table scan sweeps all hot data out of cache. | **Frequency Ghosting / Cache Stagnation**: Old keys with historically huge counts never get evicted when popularity fades. |

---

## 4. Failure Handling & Clockwise Failover

### What happens when Node 2 crashes?
1. **Detection & Routing**: The cluster marks Node 2 as unhealthy.
2. **Clockwise Successor Traversal**:
   - The consistent hash ring receives a request for a key whose natural partition belongs to Node 2.
   - The ring scans clockwise past Node 2's virtual node until it hits the first virtual node owned by an active node (e.g., Node 3).
3. **Cold Miss Cascade**:
   - Node 3 does not yet have this data in its local memory $\rightarrow$ **Cache Miss**.
   - The application fetches the record from the backing database ($\approx 20\text{ ms}$).
   - The record is inserted into Node 3 $\rightarrow$ **Re-cached**.
4. **Recovery / Re-joining**:
   - When Node 2 recovers, it re-enters the active set. Subsequent requests for its partition immediately route back to Node 2 without data loss if memory was persisted.

---

## 5. Workload Modeling: Why Zipfian Skew?
- Real-world production traffic is **never uniformly random**.
- In e-commerce (e.g. Amazon) or social networks (e.g. Twitter/X), $80\%$ of requests target top $20\%$ of keys (Pareto Principle / Zipf's Law):
  $$P(k) \propto \frac{1}{k^\alpha}, \quad \alpha \approx 0.8 - 1.2$$
- In our simulator, the Zipfian generator validates why caches are effective: even with a small cache capacity ($10\%$ of total keys), hit rates can surpass $80\%-90\%$.

---

## 6. Simulator vs. Redis: The Interview Comparison

### "Why did you benchmark against Redis?"
- **Redis Architecture**: Written in ANSI C, runs a single-threaded event loop (`ae.c`) using non-blocking epoll/kqueue, with jemalloc memory allocation and native C hash tables (`dict.c`).
- **Our Python Simulator**:
  - Focuses on architecture, algorithmic verification, and distributed systems experiment testing.
  - Uses pure Python data structures (custom Doubly Linked Lists and `bisect` binary search).
- **Key Takeaways**:
  - Algorithmic hit rates and eviction counts follow the exact same curve as Redis `allkeys-lru` and `allkeys-lfu`.
  - Redis showcases the performance advantage of compiled systems languages and dedicated socket event loops, completing single-digit microsecond operations vs Python millisecond object overhead.
