"""Tests for core/services/legend_evaluation.py — configuration loading
and validation for [REGISTO_LENDAS] / [REGISTO_LENDAS_TIERS], plus (Commit
24) a minimal test confirming the caller-supplied promoted_at timestamp
flows verbatim into a new promotion record.
"""

import unittest
from configparser import ConfigParser

from core.services.legend_evaluation import LegendConfigError, evaluate_group, load_legend_config


def make_cfg(criteria_version="v1", limiares="3,5,10,20", tiers=None,
             include_legends_section=True, include_tiers_section=True,
             include_legacy_lendas=True):
    cfg = ConfigParser()
    cfg.optionxform = str

    if include_legacy_lendas:
        # The pre-existing, unrelated narrative "Legendary Characters"
        # section — must never be confused with [REGISTO_LENDAS].
        cfg["LENDAS"] = {
            "ativo": "true",
            "min_numeros": "3",
            "min_estrelas": "2",
            "chance_eco_despertar": "0.10",
            "permitir_necromancia": "true",
        }

    if include_legends_section:
        cfg["REGISTO_LENDAS"] = {"criteria_version": criteria_version, "limiares": limiares}

    if include_tiers_section:
        cfg["REGISTO_LENDAS_TIERS"] = tiers if tiers is not None else {
            "3": "LEGEND_TIER_4",
            "5": "LEGEND_TIER_3",
            "10": "LEGEND_TIER_2",
            "20": "LEGEND_TIER_1",
        }

    return cfg


class TestRegistoLendasLoadsCorrectly(unittest.TestCase):
    """Objective 1 — [REGISTO_LENDAS] loads correctly."""

    def test_valid_config_loads(self):
        cfg = make_cfg()
        result = load_legend_config(cfg)
        self.assertEqual(result["criteria_version"], "v1")
        self.assertEqual(result["thresholds"], [3, 5, 10, 20])

    def test_criteria_version_is_stripped(self):
        cfg = make_cfg(criteria_version="  v2  ")
        result = load_legend_config(cfg)
        self.assertEqual(result["criteria_version"], "v2")

    def test_thresholds_are_returned_sorted_regardless_of_input_order(self):
        cfg = make_cfg(limiares="20,3,10,5")
        result = load_legend_config(cfg)
        self.assertEqual(result["thresholds"], [3, 5, 10, 20])

    def test_thresholds_are_integers_not_strings(self):
        cfg = make_cfg()
        result = load_legend_config(cfg)
        self.assertTrue(all(isinstance(t, int) for t in result["thresholds"]))


class TestRegistoLendasTiersMapping(unittest.TestCase):
    """Objective 2 — [REGISTO_LENDAS_TIERS] produces the expected
    threshold -> tier mapping."""

    def test_tier_map_matches_configured_pairs(self):
        cfg = make_cfg()
        result = load_legend_config(cfg)
        self.assertEqual(result["tier_map"], {3: "LEGEND_TIER_4", 5: "LEGEND_TIER_3", 10: "LEGEND_TIER_2", 20: "LEGEND_TIER_1"})

    def test_tier_order_ranks_largest_threshold_best(self):
        cfg = make_cfg()
        result = load_legend_config(cfg)
        tier_order = result["tier_order"]
        # threshold 20 -> LEGEND_TIER_1 must rank better (lower index) than threshold 3 -> LEGEND_TIER_4
        self.assertLess(tier_order["LEGEND_TIER_1"], tier_order["LEGEND_TIER_4"])
        self.assertLess(tier_order["LEGEND_TIER_2"], tier_order["LEGEND_TIER_3"])

    def test_two_thresholds_may_map_to_the_same_tier(self):
        cfg = make_cfg(limiares="3,5,10,20", tiers={
            "3": "LEGEND_TIER_2", "5": "LEGEND_TIER_2", "10": "LEGEND_TIER_1", "20": "LEGEND_TIER_1",
        })
        result = load_legend_config(cfg)
        self.assertEqual(result["tier_map"][3], result["tier_map"][5])
        self.assertEqual(result["tier_map"][10], result["tier_map"][20])
        # Repeated tiers collapse to one rank, not two.
        self.assertEqual(len(set(result["tier_order"].values())), 2)


class TestValidationRules(unittest.TestCase):
    """Objective 3 — every validation path raises LegendConfigError."""

    def test_missing_registo_lendas_section_fails(self):
        cfg = make_cfg(include_legends_section=False)
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_empty_criteria_version_fails(self):
        cfg = make_cfg(criteria_version="")
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_whitespace_only_criteria_version_fails(self):
        cfg = make_cfg(criteria_version="   ")
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_empty_limiares_fails(self):
        cfg = make_cfg(limiares="")
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_non_numeric_limiar_fails(self):
        cfg = make_cfg(limiares="3,abc,10")
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_zero_limiar_fails(self):
        cfg = make_cfg(limiares="0,5,10", tiers={"0": "LEGEND_TIER_4", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2"})
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_negative_limiar_fails(self):
        # ConfigParser stores raw text; "-5" fails the isdigit() check the
        # same way a non-numeric string would.
        cfg = make_cfg(limiares="-5,5,10", tiers={"-5": "LEGEND_TIER_4", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2"})
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_duplicate_limiar_fails(self):
        cfg = make_cfg(limiares="3,5,5,10")
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_missing_registo_lendas_tiers_section_fails(self):
        cfg = make_cfg(include_tiers_section=False)
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_threshold_without_tier_fails(self):
        # limiares lists 3,5,10,20 but the tiers mapping omits 20.
        cfg = make_cfg(tiers={"3": "LEGEND_TIER_4", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2"})
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_tier_without_threshold_fails(self):
        # [REGISTO_LENDAS_TIERS] has an orphaned entry (50) not present in limiares.
        cfg = make_cfg(limiares="3,5,10,20", tiers={
            "3": "LEGEND_TIER_4", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2",
            "20": "LEGEND_TIER_1", "50": "LEGEND_TIER_0",
        })
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_invalid_empty_tier_value_fails(self):
        cfg = make_cfg(limiares="3,5,10,20", tiers={
            "3": "", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2", "20": "LEGEND_TIER_1",
        })
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_invalid_tier_key_non_numeric_fails(self):
        cfg = make_cfg(limiares="3,5,10,20", tiers={
            "tres": "LEGEND_TIER_4", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2", "20": "LEGEND_TIER_1",
        })
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)

    def test_all_thresholds_non_positive_fails(self):
        cfg = make_cfg(limiares="0", tiers={"0": "LEGEND_TIER_1"})
        with self.assertRaises(LegendConfigError):
            load_legend_config(cfg)


class TestLegacyLendasSectionDoesNotInterfere(unittest.TestCase):
    """Objective 4 — the pre-existing, unrelated [LENDAS] section must
    never be read by, or confused with, load_legend_config()."""

    def test_valid_config_loads_with_legacy_lendas_section_present(self):
        cfg = make_cfg(include_legacy_lendas=True)
        result = load_legend_config(cfg)
        self.assertEqual(result["criteria_version"], "v1")
        self.assertEqual(result["thresholds"], [3, 5, 10, 20])

    def test_valid_config_loads_identically_without_legacy_lendas_section(self):
        with_legacy = load_legend_config(make_cfg(include_legacy_lendas=True))
        without_legacy = load_legend_config(make_cfg(include_legacy_lendas=False))
        self.assertEqual(with_legacy, without_legacy)

    def test_legacy_lendas_section_is_never_read(self):
        # Even if [LENDAS] happens to define keys with the same NAMES as
        # [REGISTO_LENDAS] (criteria_version/limiares), load_legend_config
        # must still read exclusively from [REGISTO_LENDAS].
        cfg = make_cfg()
        cfg["LENDAS"]["criteria_version"] = "should-never-be-read"
        cfg["LENDAS"]["limiares"] = "999"
        result = load_legend_config(cfg)
        self.assertEqual(result["criteria_version"], "v1")
        self.assertEqual(result["thresholds"], [3, 5, 10, 20])

    def test_missing_legacy_lendas_section_entirely_does_not_break_loading(self):
        cfg = ConfigParser()
        cfg.optionxform = str
        cfg["REGISTO_LENDAS"] = {"criteria_version": "v1", "limiares": "3,5,10,20"}
        cfg["REGISTO_LENDAS_TIERS"] = {"3": "LEGEND_TIER_4", "5": "LEGEND_TIER_3", "10": "LEGEND_TIER_2", "20": "LEGEND_TIER_1"}
        result = load_legend_config(cfg)
        self.assertEqual(result["criteria_version"], "v1")


class TestEvaluateGroupPromotedAt(unittest.TestCase):
    def test_promoted_at_is_written_verbatim_into_a_new_promotion_record(self):
        legend_config = {
            "criteria_version": "v1",
            "thresholds": [1],
            "tier_map": {1: "LEGEND_TIER_1"},
            "tier_order": {"LEGEND_TIER_1": 0},
        }
        heroes_in_group = [{
            "hero_id": "HERO-2099-001-aaaa1111",
            "draw_id": "001/2099",
            "draw_date": "2099-01-01",
            "entity_id": "H-1",
            "entity_name": "Test",
            "race": "Elfo",
            "generation": 1,
            "predicted_key": {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
            "provenance": "verified",
        }]

        decision = evaluate_group(
            "sp-1", heroes_in_group, legend_config,
            existing_legend=None, project_version="V99", git_commit="deadbeef",
            promoted_at="2099-06-15T12:00:00+00:00",
        )

        self.assertEqual(decision["action"], "promote")
        self.assertEqual(decision["record"]["promoted_at"], "2099-06-15T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
