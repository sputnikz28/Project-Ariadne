"""Tests for core/services/star_contribution_trial.py. All historico
fixtures are synthetic, hand-verified — same convention as
tests/test_backtest_generators.py's Astérias fixtures, duplicated here
locally rather than imported cross-file.
"""

import random
import unittest
from dataclasses import fields
from datetime import datetime, timezone

from core.services.backtest_lab import BacktestTarget
from core.services.star_contribution_trial import (
    StarContributionPair,
    run_star_contribution_trial,
)

TARGET_A = BacktestTarget(
    draw_id="T-A/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc),
    numeros=(1, 2, 3, 4, 5), estrelas=(1, 2),
)
TARGET_B = BacktestTarget(
    draw_id="T-B/2099", draw_datetime=datetime(2099, 3, 17, 20, 0, 0, tzinfo=timezone.utc),
    numeros=(46, 47, 48, 49, 50), estrelas=(11, 12),
)


def _star_draw(estrelas):
    return {"numeros": [1, 2, 3, 4, 5], "estrelas": estrelas}


# n(P)=5 exactly at the Abissal threshold, P=(1,2) -- both lineages participate.
_RICH_HISTORICO = [
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([1, 2]), _star_draw([5, 6]),
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([7, 8]),
    _star_draw([1, 2]),
]

# Same structure, "next" stars swapped 3/4 -> 9/10 -- same participation
# pattern, different resulting star probabilities.
_RICH_HISTORICO_ALT = [
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([1, 2]), _star_draw([5, 6]),
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([7, 8]),
    _star_draw([1, 2]),
]

# P=(1,2) never occurred before -- Abissal abstains, Marés backs off.
_SPARSE_HISTORICO = [
    _star_draw([5, 6]), _star_draw([7, 8]), _star_draw([9, 10]),
    _star_draw([11, 12]), _star_draw([3, 4]), _star_draw([1, 2]),
]

# len(historico)=3 < 5 -- both lineages abstain, even Marés's backoff.
_TOO_SHORT_HISTORICO = [
    _star_draw([9, 10]), _star_draw([11, 12]), _star_draw([1, 2]),
]


def make_ctx(historico):
    return {"historico": historico}


class TestAbstention(unittest.TestCase):
    def test_abissal_abstains_returns_none(self):
        result = run_star_contribution_trial(
            make_ctx(_SPARSE_HISTORICO), TARGET_A, "abissal", 5, generator_seed=1, arena_seed=1,
        )
        self.assertIsNone(result)

    def test_mares_backs_off_and_still_participates(self):
        result = run_star_contribution_trial(
            make_ctx(_SPARSE_HISTORICO), TARGET_A, "mares", 5, generator_seed=1, arena_seed=1,
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 5)

    def test_both_lineages_abstain_when_history_too_short(self):
        for lineage in ("abissal", "mares"):
            result = run_star_contribution_trial(
                make_ctx(_TOO_SHORT_HISTORICO), TARGET_A, lineage, 5, generator_seed=1, arena_seed=1,
            )
            self.assertIsNone(result)

    def test_never_fabricates_pairs_for_an_abstaining_lineage(self):
        # quantidade > 0 but lineage abstains -- must be None, never ().
        result = run_star_contribution_trial(
            make_ctx(_SPARSE_HISTORICO), TARGET_A, "abissal", 20, generator_seed=1, arena_seed=1,
        )
        self.assertIsNone(result)


class TestNumerosSharedByConstruction(unittest.TestCase):
    def test_numeros_identical_between_acaso_and_asteria_variant(self):
        # By construction there is only one `numeros` field per pair --
        # this test documents that fact structurally: matched_numbers
        # (and therefore numeros itself) is never exposed twice.
        result = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 5, generator_seed=1, arena_seed=1,
        )
        field_names = {f.name for f in fields(StarContributionPair)}
        self.assertIn("numeros", field_names)
        self.assertNotIn("matched_numbers", field_names)

    def test_numeros_identical_across_lineages_same_target_and_seed(self):
        result_abissal = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 6, generator_seed=1, arena_seed=1,
        )
        result_mares = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 6, generator_seed=1, arena_seed=1,
        )
        numeros_abissal = [p.numeros for p in result_abissal]
        numeros_mares = [p.numeros for p in result_mares]
        self.assertEqual(numeros_abissal, numeros_mares)

    def test_numeros_never_depend_on_star_transition_data(self):
        # Same seed, two different real-shaped histories with different
        # last star pairs / probabilities -- numeros must be identical,
        # only estrelas_asteria may differ.
        result_a = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 6, generator_seed=1, arena_seed=1,
        )
        result_b = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO_ALT), TARGET_A, "abissal", 6, generator_seed=1, arena_seed=1,
        )
        self.assertEqual([p.numeros for p in result_a], [p.numeros for p in result_b])
        stars_a = [p.estrelas_asteria for p in result_a]
        stars_b = [p.estrelas_asteria for p in result_b]
        self.assertNotEqual(stars_a, stars_b, "different star histories must produce different star picks")

    def test_numeros_never_read_from_historico(self):
        # Changing historico's own "numeros" field (never used by this
        # trial) must not perturb the numeros stream at all.
        mutated = [dict(d, numeros=[46, 47, 48, 49, 50]) for d in _RICH_HISTORICO]
        result_original = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 4, generator_seed=1, arena_seed=1,
        )
        result_mutated = run_star_contribution_trial(
            make_ctx(mutated), TARGET_A, "abissal", 4, generator_seed=1, arena_seed=1,
        )
        self.assertEqual([p.numeros for p in result_original], [p.numeros for p in result_mutated])


class TestDeterminism(unittest.TestCase):
    def test_deterministic_given_same_cell(self):
        r1 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=42, arena_seed=1,
        )
        r2 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=42, arena_seed=1,
        )
        self.assertEqual(r1, r2)

    def test_different_generator_seed_changes_result(self):
        r1 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=1, arena_seed=1,
        )
        r2 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=2, arena_seed=1,
        )
        self.assertNotEqual(r1, r2)

    def test_different_arena_seed_changes_result(self):
        r1 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=1, arena_seed=1,
        )
        r2 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=1, arena_seed=2,
        )
        self.assertNotEqual(r1, r2)

    def test_different_target_changes_result(self):
        r1 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 8, generator_seed=1, arena_seed=1,
        )
        r2 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_B, "mares", 8, generator_seed=1, arena_seed=1,
        )
        self.assertNotEqual(r1, r2)

    def test_output_independent_of_global_random_state(self):
        random.seed(111)
        r1 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 6, generator_seed=7, arena_seed=1,
        )
        random.seed(999)
        r2 = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 6, generator_seed=7, arena_seed=1,
        )
        self.assertEqual(r1, r2)


class TestDirectionAndCategoryConsistency(unittest.TestCase):
    def test_direction_matches_star_count_comparison(self):
        result = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "mares", 30, generator_seed=1, arena_seed=1,
        )
        for pair in result:
            if pair.matched_stars_asteria > pair.matched_stars_acaso:
                self.assertEqual(pair.direction, "melhorou")
            elif pair.matched_stars_asteria < pair.matched_stars_acaso:
                self.assertEqual(pair.direction, "piorou")
            else:
                self.assertEqual(pair.direction, "igual")

    def test_category_reflects_matched_numbers_and_stars(self):
        result = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 10, generator_seed=1, arena_seed=1,
        )
        for pair in result:
            matched_numbers = len(set(pair.numeros) & set(TARGET_A.numeros))
            self.assertEqual(pair.category_acaso, f"{matched_numbers}+{pair.matched_stars_acaso}")
            self.assertEqual(pair.category_asteria, f"{matched_numbers}+{pair.matched_stars_asteria}")

    def test_quantidade_controls_number_of_pairs(self):
        result = run_star_contribution_trial(
            make_ctx(_RICH_HISTORICO), TARGET_A, "abissal", 13, generator_seed=1, arena_seed=1,
        )
        self.assertEqual(len(result), 13)
        self.assertEqual([p.index for p in result], list(range(13)))


if __name__ == "__main__":
    unittest.main()
