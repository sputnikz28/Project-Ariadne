"""Academia Arcana de Nemerion — Foundation V1. Common vocabulary
shared by every future classroom/doctrine (Cátedra de Tyche first,
Rebeldes/Hi-Lo/Ecos/Cátedra das Páginas Eternas later, per the
approved Foundation V1 design doc's roadmap) — the DoctrineResult
output contract, the Academia RNG derivation, and the only constructor
that turns a doctrine's output into a CandidateKey carrying real
student identity.

Commit 1/5. Proves vocabulary only. No student, enrollment, classroom,
or doctrine exists in code yet. Nothing here registers a system in
GENERATORS, touches FactionRegistry, main.py, persistence, or any live
faction/Council flow.

Doctrine output contract: DoctrineResult is deliberately NOT modeled
after core.services.treefolks_v2.common.TreefolkScores +
build_key_from_scores(). Treefolks V2's forests are homogeneous enough
(all produce number/star preference scores) that a shared scores
representation and key constructor make sense. The Academia's
doctrines are heterogeneous by design — Cátedra de Tyche is pure
neutral sampling, a future Rebeldes copies/sabotages another
candidate, a future Hi-Lo reads real draw order — forcing them through
one shared scoring algorithm would misrepresent what is actually being
compared. The shared contract is pushed to the OUTPUT boundary only:
either a valid 5-number + 2-star key, or an explicit abstention (both
fields None together, never one without the other).

Candidate construction: build_academy_candidate_key() is deliberately
NOT core.services.backtest_generators._candidate_key_from_record() —
that function hardcodes entity_id=None for every Campaign-Runner-V2
adapter (Astérias, Treefolks V2 included), because none of those
systems represent a persistent individual. The Academia does: a
student is a real, persistent identity across cells/campaigns, so
entity_id must carry student_id honestly. This is a small, deliberate
duplication of the same record-shape — the same trade-off already made
by core.services.star_contribution_trial.py's _trial_rng versus
core.services.backtest_arena._arena_rng.

race is the legacy Arena aggregation label — "Turma/Doutrina" derived
from AcademyClassroomIdentity via classroom_race_label(), never
hardcoded per module. It is a narrative name, not identity: renaming
classroom_name changes this label, and the Arena's race-keyed
aggregation (core.services.backtest_arena.summarize_arena_participation)
would treat the rename as a NEW category in future rankings even
though classroom_id/doctrine_id stay identical. Documented technical
debt, not resolved in this commit — see the approved design doc.

RNG discipline: academia_rng() mirrors
core.services.treefolks_v2.common.forest_rng(),
core.services.backtest_arena._arena_rng(), and
core.services.star_contribution_trial._trial_rng() — SHA-256 over an
explicit, namespaced payload, never Python's randomised built-in hash
function. Namespaced by institution, classroom, doctrine (id and
version), student, and target, so: the same
(student, classroom, doctrine/version, target, seed) is always
reproducible; Student A's stream is always independent of Student B's;
Turma A's stream is always independent of Turma B's — even for the
same target and seed. Never a shared/global random.Random.

The approved design doc also proposed academia_exam_selection_rng(), a
separate namespace for randomised historical-target selection. It is
deliberately NOT included here: Foundation V1's target selection stays
mechanical (the same deterministic, non-random rule already used by
Arena Season 2/3), so a randomised-selection RNG contract would have no
caller and no real test to ground it against — pure speculative
generality. It can be added, with a real caller and real tests, if and
when randomised exam selection is actually built.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from types import MappingProxyType

from core.services.candidate_provenance import CandidateKey


@dataclass(frozen=True)
class DoctrineResult:
    """The only thing every doctrine must produce for one
    (student, target, seed) test. numeros/estrelas both None together
    means abstention; never partially populated (numeros set with
    estrelas None, or vice versa).
    """

    numeros: tuple[int, ...] | None
    estrelas: tuple[int, ...] | None


@dataclass(frozen=True)
class AcademyClassroomIdentity:
    """Canonical identity of one classroom+doctrine pairing — the
    single place a classroom's stable ids and narrative names are
    defined. Every module that needs a race label, academic provenance
    metadata, or a display name derives it from an instance of this
    class; none may hardcode the strings directly.

    institution_id/classroom_id/doctrine_id are stable slugs, never
    changed once assigned. institution_name/classroom_name are
    narrative and may change over time without affecting identity.
    doctrine_version is itself a stable slug (e.g. "v1") — a new
    doctrine revision gets a new version value, never a rewrite of an
    existing one.
    """

    institution_id: str
    institution_name: str
    classroom_id: str
    classroom_name: str
    doctrine_id: str
    doctrine_version: str


def classroom_race_label(identity: AcademyClassroomIdentity) -> str:
    """The legacy Arena `race` label for one classroom+doctrine —
    currently just `classroom_name`, produced here so no other module
    ever composes or hardcodes this string itself. See module
    docstring for the documented rename-creates-a-new-Arena-category
    limitation this label carries.
    """
    return identity.classroom_name


def academia_rng(
    seed: int,
    institution_id: str,
    classroom_id: str,
    doctrine_id: str,
    doctrine_version: str,
    student_id: str,
    target_draw_id: str,
    purpose: str = "candidate",
) -> random.Random:
    """Single seed-derivation point for every RNG draw the Academia
    makes. `purpose` leaves room for a future doctrine needing more
    than one independent stream per (student, cell) without colliding
    with this call's own stream — the same discipline as
    core.services.backtest_arena._arena_rng's `purpose` parameter.
    """
    payload = "|".join([
        "academia", str(seed), institution_id, classroom_id, doctrine_id,
        doctrine_version, student_id, target_draw_id, purpose,
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return random.Random(digest)


def build_academy_candidate_key(
    identity: AcademyClassroomIdentity,
    student_id: str,
    student_name: str,
    student_species: str | None,
    numeros: tuple[int, ...],
    estrelas: tuple[int, ...],
) -> CandidateKey:
    """The only place a doctrine's output becomes a CandidateKey.
    Requires a real key — callers must check DoctrineResult for
    abstention (numeros/estrelas both None) themselves and never call
    this function in that case; abstention is declared to the Arena
    via GeneratorOutput.attempted_races instead, the same mechanism
    already used by Astérias and Treefolks V2.

    entity_id/entity_name carry the acting student's real, stable
    identity — unlike every current Campaign-Runner-V2 adapter, whose
    entity_id is always None. race is produced from `identity` via
    classroom_race_label(), never hardcoded here or anywhere else.
    metadata carries the full academic provenance that
    race/entity_id/entity_name alone cannot express: institution and
    classroom ids and narrative names, doctrine id and version, and
    the student's species (None when not yet defined).
    """
    return CandidateKey(
        source_type="external_generator",
        source_name="academia",
        numeros=tuple(sorted(numeros)),
        estrelas=tuple(sorted(estrelas)),
        generation=None,
        entity_id=student_id,
        entity_name=student_name,
        race=classroom_race_label(identity),
        metadata=MappingProxyType({
            "institution_id": identity.institution_id,
            "institution_name": identity.institution_name,
            "classroom_id": identity.classroom_id,
            "classroom_name": identity.classroom_name,
            "doctrine_id": identity.doctrine_id,
            "doctrine_version": identity.doctrine_version,
            "student_species": student_species,
        }),
    )
