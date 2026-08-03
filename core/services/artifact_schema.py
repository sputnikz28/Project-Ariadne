"""Canonical, in-memory normalization for library/artifacts/entries/*.json.

The 15 founding entries were authored independently, over time, without a
shared writer — so several fields appear in more than one shape across
them (a plain string in one entry, a translated/id-bearing object in
another). This module never rewrites the source files to "fix" that; it
only normalizes on read, into a small, extensible ArtifactRecord.

Design (approved): a SMALL fixed core (id, nome, tipo, raridade, estado,
criador, universo_origem, energia_acumulada, vezes_encontrado,
execucoes_sobrevividas, efeitos, lore, historia, tags) plus two escape
hatches that guarantee nothing is ever lost:
  - extras: every top-level key not in the core, preserved verbatim
    under its original name (material, donos, portador_atual,
    corrupcao_sombria, purificado, bencaos, inscricao, multiplicador,
    geracao_criacao, conselhos, cor_principal, and every type-specific
    block — olhos/objetivo/rituais, condicao_ativacao/celebracao/
    aparencia, conforto/fofura, ritual, cores, guardiao/indice/
    paginas_vivas/evolucao — all land here, unmodified, under their
    original key).
  - raw: the complete original dict, untouched.

Only the core fields that were observed with genuinely inconsistent
SHAPES get typed normalization (estado, criador, nome, lore,
historia[].evento). Everything else in extras is passed through exactly
as found — no shape is assumed, no default is invented for it.

Defaults are applied ONLY where a default cannot change narrative
meaning: energia_acumulada, vezes_encontrado and execucoes_sobrevividas
default to 0/0.0 (a counter that hasn't happened yet), tags/historia
default to an empty tuple (nothing recorded yet). Every other core field
is None when absent from the source — never a guessed value.

Pure: no file or network I/O anywhere in this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

_CORE_KEYS = frozenset({
    "id", "nome", "tipo", "raridade", "estado", "criador", "universo_origem",
    "energia_acumulada", "vezes_encontrado", "execucoes_sobrevividas",
    "efeitos", "lore", "historia", "tags",
})


@dataclass(frozen=True)
class Localized:
    """A field seen as either a plain string or a translated/id-bearing
    object (estado, historia[].evento). `codigo` is the stable identifier
    (the string itself, or the object's "id"); `traducoes` holds every
    other key found on the object (usually language codes), empty if the
    source was a bare string.
    """
    codigo: str | None
    traducoes: Mapping[str, str]


@dataclass(frozen=True)
class PersonagemRef:
    """`criador`, normalized — seen as either a plain string or {id, nome}."""
    id: str | None
    nome: str


@dataclass(frozen=True)
class EventoHistoria:
    evento: Localized
    extra: Mapping[str, Any]  # everything else on this historia entry (momento, descricao, local, personagem, criador, guardiao, mago, geracao...), verbatim


@dataclass(frozen=True)
class ArtifactRecord:
    id: str | None
    nome: Mapping[str, str] | None
    tipo: str | None
    raridade: str | None
    estado: Localized | None
    criador: PersonagemRef | None
    universo_origem: int | str | None
    energia_acumulada: float
    vezes_encontrado: int
    execucoes_sobrevividas: int
    efeitos: Mapping[str, Any] | None
    lore: Mapping[str, str] | None
    historia: tuple[EventoHistoria, ...]
    tags: tuple[str, ...]
    extras: Mapping[str, Any]
    raw: Mapping[str, Any]


def _normalize_localized(value: Any) -> Localized | None:
    if value is None:
        return None
    if isinstance(value, str):
        return Localized(codigo=value, traducoes=MappingProxyType({}))
    if isinstance(value, Mapping):
        codigo = value.get("id")
        traducoes = {k: v for k, v in value.items() if k != "id"}
        return Localized(codigo=codigo, traducoes=MappingProxyType(traducoes))
    return None


def _normalize_personagem(value: Any) -> PersonagemRef | None:
    if value is None:
        return None
    if isinstance(value, str):
        return PersonagemRef(id=None, nome=value)
    if isinstance(value, Mapping):
        return PersonagemRef(id=value.get("id"), nome=value.get("nome", ""))
    return None


def _normalize_lore(value: Any) -> Mapping[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        return None
    descricao = value.get("descricao")
    if isinstance(descricao, Mapping):
        return MappingProxyType(dict(descricao))
    # Daruma shape: lore IS already {"pt": "..."} with no "descricao" wrapper.
    return MappingProxyType(dict(value))


def _normalize_historia(value: Any) -> tuple[EventoHistoria, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    events = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        evento = _normalize_localized(item.get("evento"))
        if evento is None:
            evento = Localized(codigo=None, traducoes=MappingProxyType({}))
        extra = {k: v for k, v in item.items() if k != "evento"}
        events.append(EventoHistoria(evento=evento, extra=MappingProxyType(extra)))
    return tuple(events)


def _normalize_nome(value: Any) -> Mapping[str, str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return MappingProxyType({"pt": value})
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    return None


def _normalize_efeitos(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    return None


def _as_float_default(value: Any, default: float) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return default


def _as_int_default(value: Any, default: int) -> int:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return default


def _as_tags(value: Any) -> tuple[str, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(v for v in value if isinstance(v, str))
    return ()


def normalize_artifact(raw: Mapping[str, Any]) -> ArtifactRecord:
    """Pure. Never raises: an unexpected shape on any field just falls
    back to None (core fields) or is left untouched in `extras`/`raw`.
    Never reads or writes any file — `raw` is the caller's already-loaded
    dict, returned inside the record for full traceability.
    """
    extras = {k: v for k, v in raw.items() if k not in _CORE_KEYS}

    return ArtifactRecord(
        id=raw.get("id"),
        nome=_normalize_nome(raw.get("nome")),
        tipo=raw.get("tipo"),
        raridade=raw.get("raridade"),
        estado=_normalize_localized(raw.get("estado")),
        criador=_normalize_personagem(raw.get("criador")),
        universo_origem=raw.get("universo_origem"),
        energia_acumulada=_as_float_default(raw.get("energia_acumulada"), 0.0),
        vezes_encontrado=_as_int_default(raw.get("vezes_encontrado"), 0),
        execucoes_sobrevividas=_as_int_default(raw.get("execucoes_sobrevividas"), 0),
        efeitos=_normalize_efeitos(raw.get("efeitos")),
        lore=_normalize_lore(raw.get("lore")),
        historia=_normalize_historia(raw.get("historia")),
        tags=_as_tags(raw.get("tags")),
        extras=MappingProxyType(extras),
        raw=MappingProxyType(dict(raw)),
    )


def _narrative_safety_flags(record: ArtifactRecord) -> Mapping[str, Any] | None:
    """Where the altera_algoritmo/altera_resultados/altera_probabilidades
    trio lives: inside `efeitos` for the 13 founding entries, or inside
    `extras["principios_narrativos"]` for any future entry that chooses
    that shape instead. Returns None if found in neither place.
    """
    if isinstance(record.efeitos, Mapping) and "altera_algoritmo" in record.efeitos:
        return record.efeitos
    principios = record.extras.get("principios_narrativos")
    if isinstance(principios, Mapping) and "altera_algoritmo" in principios:
        return principios
    return None


def validate_artifact_record(record: ArtifactRecord) -> list[str]:
    """Pure structural validation. Never raises — returns problem strings.
    An empty list means the record is sound.
    """
    problems: list[str] = []

    if not record.id:
        problems.append("missing id")
    if record.tipo is None:
        problems.append(f"{record.id}: missing tipo")
    if record.raridade is None:
        problems.append(f"{record.id}: missing raridade")
    if record.nome is None:
        problems.append(f"{record.id}: missing nome")

    flags = _narrative_safety_flags(record)
    if flags is None:
        problems.append(f"{record.id}: no altera_algoritmo/altera_resultados/altera_probabilidades flags found")
    else:
        for flag in ("altera_algoritmo", "altera_resultados", "altera_probabilidades"):
            if flags.get(flag) is not False:
                problems.append(f"{record.id}: {flag} is not explicitly False")

    return problems
