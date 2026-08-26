"""Tests for core/services/academia/tyche.py — Academia Arcana de
Nemerion Foundation V1, commit 4/5: Cátedra de Tyche as pure control.
Every test drives only run_tyche()/TYCHE_IDENTITY directly, with a
plain random.Random — no ctx, no registries, no filesystem.
"""

import inspect
import random
import unittest

from core.services.academia.tyche import TYCHE_IDENTITY, run_tyche


class TestTycheIdentity(unittest.TestCase):
    def test_institution(self):
        self.assertEqual(TYCHE_IDENTITY.institution_id, "nemerion")
        self.assertEqual(TYCHE_IDENTITY.institution_name, "Academia Arcana de Nemerion")

    def test_classroom(self):
        self.assertEqual(TYCHE_IDENTITY.classroom_id, "catedra_tyche")
        self.assertEqual(TYCHE_IDENTITY.classroom_name, "Cátedra de Tyche — Fundamentos do Acaso")

    def test_doctrine(self):
        self.assertEqual(TYCHE_IDENTITY.doctrine_id, "tyche")
        self.assertEqual(TYCHE_IDENTITY.doctrine_version, "v1")


class TestRunTycheShape(unittest.TestCase):
    def test_returns_5_unique_numbers_and_2_unique_stars(self):
        rng = random.Random(1)
        result = run_tyche(rng)
        self.assertEqual(len(result.numeros), 5)
        self.assertEqual(len(set(result.numeros)), 5)
        self.assertEqual(len(result.estrelas), 2)
        self.assertEqual(len(set(result.estrelas)), 2)
        self.assertTrue(all(1 <= n <= 50 for n in result.numeros))
        self.assertTrue(all(1 <= s <= 12 for s in result.estrelas))

    def test_canonical_ascending_order(self):
        rng = random.Random(2)
        result = run_tyche(rng)
        self.assertEqual(result.numeros, tuple(sorted(result.numeros)))
        self.assertEqual(result.estrelas, tuple(sorted(result.estrelas)))

    def test_never_abstains(self):
        for seed in range(50):
            result = run_tyche(random.Random(seed))
            self.assertIsNotNone(result.numeros)
            self.assertIsNotNone(result.estrelas)

    def test_deterministic_given_same_rng_state(self):
        r1 = run_tyche(random.Random(42))
        r2 = run_tyche(random.Random(42))
        self.assertEqual(r1, r2)

    def test_different_rng_state_usually_gives_different_result(self):
        r1 = run_tyche(random.Random(1))
        r2 = run_tyche(random.Random(2))
        self.assertNotEqual((r1.numeros, r1.estrelas), (r2.numeros, r2.estrelas))

    def test_uniform_coverage_over_many_draws(self):
        rng = random.Random(99)
        seen_numbers = set()
        seen_stars = set()
        for _ in range(300):
            result = run_tyche(rng)
            seen_numbers.update(result.numeros)
            seen_stars.update(result.estrelas)
        self.assertGreater(len(seen_numbers), 40)
        self.assertEqual(seen_stars, set(range(1, 13)))


class TestRunTycheSignatureAndPurity(unittest.TestCase):
    def test_signature_is_rng_only(self):
        params = list(inspect.signature(run_tyche).parameters)
        self.assertEqual(params, ["rng"])

    def test_source_never_touches_history_knowledge_or_personality_vocabulary(self):
        # Inspects only run_tyche()'s own body -- the module docstring
        # legitimately discusses "historico" while explaining why the
        # function doesn't take one; the function body itself must not.
        source = inspect.getsource(run_tyche).lower()
        for forbidden in ("historico", "ctx[", "student", "enrollment", "personality", "personalidade", "book", "livro", "registry"):
            self.assertNotIn(forbidden, source)

    def test_never_uses_builtin_hash(self):
        import core.services.academia.tyche as _tyche_module
        source = inspect.getsource(_tyche_module)
        self.assertNotIn("hash(", source)


if __name__ == "__main__":
    unittest.main()
