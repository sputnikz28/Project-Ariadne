"""Cátedra de Tyche — Fundamentos do Acaso. Academia Arcana de Nemerion
Foundation V1, commit 4/5: the first executable classroom/doctrine.

Tyche is pure control. It does not learn, does not consult history,
does not use frequency or atraso, does not use books, knowledge, or
personality, has no heuristic, and receives no advantage for being an
Academia classroom. The doctrine is deliberately equivalent to Acaso
Puro (core.services.backtest_generators._run_acaso_puro): 5 distinct
numbers drawn uniformly from 1..50, 2 distinct stars drawn uniformly
from 1..12, sorted only for canonical representation. The only
difference between Tyche and Acaso Puro at this stage is provenance
and academic identity — never algorithm.

TYCHE_IDENTITY is the single canonical definition of Cátedra de Tyche's
narrative names and stable ids. Nothing else in this codebase may
hardcode "Cátedra de Tyche — Fundamentos do Acaso", "catedra_tyche", or
"tyche" directly — every module that needs the label derives it from
this constant, e.g. via core.services.academia.common.
classroom_race_label().

run_tyche() takes only an rng — no ctx, no historico, no student, no
enrollment, no registry, no filesystem. core.services.academia.common.
DoctrineResult does not force a shared callable signature on every
doctrine (unlike core.services.treefolks_v2.common's homogeneous
Floresta contract, where every Floresta genuinely produces the same
TreefolkScores shape from the same historico) — only a shared OUTPUT
type. Tyche is the concrete proof that forcing a `historico` parameter
on every doctrine "for uniformity" would have been dishonest: Tyche's
hypothesis has nothing to do with history, so it does not receive one.
A future doctrine that genuinely needs historico (or a student's
acquired knowledge, once that exists) will simply declare that
parameter on its own function; core.services.backtest_generators.
_run_academia (the adapter, not the doctrine) is the one place that
decides what each registered doctrine is called with.
"""
from __future__ import annotations

import random

from core.services.academia.common import AcademyClassroomIdentity, DoctrineResult

TYCHE_IDENTITY = AcademyClassroomIdentity(
    institution_id="nemerion",
    institution_name="Academia Arcana de Nemerion",
    classroom_id="catedra_tyche",
    classroom_name="Cátedra de Tyche — Fundamentos do Acaso",
    doctrine_id="tyche",
    doctrine_version="v1",
)


def run_tyche(rng: random.Random) -> DoctrineResult:
    """Never abstains — always returns a valid key. numeros are drawn
    before estrelas (fixed order, so results are deterministic given
    the same rng state); sorting is purely for canonical
    representation and never changes which numbers/stars were chosen.
    """
    numeros = tuple(sorted(rng.sample(range(1, 51), 5)))
    estrelas = tuple(sorted(rng.sample(range(1, 13), 2)))
    return DoctrineResult(numeros=numeros, estrelas=estrelas)
