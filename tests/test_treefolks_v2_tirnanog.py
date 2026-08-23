"""Tests for core/services/treefolks_v2/tirnanog.py. Assumes
tests/test_treefolks_v2_common.py's VERIFIED-safety proofs for
fitness()/calculate() already pass — see that file's
TestFitnessAndCalculateVerifiedSafety, which this module's own docstring
explicitly points to."""

import inspect
import random
import unittest

from core.services.treefolks_v2.tirnanog import _ELITE_SIZE, _N_SIMULACOES, run_tirnanog


def _draw(numeros, estrelas):
    return {"numeros": numeros, "estrelas": estrelas}


_HISTORICO = [_draw([n, n + 1, n + 2, n + 3, n + 4], [(n % 12) + 1, ((n + 1) % 12) + 1]) for n in range(1, 40, 5)]


class TestFrozenHyperparameters(unittest.TestCase):
    def test_n_simulacoes_and_elite_size_match_the_approved_contract(self):
        self.assertEqual(_N_SIMULACOES, 1000)
        self.assertEqual(_ELITE_SIZE, 100)


class TestAbstention(unittest.TestCase):
    def test_abstains_on_empty_history(self):
        self.assertIsNone(run_tirnanog([], random.Random(1)))

    def test_participates_with_a_single_draw(self):
        scores = run_tirnanog([_draw([1, 2, 3, 4, 5], [1, 2])], random.Random(1))
        self.assertIsNotNone(scores)


class TestReusesRealFitnessUnmodified(unittest.TestCase):
    def test_imports_the_real_fitness_and_calculate_functions(self):
        import core.services.treefolks_v2.tirnanog as tirnanog_module
        self.assertIs(tirnanog_module.fitness, __import__("core.services.fitness", fromlist=["fitness"]).fitness)
        self.assertIs(
            tirnanog_module.calculate,
            __import__("core.evolution.statistics", fromlist=["calculate"]).calculate,
        )

    def test_no_local_reimplementation_of_fitness_scoring(self):
        import core.services.treefolks_v2.tirnanog as tirnanog_module
        source = inspect.getsource(tirnanog_module)
        # A local reimplementation would need the game's scoring
        # constants (e.g. the 110/160 sum-range check) -- their
        # absence here is evidence fitness() is genuinely reused, not
        # duplicated.
        self.assertNotIn("110", source)
        self.assertNotIn("160", source)


class TestDeterminism(unittest.TestCase):
    def test_deterministic_given_same_rng_state(self):
        r1 = run_tirnanog(_HISTORICO, random.Random(42))
        r2 = run_tirnanog(_HISTORICO, random.Random(42))
        self.assertEqual(r1, r2)

    def test_different_seed_changes_result(self):
        r1 = run_tirnanog(_HISTORICO, random.Random(1))
        r2 = run_tirnanog(_HISTORICO, random.Random(2))
        self.assertNotEqual(r1, r2)

    def test_output_independent_of_global_random_state(self):
        random.seed(111)
        r1 = run_tirnanog(_HISTORICO, random.Random(7))
        random.seed(999)
        r2 = run_tirnanog(_HISTORICO, random.Random(7))
        self.assertEqual(r1, r2)


class TestEliteAndScoring(unittest.TestCase):
    def test_scores_are_elite_frequency_fractions_never_floored(self):
        scores = run_tirnanog(_HISTORICO, random.Random(3))
        for value in list(scores.number_scores.values()) + list(scores.star_scores.values()):
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
            # Every score must be an exact multiple of 1/_ELITE_SIZE --
            # proves no floor/smoothing was added on top of the raw
            # elite-occurrence fraction.
            scaled = value * _ELITE_SIZE
            self.assertAlmostEqual(scaled, round(scaled))

    def test_tie_break_is_canonical_never_rng_order(self):
        # Two independent runs with different seeds but that happen to
        # explore the same candidate space should rank identical-
        # fitness candidates identically -- verified indirectly by
        # confirming the sort key used includes (numeros, estrelas) as
        # a deterministic secondary/tertiary key, not insertion order.
        import core.services.treefolks_v2.tirnanog as tirnanog_module
        source = inspect.getsource(tirnanog_module.run_tirnanog)
        self.assertIn("item[1]", source)
        self.assertIn("item[2]", source)

    def test_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(run_tirnanog).parameters)
        self.assertEqual(params, {"historico", "rng"})


if __name__ == "__main__":
    unittest.main()
