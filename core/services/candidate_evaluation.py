"""Candidate Evaluation (Commit 17) — pure, deterministic measurement of
one or more CandidateKey (Commit 16) against an explicitly-supplied
target key. Purely retrospective/experimental: never participates in
generation, fitness, the Council, or key selection, and never has any
way to look ahead.

This module has no concept of a "concurso"/draw, no dates, no dataset
access. It receives a frozen CandidateKey and a target the caller
already resolved — that is what makes look-ahead structurally
impossible here: the target can only ever be exactly what the caller
explicitly passed in. Temporal provenance (whether a prediction could
honestly have existed before the target draw) remains the exclusive
responsibility of core/services/hero_evaluation.py's
classify_temporal_provenance()/evaluate_heroes.py — not integrated,
not duplicated, not called from here.

`category` here is purely descriptive of match counts (e.g. "0+0",
"1+0", "0+2", "2+0" are all valid results) — it is NOT a Hero
recognition/promotion category and has no relation to
[HEROIS]/[HEROIS_TIERS]; nothing in this module reads that config.

The matched-values-and-category formula duplicates (deliberately, in
3 lines) the same computation core/services/hero_evaluation.py's
matched_values()/category_for() already perform for the Heroes domain.
That module is not reused here on purpose: its public entry point
(evaluate_record()) is inseparable from Hero-specific concerns
(HEROIS config-gated qualification/tier, dedup hashing, temporal
provenance) that must never leak into a domain-agnostic evaluator, and
its private helpers are not imported across module boundaries. See
CLAUDE.md's Known Issues for this documented, accepted duplication.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from core.services.candidate_provenance import CandidateKey


@dataclass(frozen=True)
class CandidateEvaluation:
    matched_numbers: tuple[int, ...]
    matched_stars: tuple[int, ...]
    matched_number_count: int
    matched_star_count: int
    category: str


def _matched_values(candidate_values: Sequence[int], target_values: Sequence[int]) -> tuple[int, ...]:
    """Sorted, de-duplicated intersection — numeros and estrelas are
    always compared through this same helper but never against each
    other; the caller (evaluate_candidate) keeps the two calls separate.
    """
    return tuple(sorted(set(candidate_values) & set(target_values)))


def evaluate_candidate(
    candidate: CandidateKey,
    target_numeros: Sequence[int],
    target_estrelas: Sequence[int],
) -> CandidateEvaluation:
    """Pure — no I/O, no random, no datetime, no dataset access. Never
    mutates `candidate` or the target sequences.

    matched_numbers/matched_stars: ordered, de-duplicated intersection,
    numeros and estrelas always compared separately, never mixed.
    category: f"{matched_number_count}+{matched_star_count}" — every
    combination from "0+0" to "5+2" is a valid, unrestricted result;
    this is not gated by [HEROIS].categorias.
    """
    matched_numbers = _matched_values(candidate.numeros, target_numeros)
    matched_stars = _matched_values(candidate.estrelas, target_estrelas)
    return CandidateEvaluation(
        matched_numbers=matched_numbers,
        matched_stars=matched_stars,
        matched_number_count=len(matched_numbers),
        matched_star_count=len(matched_stars),
        category=f"{len(matched_numbers)}+{len(matched_stars)}",
    )


def evaluate_candidates(
    candidates: Sequence[CandidateKey],
    target_numeros: Sequence[int],
    target_estrelas: Sequence[int],
) -> tuple[CandidateEvaluation, ...]:
    """Maps evaluate_candidate() over `candidates`, preserving their
    given order exactly — no aggregation, no ranking, no sorting by
    match count or any other criterion.
    """
    return tuple(evaluate_candidate(c, target_numeros, target_estrelas) for c in candidates)
