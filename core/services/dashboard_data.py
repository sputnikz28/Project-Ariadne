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
from types import MappingProxyType
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
class EconomyDrawRow:
    """Um por cada sorteio do ano em causa (mesma granularidade de
    DrawRow), lido de estatisticas_financeiras/premios/qualidade_dados no
    dataset histórico oficial. Sorteios sem dado real ficam com None em
    todos os campos económicos — a lacuna fica visível, nunca omitida ou
    estimada.
    """
    numero_sorteio: str
    data: str
    receita_liquida_apostas_eur: float | None
    montante_para_premios_eur: float | None
    percentagem_receita_para_premios: float | None
    previsao_proximo_jackpot_eur: int | None
    registos_portugal: int | None
    combinacoes_registadas_portugal: int | None
    apostas_registadas_portugal: int | None
    combinacoes_por_registo: float | None
    apostas_por_registo: float | None
    receita_media_por_aposta_eur: float | None
    houve_vencedor_1_premio_total: bool | None
    houve_vencedor_1_premio_portugal: bool | None
    total_vencedores_todas_categorias: int | None
    total_vencedores_portugal_todas_categorias: int | None
    dados_financeiros_disponiveis: bool
    categorias_premio_disponiveis: bool


@dataclass(frozen=True)
class EconomySummary:
    """Agregação pura sobre EconomyDrawRow — cada soma/média/mínimo/máximo
    é calculado apenas sobre os sorteios em que esse campo específico é
    real (não-None); um campo sem nenhuma observação real resolve para
    None, nunca para 0 ou uma estimativa. Estrutura nova e aditiva:
    coexiste com EconomyPlaceholder/ExecutiveSummary.economia sem os
    alterar.
    """
    moeda: str
    ano: int
    sorteios_no_periodo: int
    sorteios_com_dados_financeiros: int
    sorteios_com_previsao_jackpot: int
    sorteios_com_vencedor_1_premio_total: int
    sorteios_com_vencedor_1_premio_portugal: int
    receita_liquida_apostas_total_eur: float | None
    montante_para_premios_total_eur: float | None
    percentagem_receita_para_premios_media: float | None
    previsao_jackpot_minimo_eur: int | None
    previsao_jackpot_maximo_eur: int | None
    receita_media_por_aposta_eur_media: float | None
    total_vencedores_todas_categorias_soma: int | None
    total_vencedores_portugal_todas_categorias_soma: int | None
    percentagem_sorteios_com_dados_financeiros: float
    receita_media_por_sorteio_com_dados_eur: float | None
    montante_medio_para_premios_eur: float | None
    jackpot_medio_previsto_eur: float | None
    percentagem_sorteios_com_vencedor_1_premio_total: float
    nota: str


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
    economy_draws: tuple[EconomyDrawRow, ...] = ()
    economy_summary: EconomySummary | None = None


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


# ---------------------------------------------------------------------------
# Economia — mesma fonte e mesmo filtro de ano de build_key_base_rows
# (draw_records: a lista `sorteios` já carregada, nunca lida por este
# módulo). estatisticas_financeiras/premios só têm valores reais para um
# subconjunto dos sorteios de 2026 no dataset atual; qualidade_dados já
# assinala, sorteio a sorteio, se esses dois blocos estão completos —
# essa flag é a fonte de verdade usada aqui, não uma inferência a partir
# dos valores. build_economy_summary nunca substitui um campo ausente por
# uma estimativa: soma/média/mínimo/máximo ignoram os None e resolvem
# para None quando não há nenhuma observação real. Percentagens usam
# como denominador apenas os sorteios em que o campo relevante não é
# None — nunca o total de sorteios, para não confundir "sem dado" com
# "False"/"zero".
# ---------------------------------------------------------------------------

def _sum_or_none(values: Sequence[Any]) -> float | int | None:
    present = [v for v in values if v is not None]
    return sum(present) if present else None


def _mean_or_none(values: Sequence[Any]) -> float | None:
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def _min_or_none(values: Sequence[Any]) -> float | int | None:
    present = [v for v in values if v is not None]
    return min(present) if present else None


def _max_or_none(values: Sequence[Any]) -> float | int | None:
    present = [v for v in values if v is not None]
    return max(present) if present else None


def build_economy_rows(
    draw_records: Sequence[DashboardSourceRecord], year: int = 2026,
) -> list[EconomyDrawRow]:
    """draw_records: a mesma lista `sorteios` recebida por
    build_key_base_rows — já carregada, nunca lida por esta função.

    Mesmo filtro de calendario.ano == year de build_key_base_rows. Uma
    EconomyDrawRow por sorteio no ano (incluindo os sem dado financeiro
    real, com None em todos os campos económicos) — a lacuna fica
    visível em vez de o sorteio desaparecer da lista.
    """
    rows = []
    for d in draw_records:
        if d["calendario"]["ano"] != year:
            continue
        financeiras = d.get("estatisticas_financeiras") or {}
        premios = d.get("premios") or {}
        qualidade = d.get("qualidade_dados") or {}
        rows.append(EconomyDrawRow(
            numero_sorteio=d["numero_sorteio"],
            data=d["data"],
            receita_liquida_apostas_eur=financeiras.get("receita_liquida_apostas_eur"),
            montante_para_premios_eur=financeiras.get("montante_para_premios_eur"),
            percentagem_receita_para_premios=financeiras.get("percentagem_receita_para_premios"),
            previsao_proximo_jackpot_eur=financeiras.get("previsao_1_premio_com_jackpot_eur"),
            registos_portugal=financeiras.get("registos_portugal"),
            combinacoes_registadas_portugal=financeiras.get("combinacoes_registadas_portugal"),
            apostas_registadas_portugal=financeiras.get("apostas_registadas_portugal"),
            combinacoes_por_registo=financeiras.get("combinacoes_por_registo"),
            apostas_por_registo=financeiras.get("apostas_por_registo"),
            receita_media_por_aposta_eur=financeiras.get("receita_media_por_aposta_eur"),
            houve_vencedor_1_premio_total=premios.get("houve_vencedor_1_premio_total"),
            houve_vencedor_1_premio_portugal=premios.get("houve_vencedor_1_premio_portugal"),
            total_vencedores_todas_categorias=premios.get("total_vencedores_todas_categorias"),
            total_vencedores_portugal_todas_categorias=premios.get("total_vencedores_portugal_todas_categorias"),
            dados_financeiros_disponiveis=bool(qualidade.get("dados_financeiros_disponiveis")),
            categorias_premio_disponiveis=bool(qualidade.get("categorias_premio_disponiveis")),
        ))
    return rows


def build_economy_summary(
    rows: Sequence[EconomyDrawRow], year: int = 2026, moeda: str = "EUR",
) -> EconomySummary:
    """Pura — sem I/O. `rows`: o resultado já construído de
    build_economy_rows. `year`/`moeda` são aceites verbatim do chamador
    (este módulo nunca lê o dataset nem assume uma moeda por omissão
    silenciosa) apenas para rotular o resultado; não influenciam nenhum
    cálculo.
    """
    rows = list(rows)
    total = len(rows)
    n_com_dados = sum(1 for r in rows if r.dados_financeiros_disponiveis)

    receitas = [r.receita_liquida_apostas_eur for r in rows]
    montantes = [r.montante_para_premios_eur for r in rows]
    percentagens = [r.percentagem_receita_para_premios for r in rows]
    jackpots = [r.previsao_proximo_jackpot_eur for r in rows]
    receitas_media_aposta = [r.receita_media_por_aposta_eur for r in rows]
    total_vencedores = [r.total_vencedores_todas_categorias for r in rows]
    total_vencedores_pt = [r.total_vencedores_portugal_todas_categorias for r in rows]

    n_com_jackpot = sum(1 for j in jackpots if j is not None)
    n_com_vencedor_total = sum(1 for r in rows if r.houve_vencedor_1_premio_total is True)
    n_com_vencedor_pt = sum(1 for r in rows if r.houve_vencedor_1_premio_portugal is True)

    # Denominador da percentagem de vencedores: só os sorteios em que
    # houve_vencedor_1_premio_total NÃO é None — None significa "sem
    # dado", nunca "não houve vencedor". A maioria dos sorteios do ano
    # não tem este campo preenchido; incluí-los no denominador
    # interpretaria a ausência de dado como um "False" fabricado.
    n_com_flag_vencedor_total = sum(1 for r in rows if r.houve_vencedor_1_premio_total is not None)

    return EconomySummary(
        moeda=moeda,
        ano=year,
        sorteios_no_periodo=total,
        sorteios_com_dados_financeiros=n_com_dados,
        sorteios_com_previsao_jackpot=n_com_jackpot,
        sorteios_com_vencedor_1_premio_total=n_com_vencedor_total,
        sorteios_com_vencedor_1_premio_portugal=n_com_vencedor_pt,
        receita_liquida_apostas_total_eur=_sum_or_none(receitas),
        montante_para_premios_total_eur=_sum_or_none(montantes),
        percentagem_receita_para_premios_media=_mean_or_none(percentagens),
        previsao_jackpot_minimo_eur=_min_or_none(jackpots),
        previsao_jackpot_maximo_eur=_max_or_none(jackpots),
        receita_media_por_aposta_eur_media=_mean_or_none(receitas_media_aposta),
        total_vencedores_todas_categorias_soma=_sum_or_none(total_vencedores),
        total_vencedores_portugal_todas_categorias_soma=_sum_or_none(total_vencedores_pt),
        percentagem_sorteios_com_dados_financeiros=(n_com_dados / total * 100) if total else 0.0,
        receita_media_por_sorteio_com_dados_eur=_mean_or_none(receitas),
        montante_medio_para_premios_eur=_mean_or_none(montantes),
        jackpot_medio_previsto_eur=_mean_or_none(jackpots),
        percentagem_sorteios_com_vencedor_1_premio_total=(
            (n_com_vencedor_total / n_com_flag_vencedor_total * 100)
            if n_com_flag_vencedor_total else 0.0
        ),
        nota=(
            f"Dados financeiros reais disponíveis para {n_com_dados} de {total} "
            f"sorteios de {year} (estatisticas_financeiras/premios completos, "
            "confirmado por qualidade_dados). Os restantes sorteios ficam com "
            "None nos campos económicos — nunca estimados."
        ),
    )


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


# ---------------------------------------------------------------------------
# Normalização (privada, genérica) — contrato interno reutilizável por
# qualquer builder que precise de ler registos heterogéneos de arquivo
# (população, gerações, frequências, etc.). Não foi desenhada a pensar em
# Houses especificamente: is_valid reflete a completude do contrato comum,
# não uma necessidade de um builder concreto. Nunca levanta exceção.
# ---------------------------------------------------------------------------

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "id": ("id",),
    "nome": ("nome", "name"),
    "raca": ("raca",),
    "casa": ("casa",),
    "geracao": ("geracao", "generation"),
}
_COMMON_FIELDS: tuple[str, ...] = tuple(_FIELD_ALIASES)


def _resolve_alias(record: Mapping, canonical: str) -> tuple[str | None, Any]:
    """Returns (alias_key_used, raw_value) for the first key present in
    record among _FIELD_ALIASES[canonical], checked in precedence order —
    the canonical Portuguese name always wins if it exists at all, even
    empty; an alias is only consulted when the canonical key is entirely
    absent. (None, None) if none of the aliases are present.
    """
    for alias in _FIELD_ALIASES[canonical]:
        if alias in record:
            return alias, record[alias]
    return None, None


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return len(value) == 0
    return False


@dataclass(frozen=True)
class _NormalizedIndividual:
    entity_id: str | None
    nome: str | None
    raca: str | None
    casa: str | None
    geracao: int | None
    is_valid: bool
    missing_fields: tuple[str, ...]
    source_index: int
    extra: Mapping[str, Any]


@dataclass(frozen=True)
class _NormalizationResult:
    individuals: tuple[_NormalizedIndividual, ...]
    warnings: tuple[str, ...]


def _normalize_individual_record(record: Any, index: int) -> _NormalizedIndividual:
    """Never raises. `record` é um elemento já carregado, de forma e
    origem arbitrárias, de qualquer arquivo de população. `is_valid` só é
    True se todos os _COMMON_FIELDS estiverem presentes e não-vazios —
    reflete a completude do registo, não uma regra específica de Houses.
    """
    if not isinstance(record, Mapping):
        return _NormalizedIndividual(
            entity_id=None, nome=None, raca=None, casa=None, geracao=None,
            is_valid=False,
            missing_fields=(f"registo inválido: esperado mapeamento, recebido {type(record).__name__}",),
            source_index=index,
            extra=MappingProxyType({}),
        )

    missing = []
    resolved: dict[str, Any] = {}
    consumed_keys: set[str] = set()
    for canonical in _COMMON_FIELDS:
        alias_used, raw_value = _resolve_alias(record, canonical)
        if alias_used is None:
            missing.append(f"{canonical} (ausente)")
            resolved[canonical] = None
            continue
        consumed_keys.add(alias_used)
        resolved[canonical] = raw_value
        if _is_empty(raw_value):
            missing.append(f"{canonical} (vazio)")

    return _NormalizedIndividual(
        entity_id=resolved["id"],
        nome=resolved["nome"],
        raca=resolved["raca"],
        casa=resolved["casa"],
        geracao=resolved["geracao"],
        is_valid=not missing,
        missing_fields=tuple(missing),
        source_index=index,
        extra=MappingProxyType({k: v for k, v in record.items() if k not in consumed_keys}),
    )


def _normalize_archive(records: Sequence[Any]) -> _NormalizationResult:
    individuals = []
    warnings = []
    for index, record in enumerate(records):
        normalized = _normalize_individual_record(record, index)
        individuals.append(normalized)
        for issue in normalized.missing_fields:
            ident = normalized.entity_id or f"índice {normalized.source_index}"
            warnings.append(f"registo {ident}: {issue}")
    return _NormalizationResult(
        individuals=tuple(individuals),
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Casas — cruza casas declaradas (races/*/lineages.json) com casas
# observadas na população. Só esta função é específica de Houses; usa
# apenas o campo `casa` de cada indivíduo normalizado (independentemente
# de `is_valid`), e não devolve os warnings de _normalize_archive — esses
# pertencem exclusivamente ao contrato interno, verificado pelos testes
# desta camada.
# ---------------------------------------------------------------------------

def build_houses(
    lineage_files: Sequence[DashboardSourceRecord],
    archive_records: Sequence[Any],
) -> list[HouseEntry]:
    """lineage_files: conteúdo já lido de cada races/<raça>/lineages.json
    (um dict por raça, com 'raca' e, ao nível de topo, ou 'casa' [string
    única] ou 'casas' [string única, ou lista/tuple/set/frozenset de
    strings, quando a raça declara mais do que uma]).
    archive_records: uma sequência já carregada de registos de população —
    a origem exata é irrelevante para esta função; cada registo passa por
    _normalize_archive antes de ser usado.
    """
    declared: dict[str, set[str]] = {}
    for file_content in lineage_files:
        if not isinstance(file_content, Mapping):
            continue
        raca = file_content.get("raca")
        if not raca:
            continue

        casas_field = file_content.get("casas")
        if casas_field is None:
            casas_field = file_content.get("casa")

        if isinstance(casas_field, str):
            candidates = [casas_field]
        elif isinstance(casas_field, (list, tuple, set, frozenset)):
            candidates = list(casas_field)
        else:
            candidates = []

        for casa in candidates:
            if not isinstance(casa, str):
                continue
            casa = casa.strip()
            if not casa:
                continue
            declared.setdefault(casa, set()).add(raca)

    normalization = _normalize_archive(archive_records)
    observed_casas = {ind.casa for ind in normalization.individuals if ind.casa}

    rows = []
    for casa in sorted(declared.keys() | observed_casas):
        races = tuple(sorted(declared.get(casa, ())))
        observed = casa in observed_casas
        source = "both" if races and observed else "lineages.json" if races else "population_only"
        rows.append(HouseEntry(
            casa=casa,
            declared_by_races=races,
            observed_in_population=observed,
            source=source,
        ))
    return rows


# ---------------------------------------------------------------------------
# Executive Summary / Dashboard Dataset — pure composition of rows already
# produced by the other builders in this module. Neither function computes
# any new statistic: total_heroes/total_legends are counts of the rows
# handed in, and everything else in ExecutiveSummary that would require
# Generations/Frequencies data (taxa_sucesso, diversidade_media,
# convergencia_media, geracoes_analisadas beyond its zero default) is left
# at its dataclass default until a real producer for that data exists —
# see CLAUDE.md, Commit 5 scope note. `gerado_em` is accepted verbatim from
# the caller; this module never reads a clock itself.
# ---------------------------------------------------------------------------

def build_executive_summary(
    heroes: Sequence[HeroRow],
    legends: Sequence[LegendRow],
    economy: EconomyPlaceholder | None = None,
    gerado_em: str | None = None,
) -> ExecutiveSummary:
    return ExecutiveSummary(
        total_heroes=len(heroes),
        total_legends=len(legends),
        economia=economy if economy is not None else EconomyPlaceholder(),
        gerado_em=gerado_em,
    )


def build_dashboard_dataset(
    heroes: Sequence[HeroRow],
    legends: Sequence[LegendRow],
    key_base: Sequence[DrawRow],
    characters: Sequence[CharacterRow],
    houses: Sequence[HouseEntry],
    generations: Sequence[GenerationRow] = (),
    frequencies: Sequence[FrequenciesRow] = (),
    economy: EconomyPlaceholder | None = None,
    methodology: Mapping[str, Any] | None = None,
    gerado_em: str | None = None,
    economy_draws: Sequence[EconomyDrawRow] = (),
    economy_summary: EconomySummary | None = None,
) -> DashboardDataset:
    """Assembles rows already built by the other functions in this module
    (build_heroes_rows, build_legends_rows, build_key_base_rows,
    build_characters_rows, build_houses, build_economy_rows /
    build_economy_summary, and — once they exist — their
    Generations/Frequencies counterparts) into one DashboardDataset. Never
    calls those builders itself, never reads a file, never touches a
    Registry — every argument here is already-built data handed in by the
    caller.

    economy_draws/economy_summary are new and purely additive: they
    default to ()/None and never touch economy/economia
    (EconomyPlaceholder), which keeps every existing caller and test
    byte-identical.
    """
    resolved_economy = economy if economy is not None else EconomyPlaceholder()
    return DashboardDataset(
        executive=build_executive_summary(
            heroes,
            legends,
            economy=resolved_economy,
            gerado_em=gerado_em,
        ),
        heroes=tuple(heroes),
        legends=tuple(legends),
        key_base=tuple(key_base),
        characters=tuple(characters),
        houses=tuple(houses),
        generations=tuple(generations),
        frequencies=tuple(frequencies),
        economy=resolved_economy,
        methodology=MappingProxyType(dict(methodology)) if methodology is not None else MappingProxyType({}),
        economy_draws=tuple(economy_draws),
        economy_summary=economy_summary,
    )
