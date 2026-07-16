"""Clerics — native core.strategy.Faction skeleton.

Not yet wired into manifest.json ("class" is unset) — council.py is
the active registration path for now, consistent with every other
faction in the project. Kept here as the future migration target for
this plugin, per core/plugin_loader.py's documented resolution order.
"""

from core.strategy import Faction, Proposal


class Clerics(Faction):
    """Genetic-algorithm finalists from the 8 historical archetypes."""

    def propose(self, context: dict) -> list:
        return []
