"""Tests for ClearPulse entity resolution and the intelligence graph.

    python3 -m unittest clearpulse.tests.test_graph -v
"""

from __future__ import annotations

import unittest

from clearpulse.graph.entity import EntityResolver, name_similarity
from clearpulse.graph.network import IntelligenceGraph


class EntityResolverTests(unittest.TestCase):
    def test_name_similarity_token_order_agnostic(self):
        self.assertEqual(name_similarity("John A Smith", "smith john a"), 1.0)
        self.assertGreater(name_similarity("John Smith", "Jon Smith"), 0.0)

    def test_merges_similar_records_with_confidence(self):
        r = EntityResolver(threshold=0.6)
        r.add("rec1", {"name": "John Smith", "dob": "1980-01-01",
                       "device": "DEV-9"})
        r.add("rec2", {"name": "Smith John", "dob": "1980-01-01",
                       "device": "DEV-9"})
        r.add("rec3", {"name": "Alice Brown", "dob": "1992-07-07",
                       "device": "DEV-3"})
        entities = r.resolve()
        clusters = {tuple(e.record_ids) for e in entities}
        self.assertIn(("rec1", "rec2"), clusters)
        self.assertIn(("rec3",), clusters)
        merged = next(e for e in entities if len(e.record_ids) == 2)
        self.assertGreaterEqual(merged.confidence, 0.6)
        self.assertTrue(merged.evidence)

    def test_distinct_records_not_merged(self):
        r = EntityResolver(threshold=0.6)
        r.add("a", {"name": "Carl Jones", "dob": "1970-02-02", "device": "D1"})
        r.add("b", {"name": "Dana White", "dob": "1985-09-09", "device": "D2"})
        entities = r.resolve()
        self.assertEqual(len(entities), 2)

    def test_transitive_merge_via_shared_device(self):
        # Three records pairwise similar enough merge into one entity.
        r = EntityResolver(threshold=0.5)
        for i in range(3):
            r.add(f"r{i}", {"name": "Same Person", "device": "DEV-X",
                            "dob": "1990-03-03"})
        entities = r.resolve()
        self.assertEqual(len(entities), 1)
        self.assertEqual(len(entities[0].record_ids), 3)


class IntelligenceGraphTests(unittest.TestCase):
    def test_shared_attribute_linking(self):
        g = IntelligenceGraph()
        g.add_node("P1", "provider", device="DEV-1")
        g.add_node("P2", "provider", device="DEV-1")
        g.add_node("P3", "provider", device="DEV-2")
        added = g.link_shared_attribute("device", kind="shared_device")
        self.assertEqual(added, 1)  # only P1-P2 share DEV-1
        self.assertIn("P2", g.neighbors("P1"))
        self.assertEqual(g.degree("P3"), 0)

    def test_connected_components(self):
        g = IntelligenceGraph()
        g.add_edge("a", "b", "co_access")
        g.add_edge("b", "c", "co_access")
        g.add_node("z", "provider")
        comps = g.connected_components()
        self.assertIn(["a", "b", "c"], comps)
        self.assertIn(["z"], comps)

    def test_detect_rings_flags_dense_suspicious_cluster(self):
        g = IntelligenceGraph()
        # Four providers all sharing one device + mutual co-access = a ring.
        for p in ("P1", "P2", "P3", "P4"):
            g.add_node(p, "provider", device="DEV-RING")
        g.link_shared_attribute("device", kind="shared_device")
        g.add_edge("P1", "P3", "co_access")
        g.add_edge("P2", "P4", "co_access")
        rings = g.detect_rings(min_size=3, min_suspicious_edges=3)
        self.assertTrue(rings)
        ring = rings[0]
        self.assertGreaterEqual(len(ring.members), 4)
        self.assertIn("shared_device", ring.kinds)
        self.assertGreater(ring.suspicion, 0)

    def test_no_ring_when_below_thresholds(self):
        g = IntelligenceGraph()
        g.add_edge("x", "y", "shared_device")
        self.assertEqual(g.detect_rings(min_size=3, min_suspicious_edges=3), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
