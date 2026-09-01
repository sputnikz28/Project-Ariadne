"""Tests for bootstrap_nemerion_mnemosyne.py — Cátedra de Mnemosyne's
founding-class bootstrap. Every test drives the module's internal
functions (inspect_current_state/classify_state/create_founders)
against isolated tempfile registries — main() itself (which
constructs AcademyStudentRegistry()/AcademyEnrollmentRegistry() with
no base, i.e. the REAL library/academy/ paths) is never called here;
the real, one-time execution happens separately, outside the test
suite, exactly like bootstrap_nemerion_tyche.py's own precedent.
"""

import shutil
import tempfile
import unittest

import bootstrap_nemerion_mnemosyne as bootstrap
from core.services.academia.mnemosyne import MNEMOSYNE_IDENTITY
from core.services.academia.tyche import TYCHE_IDENTITY
from library.academy.enrollments.registry import AcademyEnrollmentRegistry
from library.academy.students.registry import AcademyStudentRegistry


class TestImportSafety(unittest.TestCase):
    def test_module_defines_no_registry_instances_at_import_time(self):
        # importing the module (already done above, at file load) must
        # never have created a real AcademyStudentRegistry/
        # AcademyEnrollmentRegistry instance or touched disk -- proven
        # by inspecting the module for top-level side effects.
        import inspect
        source = inspect.getsource(bootstrap)
        # only main() may construct real (base=None) registries
        before_main = source.split("def main(")[0]
        self.assertNotIn("AcademyStudentRegistry(", before_main)
        self.assertNotIn("AcademyEnrollmentRegistry(", before_main)

    def test_founder_names_is_a_plain_tuple_defined_at_module_level(self):
        self.assertIsInstance(bootstrap.FOUNDER_NAMES, tuple)


class TestFounderNames(unittest.TestCase):
    def test_exactly_five_founders(self):
        self.assertEqual(len(bootstrap.FOUNDER_NAMES), 5)

    def test_founder_names_are_distinct(self):
        self.assertEqual(len(set(bootstrap.FOUNDER_NAMES)), 5)

    def test_founder_names_distinct_from_tyche_founders(self):
        tyche_founders = {"Isolde Ferrand", "Corwin Ashdown", "Maren Kestrel", "Thane Vosloo", "Lyria Sundvik"}
        self.assertEqual(set(bootstrap.FOUNDER_NAMES) & tyche_founders, set())


class BootstrapMnemosyneTestBase(unittest.TestCase):
    def setUp(self):
        self._students_tmp = tempfile.mkdtemp()
        self._enrollments_tmp = tempfile.mkdtemp()
        self.student_registry = AcademyStudentRegistry(base=self._students_tmp)
        self.enrollment_registry = AcademyEnrollmentRegistry(base=self._enrollments_tmp)

    def tearDown(self):
        shutil.rmtree(self._students_tmp, ignore_errors=True)
        shutil.rmtree(self._enrollments_tmp, ignore_errors=True)

    def _run_once(self):
        founders_by_name, active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        state = bootstrap.classify_state(founders_by_name, active)
        if state == "fresh":
            return bootstrap.create_founders(self.student_registry, self.enrollment_registry)
        return None  # already_done


class TestCreateFounders(BootstrapMnemosyneTestBase):
    def test_creates_exactly_five_students(self):
        created = self._run_once()
        self.assertEqual(len(created), 5)
        self.assertEqual(self.student_registry.count(), 5)

    def test_creates_exactly_five_enrollments(self):
        self._run_once()
        self.assertEqual(self.enrollment_registry.count(), 5)

    def test_all_students_have_species_none(self):
        created = self._run_once()
        self.assertTrue(all(student.species is None for student, _enrollment in created))

    def test_all_students_active(self):
        created = self._run_once()
        self.assertTrue(all(student.status == "active" for student, _enrollment in created))

    def test_uses_mnemosyne_identity_not_hardcoded_strings(self):
        created = self._run_once()
        for _student, enrollment in created:
            self.assertEqual(enrollment.institution_id, MNEMOSYNE_IDENTITY.institution_id)
            self.assertEqual(enrollment.classroom_id, MNEMOSYNE_IDENTITY.classroom_id)
            self.assertEqual(enrollment.doctrine_id, MNEMOSYNE_IDENTITY.doctrine_id)
            self.assertEqual(enrollment.doctrine_version, MNEMOSYNE_IDENTITY.doctrine_version)
            self.assertEqual(enrollment.status, "active")

    def test_student_names_match_founder_names_in_order(self):
        created = self._run_once()
        self.assertEqual([s.name for s, _e in created], list(bootstrap.FOUNDER_NAMES))

    def test_ids_assigned_by_registries_not_hardcoded(self):
        created = self._run_once()
        for student, enrollment in created:
            self.assertTrue(student.student_id.startswith("NEM-STU-"))
            self.assertTrue(enrollment.enrollment_id.startswith("NEM-ENR-"))


class TestIdempotency(BootstrapMnemosyneTestBase):
    def test_second_run_creates_nothing(self):
        self._run_once()
        before_students = self.student_registry.count()
        before_enrollments = self.enrollment_registry.count()

        result = self._run_once()  # second call -- should classify as already_done
        self.assertIsNone(result)
        self.assertEqual(self.student_registry.count(), before_students)
        self.assertEqual(self.enrollment_registry.count(), before_enrollments)

    def test_second_run_recognizes_already_done_state(self):
        self._run_once()
        founders_by_name, active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        state = bootstrap.classify_state(founders_by_name, active)
        self.assertEqual(state, "already_done")

    def test_ids_identical_across_two_runs(self):
        first = self._run_once()
        first_ids = {s.student_id for s, _e in first}
        self._run_once()
        founders_by_name, _active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        second_ids = {s.student_id for s in founders_by_name.values()}
        self.assertEqual(first_ids, second_ids)


class TestAmbiguousStates(BootstrapMnemosyneTestBase):
    def test_partial_founders_raises_abort(self):
        # only 2 of 5 founders exist, no enrollments
        self.student_registry.create(name=bootstrap.FOUNDER_NAMES[0])
        self.student_registry.create(name=bootstrap.FOUNDER_NAMES[1])
        founders_by_name, active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        with self.assertRaises(bootstrap.BootstrapAbort):
            bootstrap.classify_state(founders_by_name, active)

    def test_founder_without_enrollment_raises_abort(self):
        for name in bootstrap.FOUNDER_NAMES:
            self.student_registry.create(name=name)
        founders_by_name, active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        with self.assertRaises(bootstrap.BootstrapAbort):
            bootstrap.classify_state(founders_by_name, active)

    def test_classroom_full_with_unexpected_students_raises_abort(self):
        strangers = [self.student_registry.create(name=f"Stranger {i}") for i in range(5)]
        for stranger in strangers:
            self.enrollment_registry.create(
                student_id=stranger.student_id,
                classroom_id=MNEMOSYNE_IDENTITY.classroom_id,
                doctrine_id=MNEMOSYNE_IDENTITY.doctrine_id,
                doctrine_version=MNEMOSYNE_IDENTITY.doctrine_version,
                student_registry=self.student_registry,
            )
        founders_by_name, active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        with self.assertRaises(bootstrap.BootstrapAbort):
            bootstrap.classify_state(founders_by_name, active)

    def test_duplicate_founder_name_raises_abort_in_inspect_itself(self):
        self.student_registry.create(name=bootstrap.FOUNDER_NAMES[0])
        self.student_registry.create(name=bootstrap.FOUNDER_NAMES[0])
        with self.assertRaises(bootstrap.BootstrapAbort):
            bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)

    def test_ambiguous_state_creates_no_new_data(self):
        for name in bootstrap.FOUNDER_NAMES:
            self.student_registry.create(name=name)
        before_students = self.student_registry.count()
        before_enrollments = self.enrollment_registry.count()
        founders_by_name, active = bootstrap.inspect_current_state(self.student_registry, self.enrollment_registry)
        try:
            bootstrap.classify_state(founders_by_name, active)
        except bootstrap.BootstrapAbort:
            pass
        self.assertEqual(self.student_registry.count(), before_students)
        self.assertEqual(self.enrollment_registry.count(), before_enrollments)


class TestNeverTouchesTyche(BootstrapMnemosyneTestBase):
    def test_pre_existing_tyche_enrollment_does_not_block_mnemosyne_bootstrap(self):
        tyche_student = self.student_registry.create(name="Some Tyche Founder")
        self.enrollment_registry.create(
            student_id=tyche_student.student_id,
            classroom_id=TYCHE_IDENTITY.classroom_id,
            doctrine_id=TYCHE_IDENTITY.doctrine_id,
            doctrine_version=TYCHE_IDENTITY.doctrine_version,
            student_registry=self.student_registry,
        )
        created = self._run_once()
        self.assertEqual(len(created), 5)
        # Tyche's own student/enrollment untouched
        self.assertEqual(self.student_registry.get(tyche_student.student_id).status, "active")

    def test_mnemosyne_enrollments_never_reference_tyche_classroom(self):
        created = self._run_once()
        for _student, enrollment in created:
            self.assertNotEqual(enrollment.classroom_id, TYCHE_IDENTITY.classroom_id)
            self.assertNotEqual(enrollment.doctrine_id, TYCHE_IDENTITY.doctrine_id)


if __name__ == "__main__":
    unittest.main()
