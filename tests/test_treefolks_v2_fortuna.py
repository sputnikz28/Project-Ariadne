"""Tests for core/services/treefolks_v2/fortuna.py."""

import inspect
import unittest

from core.services.treefolks_v2.fortuna import run_fortuna


class TestFortuna(unittest.TestCase):
    def test_uniform_scores(self):
        scores = run_fortuna([{"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}])
        self.assertTrue(all(v == 1.0 for v in scores.number_scores.values()))
        self.assertTrue(all(v == 1.0 for v in scores.star_scores.values()))
        self.assertEqual(set(scores.number_scores), set(range(1, 51)))
        self.assertEqual(set(scores.star_scores), set(range(1, 13)))

    def test_always_participates_even_with_empty_history(self):
        scores = run_fortuna([])
        self.assertIsNotNone(scores)

    def test_never_reads_historico_content(self):
        # Same result regardless of what historico actually contains --
        # proves scores never depend on history.
        r1 = run_fortuna([{"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}])
        r2 = run_fortuna([{"numeros": [46, 47, 48, 49, 50], "estrelas": [11, 12]}] * 50)
        self.assertEqual(r1, r2)

    def test_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(run_fortuna).parameters)
        self.assertEqual(params, {"historico"})


if __name__ == "__main__":
    unittest.main()
