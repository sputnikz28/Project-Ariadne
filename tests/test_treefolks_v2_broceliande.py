"""Tests for core/services/treefolks_v2/broceliande.py — including the
exact bug found and fixed during review (pooled/unconditional
transition counts instead of a per-query-value average)."""

import inspect
import unittest

from core.services.treefolks_v2.broceliande import _BROCELIANDE_ALPHA, _transition_scores, run_broceliande


def _draw(numeros, estrelas):
    return {"numeros": numeros, "estrelas": estrelas}


class TestTransitionScoresAveraging(unittest.TestCase):
    def test_per_query_distributions_are_averaged_not_pooled(self):
        # q=1 occurs 3 times (i=0,2,4), each transitioning to a
        # DIFFERENT successor (10, 11, 12). q=2 occurs only once
        # (i=6), transitioning to 20. This asymmetry (3 occurrences
        # vs. 1) is exactly what distinguishes correct per-query
        # averaging from pooled/unconditional counting: averaging
        # gives q=1 and q=2 EQUAL weight in the final score regardless
        # of how many times each occurred historically; pooling would
        # let q=1's 3 raw transitions dominate over q=2's 1.
        historico = [
            {"numeros": [1]}, {"numeros": [10]},
            {"numeros": [1]}, {"numeros": [11]},
            {"numeros": [1]}, {"numeros": [12]},
            {"numeros": [2]}, {"numeros": [20]},
        ]
        universe = range(1, 21)  # {1..20}
        alpha = _BROCELIANDE_ALPHA

        scores = _transition_scores(historico, universe, "numeros", [1, 2])

        # dist_1: total_votes=3 (-> 10, 11, 12), denom=3+20*alpha.
        denom_1 = 3 + 20 * alpha
        dist_1_10 = (1 + alpha) / denom_1
        # dist_2: total_votes=1 (-> 20), denom=1+20*alpha.
        denom_2 = 1 + 20 * alpha
        dist_2_10 = (0 + alpha) / denom_2
        dist_1_20 = (0 + alpha) / denom_1
        dist_2_20 = (1 + alpha) / denom_2

        expected_10 = (dist_1_10 + dist_2_10) / 2
        expected_20 = (dist_1_20 + dist_2_20) / 2
        self.assertAlmostEqual(scores[10], expected_10)
        self.assertAlmostEqual(scores[20], expected_20)
        # The two are NOT equal -- q=2's single transition to 20 gets
        # full weight within its own (size-1) distribution, exactly
        # like each of q=1's 3 transitions gets full weight within
        # its own (size-3) distribution -- proving per-query weight
        # is equal, not per-transition weight.
        self.assertNotAlmostEqual(expected_10, expected_20)

        # The buggy pooled version (raw counts summed across queries
        # before smoothing) would instead give q=1's 3x-more-frequent
        # transitions 3x the influence of q=2's single one, making
        # pooled_10 (from a transition seen once, via q=1) equal to
        # pooled_20 (also seen once, via q=2) -- collapsing exactly
        # the asymmetry this test exists to catch.
        pooled_denom = 4 + 20 * alpha  # 1+1+1+1 raw votes pooled
        pooled_10 = (1 + alpha) / pooled_denom
        pooled_20 = (1 + alpha) / pooled_denom
        self.assertAlmostEqual(pooled_10, pooled_20)  # sanity: the bug's own symmetry
        self.assertNotAlmostEqual(scores[10], pooled_10)
        self.assertNotAlmostEqual(scores[20], pooled_20)

    def test_single_query_value_matches_its_own_distribution_exactly(self):
        historico = [{"numeros": [1]}, {"numeros": [2]}, {"numeros": [1]}, {"numeros": [3]}]
        universe = range(1, 4)
        scores = _transition_scores(historico, universe, "numeros", [1])
        total_votes = 2  # q=1 -> 2, q=1 -> 3
        denom = total_votes + 3 * _BROCELIANDE_ALPHA
        self.assertAlmostEqual(scores[2], (1 + _BROCELIANDE_ALPHA) / denom)
        self.assertAlmostEqual(scores[3], (1 + _BROCELIANDE_ALPHA) / denom)
        self.assertAlmostEqual(scores[1], (0 + _BROCELIANDE_ALPHA) / denom)


class TestLastDrawNeverUsedAsCurrent(unittest.TestCase):
    def test_last_position_never_read_as_a_current_occurrence(self):
        # A sentinel value placed ONLY in historico[-1] must never
        # contribute a transition (it would require reading past the
        # end of historico to find its "successor").
        historico = [{"numeros": [1]}, {"numeros": [2]}, {"numeros": [99]}]
        universe = range(1, 4)
        scores = _transition_scores(historico, universe, "numeros", [1])
        # If 99 (in historico[-1]) were wrongly read as "current", the
        # loop would need historico[3], which doesn't exist -- no
        # crash occurred, and specifically q=1's only real transition
        # (i=0 -> i=1) is exactly 1 vote, not query-value 99 counted.
        total_votes = 1
        denom = total_votes + 3 * _BROCELIANDE_ALPHA
        self.assertAlmostEqual(scores[2], (1 + _BROCELIANDE_ALPHA) / denom)


class TestRunBroceliande(unittest.TestCase):
    def test_abstains_when_fewer_than_two_draws(self):
        self.assertIsNone(run_broceliande([]))
        self.assertIsNone(run_broceliande([_draw([1, 2, 3, 4, 5], [1, 2])]))

    def test_participates_with_exactly_two_draws(self):
        historico = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4])]
        scores = run_broceliande(historico)
        self.assertIsNotNone(scores)
        self.assertEqual(set(scores.number_scores), set(range(1, 51)))
        self.assertEqual(set(scores.star_scores), set(range(1, 13)))

    def test_deterministic_pure_function(self):
        historico = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4]), _draw([1, 2, 3, 4, 5], [1, 2])]
        r1 = run_broceliande(historico)
        r2 = run_broceliande(historico)
        self.assertEqual(r1, r2)

    def test_query_values_come_from_the_last_draw(self):
        historico_a = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4]), _draw([1, 2, 3, 4, 5], [1, 2])]
        historico_b = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4]), _draw([11, 12, 13, 14, 15], [5, 6])]
        scores_a = run_broceliande(historico_a)
        scores_b = run_broceliande(historico_b)
        self.assertNotEqual(scores_a, scores_b)

    def test_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(run_broceliande).parameters)
        self.assertEqual(params, {"historico"})


if __name__ == "__main__":
    unittest.main()
