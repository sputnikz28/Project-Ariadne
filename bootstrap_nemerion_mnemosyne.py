"""Bootstrap: Primeira Turma da Cátedra de Mnemosyne — Memória da
Frequência.

    python bootstrap_nemerion_mnemosyne.py

Administrative, one-time script: creates the five founding
AcademyStudents of Academia Arcana de Nemerion's Segunda Cátedra and
enrolls each of them, active, in Cátedra de Mnemosyne — Memória da
Frequência (mnemosyne/v1). Uses only the public
AcademyStudentRegistry/AcademyEnrollmentRegistry APIs — no manual
JSON, no manually-assigned student_id/enrollment_id, no AcademicEvent
(that only ever happens after a real exam, via core.services.academia.
academic_memory.record_academic_result()). Never reuses Cátedra de
Tyche's students — each Classroom has its own five.

Idempotency (a script-level convention, NOT a new registry guarantee —
same exact precedent as bootstrap_nemerion_tyche.py):
AcademyStudentRegistry.create() deliberately never deduplicates by
name — two real students may legitimately share a name. This script
narrows that down deliberately, ONLY for this fixed, closed list of
five founder names, exclusively for this one bootstrap:

  - FRESH: none of the five founder names exist yet AND there are zero
    active Cátedra de Mnemosyne enrollments at all -> create all five
    Students + five Enrollments.
  - ALREADY DONE: exactly the five founder names exist, each with
    exactly one active Mnemosyne enrollment, and the five active
    Mnemosyne enrollments belong to exactly those five students (no
    more, no fewer) -> no-op, reports what already exists, mutates
    nothing.
  - ANYTHING ELSE (a founder name missing while others exist, a
    founder name duplicated, a founder without an active Mnemosyne
    enrollment, an active Mnemosyne enrollment not belonging to a
    founder, more or fewer than five active Mnemosyne enrollments)
    -> stops with a clear diagnostic error and creates nothing. Never
    guesses, never silently repairs.

Classroom capacity (library/academy/enrollments/registry.py:
CLASSROOM_ACTIVE_STUDENT_CAPACITY) is scoped per (institution_id,
classroom_id) — Cátedra de Tyche's five active students never count
toward Cátedra de Mnemosyne's capacity, and vice versa; this script
relies on that already-proven independence, never re-implements it.

Nothing runs on import — only inside main().
"""
from __future__ import annotations

import sys

from core.services.academia.mnemosyne import MNEMOSYNE_IDENTITY
from library.academy.enrollments.registry import AcademyEnrollmentRegistry
from library.academy.students.registry import AcademyStudentRegistry

FOUNDER_NAMES = (
    "Elowen Draycott",
    "Bastian Quill",
    "Wren Callahan",
    "Seraphine Kade",
    "Osric Fenwick",
)


class BootstrapAbort(RuntimeError):
    """Raised when the persisted state doesn't cleanly match either the
    FRESH or ALREADY DONE case — never silently repaired.
    """


def _is_mnemosyne_enrollment(enrollment) -> bool:
    return (
        enrollment.status == "active"
        and enrollment.institution_id == MNEMOSYNE_IDENTITY.institution_id
        and enrollment.classroom_id == MNEMOSYNE_IDENTITY.classroom_id
        and enrollment.doctrine_id == MNEMOSYNE_IDENTITY.doctrine_id
        and enrollment.doctrine_version == MNEMOSYNE_IDENTITY.doctrine_version
    )


def inspect_current_state(student_registry, enrollment_registry):
    """Returns (founders_by_name, active_mnemosyne_enrollments) — pure
    read, no mutation. founders_by_name maps a founder name to the
    AcademyStudent found for it; a name absent from persisted students
    is simply absent from the dict (never fabricated).

    Raises BootstrapAbort if a founder name appears more than once
    among persisted students — an ambiguous state this script refuses
    to guess through.
    """
    all_students = student_registry.load_all()
    founders_by_name = {}
    for student in all_students:
        if student.name in FOUNDER_NAMES:
            if student.name in founders_by_name:
                raise BootstrapAbort(
                    f"founder name {student.name!r} matches more than one persisted AcademyStudent "
                    f"({founders_by_name[student.name].student_id} and {student.student_id}) — ambiguous, refusing to guess"
                )
            founders_by_name[student.name] = student

    active_mnemosyne_enrollments = tuple(
        e for e in enrollment_registry.load_all() if _is_mnemosyne_enrollment(e)
    )
    return founders_by_name, active_mnemosyne_enrollments


def classify_state(founders_by_name, active_mnemosyne_enrollments):
    """Returns "fresh", "already_done", or raises BootstrapAbort for
    any other persisted state. See module docstring for the exact
    three-way contract.
    """
    if not founders_by_name and not active_mnemosyne_enrollments:
        return "fresh"

    if len(founders_by_name) == len(FOUNDER_NAMES) and len(active_mnemosyne_enrollments) == len(FOUNDER_NAMES):
        founder_ids = {s.student_id for s in founders_by_name.values()}
        enrolled_ids = {e.student_id for e in active_mnemosyne_enrollments}
        if founder_ids == enrolled_ids:
            return "already_done"

    missing = [name for name in FOUNDER_NAMES if name not in founders_by_name]
    founder_ids = {s.student_id for s in founders_by_name.values()}
    enrolled_ids = {e.student_id for e in active_mnemosyne_enrollments}
    unexplained_enrollments = enrolled_ids - founder_ids
    founders_without_enrollment = founder_ids - enrolled_ids
    raise BootstrapAbort(
        "persisted state is neither FRESH nor ALREADY DONE — refusing to create or repair anything.\n"
        f"  founder names found: {sorted(founders_by_name)} (missing: {missing})\n"
        f"  active Cátedra de Mnemosyne enrollments: {len(active_mnemosyne_enrollments)} (expected 0 or {len(FOUNDER_NAMES)})\n"
        f"  active-Mnemosyne student_ids not matching any founder: {sorted(unexplained_enrollments) or 'none'}\n"
        f"  founder student_ids without an active Mnemosyne enrollment: {sorted(founders_without_enrollment) or 'none'}"
    )


def create_founders(student_registry, enrollment_registry):
    """Only ever called in the FRESH case. Creates all five Students
    then all five Enrollments, via the public APIs only. Returns the
    list of (student, enrollment) pairs in FOUNDER_NAMES order.
    """
    created = []
    for name in FOUNDER_NAMES:
        student = student_registry.create(name=name, species=None, status="active")
        enrollment = enrollment_registry.create(
            student_id=student.student_id,
            classroom_id=MNEMOSYNE_IDENTITY.classroom_id,
            doctrine_id=MNEMOSYNE_IDENTITY.doctrine_id,
            doctrine_version=MNEMOSYNE_IDENTITY.doctrine_version,
            student_registry=student_registry,
            status="active",
        )
        created.append((student, enrollment))
    return created


def main() -> int:
    student_registry = AcademyStudentRegistry()
    enrollment_registry = AcademyEnrollmentRegistry()

    founders_by_name, active_mnemosyne_enrollments = inspect_current_state(student_registry, enrollment_registry)
    try:
        state = classify_state(founders_by_name, active_mnemosyne_enrollments)
    except BootstrapAbort as exc:
        print("ABORT — bootstrap did not create or modify anything.")
        print(str(exc))
        return 1

    if state == "already_done":
        print("Primeira Turma da Cátedra de Mnemosyne já existe — nada foi criado (idempotente).")
        for name in FOUNDER_NAMES:
            student = founders_by_name[name]
            enrollment = next(e for e in active_mnemosyne_enrollments if e.student_id == student.student_id)
            print(f"  {student.student_id} | {student.name} | species={student.species} | {enrollment.enrollment_id}")
        return 0

    print("Estado FRESH — a criar os cinco fundadores da Cátedra de Mnemosyne.")
    created = create_founders(student_registry, enrollment_registry)
    for student, enrollment in created:
        print(f"  {student.student_id} | {student.name} | species={student.species} | {enrollment.enrollment_id}")

    student_registry.rebuild_index()
    enrollment_registry.rebuild_index()
    print("Índices reconstruídos: LIVRO_DA_ACADEMIA.json, LIVRO_DAS_MATRICULAS.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
