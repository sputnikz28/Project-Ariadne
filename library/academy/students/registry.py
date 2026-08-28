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

historico (commit 5/5): AcademicEvent is append-only, permanent memory
of a finished experience, stored as one exclusively-created file per
event under events/<student_id>/<event_id>.json — never embedded in
entries/<student_id>.json's own JSON blob. This is a deliberate
persistence-internals change from commit 2's original "historico:
list(...) embedded in the entry" shape (chosen after the user
identified a real lost-update race: entries/<student_id>.json has no
compare-and-swap, so a naive read-modify-write append could silently
lose a concurrent event). entries/<student_id>.json still WRITES a
vestigial "historico": [] field at creation, for shape stability with
already-approved commit 2/3 tests, but it is never read back — get()/
load_all() always source AcademyStudent.historico from events/, never
from that field. No AcademicEvent is ever written to both places.

AcademyStudent's own identity fields (student_id/name/species/
institution_id/created_at/status) are untouched by any of this:
append_event() never opens, reads, or writes entries/<student_id>.json
at all — it is structurally incapable of altering student_id or
created_at, or of rewriting/removing a past event, because past
events are immutable already-created files it never revisits.

Concurrent append safety: exactly the same
core.services.atomic_io.atomic_create_json() exclusivity already
proven for create() (student_id) and
library.academy.enrollments.registry.AcademyEnrollmentRegistry.create()
(enrollment_id) — applied one level deeper, to individual event files
instead of individual student/enrollment files. Two concurrent
append_event() calls with different event_ids just create two files,
no race possible. Two concurrent calls with the SAME event_id: exactly
one atomic_create_json() wins; the loser detects "already exists" and
returns the EXISTING content with created=False — the same
(record, created) idempotent-create shape already established by
library.heroes.registry.HeroRegistry.register(). Never
atomic_write_json() for an event — that function unconditionally
overwrites, which would violate the "never rewrite a past event"
guarantee.

event_id is supplied by the caller (deterministically derived, never
random, never content-derived — see
core.services.academia.academic_memory.record_academic_result()) so
the SAME finished experience reprocessed always resolves to the SAME
event_id and therefore never duplicates; a genuinely new academic
attempt gets a fresh run_id upstream and therefore a fresh event_id.

Ordering: get()/load_all() project each student's historico sorted by
(occurred_at, event_id) — occurred_at is Academia-time (when Nemerion
registered the event), never derived from a historical_target (which
lives separately inside the event's own `extra`). event_id is only a
deterministic tie-break for the rare case of two events sharing the
same occurred_at second; this Foundation does not attempt to solve
true cross-process causal ordering under real concurrency.
"""
from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.services.atomic_io import atomic_create_json, atomic_write_json, read_json

BASE = Path("library/academy/students")
_ID_PREFIX = "NEM-STU-"
_ID_WIDTH = 6
VALID_STATUSES = ("active", "inactive", "graduated", "expelled")


class StudentNotFoundError(KeyError):
    """Raised by AcademyStudentRegistry.append_event() when student_id
    does not exist — no AcademicEvent is ever created for an unknown
    student, and no Student is ever fabricated to make one fit.
    """


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AcademyStudent:
    """species=None is a legitimate, honest "not yet defined" — never
    fabricated. institution_id is always "nemerion" in Foundation V1
    (the only institution that exists); the field exists so a student
    record is self-describing without relying on which registry loaded
    it. historico is a tuple of AcademicEvent, projected at read time
    from events/<student_id>/ — see module docstring. Always empty for
    a student nobody has ever called append_event() for.
    """

    student_id: str
    name: str
    species: str | None
    institution_id: str
    created_at: str
    status: str
    historico: tuple["AcademicEvent", ...] = ()

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status {self.status!r} — must be one of {VALID_STATUSES}")


@dataclass(frozen=True)
class AcademicEvent:
    """One permanent, immutable unit of academic memory. extra carries
    event_type-specific fields — for "test_participation" (the only
    event_type this commit ever writes), see
    core.services.academia.academic_memory.record_academic_result()'s
    exact shape. Mirrors artifact_schema.py's EventoHistoria (evento,
    extra) shape, the closest existing precedent for a generic
    "this happened, here are the details" event.

    Once successfully created via AcademyStudentRegistry.append_event(),
    an AcademicEvent is never edited, replaced, deleted, or
    reordered — there is no API in this module for any of those.
    """

    event_id: str
    event_type: str
    occurred_at: str
    extra: Mapping[str, Any]


def _record_from_student(student: AcademyStudent) -> dict:
    return {
        "student_id": student.student_id,
        "name": student.name,
        "species": student.species,
        "institution_id": student.institution_id,
        "created_at": student.created_at,
        "status": student.status,
        "historico": [],  # vestigial — never read back, see module docstring
    }


def _student_from_record(record: dict, historico: tuple[AcademicEvent, ...] = ()) -> AcademyStudent:
    return AcademyStudent(
        student_id=record["student_id"],
        name=record["name"],
        species=record["species"],
        institution_id=record["institution_id"],
        created_at=record["created_at"],
        status=record["status"],
        historico=historico,
    )


def _record_from_event(event: AcademicEvent) -> dict:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at,
        "extra": dict(event.extra),
    }


def _event_from_record(record: dict) -> AcademicEvent:
    return AcademicEvent(
        event_id=record["event_id"],
        event_type=record["event_type"],
        occurred_at=record["occurred_at"],
        extra=MappingProxyType(dict(record.get("extra", {}))),
    )


def _read_json_until_valid(path, attempts=50, delay=0.001):
    """core.services.atomic_io.atomic_create_json() makes `path` exist
    (via os.open(O_CREAT|O_EXCL)) BEFORE its JSON content is fully
    written and fsynced — a losing caller's immediate read_json() can
    therefore race a still-in-progress winner and see an empty or
    partial file (default=None). This is not a gap in
    atomic_create_json()'s exclusivity guarantee (still exactly one
    winner, always) — it is a real TOCTOU window in the read-after-lose
    path specifically, only exercised by append_event()'s idempotent
    "return the existing event" behaviour (create()'s own retry loops
    in this module and library.academy.enrollments.registry never read
    a losing attempt's content — they just try the next candidate id).

    Retries a bounded number of times with a short sleep rather than
    introducing OS-level file locking — the winner's write is a few
    bytes plus one fsync, observed to complete near-instantly; 50
    attempts at 1ms is generous. Raises RuntimeError if the file never
    becomes valid JSON in that window — a genuine, unexpected failure,
    not something to paper over with a fabricated return value.
    """
    for _ in range(attempts):
        content = read_json(path, default=None)
        if content is not None:
            return content
        time.sleep(delay)
    raise RuntimeError(f"{path} exists but never became valid JSON after losing the create race")


class AcademyStudentRegistry:
    def __init__(self, base=None):
        self.base = Path(base) if base is not None else BASE
        self.entries_dir = self.base / "entries"
        self.events_dir = self.base / "events"
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
        return _student_from_record(record, self._load_events(student_id))

    def load_all(self):
        if not self.entries_dir.is_dir():
            return []
        students = []
        for path in sorted(self.entries_dir.glob(f"{_ID_PREFIX}*.json")):
            record = read_json(path, default=None)
            if record is not None:
                students.append(_student_from_record(record, self._load_events(record["student_id"])))
        return students

    # -- academic memory (AcademicEvent) ---------------------------------

    def _event_path(self, student_id, event_id):
        return self.events_dir / student_id / f"{event_id}.json"

    def _load_events(self, student_id) -> tuple[AcademicEvent, ...]:
        student_events_dir = self.events_dir / student_id
        if not student_events_dir.is_dir():
            return ()
        events = []
        for path in sorted(student_events_dir.glob("*.json")):
            record = read_json(path, default=None)
            if record is not None:
                events.append(_event_from_record(record))
        return tuple(sorted(events, key=lambda e: (e.occurred_at, e.event_id)))

    def append_event(self, student_id, event_type, occurred_at, event_id, extra) -> tuple[AcademicEvent, bool]:
        """Creates one permanent AcademicEvent for student_id, keyed by
        the caller-supplied event_id. Returns (event, created) —
        created=False means an event with this exact event_id already
        existed and this call was a no-op (idempotent reprocessing,
        never a duplicate, never inspects whether the existing content
        matches what was just requested — mirrors
        core.services.atomic_io.atomic_create_json()'s own semantics).

        Raises StudentNotFoundError if student_id is unknown — never
        fabricates a Student. Never opens, reads, or writes
        entries/<student_id>.json — see module docstring for why this
        makes rewriting student_id/created_at/a past event structurally
        impossible from here, not just a convention.
        """
        if not self.exists(student_id):
            raise StudentNotFoundError(f"cannot append an academic event for unknown student_id={student_id!r}")

        event = AcademicEvent(
            event_id=event_id, event_type=event_type, occurred_at=occurred_at, extra=MappingProxyType(dict(extra)),
        )
        path = self._event_path(student_id, event_id)
        if atomic_create_json(path, _record_from_event(event)):
            return event, True
        existing = _read_json_until_valid(path)
        return _event_from_record(existing), False

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
