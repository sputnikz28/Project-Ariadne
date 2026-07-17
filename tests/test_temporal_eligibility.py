"""Tests for the temporal provenance model — verified / legacy / ineligible
/ unresolved — in core/services/hero_evaluation.py.
"""

import unittest
from datetime import datetime, timedelta, timezone

from core.services.hero_evaluation import classify_temporal_provenance

DRAW_DT = datetime(2026, 7, 14, 18, 0, 0, tzinfo=timezone.utc)


def manifest(completed_at):
    return {"run_id": "RUN-x", "completed_at": completed_at}


class TestTemporalProvenance(unittest.TestCase):
    def test_prediction_before_official_result_is_verified(self):
        before = (DRAW_DT - timedelta(days=1)).isoformat()
        record = {"run_id": "RUN-x"}
        status = classify_temporal_provenance(record, {"RUN-x": manifest(before)}, DRAW_DT)
        self.assertEqual(status, "verified")

    def test_prediction_after_official_result_is_ineligible(self):
        after = (DRAW_DT + timedelta(days=1)).isoformat()
        record = {"run_id": "RUN-x"}
        status = classify_temporal_provenance(record, {"RUN-x": manifest(after)}, DRAW_DT)
        self.assertEqual(status, "ineligible")

    def test_prediction_at_exact_draw_instant_is_ineligible(self):
        record = {"run_id": "RUN-x"}
        status = classify_temporal_provenance(record, {"RUN-x": manifest(DRAW_DT.isoformat())}, DRAW_DT)
        self.assertEqual(status, "ineligible")

    def test_no_run_id_is_legacy(self):
        record = {}  # predates the provenance system entirely
        status = classify_temporal_provenance(record, {}, DRAW_DT)
        self.assertEqual(status, "legacy")

    def test_run_id_present_but_manifest_missing_is_unresolved(self):
        record = {"run_id": "RUN-does-not-exist"}
        status = classify_temporal_provenance(record, {}, DRAW_DT)
        self.assertEqual(status, "unresolved")

    def test_run_id_present_manifest_missing_completed_at_is_unresolved(self):
        record = {"run_id": "RUN-x"}
        status = classify_temporal_provenance(record, {"RUN-x": {"run_id": "RUN-x", "completed_at": None}}, DRAW_DT)
        self.assertEqual(status, "unresolved")

    def test_malformed_completed_at_is_unresolved_not_a_crash(self):
        record = {"run_id": "RUN-x"}
        status = classify_temporal_provenance(record, {"RUN-x": manifest("not-a-timestamp")}, DRAW_DT)
        self.assertEqual(status, "unresolved")

    def test_legacy_is_never_confused_with_unresolved(self):
        # legacy = no run_id at all; unresolved = run_id present but broken.
        # These must never collapse into the same status.
        legacy_record = {}
        unresolved_record = {"run_id": "RUN-ghost"}
        self.assertEqual(classify_temporal_provenance(legacy_record, {}, DRAW_DT), "legacy")
        self.assertEqual(classify_temporal_provenance(unresolved_record, {}, DRAW_DT), "unresolved")


if __name__ == "__main__":
    unittest.main()
