"""Intelligence graph - relationship analytics over resolved entities.

Where the risk engine scores one event, the graph scores *structure*: a provider
and patient who never overlap individually but share a device with three other
providers form a ring no single-event detector can see. This is a small,
dependency-free property graph with the few algorithms investigation actually
needs - connected components, shared-attribute linking, degree centrality, and
ring detection (a dense, multi-entity cluster of suspicious edges).

It is deliberately a thin in-memory model with the same seam philosophy as the
rest of ClearPulse: swap it for Neo4j at scale; the analytics contract stays.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

# Edge kinds that, en masse, suggest organised activity rather than coincidence.
SUSPICIOUS_EDGE_KINDS = frozenset({
    "shared_device", "shared_address", "temporal_billing_overlap",
    "co_access", "compromised_account",
})


@dataclass
class Node:
    node_id: str
    kind: str  # "provider" | "patient" | "device" | "entity" | ...
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    dst: str
    kind: str
    weight: float = 1.0

    def endpoints(self) -> tuple[str, str]:
        return tuple(sorted((self.src, self.dst)))  # undirected identity


@dataclass
class Ring:
    """A candidate fraud ring: a dense cluster of suspicious relationships."""

    members: list[str]
    edge_count: int
    suspicion: float
    kinds: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "members": list(self.members),
            "size": len(self.members),
            "edge_count": self.edge_count,
            "suspicion": round(self.suspicion, 3),
            "kinds": list(self.kinds),
        }


class IntelligenceGraph:
    """An undirected property graph with investigative analytics."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self._adj: dict[str, set[str]] = defaultdict(set)
        self._edges: dict[tuple[str, str], Edge] = {}

    # -- construction -------------------------------------------------------

    def add_node(self, node_id: str, kind: str, **attrs: Any) -> Node:
        node = self.nodes.get(node_id)
        if node is None:
            node = Node(node_id=node_id, kind=kind, attrs=dict(attrs))
            self.nodes[node_id] = node
        else:
            node.attrs.update(attrs)
        return node

    def add_edge(self, src: str, dst: str, kind: str, weight: float = 1.0) -> Edge:
        if src == dst:
            raise ValueError("self-edges are not meaningful here")
        for nid in (src, dst):
            if nid not in self.nodes:
                self.add_node(nid, kind="unknown")
        edge = Edge(src=src, dst=dst, kind=kind, weight=weight)
        key = edge.endpoints()
        # Keep the strongest edge per (pair, kind) but collapse the pair for
        # adjacency; later weights accumulate on the stored edge.
        existing = self._edges.get(key)
        if existing is None:
            self._edges[key] = edge
        else:
            existing.weight += weight
            if existing.kind != kind:
                existing.kind = f"{existing.kind}+{kind}"
        self._adj[src].add(dst)
        self._adj[dst].add(src)
        return self._edges[key]

    def link_shared_attribute(self, attr: str, kind: str) -> int:
        """Add edges between every pair of nodes sharing a non-null ``attr``.

        This is how device/address sharing becomes graph structure: returns the
        number of edges added. The classic ring seed.
        """
        buckets: dict[Any, list[str]] = defaultdict(list)
        for node in self.nodes.values():
            value = node.attrs.get(attr)
            if value is not None:
                buckets[value].append(node.node_id)
        added = 0
        for members in buckets.values():
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    self.add_edge(members[i], members[j], kind=kind)
                    added += 1
        return added

    # -- queries ------------------------------------------------------------

    def neighbors(self, node_id: str) -> set[str]:
        return set(self._adj.get(node_id, set()))

    def degree(self, node_id: str) -> int:
        return len(self._adj.get(node_id, set()))

    def edges(self) -> list[Edge]:
        return list(self._edges.values())

    def connected_components(self) -> list[list[str]]:
        """Undirected components via iterative DFS, each returned sorted."""
        seen: set[str] = set()
        components: list[list[str]] = []
        for start in self.nodes:
            if start in seen:
                continue
            stack, comp = [start], []
            seen.add(start)
            while stack:
                node = stack.pop()
                comp.append(node)
                for nb in self._adj[node]:
                    if nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
            components.append(sorted(comp))
        return components

    def _component_edges(self, members: Iterable[str]) -> list[Edge]:
        member_set = set(members)
        return [e for (a, b), e in self._edges.items()
                if a in member_set and b in member_set]

    def detect_rings(
        self,
        *,
        min_size: int = 3,
        min_suspicious_edges: int = 3,
    ) -> list[Ring]:
        """Flag components that look like organised rings.

        Heuristic: a component with at least ``min_size`` members and at least
        ``min_suspicious_edges`` edges of a :data:`SUSPICIOUS_EDGE_KINDS` kind.
        Suspicion is the suspicious-edge density (suspicious edges per member),
        weighted by total edge weight - higher means tighter, more coordinated.
        """
        rings: list[Ring] = []
        for comp in self.connected_components():
            if len(comp) < min_size:
                continue
            comp_edges = self._component_edges(comp)
            suspicious = [e for e in comp_edges
                          if any(k in SUSPICIOUS_EDGE_KINDS for k in e.kind.split("+"))]
            if len(suspicious) < min_suspicious_edges:
                continue
            weight = sum(e.weight for e in suspicious)
            suspicion = (len(suspicious) / len(comp)) * (weight / len(suspicious))
            kinds = sorted({k for e in suspicious for k in e.kind.split("+")
                            if k in SUSPICIOUS_EDGE_KINDS})
            rings.append(Ring(
                members=comp,
                edge_count=len(suspicious),
                suspicion=suspicion,
                kinds=kinds,
            ))
        rings.sort(key=lambda r: r.suspicion, reverse=True)
        return rings

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [{"id": n.node_id, "kind": n.kind, "attrs": n.attrs}
                      for n in self.nodes.values()],
            "edges": [{"src": e.src, "dst": e.dst, "kind": e.kind,
                       "weight": e.weight} for e in self._edges.values()],
        }
