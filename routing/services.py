import heapq
from collections import defaultdict
from decimal import Decimal

from routing.models import Edge


def build_graph():
    """Return {node_name: [(neighbor_name, latency), ...]} for directed edges."""
    graph = defaultdict(list)
    rows = Edge.objects.values_list("source__name", "destination__name", "latency")
    for source, destination, latency in rows:
        graph[source].append((destination, latency))
    return graph


def shortest_path(graph, source, destination):
    """Dijkstra. Returns (total_latency, path) or None if unreachable."""
    dist = {source: Decimal("0")}
    prev = {}
    heap = [(Decimal("0"), source)]

    while heap:
        d, node = heapq.heappop(heap)
        if node == destination:
            break
        if d > dist.get(node, Decimal("Infinity")):
            continue  # stale heap entry
        for neighbor, latency in graph.get(node, []):
            nd = d + latency
            if nd < dist.get(neighbor, Decimal("Infinity")):
                dist[neighbor] = nd
                prev[neighbor] = node
                heapq.heappush(heap, (nd, neighbor))

    if destination not in dist:
        return None

    path = [destination]
    while path[-1] != source:
        path.append(prev[path[-1]])
    return dist[destination], path[::-1]