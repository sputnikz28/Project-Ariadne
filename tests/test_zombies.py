"""Tests for the Zombie race (Commit 26) — territory + local Monte
Carlo exploration inside the Clerics evolutionary population.

Two independent units are covered:
  - factions/clerics/archetypes.py:generate() — the Zombie branch, its
    four helper functions (_zombie_config, _nascer_territorio_zombie,
    mutar_territorio_zombie, _explorar_territorio_zombie).
  - factions/clerics/algorithm.py:execute() — the reproduction/
    inheritance bookkeeping deciding whether a newly-bred Zombie child
    receives (a mutated copy of) its Zombie parent's territory.

The reproduction tests reuse the exact same harness pattern already
established in tests/test_minotauros.py: run the real execute() engine
with create()/generate() replaced by small deterministic stand-ins,
and random.sample/random.choice pinned, so only the real inheritance
branch under test runs unmodified.
"""

import configparser
import random
import unittest
from unittest import mock

from factions.clerics import archetypes
from factions.clerics.algorithm import Heroi, execute
from core.services.candidate_provenance import normalize_candidate_record
from core.services.fitness import fitness


def make_heroi(raca="Zombie", genoma=None):
    return Heroi(
        id="H-00001",
        name="Testombie",
        raca=raca,
        casa="Casa do Bosque",
        generation=1,
        genoma=dict(genoma) if genoma is not None else {},
    )


def make_ctx(estatisticas=None):
    return {
        "estatisticas": estatisticas or {"quentes": list(range(1, 13)), "frios": list(range(38, 51))},
        "historico": [{"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}],
        "mundo": {"fase_lua": "Lua cheia", "jackpot": 0},
    }


def make_cfg(**overrides):
    cfg = configparser.ConfigParser()
    sections = {
        "ZOMBIES": {
            "tamanho_pool_numeros": "12",
            "tamanho_pool_estrelas": "5",
            "n_simulacoes": "50",
            "taxa_mutacao_territorio": "0.10",
        },
    }
    for section, keys in overrides.items():
        sections.setdefault(section, {}).update(keys)
    cfg.read_dict(sections)
    return cfg


class TestZombieConfig(unittest.TestCase):
    def test_none_cfg_uses_hardcoded_defaults(self):
        result = archetypes._zombie_config(None)
        self.assertEqual(result, {"tamanho_pool_numeros": 12, "tamanho_pool_estrelas": 5, "n_simulacoes": 300})

    def test_cfg_without_zombies_section_falls_back_to_same_defaults(self):
        cfg = configparser.ConfigParser()
        result = archetypes._zombie_config(cfg)
        self.assertEqual(result, {"tamanho_pool_numeros": 12, "tamanho_pool_estrelas": 5, "n_simulacoes": 300})

    def test_cfg_values_are_read_when_present(self):
        cfg = make_cfg(ZOMBIES={"tamanho_pool_numeros": "20", "tamanho_pool_estrelas": "8", "n_simulacoes": "77"})
        result = archetypes._zombie_config(cfg)
        self.assertEqual(result, {"tamanho_pool_numeros": 20, "tamanho_pool_estrelas": 8, "n_simulacoes": 77})


class TestNascerTerritorioZombie(unittest.TestCase):
    def test_pool_sizes_and_bounds(self):
        rng = random.Random(1)
        territorio = archetypes._nascer_territorio_zombie(rng, 12, 5)
        self.assertEqual(len(territorio["pool_numeros"]), 12)
        self.assertEqual(len(territorio["pool_estrelas"]), 5)
        self.assertTrue(all(1 <= n <= 50 for n in territorio["pool_numeros"]))
        self.assertTrue(all(1 <= e <= 12 for e in territorio["pool_estrelas"]))

    def test_pool_values_are_unique(self):
        rng = random.Random(2)
        territorio = archetypes._nascer_territorio_zombie(rng, 12, 5)
        self.assertEqual(len(set(territorio["pool_numeros"])), 12)
        self.assertEqual(len(set(territorio["pool_estrelas"])), 5)

    def test_pools_are_sorted(self):
        rng = random.Random(3)
        territorio = archetypes._nascer_territorio_zombie(rng, 12, 5)
        self.assertEqual(territorio["pool_numeros"], sorted(territorio["pool_numeros"]))
        self.assertEqual(territorio["pool_estrelas"], sorted(territorio["pool_estrelas"]))

    def test_custom_pool_sizes_respected(self):
        rng = random.Random(4)
        territorio = archetypes._nascer_territorio_zombie(rng, 20, 8)
        self.assertEqual(len(territorio["pool_numeros"]), 20)
        self.assertEqual(len(territorio["pool_estrelas"]), 8)


class TestMutarTerritorioZombie(unittest.TestCase):
    def setUp(self):
        self.territorio = {"pool_numeros": list(range(1, 13)), "pool_estrelas": [1, 2, 3, 4, 5]}

    def test_zero_mutation_rate_never_changes_pools(self):
        rng = random.Random(5)
        mutado = archetypes.mutar_territorio_zombie(self.territorio, rng, 0.0)
        self.assertEqual(mutado, self.territorio)

    def test_size_always_preserved(self):
        rng = random.Random(6)
        mutado = archetypes.mutar_territorio_zombie(self.territorio, rng, 1.0)
        self.assertEqual(len(mutado["pool_numeros"]), len(self.territorio["pool_numeros"]))
        self.assertEqual(len(mutado["pool_estrelas"]), len(self.territorio["pool_estrelas"]))

    def test_uniqueness_always_preserved(self):
        rng = random.Random(7)
        mutado = archetypes.mutar_territorio_zombie(self.territorio, rng, 1.0)
        self.assertEqual(len(set(mutado["pool_numeros"])), len(mutado["pool_numeros"]))
        self.assertEqual(len(set(mutado["pool_estrelas"])), len(mutado["pool_estrelas"]))

    def test_bounds_always_respected(self):
        rng = random.Random(8)
        mutado = archetypes.mutar_territorio_zombie(self.territorio, rng, 1.0)
        self.assertTrue(all(1 <= n <= 50 for n in mutado["pool_numeros"]))
        self.assertTrue(all(1 <= e <= 12 for e in mutado["pool_estrelas"]))

    def test_never_fully_rebuilt_at_moderate_rate(self):
        # at 0.10, most elements should survive unchanged for a pool this size
        rng = random.Random(9)
        mutado = archetypes.mutar_territorio_zombie(self.territorio, rng, 0.10)
        overlap_numeros = set(mutado["pool_numeros"]) & set(self.territorio["pool_numeros"])
        self.assertGreater(len(overlap_numeros), 0)

    def test_does_not_mutate_input_territorio(self):
        original = {"pool_numeros": list(self.territorio["pool_numeros"]), "pool_estrelas": list(self.territorio["pool_estrelas"])}
        rng = random.Random(10)
        archetypes.mutar_territorio_zombie(self.territorio, rng, 1.0)
        self.assertEqual(self.territorio, original)


class TestExplorarTerritorioZombieArgmax(unittest.TestCase):
    def test_returned_key_matches_independently_replayed_argmax(self):
        territorio = {"pool_numeros": [1, 5, 9, 14, 20, 27, 33], "pool_estrelas": [2, 5, 8]}
        est = {"quentes": [1, 5, 9], "frios": [33]}
        n_simulacoes = 25

        resultado = archetypes._explorar_territorio_zombie(territorio, est, random.Random(4242), n_simulacoes)

        # Independently replay the exact same RNG stream and compute the
        # max by hand, without calling the function under test again.
        rng_replay = random.Random(4242)
        melhor_manual = None
        melhor_fitness_manual = None
        observed = []
        for _ in range(n_simulacoes):
            nums = sorted(rng_replay.sample(territorio["pool_numeros"], 5))
            ests = sorted(rng_replay.sample(territorio["pool_estrelas"], 2))
            f = fitness((nums, ests), est)
            observed.append(f)
            if melhor_fitness_manual is None or f > melhor_fitness_manual:
                melhor_fitness_manual = f
                melhor_manual = (nums, ests)

        self.assertEqual(resultado, melhor_manual)
        # every observed sample's fitness is <= the winner's fitness
        self.assertTrue(all(f <= melhor_fitness_manual for f in observed))

    def test_result_always_within_territory_pools(self):
        territorio = {"pool_numeros": [2, 6, 11, 19, 25, 30, 41, 48], "pool_estrelas": [1, 4, 7, 10]}
        est = {"quentes": [], "frios": []}
        nums, ests = archetypes._explorar_territorio_zombie(territorio, est, random.Random(11), 40)
        self.assertTrue(set(nums).issubset(set(territorio["pool_numeros"])))
        self.assertTrue(set(ests).issubset(set(territorio["pool_estrelas"])))
        self.assertEqual(len(nums), 5)
        self.assertEqual(len(ests), 2)


class TestGenerateZombieBranch(unittest.TestCase):
    def test_first_call_creates_territory_and_stores_in_genoma(self):
        random.seed(100)
        h = make_heroi()
        self.assertNotIn("territorio_zombie", h.genoma)
        archetypes.generate(h, make_ctx(), make_cfg())
        self.assertIn("territorio_zombie", h.genoma)
        self.assertEqual(len(h.genoma["territorio_zombie"]["pool_numeros"]), 12)

    def test_second_call_reuses_existing_territory_unchanged(self):
        random.seed(101)
        h = make_heroi()
        archetypes.generate(h, make_ctx(), make_cfg())
        territorio_after_first = dict(h.genoma["territorio_zombie"])
        archetypes.generate(h, make_ctx(), make_cfg())
        self.assertEqual(h.genoma["territorio_zombie"], territorio_after_first)

    def test_key_always_within_territory(self):
        random.seed(102)
        h = make_heroi()
        cfg = make_cfg()
        for _ in range(5):
            nums, ests = archetypes.generate(h, make_ctx(), cfg)
            territorio = h.genoma["territorio_zombie"]
            self.assertTrue(set(nums).issubset(set(territorio["pool_numeros"])))
            self.assertTrue(set(ests).issubset(set(territorio["pool_estrelas"])))

    def test_key_shape_is_valid(self):
        random.seed(103)
        h = make_heroi()
        nums, ests = archetypes.generate(h, make_ctx(), make_cfg())
        self.assertEqual(len(nums), 5)
        self.assertEqual(len(set(nums)), 5)
        self.assertEqual(nums, sorted(nums))
        self.assertEqual(len(ests), 2)
        self.assertEqual(len(set(ests)), 2)
        self.assertEqual(ests, sorted(ests))

    def test_never_calls_aplicar_conhecimento(self):
        random.seed(104)
        h = make_heroi(genoma={"conhecimento_oculto": [{"numeros": [99], "estrelas": [11]}]})
        with mock.patch("factions.clerics.archetypes.aplicar_conhecimento", side_effect=AssertionError("must not be called")):
            archetypes.generate(h, make_ctx(), make_cfg())

    def test_none_cfg_falls_back_to_hardcoded_defaults(self):
        random.seed(105)
        h = make_heroi()
        archetypes.generate(h, make_ctx(), None)
        self.assertEqual(len(h.genoma["territorio_zombie"]["pool_numeros"]), 12)
        self.assertEqual(len(h.genoma["territorio_zombie"]["pool_estrelas"]), 5)

    def test_two_arg_call_still_works_backward_compatible(self):
        random.seed(106)
        h = make_heroi()
        nums, ests = archetypes.generate(h, make_ctx())
        self.assertEqual(len(nums), 5)
        self.assertEqual(len(ests), 2)

    def test_same_seed_gives_same_key(self):
        random.seed(107)
        h1 = make_heroi()
        result1 = archetypes.generate(h1, make_ctx(), make_cfg())

        random.seed(107)
        h2 = make_heroi()
        result2 = archetypes.generate(h2, make_ctx(), make_cfg())

        self.assertEqual(result1, result2)
        self.assertEqual(h1.genoma["territorio_zombie"], h2.genoma["territorio_zombie"])


class TestGenerateZombieProvenance(unittest.TestCase):
    def test_zombie_normalizes_as_evolutionary_individual_with_race_zombie(self):
        record = {
            "geracao": 3, "id": "H-00042", "nome": "Testombie do Bosque",
            "classe": "Zombie", "casa": "Casa do Bosque",
            "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2],
            "origem": "racas_antigas", "virus": None,
        }
        result = normalize_candidate_record(record)
        self.assertEqual(result.source_type, "evolutionary_individual")
        self.assertEqual(result.race, "Zombie")


class TestNoUncertifiedMemory(unittest.TestCase):
    def test_algorithm_and_archetypes_never_import_uncertified_sources(self):
        import factions.clerics.algorithm as algorithm_module
        import factions.clerics.archetypes as archetypes_module
        forbidden = ("Ariadne", "grimorio", "library.heroes", "library.legends", "datetime.now(")
        for module in (algorithm_module, archetypes_module):
            with open(module.__file__, "r", encoding="utf-8") as fh:
                source = fh.read()
            for token in forbidden:
                self.assertNotIn(token, source)

    def test_no_candidate_or_temporal_module_imports(self):
        import factions.clerics.algorithm as algorithm_module
        import factions.clerics.archetypes as archetypes_module
        for module in (algorithm_module, archetypes_module):
            with open(module.__file__, "r", encoding="utf-8") as fh:
                source = fh.read()
            self.assertNotIn("candidate_evaluation", source)
            self.assertNotIn("candidate_performance", source)
            self.assertNotIn("backtest_orchestrator", source)
            self.assertNotIn("backtest_lab", source)


def run_breeding_scenario(p1_raca, p2_raca, forced_child_raca, p1_territorio, p2_territorio, taxa_mutacao="0.0"):
    """Mirrors tests/test_minotauros.py's run_breeding_scenario harness
    exactly: create()/generate() replaced by deterministic stand-ins,
    random.sample/random.choice pinned, so only the real Zombie
    inheritance block inside execute() runs unmodified.
    """
    ctx = {"historico": [{"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}], "estatisticas": {}, "mundo": {}}
    cfg = make_cfg(
        SIMULACAO={"populacao_inicial": "3", "geracoes": "2", "sobreviventes": "2"},
        CAMINHO_1000_ALMAS={"ativo": "false"},
        ARTEFACTOS_VIVOS={"ativo": "false"},
        ZOMBIES={"taxa_mutacao_territorio": taxa_mutacao},
    )

    templates = [
        Heroi(id="", name="P1", raca=p1_raca, casa="Casa Lunar", generation=1,
              genoma=({"territorio_zombie": p1_territorio} if p1_territorio else {})),
        Heroi(id="", name="P2", raca=p2_raca, casa="Casa Lunar", generation=1,
              genoma=({"territorio_zombie": p2_territorio} if p2_territorio else {})),
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

    keys_by_id = {"H-00001": ([1, 2, 3, 4, 5], [1, 2]), "H-00002": ([6, 7, 8, 9, 10], [3, 4]), "H-00003": ([20, 21, 22, 23, 24], [10, 11])}

    def fake_generate(h, ctx, cfg=None):
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
        result = execute(cfg, ctx)

    return result["todos"]["H-00004"]


P1_TERRITORIO = {"pool_numeros": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "pool_estrelas": [1, 2, 3, 4, 5]}
P2_TERRITORIO = {"pool_numeros": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41], "pool_estrelas": [8, 9, 10, 11, 12]}


class TestReproductionInheritance(unittest.TestCase):
    def test_child_of_zombie_p1_inherits_p1_territory(self):
        child = run_breeding_scenario("Zombie", "Bruxa", "Zombie", P1_TERRITORIO, None)
        self.assertIn("territorio_zombie", child.genoma)
        self.assertEqual(set(child.genoma["territorio_zombie"]["pool_numeros"]), set(P1_TERRITORIO["pool_numeros"]))

    def test_child_of_zombie_p2_only_inherits_p2_territory(self):
        child = run_breeding_scenario("Bruxa", "Zombie", "Zombie", None, P2_TERRITORIO)
        self.assertIn("territorio_zombie", child.genoma)
        self.assertEqual(set(child.genoma["territorio_zombie"]["pool_numeros"]), set(P2_TERRITORIO["pool_numeros"]))

    def test_both_parents_zombie_p1_takes_precedence(self):
        child = run_breeding_scenario("Zombie", "Zombie", "Zombie", P1_TERRITORIO, P2_TERRITORIO)
        self.assertEqual(set(child.genoma["territorio_zombie"]["pool_numeros"]), set(P1_TERRITORIO["pool_numeros"]))

    def test_non_zombie_child_of_zombie_parent_does_not_inherit(self):
        child = run_breeding_scenario("Zombie", "Bruxa", "Bruxa", P1_TERRITORIO, None)
        self.assertNotIn("territorio_zombie", child.genoma)

    def test_zombie_child_without_zombie_parent_has_no_inherited_territory(self):
        child = run_breeding_scenario("Bruxa", "Shaman", "Zombie", None, None)
        self.assertNotIn("territorio_zombie", child.genoma)

    def test_inherited_territory_is_mutated_copy_not_shared_reference(self):
        child = run_breeding_scenario("Zombie", "Bruxa", "Zombie", P1_TERRITORIO, None, taxa_mutacao="0.0")
        self.assertIsNot(child.genoma["territorio_zombie"], P1_TERRITORIO)
        self.assertIsNot(child.genoma["territorio_zombie"]["pool_numeros"], P1_TERRITORIO["pool_numeros"])
        # taxa_mutacao=0.0 -> content identical, but still a fresh object
        self.assertEqual(child.genoma["territorio_zombie"]["pool_numeros"], P1_TERRITORIO["pool_numeros"])

    def test_territory_is_never_rebuilt_from_scratch_at_moderate_mutation_rate(self):
        child = run_breeding_scenario("Zombie", "Bruxa", "Zombie", P1_TERRITORIO, None, taxa_mutacao="0.10")
        overlap = set(child.genoma["territorio_zombie"]["pool_numeros"]) & set(P1_TERRITORIO["pool_numeros"])
        self.assertGreater(len(overlap), 0)


if __name__ == "__main__":
    unittest.main()
