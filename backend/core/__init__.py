"""
Core Caching Engine
Contains low-level data structures and cache node implementations:
- dll.py: Handcrafted Doubly Linked List & Node primitives
- lru_cache.py: O(1) LRU Cache (Doubly Linked List + HashMap)
- lfu_cache.py: O(1) LFU Cache (Frequency Buckets + HashMap)
- cache_node.py: Cache node instance with TTL expiration and metrics
"""
