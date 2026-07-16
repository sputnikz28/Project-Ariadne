"""Tests for core/plugin_loader.py — CompatFaction wrapper and load_faction()."""

import types
import unittest
from configparser import ConfigParser
from pathlib import Path

from core.plugin_loader import CompatFaction, _load_manifest, load_faction


def _stub_module(council_fn):
    """A minimal stand-in for an imported council.py module."""
    mod = types.SimpleNamespace()
    mod.council = council_fn
    return mod


class TestLoadManifest(unittest.TestCase):
    def test_missing_manifest_returns_none(self):
        self.assertIsNone(_load_manifest(Path("tests/fixtures/fake_factions/real_faction")))

    def test_real_faction_manifest_parses(self):
        manifest = _load_manifest(Path("factions/kors"))
        self.assertEqual(manifest["id"], "kors_elarion")
        self.assertTrue(manifest["votes"])


class TestLoadFaction(unittest.TestCase):
    def test_directory_without_council_or_manifest_class_returns_none(self):
        self.assertIsNone(load_faction(Path("tests/fixtures/fake_factions/real_faction")))

    def test_nonexistent_directory_returns_none(self):
        self.assertIsNone(load_faction(Path("factions/does_not_exist")))

    def test_analytical_faction_without_council_function_returns_none(self):
        # chaos_cartographers has a council.py but no FACTION_META/council() —
        # it is analytical and must not be treated as a voting faction.
        self.assertIsNone(load_faction(Path("factions/chaos_cartographers")))

    def test_standard_faction_loads_as_compat_faction(self):
        faction = load_faction(Path("factions/kors"))
        self.assertIsInstance(faction, CompatFaction)
        self.assertEqual(faction.name, "Kors de Elarion")
        self.assertEqual(faction.origin, "kors_elarion")


class TestCompatFactionProposeShapes(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "config_section": "TESTE",
            "weight_key": "peso_conselho",
            "default_weight": 0.5,
        }
        self.cfg = ConfigParser()
        self.cfg.add_section("TESTE")
        self.cfg.set("TESTE", "peso_conselho", "0.75")
        self.context = {"ariadne": None, "seed": 1, "cfg": self.cfg}

    def test_standard_list_of_dicts(self):
        def council(ariadne, seed, cfg, ctx):
            return [{"nome": "Herói de Teste", "chave": ([1, 2, 3, 4, 5], [1, 2]), "tipo": "Testador"}]

        faction = CompatFaction(_stub_module(council), self.manifest)
        proposals = faction.propose(self.context)
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].name, "Herói de Teste")
        self.assertEqual(proposals[0].key, ([1, 2, 3, 4, 5], [1, 2]))
        self.assertEqual(proposals[0].weight, 0.75)
        self.assertEqual(proposals[0].faction_class, "Testador")

    def test_standard_dict_uses_explicit_weight_over_default(self):
        def council(ariadne, seed, cfg, ctx):
            return [{"nome": "Herói", "chave": ([1, 2, 3, 4, 5], [1, 2]), "peso": 3.3}]

        faction = CompatFaction(_stub_module(council), self.manifest)
        proposals = faction.propose(self.context)
        self.assertEqual(proposals[0].weight, 3.3)

    def test_dwarves_style_clan_with_carteira_expands_to_multiple_proposals(self):
        def council(ariadne, seed, cfg, ctx):
            return [{
                "nome": "Clã Ferro",
                "carteira": [([1, 2, 3, 4, 5], [1, 2]), ([6, 7, 8, 9, 10], [3, 4])],
            }]

        faction = CompatFaction(_stub_module(council), self.manifest)
        proposals = faction.propose(self.context)
        self.assertEqual(len(proposals), 2)
        self.assertEqual(proposals[0].name, "Clã Ferro #1")
        self.assertEqual(proposals[1].name, "Clã Ferro #2")
        self.assertEqual(proposals[0].extra["clan_nome"], "Clã Ferro")

    def test_werewolves_style_inactive_returns_no_proposals(self):
        def council(ariadne, seed, cfg, ctx):
            return {"ativo": False, "simulacoes": 0, "finalistas": []}

        faction = CompatFaction(_stub_module(council), self.manifest)
        self.assertEqual(faction.propose(self.context), [])

    def test_werewolves_style_active_returns_finalists_with_simulation_count(self):
        def council(ariadne, seed, cfg, ctx):
            return {
                "ativo": True,
                "simulacoes": 500,
                "finalistas": [{"nome": "Lobo Vencedor", "chave": ([1, 2, 3, 4, 5], [1, 2])}],
            }

        faction = CompatFaction(_stub_module(council), self.manifest)
        proposals = faction.propose(self.context)
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].extra["simulacoes"], 500)

    def test_non_dict_entries_in_results_are_skipped(self):
        def council(ariadne, seed, cfg, ctx):
            return [None, "not a dict", {"nome": "Válido", "chave": ([1, 2, 3, 4, 5], [1, 2])}]

        faction = CompatFaction(_stub_module(council), self.manifest)
        proposals = faction.propose(self.context)
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].name, "Válido")

    def test_falls_back_to_default_weight_without_cfg(self):
        def council(ariadne, seed, cfg, ctx):
            return [{"nome": "Herói", "chave": ([1, 2, 3, 4, 5], [1, 2])}]

        faction = CompatFaction(_stub_module(council), self.manifest)
        proposals = faction.propose({"ariadne": None, "seed": 1, "cfg": None})
        self.assertEqual(proposals[0].weight, 0.5)


if __name__ == "__main__":
    unittest.main()
