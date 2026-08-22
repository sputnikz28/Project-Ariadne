"""Tests for core/services/rolling_windows.py. Weekday selection is
checked against dates computed with stdlib date/timedelta (never a
memorised calendar fact) and deliberately paired with an incorrect
`dia_semana` text field, to prove filtering uses the ISO date, never
the text. Composition tests call core/services/statistical_profiles.py
directly over a RollingWindow — this module must never wrap those
primitives itself.
"""

import json
import unittest
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from core.services.rolling_windows import (
    FRIDAY,
    TUESDAY,
    RollingWindow,
    last_n_draws,
    last_n_draws_on_weekday,
)
from core.services.statistical_profiles import (
    absolute_frequency,
    current_delay,
    parity,
    repeated_values,
)

REAL_2026_DATASET_PATH = Path(
    "datasets/historical/euromillions/2026/euromilhoes_2026_001_067_dataset_completo.json"
)


def make_sorteio(numero_sorteio, data, dia_semana, numeros, estrelas):
    return {
        "numero_sorteio": numero_sorteio,
        "data": data,
        "dia_semana": dia_semana,
        "chave": {"numeros": numeros, "estrelas": estrelas},
    }


def _next_weekday(start, weekday):
    days_ahead = (weekday - start.weekday()) % 7
    return start + timedelta(days=days_ahead)


def _consecutive_weekdays(start, weekday, count):
    """count real dates that fall on `weekday`, in ascending order."""
    first = _next_weekday(start, weekday)
    return [first + timedelta(weeks=i) for i in range(count)]


def make_sorteios(n=5):
    return [
        make_sorteio(f"{i:03d}/2026", f"2026-01-{i:02d}", "?", [i, i + 1, i + 2, i + 3, i + 4], [1, 2])
        for i in range(1, n + 1)
    ]


class TestLastNDraws(unittest.TestCase):
    def test_returns_last_n_preserving_order(self):
        sorteios = make_sorteios(5)
        window = last_n_draws(sorteios, 3)
        self.assertEqual([d["numero_sorteio"] for d in window.draws], ["003/2026", "004/2026", "005/2026"])

    def test_n_greater_than_len_returns_all_available(self):
        sorteios = make_sorteios(3)
        window = last_n_draws(sorteios, 10)
        self.assertEqual(window.requested_size, 10)
        self.assertEqual(window.actual_size, 3)

    def test_n_zero_or_negative_returns_empty_window(self):
        sorteios = make_sorteios(5)
        self.assertEqual(last_n_draws(sorteios, 0).actual_size, 0)
        self.assertEqual(last_n_draws(sorteios, -3).actual_size, 0)

    def test_empty_input_returns_empty_window(self):
        window = last_n_draws([], 5)
        self.assertEqual(window.actual_size, 0)
        self.assertEqual(window.draws, ())
        self.assertEqual(window.numero_occurrences, ())
        self.assertEqual(window.estrela_occurrences, ())

    def test_does_not_mutate_input(self):
        sorteios = make_sorteios(5)
        before = json.loads(json.dumps(sorteios))
        last_n_draws(sorteios, 3)
        self.assertEqual(sorteios, before)

    def test_requested_size_recorded_even_when_fewer_available(self):
        sorteios = make_sorteios(2)
        window = last_n_draws(sorteios, 7)
        self.assertEqual(window.requested_size, 7)
        self.assertNotEqual(window.requested_size, window.actual_size)


class TestLastNDrawsOnWeekday(unittest.TestCase):
    def test_filters_by_date_ignoring_wrong_dia_semana_text(self):
        tuesdays = _consecutive_weekdays(date(2026, 1, 1), TUESDAY, 2)
        fridays = _consecutive_weekdays(date(2026, 1, 1), FRIDAY, 1)

        # Deliberately WRONG dia_semana text on both — a real Tuesday
        # labelled as Friday, and a real Friday labelled as Tuesday.
        sorteios = [
            make_sorteio("001/2026", tuesdays[0].isoformat(), "sexta-feira", [1, 2, 3, 4, 5], [1, 2]),
            make_sorteio("002/2026", fridays[0].isoformat(), "terça-feira", [6, 7, 8, 9, 10], [3, 4]),
            make_sorteio("003/2026", tuesdays[1].isoformat(), "sexta-feira", [11, 12, 13, 14, 15], [5, 6]),
        ]

        window = last_n_draws_on_weekday(sorteios, TUESDAY, 5)
        self.assertEqual(
            [d["numero_sorteio"] for d in window.draws], ["001/2026", "003/2026"],
            "must select by real date weekday, not the (wrong) dia_semana text",
        )

    def test_weekday_out_of_range_raises_value_error(self):
        sorteios = make_sorteios(3)
        for bad in (-1, 7, 100):
            with self.subTest(weekday=bad):
                with self.assertRaises(ValueError):
                    last_n_draws_on_weekday(sorteios, bad, 5)

    def test_no_matches_returns_empty_window(self):
        # every draw here is a real Tuesday; asking for Sunday (6) must
        # yield nothing.
        tuesdays = _consecutive_weekdays(date(2026, 1, 1), TUESDAY, 3)
        sorteios = [
            make_sorteio(f"{i:03d}/2026", d.isoformat(), "terça-feira", [1, 2, 3, 4, 5], [1, 2])
            for i, d in enumerate(tuesdays, start=1)
        ]
        window = last_n_draws_on_weekday(sorteios, 6, 5)
        self.assertEqual(window.actual_size, 0)

    def test_preserves_given_order_not_date_order(self):
        tuesdays = _consecutive_weekdays(date(2026, 1, 1), TUESDAY, 2)
        early, late = tuesdays[0], tuesdays[1]
        # deliberately given LATE-then-EARLY, out of chronological order
        sorteios = [
            make_sorteio("LATE", late.isoformat(), "terça-feira", [1, 2, 3, 4, 5], [1, 2]),
            make_sorteio("EARLY", early.isoformat(), "terça-feira", [6, 7, 8, 9, 10], [3, 4]),
        ]
        window = last_n_draws_on_weekday(sorteios, TUESDAY, 1)
        self.assertEqual(
            [d["numero_sorteio"] for d in window.draws], ["EARLY"],
            "must take the last element of the given order (positional), never re-sort by date",
        )

    def test_n_zero_or_negative_returns_empty(self):
        tuesdays = _consecutive_weekdays(date(2026, 1, 1), TUESDAY, 2)
        sorteios = [
            make_sorteio(f"{i:03d}/2026", d.isoformat(), "terça-feira", [1, 2, 3, 4, 5], [1, 2])
            for i, d in enumerate(tuesdays, start=1)
        ]
        self.assertEqual(last_n_draws_on_weekday(sorteios, TUESDAY, 0).actual_size, 0)
        self.assertEqual(last_n_draws_on_weekday(sorteios, TUESDAY, -1).actual_size, 0)

    def test_empty_input_returns_empty(self):
        window = last_n_draws_on_weekday([], TUESDAY, 5)
        self.assertEqual(window.actual_size, 0)

    def test_does_not_mutate_input(self):
        tuesdays = _consecutive_weekdays(date(2026, 1, 1), TUESDAY, 3)
        sorteios = [
            make_sorteio(f"{i:03d}/2026", d.isoformat(), "terça-feira", [1, 2, 3, 4, 5], [1, 2])
            for i, d in enumerate(tuesdays, start=1)
        ]
        before = json.loads(json.dumps(sorteios))
        last_n_draws_on_weekday(sorteios, TUESDAY, 2)
        self.assertEqual(sorteios, before)

    def test_last_10_works_via_generic_n_without_special_code(self):
        tuesdays = _consecutive_weekdays(date(2026, 1, 1), TUESDAY, 12)
        sorteios = [
            make_sorteio(f"{i:03d}/2026", d.isoformat(), "terça-feira", [1, 2, 3, 4, 5], [1, 2])
            for i, d in enumerate(tuesdays, start=1)
        ]
        window = last_n_draws_on_weekday(sorteios, TUESDAY, 10)
        self.assertEqual(window.actual_size, 10)
        self.assertEqual(window.draws[0]["numero_sorteio"], "003/2026")
        self.assertEqual(window.draws[-1]["numero_sorteio"], "012/2026")


class TestNumerosEstrelasIndependence(unittest.TestCase):
    def test_occurrences_kept_separate(self):
        # valor 5 exists in both universes; a draw with numero 5 but no
        # estrela 5 must not let one list leak into the other.
        sorteios = [
            make_sorteio("001/2026", "2026-01-06", "terça-feira", [5, 6, 7, 8, 9], [1, 2]),
            make_sorteio("002/2026", "2026-01-13", "terça-feira", [10, 11, 12, 13, 14], [3, 4]),
        ]
        window = last_n_draws(sorteios, 5)
        self.assertEqual(window.numero_occurrences, ((5, 6, 7, 8, 9), (10, 11, 12, 13, 14)))
        self.assertEqual(window.estrela_occurrences, ((1, 2), (3, 4)))
        numero_freq = absolute_frequency(window.numero_occurrences)
        estrela_freq = absolute_frequency(window.estrela_occurrences)
        self.assertEqual(numero_freq[5], 1)
        self.assertEqual(estrela_freq.get(5, 0), 0)


class TestComposesWithStatisticalProfiles(unittest.TestCase):
    def setUp(self):
        self.sorteios = [
            make_sorteio("001/2026", "2026-01-06", "terça-feira", [1, 2, 3, 4, 5], [1, 2]),
            make_sorteio("002/2026", "2026-01-13", "terça-feira", [1, 6, 7, 8, 9], [1, 3]),
            make_sorteio("003/2026", "2026-01-20", "terça-feira", [10, 11, 12, 13, 14], [4, 5]),
        ]
        self.window = last_n_draws(self.sorteios, 3)

    def test_absolute_frequency_over_window(self):
        freq = absolute_frequency(self.window.numero_occurrences)
        self.assertEqual(freq[1], 2)
        self.assertEqual(freq[10], 1)

    def test_current_delay_over_window(self):
        self.assertEqual(current_delay(self.window.numero_occurrences, 1), 1)
        self.assertEqual(current_delay(self.window.numero_occurrences, 10), 0)
        self.assertIsNone(current_delay(self.window.numero_occurrences, 99))

    def test_parity_over_window_draws(self):
        results = [parity(draw) for draw in self.window.numero_occurrences]
        self.assertEqual(results, [(2, 3), (2, 3), (3, 2)])

    def test_repeated_values_between_last_two_draws_in_window(self):
        self.assertGreaterEqual(self.window.actual_size, 2)
        repeated = repeated_values(
            self.window.numero_occurrences[-1], self.window.numero_occurrences[-2],
        )
        self.assertEqual(repeated, ())  # no overlap between draws 002 and 003 here


@unittest.skipUnless(REAL_2026_DATASET_PATH.exists(), "real 2026 dataset not present in this checkout")
class TestAgainstRealDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        cls.sorteios = data["sorteios"]

    def test_last_5_tuesdays_matches_independent_filter(self):
        expected = [s for s in self.sorteios if date.fromisoformat(s["data"]).weekday() == TUESDAY][-5:]
        window = last_n_draws_on_weekday(self.sorteios, TUESDAY, 5)
        self.assertEqual(
            [d["numero_sorteio"] for d in window.draws],
            [s["numero_sorteio"] for s in expected],
        )
        self.assertEqual(window.actual_size, len(expected))


if __name__ == "__main__":
    unittest.main()
