"""Tests for core/registry.py — FactionRegistry (discover + register + all)."""

import unittest
from pathlib import Path
from unittest.mock import patch

from core.registry import FactionRegistry


class _FakeFaction:
    def __init__(self, name="Fake"):
        self._name = name

    def propose(self, context):
        return []


class TestRegisterAndAll(unittest.TestCase):
    def test_register_adds_to_all(self):
        registry = FactionRegistry()
        f = _FakeFaction()
        registry.register(f)
        self.assertEqual(registry.all(), [f])

    def test_count_matches_registered_count(self):
        registry = FactionRegistry()
        self.assertEqual(registry.count(), 0)
        registry.register(_FakeFaction("A"))
        registry.register(_FakeFaction("B"))
        self.assertEqual(registry.count(), 2)

    def test_all_returns_a_copy_not_the_internal_list(self):
        registry = FactionRegistry()
        registry.register(_FakeFaction())
        snapshot = registry.all()
        snapshot.append(_FakeFaction("intruder"))
        self.assertEqual(registry.count(), 1)


class TestDiscover(unittest.TestCase):
    def test_discover_nonexistent_directory_is_a_noop(self):
        registry = FactionRegistry().discover("no/such/directory")
        self.assertEqual(registry.count(), 0)

    def test_discover_returns_self_for_chaining(self):
        registry = FactionRegistry()
        result = registry.discover("no/such/directory")
        self.assertIs(result, registry)

    def test_discover_skips_underscore_prefixed_and_non_directories(self, ):
        with patch("core.plugin_loader.load_faction") as mock_load:
            mock_load.return_value = None
            fixtures = Path(__file__).parent / "fixtures" / "fake_factions"
            FactionRegistry().discover(str(fixtures))
            visited = {call.args[0].name for call in mock_load.call_args_list}
            self.assertIn("real_faction", visited)
            self.assertNotIn("_ignored", visited)
            self.assertNotIn("not_a_directory.txt", visited)

    def test_discover_real_factions_directory_finds_known_voting_factions(self):
        registry = FactionRegistry().discover("factions")
        ids = {f.origin for f in registry.all()}
        self.assertIn("axiomantes_nemerion", ids)
        self.assertIn("kors_elarion", ids)

    def test_discover_finds_the_new_mystics_factions(self):
        registry = FactionRegistry().discover("factions")
        ids = {f.origin for f in registry.all()}
        for mystic_id in (
            "druids", "moon_priests", "star_gazers", "shamans",
            "witches", "seers", "oracles", "bone_readers",
        ):
            self.assertIn(mystic_id, ids)

    def test_discover_excludes_analytical_non_voting_factions(self):
        registry = FactionRegistry().discover("factions")
        ids = {f.origin for f in registry.all()}
        self.assertNotIn("chaos_cartographers", ids)

    def test_discover_finds_exactly_the_expected_number_of_voting_factions(self):
        registry = FactionRegistry().discover("factions")
        # 21 faction directories under factions/ (12 pre-Mystics + 8 Mystics
        # orders + clerics, added in the V11 Clerics migration) minus
        # chaos_cartographers (analytical, votes: false) = 20 voting factions.
        self.assertEqual(registry.count(), 20)


if __name__ == "__main__":
    unittest.main()
