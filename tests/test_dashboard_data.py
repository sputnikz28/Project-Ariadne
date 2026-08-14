"""Tests for core/services/dashboard_data.py — Heroes, Legends, Base de
Chaves and Personagens row builders. No HeroRegistry/LegendRegistry
involved anywhere here — only plain dicts, matching the module's
contract that it never touches the registries or disk itself.
"""

import dataclasses
import json
import unittest
from pathlib import Path
from types import MappingProxyType

from core.services.dashboard_data import (
    CharacterRow,
    DrawRow,
    EconomyDrawRow,
    EconomyPlaceholder,
    EconomySummary,
    HeroRow,
    HouseEntry,
    LegendRow,
    PrizeCategoryAggregate,
    PrizeCategoryRow,
    PrizeCategorySummary,
    _is_empty,
    _NormalizationResult,
    _NormalizedIndividual,
    _normalize_archive,
    _normalize_individual_record,
    _PRIZE_CATEGORY_LABELS,
    build_characters_rows,
    build_dashboard_dataset,
    build_economy_rows,
    build_economy_summary,
    build_executive_summary,
    build_heroes_rows,
    build_houses,
    build_key_base_rows,
    build_legends_rows,
    build_prize_category_rows,
    build_prize_category_summary,
)

REAL_2026_DATASET_PATH = Path(
    "datasets/historical/euromillions/2026/euromilhoes_2026_001_062_dataset_completo.json"
)


def make_hero_record(**overrides):
    record = {
        "hero_id": "HERO-2026-057-000149f4",
        "dedup_hash": "000149f4a97a6dd335f44a53ff431b463b3037e9f28c1fae4ca1a24b628f0a5c",
        "entity_id": "H-00017",
        "entity_name": "Morgana da Lua Fria",
        "race": "Chefe Tribal",
        "generation": 1,
        "provenance": "legacy",
        "draw_id": "057/2026",
        "draw_date": "2026-07-17",
        "official_key": {"numeros": [12, 21, 23, 34, 40], "estrelas": [9, 10]},
        "predicted_key": {"numeros": [12, 36, 40, 45, 50], "estrelas": [5, 10]},
        "matched_numbers_count": 2,
        "matched_stars_count": 1,
        "hero_category": "2+1",
        "hero_tier": "TIER_5",
        "registered_at": "2026-07-22T09:09:33+00:00",
    }
    record.update(overrides)
    return record


def make_legend_record(**overrides):
    record = {
        "legend_id": "LEGEND-395e24e0",
        "source_prediction_id": "395e24e0eafd0f7a6f07684d4849e82903bb25e6cbf9535265f4a9b35119a807",
        "entity_id": "H-00017",
        "entity_name": "Morgana da Lua Fria",
        "race": "Chefe Tribal",
        "promotion_draw": "058/2026",
        "promotion_draw_date": "2026-07-21",
        "promotion_threshold": 3,
        "promotion_tier": "LEGEND_TIER_4",
        "criteria_version": "v1",
        "hero_count": 3,
        "qualified_draws": 3,
        "provenance": "legacy",
    }
    record.update(overrides)
    return record


def make_draw_record(**overrides):
    record = {
        "numero_sorteio": "057/2026",
        "data": "2026-07-17",
        "dia_semana": "sexta-feira",
        "calendario": {"ano": 2026},
        "chave": {"numeros": [12, 21, 23, 34, 40], "estrelas": [9, 10]},
        "estatisticas_chave": {"soma_numeros": 130, "intervalos_ordenados": [9, 2, 11, 6]},
        "astronomia": {"fase_lua": "Lua crescente côncava"},
    }
    record.update(overrides)
    return record


def make_character_file(**overrides):
    file_content = {
        "raca": "Clérigos",
        "personagens": [
            {
                "id": "bruxa_arquetipo",
                "nome": "Bruxa",
                "titulo": "Linhagem da Mistura",
                "biografia": "...",
                "personalidade": "...",
                "artefactos_preferidos": [],
                "metodo": "Combina números quentes, frios e um número aleatório.",
            },
        ],
    }
    file_content.update(overrides)
    return file_content


class TestBuildHeroesRows(unittest.TestCase):
    def test_maps_fields_correctly(self):
        rows = build_heroes_rows([make_hero_record()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.hero_id, "HERO-2026-057-000149f4")
        self.assertEqual(row.entity_name, "Morgana da Lua Fria")
        self.assertEqual(row.official_numeros, (12, 21, 23, 34, 40))
        self.assertEqual(row.official_estrelas, (9, 10))
        self.assertEqual(row.predicted_numeros, (12, 36, 40, 45, 50))
        self.assertEqual(row.predicted_estrelas, (5, 10))
        self.assertEqual(row.matched_numbers_count, 2)
        self.assertEqual(row.hero_tier, "TIER_5")
        self.assertEqual(row.registered_at, "2026-07-22T09:09:33+00:00")

    def test_key_fields_are_tuples_not_lists(self):
        row = build_heroes_rows([make_hero_record()])[0]
        for field_name in ("official_numeros", "official_estrelas", "predicted_numeros", "predicted_estrelas"):
            self.assertIsInstance(getattr(row, field_name), tuple)

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(build_heroes_rows([]), [])

    def test_missing_registered_at_defaults_to_none(self):
        record = make_hero_record()
        del record["registered_at"]
        row = build_heroes_rows([record])[0]
        self.assertIsNone(row.registered_at)

    def test_row_is_frozen(self):
        row = build_heroes_rows([make_hero_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.hero_id = "changed"

    def test_mutating_source_record_after_build_does_not_affect_row(self):
        record = make_hero_record()
        row = build_heroes_rows([record])[0]
        record["official_key"]["numeros"].append(999)  # mutate the source list in place
        self.assertEqual(row.official_numeros, (12, 21, 23, 34, 40))  # row unaffected


class TestBuildLegendsRows(unittest.TestCase):
    def test_maps_fields_correctly(self):
        rows = build_legends_rows([make_legend_record()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.legend_id, "LEGEND-395e24e0")
        self.assertEqual(row.promotion_threshold, 3)
        self.assertEqual(row.promotion_tier, "LEGEND_TIER_4")
        self.assertEqual(row.criteria_version, "v1")
        self.assertEqual(row.provenance, "legacy")

    def test_empty_list_handled_cleanly(self):
        # No Legends promoted yet in the real project — this must not
        # raise or behave differently from a populated list.
        self.assertEqual(build_legends_rows([]), [])

    def test_row_is_frozen(self):
        row = build_legends_rows([make_legend_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.provenance = "verified"

    def test_multiple_records_preserve_order(self):
        r1 = make_legend_record(legend_id="LEGEND-aaa")
        r2 = make_legend_record(legend_id="LEGEND-bbb")
        rows = build_legends_rows([r1, r2])
        self.assertEqual([r.legend_id for r in rows], ["LEGEND-aaa", "LEGEND-bbb"])


class TestBuildKeyBaseRows(unittest.TestCase):
    def test_maps_fields_correctly(self):
        rows = build_key_base_rows([make_draw_record()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.numero_sorteio, "057/2026")
        self.assertEqual(row.data, "2026-07-17")
        self.assertEqual(row.dia_semana, "sexta-feira")
        self.assertEqual(row.numeros, (12, 21, 23, 34, 40))
        self.assertEqual(row.estrelas, (9, 10))
        self.assertEqual(row.soma, 130)
        self.assertEqual(row.gaps, (9, 2, 11, 6))
        self.assertEqual(row.fase_lua, "Lua crescente côncava")

    def test_filter_uses_calendario_ano_not_numero_sorteio(self):
        # numero_sorteio has an unexpected/malformed shape, but
        # calendario.ano is correct — the draw must still be included.
        record = make_draw_record(numero_sorteio="???", calendario={"ano": 2026})
        rows = build_key_base_rows([record], year=2026)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].numero_sorteio, "???")

    def test_draws_from_other_years_are_excluded(self):
        draw_2025 = make_draw_record(numero_sorteio="104/2025", calendario={"ano": 2025})
        draw_2026 = make_draw_record(numero_sorteio="057/2026", calendario={"ano": 2026})
        rows = build_key_base_rows([draw_2025, draw_2026], year=2026)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].numero_sorteio, "057/2026")

    def test_numero_sorteio_year_suffix_is_irrelevant_to_the_filter(self):
        # Even if numero_sorteio LOOKS like it belongs to `year` by its
        # suffix, only calendario.ano decides inclusion.
        record = make_draw_record(numero_sorteio="001/2026", calendario={"ano": 2025})
        rows = build_key_base_rows([record], year=2026)
        self.assertEqual(rows, [])

    def test_gaps_and_key_fields_are_tuples(self):
        row = build_key_base_rows([make_draw_record()])[0]
        self.assertIsInstance(row.numeros, tuple)
        self.assertIsInstance(row.estrelas, tuple)
        self.assertIsInstance(row.gaps, tuple)

    def test_missing_astronomia_defaults_fase_lua_to_none(self):
        record = make_draw_record()
        del record["astronomia"]
        row = build_key_base_rows([record])[0]
        self.assertIsNone(row.fase_lua)

    def test_mutating_source_record_after_build_does_not_affect_row(self):
        record = make_draw_record()
        row = build_key_base_rows([record])[0]
        record["chave"]["numeros"].append(999)
        self.assertEqual(row.numeros, (12, 21, 23, 34, 40))

    def test_row_is_frozen(self):
        row = build_key_base_rows([make_draw_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.soma = 0


# Real values copied verbatim from datasets/historical/euromillions/2026/
# euromilhoes_2026_001_061_dataset_completo.json, draw 040/2026 — the
# first of the 15 draws with a complete estatisticas_financeiras/premios
# block (qualidade_dados.dados_financeiros_disponiveis=true).
def make_complete_economy_record(**overrides):
    record = make_draw_record(
        numero_sorteio="040/2026",
        data="2026-05-19",
        estatisticas_financeiras={
            "receita_liquida_apostas_eur": 44929255.8,
            "montante_para_premios_eur": 22464627.9,
            "percentagem_receita_para_premios": 50.0,
            "previsao_1_premio_com_jackpot_eur": 105000000,
            "registos_portugal": 872428,
            "combinacoes_registadas_portugal": 1416011,
            "apostas_registadas_portugal": 1514096,
            "combinacoes_por_registo": 1.623069,
            "apostas_por_registo": 1.735497,
            "receita_media_por_aposta_eur": 29.673981,
        },
        premios={
            "categorias": [],
            "houve_vencedor_1_premio_total": False,
            "houve_vencedor_1_premio_portugal": False,
            "total_vencedores_todas_categorias": 1536999,
            "total_vencedores_portugal_todas_categorias": 114363,
        },
        qualidade_dados={
            "dados_financeiros_disponiveis": True,
            "categorias_premio_disponiveis": True,
            "campos_em_falta": [],
        },
    )
    record.update(overrides)
    return record


# Real values copied verbatim from draw 055/2026 — the genuine partial
# case: only previsao_1_premio_com_jackpot_eur is populated, every other
# financial field is null, and qualidade_dados.dados_financeiros_disponiveis
# is explicitly false (not inferred — the dataset states it directly).
def make_partial_economy_record(**overrides):
    record = make_draw_record(
        numero_sorteio="055/2026",
        data="2026-06-12",
        estatisticas_financeiras={
            "receita_liquida_apostas_eur": None,
            "montante_para_premios_eur": None,
            "percentagem_receita_para_premios": None,
            "previsao_1_premio_com_jackpot_eur": 29000000,
            "registos_portugal": None,
            "combinacoes_registadas_portugal": None,
            "apostas_registadas_portugal": None,
            "combinacoes_por_registo": None,
            "apostas_por_registo": None,
            "receita_media_por_aposta_eur": None,
        },
        premios={
            "categorias": None,
            "houve_vencedor_1_premio_total": None,
            "houve_vencedor_1_premio_portugal": None,
            "total_vencedores_todas_categorias": None,
            "total_vencedores_portugal_todas_categorias": None,
        },
        qualidade_dados={
            "dados_financeiros_disponiveis": False,
            "categorias_premio_disponiveis": False,
            "campos_em_falta": ["receita_liquida_apostas_eur", "montante_para_premios_eur", "categorias_premio"],
        },
    )
    record.update(overrides)
    return record


class TestBuildEconomyRows(unittest.TestCase):
    def test_maps_all_fields_from_a_complete_draw(self):
        row = build_economy_rows([make_complete_economy_record()])[0]
        self.assertEqual(row.numero_sorteio, "040/2026")
        self.assertEqual(row.data, "2026-05-19")
        self.assertEqual(row.receita_liquida_apostas_eur, 44929255.8)
        self.assertEqual(row.montante_para_premios_eur, 22464627.9)
        self.assertEqual(row.percentagem_receita_para_premios, 50.0)
        self.assertEqual(row.previsao_proximo_jackpot_eur, 105000000)
        self.assertEqual(row.registos_portugal, 872428)
        self.assertEqual(row.combinacoes_registadas_portugal, 1416011)
        self.assertEqual(row.apostas_registadas_portugal, 1514096)
        self.assertEqual(row.combinacoes_por_registo, 1.623069)
        self.assertEqual(row.apostas_por_registo, 1.735497)
        self.assertEqual(row.receita_media_por_aposta_eur, 29.673981)
        self.assertIs(row.houve_vencedor_1_premio_total, False)
        self.assertIs(row.houve_vencedor_1_premio_portugal, False)
        self.assertEqual(row.total_vencedores_todas_categorias, 1536999)
        self.assertEqual(row.total_vencedores_portugal_todas_categorias, 114363)
        self.assertIs(row.dados_financeiros_disponiveis, True)
        self.assertIs(row.categorias_premio_disponiveis, True)

    def test_year_filter_matches_build_key_base_rows(self):
        draw_2025 = make_draw_record(numero_sorteio="104/2025", calendario={"ano": 2025})
        draw_2026 = make_complete_economy_record()
        rows = build_economy_rows([draw_2025, draw_2026], year=2026)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].numero_sorteio, "040/2026")

    def test_draw_without_any_economic_block_produces_row_with_all_none(self):
        row = build_economy_rows([make_draw_record()])[0]
        self.assertEqual(row.numero_sorteio, "057/2026")
        for field_name in (
            "receita_liquida_apostas_eur", "montante_para_premios_eur",
            "percentagem_receita_para_premios", "previsao_proximo_jackpot_eur",
            "registos_portugal", "combinacoes_registadas_portugal",
            "apostas_registadas_portugal", "combinacoes_por_registo",
            "apostas_por_registo", "receita_media_por_aposta_eur",
            "houve_vencedor_1_premio_total", "houve_vencedor_1_premio_portugal",
            "total_vencedores_todas_categorias", "total_vencedores_portugal_todas_categorias",
        ):
            with self.subTest(field=field_name):
                self.assertIsNone(getattr(row, field_name))
        self.assertIs(row.dados_financeiros_disponiveis, False)
        self.assertIs(row.categorias_premio_disponiveis, False)

    def test_partial_055_style_draw_is_preserved_not_dropped(self):
        rows = build_economy_rows([make_partial_economy_record()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.numero_sorteio, "055/2026")
        self.assertEqual(row.previsao_proximo_jackpot_eur, 29000000)
        self.assertIsNone(row.receita_liquida_apostas_eur)
        self.assertIsNone(row.montante_para_premios_eur)
        self.assertIsNone(row.houve_vencedor_1_premio_total)
        self.assertIs(row.dados_financeiros_disponiveis, False)
        self.assertIs(row.categorias_premio_disponiveis, False)

    def test_row_is_frozen(self):
        row = build_economy_rows([make_draw_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.receita_liquida_apostas_eur = 0.0


class TestBuildEconomySummary(unittest.TestCase):
    def test_no_real_observations_returns_all_none_and_zero_percentages(self):
        rows = build_economy_rows([make_draw_record(), make_draw_record(numero_sorteio="058/2026")])
        summary = build_economy_summary(rows, year=2026)
        self.assertEqual(summary.sorteios_no_periodo, 2)
        self.assertEqual(summary.sorteios_com_dados_financeiros, 0)
        for field_name in (
            "receita_liquida_apostas_total_eur", "montante_para_premios_total_eur",
            "percentagem_receita_para_premios_media", "previsao_jackpot_minimo_eur",
            "previsao_jackpot_maximo_eur", "receita_media_por_aposta_eur_media",
            "total_vencedores_todas_categorias_soma", "total_vencedores_portugal_todas_categorias_soma",
            "receita_media_por_sorteio_com_dados_eur", "montante_medio_para_premios_eur",
            "jackpot_medio_previsto_eur",
        ):
            with self.subTest(field=field_name):
                self.assertIsNone(getattr(summary, field_name))
        # Coverage percentages are real 0/N computations, not fabricated —
        # both denominators exist (2 draws), just zero draws qualify.
        self.assertEqual(summary.percentagem_sorteios_com_dados_financeiros, 0.0)
        self.assertEqual(summary.percentagem_sorteios_com_vencedor_1_premio_total, 0.0)

    def test_percentagem_vencedores_uses_only_non_none_flags(self):
        # 3 draws: one real winner, one real non-winner, one with no data
        # at all (houve_vencedor_1_premio_total is None). The percentage
        # must be computed over the 2 draws with a real flag (1/2 = 50%),
        # never over all 3 (which would wrongly read as 1/3).
        winner = make_complete_economy_record(numero_sorteio="040/2026")
        non_winner = make_complete_economy_record(
            numero_sorteio="041/2026",
            premios={
                "categorias": [],
                "houve_vencedor_1_premio_total": True,
                "houve_vencedor_1_premio_portugal": False,
                "total_vencedores_todas_categorias": 1,
                "total_vencedores_portugal_todas_categorias": 0,
            },
        )
        no_data = make_draw_record(numero_sorteio="042/2026")
        rows = build_economy_rows([winner, non_winner, no_data], year=2026)
        summary = build_economy_summary(rows, year=2026)
        self.assertEqual(summary.sorteios_com_vencedor_1_premio_total, 1)
        self.assertEqual(summary.percentagem_sorteios_com_vencedor_1_premio_total, 50.0)

    def test_cobertura_financeira_usa_qualidade_dados_nao_valores_inferidos(self):
        # The partial 055/2026-style draw HAS a non-null economic field
        # (previsao_proximo_jackpot_eur) but its own qualidade_dados says
        # dados_financeiros_disponiveis=False — it must NOT count toward
        # coverage, since coverage reflects the dataset's own honesty
        # flag, not "does at least one field happen to be non-null".
        rows = build_economy_rows([make_partial_economy_record(), make_draw_record()], year=2026)
        summary = build_economy_summary(rows, year=2026)
        self.assertEqual(summary.sorteios_no_periodo, 2)
        self.assertEqual(summary.sorteios_com_dados_financeiros, 0)
        self.assertEqual(summary.percentagem_sorteios_com_dados_financeiros, 0.0)
        # But the jackpot forecast itself is still real data and must be
        # picked up by the jackpot-specific aggregates.
        self.assertEqual(summary.sorteios_com_previsao_jackpot, 1)
        self.assertEqual(summary.jackpot_medio_previsto_eur, 29000000)

    def test_real_values_from_two_complete_draws(self):
        # Two real, hand-verified draws (040/2026 and 041/2026) — sums,
        # means, min and max must match direct arithmetic on the source
        # values, not an estimate.
        draw_040 = make_complete_economy_record()
        draw_041 = make_complete_economy_record(
            numero_sorteio="041/2026",
            data="2026-05-22",
            estatisticas_financeiras={
                "receita_liquida_apostas_eur": 60524917.2,
                "montante_para_premios_eur": 30262458.6,
                "percentagem_receita_para_premios": 50.0,
                "previsao_1_premio_com_jackpot_eur": 115000000,
                "registos_portugal": 1275641,
                "combinacoes_registadas_portugal": 2142202,
                "apostas_registadas_portugal": 2285779,
                "combinacoes_por_registo": 1.679314,
                "apostas_por_registo": 1.791867,
                "receita_media_por_aposta_eur": 26.478902,
            },
            premios={
                "categorias": [],
                "houve_vencedor_1_premio_total": False,
                "houve_vencedor_1_premio_portugal": False,
                "total_vencedores_todas_categorias": 2138223,
                "total_vencedores_portugal_todas_categorias": 176873,
            },
        )
        rows = build_economy_rows([draw_040, draw_041], year=2026)
        summary = build_economy_summary(rows, year=2026)
        self.assertAlmostEqual(summary.receita_liquida_apostas_total_eur, 44929255.8 + 60524917.2, places=2)
        self.assertAlmostEqual(summary.montante_para_premios_total_eur, 22464627.9 + 30262458.6, places=2)
        self.assertEqual(summary.previsao_jackpot_minimo_eur, 105000000)
        self.assertEqual(summary.previsao_jackpot_maximo_eur, 115000000)
        self.assertEqual(summary.total_vencedores_todas_categorias_soma, 1536999 + 2138223)
        self.assertEqual(summary.total_vencedores_portugal_todas_categorias_soma, 114363 + 176873)
        self.assertEqual(summary.sorteios_com_dados_financeiros, 2)
        self.assertEqual(summary.percentagem_sorteios_com_dados_financeiros, 100.0)

    def test_moeda_and_ano_are_passed_through_verbatim(self):
        summary = build_economy_summary([], year=2026, moeda="EUR")
        self.assertEqual(summary.ano, 2026)
        self.assertEqual(summary.moeda, "EUR")

    def test_result_is_frozen(self):
        summary = build_economy_summary([], year=2026)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            summary.moeda = "USD"


@unittest.skipUnless(REAL_2026_DATASET_PATH.exists(), "real 2026 dataset not present in this checkout")
class TestBuildEconomyRealDataset(unittest.TestCase):
    """Cross-checks build_economy_rows/build_economy_summary against the
    actual datasets/historical/euromillions/2026/... file — read-only,
    never modified by this test. Expected numbers were computed directly
    from that file (see investigation notes for Commit 7) and are
    re-verified here so a future edit to the dataset that silently
    changes these real figures fails this test instead of going unnoticed.
    """

    @classmethod
    def setUpClass(cls):
        data = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        cls.sorteios = data["sorteios"]
        cls.rows = build_economy_rows(cls.sorteios, year=2026)
        cls.summary = build_economy_summary(cls.rows, year=2026, moeda=data["moeda"])

    def test_one_row_per_draw_in_2026(self):
        self.assertEqual(len(self.rows), 62)

    def test_coverage_matches_qualidade_dados(self):
        self.assertEqual(self.summary.sorteios_com_dados_financeiros, 15)
        self.assertAlmostEqual(self.summary.percentagem_sorteios_com_dados_financeiros, 24.193548387096776, places=6)

    def test_jackpot_forecast_coverage_and_range(self):
        self.assertEqual(self.summary.sorteios_com_previsao_jackpot, 15)
        self.assertEqual(self.summary.previsao_jackpot_minimo_eur, 17000000)
        self.assertEqual(self.summary.previsao_jackpot_maximo_eur, 174000000)

    def test_totals_match_direct_sum_over_the_real_dataset(self):
        self.assertAlmostEqual(self.summary.receita_liquida_apostas_total_eur, 788128343.2, places=1)
        self.assertAlmostEqual(self.summary.montante_para_premios_total_eur, 394064171.6, places=1)
        self.assertEqual(self.summary.total_vencedores_todas_categorias_soma, 27951947)
        self.assertEqual(self.summary.total_vencedores_portugal_todas_categorias_soma, 2088723)

    def test_winner_percentage_denominator_excludes_draws_without_the_flag(self):
        # Exactly 15 draws carry a real houve_vencedor_1_premio_total
        # flag (True or False); 2 of those are True.
        self.assertEqual(self.summary.sorteios_com_vencedor_1_premio_total, 2)
        self.assertAlmostEqual(
            self.summary.percentagem_sorteios_com_vencedor_1_premio_total, 2 / 15 * 100, places=6,
        )

    def test_partial_draw_055_is_present_with_only_the_jackpot_forecast(self):
        row_055 = next(r for r in self.rows if r.numero_sorteio == "055/2026")
        self.assertEqual(row_055.previsao_proximo_jackpot_eur, 29000000)
        self.assertIsNone(row_055.receita_liquida_apostas_eur)
        self.assertIs(row_055.dados_financeiros_disponiveis, False)

    def test_never_mutates_the_source_dataset(self):
        before = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        build_economy_rows(self.sorteios, year=2026)
        build_economy_summary(self.rows, year=2026)
        after = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        self.assertEqual(before, after)


# Real premios.categorias copied verbatim from draw 040/2026 — one of the
# 15 draws with a complete category breakdown
# (qualidade_dados.categorias_premio_disponiveis=true). Category 1 has a
# real percentagem_portugal_no_total of None (0 winners that draw), kept
# on purpose to exercise "ignores None" without fabricating a fixture.
REAL_CATEGORIAS_040_2026 = [
    {"categoria": 1, "acertos": "5 números + 2 estrelas", "vencedores_portugal": 0, "vencedores_total": 0, "percentagem_portugal_no_total": None},
    {"categoria": 2, "acertos": "5 números + 1 estrela", "vencedores_portugal": 0, "vencedores_total": 3, "percentagem_portugal_no_total": 0.0},
    {"categoria": 3, "acertos": "5 números + 0 estrelas", "vencedores_portugal": 0, "vencedores_total": 9, "percentagem_portugal_no_total": 0.0},
    {"categoria": 4, "acertos": "4 números + 2 estrelas", "vencedores_portugal": 2, "vencedores_total": 23, "percentagem_portugal_no_total": 8.695652},
    {"categoria": 5, "acertos": "4 números + 1 estrela", "vencedores_portugal": 45, "vencedores_total": 640, "percentagem_portugal_no_total": 7.03125},
    {"categoria": 6, "acertos": "3 números + 2 estrelas", "vencedores_portugal": 156, "vencedores_total": 1623, "percentagem_portugal_no_total": 9.61183},
    {"categoria": 7, "acertos": "4 números + 0 estrelas", "vencedores_portugal": 90, "vencedores_total": 1365, "percentagem_portugal_no_total": 6.593407},
    {"categoria": 8, "acertos": "2 números + 2 estrelas", "vencedores_portugal": 2312, "vencedores_total": 24973, "percentagem_portugal_no_total": 9.257999},
    {"categoria": 9, "acertos": "3 números + 1 estrela", "vencedores_portugal": 2479, "vencedores_total": 30031, "percentagem_portugal_no_total": 8.254803},
    {"categoria": 10, "acertos": "3 números + 0 estrelas", "vencedores_portugal": 3891, "vencedores_total": 58287, "percentagem_portugal_no_total": 6.675588},
    {"categoria": 11, "acertos": "1 número + 2 estrelas", "vencedores_portugal": 12438, "vencedores_total": 128487, "percentagem_portugal_no_total": 9.680357},
    {"categoria": 12, "acertos": "2 números + 1 estrela", "vencedores_portugal": 35008, "vencedores_total": 432564, "percentagem_portugal_no_total": 8.093138},
    {"categoria": 13, "acertos": "2 números + 0 estrelas", "vencedores_portugal": 57942, "vencedores_total": 858994, "percentagem_portugal_no_total": 6.745332},
]


def make_draw_record_with_categorias(categorias=None, categorias_disponiveis=True, **overrides):
    if categorias is None:
        categorias = REAL_CATEGORIAS_040_2026
    record = make_draw_record(
        numero_sorteio="040/2026",
        data="2026-05-19",
        premios={
            "categorias": categorias,
            "houve_vencedor_1_premio_total": False,
            "houve_vencedor_1_premio_portugal": False,
            "total_vencedores_todas_categorias": sum(c["vencedores_total"] for c in categorias) if categorias else None,
            "total_vencedores_portugal_todas_categorias": sum(c["vencedores_portugal"] for c in categorias) if categorias else None,
        },
        qualidade_dados={
            "dados_financeiros_disponiveis": True,
            "categorias_premio_disponiveis": categorias_disponiveis,
            "campos_em_falta": [],
        },
    )
    record.update(overrides)
    return record


class TestPrizeCategoryLabels(unittest.TestCase):
    def test_labels_match_all_15_real_draws_with_categorias(self):
        data = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        expected = tuple(_PRIZE_CATEGORY_LABELS)
        checked = 0
        for s in data["sorteios"]:
            categorias = (s.get("premios") or {}).get("categorias")
            if not isinstance(categorias, list):
                continue
            pairs = tuple((c["categoria"], c["acertos"]) for c in sorted(categorias, key=lambda c: c["categoria"]))
            self.assertEqual(pairs, expected, f"mismatch in {s['numero_sorteio']}")
            checked += 1
        self.assertEqual(checked, 15)


class TestBuildPrizeCategoryRows(unittest.TestCase):
    def test_generates_exactly_13_rows_per_draw(self):
        rows = build_prize_category_rows([make_draw_record_with_categorias()])
        self.assertEqual(len(rows), 13)
        self.assertEqual([r.categoria for r in rows], [c for c, _ in _PRIZE_CATEGORY_LABELS])
        self.assertEqual([r.acertos for r in rows], [a for _, a in _PRIZE_CATEGORY_LABELS])

    def test_maps_real_values_from_a_complete_draw(self):
        rows = build_prize_category_rows([make_draw_record_with_categorias()])
        by_categoria = {r.categoria: r for r in rows}

        cat1 = by_categoria[1]
        self.assertEqual(cat1.vencedores_portugal, 0)
        self.assertEqual(cat1.vencedores_total, 0)
        self.assertIsNone(cat1.percentagem_portugal_no_total)
        self.assertIs(cat1.categorias_disponiveis, True)

        cat13 = by_categoria[13]
        self.assertEqual(cat13.vencedores_portugal, 57942)
        self.assertEqual(cat13.vencedores_total, 858994)
        self.assertEqual(cat13.percentagem_portugal_no_total, 6.745332)
        self.assertIs(cat13.categorias_disponiveis, True)

        self.assertTrue(all(r.categorias_disponiveis is True for r in rows))
        self.assertTrue(all(r.numero_sorteio == "040/2026" for r in rows))
        self.assertTrue(all(r.data == "2026-05-19" for r in rows))

    def test_draw_without_categorias_has_13_rows_with_only_variable_fields_none(self):
        rows = build_prize_category_rows([make_draw_record()])
        self.assertEqual(len(rows), 13)
        for row, (categoria, acertos) in zip(rows, _PRIZE_CATEGORY_LABELS):
            with self.subTest(categoria=categoria):
                self.assertEqual(row.categoria, categoria)
                self.assertEqual(row.acertos, acertos)
                self.assertIsNone(row.vencedores_portugal)
                self.assertIsNone(row.vencedores_total)
                self.assertIsNone(row.percentagem_portugal_no_total)
                self.assertIs(row.categorias_disponiveis, False)

    def test_categorias_disponiveis_comes_from_qualidade_dados_not_inferred(self):
        # categorias IS a real, populated list here, but
        # qualidade_dados.categorias_premio_disponiveis is explicitly
        # False — the flag must win, never be inferred from the values
        # actually being present.
        record = make_draw_record_with_categorias(categorias_disponiveis=False)
        rows = build_prize_category_rows([record])
        self.assertTrue(all(r.categorias_disponiveis is False for r in rows))
        # The values themselves are still copied through — only the flag
        # reflects the (contradictory, hypothetical) qualidade_dados.
        by_categoria = {r.categoria: r for r in rows}
        self.assertEqual(by_categoria[13].vencedores_total, 858994)

    def test_year_filter_matches_other_builders(self):
        draw_2025 = make_draw_record(numero_sorteio="104/2025", calendario={"ano": 2025})
        draw_2026 = make_draw_record_with_categorias()
        rows = build_prize_category_rows([draw_2025, draw_2026], year=2026)
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(r.numero_sorteio == "040/2026" for r in rows))

    def test_row_is_frozen(self):
        row = build_prize_category_rows([make_draw_record()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.vencedores_total = 0


class TestBuildPrizeCategorySummary(unittest.TestCase):
    def test_por_categoria_has_exactly_13_aggregates_ordered_by_categoria(self):
        rows = build_prize_category_rows([make_draw_record_with_categorias()])
        summary = build_prize_category_summary(rows, year=2026)
        self.assertEqual(len(summary.por_categoria), 13)
        self.assertEqual([a.categoria for a in summary.por_categoria], [c for c, _ in _PRIZE_CATEGORY_LABELS])

    def test_percentagem_media_ignores_none(self):
        # Two draws, same category 1: one real observation
        # (percentagem=10.0) and one None (0 winners that draw). The
        # average must be 10.0, not 5.0 (which would treat None as 0).
        categorias_a = [dict(c) for c in REAL_CATEGORIAS_040_2026]
        categorias_a[0] = {"categoria": 1, "acertos": "5 números + 2 estrelas", "vencedores_portugal": 1, "vencedores_total": 5, "percentagem_portugal_no_total": 10.0}
        draw_a = make_draw_record_with_categorias(categorias=categorias_a, numero_sorteio="040/2026")
        draw_b = make_draw_record_with_categorias(numero_sorteio="041/2026", data="2026-05-22")  # category 1 stays None here
        rows = build_prize_category_rows([draw_a, draw_b], year=2026)
        summary = build_prize_category_summary(rows, year=2026)
        cat1 = next(a for a in summary.por_categoria if a.categoria == 1)
        self.assertEqual(cat1.percentagem_portugal_no_total_media, 10.0)
        self.assertEqual(cat1.sorteios_com_dados, 2)  # vencedores_total present (5 and 0) in both

    def test_no_real_observations_returns_none_aggregates_and_zero_percentage(self):
        rows = build_prize_category_rows([make_draw_record(), make_draw_record(numero_sorteio="058/2026")])
        summary = build_prize_category_summary(rows, year=2026)
        self.assertEqual(summary.sorteios_no_periodo, 2)
        self.assertEqual(summary.sorteios_com_categorias_disponiveis, 0)
        self.assertEqual(summary.percentagem_sorteios_com_categorias_disponiveis, 0.0)
        for aggregate in summary.por_categoria:
            with self.subTest(categoria=aggregate.categoria):
                self.assertEqual(aggregate.sorteios_com_dados, 0)
                self.assertIsNone(aggregate.vencedores_portugal_total)
                self.assertIsNone(aggregate.vencedores_total_total)
                self.assertIsNone(aggregate.percentagem_portugal_no_total_media)

    def test_sorteios_com_dados_is_consistent_across_categories_when_draw_has_data(self):
        rows = build_prize_category_rows([make_draw_record_with_categorias()])
        summary = build_prize_category_summary(rows, year=2026)
        self.assertTrue(all(a.sorteios_com_dados == 1 for a in summary.por_categoria))

    def test_sorteios_no_periodo_derived_from_distinct_numero_sorteio(self):
        rows = build_prize_category_rows([
            make_draw_record_with_categorias(),
            make_draw_record(numero_sorteio="041/2026", data="2026-05-22"),
        ], year=2026)
        summary = build_prize_category_summary(rows, year=2026)
        self.assertEqual(summary.sorteios_no_periodo, 2)
        self.assertEqual(summary.sorteios_com_categorias_disponiveis, 1)
        self.assertEqual(summary.percentagem_sorteios_com_categorias_disponiveis, 50.0)

    def test_result_is_frozen(self):
        summary = build_prize_category_summary([], year=2026)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            summary.ano = 2025


@unittest.skipUnless(REAL_2026_DATASET_PATH.exists(), "real 2026 dataset not present in this checkout")
class TestBuildPrizeCategoryRealDataset(unittest.TestCase):
    """Cross-checks build_prize_category_rows/build_prize_category_summary
    against the actual datasets/historical/euromillions/2026/... file —
    read-only, never modified by this test.
    """

    @classmethod
    def setUpClass(cls):
        data = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        cls.sorteios = data["sorteios"]
        cls.rows = build_prize_category_rows(cls.sorteios, year=2026)
        cls.summary = build_prize_category_summary(cls.rows, year=2026)

    def test_total_rows_is_62_draws_times_13_categories(self):
        self.assertEqual(len(self.rows), 62 * 13)

    def test_coverage_matches_qualidade_dados(self):
        self.assertEqual(self.summary.sorteios_no_periodo, 62)
        self.assertEqual(self.summary.sorteios_com_categorias_disponiveis, 15)
        self.assertAlmostEqual(
            self.summary.percentagem_sorteios_com_categorias_disponiveis, 15 / 62 * 100, places=6,
        )

    def test_por_categoria_has_13_entries_ordered(self):
        self.assertEqual(len(self.summary.por_categoria), 13)
        self.assertEqual([a.categoria for a in self.summary.por_categoria], list(range(1, 14)))

    def test_category_1_real_aggregate_mostly_none_percentage(self):
        # Real Euromillions data: category 1 (5+2, the jackpot tier) had
        # 0 Portuguese winners across the 15 draws, and only 2 of the 15
        # draws had any winner at all anywhere — the other 13 have a real
        # null percentagem_portugal_no_total (0 winners, not missing data).
        cat1 = next(a for a in self.summary.por_categoria if a.categoria == 1)
        self.assertEqual(cat1.sorteios_com_dados, 15)
        self.assertEqual(cat1.vencedores_portugal_total, 0)
        self.assertEqual(cat1.vencedores_total_total, 2)
        self.assertAlmostEqual(cat1.percentagem_portugal_no_total_media, 0.0, places=6)

    def test_category_13_real_aggregate_full_coverage(self):
        cat13 = next(a for a in self.summary.por_categoria if a.categoria == 13)
        self.assertEqual(cat13.sorteios_com_dados, 15)
        self.assertEqual(cat13.vencedores_portugal_total, 1206618)
        self.assertEqual(cat13.vencedores_total_total, 16375705)
        self.assertAlmostEqual(cat13.percentagem_portugal_no_total_media, 7.4880704, places=6)

    def test_partial_draw_055_has_no_category_data(self):
        row_055 = [r for r in self.rows if r.numero_sorteio == "055/2026"]
        self.assertEqual(len(row_055), 13)
        self.assertTrue(all(r.categorias_disponiveis is False for r in row_055))
        self.assertTrue(all(r.vencedores_total is None for r in row_055))

    def test_never_mutates_the_source_dataset(self):
        before = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        build_prize_category_rows(self.sorteios, year=2026)
        build_prize_category_summary(self.rows, year=2026)
        after = json.loads(REAL_2026_DATASET_PATH.read_text(encoding="utf-8"))
        self.assertEqual(before, after)


class TestBuildCharactersRows(unittest.TestCase):
    def test_maps_fields_correctly(self):
        rows = build_characters_rows([make_character_file()])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.entity_id, "bruxa_arquetipo")
        self.assertEqual(row.nome, "Bruxa")
        self.assertEqual(row.raca, "Clérigos")
        self.assertEqual(row.titulo, "Linhagem da Mistura")
        self.assertIsNotNone(row.metodo)
        self.assertIsNone(row.faccao)

    def test_aggregates_multiple_files_correctly(self):
        file_1 = make_character_file(raca="Clérigos")
        file_2 = make_character_file(
            raca="Vampiros",
            personagens=[{"id": "conde_vaelor", "nome": "Conde Vaelor", "titulo": "O Antigo"}],
        )
        rows = build_characters_rows([file_1, file_2])
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.raca for r in rows}, {"Clérigos", "Vampiros"})
        self.assertEqual({r.entity_id for r in rows}, {"bruxa_arquetipo", "conde_vaelor"})

    def test_missing_metodo_and_titulo_default_to_none(self):
        file_content = make_character_file(
            personagens=[{"id": "sem_extras", "nome": "Sem Extras"}],
        )
        row = build_characters_rows([file_content])[0]
        self.assertIsNone(row.titulo)
        self.assertIsNone(row.metodo)

    def test_multiple_personagens_within_one_race_all_included(self):
        file_content = make_character_file(personagens=[
            {"id": "a", "nome": "A"},
            {"id": "b", "nome": "B"},
        ])
        rows = build_characters_rows([file_content])
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.entity_id for r in rows}, {"a", "b"})

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(build_characters_rows([]), [])

    def test_mutating_source_file_after_build_does_not_affect_row(self):
        file_content = make_character_file()
        row = build_characters_rows([file_content])[0]
        file_content["personagens"][0]["nome"] = "Alterado"
        self.assertEqual(row.nome, "Bruxa")

    def test_row_is_frozen(self):
        row = build_characters_rows([make_character_file()])[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            row.nome = "changed"


def make_population_record(**overrides):
    record = {
        "id": "H-00017",
        "nome": "Morgana da Lua Fria",
        "raca": "Chefe Tribal",
        "casa": "place:floresta_ancestral",
        "geracao": 3,
        "pontos": 42,
        "titulo": "Guardiã",
    }
    record.update(overrides)
    return record


def make_lineage_file(**overrides):
    file_content = {"raca": "Treefolks", "casa": "place:floresta_ancestral"}
    file_content.update(overrides)
    return file_content


class TestIsEmpty(unittest.TestCase):
    def test_none_is_empty(self):
        self.assertTrue(_is_empty(None))

    def test_empty_string_is_empty(self):
        self.assertTrue(_is_empty(""))

    def test_whitespace_only_string_is_empty(self):
        self.assertTrue(_is_empty("   "))

    def test_empty_list_dict_set_are_empty(self):
        self.assertTrue(_is_empty([]))
        self.assertTrue(_is_empty({}))
        self.assertTrue(_is_empty(set()))

    def test_non_empty_string_is_not_empty(self):
        self.assertFalse(_is_empty("place:floresta_ancestral"))

    def test_non_empty_collection_is_not_empty(self):
        self.assertFalse(_is_empty([1, 2]))

    def test_zero_and_false_are_not_empty(self):
        self.assertFalse(_is_empty(0))
        self.assertFalse(_is_empty(False))


class TestNormalizeIndividualRecord(unittest.TestCase):
    def test_valid_record_is_valid_with_no_missing_fields(self):
        normalized = _normalize_individual_record(make_population_record(), index=0)
        self.assertTrue(normalized.is_valid)
        self.assertEqual(normalized.missing_fields, ())
        self.assertEqual(normalized.entity_id, "H-00017")
        self.assertEqual(normalized.nome, "Morgana da Lua Fria")
        self.assertEqual(normalized.raca, "Chefe Tribal")
        self.assertEqual(normalized.casa, "place:floresta_ancestral")
        self.assertEqual(normalized.geracao, 3)
        self.assertEqual(normalized.source_index, 0)

    def test_missing_field_is_flagged_as_ausente(self):
        record = make_population_record()
        del record["casa"]
        normalized = _normalize_individual_record(record, index=1)
        self.assertFalse(normalized.is_valid)
        self.assertIn("casa (ausente)", normalized.missing_fields)
        self.assertIsNone(normalized.casa)

    def test_multiple_missing_fields_all_reported(self):
        record = make_population_record()
        del record["casa"]
        del record["geracao"]
        normalized = _normalize_individual_record(record, index=2)
        self.assertEqual(
            set(normalized.missing_fields),
            {"casa (ausente)", "geracao (ausente)"},
        )

    def test_empty_string_field_is_flagged_as_vazio(self):
        record = make_population_record(raca="")
        normalized = _normalize_individual_record(record, index=3)
        self.assertFalse(normalized.is_valid)
        self.assertIn("raca (vazio)", normalized.missing_fields)

    def test_whitespace_only_string_field_is_flagged_as_vazio(self):
        record = make_population_record(nome="   ")
        normalized = _normalize_individual_record(record, index=4)
        self.assertFalse(normalized.is_valid)
        self.assertIn("nome (vazio)", normalized.missing_fields)

    def test_geracao_zero_is_not_treated_as_empty(self):
        normalized = _normalize_individual_record(make_population_record(geracao=0), index=0)
        self.assertTrue(normalized.is_valid)
        self.assertEqual(normalized.geracao, 0)

    def test_non_mapping_record_never_raises(self):
        for bad_record in (None, "not-a-dict", 123, ["a", "list"]):
            with self.subTest(bad_record=bad_record):
                normalized = _normalize_individual_record(bad_record, index=5)
                self.assertFalse(normalized.is_valid)
                self.assertIsNone(normalized.casa)
                self.assertEqual(len(normalized.missing_fields), 1)
                self.assertIn("registo inválido", normalized.missing_fields[0])

    def test_extra_excludes_common_fields(self):
        normalized = _normalize_individual_record(make_population_record(), index=0)
        self.assertNotIn("casa", normalized.extra)
        self.assertNotIn("id", normalized.extra)
        self.assertNotIn("nome", normalized.extra)
        self.assertNotIn("raca", normalized.extra)
        self.assertNotIn("geracao", normalized.extra)
        self.assertEqual(normalized.extra["pontos"], 42)
        self.assertEqual(normalized.extra["titulo"], "Guardiã")

    def test_extra_is_a_mapping_proxy_and_is_immutable(self):
        normalized = _normalize_individual_record(make_population_record(), index=0)
        self.assertIsInstance(normalized.extra, MappingProxyType)
        with self.assertRaises(TypeError):
            normalized.extra["pontos"] = 999

    def test_mutating_source_record_after_normalize_does_not_affect_extra(self):
        record = make_population_record()
        normalized = _normalize_individual_record(record, index=0)
        record["pontos"] = 999
        record["novo_campo"] = "abc"
        self.assertEqual(normalized.extra["pontos"], 42)
        self.assertNotIn("novo_campo", normalized.extra)

    def test_row_is_frozen(self):
        normalized = _normalize_individual_record(make_population_record(), index=0)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            normalized.casa = "changed"


class TestNormalizeIndividualRecordAliases(unittest.TestCase):
    def test_name_alone_resolves_to_canonical_nome(self):
        record = make_population_record()
        del record["nome"]
        record["name"] = "Aruk Pedra-Partida"
        normalized = _normalize_individual_record(record, index=0)
        self.assertTrue(normalized.is_valid)
        self.assertEqual(normalized.nome, "Aruk Pedra-Partida")

    def test_generation_alone_resolves_to_canonical_geracao(self):
        record = make_population_record()
        del record["geracao"]
        record["generation"] = 4
        normalized = _normalize_individual_record(record, index=0)
        self.assertTrue(normalized.is_valid)
        self.assertEqual(normalized.geracao, 4)

    def test_canonical_wins_when_both_present_even_if_canonical_is_empty(self):
        record = make_population_record(nome="")
        record["name"] = "Valor do Alias"
        normalized = _normalize_individual_record(record, index=0)
        self.assertFalse(normalized.is_valid)
        self.assertIn("nome (vazio)", normalized.missing_fields)
        self.assertEqual(normalized.nome, "")

    def test_alias_is_only_consulted_when_canonical_key_is_entirely_absent(self):
        # canonical present (even invalid/empty) always wins — no fallback
        # to the alias when the canonical key exists at all.
        record = make_population_record(nome="   ")
        record["name"] = "Nome Valido"
        normalized = _normalize_individual_record(record, index=0)
        self.assertIn("nome (vazio)", normalized.missing_fields)
        self.assertEqual(normalized.nome, "   ")

    def test_missing_field_message_always_uses_canonical_name(self):
        record = make_population_record()
        del record["nome"]
        del record["geracao"]
        # neither canonical nor alias present at all
        normalized = _normalize_individual_record(record, index=0)
        self.assertIn("nome (ausente)", normalized.missing_fields)
        self.assertIn("geracao (ausente)", normalized.missing_fields)
        for issue in normalized.missing_fields:
            self.assertNotIn("name", issue)
            self.assertNotIn("generation", issue)

    def test_consumed_alias_is_excluded_from_extra(self):
        record = make_population_record()
        del record["nome"]
        record["name"] = "Aruk Pedra-Partida"
        normalized = _normalize_individual_record(record, index=0)
        self.assertNotIn("name", normalized.extra)
        self.assertNotIn("nome", normalized.extra)

    def test_unconsumed_alias_survives_in_extra_when_canonical_wins(self):
        record = make_population_record(nome="Morgana da Lua Fria")
        record["name"] = "Valor Nao Usado"
        normalized = _normalize_individual_record(record, index=0)
        self.assertEqual(normalized.nome, "Morgana da Lua Fria")
        self.assertEqual(normalized.extra["name"], "Valor Nao Usado")

    def test_real_archive_shape_is_valid_via_aliases(self):
        # Mirrors the actual shape found in
        # datasets/generated/world_state/todos_individuos.json: 'name'/
        # 'generation', not 'nome'/'geracao', plus assorted extras.
        record = {
            "id": "H-00001",
            "name": "Aruk Pedra-Partida",
            "raca": "Chefe Tribal",
            "casa": "Casa Lunar",
            "generation": 1,
            "pais": [],
            "genoma": {"clareza": 0.7, "confusao": 0.1},
            "pontos": 30,
            "titulo": "Sem título",
            "amuletos": [],
            "estado": "VIVO",
            "treinos": 0,
        }
        normalized = _normalize_individual_record(record, index=0)
        self.assertTrue(normalized.is_valid)
        self.assertEqual(normalized.missing_fields, ())
        self.assertEqual(normalized.nome, "Aruk Pedra-Partida")
        self.assertEqual(normalized.geracao, 1)
        self.assertEqual(normalized.casa, "Casa Lunar")
        for excluded in ("id", "name", "raca", "casa", "generation"):
            self.assertNotIn(excluded, normalized.extra)
        for kept in ("pais", "genoma", "pontos", "titulo", "amuletos", "estado", "treinos"):
            self.assertIn(kept, normalized.extra)

    def test_original_record_is_never_mutated(self):
        record = make_population_record()
        del record["nome"]
        record["name"] = "Aruk Pedra-Partida"
        original_keys = set(record.keys())
        original_snapshot = dict(record)
        _normalize_individual_record(record, index=0)
        self.assertEqual(set(record.keys()), original_keys)
        self.assertEqual(record, original_snapshot)


class TestNormalizeArchive(unittest.TestCase):
    def test_empty_archive_returns_empty_result(self):
        result = _normalize_archive([])
        self.assertEqual(result.individuals, ())
        self.assertEqual(result.warnings, ())

    def test_valid_records_produce_no_warnings(self):
        result = _normalize_archive([make_population_record(), make_population_record(id="H-2")])
        self.assertEqual(result.warnings, ())
        self.assertEqual(len(result.individuals), 2)

    def test_warning_names_exact_missing_field_and_record_identity(self):
        record = make_population_record(id="H-99")
        del record["casa"]
        result = _normalize_archive([record])
        self.assertEqual(result.warnings, ("registo H-99: casa (ausente)",))

    def test_warning_uses_index_when_id_missing(self):
        record = make_population_record()
        del record["id"]
        del record["casa"]
        result = _normalize_archive([record])
        self.assertEqual(
            result.warnings,
            ("registo índice 0: id (ausente)", "registo índice 0: casa (ausente)"),
        )

    def test_warnings_and_individuals_preserve_record_order(self):
        good = make_population_record(id="H-good")
        bad = make_population_record(id="H-bad")
        del bad["casa"]
        result = _normalize_archive([good, bad])
        self.assertEqual(
            [ind.entity_id for ind in result.individuals],
            ["H-good", "H-bad"],
        )
        self.assertEqual(result.warnings, ("registo H-bad: casa (ausente)",))

    def test_result_is_frozen(self):
        result = _normalize_archive([])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.warnings = ("x",)


class TestBuildHouses(unittest.TestCase):
    def test_declared_only_via_casa_string_has_source_lineages_json(self):
        rows = build_houses([make_lineage_file()], [])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.casa, "place:floresta_ancestral")
        self.assertEqual(row.declared_by_races, ("Treefolks",))
        self.assertFalse(row.observed_in_population)
        self.assertEqual(row.source, "lineages.json")

    def test_declared_via_casas_list(self):
        file_content = {"raca": "Kors", "casas": ["place:norte", "place:sul"]}
        rows = build_houses([file_content], [])
        self.assertEqual({r.casa for r in rows}, {"place:norte", "place:sul"})
        for row in rows:
            self.assertEqual(row.declared_by_races, ("Kors",))
            self.assertEqual(row.source, "lineages.json")

    def test_declared_via_casas_single_string(self):
        rows = build_houses([{"raca": "Faeries", "casas": "place:jardim_eterno"}], [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].casa, "place:jardim_eterno")
        self.assertEqual(rows[0].declared_by_races, ("Faeries",))

    def test_casas_takes_precedence_over_casa_when_both_present(self):
        file_content = {"raca": "Kors", "casa": "place:antigo", "casas": ["place:novo"]}
        rows = build_houses([file_content], [])
        self.assertEqual([r.casa for r in rows], ["place:novo"])

    def test_observed_only_house_has_source_population_only(self):
        rows = build_houses([], [make_population_record(casa="place:jardim_eterno")])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.casa, "place:jardim_eterno")
        self.assertEqual(row.declared_by_races, ())
        self.assertTrue(row.observed_in_population)
        self.assertEqual(row.source, "population_only")

    def test_declared_only_house_is_not_marked_observed(self):
        rows = build_houses([make_lineage_file()], [make_population_record(casa="place:outra_casa")])
        by_casa = {row.casa: row for row in rows}
        self.assertFalse(by_casa["place:floresta_ancestral"].observed_in_population)
        self.assertEqual(by_casa["place:floresta_ancestral"].source, "lineages.json")

    def test_declared_and_observed_house_has_source_both(self):
        rows = build_houses(
            [make_lineage_file()],
            [make_population_record(casa="place:floresta_ancestral")],
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.source, "both")
        self.assertTrue(row.observed_in_population)
        self.assertEqual(row.declared_by_races, ("Treefolks",))

    def test_house_observed_even_when_other_common_fields_missing(self):
        record = make_population_record(casa="place:floresta_ancestral")
        del record["raca"]
        rows = build_houses([], [record])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].observed_in_population)

    def test_multiple_races_declaring_same_house_are_all_listed_sorted(self):
        rows = build_houses(
            [make_lineage_file(raca="Treefolks"), make_lineage_file(raca="Faeries")],
            [],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].declared_by_races, ("Faeries", "Treefolks"))

    def test_casa_names_are_stripped_of_surrounding_whitespace(self):
        rows = build_houses([{"raca": "Kors", "casa": "  place:com_espacos  "}], [])
        self.assertEqual(rows[0].casa, "place:com_espacos")

    def test_casas_whitespace_only_entries_are_ignored(self):
        file_content = {"raca": "Kors", "casas": ["place:valido", "   ", ""]}
        rows = build_houses([file_content], [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].casa, "place:valido")

    def test_casas_non_string_entries_are_ignored(self):
        file_content = {"raca": "Kors", "casas": ["place:valido", 123, None, {"a": 1}]}
        rows = build_houses([file_content], [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].casa, "place:valido")

    def test_casas_wrong_type_results_in_no_declared_houses(self):
        rows = build_houses([{"raca": "Kors", "casas": 123}], [])
        self.assertEqual(rows, [])

    def test_lineage_file_missing_raca_is_skipped(self):
        rows = build_houses([{"casa": "place:sem_raca"}], [])
        self.assertEqual(rows, [])

    def test_non_mapping_lineage_file_never_raises(self):
        rows = build_houses([None, "not-a-dict", 123], [])
        self.assertEqual(rows, [])

    def test_non_mapping_and_missing_field_archive_records_never_raise(self):
        rows = build_houses([], [None, "not-a-dict", {}, make_population_record(casa="place:x")])
        self.assertEqual([r.casa for r in rows], ["place:x"])

    def test_empty_inputs_return_empty_list(self):
        self.assertEqual(build_houses([], []), [])

    def test_rows_are_sorted_by_casa(self):
        rows = build_houses([{"raca": "Kors", "casas": ["place:zulu", "place:alfa"]}], [])
        self.assertEqual([r.casa for r in rows], ["place:alfa", "place:zulu"])

    def test_house_entry_is_frozen(self):
        rows = build_houses([make_lineage_file()], [])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rows[0].casa = "changed"


def make_hero_row(**overrides):
    fields = dict(
        hero_id="HERO-2026-057-000149f4",
        dedup_hash="000149f4",
        entity_id="H-00017",
        entity_name="Morgana da Lua Fria",
        race="Chefe Tribal",
        generation=1,
        provenance="legacy",
        draw_id="057/2026",
        draw_date="2026-07-17",
        official_numeros=(12, 21, 23, 34, 40),
        official_estrelas=(9, 10),
        predicted_numeros=(12, 36, 40, 45, 50),
        predicted_estrelas=(5, 10),
        matched_numbers_count=2,
        matched_stars_count=1,
        hero_category="2+1",
        hero_tier="TIER_5",
    )
    fields.update(overrides)
    return HeroRow(**fields)


def make_legend_row(**overrides):
    fields = dict(
        legend_id="LEGEND-395e24e0",
        source_prediction_id="395e24e0",
        entity_id="H-00017",
        entity_name="Morgana da Lua Fria",
        race="Chefe Tribal",
        promotion_draw="058/2026",
        promotion_draw_date="2026-07-21",
        promotion_threshold=3,
        promotion_tier="LEGEND_TIER_4",
        criteria_version="v1",
        hero_count=3,
        qualified_draws=3,
        provenance="legacy",
    )
    fields.update(overrides)
    return LegendRow(**fields)


def make_draw_row(**overrides):
    fields = dict(
        numero_sorteio="057/2026",
        data="2026-07-17",
        dia_semana="sexta-feira",
        numeros=(12, 21, 23, 34, 40),
        estrelas=(9, 10),
        soma=130,
        gaps=(9, 2, 11, 6),
    )
    fields.update(overrides)
    return DrawRow(**fields)


def make_character_row(**overrides):
    fields = dict(entity_id="bruxa_arquetipo", nome="Bruxa", raca="Clérigos")
    fields.update(overrides)
    return CharacterRow(**fields)


def make_house_entry(**overrides):
    fields = dict(
        casa="place:floresta_ancestral",
        declared_by_races=("Treefolks",),
        observed_in_population=False,
        source="lineages.json",
    )
    fields.update(overrides)
    return HouseEntry(**fields)


class TestBuildExecutiveSummary(unittest.TestCase):
    def test_counts_heroes_and_legends(self):
        summary = build_executive_summary([make_hero_row(), make_hero_row()], [make_legend_row()])
        self.assertEqual(summary.total_heroes, 2)
        self.assertEqual(summary.total_legends, 1)

    def test_empty_lists_return_zero_counts(self):
        summary = build_executive_summary([], [])
        self.assertEqual(summary.total_heroes, 0)
        self.assertEqual(summary.total_legends, 0)

    def test_default_economy_is_a_fresh_placeholder(self):
        summary = build_executive_summary([], [])
        self.assertIsInstance(summary.economia, EconomyPlaceholder)
        self.assertEqual(summary.economia, EconomyPlaceholder())

    def test_custom_economy_is_used_verbatim(self):
        custom = EconomyPlaceholder(investimento="1000")
        summary = build_executive_summary([], [], economy=custom)
        self.assertIs(summary.economia, custom)

    def test_gerado_em_passthrough(self):
        summary = build_executive_summary([], [], gerado_em="2026-08-01T00:00:00+00:00")
        self.assertEqual(summary.gerado_em, "2026-08-01T00:00:00+00:00")

    def test_gerado_em_defaults_to_none(self):
        summary = build_executive_summary([], [])
        self.assertIsNone(summary.gerado_em)

    def test_stats_requiring_generations_default_to_none_or_zero(self):
        # No GenerationRow producer exists yet (deferred, see CLAUDE.md) —
        # these must stay at their untouched dataclass defaults, never a
        # fabricated value.
        summary = build_executive_summary([make_hero_row()], [make_legend_row()])
        self.assertIsNone(summary.taxa_sucesso)
        self.assertIsNone(summary.diversidade_media)
        self.assertIsNone(summary.convergencia_media)
        self.assertEqual(summary.geracoes_analisadas, 0)

    def test_result_is_frozen(self):
        summary = build_executive_summary([], [])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            summary.total_heroes = 99


class TestBuildDashboardDataset(unittest.TestCase):
    def test_assembles_all_fields_correctly(self):
        heroes = [make_hero_row()]
        legends = [make_legend_row()]
        key_base = [make_draw_row()]
        characters = [make_character_row()]
        houses = [make_house_entry()]
        dataset = build_dashboard_dataset(heroes, legends, key_base, characters, houses)

        self.assertEqual(dataset.heroes, tuple(heroes))
        self.assertEqual(dataset.legends, tuple(legends))
        self.assertEqual(dataset.key_base, tuple(key_base))
        self.assertEqual(dataset.characters, tuple(characters))
        self.assertEqual(dataset.houses, tuple(houses))
        self.assertEqual(dataset.executive.total_heroes, 1)
        self.assertEqual(dataset.executive.total_legends, 1)

    def test_generations_and_frequencies_default_to_empty_tuple(self):
        dataset = build_dashboard_dataset([], [], [], [], [])
        self.assertEqual(dataset.generations, ())
        self.assertEqual(dataset.frequencies, ())

    def test_all_collections_are_tuples_not_lists(self):
        dataset = build_dashboard_dataset(
            [make_hero_row()], [make_legend_row()], [make_draw_row()],
            [make_character_row()], [make_house_entry()],
            generations=[], frequencies=[],
        )
        for field_name in ("heroes", "legends", "key_base", "characters", "houses", "generations", "frequencies"):
            with self.subTest(field=field_name):
                self.assertIsInstance(getattr(dataset, field_name), tuple)

    def test_executive_totals_always_match_heroes_and_legends_passed_in(self):
        heroes = [make_hero_row(), make_hero_row(entity_id="H-2")]
        legends = [make_legend_row()]
        dataset = build_dashboard_dataset(heroes, legends, [], [], [])
        self.assertEqual(dataset.executive.total_heroes, len(heroes))
        self.assertEqual(dataset.executive.total_legends, len(legends))

    def test_economy_is_identical_object_in_executive_and_dataset(self):
        custom = EconomyPlaceholder(investimento="500")
        dataset = build_dashboard_dataset([], [], [], [], [], economy=custom)
        self.assertIs(dataset.economy, custom)
        self.assertIs(dataset.executive.economia, custom)
        self.assertIs(dataset.economy, dataset.executive.economia)

    def test_default_economy_is_identical_object_in_executive_and_dataset(self):
        # No economy passed in — both must still resolve to the SAME
        # placeholder instance, not two separately-constructed ones.
        dataset = build_dashboard_dataset([], [], [], [], [])
        self.assertIs(dataset.economy, dataset.executive.economia)

    def test_gerado_em_reaches_executive_summary(self):
        dataset = build_dashboard_dataset([], [], [], [], [], gerado_em="2026-08-01T00:00:00+00:00")
        self.assertEqual(dataset.executive.gerado_em, "2026-08-01T00:00:00+00:00")

    def test_methodology_defaults_to_empty_mapping_proxy(self):
        dataset = build_dashboard_dataset([], [], [], [], [])
        self.assertIsInstance(dataset.methodology, MappingProxyType)
        self.assertEqual(dict(dataset.methodology), {})

    def test_methodology_is_immutable(self):
        dataset = build_dashboard_dataset([], [], [], [], [], methodology={"fonte": "manual"})
        self.assertIsInstance(dataset.methodology, MappingProxyType)
        with self.assertRaises(TypeError):
            dataset.methodology["fonte"] = "alterado"

    def test_mutating_source_methodology_after_build_does_not_affect_dataset(self):
        source = {"fonte": "manual"}
        dataset = build_dashboard_dataset([], [], [], [], [], methodology=source)
        source["fonte"] = "alterado"
        source["novo"] = "campo"
        self.assertEqual(dataset.methodology["fonte"], "manual")
        self.assertNotIn("novo", dataset.methodology)

    def test_mutating_source_list_after_build_does_not_affect_dataset_tuple(self):
        heroes = [make_hero_row()]
        dataset = build_dashboard_dataset(heroes, [], [], [], [])
        heroes.append(make_hero_row(entity_id="H-added-after"))
        self.assertEqual(len(dataset.heroes), 1)

    def test_result_is_frozen(self):
        dataset = build_dashboard_dataset([], [], [], [], [])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            dataset.heroes = ()

    def test_economy_draws_and_summary_default_to_empty_and_none(self):
        # Purely additive: a caller that never mentions the new economy
        # fields gets exactly the old, placeholder-only behaviour.
        dataset = build_dashboard_dataset([], [], [], [], [])
        self.assertEqual(dataset.economy_draws, ())
        self.assertIsNone(dataset.economy_summary)
        self.assertIsInstance(dataset.economy, EconomyPlaceholder)

    def test_economy_draws_and_summary_are_wired_through_when_provided(self):
        rows = build_economy_rows([make_complete_economy_record()], year=2026)
        summary = build_economy_summary(rows, year=2026)
        dataset = build_dashboard_dataset(
            [], [], [], [], [], economy_draws=rows, economy_summary=summary,
        )
        self.assertEqual(dataset.economy_draws, tuple(rows))
        self.assertIs(dataset.economy_summary, summary)
        # Still fully independent from the untouched placeholder fields.
        self.assertIsInstance(dataset.economy, EconomyPlaceholder)

    def test_prize_category_rows_and_summary_default_to_empty_and_none(self):
        dataset = build_dashboard_dataset([], [], [], [], [])
        self.assertEqual(dataset.prize_category_rows, ())
        self.assertIsNone(dataset.prize_category_summary)
        # Untouched by this commit's fields.
        self.assertEqual(dataset.economy_draws, ())
        self.assertIsNone(dataset.economy_summary)
        self.assertIsInstance(dataset.economy, EconomyPlaceholder)

    def test_prize_category_rows_and_summary_are_wired_through_when_provided(self):
        rows = build_prize_category_rows([make_draw_record_with_categorias()], year=2026)
        summary = build_prize_category_summary(rows, year=2026)
        dataset = build_dashboard_dataset(
            [], [], [], [], [], prize_category_rows=rows, prize_category_summary=summary,
        )
        self.assertEqual(dataset.prize_category_rows, tuple(rows))
        self.assertIs(dataset.prize_category_summary, summary)
        # Still fully independent from Economy and from the untouched
        # placeholder fields.
        self.assertEqual(dataset.economy_draws, ())
        self.assertIsNone(dataset.economy_summary)
        self.assertIsInstance(dataset.economy, EconomyPlaceholder)


if __name__ == "__main__":
    unittest.main()
