"""Tests for core/services/historical_simulation_source.py. All fixture
datasets are synthetic, built via tempfile.TemporaryDirectory() and the
same on-disk shape discover_datasets()/load_dataset() already expect
(root/<year>/<file>.json, {"sorteios": [...]}). The real dataset is
only touched by the tests that explicitly say "real" in their name.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.evolution.statistics import calculate
from core.services.historical_simulation_source import (
    adapt_to_legacy_draw,
    available_at,
    build_historical_context_for_backtest,
    load_versioned_history,
    visible_draws,
)

REAL_ROOT = Path("datasets/historical/euromillions")


def make_draw(numero_sorteio, data, timestamp_utc, numeros=None, estrelas=None,
              jackpot=None, houve_vencedor=None):
    return {
        "numero_sorteio": numero_sorteio,
        "data": data,
        "horario": {"timestamp_utc": timestamp_utc},
        "chave": {"numeros": numeros or [1, 2, 3, 4, 5], "estrelas": estrelas or [1, 2]},
        "estatisticas_financeiras": {"previsao_1_premio_com_jackpot_eur": jackpot},
        "premios": {"houve_vencedor_1_premio_total": houve_vencedor},
    }


def write_dataset(root, year, filename, sorteios):
    year_dir = Path(root) / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    path = year_dir / filename
    path.write_text(json.dumps({"sorteios": sorteios}, ensure_ascii=False), encoding="utf-8")
    return path


class TestAvailableAt(unittest.TestCase):
    def test_parses_tz_aware_timestamp(self):
        draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00")
        self.assertEqual(available_at(draw), datetime(2099, 1, 1, 20, 0, 0, tzinfo=timezone.utc))

    def test_naive_timestamp_raises(self):
        draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00")
        with self.assertRaises(ValueError):
            available_at(draw)

    def test_missing_timestamp_field_raises_key_error(self):
        draw = {"data": "2099-01-01", "horario": {}}
        with self.assertRaises(KeyError):
            available_at(draw)

    def test_missing_horario_raises_key_error(self):
        with self.assertRaises(KeyError):
            available_at({"data": "2099-01-01"})

    def test_malformed_timestamp_raises_value_error(self):
        draw = make_draw("001/2099", "2099-01-01", "not-a-timestamp")
        with self.assertRaises(ValueError):
            available_at(draw)


class TestLoadVersionedHistory(unittest.TestCase):
    def test_loads_and_sorts_across_multiple_year_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            d1 = make_draw("002/2099", "2099-02-01", "2099-02-01T20:00:00+00:00")
            d2 = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00")
            write_dataset(tmp, 2099, "a.json", [d1])
            write_dataset(tmp, 2098, "b.json", [d2])
            result = load_versioned_history(tmp)
            self.assertEqual([d["numero_sorteio"] for d in result], ["001/2099", "002/2099"])

    def test_does_not_flatten_or_adapt(self):
        with tempfile.TemporaryDirectory() as tmp:
            d1 = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00")
            write_dataset(tmp, 2099, "a.json", [d1])
            result = load_versioned_history(tmp)
            self.assertIn("chave", result[0])
            self.assertNotIn("numeros", result[0])
            self.assertNotIn("jackpot", result[0])

    def test_empty_root_returns_empty_tuple(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_versioned_history(tmp), ())


@unittest.skipUnless(REAL_ROOT.exists(), "real historical dataset not present in this checkout")
class TestRealDatasetTimestampsAreUnique(unittest.TestCase):
    """The documented invariant that makes a tie-break key unnecessary:
    every real draw has a distinct available_at(). If this ever stops
    being true, this test fails loudly instead of silently masking a
    nondeterministic sort.
    """

    def test_every_real_draw_has_a_distinct_available_at(self):
        draws = load_versioned_history()
        timestamps = [available_at(d) for d in draws]
        self.assertEqual(len(timestamps), len(set(timestamps)))
        self.assertGreater(len(draws), 1900)  # sanity: real dataset, not an empty checkout


class TestTieBreakDeterminism(unittest.TestCase):
    def test_equal_timestamps_preserve_original_scan_order_deterministically(self):
        same_ts = "2099-01-01T20:00:00+00:00"
        first = make_draw("001/2099", "2099-01-01", same_ts)
        second = make_draw("002/2099", "2099-01-01", same_ts)
        with tempfile.TemporaryDirectory() as tmp:
            write_dataset(tmp, 2099, "a.json", [first, second])
            result1 = load_versioned_history(tmp)
            result2 = load_versioned_history(tmp)
        self.assertEqual(
            [d["numero_sorteio"] for d in result1],
            [d["numero_sorteio"] for d in result2],
        )
        self.assertEqual([d["numero_sorteio"] for d in result1], ["001/2099", "002/2099"])


class TestVisibleDraws(unittest.TestCase):
    def setUp(self):
        self.d1 = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00")
        self.d2 = make_draw("002/2099", "2099-01-08", "2099-01-08T20:00:00+00:00")
        self.d3 = make_draw("003/2099", "2099-01-15", "2099-01-15T20:00:00+00:00")
        self.draws = (self.d1, self.d2, self.d3)

    def test_cutoff_before_first_draw_gives_empty_history(self):
        cutoff = datetime(2098, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(visible_draws(self.draws, cutoff), ())

    def test_cutoff_exactly_at_instant_of_x_excludes_x(self):
        cutoff = available_at(self.d2)
        result = visible_draws(self.draws, cutoff)
        self.assertEqual([d["numero_sorteio"] for d in result], ["001/2099"])

    def test_cutoff_immediately_after_x_includes_x(self):
        cutoff = available_at(self.d2) + timedelta(seconds=1)
        result = visible_draws(self.draws, cutoff)
        self.assertEqual([d["numero_sorteio"] for d in result], ["001/2099", "002/2099"])

    def test_equivalent_timezone_cutoff_represents_same_instant(self):
        cutoff_utc = datetime(2099, 1, 8, 20, 0, 0, tzinfo=timezone.utc)
        cutoff_plus2 = datetime(2099, 1, 8, 22, 0, 0, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(
            visible_draws(self.draws, cutoff_utc),
            visible_draws(self.draws, cutoff_plus2),
        )

    def test_draws_after_cutoff_never_appear(self):
        cutoff = available_at(self.d1) + timedelta(seconds=1)
        result = visible_draws(self.draws, cutoff)
        ids = [d["numero_sorteio"] for d in result]
        self.assertNotIn("002/2099", ids)
        self.assertNotIn("003/2099", ids)

    def test_nothing_visible_returns_empty_not_full_history(self):
        cutoff = datetime(2000, 1, 1, tzinfo=timezone.utc)
        result = visible_draws(self.draws, cutoff)
        self.assertEqual(result, ())
        self.assertNotEqual(result, self.draws)

    def test_naive_cutoff_raises(self):
        with self.assertRaises(ValueError):
            visible_draws(self.draws, datetime(2099, 1, 10))

    def test_order_is_preserved_not_resorted(self):
        cutoff = available_at(self.d3) + timedelta(seconds=1)
        result = visible_draws(self.draws, cutoff)
        self.assertEqual(result, self.draws)

    def test_does_not_mutate_input(self):
        before = tuple(dict(d) for d in self.draws)
        visible_draws(self.draws, available_at(self.d3) + timedelta(seconds=1))
        self.assertEqual(self.draws, before)


class TestNoClockOrLiveApiDependency(unittest.TestCase):
    def setUp(self):
        import core.services.historical_simulation_source as module
        with open(module.__file__, "r", encoding="utf-8") as fh:
            self.source = fh.read()

    def test_never_calls_the_machine_clock(self):
        self.assertNotIn("datetime.now(", self.source)
        self.assertNotIn("date.today(", self.source)

    def test_never_touches_the_live_api_or_get_history(self):
        # get_history() is legitimately named in prose (module docstring,
        # explaining the LIVE/NORMAL path this module deliberately does
        # not touch) — what actually matters is that it is never
        # imported or called, and that no network capability exists here.
        self.assertNotIn("import get_history", self.source)
        self.assertNotIn("from core.data.loaders", self.source)
        self.assertNotIn("get_history(cfg", self.source)
        self.assertNotIn("urlopen", self.source)
        self.assertNotIn("urllib", self.source)


class TestAdaptToLegacyDraw(unittest.TestCase):
    def test_flattens_chave_into_top_level_lists(self):
        draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[5, 4, 3, 2, 1], estrelas=[2, 1])
        result = adapt_to_legacy_draw(draw)
        self.assertEqual(result["numeros"], [5, 4, 3, 2, 1])
        self.assertEqual(result["estrelas"], [2, 1])
        self.assertIsInstance(result["numeros"], list)
        self.assertEqual(result["data"], "2099-01-01")

    def test_null_jackpot_becomes_zero(self):
        draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", jackpot=None)
        self.assertEqual(adapt_to_legacy_draw(draw)["jackpot"], 0)

    def test_present_jackpot_is_preserved(self):
        draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", jackpot=17_000_000)
        self.assertEqual(adapt_to_legacy_draw(draw)["jackpot"], 17_000_000)

    def test_vencedores_mapping(self):
        for houve, expected in ((True, 1), (False, 0), (None, 0)):
            with self.subTest(houve=houve):
                draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", houve_vencedor=houve)
                self.assertEqual(adapt_to_legacy_draw(draw)["vencedores"], expected)

    def test_does_not_mutate_input_draw(self):
        draw = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00")
        before = json.loads(json.dumps(draw))
        adapt_to_legacy_draw(draw)
        self.assertEqual(draw, before)


class TestBuildHistoricalContextForBacktest(unittest.TestCase):
    def test_composes_load_visible_adapt(self):
        with tempfile.TemporaryDirectory() as tmp:
            d1 = make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5])
            d2 = make_draw("002/2099", "2099-01-08", "2099-01-08T20:00:00+00:00", numeros=[10, 20, 30, 40, 50])
            write_dataset(tmp, 2099, "a.json", [d1, d2])
            result = build_historical_context_for_backtest(available_at(d2), root=tmp)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["numeros"], [1, 2, 3, 4, 5])

    def test_integrates_with_real_calculate_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            draws = [
                make_draw(f"{i:03d}/2099", f"2099-01-{i:02d}", f"2099-01-{i:02d}T20:00:00+00:00",
                          numeros=[i, i + 1, i + 2, i + 3, i + 4], estrelas=[1, 2])
                for i in range(1, 6)
            ]
            write_dataset(tmp, 2099, "a.json", draws)
            cutoff = available_at(draws[-1]) + timedelta(seconds=1)
            hist = build_historical_context_for_backtest(cutoff, root=tmp)
            stats = calculate(hist)
            self.assertIn("quentes", stats)
            self.assertIn("frios", stats)
            self.assertIn("atrasados", stats)

    def test_target_x_content_never_influences_pre_x_context(self):
        # A and B are identical up to X-1. X itself, and everything
        # from X onward, differ AGGRESSIVELY between A and B (numeros,
        # estrelas, jackpot, vencedores all different) — only the
        # instant needed to establish the cutoff (available_at(X))
        # stays the same. The pre-X context must be byte-identical.
        shared_before = [
            make_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5], estrelas=[1, 2], jackpot=10_000_000, houve_vencedor=False),
            make_draw("002/2099", "2099-01-08", "2099-01-08T20:00:00+00:00", numeros=[6, 7, 8, 9, 10], estrelas=[3, 4], jackpot=20_000_000, houve_vencedor=True),
        ]
        x_datetime = "2099-01-15T20:00:00+00:00"

        x_and_after_a = [
            make_draw("003/2099", "2099-01-15", x_datetime, numeros=[11, 12, 13, 14, 15], estrelas=[5, 6], jackpot=1, houve_vencedor=False),
            make_draw("004/2099", "2099-01-22", "2099-01-22T20:00:00+00:00", numeros=[16, 17, 18, 19, 20], estrelas=[7, 8], jackpot=2, houve_vencedor=True),
        ]
        x_and_after_b = [
            make_draw("003/2099", "2099-01-15", x_datetime, numeros=[46, 47, 48, 49, 50], estrelas=[11, 12], jackpot=999_999_999, houve_vencedor=True),
            make_draw("004/2099", "2099-01-22", "2099-01-22T20:00:00+00:00", numeros=[21, 22, 23, 24, 25], estrelas=[9, 10], jackpot=3, houve_vencedor=False),
        ]

        cutoff = datetime.fromisoformat(x_datetime)  # excludes X itself (strict <)

        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            write_dataset(tmp_a, 2099, "a.json", shared_before + x_and_after_a)
            write_dataset(tmp_b, 2099, "a.json", shared_before + x_and_after_b)
            result_a = build_historical_context_for_backtest(cutoff, root=tmp_a)
            result_b = build_historical_context_for_backtest(cutoff, root=tmp_b)

        self.assertEqual(result_a, result_b)
        self.assertEqual(len(result_a), 2)  # only the two shared_before draws


if __name__ == "__main__":
    unittest.main()
