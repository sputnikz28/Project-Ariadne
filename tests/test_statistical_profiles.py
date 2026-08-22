"""Tests for core/services/statistical_profiles.py — pure primitives,
no I/O. Numeros/estrelas independence is checked explicitly (Commit 12
rule: no primitive is allowed to know about, or mix, the two
universes), and a set of tests run against the real 2026 dataset,
independently recomputed rather than hardcoded.
"""

import json
import unittest
from collections import Counter
from pathlib import Path

from core.services.statistical_profiles import (
    absolute_frequency,
    current_delay,
    decade_bucket,
    key_gaps,
    low_high,
    parity,
    relative_frequency,
    repeated_values,
)

REAL_2026_DATASET_PATH = Path(
    "datasets/historical/euromillions/2026/euromilhoes_2026_001_067_dataset_completo.json"
)


class TestAbsoluteFrequency(unittest.TestCase):
    def test_counts_occurrences_per_value(self):
        occurrences = [[1, 2, 3, 4, 5], [1, 2, 3, 4, 6], [1, 7, 8, 9, 10]]
        result = absolute_frequency(occurrences)
        self.assertEqual(result[1], 3)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[5], 1)

    def test_empty_input_returns_empty_counter(self):
        self.assertEqual(absolute_frequency([]), Counter())

    def test_never_seen_value_has_no_entry(self):
        result = absolute_frequency([[1, 2, 3, 4, 5]])
        self.assertNotIn(99, result)
        self.assertEqual(result.get(99, 0), 0)

    def test_does_not_mutate_input(self):
        occurrences = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
        before = [list(d) for d in occurrences]
        absolute_frequency(occurrences)
        self.assertEqual(occurrences, before)


class TestRelativeFrequency(unittest.TestCase):
    def test_normal_ratios(self):
        result = relative_frequency({1: 2, 2: 1}, total_draws=4)
        self.assertAlmostEqual(result[1], 0.5)
        self.assertAlmostEqual(result[2], 0.25)

    def test_total_draws_zero_gives_zero_for_every_present_key(self):
        result = relative_frequency({1: 5, 2: 0}, total_draws=0)
        self.assertEqual(result, {1: 0.0, 2: 0.0})

    def test_total_draws_negative_raises_value_error(self):
        with self.assertRaises(ValueError):
            relative_frequency({1: 5}, total_draws=-1)

    def test_does_not_mutate_input_mapping(self):
        absolute = {1: 2, 2: 1}
        before = dict(absolute)
        relative_frequency(absolute, total_draws=4)
        self.assertEqual(absolute, before)


class TestCurrentDelay(unittest.TestCase):
    def test_zero_when_in_most_recent_draw(self):
        occurrences = [[1, 2], [3, 4], [5, 6]]
        self.assertEqual(current_delay(occurrences, 5), 0)

    def test_n_draws_ago(self):
        occurrences = [[1, 2], [3, 4], [5, 6], [7, 8]]
        self.assertEqual(current_delay(occurrences, 1), 3)
        self.assertEqual(current_delay(occurrences, 3), 2)
        self.assertEqual(current_delay(occurrences, 5), 1)

    def test_never_appeared_is_none(self):
        occurrences = [[1, 2], [3, 4], [5, 6]]
        self.assertIsNone(current_delay(occurrences, 99))

    def test_empty_occurrences_is_none(self):
        self.assertIsNone(current_delay([], 1))

    def test_trusts_given_order_not_dates(self):
        # Deliberately "out of natural order" — the function must treat
        # the LAST element as most recent regardless of any implied date.
        occurrences = [[5, 6], [1, 2], [3, 4]]
        self.assertEqual(current_delay(occurrences, 3), 0)
        self.assertEqual(current_delay(occurrences, 5), 2)

    def test_does_not_mutate_input(self):
        occurrences = [[1, 2], [3, 4], [5, 6]]
        before = [list(d) for d in occurrences]
        current_delay(occurrences, 1)
        self.assertEqual(occurrences, before)


class TestParity(unittest.TestCase):
    def test_mixed(self):
        self.assertEqual(parity([1, 2, 3, 4, 5]), (2, 3))

    def test_all_even(self):
        self.assertEqual(parity([2, 4, 6]), (3, 0))

    def test_all_odd(self):
        self.assertEqual(parity([1, 3, 5]), (0, 3))

    def test_empty(self):
        self.assertEqual(parity([]), (0, 0))

    def test_does_not_mutate_input(self):
        numeros = [1, 2, 3, 4, 5]
        before = list(numeros)
        parity(numeros)
        self.assertEqual(numeros, before)


class TestLowHigh(unittest.TestCase):
    def test_default_threshold(self):
        self.assertEqual(low_high([1, 25, 26, 50, 12]), (3, 2))

    def test_custom_threshold(self):
        self.assertEqual(low_high([1, 5, 10, 15], threshold=10), (3, 1))

    def test_all_low(self):
        self.assertEqual(low_high([1, 2, 3]), (3, 0))

    def test_all_high(self):
        self.assertEqual(low_high([30, 40, 50]), (0, 3))

    def test_does_not_mutate_input(self):
        numeros = [1, 25, 26, 50]
        before = list(numeros)
        low_high(numeros)
        self.assertEqual(numeros, before)


class TestDecadeBucket(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(decade_bucket(1), "01-10")
        self.assertEqual(decade_bucket(10), "01-10")
        self.assertEqual(decade_bucket(11), "11-20")
        self.assertEqual(decade_bucket(20), "11-20")
        self.assertEqual(decade_bucket(21), "21-30")
        self.assertEqual(decade_bucket(30), "21-30")
        self.assertEqual(decade_bucket(31), "31-40")
        self.assertEqual(decade_bucket(40), "31-40")
        self.assertEqual(decade_bucket(41), "41-50")
        self.assertEqual(decade_bucket(50), "41-50")


class TestKeyGaps(unittest.TestCase):
    def test_five_numeros(self):
        self.assertEqual(key_gaps([12, 21, 23, 34, 40]), (9, 2, 11, 6))

    def test_two_estrelas(self):
        self.assertEqual(key_gaps([9, 10]), (1,))

    def test_empty_is_empty_tuple(self):
        self.assertEqual(key_gaps([]), ())

    def test_single_value_is_empty_tuple(self):
        self.assertEqual(key_gaps([7]), ())

    def test_sorts_unsorted_input(self):
        self.assertEqual(key_gaps([40, 12, 34, 21, 23]), (9, 2, 11, 6))

    def test_does_not_mutate_input(self):
        values = [40, 12, 34, 21, 23]
        before = list(values)
        key_gaps(values)
        self.assertEqual(values, before)


class TestRepeatedValues(unittest.TestCase):
    def test_no_overlap(self):
        self.assertEqual(repeated_values([1, 2, 3], [4, 5, 6]), ())

    def test_partial_overlap(self):
        self.assertEqual(repeated_values([1, 2, 3, 4], [3, 4, 5, 6]), (3, 4))

    def test_full_overlap(self):
        self.assertEqual(repeated_values([1, 2], [2, 1]), (1, 2))

    def test_duplicates_in_input_collapse_to_unique_sorted_output(self):
        self.assertEqual(repeated_values([1, 1, 2, 2, 3], [1, 2, 2, 2]), (1, 2))

    def test_does_not_mutate_inputs(self):
        key_a, key_b = [1, 2, 3], [2, 3, 4]
        before_a, before_b = list(key_a), list(key_b)
        repeated_values(key_a, key_b)
        self.assertEqual(key_a, before_a)
        self.assertEqual(key_b, before_b)


class TestNumerosAndEstrelasNeverMixed(unittest.TestCase):
    def test_absolute_frequency_counts_independently(self):
        # valor 5 exists in both universes (numeros 1-50, estrelas 1-12);
        # a draw where 5 appears as a numero but never as an estrela must
        # not let one count leak into the other.
        numeros_occurrences = [[5, 6, 7, 8, 9], [5, 10, 11, 12, 13]]
        estrelas_occurrences = [[1, 2], [3, 4]]
        numero_freq = absolute_frequency(numeros_occurrences)
        estrela_freq = absolute_frequency(estrelas_occurrences)
        self.assertEqual(numero_freq[5], 2)
        self.assertEqual(estrela_freq.get(5, 0), 0)

    def test_current_delay_computed_independently(self):
        numeros_occurrences = [[5, 6, 7, 8, 9], [10, 11, 12, 13, 14]]
        estrelas_occurrences = [[1, 2], [3, 4]]
        self.assertEqual(current_delay(numeros_occurrences, 5), 1)
        self.assertIsNone(current_delay(estrelas_occurrences, 5))


@unittest.skipUnless(REAL_2026_DATASET_PATH.exists(), "real 2026 dataset not present in this checkout")
class TestAgainstRealDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        cls.sorteios = data["sorteios"]
        cls.numero_occurrences = [s["chave"]["numeros"] for s in cls.sorteios]
        cls.estrela_occurrences = [s["chave"]["estrelas"] for s in cls.sorteios]

    def test_absolute_frequency_matches_independent_count(self):
        expected = Counter()
        for numeros in self.numero_occurrences:
            expected.update(numeros)
        result = absolute_frequency(self.numero_occurrences)
        self.assertEqual(result, expected)

    def test_current_delay_matches_independent_computation(self):
        # Independently recomputed here, not hardcoded: last draw's own
        # numeros must all have delay 0.
        for n in self.numero_occurrences[-1]:
            self.assertEqual(current_delay(self.numero_occurrences, n), 0)

    def test_key_gaps_matches_real_draw(self):
        first = self.sorteios[0]
        expected = tuple(first["estatisticas_chave"]["intervalos_ordenados"])
        self.assertEqual(key_gaps(first["chave"]["numeros"]), expected)


if __name__ == "__main__":
    unittest.main()
