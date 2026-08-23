"""Selva de Tír na nÓg — real Monte Carlo model. What is LEARNED from
history: empirical frequency + delay weights per number/star, from
core.evolution.statistics.calculate() (the same pure function
core.services.fitness.fitness() already expects as its `est` argument,
already consumed by Skeletons/Melforks/Pantheon via
ctx['estatisticas'] in the shared backtest path).

What is SIMULATED afterwards: N_SIMULACOES candidate keys drawn using
those empirical weights (via the same shared build_key_from_scores()
every other Floresta uses), each scored by
core.services.fitness.fitness() — the SAME real fitness function
already used in production by Werewolves/Zombie, reused here without
modification. The top ELITE_SIZE highest-scoring simulated keys are
kept; Tír na nÓg's final number_scores/star_scores are how often each
value appears among that elite slice (occurrences / ELITE_SIZE) — not
the raw sampling frequency. This is what distinguishes Tír na nÓg from
"a few thousand random keys labelled as a model": there is a genuine
fitness-guided search step between the empirical prior and the final
score.

N_SIMULACOES=1000, TOP_FRACTION=0.10 (ELITE_SIZE=100) are frozen V1
hyperparameters, never adjusted after seeing Arena results. Ranking
ties (equal fitness) are broken deterministically by canonical
(numeros, estrelas) — never by RNG draw order, so the elite slice
never silently depends on simulation order.

No smoothing/floor anywhere: proven (see module tests) that
freq_norm[n] + atraso_norm[n] > 0 for every number/star whenever
len(historico) >= 1 — a number never seen has maximal atraso instead;
a number already seen has positive freq_norm regardless of atraso.
The only degenerate case is a fully empty historico, handled by
abstention below, not by a fabricated floor. Final elite-frequency
scores can be exactly 0 for a number that never appears in the elite;
this is never masked — in the astronomically unlikely case that fewer
than 5 distinct numbers (or 2 distinct stars) appear across the whole
elite, build_key_from_scores() raises ValueError rather than silently
fabricating a candidate, the same fail-loud discipline the rest of the
project already applies (official_key() returns None rather than
guessing; _assert_one_result_per_cell() raises rather than picks).

Abstains when historico is empty (len == 0) — a STRUCTURAL minimum
forced by calculate()'s own degenerate output at zero draws, not a
chosen threshold, the same category as Brocéliande's len(historico)<2.
"""
from __future__ import annotations

from core.evolution.statistics import calculate
from core.services.fitness import fitness
from core.services.treefolks_v2.common import TreefolkScores, build_key_from_scores

_N_SIMULACOES = 1000
_TOP_FRACTION = 0.10
_ELITE_SIZE = round(_N_SIMULACOES * _TOP_FRACTION)


def run_tirnanog(historico, rng) -> TreefolkScores | None:
    if not historico:
        return None

    est = calculate(historico)
    sim_number_weights = {n: est["freq_norm"][n] + est["atraso_norm"][n] for n in range(1, 51)}
    sim_star_weights = {s: est["freq_est_norm"][s] + est["atraso_est_norm"][s] for s in range(1, 13)}

    scored = []
    for _ in range(_N_SIMULACOES):
        numeros, estrelas = build_key_from_scores(sim_number_weights, sim_star_weights, rng)
        score = fitness((numeros, estrelas), est)
        scored.append((score, numeros, estrelas))

    # Deterministic, canonical tie-break: fitness descending, then the
    # candidate's own (numeros, estrelas) ascending -- never RNG order.
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    elite = scored[:_ELITE_SIZE]

    number_counts = {n: 0 for n in range(1, 51)}
    star_counts = {s: 0 for s in range(1, 13)}
    for _score, numeros, estrelas in elite:
        for n in numeros:
            number_counts[n] += 1
        for s in estrelas:
            star_counts[s] += 1

    number_scores = {n: number_counts[n] / _ELITE_SIZE for n in range(1, 51)}
    star_scores = {s: star_counts[s] / _ELITE_SIZE for s in range(1, 13)}
    return TreefolkScores(number_scores=number_scores, star_scores=star_scores)
