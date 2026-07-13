from pathlib import Path


class FactionRegistry:
    """Central registry for all voter factions.

    Usage:
        registry = FactionRegistry()
        registry.discover("factions")
        for faction in registry.all():
            proposals = faction.propose(context)

    Adding a new faction never requires changing main.py:
    just create factions/<name>/ with manifest.json + council.py (or strategy.py).
    """

    def __init__(self):
        self._factions = []

    def register(self, faction) -> None:
        self._factions.append(faction)

    def discover(self, factions_dir="factions") -> 'FactionRegistry':
        """Auto-discover voter factions from directory structure.

        Loads all factions with FACTION_META + council(), or with a class
        referenced in manifest.json. Silently skips analytical factions
        (chaos_cartographers) and directories without a council.py.
        """
        from core.plugin_loader import load_faction
        base = Path(factions_dir)
        if not base.is_dir():
            return self
        for d in sorted(base.iterdir()):
            if not d.is_dir() or d.name.startswith('_'):
                continue
            faction = load_faction(d)
            if faction is not None:
                self.register(faction)
        return self

    def all(self) -> list:
        return list(self._factions)

    def count(self) -> int:
        return len(self._factions)
