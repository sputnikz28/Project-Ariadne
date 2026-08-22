"""Tests for core/services/statistical_window_profile.py. The point of
this suite is not just "does the profile produce plausible numbers" but
"is every field genuinely derived from the Commit 12 primitives" — most
tests recompute the expected value via an independent, direct call to
absolute_frequency/relative_frequency/current_delay/parity/low_high/
decade_bucket/key_gaps/repeated_values and compare, rather than
hardcoding an expected result that could coincidentally match a broken
implementation.
"""

import json
import unittest
from collections import Counter
from datetime import date
from pathlib import Path
from types import MappingProxyType

from core.services.rolling_windows import TUESDAY, last_n_draws, last_n_draws_on_weekday
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
from core.services.statistical_window_profile import (
    StatisticalWindowProfile,
    build_statistical_window_profile,
)

REAL_2026_DATASET_PATH = Path(
    "datasets/historical/euromillions/2026/euromilhoes_2026_001_067_dataset_completo.json"
)


def make_sorteio(numero_sorteio, data, numeros, estrelas):
    return {
        "numero_sorteio": numero_sorteio,
        "data": data,
        "dia_semana": "?",
        "chave": {"numeros": numeros, "estrelas": estrelas},
    }


def make_sorteios():
    return [
        make_sorteio("001/2026", "2026-01-06", [1, 2, 3, 4, 5], [1, 2]),
        make_sorteio("002/2026", "2026-01-13", [1, 6, 7, 8, 9], [1, 3]),
        make_sorteio("003/2026", "2026-01-20", [10, 11, 12, 13, 14], [4, 5]),
    ]


class TestFrequencies(unittest.TestCase):
    def setUp(self):
        self.sorteios = make_sorteios()
        self.window = last_n_draws(self.sorteios, 3)
        self.profile = build_statistical_window_profile(self.window)

    def test_numero_frequencies_match_independent_absolute_and_relative_frequency(self):
        expected_abs = absolute_frequency(self.window.numero_occurrences)
        expected_rel = relative_frequency(expected_abs, self.window.actual_size)
        for n in range(1, 51):
            self.assertEqual(self.profile.numero_absolute_frequencies[n], expected_abs.get(n, 0))
            self.assertAlmostEqual(self.profile.numero_relative_frequencies[n], expected_rel.get(n, 0.0))

    def test_estrela_frequencies_match_independent_absolute_and_relative_frequency(self):
        expected_abs = absolute_frequency(self.window.estrela_occurrences)
        expected_rel = relative_frequency(expected_abs, self.window.actual_size)
        for e in range(1, 13):
            self.assertEqual(self.profile.estrela_absolute_frequencies[e], expected_abs.get(e, 0))
            self.assertAlmostEqual(self.profile.estrela_relative_frequencies[e], expected_rel.get(e, 0.0))

    def test_full_universe_present_with_zero_for_unobserved(self):
        self.assertEqual(len(self.profile.numero_absolute_frequencies), 50)
        self.assertEqual(len(self.profile.estrela_absolute_frequencies), 12)
        self.assertEqual(self.profile.numero_absolute_frequencies[50], 0)
        self.assertEqual(self.profile.numero_relative_frequencies[50], 0.0)
        self.assertEqual(self.profile.estrela_absolute_frequencies[12], 0)
        self.assertEqual(self.profile.estrela_relative_frequencies[12], 0.0)


class TestDelays(unittest.TestCase):
    def setUp(self):
        self.sorteios = make_sorteios()
        self.window = last_n_draws(self.sorteios, 3)
        self.profile = build_statistical_window_profile(self.window)

    def test_numero_delays_match_independent_current_delay_calls(self):
        for n in (1, 10, 6, 50):  # 50 is a valid-universe value never observed in this window
            expected = current_delay(self.window.numero_occurrences, n)
            self.assertEqual(self.profile.numero_delays[n], expected)

    def test_estrela_delays_match_independent_current_delay_calls(self):
        for e in (1, 4, 12):
            expected = current_delay(self.window.estrela_occurrences, e)
            self.assertEqual(self.profile.estrela_delays[e], expected)

    def test_delay_is_none_for_value_never_in_window(self):
        self.assertIsNone(self.profile.numero_delays[50])
        self.assertIsNone(self.profile.estrela_delays[12])

    def test_delays_are_window_scoped_not_global_history(self):
        # value 1 appears in the FULL sorteios list's draw 001/2026, but
        # a window of only the LAST draw must not "see" it at all.
        narrow_window = last_n_draws(self.sorteios, 1)
        narrow_profile = build_statistical_window_profile(narrow_window)
        self.assertIsNone(narrow_profile.numero_delays[1])
        # confirm it's genuinely scoped to narrow_window, not silently
        # falling back to the full sorteios list:
        expected = current_delay(narrow_window.numero_occurrences, 1)
        self.assertEqual(narrow_profile.numero_delays[1], expected)
        self.assertIsNone(expected)


class TestParityAndLowHighByDraw(unittest.TestCase):
    def setUp(self):
        self.sorteios = make_sorteios()
        self.window = last_n_draws(self.sorteios, 3)
        self.profile = build_statistical_window_profile(self.window)

    def test_parity_by_draw_matches_independent_parity_calls(self):
        expected = tuple(parity(draw) for draw in self.window.numero_occurrences)
        self.assertEqual(self.profile.parity_by_draw, expected)

    def test_low_high_by_draw_matches_independent_low_high_calls(self):
        expected = tuple(low_high(draw) for draw in self.window.numero_occurrences)
        self.assertEqual(self.profile.low_high_by_draw, expected)

    def test_aligned_index_for_index_with_window_draws(self):
        self.assertEqual(len(self.profile.parity_by_draw), self.window.actual_size)
        self.assertEqual(len(self.profile.low_high_by_draw), self.window.actual_size)
        self.assertEqual(self.profile.parity_by_draw[2], parity(self.window.numero_occurrences[2]))


class TestDecadeDistribution(unittest.TestCase):
    def test_matches_independent_decade_bucket_aggregation(self):
        sorteios = make_sorteios()
        window = last_n_draws(sorteios, 3)
        profile = build_statistical_window_profile(window)

        expected = Counter()
        for draw in window.numero_occurrences:
            for n in draw:
                expected[decade_bucket(n)] += 1

        for bucket in ("01-10", "11-20", "21-30", "31-40", "41-50"):
            self.assertEqual(profile.decade_distribution[bucket], expected.get(bucket, 0))

    def test_never_includes_estrelas(self):
        # a window whose estrelas would, if wrongly bucketed as numeros,
        # land in "01-10" — must not affect the count.
        sorteios = [make_sorteio("001/2026", "2026-01-06", [11, 12, 13, 14, 15], [1, 2])]
        window = last_n_draws(sorteios, 1)
        profile = build_statistical_window_profile(window)
        self.assertEqual(profile.decade_distribution["01-10"], 0)
        self.assertEqual(profile.decade_distribution["11-20"], 5)


class TestGapsByDraw(unittest.TestCase):
    def setUp(self):
        self.sorteios = make_sorteios()
        self.window = last_n_draws(self.sorteios, 3)
        self.profile = build_statistical_window_profile(self.window)

    def test_numero_gaps_match_independent_key_gaps_calls(self):
        expected = tuple(key_gaps(draw) for draw in self.window.numero_occurrences)
        self.assertEqual(self.profile.numero_gaps_by_draw, expected)

    def test_estrela_gaps_match_independent_key_gaps_calls(self):
        expected = tuple(key_gaps(draw) for draw in self.window.estrela_occurrences)
        self.assertEqual(self.profile.estrela_gaps_by_draw, expected)


class TestRepeatedBetweenDraws(unittest.TestCase):
    def test_matches_independent_repeated_values_calls(self):
        sorteios = make_sorteios()
        window = last_n_draws(sorteios, 3)
        profile = build_statistical_window_profile(window)

        expected_numeros = tuple(
            repeated_values(window.numero_occurrences[i + 1], window.numero_occurrences[i])
            for i in range(window.actual_size - 1)
        )
        expected_estrelas = tuple(
            repeated_values(window.estrela_occurrences[i + 1], window.estrela_occurrences[i])
            for i in range(window.actual_size - 1)
        )
        self.assertEqual(profile.repeated_numeros_between_draws, expected_numeros)
        self.assertEqual(profile.repeated_estrelas_between_draws, expected_estrelas)
        # sanity: draws 001 and 002 share numero 1 and estrela 1
        self.assertEqual(profile.repeated_numeros_between_draws[0], (1,))
        self.assertEqual(profile.repeated_estrelas_between_draws[0], (1,))

    def test_length_is_actual_size_minus_one(self):
        sorteios = make_sorteios()
        window = last_n_draws(sorteios, 3)
        profile = build_statistical_window_profile(window)
        self.assertEqual(len(profile.repeated_numeros_between_draws), window.actual_size - 1)
        self.assertEqual(len(profile.repeated_estrelas_between_draws), window.actual_size - 1)


class TestEmptyAndSingleDrawWindows(unittest.TestCase):
    def test_empty_window_full_universe_zero_and_empty_collections(self):
        window = last_n_draws([], 5)
        profile = build_statistical_window_profile(window)

        self.assertEqual(profile.actual_size, 0)
        self.assertEqual(profile.requested_size, 5)
        self.assertTrue(all(v == 0 for v in profile.numero_absolute_frequencies.values()))
        self.assertTrue(all(v == 0.0 for v in profile.numero_relative_frequencies.values()))
        self.assertTrue(all(v == 0 for v in profile.estrela_absolute_frequencies.values()))
        self.assertTrue(all(v is None for v in profile.numero_delays.values()))
        self.assertTrue(all(v is None for v in profile.estrela_delays.values()))
        self.assertEqual(profile.parity_by_draw, ())
        self.assertEqual(profile.low_high_by_draw, ())
        self.assertEqual(profile.numero_gaps_by_draw, ())
        self.assertEqual(profile.estrela_gaps_by_draw, ())
        self.assertEqual(profile.repeated_numeros_between_draws, ())
        self.assertEqual(profile.repeated_estrelas_between_draws, ())
        self.assertTrue(all(v == 0 for v in profile.decade_distribution.values()))

    def test_single_draw_window_repeated_is_empty_but_other_fields_populated(self):
        sorteios = make_sorteios()[:1]
        window = last_n_draws(sorteios, 1)
        profile = build_statistical_window_profile(window)

        self.assertEqual(profile.actual_size, 1)
        self.assertEqual(profile.repeated_numeros_between_draws, ())
        self.assertEqual(profile.repeated_estrelas_between_draws, ())
        self.assertEqual(len(profile.parity_by_draw), 1)
        self.assertEqual(profile.parity_by_draw[0], parity(window.numero_occurrences[0]))


class TestPartialWindow(unittest.TestCase):
    def test_uses_actual_size_and_keeps_requested_size_as_metadata_only(self):
        sorteios = make_sorteios()  # only 3 draws available
        window = last_n_draws(sorteios, 10)  # asked for 10
        profile = build_statistical_window_profile(window)

        self.assertEqual(profile.requested_size, 10)
        self.assertEqual(profile.actual_size, 3)
        self.assertEqual(len(profile.parity_by_draw), 3)  # driven by actual_size, not requested_size
        expected_abs = absolute_frequency(window.numero_occurrences)
        self.assertEqual(profile.numero_absolute_frequencies[1], expected_abs.get(1, 0))


class TestNumerosAndEstrelasNeverMixed(unittest.TestCase):
    def test_frequencies_delays_and_gaps_independent_for_shared_value(self):
        # valor 5 exists in both universes; a draw with numero 5 twice
        # and estrela 5 never must not let one leak into the other.
        sorteios = [
            make_sorteio("001/2026", "2026-01-06", [5, 6, 7, 8, 9], [1, 2]),
            make_sorteio("002/2026", "2026-01-13", [5, 10, 11, 12, 13], [3, 4]),
        ]
        window = last_n_draws(sorteios, 2)
        profile = build_statistical_window_profile(window)

        self.assertEqual(profile.numero_absolute_frequencies[5], 2)
        self.assertEqual(profile.estrela_absolute_frequencies[5], 0)
        self.assertEqual(profile.numero_delays[5], 0)
        self.assertIsNone(profile.estrela_delays[5])


class TestImmutability(unittest.TestCase):
    def setUp(self):
        self.sorteios = make_sorteios()
        self.window = last_n_draws(self.sorteios, 3)

    def test_does_not_mutate_window_or_source_sorteios(self):
        before_sorteios = json.loads(json.dumps(self.sorteios))
        before_window_draws = self.window.draws
        build_statistical_window_profile(self.window)
        self.assertEqual(self.sorteios, before_sorteios)
        self.assertEqual(self.window.draws, before_window_draws)

    def test_mapping_fields_are_read_only(self):
        profile = build_statistical_window_profile(self.window)
        self.assertIsInstance(profile.numero_absolute_frequencies, MappingProxyType)
        self.assertIsInstance(profile.numero_delays, MappingProxyType)
        self.assertIsInstance(profile.decade_distribution, MappingProxyType)
        with self.assertRaises(TypeError):
            profile.numero_absolute_frequencies[1] = 999

    def test_profile_dataclass_itself_is_frozen(self):
        profile = build_statistical_window_profile(self.window)
        with self.assertRaises(Exception):
            profile.actual_size = 999


@unittest.skipUnless(REAL_2026_DATASET_PATH.exists(), "real 2026 dataset not present in this checkout")
class TestAgainstRealDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        cls.sorteios = data["sorteios"]
        cls.window = last_n_draws_on_weekday(cls.sorteios, TUESDAY, 5)
        cls.profile = build_statistical_window_profile(cls.window)

    def test_window_is_real_tuesdays_only(self):
        for draw in self.window.draws:
            self.assertEqual(date.fromisoformat(draw["data"]).weekday(), TUESDAY)

    def test_numero_frequencies_match_independent_recount_over_the_window(self):
        expected = Counter()
        for numeros in self.window.numero_occurrences:
            expected.update(numeros)
        for n in range(1, 51):
            self.assertEqual(self.profile.numero_absolute_frequencies[n], expected.get(n, 0))

    def test_delay_zero_for_values_in_windows_own_last_draw(self):
        last_draw_numeros = self.window.numero_occurrences[-1]
        for n in last_draw_numeros:
            self.assertEqual(self.profile.numero_delays[n], 0)

    def test_repeated_numeros_between_draws_matches_independent_computation(self):
        expected = tuple(
            repeated_values(self.window.numero_occurrences[i + 1], self.window.numero_occurrences[i])
            for i in range(self.window.actual_size - 1)
        )
        self.assertEqual(self.profile.repeated_numeros_between_draws, expected)


if __name__ == "__main__":
    unittest.main()
