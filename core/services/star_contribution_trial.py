"""Star Contribution Trial — paired experiment isolating the effect of
swapping only the star-selection mechanism, holding the 5 neutral
numeros fixed. Analysis-only: never registers a system in GENERATORS,
never produces a CandidateKey, never touches backtest_orchestrator.py
or any faction algorithm.

Gap this module closes: core.services.backtest_generators._run_acaso_puro
and _run_asterias each build their own random.Random(seed), but consume
it in different orders per candidate (Acaso Puro draws numeros then
estrelas in one call; Astérias draws estrelas then numeros). Even with
the same seed, the numeros the two adapters produce are therefore not
the same numeros by construction — they only coincide, as shown by the
Astérias smoke test, when comparing the SAME system across different
real targets, never across two different systems. There was no existing
seam that produces one shared set of neutral numeros and then applies
two different star mechanisms on top of it.

This module closes that gap with 3 independently namespaced RNG
streams per (target, generator_seed, lineage) — numbers, Acaso Puro's
stars, and the Astéria lineage's stars — so the numeros stream is
identical between the two variants BY CONSTRUCTION, never by
coincidence of call order. matched_numbers is deliberately never
reported: it is identical in both variants by construction, and the
hypothesis under test here is exclusively about stars (see Astérias'
own contract in backtest_generators.py).

RNG discipline mirrors core.services.backtest_arena._arena_rng() —
SHA-256 over an explicit, namespaced payload, never Python's built-in
hash(). Not reused directly from backtest_arena.py (that function's
signature bakes in `system`/`race`, which don't map cleanly onto this
module's simpler numbers/acaso/asteria stream split); duplicated here
deliberately, the same small, explicit trade-off already made by
core.services.candidate_evaluation.py against hero_evaluation.py.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Literal

from core.services.backtest_generators import asterias_distribution, sample_two_stars
from core.services.backtest_lab import BacktestTarget


def _trial_rng(arena_seed: int, purpose: str, target: BacktestTarget, generator_seed: int) -> random.Random:
    """Single seed-derivation point for every RNG draw in this module.
    `purpose` namespaces the stream ("numbers", "acaso",
    "asteria:abissal", "asteria:mares", ...) so the three streams for
    one (target, generator_seed) cell never collide with each other or
    with any Arena/generator RNG draw elsewhere in the project.
    """
    payload = "|".join(["star_trial", str(arena_seed), purpose, target.draw_id, str(generator_seed)])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return random.Random(digest)


def _match_count(values, target_values) -> int:
    return len(set(values) & set(target_values))


@dataclass(frozen=True)
class StarContributionPair:
    """One paired trial: the exact same 5 neutral numeros, evaluated
    twice against the same target — once with Acaso Puro's uniform
    star draw, once with one Astéria lineage's star draw. numeros is
    shared BY CONSTRUCTION between the two variants (drawn once, from
    a dedicated rng stream neither star mechanism ever touches) — see
    module docstring for why this could not be done by reusing the
    two existing adapters as-is.

    matched_numbers is deliberately not exposed: it is identical in
    both variants by construction, and the hypothesis under test is
    exclusively about stars.
    """

    index: int
    numeros: tuple[int, ...]
    estrelas_acaso: tuple[int, ...]
    estrelas_asteria: tuple[int, ...]
    matched_stars_acaso: int
    matched_stars_asteria: int
    category_acaso: str
    category_asteria: str
    direction: Literal["melhorou", "igual", "piorou"]


def run_star_contribution_trial(
    ctx: dict,
    target: BacktestTarget,
    lineage: str,
    quantidade: int,
    generator_seed: int,
    arena_seed: int,
) -> tuple[StarContributionPair, ...] | None:
    """Returns None if `lineage` ("abissal" or "mares") abstains for
    ctx['historico'] at this cell — the same participation rule
    asterias_distribution() already uses. Never fabricates a
    comparison for a lineage that would not have participated in the
    real campaign.

    numeros always come from a dedicated "numbers" RNG stream that
    neither the "acaso" nor the "asteria:{lineage}" stream ever
    touches — the three streams are drawn independently per index, in
    a fixed order (numbers, then acaso stars, then asteria stars), so
    results are deterministic given the same
    (target, generator_seed, arena_seed, lineage).
    """
    historico = ctx["historico"]
    probabilities, participates = asterias_distribution(historico, lineage)
    if not participates:
        return None

    numbers_rng = _trial_rng(arena_seed, "numbers", target, generator_seed)
    acaso_rng = _trial_rng(arena_seed, "acaso", target, generator_seed)
    asteria_rng = _trial_rng(arena_seed, f"asteria:{lineage}", target, generator_seed)

    pairs = []
    for i in range(quantidade):
        numeros = tuple(sorted(numbers_rng.sample(range(1, 51), 5)))
        estrelas_acaso = tuple(sorted(acaso_rng.sample(range(1, 13), 2)))
        estrelas_asteria = sample_two_stars(probabilities, asteria_rng)

        matched_numbers = _match_count(numeros, target.numeros)
        matched_acaso = _match_count(estrelas_acaso, target.estrelas)
        matched_asteria = _match_count(estrelas_asteria, target.estrelas)

        category_acaso = f"{matched_numbers}+{matched_acaso}"
        category_asteria = f"{matched_numbers}+{matched_asteria}"

        if matched_asteria > matched_acaso:
            direction: Literal["melhorou", "igual", "piorou"] = "melhorou"
        elif matched_asteria < matched_acaso:
            direction = "piorou"
        else:
            direction = "igual"

        pairs.append(StarContributionPair(
            index=i,
            numeros=numeros,
            estrelas_acaso=estrelas_acaso,
            estrelas_asteria=estrelas_asteria,
            matched_stars_acaso=matched_acaso,
            matched_stars_asteria=matched_asteria,
            category_acaso=category_acaso,
            category_asteria=category_asteria,
            direction=direction,
        ))

    return tuple(pairs)
