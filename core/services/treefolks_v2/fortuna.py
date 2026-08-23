"""Bosque de Fortuna — the internal control of Treefolks V2. Uniform
scores over every number/star; build_key_from_scores() then reduces to
plain uniform weighted sampling, equivalent to random.sample(). A
small, local reimplementation rather than importing
core.services.backtest_generators._run_acaso_puro — keeps
treefolks_v2 self-contained, distinct in spirit (per-Floresta control)
from the project-wide acaso_puro system, even though both express the
same "no informative signal" idea.

Always participates — a uniform baseline never has an insufficient-
data condition to abstain under.
"""
from __future__ import annotations

from core.services.treefolks_v2.common import TreefolkScores


def run_fortuna(historico) -> TreefolkScores:
    """historico is accepted for interface symmetry with every other
    Floresta's run_*() function but is never read — Fortuna's scores
    never depend on history, by design.
    """
    return TreefolkScores(
        number_scores={n: 1.0 for n in range(1, 51)},
        star_scores={s: 1.0 for s in range(1, 13)},
    )
