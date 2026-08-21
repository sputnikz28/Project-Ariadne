"""Candidate Provenance Inventory (Commit 16) — pure normalization of
already-persisted candidate-key records (the 18 distinct `origem`
values confirmed against the real
datasets/generated/simulations/arquivo_destino.json during the
Commit 16 audit) into one canonical CandidateKey contract.

Normalizes only. Never generates a key, never evaluates/ranks/scores a
candidate, never compares against a winning draw, never reads a file,
never uses random. Does not alter main.py, any faction, the Council,
or persistence — this module is entirely downstream of data that
already exists.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal

SourceType = Literal[
    "evolutionary_individual",
    "external_generator",
    "aggregator",
    "transformer",
    "configured_candidate",
]

# Closed taxonomy — every origem persisted today in arquivo_destino.json
# (18 distinct values, confirmed against the real archive during the
# Commit 16 audit) must appear here explicitly. An origem outside this
# table raises ValueError in normalize_candidate_record() rather than
# being silently guessed — a new source must be classified
# deliberately, never inferred.
_SOURCE_TYPE_BY_ORIGEM: Mapping[str, SourceType] = MappingProxyType({
    "racas_antigas": "evolutionary_individual",
    "cla_anao": "external_generator",
    "fada": "external_generator",
    "melfork": "external_generator",
    "treefolk": "external_generator",
    "cronomante": "external_generator",
    "esqueleto": "external_generator",
    "vampiro": "external_generator",
    "gargula": "external_generator",
    "kors_elarion": "external_generator",
    "axiomantes_nemerion": "external_generator",
    "esquadrao_negro": "external_generator",
    "ser_superior": "external_generator",
    "chave_conselho": "aggregator",
    "deus": "aggregator",
    "corrupcao_final": "transformer",
    "necromancia_estatistica": "transformer",
    "ritual_celeste": "configured_candidate",
})

# Fields main.py:registo_externo() (and factions/clerics/algorithm.py's
# equivalent regs.append()) always write for every origem, mapped
# explicitly onto CandidateKey attributes (or deliberately discarded —
# see CandidateKey's docstring) — never allowed to leak into `metadata`
# by a side door, for any source_type.
_CANONICAL_FIELDS = frozenset({"origem", "numeros", "estrelas", "geracao", "id", "nome", "classe"})


@dataclass(frozen=True)
class CandidateKey:
    """A canonical, honest view of one already-persisted candidate-key
    record. Every field is either copied verbatim from the source
    record or left None when the source does not genuinely provide
    it — never inferred, never fabricated.

    generation/entity_id/race are populated ONLY when
    source_type == "evolutionary_individual" (origem == "racas_antigas"
    — Clerics). For every other source_type, the record's own
    "geracao"/"id"/"classe" fields are present in the JSON
    (registo_externo() writes them uniformly for every origem, to keep
    one archive schema) but are NEVER copied into these attributes:

      - "geracao" for non-Clerics origins is always main.py's
        final_generation constant, stamped identically onto every
        faction's records regardless of whether that faction has any
        real generational concept at all — not a genuine generation,
        so `generation` stays None.
      - "id" for non-Clerics origins is always a literal copy of
        "nome" — main.py:registo_externo(name, faction_class, key,
        origem, generation, casa, extra) has no distinct id parameter
        at all. Not a genuine separate identifier, so `entity_id`
        stays None.
      - "classe" means two different things depending on the source:
        for racas_antigas it is the individual's real race
        (Heroi.raca), safe to expose as `race`; for every other origem
        it is that faction's faction_class/"tipo" label (e.g. "Mago",
        "Clã Anão") — never a biological/lineage race, so `race` stays
        None there. "classe" is treated as a canonical field either
        way and is EXCLUDED from `metadata` for every source_type, even
        when it isn't promoted to `race` — for external_generator/
        aggregator/transformer/configured_candidate sources this means
        the faction_class/"tipo" label carried in "classe" is not
        exposed by CandidateKey at all in this commit (only
        `entity_name`/`source_name` survive).

    entity_name is populated whenever the source record has "nome" —
    including anonymous-per-run labels (e.g. "Mago-1") for external
    generators; that is honest provenance (this is what the source
    called itself this run), never fabricated identity.

    metadata never contains a canonical field (origem, numeros,
    estrelas, geracao, id, nome, classe) under any circumstance — only
    genuinely supplementary data already on the record (e.g. "casa",
    "run_id", faction-specific extras like "score_negro"). Read-only
    (MappingProxyType).

    No candidate_id/derived_from field exists — no source in the
    current archive honestly provides a stable id or a persisted
    parent-key link (registo_externo() has no id parameter, and
    Council -> Malphas / lenda -> eco provenance is computed in memory
    but never written to arquivo_destino.json — confirmed during the
    Commit 16 audit). Adding either would mean fabricating identity;
    left out entirely rather than included as an always-None stub.
    """

    source_type: SourceType
    source_name: str
    numeros: tuple[int, ...]
    estrelas: tuple[int, ...]
    generation: int | None
    entity_id: str | None
    entity_name: str | None
    race: str | None
    metadata: Mapping[str, Any]


def normalize_candidate_record(record: Mapping[str, Any]) -> CandidateKey:
    """record: one already-loaded element of arquivo_destino.json (or an
    equivalent already-loaded mapping with the same registo_externo()
    shape) — this function never reads a file itself, never mutates
    `record`.

    Raises ValueError if record["origem"] is not one of the 18 origens
    in the closed taxonomy above — a new source must be classified
    explicitly in _SOURCE_TYPE_BY_ORIGEM, never guessed here.
    """
    origem = record["origem"]
    source_type = _SOURCE_TYPE_BY_ORIGEM.get(origem)
    if source_type is None:
        raise ValueError(
            f"unrecognized origem {origem!r} — not in the closed source_type taxonomy; "
            "classify it explicitly in _SOURCE_TYPE_BY_ORIGEM before normalizing"
        )

    is_evolutionary = source_type == "evolutionary_individual"

    metadata = MappingProxyType({
        key: value for key, value in record.items() if key not in _CANONICAL_FIELDS
    })

    return CandidateKey(
        source_type=source_type,
        source_name=origem,
        numeros=tuple(record["numeros"]),
        estrelas=tuple(record["estrelas"]),
        generation=record.get("geracao") if is_evolutionary else None,
        entity_id=record.get("id") if is_evolutionary else None,
        entity_name=record.get("nome"),
        race=record.get("classe") if is_evolutionary else None,
        metadata=metadata,
    )
