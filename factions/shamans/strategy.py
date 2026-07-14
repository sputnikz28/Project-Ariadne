"""Shamans — native core.strategy.Faction skeleton.

Not yet wired into manifest.json ("class" is unset) — council.py is
the active registration path for now, consistent with every other
faction in the project. Kept here as the future migration target for
this plugin, per core/plugin_loader.py's documented resolution order.
"""

from core.strategy import Faction, Proposal


class Shamans(Faction):
    """Future role: rare events, outliers, symbolic randomness,
    unusual historical patterns. Not implemented yet.
    """

    def propose(self, context: dict) -> list:
        return []
