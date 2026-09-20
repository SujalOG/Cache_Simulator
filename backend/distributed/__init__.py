"""
Distributed Routing Layer
Contains consistent hashing and cluster coordination:
- hash_ring.py: Consistent Hash Ring with Virtual Nodes and Clockwise Successor Failover
- modulo_ring.py: Naive Modulo Hashing Ring for rebalancing churn comparison
- cluster.py: Cluster Coordinator managing node lifecycles and request routing
"""
