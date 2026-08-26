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
would be dishonest, not defensive.

historico of the enrolled student is never touched here: no
AcademicEvent, no append-only history API exists yet (commit 5) —
create() only ever reads a student's existence, never writes to
AcademyStudent's own record.
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


class StudentNotFoundError(ValueError):
    """Raised by AcademyEnrollmentRegistry.create() when student_id does
    not exist in the given AcademyStudentRegistry — no enrollment is
    ever created for an unknown student.
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
        deduplicates by content: the same (student_id, classroom_id,
        doctrine_id, doctrine_version) combination may be enrolled
        multiple times over history, each a distinct entity. Safe under
        real concurrent callers: see module docstring.
        """
        if not student_registry.exists(student_id):
            raise StudentNotFoundError(f"cannot enroll unknown student_id={student_id!r}")

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
