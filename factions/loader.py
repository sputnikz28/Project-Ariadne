import importlib
from pathlib import Path


def discover_factions(factions_dir="factions"):
    """Yield loaded council modules for all factions with FACTION_META + council()."""
    base = Path(factions_dir)
    if not base.is_dir():
        return
    for faction_dir in sorted(base.iterdir()):
        if not faction_dir.is_dir() or faction_dir.name.startswith('_'):
            continue
        if not (faction_dir / 'council.py').exists():
            continue
        mod_name = f"{factions_dir}.{faction_dir.name}.council"
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, 'FACTION_META') and hasattr(mod, 'council'):
                yield mod
        except ImportError as e:
            print(f"Warning: could not load {mod_name}: {e}")
