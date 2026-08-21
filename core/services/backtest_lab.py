"""Backtest Experiment Lab (Commit 20) — the missing link between
already-produced candidates (core.services.candidate_provenance,
Commit 16) and their retrospective measurement (core.services.
candidate_evaluation / candidate_performance, Commits 17-18) against
one already-revealed historical draw.

This module never generates a key, never runs a simulation, never
touches main.py, and never reads a file — it receives candidates the
caller already produced (by any generator, from any source_type) and
already-loaded run manifests, and only ever verifies/measures.

FRONTEIRA A vs. FRONTEIRA B — read this before trusting a result
--------------------------------------------------------------------
There are two structurally different temporal guarantees a backtest
could offer, and this Lab only ever provides one of them:

  Fronteira A — "training/evolution/fitness/Council only ever saw
  history strictly before the target". This module has NO visibility
  into what a generator actually used internally and CANNOT certify
  this. The closest existing mechanism is world/engine/builder.py's
  `visivel = [s for s in hist if s['data'] < data]` cutoff — but it
  has a known, UNFIXED silent-fallback risk:

      if not visivel:
          visivel = hist

  If the configured cutoff date produces an empty window, this
  silently reverts to the FULL history with no cutoff at all — a real
  look-ahead risk. This is registered here as known technical debt,
  prioritized for a future commit; Commit 20 does not touch
  world/engine/builder.py.

  Fronteira B — "the candidate provably existed before the target's
  official draw_datetime was revealed". THIS is what this module
  certifies, structurally, by reusing
  core.services.hero_evaluation.classify_temporal_provenance()
  unchanged. Nothing in this module claims Fronteira A.

Provenance policy (binding — never reworded downstream)
--------------------------------------------------------------------
  verified   — temporally demonstrated: run_id resolves to a manifest
               completed before the target's official draw_datetime.
  legacy     — accepted for exploratory analysis; NEVER temporally
               demonstrated; NEVER promoted to "verified"; NEVER given
               a fabricated run_id or timestamp. Today the entire real
               archive (arquivo_destino.json) is 100% legacy — no
               persisted record carries a run_id yet.
  ineligible — proven to postdate the target. Never produces a
               FrozenCandidate; always a hard ValueError, never a
               silent drop.
  unresolved — a run_id is present but can't be resolved to a usable
               manifest. Excluded by default; included only with the
               explicit `allow_unresolved=True` override (mirroring
               evaluate_heroes.py's --allow-unknown-provenance).

"Independent run" vs. "evolutionary prefix" — historical G20/G25/G100/
G520 reports
--------------------------------------------------------------------
Filtering CandidateKey.generation <= N over a single run_id's
evolutionary_individual candidates yields a PREFIX of one long run's
output — it is NOT equivalent to a run actually configured to stop at
G=N, and it does NOT automatically include Dwarves/Faeries/Melforks/
Treefolks/other external_generator sources, the Council, or Malphas
(all of which have generation=None and are entirely absent from any
generation-based filter). Call this an "evolutionary prefix", never a
"run G20" — reserve "run G20"/"independent run" strictly for
executions that were genuinely configured and completed for that
generation count. This module has no dedicated concept or type for
either case — both are plain caller-side filtering over
CandidateKey/FrozenCandidate tuples.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from core.services.candidate_evaluation import CandidateEvaluation, evaluate_candidates
from core.services.candidate_performance import CandidatePerformanceSummary, summarize_candidate_performance
from core.services.candidate_provenance import CandidateKey
from core.services.hero_evaluation import classify_temporal_provenance


def _require_timezone_aware(dt: datetime, label: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware, got a naive datetime: {dt!r}")


@dataclass(frozen=True)
class BacktestTarget:
    """One already-revealed historical draw, treated as a backtest
    target. Carries the winning key — by construction, only
    evaluate_backtest_candidates() ever receives this dataclass;
    freeze_backtest_candidates() never does (see module docstring).
    """

    draw_id: str
    draw_datetime: datetime
    numeros: tuple[int, ...]
    estrelas: tuple[int, ...]

    def __post_init__(self) -> None:
        _require_timezone_aware(self.draw_datetime, "BacktestTarget.draw_datetime")


@dataclass(frozen=True)
class FrozenCandidate:
    """One CandidateKey already classified against a target's
    draw_datetime and accepted into the frozen set. `provenance` is
    only ever "verified", "legacy" or "unresolved" here — "ineligible"
    can never reach a FrozenCandidate (see freeze_backtest_candidates).

    run_id is read from candidate.metadata.get("run_id") — None for
    legacy candidates (legacy is defined as "no run_id at all"). Never
    fabricated; never inferred from co-occurrence in the same input
    sequence.
    """

    candidate: CandidateKey
    provenance: Literal["verified", "legacy", "unresolved"]
    run_id: str | None


def freeze_backtest_candidates(
    candidates: Sequence[CandidateKey],
    official_draw_datetime: datetime,
    run_manifests_by_id: Mapping[str, Mapping[str, Any]],
    *,
    allow_unresolved: bool = False,
    allow_mixed_runs: bool = False,
) -> tuple[FrozenCandidate, ...]:
    """Classifies each candidate's temporal provenance and freezes the
    surviving subset. Never receives a target's numeros/estrelas —
    only the bare instant needed for classification — so it is
    structurally impossible for the winning key to leak in here.

    Raises ValueError (collecting every offender, not just the first)
    if any candidate is "ineligible" — proven to postdate
    official_draw_datetime. Never silently dropped.

    "unresolved" candidates are excluded unless allow_unresolved=True.

    After filtering, every distinct non-None run_id among the
    survivors is checked: more than one distinct run_id raises
    ValueError unless allow_mixed_runs=True. legacy candidates
    (run_id=None) never contribute to this set — they can neither
    trigger nor prevent a mixed-runs error.

    Never mutates `candidates` or `run_manifests_by_id`. Order of the
    input sequence is preserved.
    """
    _require_timezone_aware(official_draw_datetime, "official_draw_datetime")

    ineligible: list[CandidateKey] = []
    kept: list[FrozenCandidate] = []

    for candidate in candidates:
        provenance = classify_temporal_provenance(
            candidate.metadata, run_manifests_by_id, official_draw_datetime,
        )
        if provenance == "ineligible":
            ineligible.append(candidate)
            continue
        if provenance == "unresolved" and not allow_unresolved:
            continue
        run_id = candidate.metadata.get("run_id")
        kept.append(FrozenCandidate(candidate=candidate, provenance=provenance, run_id=run_id))

    if ineligible:
        offenders = "; ".join(
            f"{c.source_type}/{c.source_name} entity_id={c.entity_id!r} entity_name={c.entity_name!r}"
            for c in ineligible
        )
        raise ValueError(
            f"{len(ineligible)} candidate(s) are ineligible — proven to postdate "
            f"official_draw_datetime={official_draw_datetime.isoformat()!r} — and can never be "
            f"included in a backtest: {offenders}"
        )

    distinct_run_ids = {fc.run_id for fc in kept if fc.run_id is not None}
    if len(distinct_run_ids) > 1 and not allow_mixed_runs:
        raise ValueError(
            f"candidates span {len(distinct_run_ids)} distinct run_ids "
            f"({sorted(distinct_run_ids)}) — pass allow_mixed_runs=True if mixing runs is deliberate"
        )

    return tuple(kept)


def evaluate_backtest_candidates(
    frozen_candidates: Sequence[FrozenCandidate],
    target: BacktestTarget,
) -> tuple[CandidateEvaluation, ...]:
    """The only function in this module that sees the winning key —
    always after freezing. Thin wrapper over
    core.services.candidate_evaluation.evaluate_candidates(); no
    matching logic lives here. Order-preserving, index-aligned with
    `frozen_candidates`.
    """
    return evaluate_candidates(
        tuple(fc.candidate for fc in frozen_candidates),
        target.numeros,
        target.estrelas,
    )


def summarize_backtest(
    frozen_candidates: Sequence[FrozenCandidate],
    evaluations: Sequence[CandidateEvaluation],
    relevant_categories: Collection[str],
) -> CandidatePerformanceSummary:
    """Thin wrapper over core.services.candidate_performance.
    summarize_candidate_performance(); no diversity/category/relevance
    logic lives here. relevant_categories is always explicit — no
    default, never read from [HEROIS] — calling this twice with
    different relevant_categories over the same frozen_candidates/
    evaluations compares relevance definitions without re-freezing or
    re-evaluating anything.
    """
    return summarize_candidate_performance(
        tuple(fc.candidate for fc in frozen_candidates),
        evaluations,
        relevant_categories,
    )
