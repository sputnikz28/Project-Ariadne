"""Tests for core/services/academia/common.py — Academia Arcana de
Nemerion Foundation V1, commit 1/5. Proves only the shared vocabulary:
DoctrineResult, AcademyClassroomIdentity, classroom_race_label,
academia_rng, build_academy_candidate_key. No student, enrollment,
classroom, or doctrine exists yet — this file constructs an ad-hoc
AcademyClassroomIdentity example inline (not Tyche's real identity,
which is Tyche's own responsibility to define, in a later commit).
"""

import inspect
import unittest
from types import MappingProxyType

from core.services.academia.common import (
    AcademyClassroomIdentity,
    DoctrineResult,
    academia_rng,
    build_academy_candidate_key,
    classroom_race_label,
)
from core.services.candidate_provenance import CandidateKey

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
        })

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


if __name__ == "__main__":
    unittest.main()
