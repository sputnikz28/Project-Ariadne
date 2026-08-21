"""Tests for core/services/candidate_evaluation.py. All targets are
synthetic — none of them is drawn from, or chosen to match, any real
historical Euromillions draw. The point of this suite is the matching/
counting/category formula itself, never a specific real result.
"""

import unittest
from types import MappingProxyType

from core.services.candidate_evaluation import (
    CandidateEvaluation,
    evaluate_candidate,
    evaluate_candidates,
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
        entity_name="Forja Negra #13",
        race=None,
        metadata=MappingProxyType({}),
    )
    fields.update(overrides)
    return CandidateKey(**fields)


class TestCategoryCombinations(unittest.TestCase):
    """Candidate is always numeros=(1,2,3,4,5), estrelas=(1,2); only the
    synthetic target varies, engineered to produce each exact count.
    """

    def setUp(self):
        self.candidate = make_candidate()

    def test_5_plus_2(self):
        result = evaluate_candidate(self.candidate, [1, 2, 3, 4, 5], [1, 2])
        self.assertEqual(result.category, "5+2")
        self.assertEqual(result.matched_number_count, 5)
        self.assertEqual(result.matched_star_count, 2)

    def test_5_plus_0(self):
        result = evaluate_candidate(self.candidate, [1, 2, 3, 4, 5], [10, 11])
        self.assertEqual(result.category, "5+0")

    def test_4_plus_2(self):
        result = evaluate_candidate(self.candidate, [1, 2, 3, 4, 20], [1, 2])
        self.assertEqual(result.category, "4+2")

    def test_4_plus_0(self):
        result = evaluate_candidate(self.candidate, [1, 2, 3, 4, 20], [10, 11])
        self.assertEqual(result.category, "4+0")

    def test_3_plus_1(self):
        result = evaluate_candidate(self.candidate, [1, 2, 3, 20, 21], [1, 10])
        self.assertEqual(result.category, "3+1")

    def test_3_plus_0(self):
        result = evaluate_candidate(self.candidate, [1, 2, 3, 20, 21], [10, 11])
        self.assertEqual(result.category, "3+0")

    def test_2_plus_2(self):
        result = evaluate_candidate(self.candidate, [1, 2, 20, 21, 22], [1, 2])
        self.assertEqual(result.category, "2+2")

    def test_2_plus_0(self):
        result = evaluate_candidate(self.candidate, [1, 2, 20, 21, 22], [10, 11])
        self.assertEqual(result.category, "2+0")

    def test_1_plus_2(self):
        result = evaluate_candidate(self.candidate, [1, 20, 21, 22, 23], [1, 2])
        self.assertEqual(result.category, "1+2")

    def test_1_plus_0(self):
        result = evaluate_candidate(self.candidate, [1, 20, 21, 22, 23], [10, 11])
        self.assertEqual(result.category, "1+0")

    def test_0_plus_2(self):
        result = evaluate_candidate(self.candidate, [20, 21, 22, 23, 24], [1, 2])
        self.assertEqual(result.category, "0+2")

    def test_0_plus_0(self):
        result = evaluate_candidate(self.candidate, [20, 21, 22, 23, 24], [10, 11])
        self.assertEqual(result.category, "0+0")

    def test_low_categories_not_restricted_by_heroes_config(self):
        # "0+0"/"1+0"/"0+2"/"2+0" are not in [HEROIS].categorias by
        # default, but must still be valid, unrestricted results here.
        for target_n, target_e, expected in (
            ([20, 21, 22, 23, 24], [10, 11], "0+0"),
            ([1, 20, 21, 22, 23], [10, 11], "1+0"),
            ([20, 21, 22, 23, 24], [1, 2], "0+2"),
            ([1, 2, 20, 21, 22], [10, 11], "2+0"),
        ):
            with self.subTest(expected=expected):
                result = evaluate_candidate(self.candidate, target_n, target_e)
                self.assertEqual(result.category, expected)
                self.assertIsInstance(result, CandidateEvaluation)


class TestMatchedValuesOrderingAndDeduplication(unittest.TestCase):
    def test_matched_numbers_are_sorted_regardless_of_input_order(self):
        candidate = make_candidate(numeros=(5, 3, 1, 4, 2), estrelas=(2, 1))
        result = evaluate_candidate(candidate, [4, 1, 5, 30, 31], [2, 9])
        self.assertEqual(result.matched_numbers, (1, 4, 5))
        self.assertEqual(result.matched_stars, (2,))

    def test_duplicates_in_candidate_do_not_inflate_matches(self):
        candidate = make_candidate(numeros=(1, 1, 2, 2, 3), estrelas=(1, 1))
        result = evaluate_candidate(candidate, [1, 2, 3, 4, 5], [1, 2])
        self.assertEqual(result.matched_numbers, (1, 2, 3))
        self.assertEqual(result.matched_number_count, 3)
        self.assertEqual(result.matched_stars, (1,))
        self.assertEqual(result.matched_star_count, 1)

    def test_duplicates_in_target_do_not_inflate_matches(self):
        candidate = make_candidate(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = evaluate_candidate(candidate, [1, 1, 1, 2, 2], [1, 1])
        self.assertEqual(result.matched_numbers, (1, 2))
        self.assertEqual(result.matched_number_count, 2)
        self.assertEqual(result.matched_stars, (1,))


class TestNumerosAndEstrelasNeverMixed(unittest.TestCase):
    def test_value_shared_across_universes_does_not_cross_match(self):
        # valor 5 is a candidate numero and, separately, a target
        # estrela — must never count as a star match, and valor 1 is a
        # candidate estrela and a target numero — must never count as a
        # number match.
        candidate = make_candidate(numeros=(5, 6, 7, 8, 9), estrelas=(1, 2))
        result = evaluate_candidate(candidate, target_numeros=[1, 10, 11, 12, 13], target_estrelas=[5, 9])
        self.assertEqual(result.matched_numbers, ())
        self.assertEqual(result.matched_stars, ())
        self.assertEqual(result.category, "0+0")


class TestEmptyInputs(unittest.TestCase):
    def test_candidate_with_no_numeros_or_estrelas(self):
        candidate = make_candidate(numeros=(), estrelas=())
        result = evaluate_candidate(candidate, [1, 2, 3, 4, 5], [1, 2])
        self.assertEqual(result.matched_numbers, ())
        self.assertEqual(result.matched_stars, ())
        self.assertEqual(result.category, "0+0")

    def test_empty_target(self):
        candidate = make_candidate()
        result = evaluate_candidate(candidate, [], [])
        self.assertEqual(result.matched_numbers, ())
        self.assertEqual(result.matched_stars, ())
        self.assertEqual(result.category, "0+0")

    def test_both_empty(self):
        candidate = make_candidate(numeros=(), estrelas=())
        result = evaluate_candidate(candidate, [], [])
        self.assertEqual(result.category, "0+0")


class TestNoMutation(unittest.TestCase):
    def test_candidate_fields_unchanged_after_evaluation(self):
        candidate = make_candidate()
        before_numeros, before_estrelas = candidate.numeros, candidate.estrelas
        evaluate_candidate(candidate, [1, 2, 3, 4, 5], [1, 2])
        self.assertEqual(candidate.numeros, before_numeros)
        self.assertEqual(candidate.estrelas, before_estrelas)

    def test_target_lists_not_mutated(self):
        candidate = make_candidate()
        target_numeros = [1, 2, 30, 31, 32]
        target_estrelas = [1, 9]
        before_n, before_e = list(target_numeros), list(target_estrelas)
        evaluate_candidate(candidate, target_numeros, target_estrelas)
        self.assertEqual(target_numeros, before_n)
        self.assertEqual(target_estrelas, before_e)

    def test_evaluation_result_is_frozen(self):
        result = evaluate_candidate(make_candidate(), [1, 2, 3, 4, 5], [1, 2])
        with self.assertRaises(Exception):
            result.category = "9+9"


class TestEvaluateCandidatesPreservesOrder(unittest.TestCase):
    def test_order_and_correctness(self):
        candidates = (
            make_candidate(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2), entity_name="A"),
            make_candidate(numeros=(20, 21, 22, 23, 24), estrelas=(10, 11), entity_name="B"),
            make_candidate(numeros=(1, 2, 3, 20, 21), estrelas=(1, 10), entity_name="C"),
        )
        results = evaluate_candidates(candidates, [1, 2, 3, 4, 5], [1, 2])

        self.assertIsInstance(results, tuple)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].category, "5+2")   # A
        self.assertEqual(results[1].category, "0+0")   # B
        self.assertEqual(results[2].category, "3+1")   # C

    def test_empty_candidates_returns_empty_tuple(self):
        self.assertEqual(evaluate_candidates((), [1, 2, 3, 4, 5], [1, 2]), ())

    def test_does_not_mutate_candidates_sequence_or_targets(self):
        candidates = [make_candidate(), make_candidate(numeros=(6, 7, 8, 9, 10))]
        before = list(candidates)
        target_numeros, target_estrelas = [1, 2, 3, 4, 5], [1, 2]
        evaluate_candidates(candidates, target_numeros, target_estrelas)
        self.assertEqual(candidates, before)
        self.assertEqual(target_numeros, [1, 2, 3, 4, 5])
        self.assertEqual(target_estrelas, [1, 2])


if __name__ == "__main__":
    unittest.main()
