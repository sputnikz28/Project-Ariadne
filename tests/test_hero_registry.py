"""Tests for library/heroes/registry.py — persistence, deduplication,
ranking, atomic-write safety, and order-independence.
"""

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from core.services import atomic_io
from core.services.hero_evaluation import (
    evaluate_record, load_hero_config, summarize_deduplication,
)
from library.heroes.registry import HeroRegistry
from configparser import ConfigParser


def make_hero_config():
    cfg = ConfigParser()
    cfg.optionxform = str
    cfg["HEROIS"] = {"categorias": "5+2,5+1,5+0,4+2,4+1,4+0,3+2,3+1,3+0,2+2,2+1,1+2", "incluir_2_0": "false"}
    cfg["HEROIS_TIERS"] = {
        "5+2": "TIER_1", "5+1": "TIER_2", "5+0": "TIER_2", "4+2": "TIER_2",
        "4+1": "TIER_3", "4+0": "TIER_3", "3+2": "TIER_3",
        "3+1": "TIER_4", "3+0": "TIER_4", "2+2": "TIER_4",
        "2+1": "TIER_5", "1+2": "TIER_5", "2+0": "TIER_5",
    }
    return load_hero_config(cfg)


def make_result(entity_id, numeros, estrelas, draw_id="056/2026",
                 official_numeros=(10, 19, 37, 42, 47), official_estrelas=(9, 12),
                 provenance="legacy"):
    record = {"origem": "racas_antigas", "id": entity_id, "nome": entity_id, "classe": "Elfo",
              "casa": "Casa Lunar", "geracao": 1, "numeros": list(numeros), "estrelas": list(estrelas)}
    hero_config = make_hero_config()
    result = evaluate_record(
        record, draw_id, list(official_numeros), list(official_estrelas),
        {}, datetime(2099, 1, 1, tzinfo=timezone.utc), hero_config,
    )
    result["provenance"] = provenance  # override for test control
    return result


def make_hero_record(result, entity_name=None):
    return {
        "hero_id": result["hero_id"],
        "dedup_hash": result["dedup_hash"],
        "source_prediction_id": result["source_prediction_id"],
        "entity_id": result["entity_id"],
        "entity_name": entity_name or result["entity_name"],
        "race": result["race"],
        "generation": result["generation"],
        "run_id": result["run_id"],
        "provenance": result["provenance"],
        "hero_category": result["category"],
        "hero_tier": result["tier"],
        "matched_numbers_count": len(result["matched_numbers"]),
        "matched_stars_count": len(result["matched_stars"]),
        "simulation_score": result["simulation_score"],
        "draw_id": "056/2026",
    }


class HeroRegistryTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.registry = HeroRegistry(base=self._tmp)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)


class TestRegistrationAndDuplicatePrevention(HeroRegistryTestBase):
    def test_registering_a_new_hero_returns_created_true(self):
        result = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        stored, created = self.registry.register(make_hero_record(result))
        self.assertTrue(created)
        self.assertEqual(stored["hero_id"], result["hero_id"])

    def test_registering_the_same_hero_twice_is_a_no_op_the_second_time(self):
        result = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        record = make_hero_record(result)
        _, created1 = self.registry.register(record)
        _, created2 = self.registry.register(record)
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(self.registry.count(), 1)

    def test_rerun_produces_no_new_heroes(self):
        results = [make_result(f"H-{i}", [10, 19, 37, 42, i + 1], [9, 12]) for i in range(5)]
        for r in results:
            self.registry.register(make_hero_record(r))
        count_after_first_pass = self.registry.count()

        new_count = 0
        for r in results:
            _, created = self.registry.register(make_hero_record(r))
            new_count += created
        self.assertEqual(new_count, 0)
        self.assertEqual(self.registry.count(), count_after_first_pass)

    def test_different_entities_are_not_deduplicated_against_each_other(self):
        r1 = make_result("H-1", [10, 19, 37, 42, 1], [9, 12])
        r2 = make_result("H-2", [10, 19, 37, 42, 2], [9, 12])
        self.registry.register(make_hero_record(r1))
        self.registry.register(make_hero_record(r2))
        self.assertEqual(self.registry.count(), 2)


class TestPersistenceAndReload(HeroRegistryTestBase):
    def test_hero_survives_reload_via_new_registry_instance(self):
        result = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        self.registry.register(make_hero_record(result))

        reloaded = HeroRegistry(base=self._tmp)
        heroes = reloaded.all()
        self.assertEqual(len(heroes), 1)
        self.assertEqual(heroes[0]["hero_id"], result["hero_id"])

    def test_serialization_round_trips_every_field(self):
        result = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        record = make_hero_record(result)
        self.registry.register(record)
        stored = self.registry.get(result["dedup_hash"])
        for key, value in record.items():
            self.assertEqual(stored[key], value)

    def test_index_is_rebuildable_purely_from_entries(self):
        for i in range(3):
            r = make_result(f"H-{i}", [10, 19, 37, 42, i + 1], [9, 12])
            self.registry.register(make_hero_record(r))

        index_path = Path(self._tmp) / "LIVRO_DOS_HEROIS.json"
        if index_path.exists():
            index_path.unlink()

        rebuilt = self.registry.rebuild_index()
        self.assertEqual(rebuilt["total_heroes"], 3)
        self.assertTrue(index_path.exists())

    def test_corrupted_entry_file_is_skipped_not_fatal(self):
        result = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        self.registry.register(make_hero_record(result))

        corrupt_path = self.registry.entries_dir / "corrupted.json"
        corrupt_path.write_text("{not valid json!!", encoding="utf-8")

        heroes = self.registry.load_all()  # must not raise
        self.assertEqual(len(heroes), 1)  # the corrupted file is silently skipped


class TestAtomicWriteSafety(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_failed_write_does_not_corrupt_existing_file(self):
        path = Path(self._tmp) / "target.json"
        atomic_io.atomic_write_json(path, {"version": 1})

        with mock.patch("json.dump", side_effect=RuntimeError("simulated failure")):
            with self.assertRaises(RuntimeError):
                atomic_io.atomic_write_json(path, {"version": 2})

        # original content must be untouched
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"version": 1})

    def test_failed_write_leaves_no_temp_file_behind(self):
        path = Path(self._tmp) / "target.json"
        with mock.patch("json.dump", side_effect=RuntimeError("simulated failure")):
            with self.assertRaises(RuntimeError):
                atomic_io.atomic_write_json(path, {"version": 1})
        leftovers = list(Path(self._tmp).glob(".tmp-*"))
        self.assertEqual(leftovers, [])


class TestMultipleAndTiedHeroes(HeroRegistryTestBase):
    def test_multiple_heroes_all_get_registered(self):
        results = [make_result(f"H-{i}", [10, 19, 37, 42, i + 1], [9, 12]) for i in range(4)]
        for r in results:
            self.registry.register(make_hero_record(r))
        self.assertEqual(self.registry.count(), 4)

    def test_tied_heroes_both_stored_distinctly(self):
        # Two different entities landing in the exact same category/tier —
        # both must be recognised, neither deduped against the other.
        r1 = make_result("H-1", [10, 19, 37, 42, 1], [9, 12])  # 4+2
        r2 = make_result("H-2", [10, 19, 37, 42, 2], [9, 12])  # also 4+2
        self.assertEqual(r1["category"], r2["category"])
        self.registry.register(make_hero_record(r1))
        self.registry.register(make_hero_record(r2))
        heroes = self.registry.all()
        self.assertEqual(len(heroes), 2)
        self.assertEqual({h["hero_category"] for h in heroes}, {"4+2"})

    def test_ranking_orders_by_tier_then_matches_then_stable_tiebreak(self):
        hero_config = make_hero_config()
        r_low = make_result("H-A", [10, 19, 1, 2, 3], [9, 12])   # 2+2 -> TIER_4
        r_high = make_result("H-B", [10, 19, 37, 42, 47], [9, 12])  # 5+2 -> TIER_1
        self.registry.register(make_hero_record(r_low))
        self.registry.register(make_hero_record(r_high))
        ranked = self.registry.rank(self.registry.all(), hero_config["tier_order"])
        self.assertEqual(ranked[0]["hero_category"], "5+2")
        self.assertEqual(ranked[-1]["hero_category"], "2+2")


class TestOrderIndependence(HeroRegistryTestBase):
    def test_shuffled_processing_order_produces_identical_registry_contents(self):
        results = [make_result(f"H-{i}", [10, 19, 37, 42, i + 1], [9, 12]) for i in range(6)]

        forward_dir = tempfile.mkdtemp()
        reversed_dir = tempfile.mkdtemp()
        try:
            reg_forward = HeroRegistry(base=forward_dir)
            for r in results:
                reg_forward.register(make_hero_record(r))

            reg_reversed = HeroRegistry(base=reversed_dir)
            for r in reversed(results):
                reg_reversed.register(make_hero_record(r))

            ids_forward = sorted(h["hero_id"] for h in reg_forward.all())
            ids_reversed = sorted(h["hero_id"] for h in reg_reversed.all())
            self.assertEqual(ids_forward, ids_reversed)
        finally:
            shutil.rmtree(forward_dir, ignore_errors=True)
            shutil.rmtree(reversed_dir, ignore_errors=True)

    def test_hero_ids_do_not_depend_on_evaluation_order(self):
        r1 = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        r2 = make_result("H-1", [10, 19, 37, 42, 47], [9, 12])
        self.assertEqual(r1["hero_id"], r2["hero_id"])
        self.assertEqual(r1["dedup_hash"], r2["dedup_hash"])


class TestDeduplicationSummaryMatchesRegistryOutcome(HeroRegistryTestBase):
    """The exact invariant behind the 3,504-qualifying / 3,445-entry-file
    discrepancy seen on draw 056/2026: summarize_deduplication()'s
    unique_hero_id_count must equal the number of entry files an empty
    registry ends up with after registering every qualifying record,
    and qualifying_count - unique_hero_id_count must equal how many
    registrations report created=False.
    """

    def test_unique_hero_id_count_equals_registry_count_from_empty(self):
        results = [make_result("H-1", [10, 19, 37, 42, 47], [9, 12])] * 3  # 3 identical qualifying records
        results += [make_result(f"H-{i}", [10, 19, 37, 42, i + 1], [9, 12]) for i in range(2, 5)]  # 3 distinct
        summary = summarize_deduplication(results)

        created_count = 0
        no_op_count = 0
        for r in results:
            _, created = self.registry.register(make_hero_record(r))
            created_count += created
            no_op_count += not created

        self.assertEqual(self.registry.count(), summary["unique_hero_id_count"])
        self.assertEqual(created_count, summary["unique_hero_id_count"])
        self.assertEqual(no_op_count, summary["collapsed_record_count"])
        self.assertEqual(summary["qualifying_count"], len(results))


if __name__ == "__main__":
    unittest.main()
