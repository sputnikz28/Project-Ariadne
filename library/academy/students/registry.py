"""AcademyStudentRegistry — persistent identity for Academia Arcana de
Nemerion students. Foundation V1, commit 2/5: for the first time,
Nemerion can create a student and later find them again as the same
person. entries/<student_id>.json are the source of truth;
LIVRO_DA_ACADEMIA.json is a derived index/summary, always rebuildable
from entries/ — never the only copy. Mirrors library/heroes/registry.py
and library/legends/registry.py's entries+derived-index shape; writes
go through core/services/atomic_io.py, exactly like both.

Unlike Heroes (deduplicated by prediction content via dedup_hash) and
Legends (identified by source_prediction_id), a Student is never
deduplicated by content or by name — create() always makes a brand new,
distinct identity, even for two students who share the exact same name.
student_id is sequential and opaque ("NEM-STU-000001", ...), assigned by
create() itself; it is never derived from name, content, target, seed,
or run — created_at already carries the moment of creation, so the id
does not need to.

Concurrent creation safety: atomic_write_json() (used by both Heroes and
Legends) always succeeds and unconditionally overwrites its target — it
has no create-if-absent guarantee, so two processes racing to claim the
same candidate student_id (both scanning entries/, both computing the
same "max + 1") could otherwise silently clobber each other, losing a
student. create() instead reserves each candidate id via
core.services.atomic_io.atomic_create_json() (os.O_CREAT | os.O_EXCL —
an OS-level exclusive-create guarantee, true even across real concurrent
processes/threads, proven directly in tests/test_atomic_io.py) and
retries with the next candidate id whenever a reservation attempt loses
the race, instead of inventing any separate locking mechanism.

historico is persisted structure only in this commit: every student is
created with historico=() and there is no public API to append to it
yet. No AcademyEnrollment, no AcademicEvent, and — deliberately — no
generic "update" method exists here at all, so this commit cannot
silently rewrite student_id, created_at, or any past event. Those wait
for commit 3 (AcademyEnrollment + academic history).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.services.atomic_io import atomic_create_json, atomic_write_json, read_json

BASE = Path("library/academy/students")
_ID_PREFIX = "NEM-STU-"
_ID_WIDTH = 6
VALID_STATUSES = ("active", "inactive", "graduated", "expelled")


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AcademyStudent:
    """species=None is a legitimate, honest "not yet defined" — never
    fabricated. institution_id is always "nemerion" in Foundation V1
    (the only institution that exists); the field exists so a student
    record is self-describing without relying on which registry loaded
    it. historico is a tuple of already-serialized event dicts — empty
    for every student created by this commit.
    """

    student_id: str
    name: str
    species: str | None
    institution_id: str
    created_at: str
    status: str
    historico: tuple[dict, ...] = ()

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status {self.status!r} — must be one of {VALID_STATUSES}")


def _record_from_student(student: AcademyStudent) -> dict:
    return {
        "student_id": student.student_id,
        "name": student.name,
        "species": student.species,
        "institution_id": student.institution_id,
        "created_at": student.created_at,
        "status": student.status,
        "historico": list(student.historico),
    }


def _student_from_record(record: dict) -> AcademyStudent:
    return AcademyStudent(
        student_id=record["student_id"],
        name=record["name"],
        species=record["species"],
        institution_id=record["institution_id"],
        created_at=record["created_at"],
        status=record["status"],
        historico=tuple(record.get("historico", [])),
    )


class AcademyStudentRegistry:
    def __init__(self, base=None):
        self.base = Path(base) if base is not None else BASE
        self.entries_dir = self.base / "entries"
        self.index_path = self.base / "LIVRO_DA_ACADEMIA.json"

    # -- persistence --------------------------------------------------

    def _entry_path(self, student_id):
        return self.entries_dir / f"{student_id}.json"

    def exists(self, student_id):
        return self._entry_path(student_id).exists()

    def get(self, student_id):
        record = read_json(self._entry_path(student_id), default=None)
        if record is None:
            return None
        return _student_from_record(record)

    def load_all(self):
        if not self.entries_dir.is_dir():
            return []
        students = []
        for path in sorted(self.entries_dir.glob(f"{_ID_PREFIX}*.json")):
            record = read_json(path, default=None)
            if record is not None:
                students.append(_student_from_record(record))
        return students

    def _next_candidate_sequence(self):
        """A pure optimization to reduce the number of failed exclusive-
        create attempts under normal (non-racing) use — correctness of
        id-uniqueness never depends on this scan being accurate or
        even fresh; that guarantee comes entirely from
        atomic_create_json()'s OS-level exclusivity in create()'s retry
        loop below.
        """
        max_sequence = 0
        if self.entries_dir.is_dir():
            for path in self.entries_dir.glob(f"{_ID_PREFIX}*.json"):
                try:
                    sequence = int(path.stem[len(_ID_PREFIX):])
                except ValueError:
                    continue
                max_sequence = max(max_sequence, sequence)
        return max_sequence + 1

    def create(self, name, species=None, status="active"):
        """Always creates a brand-new AcademyStudent with a fresh,
        never-reused student_id — even if `name` matches an existing
        student exactly, this is always a distinct identity. Safe under
        real concurrent callers: see module docstring.
        """
        sequence = self._next_candidate_sequence()
        while True:
            student_id = f"{_ID_PREFIX}{sequence:0{_ID_WIDTH}d}"
            student = AcademyStudent(
                student_id=student_id,
                name=name,
                species=species,
                institution_id="nemerion",
                created_at=_now_iso(),
                status=status,
                historico=(),
            )
            if atomic_create_json(self._entry_path(student_id), _record_from_student(student)):
                return student
            sequence += 1

    def rebuild_index(self):
        """Regenerate LIVRO_DA_ACADEMIA.json purely from entries/ — the
        index never holds information entries/ doesn't already have.
        """
        students = self.load_all()
        por_status = {}
        for s in students:
            por_status[s.status] = por_status.get(s.status, 0) + 1

        index = {
            "nome": "Livro da Academia",
            "total_students": len(students),
            "por_status": por_status,
            "student_ids": [s.student_id for s in students],
            "atualizado_em": _now_iso(),
        }
        atomic_write_json(self.index_path, index)
        return index

    # -- lookup / stats -------------------------------------------------

    def all(self):
        return self.load_all()

    def count(self):
        return len(self.load_all())
