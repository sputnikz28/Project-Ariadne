"""Tests for core/services/run_manifest.py."""

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from core.services import run_manifest as rm
from core.services.hero_evaluation import classify_temporal_provenance


class TestRunManifest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._original_runs_dir = rm.RUNS_DIR
        rm.RUNS_DIR = Path(self._tmp) / "runs"

    def tearDown(self):
        rm.RUNS_DIR = self._original_runs_dir
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_start_run_creates_a_manifest_with_a_run_id(self):
        manifest = rm.start_run(seed=123, modo_semente="fixo")
        self.assertTrue(manifest["run_id"].startswith("RUN-"))
        self.assertEqual(manifest["seed"], 123)
        self.assertIsNone(manifest["completed_at"])

    def test_start_run_persists_to_disk(self):
        manifest = rm.start_run(seed=123, modo_semente="fixo")
        loaded = rm.load_run(manifest["run_id"])
        self.assertEqual(loaded["run_id"], manifest["run_id"])
        self.assertEqual(loaded["seed"], 123)

    def test_complete_run_updates_completed_at_and_report_path(self):
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        rm.complete_run(manifest, report_path="experiments/reports/generated/x.txt", generated_record_count=42)
        loaded = rm.load_run(manifest["run_id"])
        self.assertIsNotNone(loaded["completed_at"])
        self.assertEqual(loaded["report_path"], "experiments/reports/generated/x.txt")
        self.assertEqual(loaded["generated_record_count"], 42)

    def test_load_run_returns_none_for_unknown_id(self):
        self.assertIsNone(rm.load_run("RUN-does-not-exist"))

    def test_load_run_returns_none_for_none_id(self):
        self.assertIsNone(rm.load_run(None))

    def test_load_all_runs_returns_every_persisted_manifest(self):
        m1 = rm.start_run(seed=1, modo_semente="fixo")
        m2 = rm.start_run(seed=2, modo_semente="fixo")
        all_runs = rm.load_all_runs()
        self.assertIn(m1["run_id"], all_runs)
        self.assertIn(m2["run_id"], all_runs)

    def test_load_all_runs_empty_directory_returns_empty_dict(self):
        self.assertEqual(rm.load_all_runs(), {})

    def test_git_commit_capture_never_raises_on_failure(self):
        # Even if subprocess/git is unavailable, start_run must not crash.
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        self.assertTrue(manifest["git_commit"] is None or isinstance(manifest["git_commit"], str))

    # -- filename policy (this is what .gitignore's completeness split relies on) --

    def test_start_run_writes_only_the_incomplete_filename(self):
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        run_id = manifest["run_id"]
        self.assertTrue((rm.RUNS_DIR / f"{run_id}.incomplete.json").exists())
        self.assertFalse((rm.RUNS_DIR / f"{run_id}.json").exists())

    def test_complete_run_writes_final_filename_and_removes_incomplete(self):
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        run_id = manifest["run_id"]
        rm.complete_run(manifest, report_path="x.txt", generated_record_count=1)
        self.assertTrue((rm.RUNS_DIR / f"{run_id}.json").exists())
        self.assertFalse((rm.RUNS_DIR / f"{run_id}.incomplete.json").exists())

    def test_an_incomplete_run_is_still_loadable_by_run_id(self):
        # A crashed run leaves only the incomplete file — load_run() must
        # still resolve it (classify_temporal_provenance then reports
        # "unresolved" for it, not a crash) rather than pretending it
        # doesn't exist.
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        loaded = rm.load_run(manifest["run_id"])
        self.assertIsNotNone(loaded)
        self.assertIsNone(loaded["completed_at"])

    def test_load_all_runs_finds_incomplete_manifests_too(self):
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        all_runs = rm.load_all_runs()
        self.assertIn(manifest["run_id"], all_runs)
        self.assertIsNone(all_runs[manifest["run_id"]]["completed_at"])

    def test_verified_provenance_reconstructs_from_a_manifest_file_alone(self):
        # Simulates a clean clone: a manifest written as static JSON (not
        # produced by start_run/complete_run in this process) is all
        # load_all_runs() + classify_temporal_provenance() need to
        # correctly resolve "verified" — no other state involved. This is
        # the concrete guarantee behind committing completed run manifests
        # alongside the prediction records that reference their run_id.
        draw_dt = datetime(2026, 7, 14, 18, 0, 0, tzinfo=timezone.utc)
        static_manifest = {
            "run_id": "RUN-20260710T090000Z",
            "started_at": "2026-07-10T09:00:00+00:00",
            "completed_at": "2026-07-10T09:05:00+00:00",  # before the draw
            "seed": 999, "modo_semente": "fixo", "project_version": "V12",
            "git_commit": "deadbeef", "report_path": "x.txt",
            "command": "main.py", "target_draw": None, "generated_record_count": 1,
        }
        (rm.RUNS_DIR / "RUN-20260710T090000Z.json").parent.mkdir(parents=True, exist_ok=True)
        (rm.RUNS_DIR / "RUN-20260710T090000Z.json").write_text(json.dumps(static_manifest), encoding="utf-8")

        run_manifests = rm.load_all_runs()
        record = {"run_id": "RUN-20260710T090000Z"}
        self.assertEqual(classify_temporal_provenance(record, run_manifests, draw_dt), "verified")

    # -- run_id collision handling (Commit 25 finding) -----------------

    def test_same_mocked_instant_produces_distinct_run_ids(self):
        fixed_dt = datetime(2026, 8, 21, 15, 30, 12, 123456, tzinfo=timezone.utc)
        with mock.patch("core.services.run_manifest.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            m1 = rm.start_run(seed=1, modo_semente="fixo")
            m2 = rm.start_run(seed=2, modo_semente="fixo")

        self.assertNotEqual(m1["run_id"], m2["run_id"])
        self.assertEqual(m1["run_id"], "RUN-20260821T153012123456Z")
        self.assertEqual(m2["run_id"], "RUN-20260821T153012123456Z-1")

    def test_three_way_collision_uses_sequential_deterministic_suffixes(self):
        fixed_dt = datetime(2026, 8, 21, 15, 30, 12, 123456, tzinfo=timezone.utc)
        with mock.patch("core.services.run_manifest.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            m1 = rm.start_run(seed=1, modo_semente="fixo")
            m2 = rm.start_run(seed=2, modo_semente="fixo")
            m3 = rm.start_run(seed=3, modo_semente="fixo")

        self.assertEqual([m1["run_id"], m2["run_id"], m3["run_id"]], [
            "RUN-20260821T153012123456Z",
            "RUN-20260821T153012123456Z-1",
            "RUN-20260821T153012123456Z-2",
        ])

    def test_no_incomplete_manifest_is_ever_overwritten_by_a_collision(self):
        fixed_dt = datetime(2026, 8, 21, 15, 30, 12, 123456, tzinfo=timezone.utc)
        with mock.patch("core.services.run_manifest.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            m1 = rm.start_run(seed=111, modo_semente="fixo")
            rm.start_run(seed=222, modo_semente="fixo")

        # m1's own incomplete manifest still holds m1's own seed, never
        # clobbered by the second start_run() call.
        reloaded_m1 = rm.load_run(m1["run_id"])
        self.assertEqual(reloaded_m1["seed"], 111)

    def test_existing_final_manifest_with_the_base_id_also_forces_a_new_id(self):
        base_run_id = "RUN-20260821T153012123456Z"
        rm.RUNS_DIR.mkdir(parents=True, exist_ok=True)
        static_final_manifest = {
            "run_id": base_run_id, "started_at": "2026-08-21T15:30:12+00:00",
            "completed_at": "2026-08-21T15:30:20+00:00", "seed": 999,
            "modo_semente": "fixo", "project_version": None, "git_commit": None,
            "report_path": None, "command": "main.py", "target_draw": None,
            "generated_record_count": 0,
        }
        (rm.RUNS_DIR / f"{base_run_id}.json").write_text(json.dumps(static_final_manifest), encoding="utf-8")

        fixed_dt = datetime(2026, 8, 21, 15, 30, 12, 123456, tzinfo=timezone.utc)
        with mock.patch("core.services.run_manifest.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            new_manifest = rm.start_run(seed=1, modo_semente="fixo")

        self.assertEqual(new_manifest["run_id"], f"{base_run_id}-1")
        # the pre-existing final manifest is untouched
        still_there = json.loads((rm.RUNS_DIR / f"{base_run_id}.json").read_text(encoding="utf-8"))
        self.assertEqual(still_there["seed"], 999)

    def test_load_all_runs_finds_both_sides_of_a_resolved_collision(self):
        fixed_dt = datetime(2026, 8, 21, 15, 30, 12, 123456, tzinfo=timezone.utc)
        with mock.patch("core.services.run_manifest.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            m1 = rm.start_run(seed=1, modo_semente="fixo")
            m2 = rm.start_run(seed=2, modo_semente="fixo")

        all_runs = rm.load_all_runs()
        self.assertIn(m1["run_id"], all_runs)
        self.assertIn(m2["run_id"], all_runs)
        self.assertEqual(all_runs[m1["run_id"]]["seed"], 1)
        self.assertEqual(all_runs[m2["run_id"]]["seed"], 2)

    def test_run_id_prefix_still_starts_with_RUN(self):
        manifest = rm.start_run(seed=1, modo_semente="fixo")
        self.assertTrue(manifest["run_id"].startswith("RUN-"))

    def test_temporal_proof_still_comes_from_completed_at_not_run_id_content(self):
        # classify_temporal_provenance() is unmodified and unmodifiable
        # here — this only re-confirms it still reads completed_at, and
        # is indifferent to a "-1"/"-2" suffix on the run_id string.
        fixed_dt = datetime(2026, 8, 21, 15, 30, 12, 123456, tzinfo=timezone.utc)
        with mock.patch("core.services.run_manifest.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_dt
            m1 = rm.start_run(seed=1, modo_semente="fixo")
            m2 = rm.start_run(seed=2, modo_semente="fixo")
            rm.complete_run(m1)
            rm.complete_run(m2)

        run_manifests = rm.load_all_runs()
        draw_dt = fixed_dt.replace(year=2030)  # comfortably after both completions
        for run_id in (m1["run_id"], m2["run_id"]):
            record = {"run_id": run_id}
            self.assertEqual(classify_temporal_provenance(record, run_manifests, draw_dt), "verified")


if __name__ == "__main__":
    unittest.main()
