# Distributed Caching System — Master Architecture & Interview Preparation Guide

This comprehensive guide is designed to make you 100% interview-ready for software engineering, systems design, and distributed systems roles. It provides an in-depth breakdown of every component, data structure, mathematical model, and dashboard feature in this project, followed by 25+ technical interview questions with high-scoring answers.

---

# Table of Contents
1. [Project Overview & Elevator Pitch](#1-project-overview--elevator-pitch)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Core Technical Components & Data Structures](#3-core-technical-components--data-structures)
   - [3.1 Handcrafted $O(1)$ LRU Cache](#31-handcrafted-o1-lru-cache)
   - [3.2 Handcrafted $O(1)$ LFU Cache](#32-handcrafted-o1-lfu-cache)
   - [3.3 TTL Expiration & Lazy Eviction](#33-ttl-expiration--lazy-eviction)
   - [3.4 Consistent Hash Ring & Virtual Nodes](#34-consistent-hash-ring--virtual-nodes)
   - [3.5 Clockwise Successor Failover](#35-clockwise-successor-failover)
   - [3.6 Naive Modulo Hashing & Rebalancing Proof](#36-naive-modulo-hashing--rebalancing-proof)
   - [3.7 Workload Generator (Zipfian Power Law)](#37-workload-generator-zipfian-power-law)
   - [3.8 Hybrid Deterministic Latency Model](#38-hybrid-deterministic-latency-model)
   - [3.9 Production Redis Baseline](#39-production-redis-baseline)
4. [Dashboard Walkthrough: How Everything Works](#40-dashboard-walkthrough-how-everything-works)
   - [4.1 Global Header & Live Telemetry](#41-global-header--live-telemetry)
   - [4.2 Custom Playground: Interactive Parameters & Charts](#42-custom-playground-interactive-parameters--charts)
   - [4.3 The 6 Canonical System Design Experiments](#43-the-6-canonical-system-design-experiments)
5. [Master Technical Interview Questions & Model Answers](#5-master-technical-interview-questions--model-answers)
   - [Category A: Distributed Systems & Consistent Hashing](#category-a-distributed-systems--consistent-hashing)
   - [Category B: Data Structures & Eviction Algorithms](#category-b-data-structures--eviction-algorithms)
   - [Category C: Production System Design & Caching Patterns](#category-c-production-system-design--caching-patterns)
   - [Category D: Project Architecture & Engineering Decisions](#category-d-project-architecture--engineering-decisions)

---

# 1. Project Overview & Elevator Pitch

### The 60-Second Elevator Pitch
> *"I designed and implemented a distributed caching system simulator in Python and Docker to analyze how eviction policies, cluster scaling, and node failures impact distributed systems performance. To demonstrate mastery of low-level algorithms, I implemented $O(1)$ LRU and $O(1)$ LFU caches from scratch using custom doubly linked lists and frequency buckets with zero third-party caching libraries. Keys are routed across cluster nodes using a Consistent Hash Ring with 100 virtual nodes per instance, featuring clockwise successor failover during node crashes. I built a Zipfian power-law workload generator to model realistic web traffic, measured latency percentiles (P50 to P99) across 100,000 requests, and benchmarked our custom Python engine directly against a live production Redis instance."*

### The Core Problem Solved
Distributed caches are often treated as black boxes. In production, systems break during edge cases:
1. **Cluster Resizing**: Adding or removing a cache node causes cache churn. Naive hashing invalidates $\approx 75\%$ of keys, triggering a database stampede.
2. **Eviction Inefficiencies**: Under skewed access patterns, LRU can suffer from cache thrashing during sequential scans, whereas LFU can suffer from cache stagnation.
3. **Node Failures**: When a node dies, traffic must cascade gracefully without taking down the entire cluster.

This project quantitatively answers: **"How does a distributed cache behave under changing workloads, eviction strategies, cluster topologies, and hardware failures?"**

---

# 2. End-to-End System Architecture

```
                    ┌───────────────────────────────┐
                    │      React Web Dashboard      │
                    │ (Vite + Tailwind + Recharts)  │
                    └───────────────┬───────────────┘
                                    │ HTTP / REST (Port 3000 -> 5000)
                                    ▼
                    ┌───────────────────────────────┐
                    │        Flask REST API         │
                    │       (backend/app.py)        │
                    └───────┬───────────────┬───────┘
                            │               │
                            ▼               ▼
         ┌───────────────────────────┐   ┌───────────────────────────┐
         │     Simulation Engine     │   │      Redis Baseline       │
         │   (backend/simulator/)    │   │  (Live Redis 7 Container) │
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
   │  Node 0   │ │  Node 1   │ │  Node 2   │
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

### The Life of a Cache Request (`GET product:1024`):
1. **Workload Arrival**: A request arrives from the workload generator with key `product:1024`.
2. **Hash Ring Lookup**: The router computes `hash_32("product:1024")` and binary-searches the sorted consistent hash ring in $O(\log(V \cdot N))$ time to locate the responsible active node (e.g., `Node 1`).
3. **Node Check**: `Node 1` checks its local cache in $O(1)$ time.
4. **TTL Expiration Check**: If the key exists but its TTL has expired (`current_time >= expiry`), the node lazily evicts it, increments the `expired` and `misses` counters, and returns a miss.
5. **Decision Branch**:
   - **CACHE HIT**: The value is returned immediately. Latency is sampled from the in-memory cache distribution ($\approx 0.8\text{ ms}$).
   - **CACHE MISS**: The system falls back to the `SimulatedDatabase`.
6. **Database Read**: The database fetches the item, adding disk/network latency ($\approx 15-25\text{ ms}$).
7. **Cache Populate & Evict**: The database value is stored into `Node 1`. If `Node 1` is full, its eviction policy (LRU or LFU) purges the lowest-priority item in $O(1)$ time.
8. **Telemetry Recording**: The request records operation type, hit/miss status, latency, node ID, and eviction status into the `MetricsCollector`.

---

# 3. Core Technical Components & Data Structures

## 3.1 Handcrafted $O(1)$ LRU Cache
- **Location**: `backend/core/lru_cache.py` & `backend/core/dll.py`
- **Data Structures**:
  - `_map: dict[Any, Node]`: Maps key to its Doubly Linked List node.
  - `_dll: DoublyLinkedList`: Maintains access recency. Head sentinel points to Most Recently Used (MRU); Tail sentinel points to Least Recently Used (LRU).
- **Time Complexities**:
  - `get(key)`: $O(1)$. HashMap lookup $\rightarrow$ unlink node from DLL $\rightarrow$ re-insert at Head.
  - `put(key, value, ttl)`: $O(1)$. If exists, update and move to Head. If new and full, pop node at Tail (`pop_tail()`), delete from HashMap, and insert new node at Head.
  - `delete(key)`: $O(1)$. Remove from HashMap and unlink from DLL.
- **Why Custom DLL over `collections.OrderedDict`?**:
  In a coding interview, using `OrderedDict` hides algorithmic knowledge. Writing custom pointers (`prev`, `next`) with sentinel nodes proves you understand pointer manipulation, edge-case handling (empty list, single node), and memory layout.

---

## 3.2 Handcrafted $O(1)$ LFU Cache
- **Location**: `backend/core/lfu_cache.py`
- **Architecture**: The classic LeetCode 460 constant-time algorithm.
- **Data Structures**:
  - `_map: dict[Any, Node]`: Maps key to Node (storing key, value, frequency).
  - `_freq_buckets: dict[int, DoublyLinkedList]`: Maps frequency $F$ to a Doubly Linked List of nodes that have been accessed $F$ times.
  - `_min_freq: int`: Tracks the minimum access frequency currently in the cache.
- **Algorithm & Time Complexities**:
  - `get(key)`: $O(1)$.
    1. Fetch node from `_map`.
    2. Remove node from `_freq_buckets[node.freq]`.
    3. If `_freq_buckets[node.freq]` is now empty and `_min_freq == node.freq`, increment `_min_freq += 1`.
    4. Increment `node.freq += 1` and prepend to `_freq_buckets[node.freq]`.
  - `put(key, value)`: $O(1)$.
    1. If key exists, update value and promote frequency (same as `get`).
    2. If key is new and cache is full:
       - Access `_freq_buckets[_min_freq]`.
       - Evict the tail node in that bucket (`pop_tail()`). **This naturally resolves frequency ties using LRU recency!**
       - Delete the evicted key from `_map`.
    3. Insert new node with frequency $1$ into `_freq_buckets[1]`.
    4. Reset `_min_freq = 1`.

---

## 3.3 TTL Expiration & Lazy Eviction
- **Location**: `backend/core/cache_node.py`
- **Design Decision: Active Sweep vs. Lazy Deletion**:
  - Running a background thread with `while True: sleep()` to inspect every key wastes CPU and requires locking.
  - We use **Lazy (Passive) Expiration**: Each node stores an `expiry` timestamp (`time.time() + ttl`). When a key is accessed via `get(key)`, the node checks `if current_time >= node.expiry`. If expired, it unlinks the key, increments `expired` and `misses`, and returns `None`.

---

## 3.4 Consistent Hash Ring & Virtual Nodes
- **Location**: `backend/distributed/hash_ring.py`
- **Hash Space**: 32-bit integer ring $[0, 2^{32}-1]$ generated via `hashlib.md5(key.encode()).hexdigest()[:8]`.
- **Virtual Nodes**:
  - Each physical node (e.g., `node_0`) is replicated $V$ times (default: $V=100$) on the ring as `node_0#vnode_0`, `node_0#vnode_1`, ..., `node_0#vnode_99`.
  - Virtual nodes are inserted into a sorted integer list `_ring`.
- **Routing Algorithm**:
  - For key $K$, compute $H = \text{hash\_32}(K)$.
  - Find the index in `_ring` using binary search: `bisect.bisect_right(_ring, H)`.
  - If index equals the ring length, wrap around clockwise to index $0$.
  - Look up the physical node mapped to that hash.
  - **Time Complexity**: $O(\log(V \cdot N))$ where $V$ is virtual nodes and $N$ is physical nodes. For 4 nodes with 100 vnodes ($400$ total points), lookup takes $\approx 9$ comparisons!

---

## 3.5 Clockwise Successor Failover
- **Problem**: In a distributed cache without master-slave replication, what happens when a node crashes?
- **Our Implementation**:
  - The cluster maintains an active health set (`healthy_nodes`).
  - When `node_1` crashes, incoming keys that map to `node_1`'s virtual nodes are not dropped.
  - The router walks clockwise along `_ring` until it reaches a virtual node owned by an **active, healthy node** (e.g., `node_2`).
  - **Observable Effect**: `node_2` does not yet have this key in memory $\rightarrow$ triggers a cache miss $\rightarrow$ fetches from database $\rightarrow$ caches in `node_2`. This accurately models the real-world **cold-miss cascade** on remaining nodes.

---

## 3.6 Naive Modulo Hashing & Rebalancing Proof
- **Location**: `backend/distributed/modulo_ring.py`
- **Naive Modulo**: Maps keys using `hash(key) % N`.
- **Mathematical Rebalancing Proof**:
  Suppose you have $N=3$ nodes and scale to $N=4$ nodes.
  - In Naive Modulo: A key remains on the same node only if `hash(key) % 3 == hash(key) % 4`.
  - By the Chinese Remainder Theorem and number theory:
    $$\text{Probability of key moving} = \frac{N}{N+1} = \frac{3}{4} = 75\%$$
    $$\text{Probability of key staying} = \frac{1}{N+1} = \frac{1}{4} = 25\%$$
  - **System Consequence**: Adding a single node invalidates $75\%$ of your entire cache simultaneously. This causes a **Cache Stampede (Thundering Herd)** that knocks down backing databases.
  - **Consistent Hashing Advantage**:
    In Consistent Hashing, only the keys between the newly inserted node's positions and their immediate predecessors are reassigned:
    $$\text{Keys moved} \approx \frac{1}{N+1} = 25\%$$
    $75\%$ of all cached entries remain valid!

---

## 3.7 Workload Generator (Zipfian Power Law)
- **Location**: `backend/simulator/workload.py`
- **Why Real Workloads are Zipfian**:
  In production (e.g. Netflix movies, Amazon products, Twitter posts), access patterns follow the Pareto Principle ($80/20$ rule). A small fraction of items receive the vast majority of views.
- **Mathematical Formulation**:
  The probability of accessing the $k$-th most popular item among $N$ items is:
  $$P(k) = \frac{1}{k^\alpha \sum_{n=1}^N \frac{1}{n^\alpha}}$$
  where $\alpha \approx 0.99$ (YCSB standard).
- **High-Performance Implementation**:
  Generating 100,000 requests naively in Python using floating-point loops is slow. We precompute a Cumulative Distribution Function (CDF) array of length $N$. Each sample draws a uniform random float $u \in [0, 1)$ and finds the key index in $O(\log N)$ time via `bisect.bisect_right(cdf, u)`. This generates 100,000 Zipfian requests in $< 0.1$ seconds!

---

## 3.8 Hybrid Deterministic Latency Model
- **Location**: `backend/simulator/engine.py`
- **The Problem**: If a simulator pauses with real `time.sleep(0.02)` for 100,000 requests, a single simulation would take 2,000 seconds (33 minutes!).
- **The Hybrid Solution**:
  - Cache operations execute in memory in pure Python ($< 1$ second).
  - Each request samples latency from statistical distributions calibrated to real hardware:
    - **Cache Hit**: Sampled from $\mathcal{N}(\mu=0.8\text{ ms}, \sigma=0.15\text{ ms})$, clipped at min $0.2\text{ ms}$.
    - **Cache Miss (DB Fetch)**: Sampled from $\mathcal{N}(\mu=20\text{ ms}, \sigma=4\text{ ms})$ representing disk/network I/O.
    - **DB Write**: Sampled from $\mathcal{N}(\mu=25\text{ ms}, \sigma=5\text{ ms})$.
  - This allows measuring realistic P50, P90, P95, and P99 latency percentiles across 100,000 requests almost instantaneously.

---

## 3.9 Production Redis Baseline
- **Location**: `backend/simulator/redis_client.py`
- Connects to the live `redis:7-alpine` container over a dedicated connection pool.
- Replays the identical generated request sequence against Redis.
- Dynamically calculates `maxmemory` above Redis's internal boot overhead (`used_memory_startup` $\approx 1\text{ MB}$), setting `maxmemory` to $2-10\text{ MB}$ with `allkeys-lru`.
- Captures real TCP network socket round-trip time and queries Redis `INFO stats` for `keyspace_hits`, `keyspace_misses`, and `evicted_keys`.

---

# 4. Dashboard Walkthrough: How Everything Works

The dashboard is built with **React (Vite), Tailwind CSS, Recharts, and Lucide Icons**. It operates in two main modes:

## 4.1 Global Header & Live Telemetry
- **Header Status Lights**:
  - **Flask API**: Polls `/api/health` every 15 seconds. Shows a pulsing green dot when online.
  - **Redis Baseline**: Shows **Active** (green) when the live Redis container responds to TCP ping; shows **Standby** (amber) if Redis is unreachable.
- **View Switcher**: Toggles seamlessly between **Custom Playground** and **6 Canonical Benchmarks**.

---

## 4.2 Custom Playground: Interactive Parameters & Charts

### Control Panel Inputs:
1. **Eviction Policy**: Choose between **LRU** (Least Recently Used) and **LFU** (Least Frequently Used).
2. **Workload Pattern**:
   - **Hot Keys (Zipfian)**: Generates heavy access skew where top $20\%$ of keys get $\approx 80\%$ of traffic.
   - **Random (Uniform)**: Uniformly distributes requests across the entire key range.
   - **Sequential**: Cycles monotonically through keys, simulating a database scan that pollutes the cache.
3. **Cluster Nodes Slider (1 to 6)**: Dynamically scales the number of physical nodes in the hash ring.
4. **Capacity Per Node (Keys)**: Configures individual node memory boundaries (triggers evictions when exceeded).
5. **Total Requests**: Choose from 1,000 up to 100,000 requests.
6. **Unique Keys Pool**: Defines working set size (e.g. 1,000 unique keys vs 500 total capacity).
7. **Read / Write Ratio**: Configures the percentage of `GET` lookups vs `SET` write operations.
8. **Virtual Nodes Per Node**: Sets the number of virtual node positions per physical node on the hash ring (default: 100).
9. **Node Crash Simulation Toggle**:
   - Select a target node (e.g., `node_1`).
   - Specify the exact request step at which the node crashes (e.g., at request #5,000 of 10,000).
   - Demonstrates clockwise failover live!

### Output Cards & Visualizations:
- **KPI Metrics Cards**:
  - **Hit Rate %**: Color-coded (green $\ge 70\%$, amber $40-70\%$, rose $<40\%$).
  - **Requests**: Total requests processed with breakdown between GET and SET.
  - **Avg Latency & P95 Latency**: High-resolution response timing in milliseconds.
  - **Evictions & TTL Expired**: Total items pushed out due to capacity limits or expired timestamps.
  - **DB Activity**: Total cache-miss queries that hit the backing database.
- **Interactive Charts**:
  - **Cluster Node Distribution**: Bar chart displaying the percentage of traffic routed to each node, including the **standard deviation** of load balance.
  - **Hit vs. Miss Ratio**: Donut chart showing the proportion of cache hits vs misses.
  - **Latency Distribution**: Bar chart comparing Min, Avg, P50, P90, P95, P99, and Max latencies.
- **Cluster Node Memory & Health Table**:
  - Displays each node's ID, live status (**Active** or **Failed**), policy, keys stored vs capacity, a visual percentage utilization bar, and per-node hit/miss breakdown.

---

## 4.3 The 6 Canonical System Design Experiments

Located under the **"6 Canonical Benchmarks"** tab:

### Experiment 01: LRU vs. LFU Eviction Performance
- **Workload**: Identical 10,000 Zipfian requests executed on LRU vs LFU clusters.
- **Visuals**: Comparative side-by-side performance cards.
- **Interview Insight**: Under hot-key workloads, LFU retains frequently accessed keys even if there is a brief pause in requests. However, LFU suffers from cache pollution when previously popular keys fade. LRU adapts more rapidly to shifting working sets.

### Experiment 02: Access Pattern Comparison (Locality vs. Thrashing)
- **Workload**: Evaluates the same cache cluster under **Hot-Keys**, **Uniform Random**, and **Sequential** traffic.
- **Visuals**: 3-way comparative metrics cards.
- **Interview Insight**: Cache effectiveness is entirely dependent on temporal and spatial locality. Hot-key workloads yield $>80\%$ hit rates, Uniform Random drops to approximately $\text{Capacity} / \text{Keys}$, and Sequential scans thrash the cache completely.

### Experiment 03: Horizontal Cluster Scaling (1 to 4 Nodes)
- **Workload**: Runs identical traffic while scaling from 1 node to 4 nodes.
- **Visuals**: Tabular comparison of total capacity, hit rate growth, eviction drop, and load standard deviation.
- **Interview Insight**: Demonstrates horizontal scalability. Adding nodes increases cluster capacity linearly, reducing evictions and lowering P95 latency.

### Experiment 04: Key Rebalancing Churn on Scale-Out
- **Workload**: Compares Consistent Hashing against Naive Modulo Hashing when scaling from 3 to 4 nodes across 5,000 keys.
- **Visuals**: High-contrast comparison cards showing percentage of keys invalidated.
- **Interview Insight**: Naive Modulo invalidates $\approx 75\%$ of keys ($N / (N+1)$), causing a database stampede. Consistent Hashing only moves $\approx 25\%$ of keys ($1 / (N+1)$), proving why consistent hashing is the industry standard in DynamoDB, Cassandra, and Memcached.

### Experiment 05: Node Crash Simulation & Successor Failover
- **Workload**: A 3-node cluster experiences a sudden crash of `node_1` midway through execution.
- **Visuals**: Pre-crash baseline vs Post-crash metrics showing the surge in database reads and traffic redistribution.
- **Interview Insight**: Illustrates clockwise successor routing. Incoming requests for the dead node route to its healthy successor, which initially lacks the keys—causing a temporary surge of cold misses on the database before stabilizing.

### Experiment 06: Simulator vs. Production Redis Baseline
- **Workload**: Executes the exact same request stream against our custom Python simulator and the live C-based Redis 7 container.
- **Visuals**: Side-by-side comparison showing hit rate parity, evictions, and real socket latencies.
- **Interview Insight**: Demonstrates that our custom Python engine achieves algorithmic parity with Redis (matching hit rates and eviction behaviors), while illustrating the latency advantage of Redis's compiled C event loop (`ae.c`) and low-level socket handling.

---

# 5. Master Technical Interview Questions & Model Answers

---

## Category A: Distributed Systems & Consistent Hashing

### Q1: "Explain how Consistent Hashing works and why we need virtual nodes."
**Model Answer:**
> "Consistent Hashing maps both physical nodes and data keys to a circular numeric ring—in our system, a 32-bit integer space from $0$ to $2^{32}-1$ using MD5. A key is assigned to the first node encountered moving clockwise on the ring.
>
> If we only placed physical nodes on the ring, hashing variance would create unequal partitions—one node might own $60\%$ of the ring while another owns $10\%$. To guarantee uniform distribution, we assign virtual nodes ($V=100$ per physical node) formatted as `node_id#vnode_i`. By the Law of Large Numbers, interleaving 400 virtual points ensures each physical node receives an even share of keys ($\approx 25\%$ on a 4-node cluster) with low standard deviation. Lookups remain very fast at $O(\log(V \cdot N))$ using binary search."

---

### Q2: "What happens when a node fails in consistent hashing?"
**Model Answer:**
> "When a node fails, its virtual points become inactive. In our simulator, we implement **Clockwise Successor Failover**: any key that hashes to a position owned by the dead node continues traversing clockwise until it reaches the first active, healthy node.
>
> Because that successor node does not yet have those keys in its local memory, those requests result in cold cache misses, temporarily increasing database reads until the successor caches the data. Only the keys assigned to the failed node are affected; all keys assigned to other healthy nodes remain completely unaffected."

---

### Q3: "How does Consistent Hashing compare to Naive Modulo Hashing when scaling out?"
**Model Answer:**
> "With naive hashing, a key's node is determined by `hash(key) % N`. If you scale from $N=3$ to $N=4$ nodes, the modulo denominator changes for every single calculation. Statistically, $N / (N+1)$ or $75\%$ of all keys change node assignments. This invalidates three-quarters of the cache in an instant, causing a massive Cache Stampede (Thundering Herd) that can crash the database.
>
> In Consistent Hashing, adding a 4th node only takes over a fraction of the ring from its immediate neighbors. Only $1 / (N+1)$ or $\approx 25\%$ of keys move, leaving $75\%$ of cached entries undisturbed."

---

## Category B: Data Structures & Eviction Algorithms

### Q4: "How do you achieve $O(1)$ time complexity for LRU Cache?"
**Model Answer:**
> "A standalone hash table gives $O(1)$ lookups but cannot maintain order. A standalone array or linked list maintains order but requires $O(N)$ lookups.
>
> By pairing a **Hash Map** with a **Doubly Linked List (DLL)**, we get the best of both:
> - The Hash Map maps keys directly to DLL `Node` objects for $O(1)$ access.
> - The DLL maintains recency order with sentinel `head` and `tail` nodes.
> - On a `get(key)` or `put(key)`, we unlink the node and re-insert it at the `head` in $O(1)$ by updating four pointers (`prev.next` and `next.prev`).
> - When the cache is full, we evict the node immediately before the `tail` (`tail.prev`) in $O(1)$ and delete its key from the Hash Map."

---

### Q5: "How does your LFU Cache achieve strict $O(1)$ time complexity?"
**Model Answer:**
> "Many naive LFU implementations use a min-heap, which takes $O(\log N)$ on access because frequency updates require heap restructuring.
>
> Our implementation achieves strict $O(1)$ using **Frequency Buckets**:
> 1. A Hash Map (`_map`) maps keys to Node objects, where each node stores its current frequency count.
> 2. A second Hash Map (`_freq_buckets`) maps each integer frequency $F$ to a Doubly Linked List of all nodes with frequency $F$.
> 3. We maintain a `_min_freq` integer pointer.
>
> When a key is accessed, we unlink it from its current frequency DLL in $O(1)$ and insert it into frequency bucket $F+1$. If the old bucket was `_min_freq` and is now empty, we increment `_min_freq += 1`. When capacity is reached, we evict the tail of `_freq_buckets[_min_freq]` in $O(1)$ time. This also automatically resolves frequency ties using LRU recency!"

---

### Q6: "What are the failure modes of LRU vs LFU in production?"
**Model Answer:**
> "- **LRU Failure Mode (Cache Thrashing / Pollution)**: If a background job executes a sequential table scan across 100,000 records, LRU pushes out all genuinely popular hot keys to make room for records that will only be read once.
> - **LFU Failure Mode (Cache Stagnation / Ghosting)**: If an item experiences a viral surge of 10,000 views in the morning and its traffic subsequently drops to zero in the afternoon, its frequency count remains 10,000. It occupies cache memory indefinitely and blocks newly popular items from being cached. Modern systems often resolve this using decayed frequencies or TinyLFU."

---

## Category C: Production System Design & Caching Patterns

### Q7: "What caching pattern did you implement, and what are the alternatives?"
**Model Answer:**
> "We implemented the **Cache-Aside (Lazy Loading)** pattern:
> 1. The application checks the cache first.
> 2. On a hit, data is returned immediately.
> 3. On a miss, the application reads from the database, writes the entry into the cache, and returns the data.
>
> **Alternatives**:
> - **Read-Through**: The application only talks to the cache; the cache itself is responsible for fetching from the database on a miss.
> - **Write-Through**: The application writes to the cache, and the cache synchronously writes to the database before acknowledging success (ensures consistency, but higher write latency).
> - **Write-Behind (Write-Back)**: Writes go to cache and acknowledge immediately; asynchronous batches flush updates to the database (high write throughput, but risk of data loss on cache crash)."

---

### Q8: "What is a Cache Stampede (Thundering Herd) and how do you prevent it?"
**Model Answer:**
> "A Cache Stampede occurs when a high-traffic key (e.g. homepage news) expires or is evicted. Thousands of concurrent requests experience a cache miss simultaneously and all query the backing database at the same instant, causing connection pool exhaustion and potential outage.
>
> **Mitigation Strategies**:
> 1. **Mutex / Distributed Locking**: The first thread to miss acquires a lock (e.g., via Redis `SETNX`) to query the database and populate the cache; all other threads wait or retry.
> 2. **Probabilistic Early Expiration (XFetch algorithm)**: As a key nears expiration, requests probabilistically recalculate and re-cache the value in the background before it actually expires.
> 3. **Consistent Hashing**: Minimizes key invalidation churn during cluster resizing so that keys do not suddenly disappear en masse."

---

### Q9: "What is the difference between Cache Penetration, Cache Breakdown, and Cache Avalanche?"
**Model Answer:**
> "- **Cache Breakdown**: A single, ultra-popular 'hot key' expires, causing a sudden spike of queries for that specific key to hit the database. (Fixed with distributed locks or mutual exclusion).
> - **Cache Penetration**: Requests query keys that exist neither in the cache nor in the database (e.g., malicious requests for negative user IDs). Every request bypasses the cache and hits the database. (Fixed with **Bloom Filters** or caching empty/null values with a short TTL).
> - **Cache Avalanche**: Many keys are configured with the exact same TTL (e.g., 3600s) and expire at the exact same second, or an entire cache node crashes, sending a massive wave of misses to the database. (Fixed by adding **jitter / random variance** to TTLs and using consistent hashing failover)."

---

## Category D: Project Architecture & Engineering Decisions

### Q10: "Why did you build a custom simulator in Python instead of just running Redis?"
**Model Answer:**
> "Running an existing Redis instance only teaches you how to be a consumer of an API (`client.get()` and `client.set()`). It doesn't prove that you understand how hash rings balance data, how virtual nodes mitigate hot-spot variance, how doubly linked lists achieve $O(1)$ eviction, or why consistent hashing moves only $1/(N+1)$ keys.
>
> By writing the data structures and routing algorithms myself, I developed a deep first-principles understanding of distributed caching. Then, by benchmarking my Python simulator against production Redis in Docker, I showed how high-level architectural concepts translate to production C-based systems."

---

### Q11: "What was a subtle technical bug you encountered during this project, and how did you resolve it?"
**Model Answer:**
> "When benchmarking against Redis 7 in Docker, Experiment 6 unexpectedly returned an error: `command not allowed when used memory > 'maxmemory'`.
>
> Upon investigation, I discovered that Redis 7 has an internal startup memory overhead of $\approx 1.04\text{ MB}$ for event loops, hash table buckets, and server structures before any keys are stored. The code was attempting to enforce an arbitrary $1.00\text{ MB}$ limit. Because initial used memory exceeded $1.00\text{ MB}$, Redis entered out-of-memory protection and rejected commands.
>
> I fixed this by updating the client to dynamically inspect Redis's `used_memory_startup` from `INFO memory` and sizing the memory ceiling safely above it ($\ge 2\text{ MB}$). This allowed key allocations and eviction routines to execute cleanly."

---

### Q12: "If you had 3 more months to work on this system, what would you build next?"
**Model Answer:**
> "I would focus on three production enhancements:
> 1. **Master-Slave Replication & Sentinel**: Implement primary-replica node pairs on the hash ring with automated heartbeat health checks and leader election.
> 2. **Advanced Eviction Policies**: Implement **W-TinyLFU** (used by Caffeine cache) and **2Q**, which combine an admission window with a frequency filter to eliminate the scan-resistance flaws of both LRU and LFU.
> 3. **Bloom Filter Fronting**: Add an in-memory Bloom filter before the hash ring to eliminate cache penetration for non-existent keys."
