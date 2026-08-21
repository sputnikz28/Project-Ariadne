"""Tests for core/services/historical_ariadne_source.py (Commit 23) and
the corresponding TEMPORAL mode of library/ariadne/engine.py:Ariadne.
All fixture scrolls are synthetic (tempfile.TemporaryDirectory()); the
real library/scrolls/ tree is only touched by tests that say "real" in
their name.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from core.services.historical_ariadne_source import (
    build_scrolls_for_backtest,
    load_scrolls,
    pergaminho_available_at,
    visible_scrolls,
)
from library.ariadne.engine import Ariadne

REAL_SCROLLS_ROOT = Path("library/scrolls")


def make_scroll_2026(scroll_id, extracao_data, timestamp_utc, numeros=None, estrelas=None, fase_lua=None):
    return {
        "id": scroll_id,
        "data": {"extracao": extracao_data, "timestamp_utc": timestamp_utc},
        "extracao": {"numeros": numeros or [1, 2, 3, 4, 5], "estrelas": estrelas or [1, 2]},
        "estatisticas": {"soma": sum(numeros or [1, 2, 3, 4, 5])},
        "astronomia": {"fase_lua": fase_lua or "Lua cheia"},
        "estado": "SELADO",
        "assinatura": {"integridade": "100%"},
    }


def make_scroll_pre2026(scroll_id, data_str, timestamp_utc, numeros=None, estrelas=None, fase_lua=None):
    return {
        "id": scroll_id,
        "data": data_str,
        "horario": {"timestamp_utc": timestamp_utc},
        "extracao": {"numeros": numeros or [1, 2, 3, 4, 5], "estrelas": estrelas or [1, 2]},
        "estatisticas": {"soma": sum(numeros or [1, 2, 3, 4, 5])},
        "astronomia": {"fase_lua": fase_lua or "Lua cheia"},
        "estado": "SELADO",
        "assinatura": {"integridade": "100%"},
    }


def write_scroll(root, year, filename, scroll):
    year_dir = Path(root) / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    (year_dir / filename).write_text(json.dumps(scroll, ensure_ascii=False), encoding="utf-8")


class TestPergaminhoAvailableAt(unittest.TestCase):
    def test_2026_format_dict_data(self):
        scroll = make_scroll_2026("PERG-2026-001", "2099-01-01", "2099-01-01T20:00:00+00:00")
        self.assertEqual(pergaminho_available_at(scroll), datetime(2099, 1, 1, 20, 0, tzinfo=timezone.utc))

    def test_pre_2026_format_string_data(self):
        scroll = make_scroll_pre2026("PERG-2011-001", "2099-01-01", "2099-01-01T19:00:00+00:00")
        self.assertEqual(pergaminho_available_at(scroll), datetime(2099, 1, 1, 19, 0, tzinfo=timezone.utc))

    def test_naive_timestamp_raises(self):
        scroll = make_scroll_2026("PERG-2026-001", "2099-01-01", "2099-01-01T20:00:00")
        with self.assertRaises(ValueError):
            pergaminho_available_at(scroll)

    def test_missing_data_raises_key_error(self):
        with self.assertRaises(KeyError):
            pergaminho_available_at({"id": "X"})

    def test_malformed_timestamp_raises_value_error(self):
        scroll = make_scroll_2026("PERG-2026-001", "2099-01-01", "not-a-timestamp")
        with self.assertRaises(ValueError):
            pergaminho_available_at(scroll)


class TestLoadScrolls(unittest.TestCase):
    def test_loads_and_sorts_across_years(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_scroll(tmp, 2099, "002.json", make_scroll_2026("PERG-2099-002", "2099-02-01", "2099-02-01T20:00:00+00:00"))
            write_scroll(tmp, 2098, "001.json", make_scroll_pre2026("PERG-2098-001", "2098-01-01", "2098-01-01T19:00:00+00:00"))
            result = load_scrolls(tmp)
            self.assertEqual([s["id"] for s in result], ["PERG-2098-001", "PERG-2099-002"])

    def test_excludes_indice_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_scroll(tmp, 2099, "001.json", make_scroll_2026("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00"))
            year_dir = Path(tmp) / "2099"
            (year_dir / "indice.json").write_text(
                json.dumps({"ano": 2099, "quantidade_sorteios": 1}), encoding="utf-8",
            )
            result = load_scrolls(tmp)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], "PERG-2099-001")

    @unittest.skipUnless(REAL_SCROLLS_ROOT.exists(), "real library/scrolls/ not present in this checkout")
    def test_every_real_scroll_has_a_valid_available_at(self):
        scrolls = load_scrolls()
        # this both proves indice.json exclusion works against the real
        # tree and that every real pergaminho has a usable timestamp.
        timestamps = [pergaminho_available_at(s) for s in scrolls]
        self.assertGreater(len(timestamps), 1900)


class TestVisibleScrolls(unittest.TestCase):
    def setUp(self):
        self.s1 = make_scroll_2026("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00")
        self.s2 = make_scroll_2026("PERG-2099-002", "2099-01-08", "2099-01-08T20:00:00+00:00")
        self.s3 = make_scroll_2026("PERG-2099-003", "2099-01-15", "2099-01-15T20:00:00+00:00")
        self.scrolls = (self.s1, self.s2, self.s3)

    def test_cutoff_before_first_gives_empty(self):
        self.assertEqual(visible_scrolls(self.scrolls, datetime(2098, 1, 1, tzinfo=timezone.utc)), ())

    def test_cutoff_exactly_at_x_excludes_x(self):
        result = visible_scrolls(self.scrolls, pergaminho_available_at(self.s2))
        self.assertEqual([s["id"] for s in result], ["PERG-2099-001"])

    def test_cutoff_after_x_includes_x(self):
        cutoff = pergaminho_available_at(self.s2) + timedelta(seconds=1)
        result = visible_scrolls(self.scrolls, cutoff)
        self.assertEqual([s["id"] for s in result], ["PERG-2099-001", "PERG-2099-002"])

    def test_timezone_equivalent_cutoff_same_instant(self):
        utc_cutoff = datetime(2099, 1, 8, 20, 0, tzinfo=timezone.utc)
        plus2_cutoff = datetime(2099, 1, 8, 22, 0, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(visible_scrolls(self.scrolls, utc_cutoff), visible_scrolls(self.scrolls, plus2_cutoff))

    def test_nothing_visible_never_falls_back_to_full(self):
        result = visible_scrolls(self.scrolls, datetime(2000, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(result, ())
        self.assertNotEqual(result, self.scrolls)

    def test_naive_cutoff_raises(self):
        with self.assertRaises(ValueError):
            visible_scrolls(self.scrolls, datetime(2099, 1, 10))

    def test_order_preserved(self):
        cutoff = pergaminho_available_at(self.s3) + timedelta(seconds=1)
        self.assertEqual(visible_scrolls(self.scrolls, cutoff), self.scrolls)

    def test_does_not_mutate_input(self):
        before = tuple(dict(s) for s in self.scrolls)
        visible_scrolls(self.scrolls, pergaminho_available_at(self.s3) + timedelta(seconds=1))
        self.assertEqual(self.scrolls, before)


class TestBuildScrollsForBacktest(unittest.TestCase):
    def test_target_x_content_never_influences_pre_x_view(self):
        shared_before = [
            make_scroll_2026("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5]),
            make_scroll_2026("PERG-2099-002", "2099-01-08", "2099-01-08T20:00:00+00:00", numeros=[6, 7, 8, 9, 10]),
        ]
        x_datetime = "2099-01-15T20:00:00+00:00"
        x_and_after_a = [
            make_scroll_2026("PERG-2099-003", "2099-01-15", x_datetime, numeros=[11, 12, 13, 14, 15]),
            make_scroll_2026("PERG-2099-004", "2099-01-22", "2099-01-22T20:00:00+00:00", numeros=[16, 17, 18, 19, 20]),
        ]
        x_and_after_b = [
            make_scroll_2026("PERG-2099-003", "2099-01-15", x_datetime, numeros=[46, 47, 48, 49, 50]),
            make_scroll_2026("PERG-2099-004", "2099-01-22", "2099-01-22T20:00:00+00:00", numeros=[21, 22, 23, 24, 25]),
        ]
        cutoff = datetime.fromisoformat(x_datetime)

        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            for i, s in enumerate(shared_before + x_and_after_a):
                write_scroll(tmp_a, 2099, f"{i:03d}.json", s)
            for i, s in enumerate(shared_before + x_and_after_b):
                write_scroll(tmp_b, 2099, f"{i:03d}.json", s)
            result_a = build_scrolls_for_backtest(cutoff, tmp_a)
            result_b = build_scrolls_for_backtest(cutoff, tmp_b)

        self.assertEqual(result_a, result_b)
        self.assertEqual(len(result_a), 2)


class TestAriadneLiveModeUnaffected(unittest.TestCase):
    """No `scrolls=` passed — must behave exactly as before Commit 23."""

    def test_default_construction_is_not_temporal(self):
        self.assertFalse(Ariadne()._temporal)

    def test_scope_a_is_2026_only(self):
        # self.scrolls in LIVE mode is still the 2026-only path list —
        # 64 real draws confirmed in Commit 21/22's audits.
        self.assertEqual(len(Ariadne().scrolls), 64)

    def test_scope_b_sees_all_years(self):
        # confirmed real total across 2004-2026 in Commit 22's audit.
        self.assertEqual(len(Ariadne().full_history()), 1971)

    def test_index_methods_still_work_live(self):
        # pairs()/triples() never call save_query(); least_frequent_numbers()
        # does — patched here so running this test never writes to the
        # real library/cache/.
        a = Ariadne()
        self.assertIsInstance(a.pairs(5), list)
        self.assertIsInstance(a.triples(5), list)
        with mock.patch("library.ariadne.engine.save_query"):
            self.assertIsInstance(a.least_frequent_numbers(5), list)

    def test_scroll_state_still_works_live(self):
        result = Ariadne().scroll_state(64)
        self.assertTrue(result["encontrado"])
        self.assertEqual(result["id"], "PERG-2026-064")


class TestAriadneTemporalScrollState(unittest.TestCase):
    def test_x_excluded_by_cutoff_is_ausente_despite_real_file_on_disk(self):
        # numero=64 really exists on disk at library/scrolls/2026/064.json
        # (confirmed in the audit) — the frozen collection deliberately
        # excludes it.
        frozen = (make_scroll_2026("PERG-2026-063", "2026-08-04", "2026-08-04T18:00:00+00:00"),)
        a = Ariadne(scrolls=frozen)
        self.assertEqual(a.scroll_state(64), {"encontrado": False, "estado": "AUSENTE"})

    def test_pre_2026_scroll_with_same_numero_is_never_returned(self):
        frozen = (make_scroll_pre2026("PERG-2011-064", "2011-01-01", "2011-01-01T19:00:00+00:00"),)
        a = Ariadne(scrolls=frozen)
        self.assertEqual(a.scroll_state(64), {"encontrado": False, "estado": "AUSENTE"})

    def test_x_present_in_frozen_collection_is_found(self):
        frozen = (make_scroll_2026("PERG-2026-064", "2026-08-11", "2026-08-11T18:00:00+00:00"),)
        a = Ariadne(scrolls=frozen)
        result = a.scroll_state(64)
        self.assertTrue(result["encontrado"])
        self.assertEqual(result["id"], "PERG-2026-064")

    def test_no_disk_fallback_for_excluded_x(self):
        frozen = ()
        a = Ariadne(scrolls=frozen)
        with mock.patch("pathlib.Path.exists", side_effect=AssertionError("must not touch disk in temporal mode")), \
             mock.patch("library.ariadne.engine.ler_json", side_effect=AssertionError("must not read a file in temporal mode")):
            self.assertEqual(a.scroll_state(64), {"encontrado": False, "estado": "AUSENTE"})


class TestAriadneTemporalScopesNeverTouchDisk(unittest.TestCase):
    def setUp(self):
        self.frozen = (
            make_scroll_2026("PERG-2026-001", "2026-01-01", "2026-01-01T18:00:00+00:00", fase_lua="Lua nova"),
            make_scroll_2026("PERG-2026-002", "2026-01-08", "2026-01-08T18:00:00+00:00", fase_lua="Lua cheia"),
        )
        self.ariadne = Ariadne(scrolls=self.frozen)

    def _assert_no_filesystem_access(self, callable_):
        # save_query() is patched here purely for test isolation (it
        # writes to the real library/cache/ regardless of mode — a
        # pre-existing side effect, explicitly not altered by Commit 23
        # per scope decision) — not itself part of the "no disk read"
        # claim under test, which is about library/scrolls/ only.
        with mock.patch("pathlib.Path.exists", side_effect=AssertionError("Path.exists() called in temporal mode")), \
             mock.patch("pathlib.Path.iterdir", side_effect=AssertionError("Path.iterdir() called in temporal mode")), \
             mock.patch("pathlib.Path.glob", side_effect=AssertionError("Path.glob() called in temporal mode")), \
             mock.patch("library.ariadne.engine.ler_json", side_effect=AssertionError("ler_json() called in temporal mode")), \
             mock.patch("library.ariadne.engine.save_query"):
            return callable_()

    def test_search_moon_no_disk(self):
        result = self._assert_no_filesystem_access(lambda: self.ariadne.search_moon("Lua cheia"))
        self.assertEqual(result["scrolls_encontrados"], 1)

    def test_overdue_numbers_no_disk(self):
        result = self._assert_no_filesystem_access(lambda: self.ariadne.overdue_numbers(5))
        self.assertIsInstance(result, list)

    def test_transition_pattern_no_disk(self):
        result = self._assert_no_filesystem_access(lambda: self.ariadne.transition_pattern())
        self.assertEqual(result["persistentes"], sorted(set(range(1, 6)) & set(range(1, 6))))

    def test_full_history_no_disk(self):
        result = self._assert_no_filesystem_access(lambda: self.ariadne.full_history())
        self.assertEqual(len(result), 2)

    def test_weekly_echoes_no_disk(self):
        result = self._assert_no_filesystem_access(lambda: self.ariadne.weekly_echoes(1))
        self.assertIsInstance(result["total_ecos"], int)

    def test_last_known_key_no_disk(self):
        result = self._assert_no_filesystem_access(lambda: self.ariadne.last_known_key())
        self.assertEqual(result["id"], "PERG-2026-002")

    def test_full_history_temporal_only_sees_frozen_collection(self):
        # 2 draws injected, not 1971 real ones — proves it never fell
        # back to the real disk tree.
        self.assertEqual(len(self.ariadne.full_history()), 2)


class TestAriadneTemporalFutureScrollsDoNotLeak(unittest.TestCase):
    def test_altering_future_scrolls_does_not_change_pre_cutoff_view(self):
        shared_before = (
            make_scroll_2026("PERG-2026-001", "2026-01-01", "2026-01-01T18:00:00+00:00", numeros=[1, 2, 3, 4, 5]),
        )
        future_a = make_scroll_2026("PERG-2026-002", "2026-01-08", "2026-01-08T18:00:00+00:00", numeros=[6, 7, 8, 9, 10])
        future_b = make_scroll_2026("PERG-2026-002", "2026-01-08", "2026-01-08T18:00:00+00:00", numeros=[46, 47, 48, 49, 50])

        cutoff = pergaminho_available_at(future_a)  # excludes the future scroll itself
        a_view = visible_scrolls(shared_before + (future_a,), cutoff)
        b_view = visible_scrolls(shared_before + (future_b,), cutoff)

        ariadne_a = Ariadne(scrolls=a_view)
        ariadne_b = Ariadne(scrolls=b_view)
        # criada_em is a real-clock timestamp on weekly_echoes()'s
        # response, not part of the historical content — excluded from
        # this comparison per explicit scope decision (not a temporal
        # leak: the clock never enters scroll selection/analysis, and
        # library/cache/ is never read back by Ariadne).
        history_a = ariadne_a.full_history()
        history_b = ariadne_b.full_history()
        self.assertEqual(history_a, history_b)
        self.assertEqual(len(history_a), 1)


class TestAriadneTemporalIndicesRaise(unittest.TestCase):
    def setUp(self):
        self.ariadne = Ariadne(scrolls=())

    def test_pairs_raises(self):
        with self.assertRaises(RuntimeError):
            self.ariadne.pairs()

    def test_triples_raises(self):
        with self.assertRaises(RuntimeError):
            self.ariadne.triples()

    def test_numero_raises(self):
        with self.assertRaises(RuntimeError):
            self.ariadne.numero(17)

    def test_least_frequent_numbers_raises(self):
        with self.assertRaises(RuntimeError):
            self.ariadne.least_frequent_numbers()

    def test_raised_error_never_reads_indexes_from_disk(self):
        with mock.patch("library.ariadne.engine.ler_json", side_effect=AssertionError("must not read library/indexes/ in temporal mode")):
            with self.assertRaises(RuntimeError):
                self.ariadne.pairs()


if __name__ == "__main__":
    unittest.main()
