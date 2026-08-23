"""Floresta de Dodona — real Bayesian model. Each number/star is
modeled as an independent Bernoulli process (appears in a draw, or
doesn't); a Beta(alpha, alpha) prior is updated with the observed
appearance count over the visible history to give a posterior mean
per number/star. That posterior mean is the score — never described
as "the real probability of being drawn": it is a posterior belief
under a specific, stated model (independent-Bernoulli-per-value),
which is a simplification of the true drawing process (5 numbers
drawn without replacement, not 50 independent coin flips).

alpha is fixed and pre-declared, the same Laplace/Beta-smoothing
philosophy already approved for Astérias de Thalássia — never chosen
after seeing results.

Always participates: a Beta prior is well-defined even with zero
observations (posterior mean reduces to the prior mean, 0.5, for
every value) — there is no "insufficient data" condition to abstain
under, unlike Yggdrasil/Brocéliande.
"""
from __future__ import annotations

from core.services.treefolks_v2.common import TreefolkScores

_DODONA_ALPHA = 1.0


def _posterior_means(historico, universe: range, key: str) -> dict[int, float]:
    total_draws = len(historico)
    counts = {v: 0 for v in universe}
    for draw in historico:
        for v in draw[key]:
            counts[v] += 1
    denom = total_draws + 2 * _DODONA_ALPHA
    return {v: (counts[v] + _DODONA_ALPHA) / denom for v in universe}


def run_dodona(historico) -> TreefolkScores:
    number_scores = _posterior_means(historico, range(1, 51), "numeros")
    star_scores = _posterior_means(historico, range(1, 13), "estrelas")
    return TreefolkScores(number_scores=number_scores, star_scores=star_scores)
