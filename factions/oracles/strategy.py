"""Oracles — native core.strategy.Faction skeleton.

Not yet wired into manifest.json ("class" is unset) — council.py is
the active registration path for now, consistent with every other
faction in the project. Kept here as the future migration target for
this plugin, per core/plugin_loader.py's documented resolution order.

See council.py for the architecture note on why Oracles don't generate
candidate keys even once implemented.
"""

from core.strategy import Faction, Proposal


class Oracles(Faction):
    """Future role: proposal ranking, confidence estimation,
    meta-analysis of the Council's own proposals. Not implemented yet.
    """

    def propose(self, context: dict) -> list:
        return []
