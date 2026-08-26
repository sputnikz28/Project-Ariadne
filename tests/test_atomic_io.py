"""Tests for core/services/atomic_io.py's atomic_create_json() — the
create-if-absent primitive added for the Academia's AcademyStudentRegistry
(library/academy/students/registry.py). atomic_write_json()/read_json()
already have extensive implicit coverage via the Heroes/Legends registry
tests; this file only covers the new function.
"""

import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from core.services.atomic_io import atomic_create_json, atomic_write_json, read_json


class TestAtomicCreateJson(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _path(self, name="entry.json"):
        return Path(self._tmp) / name

    def test_creates_file_and_returns_true(self):
        created = atomic_create_json(self._path(), {"a": 1})
        self.assertTrue(created)
        self.assertEqual(read_json(self._path()), {"a": 1})

    def test_creates_missing_parent_directories(self):
        path = Path(self._tmp) / "nested" / "deeper" / "entry.json"
        created = atomic_create_json(path, {"a": 1})
        self.assertTrue(created)
        self.assertEqual(read_json(path), {"a": 1})

    def test_second_call_on_same_path_returns_false(self):
        atomic_create_json(self._path(), {"a": 1})
        created_again = atomic_create_json(self._path(), {"a": 2})
        self.assertFalse(created_again)

    def test_second_call_never_overwrites_existing_content(self):
        atomic_create_json(self._path(), {"a": 1})
        atomic_create_json(self._path(), {"a": 2})
        self.assertEqual(read_json(self._path()), {"a": 1})

    def test_does_not_collide_with_atomic_write_json_on_a_different_path(self):
        atomic_write_json(self._path("other.json"), {"x": 1})
        created = atomic_create_json(self._path(), {"a": 1})
        self.assertTrue(created)

    def test_file_content_is_valid_json_written_with_indent(self):
        atomic_create_json(self._path(), {"a": 1, "b": [1, 2, 3]})
        raw = self._path().read_text(encoding="utf-8")
        self.assertEqual(json.loads(raw), {"a": 1, "b": [1, 2, 3]})
        self.assertIn("\n", raw)  # indent=2 formatting, not a single line

    def test_true_concurrent_race_exactly_one_winner(self):
        # Two threads racing os.open(O_CREAT|O_EXCL) against the exact
        # same path -- os.open is a real syscall that releases the GIL,
        # so this exercises the actual OS-level exclusivity guarantee,
        # not just Python-level serialization.
        path = self._path("race.json")
        results = []
        barrier = threading.Barrier(2)

        def attempt(value):
            barrier.wait()
            results.append(atomic_create_json(path, {"winner": value}))

        t1 = threading.Thread(target=attempt, args=(1,))
        t2 = threading.Thread(target=attempt, args=(2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(sorted(results), [False, True])
        self.assertTrue(path.exists())
        # exactly one winner's content survives -- never a mix, never both
        stored = read_json(path)
        self.assertIn(stored["winner"], (1, 2))


if __name__ == "__main__":
    unittest.main()
