"""Loading, indexing and querying the Artifact Library
(library/artifacts/entries/*.json).

library/artifacts/entries/*.json is the ONLY primary source. Everything
here is read-only with respect to it — load_all_artifacts() never writes
back to an entry, and LIVRO_DOS_ARTEFACTOS.json (built by build_index(),
written by write_index()) is always a derived artifact, never edited by
hand and never consulted as a source of truth.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from core.services.artifact_schema import ArtifactRecord, normalize_artifact
from core.services.atomic_io import atomic_write_json


class ArtifactLoadError(ValueError):
    """Raised for anything that would silently corrupt the collection if
    allowed through: unparsable JSON, a filename that doesn't match its
    own id, a duplicate id on disk, or a duplicate id passed directly
    into ArtifactRegistry. Always names the offending file path when one
    is available.
    """


def load_all_artifacts(entries_dir: Path) -> list[ArtifactRecord]:
    """Reads and normalizes every *.json in entries_dir. Deterministic
    order (sorted by id). Never mutates any entry file.
    """
    entries_dir = Path(entries_dir)
    records: list[ArtifactRecord] = []
    seen_ids: dict[str, Path] = {}

    for path in sorted(entries_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ArtifactLoadError(f"invalid JSON in {path}: {exc}") from exc

        record = normalize_artifact(raw)

        # Duplicate check first: two files sharing an id can never both
        # satisfy filename == id (that would need two files with the
        # same name in one directory), so checking filename first would
        # always mask this error. Order matters for both to be reachable.
        if record.id in seen_ids:
            raise ArtifactLoadError(
                f"duplicate artifact id {record.id!r}: found in both {seen_ids[record.id]} and {path}"
            )
        seen_ids[record.id] = path

        if record.id != path.stem:
            raise ArtifactLoadError(
                f"{path}: filename does not match id (filename={path.stem!r}, id={record.id!r})"
            )

        records.append(record)

    records.sort(key=lambda r: r.id)
    return records


class ArtifactRegistry:
    """Read-only query surface over an already-loaded, immutable list of
    ArtifactRecord. Holds no reference back to disk — construct with
    load_all_artifacts()'s result. No randomness anywhere in this class.
    """

    def __init__(self, records: Sequence[ArtifactRecord]):
        sorted_records = tuple(sorted(records, key=lambda r: r.id))
        by_id: dict[str, ArtifactRecord] = {}
        for record in sorted_records:
            if record.id in by_id:
                raise ArtifactLoadError(f"duplicate artifact id in ArtifactRegistry: {record.id!r}")
            by_id[record.id] = record
        self._records: tuple[ArtifactRecord, ...] = sorted_records
        self._by_id: dict[str, ArtifactRecord] = by_id

    def all(self) -> tuple[ArtifactRecord, ...]:
        return self._records

    def by_id(self, artifact_id: str) -> ArtifactRecord | None:
        return self._by_id.get(artifact_id)

    def by_type(self, tipo: str) -> tuple[ArtifactRecord, ...]:
        return tuple(r for r in self._records if r.tipo == tipo)

    def by_tag(self, tag: str) -> tuple[ArtifactRecord, ...]:
        needle = tag.strip().lower()
        return tuple(
            r for r in self._records
            if any(t.strip().lower() == needle for t in r.tags)
        )

    def by_creator(self, creator: str) -> tuple[ArtifactRecord, ...]:
        def matches(record: ArtifactRecord) -> bool:
            if record.criador is None:
                return False
            return record.criador.id == creator or record.criador.nome == creator
        return tuple(r for r in self._records if matches(r))


_DESCONHECIDO = "DESCONHECIDO"


def _criador_key(record: ArtifactRecord) -> str:
    if record.criador is None:
        return _DESCONHECIDO
    if record.criador.id:
        return record.criador.id
    if record.criador.nome:
        return record.criador.nome
    return _DESCONHECIDO


def _estado_key(record: ArtifactRecord) -> str:
    if record.estado is not None and record.estado.codigo:
        return record.estado.codigo
    return _DESCONHECIDO


def build_index(records: list[ArtifactRecord]) -> dict:
    """Pure with respect to `records` — the only non-deterministic part is
    `atualizado_em`, generated fresh on every call by design (the one
    field explicitly meant to record when the index was built; every
    other field is fully derived from `records` and reproducible, with
    all grouped counts sorted by key for a stable result regardless of
    the order `records` was given in).
    """
    por_tipo = dict(sorted(Counter(r.tipo or _DESCONHECIDO for r in records).items()))
    por_raridade = dict(sorted(Counter(r.raridade or _DESCONHECIDO for r in records).items()))
    por_estado = dict(sorted(Counter(_estado_key(r) for r in records).items()))
    por_criador = dict(sorted(Counter(_criador_key(r) for r in records).items()))
    por_universo = dict(sorted(Counter(
        str(r.universo_origem) if r.universo_origem is not None else _DESCONHECIDO
        for r in records
    ).items()))
    por_tag = dict(sorted(Counter(tag for r in records for tag in r.tags).items()))

    ranking_energia = [
        {"id": r.id, "energia_acumulada": r.energia_acumulada}
        for r in sorted(records, key=lambda r: (-r.energia_acumulada, r.id))
    ]
    ranking_execucoes_sobrevividas = [
        {"id": r.id, "execucoes_sobrevividas": r.execucoes_sobrevividas}
        for r in sorted(records, key=lambda r: (-r.execucoes_sobrevividas, r.id))
    ]

    return {
        "nome": "Livro dos Artefactos",
        "total_artifacts": len(records),
        "artifact_ids": sorted(r.id for r in records),
        "por_tipo": por_tipo,
        "por_raridade": por_raridade,
        "por_estado": por_estado,
        "por_criador": por_criador,
        "por_universo": por_universo,
        "por_tag": por_tag,
        "ranking_energia": ranking_energia,
        "ranking_execucoes_sobrevividas": ranking_execucoes_sobrevividas,
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def write_index(index: dict, path: Path) -> None:
    atomic_write_json(Path(path), index)
