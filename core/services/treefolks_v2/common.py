"""Treefolks V2 — As Grandes Florestas. Shared representation, scoring
contract, and key construction used by every Floresta (Yggdrasil,
Dodona, Brocéliande, Tír na nÓg, Fortuna) — the only place any of them
turns scores into an actual 5-number + 2-star key, so differences in
Arena performance come from the model, never from the constructor.

TreefolkScores is deliberately NOT a probability distribution: scores
represent a model's experimental belief, never the real physical
probability of a number/star being drawn. Every Floresta returns the
same shape regardless of its internal method (LSTM logits, Bayesian
posterior, Markov transition counts, Monte Carlo empirical frequency,
Fortuna's uniform baseline).

RNG discipline: each Floresta gets its OWN independently-namespaced
random.Random, derived via forest_rng() (SHA-256 over an explicit
payload, never Python's randomised built-in hash function) — never a
single sequential
stream shared across Florestas. This is a deliberate departure from
the simpler single-shared-rng convention Astérias/Pantheon use: unlike
those, Yggdrasil's internal training can consume a variable amount of
randomness (weight init, plus whatever torch does internally), and a
shared sequential stream would let that silently perturb every other
Floresta's draws. Each Floresta's stream is fully independent of every
other Floresta's, and of every Arena-side draw (_arena_rng in
core.services.backtest_arena) and every other generator's own RNG.
"""
from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class TreefolkScores:
    """number_scores: keys 1..50, all present. star_scores: keys 1..12,
    all present. Values are finite and non-negative; they do not need
    to sum to 1 — normalization (if any) happens only inside
    build_key_from_scores(), never inside a Floresta's own scoring
    function.
    """

    number_scores: Mapping[int, float]
    star_scores: Mapping[int, float]


def forest_rng(seed: int, floresta: str, draw_id: str) -> random.Random:
    """Single seed-derivation point for every Floresta's own RNG
    stream. `floresta` namespaces which Floresta this stream belongs
    to (e.g. "yggdrasil", "dodona") so two different Florestas in the
    same cell never draw from the same stream, even by accident.
    Public — the treefolks_v2 dispatcher in
    core.services.backtest_generators calls this directly to derive
    each Floresta's stream before invoking its run_*() function.
    """
    payload = "|".join(["treefolks_v2", str(seed), floresta, draw_id])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return random.Random(digest)


def build_key_from_scores(
    number_scores: Mapping[int, float], star_scores: Mapping[int, float], rng: random.Random,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Weighted sampling without replacement — 5 numbers from
    number_scores (1..50), 2 stars from star_scores (1..12) — the
    ONLY function any Floresta uses to turn scores into a key. Feeds
    the sampler in canonical ascending order every time, exactly like
    core.services.backtest_generators._sample_two_stars(), so
    reproducibility given a fixed rng state never depends on dict/set
    iteration order. Ties resolved naturally by the weighted sampler,
    never by a separate tie-break rule.

    All-zero scores (a Floresta with literally no signal) would make
    every weight 0, which random.choices() cannot renormalize —
    callers must never pass all-zero scores; Fortuna uses uniform
    positive scores (1.0) precisely to avoid this degenerate case.
    """
    numbers = list(range(1, 51))
    stars = list(range(1, 13))

    chosen_numbers: list[int] = []
    remaining_numbers = list(numbers)
    for _ in range(5):
        weights = [number_scores[n] for n in remaining_numbers]
        pick = rng.choices(remaining_numbers, weights=weights, k=1)[0]
        chosen_numbers.append(pick)
        remaining_numbers.remove(pick)

    chosen_stars: list[int] = []
    remaining_stars = list(stars)
    for _ in range(2):
        weights = [star_scores[s] for s in remaining_stars]
        pick = rng.choices(remaining_stars, weights=weights, k=1)[0]
        chosen_stars.append(pick)
        remaining_stars.remove(pick)

    return tuple(sorted(chosen_numbers)), tuple(sorted(chosen_stars))
