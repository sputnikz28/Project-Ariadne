"""Tests for core/services/academia/common.py — Academia Arcana de
Nemerion Foundation V1. Commit 1/5 proved the shared vocabulary:
DoctrineResult, AcademyClassroomIdentity, classroom_race_label,
academia_rng, build_academy_candidate_key — this file constructs an
ad-hoc AcademyClassroomIdentity example inline for those (not Tyche's
real identity, which is core.services.academia.tyche's own
responsibility, see tests/test_academia_tyche.py). Commit 4/5 added
resolve_eligible_participants(), tested below against isolated
tempfile student/enrollment registries — never the real
library/academy/.
"""

import inspect
import shutil
import tempfile
import unittest
from types import MappingProxyType

from core.services.academia.common import (
    AcademyClassroomIdentity,
    DoctrineResult,
    academia_rng,
    build_academy_candidate_key,
    classroom_race_label,
    resolve_eligible_participants,
)
from core.services.candidate_provenance import CandidateKey
from library.academy.enrollments.registry import AcademyEnrollmentRegistry
from library.academy.students.registry import AcademyStudentRegistry

_EXAMPLE_IDENTITY = AcademyClassroomIdentity(
    institution_id="nemerion",
    institution_name="Academia Arcana de Nemerion",
    classroom_id="example_classroom",
    classroom_name="Example Classroom — Example Doctrine",
    doctrine_id="example_doctrine",
    doctrine_version="v1",
)


class TestDoctrineResult(unittest.TestCase):
    def test_holds_a_key(self):
        result = DoctrineResult(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        self.assertEqual(result.numeros, (1, 2, 3, 4, 5))
        self.assertEqual(result.estrelas, (1, 2))

    def test_holds_abstention(self):
        result = DoctrineResult(numeros=None, estrelas=None)
        self.assertIsNone(result.numeros)
        self.assertIsNone(result.estrelas)


class TestClassroomRaceLabel(unittest.TestCase):
    def test_uses_classroom_name(self):
        self.assertEqual(
            classroom_race_label(_EXAMPLE_IDENTITY),
            "Example Classroom — Example Doctrine",
        )

    def test_ignores_classroom_id_and_doctrine_fields(self):
        renamed = AcademyClassroomIdentity(
            institution_id="nemerion",
            institution_name="Academia Arcana de Nemerion",
            classroom_id="example_classroom",  # same id
            classroom_name="A Different Narrative Name",  # renamed
            doctrine_id="example_doctrine",  # same id
            doctrine_version="v1",
        )
        self.assertNotEqual(
            classroom_race_label(_EXAMPLE_IDENTITY), classroom_race_label(renamed)
        )


class TestAcademiaRng(unittest.TestCase):
    _BASE_ARGS = dict(
        seed=1,
        institution_id="nemerion",
        classroom_id="example_classroom",
        doctrine_id="example_doctrine",
        doctrine_version="v1",
        student_id="NEM-STU-000001",
        target_draw_id="001/2099",
    )

    def test_same_arguments_give_the_same_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**self._BASE_ARGS)
        self.assertEqual(r1.random(), r2.random())

    def test_different_student_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, student_id="NEM-STU-000002"))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_classroom_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, classroom_id="other_classroom"))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_institution_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, institution_id="other_institution"))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_doctrine_id_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, doctrine_id="other_doctrine"))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_doctrine_version_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, doctrine_version="v2"))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_target_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, target_draw_id="002/2099"))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_seed_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS)
        r2 = academia_rng(**dict(self._BASE_ARGS, seed=2))
        self.assertNotEqual(r1.random(), r2.random())

    def test_different_purpose_gives_different_stream(self):
        r1 = academia_rng(**self._BASE_ARGS, purpose="candidate")
        r2 = academia_rng(**self._BASE_ARGS, purpose="other")
        self.assertNotEqual(r1.random(), r2.random())

    def test_never_uses_builtin_hash(self):
        import core.services.academia.common as _common_module
        source = inspect.getsource(_common_module)
        self.assertNotIn("hash(", source)


class TestBuildAcademyCandidateKey(unittest.TestCase):
    def _build(self, **overrides):
        args = dict(
            identity=_EXAMPLE_IDENTITY,
            student_id="NEM-STU-000001",
            student_name="Aurelia Vance",
            student_species=None,
            enrollment_id="NEM-ENR-000001",
            numeros=(41, 7, 22, 33, 14),
            estrelas=(9, 3),
        )
        args.update(overrides)
        return build_academy_candidate_key(**args)

    def test_returns_candidate_key(self):
        self.assertIsInstance(self._build(), CandidateKey)

    def test_source_type_and_name(self):
        key = self._build()
        self.assertEqual(key.source_type, "external_generator")
        self.assertEqual(key.source_name, "academia")

    def test_numeros_and_estrelas_sorted(self):
        key = self._build()
        self.assertEqual(key.numeros, (7, 14, 22, 33, 41))
        self.assertEqual(key.estrelas, (3, 9))

    def test_generation_always_none(self):
        self.assertIsNone(self._build().generation)

    def test_entity_id_is_student_id(self):
        self.assertEqual(self._build().entity_id, "NEM-STU-000001")

    def test_entity_name_is_student_name(self):
        self.assertEqual(self._build().entity_name, "Aurelia Vance")

    def test_race_is_classroom_race_label(self):
        self.assertEqual(self._build().race, "Example Classroom — Example Doctrine")

    def test_metadata_carries_full_provenance(self):
        key = self._build()
        self.assertEqual(dict(key.metadata), {
            "institution_id": "nemerion",
            "institution_name": "Academia Arcana de Nemerion",
            "classroom_id": "example_classroom",
            "classroom_name": "Example Classroom — Example Doctrine",
            "doctrine_id": "example_doctrine",
            "doctrine_version": "v1",
            "student_species": None,
            "enrollment_id": "NEM-ENR-000001",
        })

    def test_metadata_carries_enrollment_id(self):
        key = self._build(enrollment_id="NEM-ENR-000042")
        self.assertEqual(key.metadata["enrollment_id"], "NEM-ENR-000042")

    def test_metadata_is_read_only(self):
        key = self._build()
        self.assertIsInstance(key.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            key.metadata["institution_id"] = "changed"

    def test_metadata_carries_species_when_defined(self):
        key = self._build(student_species="Fada")
        self.assertEqual(key.metadata["student_species"], "Fada")

    def test_two_students_same_classroom_have_different_entity_id_same_race(self):
        k1 = self._build(student_id="NEM-STU-000001", student_name="Aurelia Vance")
        k2 = self._build(student_id="NEM-STU-000002", student_name="Bram Ostergren")
        self.assertNotEqual(k1.entity_id, k2.entity_id)
        self.assertEqual(k1.race, k2.race)


class TestResolveEligibleParticipants(unittest.TestCase):
    def setUp(self):
        self._students_tmp = tempfile.mkdtemp()
        self._enrollments_tmp = tempfile.mkdtemp()
        self.student_registry = AcademyStudentRegistry(base=self._students_tmp)
        self.enrollment_registry = AcademyEnrollmentRegistry(base=self._enrollments_tmp)

    def tearDown(self):
        shutil.rmtree(self._students_tmp, ignore_errors=True)
        shutil.rmtree(self._enrollments_tmp, ignore_errors=True)

    def _resolve(self):
        return resolve_eligible_participants(_EXAMPLE_IDENTITY, self._students_tmp, self._enrollments_tmp)

    def _enroll(self, student, **overrides):
        args = dict(
            student_id=student.student_id,
            classroom_id=_EXAMPLE_IDENTITY.classroom_id,
            doctrine_id=_EXAMPLE_IDENTITY.doctrine_id,
            doctrine_version=_EXAMPLE_IDENTITY.doctrine_version,
            student_registry=self.student_registry,
        )
        args.update(overrides)
        return self.enrollment_registry.create(**args)

    def test_empty_registries_yield_no_participants(self):
        self.assertEqual(self._resolve(), ())

    def test_active_student_with_active_enrollment_is_eligible(self):
        student = self.student_registry.create(name="Aurelia Vance")
        enrollment = self._enroll(student)
        self.assertEqual(self._resolve(), ((student, enrollment),))

    def test_inactive_student_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance", status="inactive")
        self._enroll(student)
        self.assertEqual(self._resolve(), ())

    def test_graduated_student_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance", status="graduated")
        self._enroll(student)
        self.assertEqual(self._resolve(), ())

    def test_expelled_student_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance", status="expelled")
        self._enroll(student)
        self.assertEqual(self._resolve(), ())

    def test_withdrawn_enrollment_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student, status="withdrawn")
        self.assertEqual(self._resolve(), ())

    def test_completed_enrollment_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student, status="completed")
        self.assertEqual(self._resolve(), ())

    def test_enrollment_for_a_different_classroom_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student, classroom_id="rebeldes")
        self.assertEqual(self._resolve(), ())

    def test_enrollment_for_a_different_doctrine_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student, doctrine_id="outra_doutrina")
        self.assertEqual(self._resolve(), ())

    def test_enrollment_for_a_different_doctrine_version_is_excluded(self):
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student, doctrine_version="v2")
        self.assertEqual(self._resolve(), ())

    def test_multiple_eligible_students_all_included(self):
        s1 = self.student_registry.create(name="Aurelia Vance")
        s2 = self.student_registry.create(name="Bram Ostergren")
        e1 = self._enroll(s1)
        e2 = self._enroll(s2)
        self.assertEqual(self._resolve(), ((s1, e1), (s2, e2)))

    def test_ineligible_student_does_not_block_eligible_ones(self):
        eligible = self.student_registry.create(name="Aurelia Vance")
        ineligible = self.student_registry.create(name="Ghost", status="expelled")
        e1 = self._enroll(eligible)
        self._enroll(ineligible)
        self.assertEqual(self._resolve(), ((eligible, e1),))

    def test_dangling_student_reference_is_excluded_not_raised(self):
        # Simulates a student that no longer exists on record -- there
        # is no public delete API, so this is only reachable via
        # external tampering; still must never be fabricated into a
        # participant nor raise an error that would abort a cell.
        from core.services.atomic_io import atomic_create_json
        from pathlib import Path
        entries_dir = Path(self._enrollments_tmp) / "entries"
        atomic_create_json(entries_dir / "NEM-ENR-000001.json", {
            "enrollment_id": "NEM-ENR-000001", "student_id": "NEM-STU-999999",
            "institution_id": _EXAMPLE_IDENTITY.institution_id,
            "classroom_id": _EXAMPLE_IDENTITY.classroom_id,
            "doctrine_id": _EXAMPLE_IDENTITY.doctrine_id,
            "doctrine_version": _EXAMPLE_IDENTITY.doctrine_version,
            "status": "active", "enrolled_at": "2026-01-01T00:00:00+00:00",
        })
        self.assertEqual(self._resolve(), ())

    def test_never_creates_mutates_or_deletes_a_student_or_enrollment(self):
        student = self.student_registry.create(name="Aurelia Vance")
        enrollment = self._enroll(student)
        before_students = self.student_registry.load_all()
        before_enrollments = self.enrollment_registry.load_all()
        self._resolve()
        self.assertEqual(self.student_registry.load_all(), before_students)
        self.assertEqual(self.enrollment_registry.load_all(), before_enrollments)


if __name__ == "__main__":
    unittest.main()
