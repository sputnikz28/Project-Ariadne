"""Tests for library/academy/enrollments/registry.py — Academia Arcana
de Nemerion Foundation V1, commit 3/5: AcademyEnrollment as the
persistent relationship between a student and a classroom/doctrine/
version, still with no executable Tyche and no test participation.
Every test drives only the public API and observes only stored
content. Every test uses isolated tempfile bases for both the
enrollment registry and the student registry it depends on; nothing
here ever writes to the real library/academy/.
"""

import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from core.services.atomic_io import atomic_create_json, read_json
from library.academy.enrollments.registry import (
    VALID_STATUSES,
    AcademyEnrollment,
    AcademyEnrollmentRegistry,
    StudentNotFoundError,
)
from library.academy.students.registry import AcademyStudentRegistry


class AcademyEnrollmentRegistryTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._students_tmp = tempfile.mkdtemp()
        self.registry = AcademyEnrollmentRegistry(base=self._tmp)
        self.student_registry = AcademyStudentRegistry(base=self._students_tmp)
        self.student = self.student_registry.create(name="Aurelia Vance")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)
        shutil.rmtree(self._students_tmp, ignore_errors=True)

    def _create(self, **overrides):
        args = dict(
            student_id=self.student.student_id,
            classroom_id="catedra_tyche",
            doctrine_id="tyche",
            doctrine_version="v1",
            student_registry=self.student_registry,
        )
        args.update(overrides)
        return self.registry.create(**args)


class TestAcademyEnrollmentValidation(unittest.TestCase):
    def _kwargs(self, **overrides):
        args = dict(
            enrollment_id="NEM-ENR-000001", student_id="NEM-STU-000001",
            institution_id="nemerion", classroom_id="catedra_tyche",
            doctrine_id="tyche", doctrine_version="v1", status="active",
            enrolled_at="2026-08-24T10:00:00+00:00",
        )
        args.update(overrides)
        return args

    def test_valid_status_accepted(self):
        for status in VALID_STATUSES:
            enrollment = AcademyEnrollment(**self._kwargs(status=status))
            self.assertEqual(enrollment.status, status)

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            AcademyEnrollment(**self._kwargs(status="graduated"))

    def test_empty_classroom_id_rejected(self):
        with self.assertRaises(ValueError):
            AcademyEnrollment(**self._kwargs(classroom_id=""))

    def test_whitespace_only_classroom_id_rejected(self):
        with self.assertRaises(ValueError):
            AcademyEnrollment(**self._kwargs(classroom_id="   "))

    def test_empty_doctrine_id_rejected(self):
        with self.assertRaises(ValueError):
            AcademyEnrollment(**self._kwargs(doctrine_id=""))

    def test_empty_doctrine_version_rejected(self):
        with self.assertRaises(ValueError):
            AcademyEnrollment(**self._kwargs(doctrine_version=""))


class TestCreate(AcademyEnrollmentRegistryTestBase):
    def test_first_enrollment_gets_id_000001(self):
        enrollment = self._create()
        self.assertEqual(enrollment.enrollment_id, "NEM-ENR-000001")

    def test_second_enrollment_gets_id_000002(self):
        self._create()
        second = self._create(doctrine_version="v2")
        self.assertEqual(second.enrollment_id, "NEM-ENR-000002")

    def test_sequence_increments_across_several_creates(self):
        ids = [self._create(doctrine_version=f"v{i}").enrollment_id for i in range(1, 4)]
        self.assertEqual(ids, ["NEM-ENR-000001", "NEM-ENR-000002", "NEM-ENR-000003"])

    def test_unknown_student_is_rejected(self):
        with self.assertRaises(StudentNotFoundError):
            self._create(student_id="NEM-STU-999999")

    def test_unknown_student_leaves_no_entry_behind(self):
        try:
            self._create(student_id="NEM-STU-999999")
        except StudentNotFoundError:
            pass
        self.assertEqual(self.registry.load_all(), [])

    def test_known_student_is_accepted(self):
        enrollment = self._create()
        self.assertEqual(enrollment.student_id, self.student.student_id)

    def test_institution_id_is_nemerion(self):
        enrollment = self._create()
        self.assertEqual(enrollment.institution_id, "nemerion")

    def test_classroom_id_persisted(self):
        enrollment = self._create(classroom_id="catedra_tyche")
        self.assertEqual(enrollment.classroom_id, "catedra_tyche")

    def test_doctrine_id_persisted(self):
        enrollment = self._create(doctrine_id="tyche")
        self.assertEqual(enrollment.doctrine_id, "tyche")

    def test_doctrine_version_persisted(self):
        enrollment = self._create(doctrine_version="v3")
        self.assertEqual(enrollment.doctrine_version, "v3")

    def test_status_defaults_to_active(self):
        enrollment = self._create()
        self.assertEqual(enrollment.status, "active")

    def test_status_can_be_overridden(self):
        enrollment = self._create(status="withdrawn")
        self.assertEqual(enrollment.status, "withdrawn")

    def test_invalid_status_rejected_at_create(self):
        with self.assertRaises(ValueError):
            self._create(status="not_a_real_status")

    def test_enrolled_at_is_set(self):
        enrollment = self._create()
        self.assertTrue(enrollment.enrolled_at)

    def test_same_student_can_have_two_distinct_enrollments(self):
        e1 = self._create(classroom_id="catedra_tyche")
        e2 = self._create(classroom_id="rebeldes")
        self.assertEqual(e1.student_id, e2.student_id)
        self.assertNotEqual(e1.enrollment_id, e2.enrollment_id)

    def test_two_enrollments_with_identical_fields_get_different_ids(self):
        e1 = self._create()
        e2 = self._create()  # same student/classroom/doctrine/version
        self.assertNotEqual(e1.enrollment_id, e2.enrollment_id)
        self.assertEqual(e1.student_id, e2.student_id)
        self.assertEqual(e1.classroom_id, e2.classroom_id)

    def test_student_record_is_unchanged_after_enrollment_created(self):
        before = self.student_registry.get(self.student.student_id)
        self._create()
        after = self.student_registry.get(self.student.student_id)
        self.assertEqual(before, after)

    def test_student_historico_remains_empty_after_enrollment(self):
        self._create()
        student = self.student_registry.get(self.student.student_id)
        self.assertEqual(student.historico, ())


class TestRoundTrip(AcademyEnrollmentRegistryTestBase):
    def test_get_returns_equivalent_enrollment(self):
        created = self._create()
        fetched = self.registry.get(created.enrollment_id)
        self.assertEqual(fetched, created)

    def test_round_trip_preserves_enrolled_at_exactly(self):
        created = self._create()
        fetched = self.registry.get(created.enrollment_id)
        self.assertEqual(fetched.enrolled_at, created.enrolled_at)


class TestUnknownEnrollment(AcademyEnrollmentRegistryTestBase):
    def test_get_unknown_enrollment_returns_none(self):
        self.assertIsNone(self.registry.get("NEM-ENR-999999"))

    def test_exists_false_for_unknown_enrollment(self):
        self.assertFalse(self.registry.exists("NEM-ENR-999999"))

    def test_exists_true_for_known_enrollment(self):
        enrollment = self._create()
        self.assertTrue(self.registry.exists(enrollment.enrollment_id))


class TestEntriesAreSourceOfTruth(AcademyEnrollmentRegistryTestBase):
    def test_load_all_works_without_ever_calling_rebuild_index(self):
        self._create()
        self._create(doctrine_version="v2")
        self.assertFalse(self.registry.index_path.exists())
        self.assertEqual(len(self.registry.load_all()), 2)

    def test_get_works_without_ever_calling_rebuild_index(self):
        created = self._create()
        self.assertFalse(self.registry.index_path.exists())
        self.assertEqual(self.registry.get(created.enrollment_id), created)

    def test_load_all_on_empty_registry_returns_empty_list(self):
        self.assertEqual(self.registry.load_all(), [])

    def test_load_all_survives_missing_entries_directory(self):
        fresh = AcademyEnrollmentRegistry(base=tempfile.mkdtemp())
        try:
            self.assertEqual(fresh.load_all(), [])
            self.assertEqual(fresh.count(), 0)
        finally:
            shutil.rmtree(fresh.base, ignore_errors=True)

    def test_count_matches_number_created(self):
        self._create()
        self._create(doctrine_version="v2")
        self._create(doctrine_version="v3")
        self.assertEqual(self.registry.count(), 3)

    def test_all_is_an_alias_for_load_all(self):
        self._create()
        self.assertEqual(self.registry.all(), self.registry.load_all())


class TestRebuildIndex(AcademyEnrollmentRegistryTestBase):
    def test_index_is_derived_and_reconstructible(self):
        e1 = self._create(classroom_id="catedra_tyche")
        e2 = self._create(classroom_id="rebeldes", status="withdrawn")
        index = self.registry.rebuild_index()
        self.assertEqual(index["total_enrollments"], 2)
        self.assertEqual(set(index["enrollment_ids"]), {e1.enrollment_id, e2.enrollment_id})
        self.assertEqual(index["por_status"], {"active": 1, "withdrawn": 1})
        self.assertEqual(index["por_classroom"], {"catedra_tyche": 1, "rebeldes": 1})

    def test_index_rebuild_never_touches_entries(self):
        enrollment = self._create()
        before = read_json(self.registry._entry_path(enrollment.enrollment_id))
        self.registry.rebuild_index()
        after = read_json(self.registry._entry_path(enrollment.enrollment_id))
        self.assertEqual(before, after)

    def test_index_can_be_rebuilt_after_deleting_it(self):
        self._create()
        self.registry.rebuild_index()
        self.registry.index_path.unlink()
        rebuilt = self.registry.rebuild_index()
        self.assertEqual(rebuilt["total_enrollments"], 1)

    def test_empty_registry_rebuilds_to_zero_enrollments(self):
        index = self.registry.rebuild_index()
        self.assertEqual(index["total_enrollments"], 0)
        self.assertEqual(index["enrollment_ids"], [])

    def test_index_filename_is_distinct_from_students_index(self):
        self.assertEqual(self.registry.index_path.name, "LIVRO_DAS_MATRICULAS.json")
        self.assertEqual(self.student_registry.index_path.name, "LIVRO_DA_ACADEMIA.json")

    def test_rebuilding_enrollment_index_never_writes_student_index(self):
        self._create()
        self.registry.rebuild_index()
        self.assertFalse(self.student_registry.index_path.exists())


class TestIdCollisionAndRetry(AcademyEnrollmentRegistryTestBase):
    def test_pre_claimed_candidate_id_is_skipped(self):
        entries_dir = Path(self._tmp) / "entries"
        atomic_create_json(entries_dir / "NEM-ENR-000001.json", {
            "enrollment_id": "NEM-ENR-000001", "student_id": "NEM-STU-000099",
            "institution_id": "nemerion", "classroom_id": "ghost_classroom",
            "doctrine_id": "ghost_doctrine", "doctrine_version": "v1",
            "status": "active", "enrolled_at": "2026-01-01T00:00:00+00:00",
        })
        enrollment = self._create()
        self.assertEqual(enrollment.enrollment_id, "NEM-ENR-000002")

    def test_pre_claimed_id_content_is_never_overwritten(self):
        entries_dir = Path(self._tmp) / "entries"
        atomic_create_json(entries_dir / "NEM-ENR-000001.json", {
            "enrollment_id": "NEM-ENR-000001", "student_id": "NEM-STU-000099",
            "institution_id": "nemerion", "classroom_id": "ghost_classroom",
            "doctrine_id": "ghost_doctrine", "doctrine_version": "v1",
            "status": "active", "enrolled_at": "2026-01-01T00:00:00+00:00",
        })
        self._create()
        ghost = self.registry.get("NEM-ENR-000001")
        self.assertEqual(ghost.classroom_id, "ghost_classroom")

    def test_retries_past_multiple_consecutive_claimed_ids(self):
        entries_dir = Path(self._tmp) / "entries"
        for n in (1, 2, 3):
            atomic_create_json(entries_dir / f"NEM-ENR-{n:06d}.json", {
                "enrollment_id": f"NEM-ENR-{n:06d}", "student_id": "NEM-STU-000099",
                "institution_id": "nemerion", "classroom_id": "ghost_classroom",
                "doctrine_id": "ghost_doctrine", "doctrine_version": "v1",
                "status": "active", "enrolled_at": "2026-01-01T00:00:00+00:00",
            })
        enrollment = self._create()
        self.assertEqual(enrollment.enrollment_id, "NEM-ENR-000004")

    def test_true_concurrent_creates_never_collide(self):
        created = []
        lock = threading.Lock()
        barrier = threading.Barrier(2)

        def worker(doctrine_version):
            barrier.wait()
            enrollment = self._create(doctrine_version=doctrine_version)
            with lock:
                created.append(enrollment)

        t1 = threading.Thread(target=worker, args=("v1",))
        t2 = threading.Thread(target=worker, args=("v2",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(created), 2)
        ids = {e.enrollment_id for e in created}
        self.assertEqual(len(ids), 2)  # no duplicate id, no lost enrollment
        self.assertEqual(self.registry.count(), 2)


class TestIdIndependence(AcademyEnrollmentRegistryTestBase):
    def test_enrollment_id_does_not_contain_student_id(self):
        enrollment = self._create()
        self.assertNotIn(self.student.student_id, enrollment.enrollment_id)

    def test_enrollment_id_does_not_contain_classroom_id(self):
        enrollment = self._create(classroom_id="catedra_tyche")
        self.assertNotIn("catedra_tyche", enrollment.enrollment_id)

    def test_enrollment_id_does_not_contain_doctrine_id(self):
        enrollment = self._create(doctrine_id="tyche")
        self.assertNotIn("tyche", enrollment.enrollment_id.lower())


class TestIsolation(AcademyEnrollmentRegistryTestBase):
    def test_writes_stay_inside_the_configured_base(self):
        enrollment = self._create()
        self.assertTrue(str(self.registry.base).startswith(tempfile.gettempdir()))
        real_entry = Path("library/academy/enrollments/entries") / f"{enrollment.enrollment_id}.json"
        self.assertFalse(real_entry.exists())


if __name__ == "__main__":
    unittest.main()
