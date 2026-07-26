"""Tests for core/services/dashboard_data.py — Heroes and Legends row
builders only (scope of this commit). No HeroRegistry/LegendRegistry
involved anywhere here — only plain dicts, matching the module's
contract that it never touches the registries or disk itself.
"""

import dataclasses
import unittest

from core.services.dashboard_data import (
    HeroRow,
    LegendRow,
    build_heroes_rows,
    build_legends_rows,
)


def make_hero_record(**overrides):
    record = {
        "hero_id": "HERO-2026-057-000149f4",
        "dedup_hash": "000149f4a97a6dd335f44a53ff431b463b3037e9f28c1fae4ca1a24b628f0a5c",
        "entity_id": "H-00017",
        "entity_name": "Morgana da Lua Fria",
        "race": "Chefe Tribal",
        "generation": 1,
        "provenance": "legacy",
        "draw_id": "057/2026",
        "draw_date": "2026-07-17",
        "official_key": {"numeros": [12, 21, 23, 34, 40], "estrelas": [9, 10]},
        "predicted_key": {"numeros": [12, 36, 40, 45, 50], "estrelas": [5, 10]},
        "matched_numbers_count": 2,
        "matched_stars_count": 1,
        "hero_category": "2+1",
        "hero_tier": "TIER_5",
        "registered_at": "2026-07-22T09:09:33+00:00",
    }
    record.update(overrides)
    return record


def make_legend_record(**overrides):
    record = {
        "legend_id": "LEGEND-395e24e0",
        "source_prediction_id": "395e24e0eafd0f7a6f07684d4849e82903bb25e6cbf9535265f4a9b35119a807",
        "entity_id": "H-00017",
        "entity_name": "Morgana da Lua Fria",
        "race": "Chefe Tribal",
        "promotion_draw": "058/2026",
        "promotion_draw_date": "2026-07-21",
        "promotion_threshold": 3,
        "promotion_tier": "LEGEND_TIER_4",
        "criteria_version": "v1",
        "hero_count": 3,
        "qualified_draws": 3,
        "provenance": "legacy",
    }
    record.update(overrides)
    return record


class TestBuildHeroesRows(unittest.TestCase):
    def test_maps_fields_correctly(self):
        rows = build_heroes_rows([make_hero_record()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.hero_id, "HERO-2026-057-000149f4")
        self.assertEqual(row.entity_name, "Morgana da Lua Fria")
        self.assertEqual(row.official_numeros, (12, 21, 23, 34, 40))
        self.assertEqual(row.official_estrelas, (9, 10))
        self.assertEqual(row.predicted_numeros, (12, 36, 40, 45, 50))
        self.assertEqual(row.predicted_estrelas, (5, 10))
        self.assertEqual(row.matched_numbers_count, 2)
        self.assertEqual(row.hero_tier, "TIER_5")
        self.assertEqual(row.registered_at, "2026-07-22T09:09:33+00:00")

    def test_key_fields_are_tuples_not_lists(self):
        row = build_heroes_rows([make_hero_record()])[0]
        for field_name in ("official_numeros", "official_estrelas", "predicted_numeros", "predicted_estrelas"):
            self.assertIsInstance(getattr(row, field_name), tuple)

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(build_heroes_rows([]), [])

    def test_missing_registered_at_defaults_to_none(self):
        record = make_hero_record()
        del record["registered_at"]
        row = build_heroes_rows([record])[0]
        self.assertIsNone(row.registered_at)

    def test_row_is_frozen(self):
        row = build_heroes_rows([make_hero_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.hero_id = "changed"

    def test_mutating_source_record_after_build_does_not_affect_row(self):
        record = make_hero_record()
        row = build_heroes_rows([record])[0]
        record["official_key"]["numeros"].append(999)  # mutate the source list in place
        self.assertEqual(row.official_numeros, (12, 21, 23, 34, 40))  # row unaffected


class TestBuildLegendsRows(unittest.TestCase):
    def test_maps_fields_correctly(self):
        rows = build_legends_rows([make_legend_record()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.legend_id, "LEGEND-395e24e0")
        self.assertEqual(row.promotion_threshold, 3)
        self.assertEqual(row.promotion_tier, "LEGEND_TIER_4")
        self.assertEqual(row.criteria_version, "v1")
        self.assertEqual(row.provenance, "legacy")

    def test_empty_list_handled_cleanly(self):
        # No Legends promoted yet in the real project — this must not
        # raise or behave differently from a populated list.
        self.assertEqual(build_legends_rows([]), [])

    def test_row_is_frozen(self):
        row = build_legends_rows([make_legend_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.provenance = "verified"

    def test_multiple_records_preserve_order(self):
        r1 = make_legend_record(legend_id="LEGEND-aaa")
        r2 = make_legend_record(legend_id="LEGEND-bbb")
        rows = build_legends_rows([r1, r2])
        self.assertEqual([r.legend_id for r in rows], ["LEGEND-aaa", "LEGEND-bbb"])


if __name__ == "__main__":
    unittest.main()
