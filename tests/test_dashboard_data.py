"""Tests for core/services/dashboard_data.py — Heroes, Legends, Base de
Chaves and Personagens row builders. No HeroRegistry/LegendRegistry
involved anywhere here — only plain dicts, matching the module's
contract that it never touches the registries or disk itself.
"""

import dataclasses
import unittest

from core.services.dashboard_data import (
    HeroRow,
    LegendRow,
    build_characters_rows,
    build_heroes_rows,
    build_key_base_rows,
    build_legends_rows,
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


if __name__ == "__main__":
    unittest.main()
