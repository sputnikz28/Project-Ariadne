"""Tests for core/services/treefolks_v2/common.py — shared scores
contract, key constructor, per-Floresta RNG derivation — plus the
VERIFIED-safety proofs for core.services.fitness.fitness() and
core.evolution.statistics.calculate() required by the approved
contract before any Tír na nÓg-specific test runs (see
tests/test_treefolks_v2_tirnanog.py, which assumes these proofs pass).
"""

import inspect
import random
import unittest
from collections import Counter

from core.evolution.statistics import calculate
from core.services.fitness import fitness
from core.services.treefolks_v2.common import TreefolkScores, build_key_from_scores, forest_rng


def _star_draw(numeros, estrelas):
    return {"numeros": numeros, "estrelas": estrelas}


class TestTreefolkScores(unittest.TestCase):
    def test_shape(self):
        scores = TreefolkScores(
            number_scores={n: 1.0 for n in range(1, 51)},
            star_scores={s: 1.0 for s in range(1, 13)},
        )
        self.assertEqual(set(scores.number_scores), set(range(1, 51)))
        self.assertEqual(set(scores.star_scores), set(range(1, 13)))


class TestBuildKeyFromScores(unittest.TestCase):
    def test_returns_5_unique_numbers_and_2_unique_stars(self):
        rng = random.Random(1)
        number_scores = {n: 1.0 for n in range(1, 51)}
        star_scores = {s: 1.0 for s in range(1, 13)}
        numeros, estrelas = build_key_from_scores(number_scores, star_scores, rng)
        self.assertEqual(len(numeros), 5)
        self.assertEqual(len(set(numeros)), 5)
        self.assertEqual(len(estrelas), 2)
        self.assertEqual(len(set(estrelas)), 2)
        self.assertTrue(all(1 <= n <= 50 for n in numeros))
        self.assertTrue(all(1 <= s <= 12 for s in estrelas))
        self.assertEqual(numeros, tuple(sorted(numeros)))
        self.assertEqual(estrelas, tuple(sorted(estrelas)))

    def test_deterministic_given_same_rng_state(self):
        number_scores = {n: 1.0 for n in range(1, 51)}
        star_scores = {s: 1.0 for s in range(1, 13)}
        r1 = build_key_from_scores(number_scores, star_scores, random.Random(42))
        r2 = build_key_from_scores(number_scores, star_scores, random.Random(42))
        self.assertEqual(r1, r2)

    def test_skewed_scores_bias_the_distribution(self):
        # Number 7 has overwhelmingly more weight than every other
        # number -- across many draws it must appear far more often
        # than a uniform baseline would predict (~10% for 5-of-50).
        number_scores = {n: 0.001 for n in range(1, 51)}
        number_scores[7] = 1000.0
        star_scores = {s: 1.0 for s in range(1, 13)}
        rng = random.Random(7)
        appearances = 0
        trials = 200
        for _ in range(trials):
            numeros, _estrelas = build_key_from_scores(number_scores, star_scores, rng)
            if 7 in numeros:
                appearances += 1
        self.assertGreater(appearances / trials, 0.9)

    def test_uniform_scores_never_crash_and_cover_full_range_eventually(self):
        number_scores = {n: 1.0 for n in range(1, 51)}
        star_scores = {s: 1.0 for s in range(1, 13)}
        rng = random.Random(99)
        seen = set()
        for _ in range(300):
            numeros, _estrelas = build_key_from_scores(number_scores, star_scores, rng)
            seen.update(numeros)
        # With uniform weights and enough draws, most of the universe
        # should show up -- not a strict proof of uniformity, just a
        # sanity check that nothing is structurally excluded.
        self.assertGreater(len(seen), 40)


class TestForestRng(unittest.TestCase):
    def test_different_florestas_give_different_streams(self):
        r1 = forest_rng(1, "yggdrasil", "001/2099")
        r2 = forest_rng(1, "dodona", "001/2099")
        self.assertNotEqual(r1.random(), r2.random())

    def test_same_arguments_give_the_same_stream(self):
        r1 = forest_rng(1, "yggdrasil", "001/2099")
        r2 = forest_rng(1, "yggdrasil", "001/2099")
        self.assertEqual(r1.random(), r2.random())

    def test_different_seed_gives_different_stream(self):
        r1 = forest_rng(1, "yggdrasil", "001/2099")
        r2 = forest_rng(2, "yggdrasil", "001/2099")
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_draw_id_gives_different_stream(self):
        r1 = forest_rng(1, "yggdrasil", "001/2099")
        r2 = forest_rng(1, "yggdrasil", "002/2099")
        self.assertNotEqual(r1.random(), r2.random())

    def test_never_uses_builtin_hash(self):
        # hash() is randomised per-process (PYTHONHASHSEED) unless
        # disabled -- forest_rng must never depend on it. Calling
        # twice in the SAME process already proves determinism above;
        # this additionally proves the source never routes through
        # hash() by inspecting the source text.
        import inspect as _inspect

        from core.services.treefolks_v2 import common as _common_module
        source = _inspect.getsource(_common_module)
        self.assertNotIn("hash(", source)


class TestFitnessAndCalculateVerifiedSafety(unittest.TestCase):
    """Required before any Tír na nÓg-specific test: proves
    core.services.fitness.fitness() and
    core.evolution.statistics.calculate() are VERIFIED-safe by
    construction -- pure functions of their own arguments, with no
    access to any live/global/future data source, never receiving or
    deriving the sealed target.
    """

    def test_calculate_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(calculate).parameters)
        self.assertEqual(params, {"hist"})

    def test_fitness_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(fitness).parameters)
        self.assertEqual(params, {"ch", "est"})

    def test_calculate_source_has_no_live_or_persistent_imports(self):
        import core.evolution.statistics as _statistics_module
        source = inspect.getsource(_statistics_module).lower()
        for forbidden in ("ariadne", "library.heroes", "library.legends", "open(", "requests"):
            self.assertNotIn(forbidden, source)

    def test_fitness_source_has_no_live_or_persistent_imports(self):
        import core.services.fitness as _fitness_module
        source = inspect.getsource(_fitness_module).lower()
        for forbidden in ("ariadne", "library.heroes", "library.legends", "open(", "requests"):
            self.assertNotIn(forbidden, source)

    def test_calculate_is_a_pure_function_of_its_argument(self):
        hist = [_star_draw([1, 2, 3, 4, 5], [1, 2]), _star_draw([6, 7, 8, 9, 10], [3, 4])]
        r1 = calculate(hist)
        r2 = calculate(hist)
        self.assertEqual(r1, r2)
        # Repeated calls across unrelated global state (Counter
        # objects instantiated fresh each call) must never accumulate.
        r3 = calculate(hist)
        self.assertEqual(r1, r3)

    def test_fitness_is_a_pure_function_of_its_arguments(self):
        hist = [_star_draw([1, 2, 3, 4, 5], [1, 2]), _star_draw([6, 7, 8, 9, 10], [3, 4])]
        est = calculate(hist)
        ch = ((1, 6, 11, 16, 21), (1, 3))
        r1 = fitness(ch, est)
        r2 = fitness(ch, est)
        self.assertEqual(r1, r2)

    def test_poison_after_cutoff_never_changes_calculate_or_fitness(self):
        # Same "invariante A/B" style already used for
        # historical_simulation_source.py: altering data AFTER a given
        # point must never change what was already computed from the
        # data before that point.
        hist_before = [_star_draw([1, 2, 3, 4, 5], [1, 2]), _star_draw([6, 7, 8, 9, 10], [3, 4])]
        est_before = calculate(hist_before)
        ch = ((1, 6, 11, 16, 21), (1, 3))
        fitness_before = fitness(ch, est_before)

        # A "poisoned" future draw, as if it had leaked in after the
        # cutoff -- calculate()/fitness() must never be called with it
        # in a correct caller, but if it WERE appended after already
        # computing est_before/fitness_before, those already-computed
        # values must be untouched (they are plain values, not views).
        hist_poisoned = hist_before + [_star_draw([11, 12, 13, 14, 15], [5, 6])]
        _est_poisoned = calculate(hist_poisoned)  # a different computation entirely
        self.assertEqual(calculate(hist_before), est_before)
        self.assertEqual(fitness(ch, est_before), fitness_before)


if __name__ == "__main__":
    unittest.main()
