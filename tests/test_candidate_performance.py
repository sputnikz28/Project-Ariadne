"""Tests for core/services/candidate_performance.py. All fixtures are
synthetic — no dataset, no real draw, no [HEROIS] involved. Evaluations
are hand-built to match Commit 17's CandidateEvaluation contract
directly (category is accepted verbatim, never recomputed here).
"""

import unittest
from types import MappingProxyType

from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_performance import (
    CandidatePerformanceSummary,
    summarize_candidate_performance,
)
from core.services.candidate_provenance import CandidateKey


def make_candidate(**overrides):
    fields = dict(
        source_type="external_generator",
        source_name="cla_anao",
        numeros=(1, 2, 3, 4, 5),
        estrelas=(1, 2),
        generation=None,
        entity_id=None,
        entity_name="Forja Negra #1",
        race=None,
        metadata=MappingProxyType({}),
    )
    fields.update(overrides)
    return CandidateKey(**fields)


def make_evaluation(category, matched_numbers=(), matched_stars=()):
    n, e = (int(x) for x in category.split("+"))
    return CandidateEvaluation(
        matched_numbers=tuple(matched_numbers),
        matched_stars=tuple(matched_stars),
        matched_number_count=n,
        matched_star_count=e,
        category=category,
    )


class TestBasicCounts(unittest.TestCase):
    def test_total_candidates(self):
        candidates = [make_candidate(), make_candidate(numeros=(6, 7, 8, 9, 10))]
        evaluations = [make_evaluation("0+0"), make_evaluation("1+0")]
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.total_candidates, 2)

    def test_length_mismatch_raises_value_error(self):
        candidates = [make_candidate()]
        evaluations = [make_evaluation("0+0"), make_evaluation("1+0")]
        with self.assertRaises(ValueError):
            summarize_candidate_performance(candidates, evaluations, relevant_categories=())

    def test_empty_input_all_rates_zero_no_error(self):
        result = summarize_candidate_performance([], [], relevant_categories=("3+1",))
        self.assertEqual(result.total_candidates, 0)
        self.assertEqual(result.unique_full_keys, 0)
        self.assertEqual(result.unique_number_sets, 0)
        self.assertEqual(result.duplicate_count, 0)
        self.assertEqual(result.full_key_diversity_rate, 0.0)
        self.assertEqual(result.number_set_diversity_rate, 0.0)
        self.assertEqual(result.relevant_count, 0)
        self.assertEqual(result.relevant_rate, 0.0)


class TestDiversity(unittest.TestCase):
    def test_identical_full_keys_count_as_one_unique(self):
        candidates = [make_candidate(), make_candidate()]  # same numeros/estrelas
        evaluations = [make_evaluation("0+0"), make_evaluation("0+0")]
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.unique_full_keys, 1)
        self.assertEqual(result.duplicate_count, 1)
        self.assertAlmostEqual(result.full_key_diversity_rate, 0.5)

    def test_same_numeros_stored_in_different_order_count_as_one_unique(self):
        # this is the frozenset-vs-tuple distinction: same set of
        # numbers, different internal list order — must not be
        # miscounted as two distinct keys.
        candidates = [
            make_candidate(numeros=(1, 2, 3, 4, 5)),
            make_candidate(numeros=(5, 4, 3, 2, 1)),
        ]
        evaluations = [make_evaluation("0+0"), make_evaluation("0+0")]
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.unique_full_keys, 1)

    def test_same_numeros_different_estrelas_are_distinct_full_keys_but_one_number_set(self):
        candidates = [
            make_candidate(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2)),
            make_candidate(numeros=(1, 2, 3, 4, 5), estrelas=(3, 4)),
        ]
        evaluations = [make_evaluation("0+0"), make_evaluation("0+0")]
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.unique_full_keys, 2)
        self.assertEqual(result.unique_number_sets, 1)

    def test_all_unique_gives_diversity_rate_one(self):
        candidates = [
            make_candidate(numeros=(1, 2, 3, 4, 5)),
            make_candidate(numeros=(6, 7, 8, 9, 10)),
            make_candidate(numeros=(11, 12, 13, 14, 15)),
        ]
        evaluations = [make_evaluation("0+0")] * 3
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.full_key_diversity_rate, 1.0)
        self.assertEqual(result.number_set_diversity_rate, 1.0)
        self.assertEqual(result.duplicate_count, 0)


class TestCategoryCounts(unittest.TestCase):
    def test_all_18_categories_always_present(self):
        result = summarize_candidate_performance(
            [make_candidate()], [make_evaluation("0+0")], relevant_categories=(),
        )
        self.assertEqual(len(result.category_counts), 18)
        for n in range(6):
            for e in range(3):
                self.assertIn(f"{n}+{e}", result.category_counts)

    def test_unobserved_categories_are_zero(self):
        result = summarize_candidate_performance(
            [make_candidate()], [make_evaluation("5+2")], relevant_categories=(),
        )
        self.assertEqual(result.category_counts["5+2"], 1)
        self.assertEqual(result.category_counts["0+0"], 0)
        self.assertEqual(result.category_counts["3+1"], 0)

    def test_counts_multiple_occurrences_of_same_category(self):
        candidates = [make_candidate(numeros=(i, i + 1, i + 2, i + 3, i + 4)) for i in range(1, 4)]
        evaluations = [make_evaluation("2+1"), make_evaluation("2+1"), make_evaluation("0+0")]
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.category_counts["2+1"], 2)
        self.assertEqual(result.category_counts["0+0"], 1)

    def test_category_accepted_verbatim_never_recomputed_from_candidate(self):
        # deliberately inconsistent: candidate's actual numeros bear no
        # relation to the evaluation's category — this module must not
        # try to recompute/validate it, only count it.
        candidate = make_candidate(numeros=(40, 41, 42, 43, 44), estrelas=(11, 12))
        evaluation = make_evaluation("5+2")
        result = summarize_candidate_performance([candidate], [evaluation], relevant_categories=())
        self.assertEqual(result.category_counts["5+2"], 1)


class TestRelevantRate(unittest.TestCase):
    def test_empty_relevant_categories_means_nothing_is_relevant(self):
        evaluations = [make_evaluation("5+2"), make_evaluation("4+1")]
        candidates = [make_candidate(), make_candidate()]
        result = summarize_candidate_performance(candidates, evaluations, relevant_categories=())
        self.assertEqual(result.relevant_count, 0)
        self.assertEqual(result.relevant_rate, 0.0)

    def test_partial_relevant_categories(self):
        candidates = [make_candidate() for _ in range(4)]
        evaluations = [
            make_evaluation("2+0"), make_evaluation("1+2"),
            make_evaluation("0+0"), make_evaluation("2+0"),
        ]
        result = summarize_candidate_performance(
            candidates, evaluations, relevant_categories=("2+0", "1+2"),
        )
        self.assertEqual(result.relevant_count, 3)
        self.assertAlmostEqual(result.relevant_rate, 0.75)

    def test_all_relevant(self):
        candidates = [make_candidate(), make_candidate()]
        evaluations = [make_evaluation("0+0"), make_evaluation("1+0")]
        result = summarize_candidate_performance(
            candidates, evaluations, relevant_categories=("0+0", "1+0"),
        )
        self.assertEqual(result.relevant_rate, 1.0)


class TestNoMutation(unittest.TestCase):
    def test_candidates_and_evaluations_lists_unchanged(self):
        candidates = [make_candidate(), make_candidate(numeros=(6, 7, 8, 9, 10))]
        evaluations = [make_evaluation("0+0"), make_evaluation("1+0")]
        before_candidates = list(candidates)
        before_evaluations = list(evaluations)
        summarize_candidate_performance(candidates, evaluations, relevant_categories=("1+0",))
        self.assertEqual(candidates, before_candidates)
        self.assertEqual(evaluations, before_evaluations)

    def test_candidate_key_fields_unchanged(self):
        candidate = make_candidate()
        before_numeros, before_estrelas = candidate.numeros, candidate.estrelas
        summarize_candidate_performance([candidate], [make_evaluation("0+0")], relevant_categories=())
        self.assertEqual(candidate.numeros, before_numeros)
        self.assertEqual(candidate.estrelas, before_estrelas)

    def test_summary_is_frozen(self):
        result = summarize_candidate_performance(
            [make_candidate()], [make_evaluation("0+0")], relevant_categories=(),
        )
        with self.assertRaises(Exception):
            result.total_candidates = 999


class TestContractShape(unittest.TestCase):
    def test_no_best_category_field_exists(self):
        result = summarize_candidate_performance(
            [make_candidate()], [make_evaluation("5+2")], relevant_categories=(),
        )
        self.assertFalse(hasattr(result, "best_category"))

    def test_no_grouping_fields_exist(self):
        result = summarize_candidate_performance(
            [make_candidate()], [make_evaluation("0+0")], relevant_categories=(),
        )
        for forbidden in ("by_source_name", "by_source_type", "by_race", "by_generation"):
            self.assertFalse(hasattr(result, forbidden))

    def test_returns_the_documented_dataclass(self):
        result = summarize_candidate_performance(
            [make_candidate()], [make_evaluation("0+0")], relevant_categories=(),
        )
        self.assertIsInstance(result, CandidatePerformanceSummary)


if __name__ == "__main__":
    unittest.main()
