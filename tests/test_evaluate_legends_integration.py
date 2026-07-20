"""Integration tests for evaluate_legends.py — drives the real CLI
main() against a real config.txt (via load_legend_config()) and a real
LegendRegistry/HeroRegistry, redirected to temporary directories so
project state is never touched. No production code is modified: only
the module-level names HeroRegistry/LegendRegistry/load_config are
monkeypatched for the duration of each test, exactly as evaluate_legends
already imports and calls them.
"""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import evaluate_legends
from library.heroes.registry import HeroRegistry
from library.legends.registry import LegendRegistry

REPORT_PATH = Path("experiments/reports/generated") / "legends_evaluation.txt"


def bound_hero_registry(base):
    class _Bound(HeroRegistry):
        def __init__(self, *_a, **_kw):
            super().__init__(base=base)
    return _Bound


def bound_legend_registry(base):
    class _Bound(LegendRegistry):
        def __init__(self, *_a, **_kw):
            super().__init__(base=base)
    return _Bound


def make_hero(source_prediction_id, draw_num, entity_id="H-1", entity_name="Test Entity",
              race="Elfo", generation=1, numeros=None, estrelas=None, provenance="legacy"):
    draw_id = f"{draw_num:03d}/2026"
    draw_date = f"2026-{(draw_num % 12) + 1:02d}-{(draw_num % 27) + 1:02d}"
    hero_id = f"HERO-2026-{draw_num:03d}-{source_prediction_id[:6]}"
    return {
        "hero_id": hero_id,
        # HeroRegistry.register() persists by dedup_hash — not otherwise
        # read anywhere in legend_evaluation.py/evaluate_legends.py, so a
        # unique stand-in value is sufficient for these tests.
        "dedup_hash": hero_id,
        "source_prediction_id": source_prediction_id,
        "draw_id": draw_id,
        "draw_date": draw_date,
        "provenance": provenance,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "race": race,
        "generation": generation,
        "predicted_key": {"numeros": numeros or [10, 19, 37, 42, 47], "estrelas": estrelas or [9, 12]},
    }


class EvaluateLegendsIntegrationTestBase(unittest.TestCase):
    def setUp(self):
        self.hero_base = tempfile.mkdtemp()
        self.legend_base = tempfile.mkdtemp()
        self.hero_registry = HeroRegistry(base=self.hero_base)

    def tearDown(self):
        shutil.rmtree(self.hero_base, ignore_errors=True)
        shutil.rmtree(self.legend_base, ignore_errors=True)
        if REPORT_PATH.exists():
            REPORT_PATH.unlink()

    def add_hero(self, **kwargs):
        hero = make_hero(**kwargs)
        self.hero_registry.register(hero)
        return hero

    def run_cli(self, dry_run=False):
        argv = ["evaluate_legends.py"] + (["--dry-run"] if dry_run else [])
        legend_registry_cls = bound_legend_registry(self.legend_base)
        hero_registry_cls = bound_hero_registry(self.hero_base)
        out = io.StringIO()
        with patch.object(sys, "argv", argv), \
             patch.object(evaluate_legends, "HeroRegistry", hero_registry_cls), \
             patch.object(evaluate_legends, "LegendRegistry", legend_registry_cls), \
             redirect_stdout(out):
            evaluate_legends.main()
        return out.getvalue()

    def legends(self):
        return LegendRegistry(base=self.legend_base)


class TestDryRun(EvaluateLegendsIntegrationTestBase):
    def test_dry_run_writes_nothing(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-dry", draw_num=57 + i)
        self.run_cli(dry_run=True)
        self.assertEqual(self.legends().count(), 0)

    def test_dry_run_reports_the_correct_promotion(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-dry", draw_num=57 + i)
        report = self.run_cli(dry_run=True)
        self.assertIn("DRY RUN", report)
        self.assertIn("Promoted (new):        1", report)

    def test_dry_run_output_is_deterministic_across_repeated_runs(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-dry", draw_num=57 + i)
        report_1 = self.run_cli(dry_run=True)
        report_2 = self.run_cli(dry_run=True)
        self.assertEqual(report_1, report_2)
        self.assertEqual(self.legends().count(), 0)  # still nothing written after two dry-runs


class TestFirstRealRun(EvaluateLegendsIntegrationTestBase):
    def test_new_legend_is_registered(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-first", draw_num=57 + i)
        self.run_cli(dry_run=False)
        self.assertEqual(self.legends().count(), 1)
        stored = self.legends().get("spid-first")
        self.assertEqual(stored["promotion_threshold"], 3)
        self.assertEqual(stored["promotion_tier"], "LEGEND_TIER_4")
        self.assertEqual(stored["qualified_draws"], 3)
        self.assertEqual(stored["hero_count"], 3)
        self.assertEqual(stored["provenance"], "legacy")

    def test_index_is_rebuilt(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-first", draw_num=57 + i)
        self.run_cli(dry_run=False)
        index = json.loads(self.legends().index_path.read_text(encoding="utf-8"))
        self.assertEqual(index["total_legends"], 1)

    def test_report_shows_correct_final_counts(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-first", draw_num=57 + i)
        report = self.run_cli(dry_run=False)
        self.assertIn("Promoted (new):        1", report)
        self.assertIn("Refreshed (existing):  0", report)
        self.assertIn("Total Legends (projected): 1", report)


class TestSecondRunSameState(EvaluateLegendsIntegrationTestBase):
    def test_second_run_produces_no_new_promotion_no_duplicate_no_change(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-stable", draw_num=57 + i)
        self.run_cli(dry_run=False)
        before = self.legends().get("spid-stable")

        report = self.run_cli(dry_run=False)  # identical Hero state, run again

        self.assertEqual(self.legends().count(), 1)  # still exactly one, no duplicate
        after = self.legends().get("spid-stable")
        self.assertEqual(before, after)  # byte-identical — idempotent
        self.assertIn("Promoted (new):        0", report)
        self.assertIn("Refreshed (existing):  0", report)
        self.assertIn("Unchanged (existing):  1", report)

    def test_index_unchanged_across_idempotent_reruns(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-stable", draw_num=57 + i)
        self.run_cli(dry_run=False)
        index_before = self.legends().index_path.read_text(encoding="utf-8")
        self.run_cli(dry_run=False)
        index_after = self.legends().index_path.read_text(encoding="utf-8")
        self.assertEqual(index_before, index_after)


class TestRefresh(EvaluateLegendsIntegrationTestBase):
    def test_new_qualifying_draw_refreshes_accumulative_fields_only(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-refresh", draw_num=57 + i)
        self.run_cli(dry_run=False)
        before = self.legends().get("spid-refresh")

        self.add_hero(source_prediction_id="spid-refresh", draw_num=61)  # a 4th distinct draw
        report = self.run_cli(dry_run=False)
        after = self.legends().get("spid-refresh")

        self.assertIn("Refreshed (existing):  1", report)
        self.assertEqual(after["qualified_draws"], 4)
        self.assertEqual(after["hero_count"], 4)
        self.assertIn("HERO-2026-061-spid-r", after["contributing_hero_ids"])

        for frozen_key in ("legend_id", "source_prediction_id", "promotion_draw", "promotion_draw_date",
                           "promotion_threshold", "promotion_tier", "criteria_version", "promotion_hero_ids"):
            self.assertEqual(before[frozen_key], after[frozen_key])

    def test_only_one_legend_still_exists_after_refresh(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-refresh", draw_num=57 + i)
        self.run_cli(dry_run=False)
        self.add_hero(source_prediction_id="spid-refresh", draw_num=61)
        self.run_cli(dry_run=False)
        self.assertEqual(self.legends().count(), 1)


class TestNoDuplicatePromotion(EvaluateLegendsIntegrationTestBase):
    def test_already_promoted_prediction_is_never_registered_again_across_many_runs(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-once", draw_num=57 + i)
        legend_id_after_runs = []
        for extra_draw in range(4):
            if extra_draw:
                self.add_hero(source_prediction_id="spid-once", draw_num=61 + extra_draw)
            self.run_cli(dry_run=False)
            legend_id_after_runs.append(self.legends().get("spid-once")["legend_id"])
        self.assertEqual(self.legends().count(), 1)
        self.assertEqual(len(set(legend_id_after_runs)), 1)  # same legend_id every single time


class TestRealConfiguration(EvaluateLegendsIntegrationTestBase):
    def test_smallest_threshold_wins_even_when_group_already_exceeds_it(self):
        # Approved contract (regra b): a Legend freezes the first
        # chronological promotion possible. With the real config's
        # limiares=3,5,10,20, chronological position 3 is always reached
        # before position 5 or 10, so a group that already has 5
        # qualifying draws at its very first evaluation still promotes
        # at threshold=3/LEGEND_TIER_4 — never at a higher configured
        # threshold. qualified_draws still reflects the true, full count.
        for i in range(5):
            self.add_hero(source_prediction_id="spid-tier3", draw_num=57 + i)
        self.run_cli(dry_run=False)
        stored = self.legends().get("spid-tier3")
        self.assertEqual(stored["promotion_threshold"], 3)
        self.assertEqual(stored["promotion_tier"], "LEGEND_TIER_4")
        self.assertEqual(stored["qualified_draws"], 5)

    def test_smallest_threshold_wins_with_ten_draws_present_at_first_evaluation(self):
        for i in range(10):
            self.add_hero(source_prediction_id="spid-tier2", draw_num=57 + i)
        self.run_cli(dry_run=False)
        stored = self.legends().get("spid-tier2")
        self.assertEqual(stored["promotion_threshold"], 3)
        self.assertEqual(stored["promotion_tier"], "LEGEND_TIER_4")
        self.assertEqual(stored["qualified_draws"], 10)

    def test_criteria_version_from_real_config_is_stamped(self):
        for i in range(3):
            self.add_hero(source_prediction_id="spid-criteria", draw_num=57 + i)
        self.run_cli(dry_run=False)
        stored = self.legends().get("spid-criteria")
        self.assertEqual(stored["criteria_version"], "v1")  # matches config.txt's real value


class TestErrorPaths(EvaluateLegendsIntegrationTestBase):
    def test_invalid_configuration_aborts_with_nonzero_exit(self):
        from configparser import ConfigParser
        broken_cfg = ConfigParser()  # no [REGISTO_LENDAS] section at all

        with patch.object(sys, "argv", ["evaluate_legends.py"]), \
             patch.object(evaluate_legends, "load_config", lambda *_a, **_kw: broken_cfg), \
             patch.object(evaluate_legends, "HeroRegistry", bound_hero_registry(self.hero_base)), \
             patch.object(evaluate_legends, "LegendRegistry", bound_legend_registry(self.legend_base)), \
             redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(SystemExit) as ctx:
                evaluate_legends.main()
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("Configuration error", out.getvalue())
        self.assertEqual(self.legends().count(), 0)

    def test_nonexistent_legend_registry_directory_is_treated_as_empty_not_an_error(self):
        # First-ever run: legend_base's entries/ doesn't exist yet at all.
        never_used_base = tempfile.mkdtemp()
        shutil.rmtree(never_used_base)  # directory itself doesn't exist
        for i in range(3):
            self.add_hero(source_prediction_id="spid-fresh", draw_num=57 + i)

        argv = ["evaluate_legends.py"]
        with patch.object(sys, "argv", argv), \
             patch.object(evaluate_legends, "HeroRegistry", bound_hero_registry(self.hero_base)), \
             patch.object(evaluate_legends, "LegendRegistry", bound_legend_registry(never_used_base)), \
             redirect_stdout(io.StringIO()) as out:
            evaluate_legends.main()  # must not raise

        self.assertIn("Promoted (new):        1", out.getvalue())
        shutil.rmtree(never_used_base, ignore_errors=True)

    def test_corrupted_legend_entry_aborts_before_any_further_write(self):
        # Pre-populate a Legend entry whose filename doesn't match its own
        # source_prediction_id — an integrity violation load_all() must
        # surface immediately, before any evaluation or write happens.
        entries_dir = Path(self.legend_base) / "entries"
        entries_dir.mkdir(parents=True, exist_ok=True)
        bad_record = {
            "legend_id": "LEGEND-mismatch", "source_prediction_id": "spid-OTHER",
            "promotion_threshold": 3, "promotion_tier": "LEGEND_TIER_4",
            "hero_count": 3, "qualified_draws": 3, "contributing_hero_ids": [],
            "provenance": "legacy",
        }
        (entries_dir / "spid-mismatched-filename.json").write_text(json.dumps(bad_record), encoding="utf-8")

        for i in range(3):
            self.add_hero(source_prediction_id="spid-fine", draw_num=57 + i)

        with patch.object(sys, "argv", ["evaluate_legends.py"]), \
             patch.object(evaluate_legends, "HeroRegistry", bound_hero_registry(self.hero_base)), \
             patch.object(evaluate_legends, "LegendRegistry", bound_legend_registry(self.legend_base)), \
             redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(SystemExit) as ctx:
                evaluate_legends.main()

        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("integrity error", out.getvalue().lower())
        # the unrelated, legitimately qualifying prediction must NOT have
        # been promoted either — the whole run aborted before any write.
        self.assertIsNone(self.legends().get("spid-fine"))


if __name__ == "__main__":
    unittest.main()
