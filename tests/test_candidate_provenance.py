"""Tests for core/services/candidate_provenance.py. Covers all 18
`origem` values confirmed against the real arquivo_destino.json during
the Commit 16 audit — both synthetic fixtures (for precise field-level
assertions) and real records loaded from the actual archive (to prove
the taxonomy and honesty rules hold against production data, not just
hand-built examples).
"""

import json
import unittest
from pathlib import Path
from types import MappingProxyType

from core.services.candidate_provenance import (
    CandidateKey,
    normalize_candidate_record,
)

REAL_ARCHIVE_PATH = Path("datasets/generated/simulations/arquivo_destino.json")

_EXTERNAL_GENERATOR_ORIGENS = (
    "cla_anao", "fada", "melfork", "treefolk", "cronomante", "esqueleto",
    "vampiro", "gargula", "kors_elarion", "axiomantes_nemerion",
    "esquadrao_negro", "ser_superior",
)
_AGGREGATOR_ORIGENS = ("chave_conselho", "deus")
_TRANSFORMER_ORIGENS = ("corrupcao_final", "necromancia_estatistica")
_CONFIGURED_CANDIDATE_ORIGENS = ("ritual_celeste",)

_ALL_18_ORIGENS = (
    ("racas_antigas", "evolutionary_individual"),
    *((o, "external_generator") for o in _EXTERNAL_GENERATOR_ORIGENS),
    *((o, "aggregator") for o in _AGGREGATOR_ORIGENS),
    *((o, "transformer") for o in _TRANSFORMER_ORIGENS),
    *((o, "configured_candidate") for o in _CONFIGURED_CANDIDATE_ORIGENS),
)


def make_evolutionary_record(**overrides):
    record = {
        "geracao": 7, "id": "H-00042", "nome": "Kael da Lua Fria",
        "classe": "Elfo", "casa": "Casa das Estrelas",
        "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2],
        "origem": "racas_antigas", "virus": None,
    }
    record.update(overrides)
    return record


def make_record(origem, **overrides):
    record = {
        "geracao": 14, "id": "Forja Negra #13", "nome": "Forja Negra #13",
        "classe": "Clã Anão", "casa": "Montanha Eterna",
        "numeros": [10, 20, 30, 40, 50], "estrelas": [3, 7],
        "origem": origem,
    }
    record.update(overrides)
    return record


class TestNormalizeEvolutionaryIndividual(unittest.TestCase):
    def test_generation_entity_id_and_race_are_preserved(self):
        result = normalize_candidate_record(make_evolutionary_record())
        self.assertEqual(result.source_type, "evolutionary_individual")
        self.assertEqual(result.generation, 7)
        self.assertEqual(result.entity_id, "H-00042")
        self.assertEqual(result.entity_name, "Kael da Lua Fria")
        self.assertEqual(result.race, "Elfo")

    def test_numeros_and_estrelas_are_separate_tuples(self):
        result = normalize_candidate_record(make_evolutionary_record())
        self.assertEqual(result.numeros, (1, 2, 3, 4, 5))
        self.assertEqual(result.estrelas, (1, 2))
        self.assertIsInstance(result.numeros, tuple)
        self.assertIsInstance(result.estrelas, tuple)

    def test_metadata_excludes_canonical_fields_but_keeps_the_rest(self):
        result = normalize_candidate_record(make_evolutionary_record())
        for field in ("origem", "numeros", "estrelas", "geracao", "id", "nome", "classe"):
            self.assertNotIn(field, result.metadata)
        self.assertEqual(result.metadata["casa"], "Casa das Estrelas")
        self.assertIn("virus", result.metadata)


class TestNormalizeExternalGenerators(unittest.TestCase):
    def test_all_external_generator_origens_classified_correctly(self):
        for origem in _EXTERNAL_GENERATOR_ORIGENS:
            with self.subTest(origem=origem):
                result = normalize_candidate_record(make_record(origem))
                self.assertEqual(result.source_type, "external_generator")

    def test_fabricated_generation_never_copied(self):
        for origem in _EXTERNAL_GENERATOR_ORIGENS:
            with self.subTest(origem=origem):
                record = make_record(origem, geracao=14)
                result = normalize_candidate_record(record)
                self.assertIsNone(result.generation)

    def test_id_equal_to_nome_never_becomes_entity_id(self):
        for origem in _EXTERNAL_GENERATOR_ORIGENS:
            with self.subTest(origem=origem):
                record = make_record(origem, id="Forja Negra #13", nome="Forja Negra #13")
                result = normalize_candidate_record(record)
                self.assertIsNone(result.entity_id)
                # entity_name still honestly preserved
                self.assertEqual(result.entity_name, "Forja Negra #13")

    def test_classe_never_promoted_to_race(self):
        for origem in _EXTERNAL_GENERATOR_ORIGENS:
            with self.subTest(origem=origem):
                record = make_record(origem, classe="Clã Anão")
                result = normalize_candidate_record(record)
                self.assertIsNone(result.race)

    def test_classe_is_not_leaked_into_metadata_either(self):
        for origem in _EXTERNAL_GENERATOR_ORIGENS:
            with self.subTest(origem=origem):
                record = make_record(origem, classe="Clã Anão")
                result = normalize_candidate_record(record)
                self.assertNotIn("classe", result.metadata)

    def test_entity_name_preserved_even_when_anonymous_per_run(self):
        record = make_record("ser_superior", nome="Mago-1", id="Mago-1")
        result = normalize_candidate_record(record)
        self.assertEqual(result.entity_name, "Mago-1")


class TestNormalizeAggregators(unittest.TestCase):
    def test_conselho_and_aion_classified_as_aggregator(self):
        for origem in _AGGREGATOR_ORIGENS:
            with self.subTest(origem=origem):
                result = normalize_candidate_record(make_record(origem))
                self.assertEqual(result.source_type, "aggregator")
                self.assertIsNone(result.generation)
                self.assertIsNone(result.entity_id)
                self.assertIsNone(result.race)


class TestNormalizeTransformers(unittest.TestCase):
    def test_corrupcao_and_necromancia_classified_as_transformer(self):
        for origem in _TRANSFORMER_ORIGENS:
            with self.subTest(origem=origem):
                result = normalize_candidate_record(make_record(origem))
                self.assertEqual(result.source_type, "transformer")
                self.assertIsNone(result.generation)
                self.assertIsNone(result.entity_id)
                self.assertIsNone(result.race)


class TestNormalizeConfiguredCandidate(unittest.TestCase):
    def test_ritual_celeste_classified_as_configured_candidate(self):
        result = normalize_candidate_record(make_record("ritual_celeste"))
        self.assertEqual(result.source_type, "configured_candidate")
        self.assertIsNone(result.generation)
        self.assertIsNone(result.entity_id)
        self.assertIsNone(result.race)


class TestUnknownOrigem(unittest.TestCase):
    def test_unrecognized_origem_raises_value_error(self):
        record = make_record("uma_origem_nova_desconhecida")
        with self.assertRaises(ValueError):
            normalize_candidate_record(record)


class TestGenericInvariants(unittest.TestCase):
    def test_does_not_mutate_input_record(self):
        record = make_record("cla_anao", extra={"score": 42})
        before = json.loads(json.dumps(record))
        normalize_candidate_record(record)
        self.assertEqual(record, before)

    def test_metadata_is_read_only(self):
        result = normalize_candidate_record(make_record("cla_anao", casa="Montanha Eterna"))
        self.assertIsInstance(result.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            result.metadata["casa"] = "outra coisa"

    def test_candidate_key_dataclass_itself_is_frozen(self):
        result = normalize_candidate_record(make_record("cla_anao"))
        with self.assertRaises(Exception):
            result.source_type = "aggregator"

    def test_metadata_never_contains_any_canonical_field(self):
        record = make_record(
            "esquadrao_negro",
            casa="Biblioteca Sombria",
            score_negro=0.87,
            nivel_grimorio=3,
        )
        result = normalize_candidate_record(record)
        for field in ("origem", "numeros", "estrelas", "geracao", "id", "nome", "classe"):
            self.assertNotIn(field, result.metadata)
        self.assertEqual(result.metadata["casa"], "Biblioteca Sombria")
        self.assertEqual(result.metadata["score_negro"], 0.87)
        self.assertEqual(result.metadata["nivel_grimorio"], 3)

    def test_no_candidate_id_or_derived_from_attributes_exist(self):
        result = normalize_candidate_record(make_record("cla_anao"))
        self.assertFalse(hasattr(result, "candidate_id"))
        self.assertFalse(hasattr(result, "derived_from"))
        self.assertFalse(hasattr(result, "derived_from_id"))


@unittest.skipUnless(REAL_ARCHIVE_PATH.exists(), "real prediction archive not present in this checkout")
class TestAgainstRealArchive(unittest.TestCase):
    """Confirms the closed taxonomy and honesty rules against real,
    already-persisted records — not just hand-built fixtures — for
    every one of the 18 origens found during the Commit 16 audit.
    """

    @classmethod
    def setUpClass(cls):
        records = json.loads(REAL_ARCHIVE_PATH.read_text(encoding="utf-8"))
        cls.sample_by_origem = {}
        for record in records:
            origem = record.get("origem")
            if origem and origem not in cls.sample_by_origem:
                cls.sample_by_origem[origem] = record
            if len(cls.sample_by_origem) == len(_SOURCE_TYPE_BY_ORIGEM_KEYS):
                break

    def test_every_known_origem_is_present_in_the_real_archive(self):
        # Sanity check on the audit itself: if this ever fails, the real
        # archive no longer has one of the 18 origens the taxonomy was
        # built from — worth re-auditing, not silently ignoring.
        missing = set(_SOURCE_TYPE_BY_ORIGEM_KEYS) - set(self.sample_by_origem)
        self.assertEqual(missing, set(), f"origens missing from the real archive: {missing}")

    def test_every_real_sample_normalizes_without_error_and_with_correct_source_type(self):
        for origem, expected_source_type in _ALL_18_ORIGENS:
            with self.subTest(origem=origem):
                record = self.sample_by_origem[origem]
                result = normalize_candidate_record(record)
                self.assertEqual(result.source_type, expected_source_type)
                self.assertIsInstance(result.numeros, tuple)
                self.assertIsInstance(result.estrelas, tuple)

    def test_real_racas_antigas_sample_has_real_generation_and_entity_id(self):
        record = self.sample_by_origem["racas_antigas"]
        result = normalize_candidate_record(record)
        self.assertIsNotNone(result.generation)
        self.assertIsNotNone(result.entity_id)
        self.assertIsNotNone(result.race)
        self.assertEqual(result.generation, record["geracao"])
        self.assertEqual(result.entity_id, record["id"])
        self.assertEqual(result.race, record["classe"])

    def test_real_non_evolutionary_samples_never_carry_generation_entity_id_or_race(self):
        for origem, source_type in _ALL_18_ORIGENS:
            if source_type == "evolutionary_individual":
                continue
            with self.subTest(origem=origem):
                record = self.sample_by_origem[origem]
                result = normalize_candidate_record(record)
                self.assertIsNone(result.generation)
                self.assertIsNone(result.entity_id)
                self.assertIsNone(result.race)


_SOURCE_TYPE_BY_ORIGEM_KEYS = tuple(o for o, _ in _ALL_18_ORIGENS)


if __name__ == "__main__":
    unittest.main()
