"""Mata de Brocéliande — real Markov transition model. State is
deliberately a SINGLE number/star from the previous draw, never the
full 5-number/2-star combination — the same principle already
established for Astérias' star-pair conditional model, and the same
pattern already real and working in
factions/chaos_cartographers/markov.py (Oryn dos Ecos Sequenciais,
number-to-number transitions between consecutive draws). 50x50 + 12x12
transition cells — no combinatorial explosion.

For each value q present in the immediately preceding draw
(historico[-1]), builds a SEPARATE Laplace-smoothed transition
distribution using only historical transitions i -> i+1 where
q was present in draw i — i.e. genuinely "given q appeared, what
tended to appear next", never a global/unconditional transition
count. The final score is the arithmetic mean of those per-q
distributions across every q in the query (5 numbers or 2 stars),
so each element of the previous key carries equal weight in
Brocéliande's belief, regardless of how historically frequent that
element itself is.

Abstains when len(historico) < 2 — a STRUCTURAL minimum, not a chosen
threshold: a transition (draw i -> draw i+1) cannot exist with fewer
than 2 draws, so there is literally no transition table to build.
Consistent with the project's abstain-rather-than-fabricate
philosophy already applied to Astéria Abissal, applied here to a case
forced by the definition of a transition rather than picked as a
tunable cutoff.
"""
from __future__ import annotations

from core.services.treefolks_v2.common import TreefolkScores

_BROCELIANDE_ALPHA = 1.0


def _transition_scores(historico, universe: range, key: str, query_values) -> dict[int, float]:
    """One Laplace-smoothed transition distribution per q in
    query_values (range(len(historico) - 1) loop bound => the last
    position of historico is never read as a "current" draw, so no
    transition can ever use the target's own instant as its
    successor), then the arithmetic mean of those distributions —
    never a single pooled count across every q.
    """
    size = len(universe)
    per_query_distributions = []
    for q in query_values:
        counts = {v: 0 for v in universe}
        for i in range(len(historico) - 1):
            if q not in historico[i][key]:
                continue
            for v in historico[i + 1][key]:
                counts[v] += 1
        total_votes = sum(counts.values())
        denom = total_votes + size * _BROCELIANDE_ALPHA
        per_query_distributions.append({v: (counts[v] + _BROCELIANDE_ALPHA) / denom for v in universe})

    n_queries = len(per_query_distributions)
    return {v: sum(dist[v] for dist in per_query_distributions) / n_queries for v in universe}


def run_broceliande(historico) -> TreefolkScores | None:
    if len(historico) < 2:
        return None
    last_draw = historico[-1]
    number_scores = _transition_scores(historico, range(1, 51), "numeros", last_draw["numeros"])
    star_scores = _transition_scores(historico, range(1, 13), "estrelas", last_draw["estrelas"])
    return TreefolkScores(number_scores=number_scores, star_scores=star_scores)
