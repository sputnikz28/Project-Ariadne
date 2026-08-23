"""Tests for core/services/treefolks_v2/dodona.py."""

import inspect
import unittest

from core.services.treefolks_v2.dodona import _DODONA_ALPHA, run_dodona


def _draw(numeros, estrelas):
    return {"numeros": numeros, "estrelas": estrelas}


class TestDodona(unittest.TestCase):
    def test_always_participates_even_with_empty_history(self):
        scores = run_dodona([])
        self.assertIsNotNone(scores)
        # Posterior mean with zero observations reduces to the prior
        # mean, alpha/(2*alpha) = 0.5 for every value.
        self.assertTrue(all(abs(v - 0.5) < 1e-9 for v in scores.number_scores.values()))
        self.assertTrue(all(abs(v - 0.5) < 1e-9 for v in scores.star_scores.values()))

    def test_posterior_mean_matches_hand_computed_formula(self):
        # Number 7 appears in every one of 4 draws; number 8 never.
        historico = [
            _draw([7, 1, 2, 3, 4], [1, 2]),
            _draw([7, 5, 6, 9, 10], [3, 4]),
            _draw([7, 11, 12, 13, 14], [5, 6]),
            _draw([7, 15, 16, 17, 18], [7, 8]),
        ]
        scores = run_dodona(historico)
        total_draws = 4
        expected_7 = (4 + _DODONA_ALPHA) / (total_draws + 2 * _DODONA_ALPHA)
        expected_8 = (0 + _DODONA_ALPHA) / (total_draws + 2 * _DODONA_ALPHA)
        self.assertAlmostEqual(scores.number_scores[7], expected_7)
        self.assertAlmostEqual(scores.number_scores[8], expected_8)

    def test_shape_always_full_universe(self):
        scores = run_dodona([_draw([1, 2, 3, 4, 5], [1, 2])])
        self.assertEqual(set(scores.number_scores), set(range(1, 51)))
        self.assertEqual(set(scores.star_scores), set(range(1, 13)))

    def test_deterministic_pure_function(self):
        historico = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4])]
        r1 = run_dodona(historico)
        r2 = run_dodona(historico)
        self.assertEqual(r1, r2)

    def test_last_draw_alone_never_used_as_a_query_unlike_broceliande(self):
        # Dodona has no notion of "query pair" at all -- unlike
        # Brocéliande/Astérias, it treats every draw in historico
        # identically as evidence. This test documents that the last
        # draw is just one more observation, not special-cased.
        historico = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4])]
        scores_with_last = run_dodona(historico)
        scores_without_last = run_dodona(historico[:-1])
        self.assertNotEqual(scores_with_last, scores_without_last)

    def test_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(run_dodona).parameters)
        self.assertEqual(params, {"historico"})


if __name__ == "__main__":
    unittest.main()
