"""AcademyEnrollmentRegistry — persistent record of the academic
relationship between a student and a classroom/doctrine/version.
Foundation V1, commit 3/5: Nemerion can now register that a persistent
student belongs to a given Turma/Doutrina, without executing any exam
yet. entries/<enrollment_id>.json are the source of truth;
LIVRO_DAS_MATRICULAS.json is a derived index/summary, always
rebuildable from entries/ — never the only copy. Mirrors
library/academy/students/registry.py's entries+derived-index shape
exactly; writes go through core/services/atomic_io.py.

AcademyEnrollment is deliberately narrow: student + institution +
classroom + doctrine + doctrine_version + status + enrolled_at. It
never carries a historical target, seed, Candidate, result, run,
personality, knowledge, book, or skill — those belong to a concrete
test participation (a later commit) or to systems explicitly out of
Foundation V1's scope, never to the enrollment relationship itself.

enrollment_id is sequential and opaque ("NEM-ENR-000001", ...), same
scheme and same concurrency-safety mechanism as
library/academy/students/registry.py's student_id: _next_candidate_
sequence() only suggests a starting point, uniqueness is guaranteed
entirely by core.services.atomic_io.atomic_create_json()'s
os.O_CREAT | os.O_EXCL, and a lost race retries with the next
candidate id. It is never derived from student_id, classroom_id,
doctrine_id, or any other content — the same student can hold many
enrollments over time (different classrooms, repeated enrollments in
the same classroom after a withdrawal, future doctrine versions),
and each one is its own distinct, permanent historical entity;
enrollments are never deduplicated by content.

Referential integrity without circular coupling: create() requires an
AcademyStudentRegistry instance to check student_id.exists() against
before creating an enrollment (StudentNotFoundError otherwise) — a
plain existence check via the already-public API, not a foreign key,
not a shared database, not a second source of truth. The dependency
is one-directional (enrollments -> students) and is passed explicitly
to create() rather than stored on the registry at construction time,
since no other operation here (get/load_all/rebuild_index) needs to
know about students at all. library/academy/students/registry.py
never imports this module — the reverse direction never exists.

institution_id is hardcoded to "nemerion" here, exactly like
AcademyStudentRegistry — this registry is specifically the Academia
Arcana de Nemerion's enrollment registry, not a generic multi-
institution framework; generalizing now would be scope creep ahead of
any actual second institution.

classroom_id/doctrine_id/doctrine_version are persisted as plain,
structurally-validated (non-empty) strings — no ClassroomRegistry, no
DoctrineRegistry, no catalog, no validation against Cátedra de Tyche
or any other module exists yet (Tyche's canonical identity is wired
up starting in commit 4). Pretending a catalog exists before it does
would be dishonest, not defensive. In particular, nothing here
validates that every enrollment in a given (institution_id,
classroom_id) actually shares the same doctrine_id/doctrine_version —
the real bootstrap path (a script driving every enrollment from one
shared core.services.academia.tyche.TYCHE_IDENTITY constant) makes
that true operationally for Cátedra de Tyche today, but there is no
Classroom -> Doctrine consistency check enforced here. Registered
technical debt, not solved in this change — out of scope until a real
ClassroomRegistry exists.

historico of the enrolled student is never touched here: no
AcademicEvent, no append-only history API exists yet (commit 5) —
create() only ever reads a student's existence, never writes to
AcademyStudent's own record.

Classroom capacity (institutional rule, added after commit 5): a
Classroom is considered full at CLASSROOM_ACTIVE_STUDENT_CAPACITY
distinct students with an `active` enrollment. Capacity is scoped to
(institution_id, classroom_id) ONLY — never
(..., doctrine_id, doctrine_version) — so a future doctrine_version
bump (e.g. tyche/v1 -> tyche/v2) can never open five fresh seats in
the same Cátedra; doctrine/version stay pure provenance/methodology on
each AcademyEnrollment, never a second axis of capacity. This is a
deliberate correction from an earlier draft of this rule that scoped
capacity per (classroom_id, doctrine_id, doctrine_version).

This is a MAXIMUM, not a target: create() only ever rejects a 6th
active enrollment (ClassroomFullError) or a student's 2nd simultaneous
active enrollment in the same classroom (AlreadyActivelyEnrolledError)
— it never requires 5 to already exist, since a classroom naturally
grows 0 -> 1 -> ... -> 5 during its own bootstrap. "Exactly 5 = a
complete/operational turma" is an academic-level expectation a caller
(e.g. a pilot campaign) enforces before running exams, never a
create()-level precondition.

Concurrency (explicitly NOT solved here): the capacity check is a
plain load_all()-then-count -> create() sequence, not a transaction.
Two truly concurrent create() calls for the same (institution_id,
classroom_id) when 4 students are already active could theoretically
both observe count=4 and both succeed, producing 6 active students —
the same class of race atomic_create_json() alone cannot prevent,
because the invariant being protected here spans multiple entries,
not one file. This is NOT concurrency-safe and must never be
described as such. Individual AcademyEnrollment persistence is still
fully protected by atomic_create_json() (a single entry can never be
half-written or double-created) — only the AGGREGATE capacity
invariant across entries is single-writer-only for now. Accepted
today because enrollment administration (bootstrap scripts, pilot
setup) is sequential/single-writer by construction; revisit with a
real mechanism (e.g. a claimed-slot-number technique analogous to
student_id/enrollment_id assignment) only if genuine concurrent
enrollment ever becomes a real requirement.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.services.atomic_io import atomic_create_json, atomic_write_json, read_json

BASE = Path("library/academy/enrollments")
_ID_PREFIX = "NEM-ENR-"
_ID_WIDTH = 6
VALID_STATUSES = ("active", "completed", "withdrawn")

CLASSROOM_ACTIVE_STUDENT_CAPACITY = 5
"""Institutional invariant, not a Tyche-specific value: every Classroom
in Academia Arcana de Nemerion holds at most this many distinct
students with an `active` enrollment, scoped to
(institution_id, classroom_id) only — see module docstring. Deliberately
NOT named after any specific classroom (e.g. never TYCHE_MAX_STUDENTS)
so future classrooms share this exact rule without inventing a new
constant per classroom.
"""


class StudentNotFoundError(ValueError):
    """Raised by AcademyEnrollmentRegistry.create() when student_id does
    not exist in the given AcademyStudentRegistry — no enrollment is
    ever created for an unknown student.
    """


class AlreadyActivelyEnrolledError(ValueError):
    """Raised by AcademyEnrollmentRegistry.create() when student_id
    already holds an `active` enrollment in the same
    (institution_id, classroom_id) — a student may never occupy two of
    a classroom's seats at once, even under a different doctrine_id/
    doctrine_version. A student MAY hold unlimited historical
    completed/withdrawn enrollments in the same classroom; only a
    second simultaneous `active` one is rejected.
    """


class ClassroomFullError(ValueError):
    """Raised by AcademyEnrollmentRegistry.create() when the target
    (institution_id, classroom_id) already has
    CLASSROOM_ACTIVE_STUDENT_CAPACITY distinct students with an
    `active` enrollment — no 6th seat is ever created. Enrollments
    created directly with status="completed"/"withdrawn" never count
    toward this capacity.
    """


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _require_non_empty_slug(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string, got {value!r}")


@dataclass(frozen=True)
class AcademyEnrollment:
    """institution_id is always "nemerion" in Foundation V1 — see
    module docstring. classroom_id/doctrine_id/doctrine_version are
    only structurally validated (non-empty strings); no catalog exists
    yet to validate them further.
    """

    enrollment_id: str
    student_id: str
    institution_id: str
    classroom_id: str
    doctrine_id: str
    doctrine_version: str
    status: str
    enrolled_at: str

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status {self.status!r} — must be one of {VALID_STATUSES}")
        _require_non_empty_slug(self.student_id, "student_id")
        _require_non_empty_slug(self.classroom_id, "classroom_id")
        _require_non_empty_slug(self.doctrine_id, "doctrine_id")
        _require_non_empty_slug(self.doctrine_version, "doctrine_version")


def _record_from_enrollment(enrollment: AcademyEnrollment) -> dict:
    return {
        "enrollment_id": enrollment.enrollment_id,
        "student_id": enrollment.student_id,
        "institution_id": enrollment.institution_id,
        "classroom_id": enrollment.classroom_id,
        "doctrine_id": enrollment.doctrine_id,
        "doctrine_version": enrollment.doctrine_version,
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at,
    }


def _enrollment_from_record(record: dict) -> AcademyEnrollment:
    return AcademyEnrollment(
        enrollment_id=record["enrollment_id"],
        student_id=record["student_id"],
        institution_id=record["institution_id"],
        classroom_id=record["classroom_id"],
        doctrine_id=record["doctrine_id"],
        doctrine_version=record["doctrine_version"],
        status=record["status"],
        enrolled_at=record["enrolled_at"],
    )


class AcademyEnrollmentRegistry:
    def __init__(self, base=None):
        self.base = Path(base) if base is not None else BASE
        self.entries_dir = self.base / "entries"
        self.index_path = self.base / "LIVRO_DAS_MATRICULAS.json"

    # -- persistence --------------------------------------------------

    def _entry_path(self, enrollment_id):
        return self.entries_dir / f"{enrollment_id}.json"

    def exists(self, enrollment_id):
        return self._entry_path(enrollment_id).exists()

    def get(self, enrollment_id):
        record = read_json(self._entry_path(enrollment_id), default=None)
        if record is None:
            return None
        return _enrollment_from_record(record)

    def load_all(self):
        if not self.entries_dir.is_dir():
            return []
        enrollments = []
        for path in sorted(self.entries_dir.glob(f"{_ID_PREFIX}*.json")):
            record = read_json(path, default=None)
            if record is not None:
                enrollments.append(_enrollment_from_record(record))
        return enrollments

    def _next_candidate_sequence(self):
        """Same pure optimization as
        AcademyStudentRegistry._next_candidate_sequence() — correctness
        of id-uniqueness never depends on this scan; it comes entirely
        from atomic_create_json()'s OS-level exclusivity in create()'s
        retry loop below.
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

    def create(self, student_id, classroom_id, doctrine_id, doctrine_version, student_registry, status="active"):
        """Creates a brand-new AcademyEnrollment with a fresh, never-
        reused enrollment_id. Requires student_registry (an
        AcademyStudentRegistry) so student_id can be checked for
        existence first — raises StudentNotFoundError if the student is
        unknown to it; no enrollment is created in that case. Never
        deduplicates by content in general: the same (student_id,
        classroom_id, doctrine_id, doctrine_version) combination may be
        enrolled multiple times over history (e.g. after a withdrawal),
        each a distinct entity.

        When status == "active" only, two classroom-capacity checks run
        first (see module docstring for the exact rule and its
        deliberately-NOT-concurrency-safe caveat):
        AlreadyActivelyEnrolledError if student_id already holds an
        active enrollment in this (institution_id, classroom_id);
        ClassroomFullError if CLASSROOM_ACTIVE_STUDENT_CAPACITY distinct
        students already hold one. Neither check applies when creating
        an enrollment directly as "completed"/"withdrawn" — those never
        occupy a seat.
        """
        if not student_registry.exists(student_id):
            raise StudentNotFoundError(f"cannot enroll unknown student_id={student_id!r}")

        if status == "active":
            active_here = [
                e for e in self.load_all()
                if e.status == "active" and e.institution_id == "nemerion" and e.classroom_id == classroom_id
            ]
            if any(e.student_id == student_id for e in active_here):
                raise AlreadyActivelyEnrolledError(
                    f"student_id={student_id!r} already holds an active enrollment in classroom_id={classroom_id!r}"
                )
            active_student_ids = {e.student_id for e in active_here}
            if len(active_student_ids) >= CLASSROOM_ACTIVE_STUDENT_CAPACITY:
                raise ClassroomFullError(
                    f"classroom_id={classroom_id!r} already has {len(active_student_ids)} active students "
                    f"(capacity={CLASSROOM_ACTIVE_STUDENT_CAPACITY})"
                )

        sequence = self._next_candidate_sequence()
        while True:
            enrollment_id = f"{_ID_PREFIX}{sequence:0{_ID_WIDTH}d}"
            enrollment = AcademyEnrollment(
                enrollment_id=enrollment_id,
                student_id=student_id,
                institution_id="nemerion",
                classroom_id=classroom_id,
                doctrine_id=doctrine_id,
                doctrine_version=doctrine_version,
                status=status,
                enrolled_at=_now_iso(),
            )
            if atomic_create_json(self._entry_path(enrollment_id), _record_from_enrollment(enrollment)):
                return enrollment
            sequence += 1

    def rebuild_index(self):
        """Regenerate LIVRO_DAS_MATRICULAS.json purely from entries/ —
        never mixed with library/academy/students/'s own
        LIVRO_DA_ACADEMIA.json, a separate projection over separate
        source-of-truth entries.
        """
        enrollments = self.load_all()
        por_status = {}
        por_classroom = {}
        for e in enrollments:
            por_status[e.status] = por_status.get(e.status, 0) + 1
            por_classroom[e.classroom_id] = por_classroom.get(e.classroom_id, 0) + 1

        index = {
            "nome": "Livro das Matrículas",
            "total_enrollments": len(enrollments),
            "por_status": por_status,
            "por_classroom": por_classroom,
            "enrollment_ids": [e.enrollment_id for e in enrollments],
            "atualizado_em": _now_iso(),
        }
        atomic_write_json(self.index_path, index)
        return index

    # -- lookup / stats -------------------------------------------------

    def all(self):
        return self.load_all()

    def count(self):
        return len(self.load_all())
