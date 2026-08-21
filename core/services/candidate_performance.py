"""Candidate Performance Analysis (Commit 18) — pure aggregation of
already-produced CandidateKey (Commit 16) + CandidateEvaluation
(Commit 17) pairs into a single summary. Never generates, selects, or
modifies a candidate; never ranks; never scores; never reads
[HEROIS]/[HEROIS_TIERS]; never reads a dataset or a winning draw
itself. Receives only what an honest caller already produced,
downstream of the mandatory temporal boundary already established in
Commit 17: histórico -> gerar/evoluir -> congelar candidatos -> revelar
resultado -> CandidateEvaluation -> this module.

This module does not group by source_name/source_type/race/generation.
A caller who wants "performance by X" filters the zipped
(candidates, evaluations) pairs themselves and calls
summarize_candidate_performance() once per group — deliberately, so
this module never has to invent what an absent generation/race means
for a group label (see CLAUDE.md Commit 18 audit: generation=None must
never be treated as a real generation, race=None must never become
"Unknown", and "Cronomante" the evolutionary race is a different
concept from "cronomante" the external faction's source_name).

category is accepted exactly as CandidateEvaluation.category already
computed it (Commit 17) — this module never recomputes, re-derives, or
validates a category string; it only counts occurrences.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_provenance import CandidateKey

# The 18 possible category strings given a 5-numeros/2-estrelas key —
# matched_number_count in 0..5, matched_star_count in 0..2. A fixed
# combinatorial fact of the game, not read from [HEROIS] (which only
# lists a configured subset) and not derived from any observed data.
_ALL_CATEGORIES: tuple[str, ...] = tuple(f"{n}+{e}" for n in range(6) for e in range(3))


@dataclass(frozen=True)
class CandidatePerformanceSummary:
    total_candidates: int
    unique_full_keys: int
    unique_number_sets: int
    duplicate_count: int
    full_key_diversity_rate: float
    number_set_diversity_rate: float
    category_counts: Mapping[str, int]
    relevant_count: int
    relevant_rate: float


def summarize_candidate_performance(
    candidates: Sequence[CandidateKey],
    evaluations: Sequence[CandidateEvaluation],
    relevant_categories: Collection[str],
) -> CandidatePerformanceSummary:
    """candidates/evaluations: already produced by an honest caller,
    paired by position exactly like evaluate_candidates() preserves
    order — evaluations[i] must describe candidates[i]. Raises
    ValueError if the two sequences have different lengths (a caller
    bug, not a data gap).

    relevant_categories: which CandidateEvaluation.category strings
    count as "relevant" — no default, never read from [HEROIS]; the
    caller decides every time, explicitly.

    Diversity is computed on frozenset(candidate.numeros)/
    frozenset(candidate.estrelas) purely as an internal deduplication
    key — this never reorders or otherwise touches the CandidateKey
    objects themselves (they are read-only here), it only prevents two
    logically-identical keys stored in different internal order from
    being miscounted as distinct.

    Never mutates `candidates` or `evaluations`. Pure: no I/O, no
    random, no config reads, no grouping, no ranking, no "best
    category".
    """
    if len(candidates) != len(evaluations):
        raise ValueError(
            f"candidates and evaluations must have the same length, "
            f"got {len(candidates)} and {len(evaluations)}"
        )

    total_candidates = len(candidates)

    full_keys = {
        (frozenset(c.numeros), frozenset(c.estrelas)) for c in candidates
    }
    number_sets = {frozenset(c.numeros) for c in candidates}
    unique_full_keys = len(full_keys)
    unique_number_sets = len(number_sets)

    category_counts = {category: 0 for category in _ALL_CATEGORIES}
    for evaluation in evaluations:
        category_counts[evaluation.category] = category_counts.get(evaluation.category, 0) + 1

    relevant_categories = set(relevant_categories)
    relevant_count = sum(1 for e in evaluations if e.category in relevant_categories)

    return CandidatePerformanceSummary(
        total_candidates=total_candidates,
        unique_full_keys=unique_full_keys,
        unique_number_sets=unique_number_sets,
        duplicate_count=total_candidates - unique_full_keys,
        full_key_diversity_rate=(unique_full_keys / total_candidates) if total_candidates else 0.0,
        number_set_diversity_rate=(unique_number_sets / total_candidates) if total_candidates else 0.0,
        category_counts=category_counts,
        relevant_count=relevant_count,
        relevant_rate=(relevant_count / total_candidates) if total_candidates else 0.0,
    )
