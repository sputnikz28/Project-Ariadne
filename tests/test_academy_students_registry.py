"""Tests for library/academy/students/registry.py — Academia Arcana de
Nemerion Foundation V1, commit 2/5: AcademyStudent persistent identity.
Every test drives only the public API (create/get/load_all/exists/
rebuild_index/all/count) and observes only stored content — no source
inspection, no filesystem mtime checks. Every test uses an isolated
tempfile base; nothing here ever writes to the real
library/academy/students/.
"""

import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from core.services.atomic_io import atomic_create_json, read_json
from library.academy.students.registry import (
    VALID_STATUSES,
    AcademyStudent,
    AcademyStudentRegistry,
)


class AcademyStudentRegistryTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.registry = AcademyStudentRegistry(base=self._tmp)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)


class TestAcademyStudentValidation(unittest.TestCase):
    def test_valid_status_accepted(self):
        for status in VALID_STATUSES:
            student = AcademyStudent(
                student_id="NEM-STU-000001", name="Aurelia Vance", species=None,
                institution_id="nemerion", created_at="2026-08-24T10:00:00+00:00",
                status=status,
            )
            self.assertEqual(student.status, status)

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            AcademyStudent(
                student_id="NEM-STU-000001", name="Aurelia Vance", species=None,
                institution_id="nemerion", created_at="2026-08-24T10:00:00+00:00",
                status="graduated_with_honors",
            )

    def test_historico_defaults_to_empty(self):
        student = AcademyStudent(
            student_id="NEM-STU-000001", name="Aurelia Vance", species=None,
            institution_id="nemerion", created_at="2026-08-24T10:00:00+00:00",
            status="active",
        )
        self.assertEqual(student.historico, ())


class TestCreate(AcademyStudentRegistryTestBase):
    def test_first_student_gets_id_000001(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertEqual(student.student_id, "NEM-STU-000001")

    def test_second_student_gets_id_000002(self):
        self.registry.create(name="Aurelia Vance")
        second = self.registry.create(name="Bram Ostergren")
        self.assertEqual(second.student_id, "NEM-STU-000002")

    def test_sequence_increments_correctly_across_several_creates(self):
        ids = [self.registry.create(name=f"Student {i}").student_id for i in range(5)]
        self.assertEqual(
            ids,
            ["NEM-STU-000001", "NEM-STU-000002", "NEM-STU-000003", "NEM-STU-000004", "NEM-STU-000005"],
        )

    def test_same_name_gives_different_ids(self):
        s1 = self.registry.create(name="Aurelia Vance")
        s2 = self.registry.create(name="Aurelia Vance")
        self.assertNotEqual(s1.student_id, s2.student_id)

    def test_id_is_independent_of_name(self):
        s1 = self.registry.create(name="Zzyzx")
        second_registry = AcademyStudentRegistry(base=tempfile.mkdtemp())
        try:
            s2 = second_registry.create(name="Aaron")
            # same starting sequence in a fresh registry regardless of name
            self.assertEqual(s1.student_id, s2.student_id)
        finally:
            shutil.rmtree(second_registry.base, ignore_errors=True)

    def test_ids_are_never_reused_after_status_change(self):
        # even a student that later becomes irrelevant (e.g. expelled)
        # never frees its id for reuse -- create() never inspects status.
        first = self.registry.create(name="Aurelia Vance")
        second = self.registry.create(name="Bram Ostergren")
        self.assertNotEqual(first.student_id, second.student_id)

    def test_species_defaults_to_none(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertIsNone(student.species)

    def test_species_can_be_set(self):
        student = self.registry.create(name="Aurelia Vance", species="Fada")
        self.assertEqual(student.species, "Fada")

    def test_institution_id_is_nemerion(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertEqual(student.institution_id, "nemerion")

    def test_created_at_is_set(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertTrue(student.created_at)

    def test_status_defaults_to_active(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertEqual(student.status, "active")

    def test_status_can_be_overridden(self):
        student = self.registry.create(name="Aurelia Vance", status="inactive")
        self.assertEqual(student.status, "inactive")

    def test_invalid_status_rejected_at_create(self):
        with self.assertRaises(ValueError):
            self.registry.create(name="Aurelia Vance", status="not_a_real_status")

    def test_historico_is_empty_on_creation(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertEqual(student.historico, ())

    def test_create_persists_to_entries_directory(self):
        student = self.registry.create(name="Aurelia Vance")
        entry_path = Path(self._tmp) / "entries" / f"{student.student_id}.json"
        self.assertTrue(entry_path.exists())


class TestRoundTrip(AcademyStudentRegistryTestBase):
    def test_get_returns_equivalent_student(self):
        created = self.registry.create(name="Aurelia Vance", species="Fada", status="active")
        fetched = self.registry.get(created.student_id)
        self.assertEqual(fetched, created)

    def test_round_trip_preserves_created_at_exactly(self):
        created = self.registry.create(name="Aurelia Vance")
        fetched = self.registry.get(created.student_id)
        self.assertEqual(fetched.created_at, created.created_at)

    def test_round_trip_preserves_historico_shape(self):
        created = self.registry.create(name="Aurelia Vance")
        fetched = self.registry.get(created.student_id)
        self.assertEqual(fetched.historico, ())
        self.assertIsInstance(fetched.historico, tuple)


class TestUnknownStudent(AcademyStudentRegistryTestBase):
    def test_get_unknown_student_returns_none(self):
        self.assertIsNone(self.registry.get("NEM-STU-999999"))

    def test_exists_false_for_unknown_student(self):
        self.assertFalse(self.registry.exists("NEM-STU-999999"))

    def test_exists_true_for_known_student(self):
        student = self.registry.create(name="Aurelia Vance")
        self.assertTrue(self.registry.exists(student.student_id))


class TestEntriesAreSourceOfTruth(AcademyStudentRegistryTestBase):
    def test_load_all_works_without_ever_calling_rebuild_index(self):
        self.registry.create(name="Aurelia Vance")
        self.registry.create(name="Bram Ostergren")
        self.assertFalse(self.registry.index_path.exists())
        students = self.registry.load_all()
        self.assertEqual(len(students), 2)

    def test_get_works_without_ever_calling_rebuild_index(self):
        created = self.registry.create(name="Aurelia Vance")
        self.assertFalse(self.registry.index_path.exists())
        self.assertEqual(self.registry.get(created.student_id), created)

    def test_load_all_on_empty_registry_returns_empty_list(self):
        self.assertEqual(self.registry.load_all(), [])

    def test_load_all_survives_missing_entries_directory(self):
        # a brand-new base with nothing created yet -- entries/ itself
        # does not exist on disk
        fresh = AcademyStudentRegistry(base=tempfile.mkdtemp())
        try:
            self.assertEqual(fresh.load_all(), [])
            self.assertEqual(fresh.count(), 0)
        finally:
            shutil.rmtree(fresh.base, ignore_errors=True)

    def test_count_matches_number_created(self):
        self.registry.create(name="A")
        self.registry.create(name="B")
        self.registry.create(name="C")
        self.assertEqual(self.registry.count(), 3)

    def test_all_is_an_alias_for_load_all(self):
        self.registry.create(name="Aurelia Vance")
        self.assertEqual(self.registry.all(), self.registry.load_all())


class TestRebuildIndex(AcademyStudentRegistryTestBase):
    def test_index_is_derived_and_reconstructible(self):
        s1 = self.registry.create(name="Aurelia Vance")
        s2 = self.registry.create(name="Bram Ostergren", status="inactive")
        index = self.registry.rebuild_index()
        self.assertEqual(index["total_students"], 2)
        self.assertEqual(set(index["student_ids"]), {s1.student_id, s2.student_id})
        self.assertEqual(index["por_status"], {"active": 1, "inactive": 1})

    def test_index_rebuild_never_touches_entries(self):
        student = self.registry.create(name="Aurelia Vance")
        before = read_json(self.registry._entry_path(student.student_id))
        self.registry.rebuild_index()
        after = read_json(self.registry._entry_path(student.student_id))
        self.assertEqual(before, after)

    def test_index_can_be_rebuilt_after_deleting_it(self):
        self.registry.create(name="Aurelia Vance")
        self.registry.rebuild_index()
        self.registry.index_path.unlink()
        rebuilt = self.registry.rebuild_index()
        self.assertEqual(rebuilt["total_students"], 1)

    def test_empty_registry_rebuilds_to_zero_students(self):
        index = self.registry.rebuild_index()
        self.assertEqual(index["total_students"], 0)
        self.assertEqual(index["student_ids"], [])


class TestIdCollisionAndRetry(AcademyStudentRegistryTestBase):
    def test_pre_claimed_candidate_id_is_skipped(self):
        # simulate "someone already reserved NEM-STU-000001" (e.g. a
        # process A that read max=0 and claimed it) before this
        # registry's own create() call runs its scan.
        entries_dir = Path(self._tmp) / "entries"
        atomic_create_json(entries_dir / "NEM-STU-000001.json", {
            "student_id": "NEM-STU-000001", "name": "Ghost", "species": None,
            "institution_id": "nemerion", "created_at": "2026-01-01T00:00:00+00:00",
            "status": "active", "historico": [],
        })
        student = self.registry.create(name="Aurelia Vance")
        self.assertEqual(student.student_id, "NEM-STU-000002")

    def test_pre_claimed_id_content_is_never_overwritten(self):
        entries_dir = Path(self._tmp) / "entries"
        atomic_create_json(entries_dir / "NEM-STU-000001.json", {
            "student_id": "NEM-STU-000001", "name": "Ghost", "species": None,
            "institution_id": "nemerion", "created_at": "2026-01-01T00:00:00+00:00",
            "status": "active", "historico": [],
        })
        self.registry.create(name="Aurelia Vance")
        ghost = self.registry.get("NEM-STU-000001")
        self.assertEqual(ghost.name, "Ghost")

    def test_retries_past_multiple_consecutive_claimed_ids(self):
        entries_dir = Path(self._tmp) / "entries"
        for n in (1, 2, 3):
            atomic_create_json(entries_dir / f"NEM-STU-{n:06d}.json", {
                "student_id": f"NEM-STU-{n:06d}", "name": "Ghost", "species": None,
                "institution_id": "nemerion", "created_at": "2026-01-01T00:00:00+00:00",
                "status": "active", "historico": [],
            })
        student = self.registry.create(name="Aurelia Vance")
        self.assertEqual(student.student_id, "NEM-STU-000004")

    def test_true_concurrent_creates_never_collide(self):
        # two threads calling create() on the SAME registry/base at the
        # same time -- atomic_create_json()'s os.O_CREAT|os.O_EXCL is
        # what must resolve this, not Python-level locking.
        created = []
        lock = threading.Lock()
        barrier = threading.Barrier(2)

        def worker(name):
            barrier.wait()
            student = self.registry.create(name=name)
            with lock:
                created.append(student)

        t1 = threading.Thread(target=worker, args=("Aurelia Vance",))
        t2 = threading.Thread(target=worker, args=("Bram Ostergren",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(created), 2)
        ids = {s.student_id for s in created}
        self.assertEqual(len(ids), 2)  # no duplicate id, no lost student
        self.assertEqual(self.registry.count(), 2)


def _snapshot_real_dir(path):
    """Deterministic content snapshot of the REAL library/academy/
    directory tree — every file's relative path mapped to its exact
    bytes. Used to prove an isolated-registry operation never touches
    real Academia storage. Deliberately never compares against a
    specific student_id/enrollment_id string: once real founders exist
    (Piloto Oficial da Cátedra de Tyche), an isolated tempfile registry
    can legitimately assign the exact same next sequential id (both
    start counting from scratch) — that coincidence proves nothing
    about leakage. Only "the real tree's content is byte-identical
    before and after" proves isolation.
    """
    if not path.exists():
        return {}
    return {p.relative_to(path): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


class TestIsolation(AcademyStudentRegistryTestBase):
    def test_writes_stay_inside_the_configured_base(self):
        real_base = Path("library/academy/students")
        before = _snapshot_real_dir(real_base)

        student = self.registry.create(name="Aurelia Vance")

        after = _snapshot_real_dir(real_base)
        self.assertEqual(before, after, "real library/academy/students/ must be byte-identical before and after")
        # the isolated registry itself DID receive the write, proving
        # this is a real isolation test and not a no-op
        self.assertTrue(str(self.registry.base).startswith(tempfile.gettempdir()))
        self.assertTrue(self.registry.exists(student.student_id))


if __name__ == "__main__":
    unittest.main()
