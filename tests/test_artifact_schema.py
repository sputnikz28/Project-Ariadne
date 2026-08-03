"""Tests for core/services/artifact_schema.py.

Covers both the pure normalization logic (with synthetic fixtures) and,
critically, the real 15 founding entries in library/artifacts/entries/ —
proving losslessness and narrative-safety against the actual collection,
not just against invented test cases.
"""

import json
import unittest
from pathlib import Path
from types import MappingProxyType

from core.services.artifact_schema import (
    ArtifactRecord,
    EventoHistoria,
    Localized,
    PersonagemRef,
    normalize_artifact,
    validate_artifact_record,
)

ENTRIES_DIR = Path("library/artifacts/entries")
EXPECTED_IDS = {
    "ART-CLOVER-AETHORIA-0001", "ART-HORSESHOE-TRAPALHAO-0001", "ART-HORSESHOE-TOBIAS-0001",
    "ART-HORSESHOE-TEMPESTADE-0001", "ART-HORSESHOE-VALENTE-0001", "ART-HORSESHOE-ASTERION-0001",
    "ART-DARUMA-0001", "ART-BRANDY-NAPOLEON-0001", "ART-7A3F91C2BE", "ART-COIN-MIDAS-0001",
    "ART-LADYBUG-SYLVARIS-0001", "ART-STAR-LYRA-0001", "ART-RAINBOW-IRIS-0001",
    "ART-LOTUS-TRANQUILIDADE-0001", "ART-CODEX-FORTUNA-ETERNA-0001",
}


def load_real_records():
    records = {}
    for path in sorted(ENTRIES_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        records[raw["id"]] = (raw, normalize_artifact(raw))
    return records


class TestRealCollectionLoads(unittest.TestCase):
    """Requirement: the 15 files load, exactly 15, matching the expected ids."""

    @classmethod
    def setUpClass(cls):
        cls.records = load_real_records()

    def test_exactly_fifteen_entries_present(self):
        self.assertEqual(len(self.records), 15)

    def test_ids_match_expected_collection(self):
        self.assertEqual(set(self.records.keys()), EXPECTED_IDS)

    def test_every_entry_normalizes_without_raising(self):
        for artifact_id, (raw, record) in self.records.items():
            with self.subTest(artifact_id=artifact_id):
                self.assertIsInstance(record, ArtifactRecord)


class TestRawIsLossless(unittest.TestCase):
    """Requirement: raw preserva o conteúdo original — for all 15 real entries."""

    @classmethod
    def setUpClass(cls):
        cls.records = load_real_records()

    def test_raw_is_byte_identical_to_source_for_every_entry(self):
        for artifact_id, (raw, record) in self.records.items():
            with self.subTest(artifact_id=artifact_id):
                self.assertEqual(dict(record.raw), raw)

    def test_raw_is_immutable(self):
        _, record = self.records["ART-DARUMA-0001"]
        with self.assertRaises(TypeError):
            record.raw["id"] = "changed"

    def test_mutating_source_dict_after_normalize_does_not_affect_raw(self):
        raw = json.loads((ENTRIES_DIR / "ART-DARUMA-0001.json").read_text(encoding="utf-8"))
        record = normalize_artifact(raw)
        raw["novo_campo"] = "abc"
        raw["nome"] = {"pt": "alterado"}
        self.assertNotIn("novo_campo", record.raw)
        self.assertEqual(record.raw["nome"]["pt"], "Daruma da Perseverança")


class TestExtrasCaptureTypeSpecificFields(unittest.TestCase):
    """Requirement: extras contém os campos específicos, sem os mover para
    campos genéricos — verified against the real per-type extension blocks.
    """

    @classmethod
    def setUpClass(cls):
        cls.records = load_real_records()

    def test_daruma_extras_has_olhos_objetivo_rituais(self):
        _, record = self.records["ART-DARUMA-0001"]
        self.assertEqual(record.extras["olhos"], {"esquerdo": True, "direito": False})
        self.assertIn("objetivo", record.extras)
        self.assertIn("rituais", record.extras)

    def test_brandy_extras_has_condicao_ativacao_celebracao_aparencia(self):
        _, record = self.records["ART-BRANDY-NAPOLEON-0001"]
        self.assertIn("condicao_ativacao", record.extras)
        self.assertIn("celebracao", record.extras)
        self.assertIn("aparencia", record.extras)

    def test_cuequinhas_extras_has_conforto_fofura(self):
        _, record = self.records["ART-7A3F91C2BE"]
        self.assertEqual(record.extras["conforto"], 100)
        self.assertEqual(record.extras["fofura"], 999)

    def test_lyra_extras_has_ritual(self):
        _, record = self.records["ART-STAR-LYRA-0001"]
        self.assertIn("ritual", record.extras)

    def test_iris_extras_has_cores(self):
        _, record = self.records["ART-RAINBOW-IRIS-0001"]
        self.assertEqual(
            record.extras["cores"],
            ["VERMELHO", "LARANJA", "AMARELO", "VERDE", "AZUL", "ANIL", "VIOLETA"],
        )

    def test_codex_extras_has_guardiao_indice_paginas_vivas_evolucao(self):
        _, record = self.records["ART-CODEX-FORTUNA-ETERNA-0001"]
        for key in ("guardiao", "indice", "paginas_vivas", "evolucao"):
            self.assertIn(key, record.extras)

    def test_lotus_extras_has_evolucao(self):
        _, record = self.records["ART-LOTUS-TRANQUILIDADE-0001"]
        self.assertIn("evolucao", record.extras)

    def test_extras_never_contains_core_keys(self):
        core_keys = {
            "id", "nome", "tipo", "raridade", "estado", "criador", "universo_origem",
            "energia_acumulada", "vezes_encontrado", "execucoes_sobrevividas",
            "efeitos", "lore", "historia", "tags",
        }
        for artifact_id, (raw, record) in self.records.items():
            with self.subTest(artifact_id=artifact_id):
                self.assertEqual(set(record.extras.keys()) & core_keys, set())


class TestMissingFieldsStayNoneNeverInvented(unittest.TestCase):
    """Requirement: campos ausentes ficam None, não recebem significado
    inventado. HORSESHOE-TRAPALHAO is missing many core fields entirely.
    """

    def test_horseshoe_missing_core_fields_are_none_not_guessed(self):
        # ART-HORSESHOE-TRAPALHAO-0001 DOES have criador, estado, efeitos —
        # the fields genuinely absent from its source are universo_origem,
        # historia and tags. Only those are asserted here.
        _, record = load_real_records()["ART-HORSESHOE-TRAPALHAO-0001"]
        self.assertEqual(record.historia, ())
        self.assertEqual(record.tags, ())
        self.assertIsNone(record.universo_origem)

    def test_daruma_missing_criador_energia_is_none_and_default_respectively(self):
        _, record = load_real_records()["ART-DARUMA-0001"]
        self.assertIsNone(record.criador)
        self.assertIsNone(record.universo_origem)
        # energia_acumulada is a neutral-default field, not a semantic one:
        self.assertEqual(record.energia_acumulada, 0.0)

    def test_synthetic_record_with_nothing_gets_only_neutral_defaults(self):
        record = normalize_artifact({"id": "ART-TEST-0001"})
        self.assertIsNone(record.nome)
        self.assertIsNone(record.tipo)
        self.assertIsNone(record.raridade)
        self.assertIsNone(record.estado)
        self.assertIsNone(record.criador)
        self.assertIsNone(record.universo_origem)
        self.assertIsNone(record.efeitos)
        self.assertIsNone(record.lore)
        # only these get neutral (non-semantic) defaults:
        self.assertEqual(record.energia_acumulada, 0.0)
        self.assertEqual(record.vezes_encontrado, 0)
        self.assertEqual(record.execucoes_sobrevividas, 0)
        self.assertEqual(record.tags, ())
        self.assertEqual(record.historia, ())

    def test_purificado_and_corrupcao_sombria_are_not_defaulted_in_extras(self):
        # These are NOT core fields — when absent from the source, they
        # simply don't appear in extras at all (no invented True/0.0).
        record = normalize_artifact({"id": "ART-TEST-0001"})
        self.assertNotIn("purificado", record.extras)
        self.assertNotIn("corrupcao_sombria", record.extras)


class TestLocalizedNormalization(unittest.TestCase):
    def test_string_estado_becomes_localized_with_empty_traducoes(self):
        record = normalize_artifact({"id": "x", "estado": "FLORESCENTE"})
        self.assertEqual(record.estado, Localized(codigo="FLORESCENTE", traducoes=MappingProxyType({})))

    def test_object_estado_splits_id_from_translations(self):
        record = normalize_artifact({"id": "x", "estado": {"id": "LACRADO", "pt": "Lacrado", "en": "Sealed"}})
        self.assertEqual(record.estado.codigo, "LACRADO")
        self.assertEqual(dict(record.estado.traducoes), {"pt": "Lacrado", "en": "Sealed"})

    def test_string_historia_evento_becomes_localized(self):
        record = normalize_artifact({"id": "x", "historia": [{"evento": "CUNHADA", "momento": "t"}]})
        self.assertEqual(record.historia[0].evento.codigo, "CUNHADA")
        self.assertEqual(record.historia[0].extra["momento"], "t")

    def test_object_historia_evento_splits_id_from_translations(self):
        raw_event = {"evento": {"id": "DESABROCHOU", "pt": "Desabrochou", "en": "Bloomed"}, "momento": "t"}
        record = normalize_artifact({"id": "x", "historia": [raw_event]})
        self.assertEqual(record.historia[0].evento.codigo, "DESABROCHOU")
        self.assertEqual(dict(record.historia[0].evento.traducoes), {"pt": "Desabrochou", "en": "Bloomed"})
        self.assertEqual(record.historia[0].extra, {"momento": "t"})


class TestLoreNormalization(unittest.TestCase):
    def test_lore_with_descricao_wrapper_is_unwrapped(self):
        record = normalize_artifact({"id": "x", "lore": {"descricao": {"pt": "a", "en": "b"}}})
        self.assertEqual(dict(record.lore), {"pt": "a", "en": "b"})

    def test_daruma_shape_lore_direct_pt_is_used_as_is(self):
        record = normalize_artifact({"id": "x", "lore": {"pt": "texto direto"}})
        self.assertEqual(dict(record.lore), {"pt": "texto direto"})


class TestCriadorNormalization(unittest.TestCase):
    def test_string_criador_becomes_personagem_ref_with_no_id(self):
        record = normalize_artifact({"id": "x", "criador": "Alguém"})
        self.assertEqual(record.criador, PersonagemRef(id=None, nome="Alguém"))

    def test_object_criador_preserves_id_and_nome(self):
        record = normalize_artifact({"id": "x", "criador": {"id": "C-1", "nome": "Alguém"}})
        self.assertEqual(record.criador, PersonagemRef(id="C-1", nome="Alguém"))


class TestNeverRaises(unittest.TestCase):
    def test_completely_empty_dict(self):
        record = normalize_artifact({})
        self.assertIsNone(record.id)

    def test_wrong_types_on_every_field_do_not_raise(self):
        garbage = {
            "id": 123, "nome": 456, "tipo": [], "raridade": {}, "estado": 3.5,
            "criador": [1, 2], "universo_origem": {"x": 1}, "energia_acumulada": "not a number",
            "vezes_encontrado": None, "execucoes_sobrevividas": [], "efeitos": "not a mapping",
            "lore": 42, "historia": "not a list", "tags": {"not": "a list"},
        }
        record = normalize_artifact(garbage)
        self.assertIsInstance(record, ArtifactRecord)
        self.assertEqual(record.energia_acumulada, 0.0)
        self.assertEqual(record.historia, ())
        self.assertEqual(record.tags, ())


class TestNarrativeSafetyAcrossRealCollection(unittest.TestCase):
    """Requirement: nenhum artefacto altera algoritmo, resultados ou
    probabilidades — verified against all 15 real entries.
    """

    def test_all_fifteen_have_explicit_false_flags_and_zero_problems(self):
        records = load_real_records()
        for artifact_id, (raw, record) in records.items():
            with self.subTest(artifact_id=artifact_id):
                problems = validate_artifact_record(record)
                self.assertEqual(problems, [], f"{artifact_id}: {problems}")

    def test_flags_found_in_efeitos_for_founding_thirteen(self):
        _, record = load_real_records()["ART-COIN-MIDAS-0001"]
        self.assertIs(record.efeitos["altera_algoritmo"], False)
        self.assertIs(record.efeitos["altera_resultados"], False)
        self.assertIs(record.efeitos["altera_probabilidades"], False)

    def test_validate_flags_missing_narrative_safety_block(self):
        record = normalize_artifact({"id": "x", "efeitos": {"tipo": "SEM_FLAGS"}})
        problems = validate_artifact_record(record)
        self.assertTrue(any("altera_algoritmo" in p for p in problems))

    def test_validate_flags_a_true_value_as_a_problem(self):
        record = normalize_artifact({
            "id": "x",
            "efeitos": {"altera_algoritmo": True, "altera_resultados": False, "altera_probabilidades": False},
        })
        problems = validate_artifact_record(record)
        self.assertTrue(any("altera_algoritmo is not explicitly False" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
