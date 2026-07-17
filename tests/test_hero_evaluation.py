"""Tests for core/services/hero_evaluation.py — the Hero Evaluation Engine.

Covers recognition categories, config validation, and the structural
guarantee that simulation_score never influences qualification.
"""

import inspect
import unittest
from configparser import ConfigParser

from core.services import hero_evaluation as engine
from core.services.hero_evaluation import (
    HeroConfigError,
    category_for,
    compute_dedup_hash,
    compute_source_prediction_id,
    evaluate_record,
    hero_display_id,
    load_hero_config,
    matched_values,
    simulation_score,
    summarize_deduplication,
)


def make_cfg(categorias="5+2,5+1,5+0,4+2,4+1,4+0,3+2,3+1,3+0,2+2,2+1,1+2",
             incluir_2_0="false", tiers=None):
    cfg = ConfigParser()
    cfg.optionxform = str
    cfg["HEROIS"] = {"categorias": categorias, "incluir_2_0": incluir_2_0}
    cfg["HEROIS_TIERS"] = tiers or {
        "5+2": "TIER_1",
        "5+1": "TIER_2", "5+0": "TIER_2", "4+2": "TIER_2",
        "4+1": "TIER_3", "4+0": "TIER_3", "3+2": "TIER_3",
        "3+1": "TIER_4", "3+0": "TIER_4", "2+2": "TIER_4",
        "2+1": "TIER_5", "1+2": "TIER_5", "2+0": "TIER_5",
    }
    return cfg


class TestRecognitionCategories(unittest.TestCase):
    """Every category the spec lists, verified against matched values."""

    def test_all_thirteen_categories_classified_correctly(self):
        cases = [
            (5, 2, "5+2"), (5, 1, "5+1"), (5, 0, "5+0"),
            (4, 2, "4+2"), (4, 1, "4+1"), (4, 0, "4+0"),
            (3, 2, "3+2"), (3, 1, "3+1"), (3, 0, "3+0"),
            (2, 2, "2+2"), (2, 1, "2+1"),
            (1, 2, "1+2"), (2, 0, "2+0"),
        ]
        for matched_n, matched_e, expected in cases:
            with self.subTest(matched_n=matched_n, matched_e=matched_e):
                self.assertEqual(category_for(matched_n, matched_e), expected)

    def test_matched_values_uses_set_intersection_and_difference(self):
        result = matched_values([1, 2, 3, 4, 5], [1, 2], [3, 4, 5, 6, 7], [2, 3])
        self.assertEqual(result["matched_numbers"], [3, 4, 5])
        self.assertEqual(result["matched_stars"], [2])
        self.assertEqual(result["missed_numbers"], [6, 7])
        self.assertEqual(result["missed_stars"], [3])
        self.assertEqual(result["extra_numbers"], [1, 2])
        self.assertEqual(result["extra_stars"], [1])

    def test_non_qualifying_category_still_classified_but_not_a_hero(self):
        cfg = make_cfg()
        hero_config = load_hero_config(cfg)
        record = {"origem": "x", "id": "H-1", "geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}
        # 0 matched numbers, 0 matched stars -> "0+0", not in any enabled category
        result = evaluate_record(record, "056/2026", [10, 20, 30, 40, 50], [11, 12], {}, __import__("datetime").datetime(2099, 1, 1), hero_config)
        self.assertEqual(result["category"], "0+0")
        self.assertFalse(result["qualifies"])
        self.assertIsNone(result["tier"])


class TestSimulationScoreIsDescriptiveOnly(unittest.TestCase):
    def test_score_formula_matches_compare_result(self):
        # Reused verbatim from compare_result.py::avaliar_registo
        self.assertEqual(simulation_score(5, 2), 5 * 10 + 2 * 5 + 8 + 5)
        self.assertEqual(simulation_score(3, 0), 3 * 10 + 0 + 8 + 0)
        self.assertEqual(simulation_score(0, 0), 0)

    def test_score_does_not_appear_in_qualification_logic(self):
        # Structural guarantee: evaluate_record's qualification decision
        # only reads hero_config["enabled_categories"] and the computed
        # category string — simulation_score is computed separately and
        # merged into the result dict afterward, never consulted.
        source = inspect.getsource(engine.evaluate_record)
        qualifies_line = [l for l in source.splitlines() if "qualifies =" in l][0]
        self.assertNotIn("score", qualifies_line)


class TestHeroConfigValidation(unittest.TestCase):
    def test_valid_config_loads(self):
        cfg = make_cfg()
        result = load_hero_config(cfg)
        self.assertIn("5+2", result["enabled_categories"])
        self.assertNotIn("2+0", result["enabled_categories"])

    def test_missing_heroes_section_fails(self):
        cfg = ConfigParser()
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)

    def test_empty_categorias_fails(self):
        cfg = make_cfg(categorias="")
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)

    def test_invalid_category_syntax_fails(self):
        cfg = make_cfg(categorias="5+2,6+2")
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)

    def test_duplicate_category_fails(self):
        cfg = make_cfg(categorias="5+2,5+2")
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)

    def test_2_0_listed_directly_in_categorias_fails(self):
        cfg = make_cfg(categorias="5+2,2+0")
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)

    def test_2_0_enabled_via_flag_is_included(self):
        cfg = make_cfg(incluir_2_0="true")
        result = load_hero_config(cfg)
        self.assertIn("2+0", result["enabled_categories"])

    def test_2_0_disabled_by_default(self):
        cfg = make_cfg()
        result = load_hero_config(cfg)
        self.assertFalse(result["incluir_2_0"])
        self.assertNotIn("2+0", result["enabled_categories"])

    def test_enabled_category_missing_tier_fails(self):
        tiers = {"5+2": "TIER_1"}  # missing tiers for the other 11 default categories
        cfg = make_cfg(tiers=tiers)
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)

    def test_missing_heroes_tiers_section_fails(self):
        cfg = ConfigParser()
        cfg.optionxform = str
        cfg["HEROIS"] = {"categorias": "5+2", "incluir_2_0": "false"}
        with self.assertRaises(HeroConfigError):
            load_hero_config(cfg)


class TestDeterministicIdentity(unittest.TestCase):
    def test_source_prediction_id_is_deterministic(self):
        record = {"origem": "racas_antigas", "id": "H-00001", "geracao": 3, "numeros": [5, 3, 1, 4, 2], "estrelas": [2, 1], "classe": "Elfo", "casa": "Casa Lunar"}
        id1 = compute_source_prediction_id(record)
        id2 = compute_source_prediction_id(dict(record))
        self.assertEqual(id1, id2)

    def test_source_prediction_id_ignores_number_order(self):
        r1 = {"origem": "x", "id": "H-1", "geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}
        r2 = {"origem": "x", "id": "H-1", "geracao": 1, "numeros": [5, 4, 3, 2, 1], "estrelas": [2, 1]}
        self.assertEqual(compute_source_prediction_id(r1), compute_source_prediction_id(r2))

    def test_different_records_produce_different_ids(self):
        r1 = {"origem": "x", "id": "H-1", "geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}
        r2 = {"origem": "x", "id": "H-2", "geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}
        self.assertNotEqual(compute_source_prediction_id(r1), compute_source_prediction_id(r2))

    def test_hero_id_stable_and_dedup_key_excludes_run_id(self):
        spid = "abc123"
        h1 = compute_dedup_hash("056/2026", spid)
        h2 = compute_dedup_hash("056/2026", spid)
        self.assertEqual(h1, h2)
        display = hero_display_id("056/2026", h1)
        self.assertTrue(display.startswith("HERO-2026-056-"))
        self.assertEqual(len(display), len("HERO-2026-056-") + 8)

    def test_different_draw_produces_different_dedup_hash(self):
        spid = "abc123"
        self.assertNotEqual(
            compute_dedup_hash("055/2026", spid),
            compute_dedup_hash("056/2026", spid),
        )


class TestDeduplicationSummary(unittest.TestCase):
    def _make_records(self, entity_id, geracao, numeros, estrelas, classe="Elfo", casa="Casa Lunar", origem="racas_antigas"):
        cfg = make_cfg()
        hero_config = load_hero_config(cfg)
        record = {"origem": origem, "id": entity_id, "nome": entity_id, "geracao": geracao,
                   "numeros": numeros, "estrelas": estrelas, "classe": classe, "casa": casa}
        return evaluate_record(record, "056/2026", [10, 19, 37, 42, 47], [9, 12], {},
                                __import__("datetime").datetime(2099, 1, 1), hero_config)

    def test_no_duplicates_means_zero_collapsed(self):
        results = [self._make_records(f"H-{i}", 1, [10, 19, 37, 42, i + 1], [9, 12]) for i in range(3)]
        summary = summarize_deduplication(results)
        self.assertEqual(summary["qualifying_count"], 3)
        self.assertEqual(summary["unique_hero_id_count"], 3)
        self.assertEqual(summary["duplicate_hero_id_groups"], 0)
        self.assertEqual(summary["collapsed_record_count"], 0)
        self.assertEqual(summary["rejected_record_count"], 0)

    def test_identical_records_collapse_into_one_hero_id(self):
        r1 = self._make_records("H-1", 3, [10, 19, 37, 42, 47], [9, 12])
        r2 = self._make_records("H-1", 3, [10, 19, 37, 42, 47], [9, 12])
        r3 = self._make_records("H-2", 3, [10, 19, 37, 42, 47], [9, 12])
        summary = summarize_deduplication([r1, r2, r3])
        self.assertEqual(summary["qualifying_count"], 3)
        self.assertEqual(summary["unique_hero_id_count"], 2)
        self.assertEqual(summary["duplicate_hero_id_groups"], 1)
        self.assertEqual(summary["collapsed_record_count"], 1)

    def test_records_differing_only_by_display_name_still_collapse(self):
        # nome/entity_name is deliberately not part of the identity hash —
        # this documents that behaviour rather than hiding it.
        base = {"origem": "racas_antigas", "id": "H-1", "geracao": 3,
                "numeros": [10, 19, 37, 42, 47], "estrelas": [9, 12], "classe": "Elfo", "casa": "Casa Lunar"}
        cfg = make_cfg()
        hero_config = load_hero_config(cfg)
        from datetime import datetime as dt
        r1 = evaluate_record({**base, "nome": "Morgana dos Ossos"}, "056/2026", [10, 19, 37, 42, 47], [9, 12], {}, dt(2099, 1, 1), hero_config)
        r2 = evaluate_record({**base, "nome": "Elarion da Lua Fria"}, "056/2026", [10, 19, 37, 42, 47], [9, 12], {}, dt(2099, 1, 1), hero_config)
        self.assertEqual(r1["hero_id"], r2["hero_id"])
        summary = summarize_deduplication([r1, r2])
        self.assertEqual(summary["unique_hero_id_count"], 1)
        self.assertEqual(summary["collapsed_record_count"], 1)

    def test_empty_input_does_not_crash(self):
        summary = summarize_deduplication([])
        self.assertEqual(summary["qualifying_count"], 0)
        self.assertEqual(summary["unique_hero_id_count"], 0)
        self.assertEqual(summary["collapsed_record_count"], 0)


class TestNoRandomness(unittest.TestCase):
    def test_engine_module_never_imports_random_or_secrets(self):
        source = inspect.getsource(engine)
        self.assertNotIn("import random", source)
        self.assertNotIn("import secrets", source)
        self.assertNotIn("random.", source)
        self.assertNotIn("secrets.", source)


if __name__ == "__main__":
    unittest.main()
