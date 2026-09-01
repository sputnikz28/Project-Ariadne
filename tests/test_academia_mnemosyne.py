"""Tests for core/services/academia/mnemosyne.py — Academia Arcana de
Nemerion, Segunda Cátedra: Cátedra de Mnemosyne — Memória da
Frequência. Every test drives run_mnemosyne()/MNEMOSYNE_IDENTITY/the
private weight helpers directly, with plain random.Random instances —
no ctx, no registries, no filesystem.
"""

import inspect
import random
import unittest

from core.services.academia.mnemosyne import (
    MNEMOSYNE_IDENTITY,
    _laplace_weights,
    _weighted_sample_without_replacement,
    run_mnemosyne,
)


def _draw(numeros, estrelas):
    return {"numeros": list(numeros), "estrelas": list(estrelas)}


_RICH_HISTORICO = [
    _draw([1, 2, 3, 4, 5], [1, 2]),
    _draw([1, 2, 6, 7, 8], [1, 3]),
    _draw([1, 9, 10, 11, 12], [2, 4]),
    _draw([13, 14, 15, 16, 17], [5, 6]),
]


class TestMnemosyneIdentity(unittest.TestCase):
    def test_institution(self):
        self.assertEqual(MNEMOSYNE_IDENTITY.institution_id, "nemerion")
        self.assertEqual(MNEMOSYNE_IDENTITY.institution_name, "Academia Arcana de Nemerion")

    def test_classroom(self):
        self.assertEqual(MNEMOSYNE_IDENTITY.classroom_id, "catedra_mnemosyne")
        self.assertEqual(MNEMOSYNE_IDENTITY.classroom_name, "Cátedra de Mnemosyne — Memória da Frequência")

    def test_doctrine(self):
        self.assertEqual(MNEMOSYNE_IDENTITY.doctrine_id, "mnemosyne")
        self.assertEqual(MNEMOSYNE_IDENTITY.doctrine_version, "v1")


class TestLaplaceWeights(unittest.TestCase):
    def test_never_seen_value_has_weight_exactly_one(self):
        weights = _laplace_weights(_RICH_HISTORICO, lambda d: d["numeros"], range(1, 51))
        # 50 never appears in _RICH_HISTORICO
        self.assertEqual(weights[50], 1)

    def test_seen_value_has_weight_count_plus_one(self):
        weights = _laplace_weights(_RICH_HISTORICO, lambda d: d["numeros"], range(1, 51))
        # number 1 appears in 3 of the 4 draws
        self.assertEqual(weights[1], 3 + 1)

    def test_more_frequent_value_never_has_smaller_weight_than_less_frequent(self):
        weights = _laplace_weights(_RICH_HISTORICO, lambda d: d["numeros"], range(1, 51))
        # 1 appears 3x, 2 appears 2x, 50 appears 0x
        self.assertGreater(weights[1], weights[2])
        self.assertGreater(weights[2], weights[50])

    def test_all_weights_strictly_positive_even_with_sparse_historico(self):
        sparse = [_draw([1, 2, 3, 4, 5], [1, 2])]
        weights = _laplace_weights(sparse, lambda d: d["numeros"], range(1, 51))
        self.assertTrue(all(w > 0 for w in weights.values()))
        star_weights = _laplace_weights(sparse, lambda d: d["estrelas"], range(1, 13))
        self.assertTrue(all(w > 0 for w in star_weights.values()))

    def test_extreme_synthetic_case_frequent_vs_rare_weight_directly(self):
        # a deterministic, non-flaky proof: number 7 appears in every
        # draw, number 40 never appears -- assert the WEIGHT function
        # directly, never infer this from sampling counts.
        historico = [_draw([7, 1, 2, 3, 4], [1, 2]) for _ in range(20)]
        weights = _laplace_weights(historico, lambda d: d["numeros"], range(1, 51))
        self.assertEqual(weights[7], 20 + 1)
        self.assertEqual(weights[40], 1)
        self.assertGreater(weights[7], weights[40])

    def test_never_mutates_historico(self):
        historico = [_draw([1, 2, 3, 4, 5], [1, 2])]
        before = [dict(d) for d in historico]
        _laplace_weights(historico, lambda d: d["numeros"], range(1, 51))
        self.assertEqual(historico, before)


class TestWeightedSampleWithoutReplacement(unittest.TestCase):
    def test_returns_k_distinct_values(self):
        weights = {n: 1 for n in range(1, 51)}
        chosen = _weighted_sample_without_replacement(weights, range(1, 51), 5, random.Random(1))
        self.assertEqual(len(chosen), 5)
        self.assertEqual(len(set(chosen)), 5)

    def test_only_draws_from_universe(self):
        weights = {n: 1 for n in range(1, 51)}
        chosen = _weighted_sample_without_replacement(weights, range(1, 51), 5, random.Random(1))
        self.assertTrue(all(1 <= v <= 50 for v in chosen))


class TestRunMnemosyneShape(unittest.TestCase):
    def test_returns_5_unique_numbers_and_2_unique_stars(self):
        result = run_mnemosyne(_RICH_HISTORICO, random.Random(1))
        self.assertEqual(len(result.numeros), 5)
        self.assertEqual(len(set(result.numeros)), 5)
        self.assertEqual(len(result.estrelas), 2)
        self.assertEqual(len(set(result.estrelas)), 2)
        self.assertTrue(all(1 <= n <= 50 for n in result.numeros))
        self.assertTrue(all(1 <= s <= 12 for s in result.estrelas))

    def test_canonical_ascending_order(self):
        result = run_mnemosyne(_RICH_HISTORICO, random.Random(2))
        self.assertEqual(result.numeros, tuple(sorted(result.numeros)))
        self.assertEqual(result.estrelas, tuple(sorted(result.estrelas)))

    def test_deterministic_given_same_historico_and_seed(self):
        r1 = run_mnemosyne(_RICH_HISTORICO, random.Random(42))
        r2 = run_mnemosyne(_RICH_HISTORICO, random.Random(42))
        self.assertEqual(r1, r2)

    def test_different_seeds_can_give_different_results(self):
        results = {run_mnemosyne(_RICH_HISTORICO, random.Random(s)) for s in range(20)}
        self.assertGreater(len(results), 1)

    def test_never_mutates_historico(self):
        historico = [_draw([1, 2, 3, 4, 5], [1, 2]), _draw([6, 7, 8, 9, 10], [3, 4])]
        before = [dict(d) for d in historico]
        run_mnemosyne(historico, random.Random(1))
        self.assertEqual(historico, before)

    def test_empty_historico_abstains_explicitly(self):
        result = run_mnemosyne([], random.Random(1))
        self.assertIsNone(result.numeros)
        self.assertIsNone(result.estrelas)

    def test_single_draw_historico_never_crashes_and_still_produces_valid_key(self):
        result = run_mnemosyne([_draw([1, 2, 3, 4, 5], [1, 2])], random.Random(1))
        self.assertIsNotNone(result.numeros)
        self.assertEqual(len(result.numeros), 5)
        self.assertEqual(len(result.estrelas), 2)


class TestRunMnemosyneSignatureAndPurity(unittest.TestCase):
    def test_signature_is_historico_and_rng_only(self):
        params = list(inspect.signature(run_mnemosyne).parameters)
        self.assertEqual(params, ["historico", "rng"])

    def test_source_never_touches_student_enrollment_or_treefolks_vocabulary(self):
        source = inspect.getsource(run_mnemosyne).lower()
        for forbidden in (
            "student", "enrollment", "personality", "personalidade", "book", "livro",
            "registry", "treefolks", "skill", "knowledge",
        ):
            self.assertNotIn(forbidden, source)

    def test_never_uses_builtin_hash(self):
        import core.services.academia.mnemosyne as _module
        source = inspect.getsource(_module)
        self.assertNotIn("hash(", source)

    def test_never_imports_random_global_module_level_state(self):
        # confirms the module never calls the bare `random.seed`/module-
        # level random functions -- only random.Random instances passed
        # in are ever used.
        import core.services.academia.mnemosyne as _module
        source = inspect.getsource(_module)
        self.assertNotIn("random.seed(", source)
        self.assertNotIn("random.choice(", source)
        self.assertNotIn("random.sample(", source)
        self.assertNotIn("random.choices(", source)


if __name__ == "__main__":
    unittest.main()
