"""Academia Arcana de Nemerion — Foundation V1, commit 5/5. The one
place a FINISHED, already-scientifically-determined experience gets
turned into academic memory (AcademicEvent). Deliberately NOT called
by anything in core.services.backtest_campaign.run_system_campaign()
or core.services.backtest_generators._run_academia() — it is a small,
separate, optional post-run step, invoked by whatever orchestrates a
real Academia campaign (a script, not the generic Campaign Runner
core), exactly as approved: "experiência científica primeiro; memória
académica depois."

Source-of-truth boundary: a GeneratorRunResult's own candidates/
evaluations/run_id/target/seed ARE the experimental source of truth —
already returned to the caller, already (optionally) manifested via
core.services.run_manifest, completely unaffected by anything in this
module. record_academic_result() only ever READS a GeneratorRunResult
that already exists; it never re-runs, re-evaluates, or persists a
second copy of the Candidate/evaluation anywhere. What it writes
(candidate_summary, category) are small, explicitly denormalized
snapshots for convenience — never the authority, never a substitute
for the real evaluation.

Failure isolation: if appending an AcademicEvent fails for one
candidate, this never invalidates or rolls back anything scientific —
result.candidates/evaluations/run_id are plain, already-returned
values; nothing here can un-return them. Each candidate's outcome is
recorded independently (AcademicRecordingOutcome) — one failure never
blocks recording for other students in the same run. A failure can
always be retried later: this whole module is idempotent by
construction (see event_id below), so reprocessing the exact same
GeneratorRunResult a second time — whether because the first attempt
partially failed or purely as a safety re-run — never duplicates an
already-recorded event.

event_id composition: SHA-256 over (run_id, student_id, enrollment_id)
— never over the candidate's numeros/estrelas/category, which can
legitimately coincide across two genuinely different experiences.
run_id alone is not sufficient: resolve_eligible_participants()
(core.services.academia.common) iterates ENROLLMENTS, not deduplicated
students — core.services.academia.enrollments' own commit 3 contract
explicitly allows a student to hold more than one simultaneous active
enrollment in the same classroom/doctrine/version (no uniqueness rule
was introduced), so the SAME student_id can legitimately appear twice
in one _run_academia() call's participants, each via a different
enrollment_id, each a distinct, real academic participation. Including
enrollment_id is therefore not preventive over-composition — it is the
minimum needed for logical uniqueness, confirmed by reading
resolve_eligible_participants()'s actual loop, not assumed. Doctrine/
version are not included: Foundation V1's Cátedra de Tyche is the only
classroom, so every candidate in a given run already shares the same
doctrine/version — adding them would not disambiguate anything today.

A genuinely new academic attempt (not a technical retry/replay of the
same finished run) always gets processed via a FRESH
core.services.backtest_generators._run_academia() call, which always
calls core.services.run_manifest.start_run() again — run_ids are never
reused (see run_manifest.py's own collision-avoidance) — so a
deliberate new attempt automatically produces a new event_id, with
zero special-casing needed here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from core.services.backtest_campaign import GeneratorRunResult
from library.academy.students.registry import AcademicEvent, AcademyStudentRegistry, StudentNotFoundError


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _derive_event_id(run_id: str, student_id: str, enrollment_id: str) -> str:
    payload = "|".join(["academia_event", run_id, student_id, enrollment_id])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"EVT-{digest[:32]}"


@dataclass(frozen=True)
class AcademicRecordingOutcome:
    """One candidate's academic-recording outcome. entity_id is None
    only when the candidate itself had no entity_id at all (not
    attributable to a student — see module docstring's failure
    isolation). error is None on success; created distinguishes a
    fresh write (True) from an idempotent no-op (False, event already
    existed) — both are successes, never conflated with error!=None.
    """

    entity_id: str | None
    event_id: str | None
    created: bool
    error: str | None


def record_academic_result(result: GeneratorRunResult, students_root=None) -> tuple[AcademicRecordingOutcome, ...]:
    """Turns one already-finished GeneratorRunResult from the
    "academia" system into academic memory — one AcademicEvent per
    candidate that carries a real entity_id, a real, existing student,
    and a real enrollment_id in its metadata. Never fabricates a
    Student or an Enrollment for a candidate missing either — that
    candidate's outcome carries an explicit `error` instead, and
    recording continues for every other candidate in `result`.

    result.candidates[i] pairs with result.evaluations[i] positionally
    — the same order core.services.candidate_evaluation.
    evaluate_candidates() always preserves (confirmed directly in that
    module, never assumed) — no candidate id is invented here to
    achieve this pairing.

    Raises ValueError immediately if result.system != "academia" — a
    caller-usage error (wrong result passed in), not a per-candidate
    runtime condition.
    """
    if result.system != "academia":
        raise ValueError(f"record_academic_result() only accepts system='academia' results, got {result.system!r}")

    student_registry = AcademyStudentRegistry(base=students_root)
    occurred_at = _now_iso()

    outcomes = []
    for simulated, evaluation in zip(result.candidates, result.evaluations):
        candidate = simulated.candidate
        entity_id = candidate.entity_id

        if entity_id is None:
            outcomes.append(AcademicRecordingOutcome(
                entity_id=None, event_id=None, created=False,
                error="candidate has no entity_id — not attributable to a student",
            ))
            continue

        enrollment_id = candidate.metadata.get("enrollment_id")
        if not enrollment_id:
            outcomes.append(AcademicRecordingOutcome(
                entity_id=entity_id, event_id=None, created=False,
                error="candidate metadata missing enrollment_id",
            ))
            continue

        event_id = _derive_event_id(result.run_id, entity_id, enrollment_id)
        extra = {
            "enrollment_id": enrollment_id,
            "classroom_id": candidate.metadata.get("classroom_id"),
            "doctrine_id": candidate.metadata.get("doctrine_id"),
            "doctrine_version": candidate.metadata.get("doctrine_version"),
            "historical_target": result.target.draw_id,
            "generator_seed": result.seed,
            "run_id": result.run_id,
            "candidate_summary": {"numeros": list(candidate.numeros), "estrelas": list(candidate.estrelas)},
            "category": evaluation.category,
        }

        try:
            event: AcademicEvent
            event, created = student_registry.append_event(
                student_id=entity_id, event_type="test_participation",
                occurred_at=occurred_at, event_id=event_id, extra=extra,
            )
        except StudentNotFoundError as exc:
            outcomes.append(AcademicRecordingOutcome(
                entity_id=entity_id, event_id=event_id, created=False, error=str(exc),
            ))
            continue

        outcomes.append(AcademicRecordingOutcome(
            entity_id=entity_id, event_id=event.event_id, created=created, error=None,
        ))

    return tuple(outcomes)
