"""Ariadne Research Dashboard — data assembly layer.

Row contracts and data-shaping functions. The functions defined here
take already-loaded plain Python structures (e.g. the result of calling
HeroRegistry().load_all() / LegendRegistry().load_all(), or the content
of an already-read JSON file) and reshape them into the typed row
contracts below; they perform no file or network I/O themselves. Every
row type is a frozen dataclass built from immutable field values —
tuples, not lists — so a produced row can never be mutated through a
reference into the source data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

# A single record as loaded from a registry/JSON source, before this
# module reshapes it into a typed row. Read-only by contract — nothing
# here ever mutates a DashboardSourceRecord.
DashboardSourceRecord = Mapping[str, Any]


@dataclass(frozen=True)
class HeroRow:
    hero_id: str
    dedup_hash: str
    entity_id: str
    entity_name: str
    race: str
    generation: int
    provenance: str
    draw_id: str
    draw_date: str
    official_numeros: tuple[int, ...]
    official_estrelas: tuple[int, ...]
    predicted_numeros: tuple[int, ...]
    predicted_estrelas: tuple[int, ...]
    matched_numbers_count: int
    matched_stars_count: int
    hero_category: str
    hero_tier: str
    registered_at: str | None = None


@dataclass(frozen=True)
class LegendRow:
    legend_id: str
    source_prediction_id: str
    entity_id: str
    entity_name: str
    race: str
    promotion_draw: str
    promotion_draw_date: str
    promotion_threshold: int
    promotion_tier: str
    criteria_version: str
    hero_count: int
    qualified_draws: int
    provenance: str


@dataclass(frozen=True)
class DrawRow:
    numero_sorteio: str
    data: str
    dia_semana: str
    numeros: tuple[int, ...]
    estrelas: tuple[int, ...]
    soma: int
    gaps: tuple[int, ...]
    fase_lua: str | None = None


@dataclass(frozen=True)
class CharacterRow:
    entity_id: str
    nome: str
    raca: str
    titulo: str | None = None
    metodo: str | None = None
    faccao: str | None = None


@dataclass(frozen=True)
class HouseEntry:
    casa: str
    declared_by_races: tuple[str, ...]
    observed_in_population: bool
    source: str  # "lineages.json" | "population_only" | "both"


@dataclass(frozen=True)
class GenerationRow:
    # Shared by Diversidade Genética, Convergência Jaccard and Desempenho
    # Geracional — each sheet reads a different subset of these columns.
    geracao: int
    individuos_total: int
    chaves_unicas: int
    taxa_diversidade: float
    cobertura_numeros: int
    cobertura_estrelas: int
    jaccard_medio_vs_geracao_anterior: float | None = None
    fitness_medio: float | None = None
    fitness_maximo: float | None = None
    fitness_minimo: float | None = None


@dataclass(frozen=True)
class FrequenciesRow:
    valor: int
    tipo: str  # "numero" | "estrela"
    frequencia_absoluta: int
    frequencia_relativa: float
    atraso_atual: int | None = None


@dataclass(frozen=True)
class EconomyPlaceholder:
    investimento: str = "N/D"
    premios: str = "N/D"
    saldo: str = "N/D"
    roi: str = "N/D"
    fonte_financeira: str = "não configurada"
    nota: str = (
        "Dados financeiros indisponíveis no dataset histórico; "
        "scraper opcional existe mas está desativado."
    )


@dataclass(frozen=True)
class ExecutiveSummary:
    total_heroes: int
    total_legends: int
    taxa_sucesso: float | None = None
    diversidade_media: float | None = None
    convergencia_media: float | None = None
    geracoes_analisadas: int = 0
    economia: EconomyPlaceholder = field(default_factory=EconomyPlaceholder)
    gerado_em: str | None = None


@dataclass(frozen=True)
class DashboardDataset:
    executive: ExecutiveSummary
    heroes: tuple[HeroRow, ...]
    legends: tuple[LegendRow, ...]
    key_base: tuple[DrawRow, ...]
    characters: tuple[CharacterRow, ...]
    houses: tuple[HouseEntry, ...]
    generations: tuple[GenerationRow, ...]
    frequencies: tuple[FrequenciesRow, ...]
    economy: EconomyPlaceholder
    methodology: Mapping[str, Any]


# ---------------------------------------------------------------------------
# Heroes / Legends — direct reshape: both source schemas are already
# strict, tested contracts (library/heroes/registry.py,
# library/legends/registry.py), unlike the heterogeneous archive records
# handled by later commits, so no normalization step is needed here.
# ---------------------------------------------------------------------------

def build_heroes_rows(hero_records: Sequence[DashboardSourceRecord]) -> list[HeroRow]:
    """hero_records: the plain list of dicts returned by
    HeroRegistry().load_all() — never a HeroRegistry instance itself.
    """
    rows = []
    for r in hero_records:
        rows.append(HeroRow(
            hero_id=r["hero_id"],
            dedup_hash=r["dedup_hash"],
            entity_id=r["entity_id"],
            entity_name=r["entity_name"],
            race=r["race"],
            generation=r["generation"],
            provenance=r["provenance"],
            draw_id=r["draw_id"],
            draw_date=r["draw_date"],
            official_numeros=tuple(r["official_key"]["numeros"]),
            official_estrelas=tuple(r["official_key"]["estrelas"]),
            predicted_numeros=tuple(r["predicted_key"]["numeros"]),
            predicted_estrelas=tuple(r["predicted_key"]["estrelas"]),
            matched_numbers_count=r["matched_numbers_count"],
            matched_stars_count=r["matched_stars_count"],
            hero_category=r["hero_category"],
            hero_tier=r["hero_tier"],
            registered_at=r.get("registered_at"),
        ))
    return rows


def build_legends_rows(legend_records: Sequence[DashboardSourceRecord]) -> list[LegendRow]:
    """legend_records: the plain list of dicts returned by
    LegendRegistry().load_all() — never a LegendRegistry instance itself.
    Must handle an empty list cleanly (no Legends promoted yet).
    """
    rows = []
    for r in legend_records:
        rows.append(LegendRow(
            legend_id=r["legend_id"],
            source_prediction_id=r["source_prediction_id"],
            entity_id=r["entity_id"],
            entity_name=r["entity_name"],
            race=r["race"],
            promotion_draw=r["promotion_draw"],
            promotion_draw_date=r["promotion_draw_date"],
            promotion_threshold=r["promotion_threshold"],
            promotion_tier=r["promotion_tier"],
            criteria_version=r["criteria_version"],
            hero_count=r["hero_count"],
            qualified_draws=r["qualified_draws"],
            provenance=r["provenance"],
        ))
    return rows


# ---------------------------------------------------------------------------
# Base de Chaves / Personagens — also direct reshape from strict, tested
# canonical sources: the historical dataset (tests/test_historical_dataset.py
# already enforces its schema) and races/*/characters.json.
# ---------------------------------------------------------------------------

def build_key_base_rows(
    draw_records: Sequence[DashboardSourceRecord], year: int = 2026,
) -> list[DrawRow]:
    """draw_records: the `sorteios` list already loaded from a historical
    dataset JSON file (datasets/historical/euromillions/<year>/*.json) —
    the caller reads the file, this function never does.

    Strictly filters to draws whose calendario.ano equals `year` — the
    explicit year field, verified present and consistent with
    numero_sorteio across all 1,965 draws in the canonical dataset
    (2004-2026). Anything outside `year` is excluded, not an error —
    this is a deliberate scope filter (V12.3 covers 2026 only), not a
    correction of malformed data.
    """
    rows = []
    for d in draw_records:
        if d["calendario"]["ano"] != year:
            continue
        rows.append(DrawRow(
            numero_sorteio=d["numero_sorteio"],
            data=d["data"],
            dia_semana=d["dia_semana"],
            numeros=tuple(d["chave"]["numeros"]),
            estrelas=tuple(d["chave"]["estrelas"]),
            soma=d["estatisticas_chave"]["soma_numeros"],
            gaps=tuple(d["estatisticas_chave"]["intervalos_ordenados"]),
            fase_lua=d.get("astronomia", {}).get("fase_lua"),
        ))
    return rows


def build_characters_rows(
    character_files: Sequence[DashboardSourceRecord],
) -> list[CharacterRow]:
    """character_files: the already-loaded content of each
    races/*/characters.json file, one element per race, each shaped
    {"raca": ..., "personagens": [...]} — the caller reads every file,
    this function never does.

    `id`/`nome` are uniform across every race checked and read directly.
    `titulo`/`metodo` are read defensively via .get() since not every
    race's personagens carry `metodo` (some use `linhagem` or
    `especialidade_analitica_futura` instead — neither is part of this
    contract yet). `faccao` is always None here: characters.json does
    not carry a faction reference (that field lives in lineages.json,
    which this function does not read).
    """
    rows = []
    for file_content in character_files:
        raca = file_content["raca"]
        for personagem in file_content["personagens"]:
            rows.append(CharacterRow(
                entity_id=personagem["id"],
                nome=personagem["nome"],
                raca=raca,
                titulo=personagem.get("titulo"),
                metodo=personagem.get("metodo"),
                faccao=None,
            ))
    return rows
