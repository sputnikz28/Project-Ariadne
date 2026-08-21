"""Tests for the Minotauro race (Commit 19) — key persistence across
generations inside the Clerics evolutionary population.

Two independent units are covered:
  - factions/clerics/archetypes.py:generate() — the Minotauro branch
    itself (persistence via h.keys[-1], founder birth via
    h.genoma["chave_herdada"] or a fresh RNG key, never
    aplicar_conhecimento()).
  - factions/clerics/algorithm.py:execute() — the reproduction/
    inheritance bookkeeping inside the breeding loop that decides
    whether a newly-bred Minotauro child receives its Minotauro
    parent's last key via f.genoma["chave_herdada"].

The reproduction tests run the real execute() engine with `create()`
and `generate()` replaced by small deterministic stand-ins (so the
test does not depend on unrelated subsystems: other races' generation
logic, artefacts, virus infection, monastery audiences) and with
random.sample/random.choice pinned so the elite pairing and race pick
are fully controlled — everything else in execute()'s reproduction
bookkeeping (elite sort by real pontos, real h.keys.append(), the real
inheritance branch under test) runs unmodified.
"""

import configparser
import itertools
import unittest
from unittest import mock

from factions.clerics import archetypes
from factions.clerics.algorithm import Heroi, execute
from core.services.candidate_provenance import normalize_candidate_record


def make_heroi(raca="Minotauro", keys=None, genoma=None):
    return Heroi(
        id="H-00001",
        name="Testauro",
        raca=raca,
        casa="Casa Lunar",
        generation=1,
        keys=list(keys) if keys is not None else [],
        genoma=dict(genoma) if genoma is not None else {},
    )


def make_ctx():
    return {"estatisticas": {}, "historico": [], "mundo": {}}


class TestGenerateSurvivorPersistence(unittest.TestCase):
    def test_returns_exactly_the_last_key_numeros_and_estrelas(self):
        h = make_heroi(keys=[{"geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}])
        result = archetypes.generate(h, make_ctx())
        self.assertEqual(result, ([1, 2, 3, 4, 5], [1, 2]))

    def test_uses_the_most_recent_entry_when_several_exist(self):
        h = make_heroi(keys=[
            {"geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
            {"geracao": 2, "numeros": [10, 20, 30, 40, 50], "estrelas": [11, 12]},
        ])
        result = archetypes.generate(h, make_ctx())
        self.assertEqual(result, ([10, 20, 30, 40, 50], [11, 12]))

    def test_return_type_is_list_not_the_stored_list(self):
        stored = {"geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}
        h = make_heroi(keys=[stored])
        numeros, estrelas = archetypes.generate(h, make_ctx())
        self.assertIsInstance(numeros, list)
        self.assertIsInstance(estrelas, list)
        self.assertIsNot(numeros, stored["numeros"])
        self.assertIsNot(estrelas, stored["estrelas"])

    def test_never_calls_aplicar_conhecimento(self):
        h = make_heroi(
            keys=[{"geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}],
            genoma={"conhecimento_oculto": [{"numeros": [99], "estrelas": [11]}]},
        )
        with mock.patch("factions.clerics.archetypes.aplicar_conhecimento", side_effect=AssertionError("must not be called")):
            result = archetypes.generate(h, make_ctx())
        self.assertEqual(result, ([1, 2, 3, 4, 5], [1, 2]))

    def test_ignores_chave_herdada_once_keys_exist(self):
        # chave_herdada is a birth-only mechanism. Once a Minotauro has
        # survived a generation, its persistence must come exclusively
        # from h.keys[-1] — a leftover/stale genoma["chave_herdada"]
        # must never be consulted again.
        h = make_heroi(
            keys=[{"geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}],
            genoma={"chave_herdada": ((10, 11, 12, 13, 14), (10, 11))},
        )
        result = archetypes.generate(h, make_ctx())
        self.assertEqual(result, ([1, 2, 3, 4, 5], [1, 2]))

    def test_distinct_generations_never_share_the_same_list_object(self):
        h = make_heroi(keys=[{"geracao": 1, "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}])
        ctx = make_ctx()
        for g in (2, 3, 4):
            numeros, estrelas = archetypes.generate(h, ctx)
            h.keys.append({"geracao": g, "numeros": numeros, "estrelas": estrelas})
        numero_lists = [entry["numeros"] for entry in h.keys]
        estrela_lists = [entry["estrelas"] for entry in h.keys]
        for a, b in itertools.combinations(numero_lists, 2):
            self.assertEqual(a, b)
            self.assertIsNot(a, b)
        for a, b in itertools.combinations(estrela_lists, 2):
            self.assertEqual(a, b)
            self.assertIsNot(a, b)


class TestGenerateFounderBirth(unittest.TestCase):
    def test_uses_chave_herdada_when_present_and_no_keys_yet(self):
        h = make_heroi(keys=[], genoma={"chave_herdada": ((10, 11, 12, 13, 14), (10, 11))})
        result = archetypes.generate(h, make_ctx())
        self.assertEqual(result, ([10, 11, 12, 13, 14], [10, 11]))

    def test_chave_herdada_return_type_is_list(self):
        h = make_heroi(keys=[], genoma={"chave_herdada": ((10, 11, 12, 13, 14), (10, 11))})
        numeros, estrelas = archetypes.generate(h, make_ctx())
        self.assertIsInstance(numeros, list)
        self.assertIsInstance(estrelas, list)

    def test_founder_with_chave_herdada_never_calls_aplicar_conhecimento(self):
        h = make_heroi(
            keys=[],
            genoma={
                "chave_herdada": ((10, 11, 12, 13, 14), (10, 11)),
                "conhecimento_oculto": [{"numeros": [99], "estrelas": [11]}],
            },
        )
        with mock.patch("factions.clerics.archetypes.aplicar_conhecimento", side_effect=AssertionError("must not be called")):
            result = archetypes.generate(h, make_ctx())
        self.assertEqual(result, ([10, 11, 12, 13, 14], [10, 11]))

    def test_without_chave_herdada_generates_a_fresh_valid_key(self):
        import random
        random.seed(20260819)
        h = make_heroi(keys=[], genoma={})
        numeros, estrelas = archetypes.generate(h, make_ctx())
        self.assertEqual(len(numeros), 5)
        self.assertEqual(len(set(numeros)), 5)
        self.assertTrue(all(1 <= n <= 50 for n in numeros))
        self.assertEqual(numeros, sorted(numeros))
        self.assertEqual(len(estrelas), 2)
        self.assertEqual(len(set(estrelas)), 2)
        self.assertTrue(all(1 <= e <= 12 for e in estrelas))
        self.assertEqual(estrelas, sorted(estrelas))

    def test_without_chave_herdada_never_calls_aplicar_conhecimento(self):
        h = make_heroi(keys=[], genoma={"conhecimento_oculto": [{"numeros": [99], "estrelas": [11]}]})
        with mock.patch("factions.clerics.archetypes.aplicar_conhecimento", side_effect=AssertionError("must not be called")):
            archetypes.generate(h, make_ctx())

    def test_same_seed_gives_same_founder_key(self):
        import random

        random.seed(20260819)
        h1 = make_heroi(keys=[], genoma={})
        result1 = archetypes.generate(h1, make_ctx())

        random.seed(20260819)
        h2 = make_heroi(keys=[], genoma={})
        result2 = archetypes.generate(h2, make_ctx())

        self.assertEqual(result1, result2)


class TestGenerateProvenanceUnaffected(unittest.TestCase):
    def test_minotauro_normalizes_as_evolutionary_individual_with_race_minotauro(self):
        record = {
            "geracao": 3, "id": "H-00042", "nome": "Testauro da Cripta",
            "classe": "Minotauro", "casa": "Casa Lunar",
            "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2],
            "origem": "racas_antigas", "virus": None,
        }
        result = normalize_candidate_record(record)
        self.assertEqual(result.source_type, "evolutionary_individual")
        self.assertEqual(result.race, "Minotauro")


class TestNoCandidateModuleImports(unittest.TestCase):
    def test_algorithm_and_archetypes_never_import_candidate_evaluation_or_performance(self):
        import factions.clerics.algorithm as algorithm_module
        import factions.clerics.archetypes as archetypes_module
        for module in (algorithm_module, archetypes_module):
            with open(module.__file__, "r", encoding="utf-8") as fh:
                source = fh.read()
            self.assertNotIn("candidate_evaluation", source)
            self.assertNotIn("candidate_performance", source)


def make_cfg():
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        "SIMULACAO": {"populacao_inicial": "3", "geracoes": "2", "sobreviventes": "2"},
        "CAMINHO_1000_ALMAS": {"ativo": "false"},
        "ARTEFACTOS_VIVOS": {"ativo": "false"},
    })
    return cfg


def run_breeding_scenario(p1_raca, p2_raca, forced_child_raca, p1_key, p2_key):
    """Runs the real execute() with create()/generate() replaced by
    deterministic stand-ins and random.sample/random.choice pinned, so
    only the reproduction/inheritance bookkeeping under test runs
    unmodified. Returns the bred child Heroi (id H-00004).
    """
    p3_key = ([20, 21, 22, 23, 24], [10, 11])
    alvo = {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}
    ctx = {"historico": [alvo], "estatisticas": {}, "mundo": {}}

    templates = [
        Heroi(id="", name="P1", raca=p1_raca, casa="Casa Lunar", generation=1),
        Heroi(id="", name="P2", raca=p2_raca, casa="Casa Lunar", generation=1),
        Heroi(id="", name="P3", raca="Goblin", casa="Casa Lunar", generation=1),
    ]
    call_count = [0]

    def fake_create(i, g=1, pais=None):
        idx = call_count[0]
        call_count[0] += 1
        if idx < len(templates):
            h = templates[idx]
            h.id = f"H-{i:05d}"
            h.generation = g
            h.pais = pais or []
            return h
        return Heroi(id=f"H-{i:05d}", name="Child", raca="Goblin", casa="Casa Lunar", generation=g, pais=pais or [])

    keys_by_id = {"H-00001": p1_key, "H-00002": p2_key, "H-00003": p3_key}

    def fake_generate(h, ctx):
        return keys_by_id.get(h.id, ([1, 2, 3, 4, 5], [1, 2]))

    race_pair = [p1_raca, p2_raca]

    def controlled_choice(seq):
        seq_list = list(seq)
        if seq_list == race_pair:
            return forced_child_raca
        return seq_list[0]

    def identity_sample(population, k):
        return list(population)[:k]

    with mock.patch("factions.clerics.algorithm.create", side_effect=fake_create), \
         mock.patch("factions.clerics.algorithm.generate", side_effect=fake_generate), \
         mock.patch("factions.clerics.algorithm.infetar", return_value=None), \
         mock.patch("factions.clerics.algorithm.tentar_encontrar", return_value=0), \
         mock.patch("factions.clerics.algorithm.conceder_audiencia", return_value=None), \
         mock.patch("random.choice", side_effect=controlled_choice), \
         mock.patch("random.sample", side_effect=identity_sample):
        result = execute(make_cfg(), ctx)

    return result["todos"]["H-00004"]


P1_KEY = ([1, 2, 3, 4, 5], [1, 2])
P2_KEY = ([1, 2, 3, 4, 20], [1, 2])


class TestReproductionInheritance(unittest.TestCase):
    def test_child_of_minotauro_p1_inherits_p1_key(self):
        child = run_breeding_scenario("Minotauro", "Bruxa", "Minotauro", P1_KEY, P2_KEY)
        self.assertEqual(child.genoma.get("chave_herdada"), (tuple(P1_KEY[0]), tuple(P1_KEY[1])))

    def test_child_of_minotauro_p2_only_inherits_p2_key(self):
        child = run_breeding_scenario("Bruxa", "Minotauro", "Minotauro", P1_KEY, P2_KEY)
        self.assertEqual(child.genoma.get("chave_herdada"), (tuple(P2_KEY[0]), tuple(P2_KEY[1])))

    def test_both_parents_minotauro_p1_takes_precedence(self):
        child = run_breeding_scenario("Minotauro", "Minotauro", "Minotauro", P1_KEY, P2_KEY)
        self.assertEqual(child.genoma.get("chave_herdada"), (tuple(P1_KEY[0]), tuple(P1_KEY[1])))

    def test_non_minotauro_child_of_minotauro_parent_does_not_inherit(self):
        child = run_breeding_scenario("Minotauro", "Bruxa", "Bruxa", P1_KEY, P2_KEY)
        self.assertNotIn("chave_herdada", child.genoma)

    def test_minotauro_child_without_minotauro_parent_has_no_inherited_key(self):
        child = run_breeding_scenario("Bruxa", "Shaman", "Minotauro", P1_KEY, P2_KEY)
        self.assertNotIn("chave_herdada", child.genoma)

    def test_inherited_key_does_not_alias_parent_mutable_list(self):
        mutable_p1_numeros = [1, 2, 3, 4, 5]
        p1_key = (mutable_p1_numeros, [1, 2])
        child = run_breeding_scenario("Minotauro", "Bruxa", "Minotauro", p1_key, P2_KEY)
        inherited_numeros_before = child.genoma["chave_herdada"][0]
        mutable_p1_numeros[0] = 999
        self.assertEqual(inherited_numeros_before, (1, 2, 3, 4, 5))
        self.assertNotEqual(inherited_numeros_before, tuple(mutable_p1_numeros))


if __name__ == "__main__":
    unittest.main()
