"""Tests for core/strategy.py — the shared Proposal/Faction data models."""

import unittest

from core.strategy import Faction, Proposal


class TestProposal(unittest.TestCase):
    def test_required_fields(self):
        p = Proposal(name="Testador", key=([1, 2, 3, 4, 5], [1, 2]), weight=1.0)
        self.assertEqual(p.name, "Testador")
        self.assertEqual(p.key, ([1, 2, 3, 4, 5], [1, 2]))
        self.assertEqual(p.weight, 1.0)

    def test_optional_fields_default(self):
        p = Proposal(name="Testador", key=([1, 2, 3, 4, 5], [1, 2]), weight=1.0)
        self.assertEqual(p.origin, "")
        self.assertEqual(p.home, "")
        self.assertEqual(p.faction_class, "")
        self.assertEqual(p.extra, {})

    def test_extra_default_is_not_shared_between_instances(self):
        a = Proposal(name="A", key=([1], [1]), weight=1.0)
        b = Proposal(name="B", key=([2], [2]), weight=1.0)
        a.extra["marker"] = True
        self.assertNotIn("marker", b.extra)

    def test_all_fields_settable(self):
        p = Proposal(
            name="Testador", key=([1, 2, 3, 4, 5], [1, 2]), weight=0.5,
            origin="teste", home="Casa de Teste", faction_class="Classe X",
            extra={"nota": 1},
        )
        self.assertEqual(p.origin, "teste")
        self.assertEqual(p.home, "Casa de Teste")
        self.assertEqual(p.faction_class, "Classe X")
        self.assertEqual(p.extra, {"nota": 1})


class _DummyFaction(Faction):
    """Minimal concrete Faction used only to exercise the base-class behaviour."""

    def propose(self, context):
        return []


class TestFaction(unittest.TestCase):
    def test_cannot_instantiate_abstract_class_directly(self):
        with self.assertRaises(TypeError):
            Faction()

    def test_name_falls_back_to_class_name_without_manifest(self):
        f = _DummyFaction()
        self.assertEqual(f.name, "_DummyFaction")

    def test_origin_falls_back_to_unknown_without_manifest(self):
        f = _DummyFaction()
        self.assertEqual(f.origin, "unknown")

    def test_home_falls_back_to_empty_string_without_manifest(self):
        f = _DummyFaction()
        self.assertEqual(f.home, "")

    def test_properties_read_from_manifest(self):
        f = _DummyFaction()
        f.manifest = {"name": "Testadores", "id": "testadores", "home": "Torre de Testes"}
        self.assertEqual(f.name, "Testadores")
        self.assertEqual(f.origin, "testadores")
        self.assertEqual(f.home, "Torre de Testes")

    def test_propose_contract_returns_list(self):
        f = _DummyFaction()
        self.assertEqual(f.propose({}), [])


if __name__ == "__main__":
    unittest.main()
