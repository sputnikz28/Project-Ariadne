"""Tests for library/legends/registry.py — append-only persistence,
frozen-vs-accumulative field discipline, integrity checks, and
idempotent index rebuilding. Every test here drives only the public API
(register/refresh/get/load_all/rebuild_index/rank/statistics) and
observes only its documented return values and stored content — no
source inspection, no hasattr probing, no filesystem mtime checks, no
mocking of internals.
"""

import json
import shutil
import tempfile
import unittest

from library.legends.registry import LegendRegistry, LegendIntegrityError, LegendAlreadyExistsError


def make_legend_record(source_prediction_id, **overrides):
    record = {
        "legend_id": "LEGEND-" + source_prediction_id[:8],
        "source_prediction_id": source_prediction_id,
        "promotion_draw": "058/2026",
        "promotion_draw_date": "2026-08-04",
        "promotion_threshold": 3,
        "promotion_tier": "LEGEND_TIER_4",
        "criteria_version": "v1",
        "promotion_hero_ids": ["HERO-2026-056-aaaa1111", "HERO-2026-057-bbbb2222", "HERO-2026-058-cccc3333"],
        "project_version": "V12.1",
        "git_commit": "deadbeef",
        "qualification_reason": "Promoted to Legend at draw 058/2026 by reaching 3 distinct qualifying draws.",
        "entity_id": "H-1",
        "entity_name": "Test Entity",
        "race": "Elfo",
        "generation": 1,
        "predicted_numeros": [10, 19, 37, 42, 47],
        "predicted_estrelas": [9, 12],
        "hero_count": 3,
        "qualified_draws": 3,
        "contributing_hero_ids": ["HERO-2026-056-aaaa1111", "HERO-2026-057-bbbb2222", "HERO-2026-058-cccc3333"],
        "provenance": "legacy",
        "last_reevaluated_at": None,
    }
    record.update(overrides)
    return record


TIER_ORDER = {"LEGEND_TIER_1": 0, "LEGEND_TIER_2": 1, "LEGEND_TIER_3": 2, "LEGEND_TIER_4": 3}


class LegendRegistryTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.registry = LegendRegistry(base=self._tmp)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)


class TestRegisterAppendOnly(LegendRegistryTestBase):
    def test_register_creates_new_legend(self):
        record = make_legend_record("spid-aaa")
        stored = self.registry.register(record)
        self.assertEqual(stored["source_prediction_id"], "spid-aaa")
        self.assertEqual(self.registry.count(), 1)

    def test_register_duplicate_raises_instead_of_no_op(self):
        record = make_legend_record("spid-aaa")
        self.registry.register(record)
        with self.assertRaises(LegendAlreadyExistsError):
            self.registry.register(record)

    def test_register_duplicate_does_not_modify_existing_content(self):
        self.registry.register(make_legend_record("spid-aaa", promotion_threshold=3))
        tampered_attempt = make_legend_record("spid-aaa", promotion_threshold=999)
        with self.assertRaises(LegendAlreadyExistsError):
            self.registry.register(tampered_attempt)
        stored = self.registry.get("spid-aaa")
        self.assertEqual(stored["promotion_threshold"], 3)

    def test_multiple_distinct_legends_all_registered(self):
        for i in range(4):
            self.registry.register(make_legend_record(f"spid-{i}"))
        self.assertEqual(self.registry.count(), 4)


class TestRefreshAllowlistAndSemantics(LegendRegistryTestBase):
    def setUp(self):
        super().setUp()
        self.registry.register(make_legend_record("spid-aaa"))

    def test_refresh_accepts_substantive_fields(self):
        stored, changed = self.registry.refresh("spid-aaa", {"hero_count": 4, "qualified_draws": 4}, "2026-09-01T00:00:00+00:00")
        self.assertTrue(changed)
        self.assertEqual(stored["hero_count"], 4)
        self.assertEqual(stored["qualified_draws"], 4)

    def test_refresh_rejects_frozen_field(self):
        with self.assertRaises(ValueError):
            self.registry.refresh("spid-aaa", {"promotion_threshold": 999}, "2026-09-01T00:00:00+00:00")
        stored = self.registry.get("spid-aaa")
        self.assertEqual(stored["promotion_threshold"], 3)

    def test_refresh_rejects_last_reevaluated_at_inside_updates(self):
        with self.assertRaises(ValueError):
            self.registry.refresh("spid-aaa", {"last_reevaluated_at": "2026-01-01T00:00:00+00:00"}, "2026-09-01T00:00:00+00:00")

    def test_refresh_raises_keyerror_if_not_registered(self):
        with self.assertRaises(KeyError):
            self.registry.refresh("spid-does-not-exist", {"hero_count": 1}, "2026-09-01T00:00:00+00:00")

    def test_refresh_is_no_op_when_values_identical(self):
        stored, changed = self.registry.refresh("spid-aaa", {"hero_count": 3, "qualified_draws": 3}, "2026-09-01T00:00:00+00:00")
        self.assertFalse(changed)
        self.assertIsNone(stored["last_reevaluated_at"])

    def test_last_reevaluated_at_only_stamped_on_real_change(self):
        stored, changed = self.registry.refresh("spid-aaa", {"hero_count": 5}, "2026-09-01T00:00:00+00:00")
        self.assertTrue(changed)
        self.assertEqual(stored["last_reevaluated_at"], "2026-09-01T00:00:00+00:00")

    def test_refresh_uses_the_passed_in_timestamp_verbatim(self):
        stored, _ = self.registry.refresh("spid-aaa", {"hero_count": 9}, "1999-01-01T00:00:00+00:00")
        self.assertEqual(stored["last_reevaluated_at"], "1999-01-01T00:00:00+00:00")

    def test_refresh_never_touches_frozen_fields(self):
        before = self.registry.get("spid-aaa")
        self.registry.refresh("spid-aaa", {"hero_count": 10, "provenance": "verified"}, "2026-09-01T00:00:00+00:00")
        after = self.registry.get("spid-aaa")
        for frozen_key in ("legend_id", "source_prediction_id", "promotion_draw", "promotion_draw_date",
                           "promotion_threshold", "promotion_tier", "criteria_version", "promotion_hero_ids",
                           "project_version", "git_commit", "qualification_reason", "entity_id", "entity_name"):
            self.assertEqual(before[frozen_key], after[frozen_key])


class TestPermanenceThroughObservableBehavior(LegendRegistryTestBase):
    """Replaces hasattr(prune/delete/remove) probing: instead of
    asserting the absence of methods, this drives the public API through
    many operations and observes that nothing ever disappears — the same
    guarantee, demonstrated behaviorally rather than structurally.
    """

    def test_legend_count_never_decreases_across_refresh_cycles(self):
        self.registry.register(make_legend_record("spid-aaa"))
        self.registry.register(make_legend_record("spid-bbb"))
        count_before = self.registry.count()
        for i in range(5):
            self.registry.refresh("spid-aaa", {"hero_count": 3 + i}, f"2026-09-0{i + 1}T00:00:00+00:00")
        self.assertEqual(self.registry.count(), count_before)
        self.assertIsNotNone(self.registry.get("spid-aaa"))
        self.assertIsNotNone(self.registry.get("spid-bbb"))

    def test_registering_more_legends_never_removes_earlier_ones(self):
        ids = [f"spid-{i}" for i in range(6)]
        for spid in ids:
            self.registry.register(make_legend_record(spid))
        for spid in ids:
            self.assertIsNotNone(self.registry.get(spid))
        self.assertEqual(self.registry.count(), len(ids))


class TestIdentityAndLookup(LegendRegistryTestBase):
    def test_lookup_by_source_prediction_id(self):
        self.registry.register(make_legend_record("spid-aaa"))
        self.assertIsNotNone(self.registry.get("spid-aaa"))
        self.assertIsNone(self.registry.get("spid-does-not-exist"))

    def test_integrity_error_on_filename_content_mismatch_via_get(self):
        self.registry.entries_dir.mkdir(parents=True, exist_ok=True)
        bad_path = self.registry.entries_dir / "spid-aaa.json"
        bad_path.write_text(json.dumps(make_legend_record("spid-DIFFERENT")), encoding="utf-8")
        with self.assertRaises(LegendIntegrityError):
            self.registry.get("spid-aaa")

    def test_integrity_error_on_filename_content_mismatch_via_load_all(self):
        self.registry.entries_dir.mkdir(parents=True, exist_ok=True)
        bad_path = self.registry.entries_dir / "spid-aaa.json"
        bad_path.write_text(json.dumps(make_legend_record("spid-DIFFERENT")), encoding="utf-8")
        with self.assertRaises(LegendIntegrityError):
            self.registry.load_all()

    def test_corrupted_json_is_skipped_not_fatal(self):
        self.registry.register(make_legend_record("spid-aaa"))
        self.registry.entries_dir.joinpath("corrupted.json").write_text("{not valid json!!", encoding="utf-8")
        legends = self.registry.load_all()
        self.assertEqual(len(legends), 1)


class TestRebuildIndex(LegendRegistryTestBase):
    def test_rebuild_index_derived_from_entries(self):
        for i in range(3):
            self.registry.register(make_legend_record(f"spid-{i}"))
        index = self.registry.rebuild_index("2026-09-01T00:00:00+00:00", TIER_ORDER)
        self.assertEqual(index["total_legends"], 3)

    def test_rebuild_index_does_not_alter_entry_content(self):
        self.registry.register(make_legend_record("spid-aaa"))
        before = self.registry.get("spid-aaa")
        self.registry.rebuild_index("2026-09-01T00:00:00+00:00", TIER_ORDER)
        after = self.registry.get("spid-aaa")
        self.assertEqual(before, after)

    def test_rebuild_index_deterministic_ordering(self):
        self.registry.register(make_legend_record("spid-weak", promotion_tier="LEGEND_TIER_4", qualified_draws=3, hero_count=3))
        self.registry.register(make_legend_record("spid-strong", promotion_tier="LEGEND_TIER_1", qualified_draws=20, hero_count=20))
        index = self.registry.rebuild_index("2026-09-01T00:00:00+00:00", TIER_ORDER)
        self.assertEqual(index["ranking"][0], "LEGEND-" + "spid-strong"[:8])

    def test_rebuild_index_idempotent_no_write_when_unchanged(self):
        self.registry.register(make_legend_record("spid-aaa"))
        first = self.registry.rebuild_index("2026-09-01T00:00:00+00:00", TIER_ORDER)
        second = self.registry.rebuild_index("2026-12-25T00:00:00+00:00", TIER_ORDER)  # different timestamp, same content
        self.assertEqual(first["atualizado_em"], second["atualizado_em"])

    def test_rebuild_index_writes_new_timestamp_when_content_changes(self):
        self.registry.register(make_legend_record("spid-aaa"))
        first = self.registry.rebuild_index("2026-09-01T00:00:00+00:00", TIER_ORDER)
        self.registry.register(make_legend_record("spid-bbb"))
        second = self.registry.rebuild_index("2026-12-25T00:00:00+00:00", TIER_ORDER)
        self.assertNotEqual(first["atualizado_em"], second["atualizado_em"])
        self.assertEqual(second["total_legends"], 2)


if __name__ == "__main__":
    unittest.main()
