from __future__ import annotations

import importlib
import json
from pathlib import Path

from core.strategy import Faction, Proposal


class CompatFaction(Faction):
    """Wraps a council.py module (FACTION_META + council()) into the Faction interface.

    Handles three return shapes from council():
      - Standard list of dicts with 'nome', 'chave', optional 'peso'
      - Dwarves-style: list of clan dicts with nested 'carteira' (multiple keys per clan)
      - Werewolves-style: {'ativo': bool, 'simulacoes': int, 'finalistas': list}
    """

    def __init__(self, mod, manifest: dict):
        self.manifest = manifest
        self._mod = mod

    def propose(self, context: dict) -> list:
        results = self._mod.council(
            context.get('ariadne'),
            context.get('seed'),
            context.get('cfg'),
            context,
        )

        cfg = context.get('cfg')
        section = self.manifest.get('config_section', '')
        weight_key = self.manifest.get('weight_key', 'peso_conselho')
        default_weight = float(self.manifest.get('default_weight', 1.0))
        if cfg and section:
            try:
                weight = cfg.getfloat(section, weight_key, fallback=default_weight)
            except Exception:
                weight = default_weight
        else:
            weight = default_weight

        # Werewolves-style: {'ativo': bool, 'simulacoes': int, 'finalistas': list}
        sims = 0
        if isinstance(results, dict):
            if not results.get('ativo', True):
                return []
            sims = results.get('simulacoes', 0)
            results = results.get('finalistas', [])

        proposals = []
        for x in results:
            if not isinstance(x, dict):
                continue

            # Dwarves-style: clan dict with 'carteira' (multiple keys per entry)
            if 'carteira' in x:
                clan_extra = {k: v for k, v in x.items() if k != 'carteira'}
                clan_extra['clan_nome'] = x['nome']
                for ch in x['carteira']:
                    i = len([p for p in proposals if p.extra.get('clan_nome') == x['nome']])
                    proposals.append(Proposal(
                        name=f"{x['nome']} #{i + 1}",
                        key=ch,
                        weight=weight,
                        origin=self.origin,
                        home=self.home,
                        faction_class='Clã Anão',
                        extra=dict(clan_extra),
                    ))
            else:
                extra = {k: v for k, v in x.items()
                         if k not in ('nome', 'tipo', 'classe', 'chave', 'peso')}
                if sims:
                    extra['simulacoes'] = sims
                proposals.append(Proposal(
                    name=x['nome'],
                    key=x['chave'],
                    weight=x.get('peso', weight),
                    origin=self.origin,
                    home=self.home,
                    faction_class=x.get('tipo', x.get('classe', '')),
                    extra=extra,
                ))
        return proposals


def load_faction(faction_dir: Path) -> Faction | None:
    """Load a faction from a directory. Returns a Faction instance or None.

    Resolution order:
    1. manifest.json with "class" key → load named class from strategy.py
    2. council.py with FACTION_META + council() → wrap in CompatFaction
    3. Otherwise → return None (analytical or incomplete faction)
    """
    manifest = _load_manifest(faction_dir)

    # Future: native class-based faction via manifest.json + strategy.py
    if manifest and manifest.get('class') and (faction_dir / 'strategy.py').exists():
        return _load_class_faction(faction_dir, manifest)

    # Current: compatibility wrapper around council.py
    council_path = faction_dir / 'council.py'
    if not council_path.exists():
        return None

    mod_name = f"factions.{faction_dir.name}.council"
    try:
        mod = importlib.import_module(mod_name)
    except ImportError as e:
        print(f"Warning: could not load {mod_name}: {e}")
        return None

    if not (hasattr(mod, 'FACTION_META') and hasattr(mod, 'council')):
        return None  # Analytical faction (chaos_cartographers) — skip

    meta = {**mod.FACTION_META, **(manifest or {})}
    return CompatFaction(mod, meta)


def _load_class_faction(faction_dir: Path, manifest: dict) -> Faction | None:
    """Load a native Faction subclass from strategy.py."""
    mod_name = f"factions.{faction_dir.name}.strategy"
    class_name = manifest['class']
    try:
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, class_name)
        instance = cls()
        instance.manifest = manifest
        return instance
    except Exception as e:
        print(f"Warning: could not load {mod_name}.{class_name}: {e}")
        return None


def _load_manifest(faction_dir: Path) -> dict | None:
    path = faction_dir / 'manifest.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
