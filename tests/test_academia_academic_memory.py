"""Tests for core/services/academia/academic_memory.py — Academia
Arcana de Nemerion Foundation V1, commit 5/5: turning a FINISHED
GeneratorRunResult into academic memory (AcademicEvent), after the
scientific experience is already fully determined. Every test uses
isolated tempfile student/enrollment registries; nothing here ever
writes to the real library/academy/.

TestFoundationSmokeEndToEnd (item 18 of the approved commit 5/5 plan)
drives the REAL Campaign Runner (run_system_campaign) end to end,
reusing test_backtest_generators.py's own historical/scroll fixture
helpers rather than duplicating them — the only test in this file that
does not hand-build a GeneratorRunResult directly.
"""

import inspect
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from core.services.academia.academic_memory import (
    AcademicRecordingOutcome,
    _derive_event_id,
    record_academic_result,
)
from core.services.academia.common import build_academy_candidate_key
from core.services.academia.tyche import TYCHE_IDENTITY
from core.services.backtest_campaign import (
    GeneratorRunResult,
    MultiSystemCampaignSpec,
    run_system_campaign,
)
from core.services.backtest_lab import BacktestTarget
from core.services.backtest_orchestrator import SimulatedBacktestCandidate
from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_performance import CandidatePerformanceSummary
from library.academy.enrollments.registry import AcademyEnrollmentRegistry
from library.academy.students.registry import AcademyStudentRegistry
from tests.test_backtest_generators import make_dataset_draw, make_minimal_cfg, write_historical_dataset

_TARGET = BacktestTarget(
    draw_id="T-A/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc),
    numeros=(1, 2, 3, 4, 5), estrelas=(1, 2),
)


def _snapshot_real_dir(path):
    """Deterministic content snapshot of a real library/academy/
    directory tree — relative path -> exact bytes, for every file.
    Used only to prove an isolated-registry operation never touches
    real Academia storage. See TestFoundationSmokeEndToEnd's own test
    for why comparing a specific student_id/enrollment_id string is
    not a valid proxy for isolation once real founders exist.
    """
    if not path.exists():
        return {}
    return {p.relative_to(path): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def _dummy_performance():
    return CandidatePerformanceSummary(
        total_candidates=1, unique_full_keys=1, unique_number_sets=1, duplicate_count=0,
        full_key_diversity_rate=1.0, number_set_diversity_rate=1.0, category_counts={},
        relevant_count=0, relevant_rate=0.0,
    )


def _make_key(student_id="NEM-STU-000001", student_name="Aurelia Vance", enrollment_id="NEM-ENR-000001", **overrides):
    args = dict(
        identity=TYCHE_IDENTITY, student_id=student_id, student_name=student_name,
        student_species=None, enrollment_id=enrollment_id,
        numeros=(1, 2, 3, 4, 5), estrelas=(1, 2),
    )
    args.update(overrides)
    return build_academy_candidate_key(**args)


def _make_result(run_id, candidate_keys, categories, target=_TARGET, seed=1, system="academia"):
    simulated = tuple(
        SimulatedBacktestCandidate(candidate=k, temporal_basis="historical_input_boundary", run_id=run_id)
        for k in candidate_keys
    )
    evaluations = tuple(
        CandidateEvaluation(matched_numbers=(), matched_stars=(), matched_number_count=0, matched_star_count=0, category=cat)
        for cat in categories
    )
    return GeneratorRunResult(
        system=system, target=target, seed=seed, generations=None, run_id=run_id,
        candidates=simulated, evaluations=evaluations, performance=_dummy_performance(),
        attempted_races=frozenset(),
    )


class AcademicMemoryTestBase(unittest.TestCase):
    def setUp(self):
        self._students_tmp = tempfile.mkdtemp()
        self.student_registry = AcademyStudentRegistry(base=self._students_tmp)

    def tearDown(self):
        shutil.rmtree(self._students_tmp, ignore_errors=True)

    def _record(self, result):
        return record_academic_result(result, students_root=self._students_tmp)


class TestDeriveEventId(unittest.TestCase):
    def test_deterministic_given_same_arguments(self):
        e1 = _derive_event_id("run-1", "NEM-STU-000001", "NEM-ENR-000001")
        e2 = _derive_event_id("run-1", "NEM-STU-000001", "NEM-ENR-000001")
        self.assertEqual(e1, e2)

    def test_different_run_id_gives_different_event_id(self):
        e1 = _derive_event_id("run-1", "NEM-STU-000001", "NEM-ENR-000001")
        e2 = _derive_event_id("run-2", "NEM-STU-000001", "NEM-ENR-000001")
        self.assertNotEqual(e1, e2)

    def test_different_student_id_gives_different_event_id(self):
        e1 = _derive_event_id("run-1", "NEM-STU-000001", "NEM-ENR-000001")
        e2 = _derive_event_id("run-1", "NEM-STU-000002", "NEM-ENR-000001")
        self.assertNotEqual(e1, e2)

    def test_different_enrollment_id_gives_different_event_id(self):
        e1 = _derive_event_id("run-1", "NEM-STU-000001", "NEM-ENR-000001")
        e2 = _derive_event_id("run-1", "NEM-STU-000001", "NEM-ENR-000002")
        self.assertNotEqual(e1, e2)

    def test_never_uses_builtin_hash(self):
        import core.services.academia.academic_memory as _module
        source = inspect.getsource(_module)
        self.assertNotIn("hash(", source)


class TestRejectsWrongSystem(AcademicMemoryTestBase):
    def test_raises_for_non_academia_system(self):
        result = _make_result("run-1", (), (), system="treefolks_v2")
        with self.assertRaises(ValueError):
            self._record(result)


class TestRecordAcademicResult(AcademicMemoryTestBase):
    def test_creates_one_event_for_a_known_student(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-1", (key,), ("0+0",))
        outcomes = self._record(result)
        self.assertEqual(len(outcomes), 1)
        self.assertTrue(outcomes[0].created)
        self.assertIsNone(outcomes[0].error)
        reloaded = self.student_registry.get(student.student_id)
        self.assertEqual(len(reloaded.historico), 1)

    def test_entity_id_none_is_reported_not_crashed(self):
        key = _make_key()
        # simulate a candidate that structurally lacks entity_id -- build
        # via dataclasses.replace on the real CandidateKey shape
        from dataclasses import replace
        no_entity_key = replace(key, entity_id=None)
        result = _make_result("run-1", (no_entity_key,), ("0+0",))
        outcomes = self._record(result)
        self.assertEqual(len(outcomes), 1)
        self.assertIsNone(outcomes[0].entity_id)
        self.assertIsNotNone(outcomes[0].error)
        self.assertFalse(outcomes[0].created)

    def test_missing_enrollment_id_is_reported_not_crashed(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        from dataclasses import replace
        from types import MappingProxyType
        stripped_metadata = {k: v for k, v in key.metadata.items() if k != "enrollment_id"}
        key_without_enrollment = replace(key, metadata=MappingProxyType(stripped_metadata))
        result = _make_result("run-1", (key_without_enrollment,), ("0+0",))
        outcomes = self._record(result)
        self.assertEqual(len(outcomes), 1)
        self.assertIsNotNone(outcomes[0].error)
        self.assertFalse(outcomes[0].created)

    def test_unknown_student_is_reported_not_crashed(self):
        key = _make_key(student_id="NEM-STU-999999", student_name="Ghost")
        result = _make_result("run-1", (key,), ("0+0",))
        outcomes = self._record(result)
        self.assertEqual(len(outcomes), 1)
        self.assertIsNotNone(outcomes[0].error)
        self.assertFalse(outcomes[0].created)

    def test_one_failing_candidate_does_not_block_others(self):
        good_student = self.student_registry.create(name="Aurelia Vance")
        good_key = _make_key(student_id=good_student.student_id, student_name=good_student.name)
        bad_key = _make_key(student_id="NEM-STU-999999", student_name="Ghost")
        result = _make_result("run-1", (bad_key, good_key), ("0+0", "1+0"))
        outcomes = self._record(result)
        self.assertEqual(len(outcomes), 2)
        self.assertIsNotNone(outcomes[0].error)
        self.assertIsNone(outcomes[1].error)
        self.assertTrue(outcomes[1].created)
        reloaded = self.student_registry.get(good_student.student_id)
        self.assertEqual(len(reloaded.historico), 1)

    def test_category_preserved_in_extra(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-1", (key,), ("2+1",))
        self._record(result)
        event = self.student_registry.get(student.student_id).historico[0]
        self.assertEqual(event.extra["category"], "2+1")

    def test_candidate_summary_preserved(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name, numeros=(7, 14, 22, 33, 41), estrelas=(3, 9))
        result = _make_result("run-1", (key,), ("0+0",))
        self._record(result)
        event = self.student_registry.get(student.student_id).historico[0]
        self.assertEqual(event.extra["candidate_summary"], {"numeros": [7, 14, 22, 33, 41], "estrelas": [3, 9]})

    def test_historical_target_is_the_result_target_not_occurred_at(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-1", (key,), ("0+0",), target=_TARGET)
        self._record(result)
        event = self.student_registry.get(student.student_id).historico[0]
        self.assertEqual(event.extra["historical_target"], _TARGET.draw_id)
        self.assertNotEqual(event.occurred_at, event.extra["historical_target"])

    def test_generator_seed_recorded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-1", (key,), ("0+0",), seed=20260821)
        self._record(result)
        event = self.student_registry.get(student.student_id).historico[0]
        self.assertEqual(event.extra["generator_seed"], 20260821)

    def test_run_id_recorded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-called-out", (key,), ("0+0",))
        self._record(result)
        event = self.student_registry.get(student.student_id).historico[0]
        self.assertEqual(event.extra["run_id"], "run-called-out")

    def test_classroom_doctrine_metadata_recorded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-1", (key,), ("0+0",))
        self._record(result)
        event = self.student_registry.get(student.student_id).historico[0]
        self.assertEqual(event.extra["classroom_id"], TYCHE_IDENTITY.classroom_id)
        self.assertEqual(event.extra["doctrine_id"], TYCHE_IDENTITY.doctrine_id)
        self.assertEqual(event.extra["doctrine_version"], TYCHE_IDENTITY.doctrine_version)

    def test_multiple_students_each_get_their_own_event(self):
        s1 = self.student_registry.create(name="Aurelia Vance")
        s2 = self.student_registry.create(name="Bram Ostergren")
        k1 = _make_key(student_id=s1.student_id, student_name=s1.name, enrollment_id="NEM-ENR-000001")
        k2 = _make_key(student_id=s2.student_id, student_name=s2.name, enrollment_id="NEM-ENR-000002")
        result = _make_result("run-1", (k1, k2), ("0+0", "1+1"))
        outcomes = self._record(result)
        self.assertTrue(all(o.created for o in outcomes))
        self.assertEqual(len(self.student_registry.get(s1.student_id).historico), 1)
        self.assertEqual(len(self.student_registry.get(s2.student_id).historico), 1)


class TestIdempotentReprocessing(AcademicMemoryTestBase):
    def test_same_result_processed_twice_yields_one_event(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result = _make_result("run-1", (key,), ("0+0",))
        outcomes1 = self._record(result)
        outcomes2 = self._record(result)
        self.assertTrue(outcomes1[0].created)
        self.assertFalse(outcomes2[0].created)
        self.assertEqual(outcomes1[0].event_id, outcomes2[0].event_id)
        reloaded = self.student_registry.get(student.student_id)
        self.assertEqual(len(reloaded.historico), 1)

    def test_two_students_sharing_a_run_but_different_enrollments_never_collide(self):
        # confirms the audited real risk: two participants in ONE run_id
        # for the SAME student via two different enrollments must not
        # collapse into a single event_id.
        student = self.student_registry.create(name="Aurelia Vance")
        k1 = _make_key(student_id=student.student_id, student_name=student.name, enrollment_id="NEM-ENR-000001")
        k2 = _make_key(student_id=student.student_id, student_name=student.name, enrollment_id="NEM-ENR-000002")
        result = _make_result("run-1", (k1, k2), ("0+0", "1+0"))
        outcomes = self._record(result)
        self.assertTrue(all(o.created for o in outcomes))
        self.assertNotEqual(outcomes[0].event_id, outcomes[1].event_id)
        reloaded = self.student_registry.get(student.student_id)
        self.assertEqual(len(reloaded.historico), 2)

    def test_a_deliberate_new_attempt_with_a_fresh_run_id_is_a_new_event(self):
        student = self.student_registry.create(name="Aurelia Vance")
        key = _make_key(student_id=student.student_id, student_name=student.name)
        result_first = _make_result("run-1", (key,), ("0+0",))
        result_second = _make_result("run-2", (key,), ("0+0",))  # same student/enrollment/candidate content
        self._record(result_first)
        self._record(result_second)
        reloaded = self.student_registry.get(student.student_id)
        self.assertEqual(len(reloaded.historico), 2)

    def test_same_candidate_content_across_different_runs_is_never_deduplicated_by_content(self):
        student = self.student_registry.create(name="Aurelia Vance")
        # identical numeros/estrelas/category, only run_id differs
        key1 = _make_key(student_id=student.student_id, student_name=student.name, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        key2 = _make_key(student_id=student.student_id, student_name=student.name, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result1 = _make_result("run-A", (key1,), ("0+0",))
        result2 = _make_result("run-B", (key2,), ("0+0",))
        self._record(result1)
        self._record(result2)
        reloaded = self.student_registry.get(student.student_id)
        self.assertEqual(len(reloaded.historico), 2)


class TestFoundationSmokeEndToEnd(unittest.TestCase):
    """Item 18 of the approved commit 5/5 plan: 2 AcademyStudents, 2
    active Tyche enrollments, 1 real historical target x 1 seed, run
    through the real Campaign Runner (run_system_campaign), evaluate,
    record academic memory for both, re-read both students, confirm
    exactly 1 event each, reprocess the SAME result, confirm still
    exactly 1 event each. No real student/enrollment is ever created in
    the repository — everything lives under tempfile bases.
    """

    def setUp(self):
        self._students_tmp = tempfile.TemporaryDirectory()
        self._enrollments_tmp = tempfile.TemporaryDirectory()
        self._hist_root = tempfile.TemporaryDirectory()
        self.addCleanup(self._students_tmp.cleanup)
        self.addCleanup(self._enrollments_tmp.cleanup)
        self.addCleanup(self._hist_root.cleanup)

        self.student_registry = AcademyStudentRegistry(base=self._students_tmp.name)
        self.enrollment_registry = AcademyEnrollmentRegistry(base=self._enrollments_tmp.name)

        write_historical_dataset(self._hist_root.name, 2099, "a.json", [
            make_dataset_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5]),
            make_dataset_draw("002/2099", "2099-01-08", "2099-01-08T20:00:00+00:00", numeros=[6, 7, 8, 9, 10]),
        ])

        self.cfg = make_minimal_cfg(ACADEMIA={
            "students_root": self._students_tmp.name,
            "enrollments_root": self._enrollments_tmp.name,
        })

        self.s1 = self.student_registry.create(name="Aurelia Vance")
        self.s2 = self.student_registry.create(name="Bram Ostergren")
        for student in (self.s1, self.s2):
            self.enrollment_registry.create(
                student_id=student.student_id, classroom_id=TYCHE_IDENTITY.classroom_id,
                doctrine_id=TYCHE_IDENTITY.doctrine_id, doctrine_version=TYCHE_IDENTITY.doctrine_version,
                student_registry=self.student_registry,
            )

        # A boundary strictly AFTER both seeded draws -- so ctx['historico']
        # is non-empty (both draws are visible), matching the pattern
        # test_backtest_generators.py's own BOUNDARY/_GeneratorFixture use.
        self.target = BacktestTarget(
            draw_id="T-A/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc),
            numeros=(11, 12, 13, 14, 15), estrelas=(5, 6),
        )
        self.spec = MultiSystemCampaignSpec(
            targets=(self.target,), seeds=(777,), systems=("academia",),
            generations=(), mode="verified", relevant_categories=frozenset({"5+2"}),
        )

    def _run_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            from unittest import mock
            with mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
                return run_system_campaign(
                    self.cfg, self.spec, historical_root=self._hist_root.name, scrolls_root=None,
                )

    def test_full_pipeline_produces_two_candidates(self):
        results = self._run_campaign()
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].candidates), 2)

    def test_recording_writes_one_event_per_student(self):
        results = self._run_campaign()
        outcomes = record_academic_result(results[0], students_root=self._students_tmp.name)
        self.assertEqual(len(outcomes), 2)
        self.assertTrue(all(o.created for o in outcomes))
        self.assertEqual(len(self.student_registry.get(self.s1.student_id).historico), 1)
        self.assertEqual(len(self.student_registry.get(self.s2.student_id).historico), 1)

    def test_reprocessing_the_same_result_stays_idempotent(self):
        results = self._run_campaign()
        record_academic_result(results[0], students_root=self._students_tmp.name)
        outcomes2 = record_academic_result(results[0], students_root=self._students_tmp.name)
        self.assertTrue(all(not o.created for o in outcomes2))  # already existed, no-op
        self.assertEqual(len(self.student_registry.get(self.s1.student_id).historico), 1)
        self.assertEqual(len(self.student_registry.get(self.s2.student_id).historico), 1)

    def test_no_real_student_or_enrollment_created_in_repository(self):
        # Snapshot the REAL Academia trees' exact content before/after
        # -- never compare against a specific student_id/enrollment_id
        # string. Once real founders exist (Piloto Oficial da Cátedra
        # de Tyche), this test's own isolated tempfile registries can
        # legitimately assign the exact same next sequential id (both
        # start counting from scratch) -- that coincidence proves
        # nothing about leakage. Only "the real trees are byte-
        # identical before and after" does.
        real_students_dir = Path("library/academy/students")
        real_enrollments_dir = Path("library/academy/enrollments")
        before_students = _snapshot_real_dir(real_students_dir)
        before_enrollments = _snapshot_real_dir(real_enrollments_dir)

        results = self._run_campaign()
        record_academic_result(results[0], students_root=self._students_tmp.name)

        after_students = _snapshot_real_dir(real_students_dir)
        after_enrollments = _snapshot_real_dir(real_enrollments_dir)
        self.assertEqual(before_students, after_students, "real library/academy/students/ must be untouched")
        self.assertEqual(before_enrollments, after_enrollments, "real library/academy/enrollments/ must be untouched")
        # the isolated registry itself DID receive the write
        self.assertEqual(len(self.student_registry.get(self.s1.student_id).historico), 1)


if __name__ == "__main__":
    unittest.main()
