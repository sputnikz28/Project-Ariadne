"""Cátedra de Mnemosyne — Memória da Frequência. Academia Arcana de
Nemerion, Segunda Cátedra: the first non-control doctrine.

Hypothesis V1: "Números e estrelas historicamente mais frequentes
possuem maior probabilidade de seleção do que sob amostragem
uniforme." Cátedra de Tyche — Fundamentos do Acaso (core.services.
academia.tyche) remains the control this Doctrine is compared
against — this module never claims statistical superiority over
Tyche, only implements the hypothesis honestly.

Mathematics (approved after a dedicated read-only audit of
core.evolution.statistics.calculate()): weight(n) = count_historico(n)
+ 1 for every n in 1..50, weight(e) = count_historico(e) + 1 for
every e in 1..12 — Laplace α=1 over RAW appearance counts. Deliberately
NEVER calculate()'s own freq_norm/freq_est_norm: those are normalized
by the MAXIMUM observed count (not a probability mass), and produce
an exact zero weight for any value never observed — confirmed
empirically against the real dataset to be a live problem, not a
theoretical one (the Piloto's own first target, 002/2004, has exactly
1 prior draw, leaving 45/50 numbers and 10/12 stars at zero raw
frequency). Laplace α=1 guarantees every value gets weight >= 1 > 0,
and a more-frequent value never receives a smaller weight than a
less-frequent one (count is monotonic; +1 is a constant shift that
preserves strict ordering). This exact smoothing convention already
has real precedent in this project: core.services.backtest_generators.
_smoothed_probabilities() (Astérias) uses the identical α=1 Laplace
scheme — Mnemosyne reuses the CONVENTION, never the code (see below).

Weighted sampling without replacement: no neutral primitive for this
exists in the codebase outside core.services.treefolks_v2.common.
build_key_from_scores() — deliberately never imported here. Importing
a sibling experimental system's internals would couple Mnemosyne's
hypothesis to Treefolks V2's implementation choices, silently
changing what "Mnemosyne v1" means if that module ever changes.
_weighted_sample_without_replacement() below is a small, private,
self-contained implementation — pick-then-remove using rng.choices()
for one single draw at each step. Small deliberate duplication of the
same shape build_key_from_scores() already uses, the same trade-off
already made repeatedly in this project (e.g. core.services.academia.
common.build_academy_candidate_key() vs core.services.
backtest_generators._candidate_key_from_record()).

Abstention: DoctrineResult(numeros=None, estrelas=None) exactly when
historico is empty — the ONLY abstention condition in V1, per the
approved decision. No minimum-history-count threshold, no
"all values observed at least once" gate — either of those would
itself become part of the hypothesis under test, not a neutral
technical guard. Never falls back to Tyche or any other doctrine.

run_mnemosyne(historico, rng) receives only historico (already cut by
the Campaign Runner's anti-look-ahead boundary) and rng (already
namespaced per student by core.services.academia.common.academia_rng)
— never a Student, AcademyEnrollment, academic history, Personality,
Knowledge, Book, or Skill. The student has no algorithmic power over
this Doctrine, exactly like Tyche.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Iterable, Mapping, Sequence
from collections import Counter

from core.services.academia.common import AcademyClassroomIdentity, DoctrineResult

MNEMOSYNE_IDENTITY = AcademyClassroomIdentity(
    institution_id="nemerion",
    institution_name="Academia Arcana de Nemerion",
    classroom_id="catedra_mnemosyne",
    classroom_name="Cátedra de Mnemosyne — Memória da Frequência",
    doctrine_id="mnemosyne",
    doctrine_version="v1",
)


def _laplace_weights(
    historico: Sequence[Mapping[str, object]], key: Callable[[Mapping[str, object]], Iterable[int]], universe: range,
) -> dict[int, int]:
    """weight(v) = count_historico(v) + 1 for every v in `universe` —
    Laplace α=1 over RAW appearance counts, never core.evolution.
    statistics.calculate()'s freq_norm (max-normalized, exact zero for
    never-observed values — see module docstring). `key` extracts the
    list of values from one historico entry (e.g. a lambda returning
    draw["numeros"]). Never mutates `historico` or any of its entries.
    """
    counts: Counter = Counter()
    for draw in historico:
        counts.update(key(draw))
    return {v: counts.get(v, 0) + 1 for v in universe}


def _weighted_sample_without_replacement(
    weights: Mapping[int, int], universe: range, k: int, rng: random.Random,
) -> list[int]:
    """Picks k distinct values from `universe`, weighted by `weights`,
    without replacement — pick-then-remove, one rng.choices() draw per
    step. Small, private, self-contained (see module docstring for why
    this is not imported from core.services.treefolks_v2.common).
    """
    remaining = list(universe)
    chosen: list[int] = []
    for _ in range(k):
        picked = rng.choices(remaining, weights=[weights[v] for v in remaining], k=1)[0]
        chosen.append(picked)
        remaining.remove(picked)
    return chosen


def run_mnemosyne(historico: Sequence[Mapping[str, object]], rng: random.Random) -> DoctrineResult:
    """Abstains (numeros=None, estrelas=None) only when historico is
    empty — the sole V1 abstention condition. Otherwise always returns
    a valid, canonically-sorted 5-number + 2-star key.
    """
    if not historico:
        return DoctrineResult(numeros=None, estrelas=None)

    number_weights = _laplace_weights(historico, lambda d: d["numeros"], range(1, 51))
    star_weights = _laplace_weights(historico, lambda d: d["estrelas"], range(1, 13))

    numeros = tuple(sorted(_weighted_sample_without_replacement(number_weights, range(1, 51), 5, rng)))
    estrelas = tuple(sorted(_weighted_sample_without_replacement(star_weights, range(1, 13), 2, rng)))
    return DoctrineResult(numeros=numeros, estrelas=estrelas)
