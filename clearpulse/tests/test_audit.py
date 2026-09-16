"""Tests for the ClearPulse cryptographic audit chain.

    python3 -m unittest clearpulse.tests.test_audit -v
"""

from __future__ import annotations

import dataclasses
import unittest

from clearpulse.audit.ledger import (
    AuditChain,
    GENESIS_PREV_HASH,
    verify_inclusion_proof,
)


class AuditChainTests(unittest.TestCase):
    def _chain(self, n: int) -> AuditChain:
        chain = AuditChain()
        for i in range(n):
            chain.append("ALERT", {"i": i, "summary": f"event {i}"},
                         trace_id=f"T-{i}")
        return chain

    def test_append_chains_prev_hash(self):
        chain = self._chain(3)
        entries = chain.entries
        self.assertEqual(entries[0].prev_hash, GENESIS_PREV_HASH)
        self.assertEqual(entries[1].prev_hash, entries[0].entry_hash)
        self.assertEqual(entries[2].prev_hash, entries[1].entry_hash)
        self.assertEqual(chain.head_hash, entries[-1].entry_hash)

    def test_clean_chain_verifies(self):
        result = self._chain(5).verify()
        self.assertTrue(result.ok)
        self.assertEqual(result.entries, 5)
        self.assertIsNone(result.broken_index)

    def test_content_tamper_detected(self):
        chain = self._chain(5)
        # Edit entry 2's payload but leave its stored hash stale.
        chain._entries[2] = dataclasses.replace(
            chain._entries[2], payload={"i": 2, "summary": "TAMPERED"})
        result = chain.verify()
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_index, 2)
        self.assertIn("content hash", result.reason)

    def test_reorder_tamper_detected(self):
        chain = self._chain(4)
        chain._entries[1], chain._entries[2] = chain._entries[2], chain._entries[1]
        result = chain.verify()
        self.assertFalse(result.ok)
        self.assertIn("prev_hash", result.reason)

    def test_merkle_root_is_stable_and_grows(self):
        chain = self._chain(4)
        root_a = chain.merkle_root()
        self.assertEqual(root_a, chain.merkle_root())  # deterministic
        chain.append("ALERT", {"i": 99})
        self.assertNotEqual(root_a, chain.merkle_root())  # commitment moved

    def test_empty_chain_root_is_genesis(self):
        self.assertEqual(AuditChain().merkle_root(), GENESIS_PREV_HASH)

    def test_inclusion_proofs_verify_for_all_entries(self):
        chain = self._chain(7)  # odd count exercises the duplicate-last path
        root = chain.merkle_root()
        for i, entry in enumerate(chain.entries):
            proof = chain.inclusion_proof(i)
            self.assertTrue(verify_inclusion_proof(entry.entry_hash, proof, root),
                            f"proof failed for index {i}")

    def test_inclusion_proof_rejects_wrong_leaf(self):
        chain = self._chain(4)
        root = chain.merkle_root()
        proof = chain.inclusion_proof(1)
        self.assertFalse(verify_inclusion_proof("deadbeef" * 8, proof, root))

    def test_export_roundtrip_shape(self):
        chain = self._chain(2)
        data = chain.to_dict()
        self.assertEqual(data["length"], 2)
        self.assertEqual(len(data["entries"]), 2)
        self.assertEqual(data["head_hash"], chain.head_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)
