"""Tests for core/services/dashboard_data.py — Heroes, Legends, Base de
Chaves and Personagens row builders. No HeroRegistry/LegendRegistry
involved anywhere here — only plain dicts, matching the module's
contract that it never touches the registries or disk itself.
"""

import dataclasses
import unittest
from types import MappingProxyType

from core.services.dashboard_data import (
    CharacterRow,
    DrawRow,
    EconomyPlaceholder,
    HeroRow,
    HouseEntry,
    LegendRow,
    _is_empty,
    _NormalizationResult,
    _NormalizedIndividual,
    _normalize_archive,
    _normalize_individual_record,
    build_characters_rows,
    build_dashboard_dataset,
    build_executive_summary,
    build_heroes_rows,
    build_houses,
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


if __name__ == "__main__":
    unittest.main()
