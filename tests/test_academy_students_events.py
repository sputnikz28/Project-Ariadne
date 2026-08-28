"""Tests for library/academy/students/registry.py's AcademicEvent /
append_event() / historico projection — Academia Arcana de Nemerion
Foundation V1, commit 5/5. Every test uses an isolated tempfile base;
nothing here ever writes to the real library/academy/students/.
"""

import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from types import MappingProxyType

from core.services.atomic_io import read_json
from library.academy.students.registry import (
    AcademicEvent,
    AcademyStudentRegistry,
    StudentNotFoundError,
)


class AcademyStudentEventsTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.registry = AcademyStudentRegistry(base=self._tmp)
        self.student = self.registry.create(name="Aurelia Vance")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _append(self, event_id, **overrides):
        args = dict(
            student_id=self.student.student_id,
            event_type="test_participation",
            occurred_at="2026-08-25T10:00:00+00:00",
            event_id=event_id,
            extra={"enrollment_id": "NEM-ENR-000001"},
        )
        args.update(overrides)
        return self.registry.append_event(**args)


class TestAppendEventBasics(AcademyStudentEventsTestBase):
    def test_first_event_created(self):
        event, created = self._append("EVT-001")
        self.assertTrue(created)
        self.assertEqual(event.event_id, "EVT-001")

    def test_event_persisted_to_events_directory(self):
        self._append("EVT-001")
        path = Path(self._tmp) / "events" / self.student.student_id / "EVT-001.json"
        self.assertTrue(path.exists())

    def test_second_event_preserves_first(self):
        self._append("EVT-001")
        self._append("EVT-002")
        student = self.registry.get(self.student.student_id)
        self.assertEqual({e.event_id for e in student.historico}, {"EVT-001", "EVT-002"})

    def test_old_event_content_unchanged_after_a_second_append(self):
        self._append("EVT-001", extra={"marker": "first"})
        before = read_json(Path(self._tmp) / "events" / self.student.student_id / "EVT-001.json")
        self._append("EVT-002", extra={"marker": "second"})
        after = read_json(Path(self._tmp) / "events" / self.student.student_id / "EVT-001.json")
        self.assertEqual(before, after)

    def test_student_id_and_created_at_untouched_by_append(self):
        before = self.registry.get(self.student.student_id)
        self._append("EVT-001")
        after = self.registry.get(self.student.student_id)
        self.assertEqual(before.student_id, after.student_id)
        self.assertEqual(before.created_at, after.created_at)

    def test_unknown_student_is_rejected(self):
        with self.assertRaises(StudentNotFoundError):
            self.registry.append_event(
                student_id="NEM-STU-999999", event_type="test_participation",
                occurred_at="2026-08-25T10:00:00+00:00", event_id="EVT-001", extra={},
            )

    def test_unknown_student_leaves_no_event_file(self):
        try:
            self.registry.append_event(
                student_id="NEM-STU-999999", event_type="test_participation",
                occurred_at="2026-08-25T10:00:00+00:00", event_id="EVT-001", extra={},
            )
        except StudentNotFoundError:
            pass
        events_root = Path(self._tmp) / "events" / "NEM-STU-999999"
        self.assertFalse(events_root.exists())


class TestAcademicEventShape(AcademyStudentEventsTestBase):
    def test_round_trip(self):
        self._append("EVT-001", extra={"enrollment_id": "NEM-ENR-000001", "category": "0+0"})
        student = self.registry.get(self.student.student_id)
        event = student.historico[0]
        self.assertIsInstance(event, AcademicEvent)
        self.assertEqual(event.event_type, "test_participation")
        self.assertEqual(event.occurred_at, "2026-08-25T10:00:00+00:00")
        self.assertEqual(event.extra["enrollment_id"], "NEM-ENR-000001")
        self.assertEqual(event.extra["category"], "0+0")

    def test_extra_is_read_only(self):
        self._append("EVT-001")
        event = self.registry.get(self.student.student_id).historico[0]
        self.assertIsInstance(event.extra, MappingProxyType)
        with self.assertRaises(TypeError):
            event.extra["enrollment_id"] = "changed"

    def test_historical_target_lives_separately_from_occurred_at(self):
        self._append("EVT-001", extra={"enrollment_id": "NEM-ENR-000001", "historical_target": "006/2005"})
        event = self.registry.get(self.student.student_id).historico[0]
        self.assertEqual(event.occurred_at, "2026-08-25T10:00:00+00:00")
        self.assertEqual(event.extra["historical_target"], "006/2005")
        self.assertNotEqual(event.occurred_at, event.extra["historical_target"])

    def test_candidate_summary_preserved(self):
        self._append("EVT-001", extra={
            "enrollment_id": "NEM-ENR-000001",
            "candidate_summary": {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
        })
        event = self.registry.get(self.student.student_id).historico[0]
        self.assertEqual(event.extra["candidate_summary"], {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]})


class TestAppendOnlyImmutability(AcademyStudentEventsTestBase):
    def test_no_edit_api_exists(self):
        self.assertFalse(hasattr(self.registry, "edit_event"))
        self.assertFalse(hasattr(self.registry, "update_event"))

    def test_no_delete_api_exists(self):
        self.assertFalse(hasattr(self.registry, "delete_event"))
        self.assertFalse(hasattr(self.registry, "remove_event"))

    def test_no_generic_update_student_api_exists(self):
        self.assertFalse(hasattr(self.registry, "update_student"))


class TestIdempotency(AcademyStudentEventsTestBase):
    def test_same_event_id_processed_twice_yields_one_logical_event(self):
        self._append("EVT-001", extra={"enrollment_id": "NEM-ENR-000001"})
        self._append("EVT-001", extra={"enrollment_id": "NEM-ENR-000001"})
        student = self.registry.get(self.student.student_id)
        self.assertEqual(len(student.historico), 1)

    def test_second_call_with_same_event_id_reports_created_false(self):
        _event1, created1 = self._append("EVT-001")
        _event2, created2 = self._append("EVT-001")
        self.assertTrue(created1)
        self.assertFalse(created2)

    def test_second_call_returns_the_original_content_not_the_new_attempt(self):
        self._append("EVT-001", extra={"enrollment_id": "NEM-ENR-000001", "marker": "original"})
        event2, created2 = self._append("EVT-001", extra={"enrollment_id": "NEM-ENR-000001", "marker": "attempted-overwrite"})
        self.assertFalse(created2)
        self.assertEqual(event2.extra["marker"], "original")

    def test_different_event_ids_are_distinct_events(self):
        self._append("EVT-001")
        self._append("EVT-002")
        student = self.registry.get(self.student.student_id)
        self.assertEqual(len(student.historico), 2)

    def test_different_students_never_collide_on_the_same_event_id(self):
        other = self.registry.create(name="Bram Ostergren")
        self._append("EVT-SAME")
        self.registry.append_event(
            student_id=other.student_id, event_type="test_participation",
            occurred_at="2026-08-25T10:00:00+00:00", event_id="EVT-SAME", extra={},
        )
        self.assertEqual(len(self.registry.get(self.student.student_id).historico), 1)
        self.assertEqual(len(self.registry.get(other.student_id).historico), 1)


class TestOrdering(AcademyStudentEventsTestBase):
    def test_historico_sorted_by_occurred_at(self):
        self._append("EVT-LATER", occurred_at="2026-08-25T12:00:00+00:00")
        self._append("EVT-EARLIER", occurred_at="2026-08-25T09:00:00+00:00")
        student = self.registry.get(self.student.student_id)
        self.assertEqual([e.event_id for e in student.historico], ["EVT-EARLIER", "EVT-LATER"])

    def test_never_ordered_by_historical_target(self):
        # Grumbar-style example from the approved design: an exam about
        # a LATER historical draw registered FIRST, followed by an exam
        # about an EARLIER historical draw registered SECOND -- academic
        # order must follow occurred_at (registration order), never the
        # historical_target value embedded in extra.
        self._append("EVT-FIRST", occurred_at="2026-08-25T09:00:00+00:00", extra={"historical_target": "050/2024"})
        self._append("EVT-SECOND", occurred_at="2026-08-25T10:00:00+00:00", extra={"historical_target": "006/2008"})
        student = self.registry.get(self.student.student_id)
        self.assertEqual([e.event_id for e in student.historico], ["EVT-FIRST", "EVT-SECOND"])

    def test_tie_break_by_event_id_when_occurred_at_matches(self):
        same_time = "2026-08-25T10:00:00+00:00"
        self._append("EVT-B", occurred_at=same_time)
        self._append("EVT-A", occurred_at=same_time)
        student = self.registry.get(self.student.student_id)
        self.assertEqual([e.event_id for e in student.historico], ["EVT-A", "EVT-B"])

    def test_load_all_also_projects_ordered_historico(self):
        self._append("EVT-LATER", occurred_at="2026-08-25T12:00:00+00:00")
        self._append("EVT-EARLIER", occurred_at="2026-08-25T09:00:00+00:00")
        student = next(s for s in self.registry.load_all() if s.student_id == self.student.student_id)
        self.assertEqual([e.event_id for e in student.historico], ["EVT-EARLIER", "EVT-LATER"])


class TestConcurrency(AcademyStudentEventsTestBase):
    def test_different_events_in_parallel_both_survive(self):
        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(2)

        def worker(event_id):
            barrier.wait()
            result = self._append(event_id)
            with lock:
                results.append(result)

        t1 = threading.Thread(target=worker, args=("EVT-A",))
        t2 = threading.Thread(target=worker, args=("EVT-B",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertTrue(all(created for _event, created in results))
        student = self.registry.get(self.student.student_id)
        self.assertEqual({e.event_id for e in student.historico}, {"EVT-A", "EVT-B"})

    def test_same_event_in_parallel_exactly_one_winner_no_duplicate(self):
        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(2)

        def worker(marker):
            barrier.wait()
            result = self._append("EVT-RACE", extra={"enrollment_id": "NEM-ENR-000001", "marker": marker})
            with lock:
                results.append(result)

        t1 = threading.Thread(target=worker, args=("t1",))
        t2 = threading.Thread(target=worker, args=("t2",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        created_flags = sorted(created for _event, created in results)
        self.assertEqual(created_flags, [False, True])
        student = self.registry.get(self.student.student_id)
        self.assertEqual(len(student.historico), 1)  # never duplicated


if __name__ == "__main__":
    unittest.main()
