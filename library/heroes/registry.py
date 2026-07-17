"""HeroRegistry — persistent storage for recognised Heroes.

entries/<dedup_hash>.json are the source of truth. LIVRO_DOS_HEROIS.json
is a derived index/summary, always rebuildable from entries/ — never the
only copy. Writes go through core/services/atomic_io.py so a failure
mid-write can't corrupt either file.
"""

from datetime import datetime, timezone
from pathlib import Path

from core.services.atomic_io import atomic_write_json, read_json

BASE = Path("library/heroes")
ENTRIES_DIR = BASE / "entries"
INDEX_PATH = BASE / "LIVRO_DOS_HEROIS.json"


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class HeroRegistry:
    def __init__(self, base=None):
        self.base = Path(base) if base is not None else BASE
        self.entries_dir = self.base / "entries"
        self.index_path = self.base / "LIVRO_DOS_HEROIS.json"

    # -- persistence --------------------------------------------------

    def _entry_path(self, dedup_hash):
        return self.entries_dir / f"{dedup_hash}.json"

    def exists(self, dedup_hash):
        return self._entry_path(dedup_hash).exists()

    def get(self, dedup_hash):
        return read_json(self._entry_path(dedup_hash), default=None)

    def load_all(self):
        if not self.entries_dir.is_dir():
            return []
        heroes = []
        for path in sorted(self.entries_dir.glob("*.json")):
            hero = read_json(path, default=None)
            if hero is not None:
                heroes.append(hero)
        return heroes

    def register(self, hero_record):
        """Persist a Hero record, keyed by its dedup_hash. Returns
        (hero_record, created) — created=False means it already existed
        and this call was a no-op (duplicate prevention).
        """
        dedup_hash = hero_record["dedup_hash"]
        if self.exists(dedup_hash):
            return self.get(dedup_hash), False

        hero_record = dict(hero_record)
        hero_record.setdefault("registered_at", _now_iso())
        atomic_write_json(self._entry_path(dedup_hash), hero_record)
        return hero_record, True

    def rebuild_index(self):
        """Regenerate LIVRO_DOS_HEROIS.json purely from entries/ — the
        index never has information entries/ doesn't already have.
        """
        heroes = self.load_all()
        heroes_sorted = self.rank(heroes)

        by_tier = {}
        by_category = {}
        by_provenance = {}
        for h in heroes_sorted:
            by_tier.setdefault(h["hero_tier"], []).append(h["hero_id"])
            by_category.setdefault(h["hero_category"], []).append(h["hero_id"])
            by_provenance[h["provenance"]] = by_provenance.get(h["provenance"], 0) + 1

        index = {
            "nome": "Livro dos Heróis",
            "total_heroes": len(heroes_sorted),
            "por_tier": {tier: len(ids) for tier, ids in by_tier.items()},
            "por_categoria": {cat: len(ids) for cat, ids in by_category.items()},
            "por_provenance": by_provenance,
            "ranking": [h["hero_id"] for h in heroes_sorted],
            "atualizado_em": _now_iso(),
        }
        atomic_write_json(self.index_path, index)
        return index

    # -- lookup / stats -------------------------------------------------

    def all(self):
        return self.load_all()

    def count(self):
        return len(self.load_all())

    TIER_RANK_FALLBACK = 999

    @staticmethod
    def rank(heroes, tier_order=None):
        """Deterministic ranking — see docs: tier asc, matched numbers
        desc, matched stars desc, simulation score desc (descriptive
        tie-break only), entity_id asc, hero_id asc. No timestamps.
        """
        def key(h):
            tier_rank = (tier_order or {}).get(h["hero_tier"], HeroRegistry.TIER_RANK_FALLBACK)
            return (
                tier_rank,
                -h["matched_numbers_count"],
                -h["matched_stars_count"],
                -h["simulation_score"],
                str(h.get("entity_id") or ""),
                h["hero_id"],
            )
        return sorted(heroes, key=key)

    def statistics(self):
        heroes = self.load_all()
        by_tier = {}
        by_category = {}
        by_provenance = {}
        for h in heroes:
            by_tier[h["hero_tier"]] = by_tier.get(h["hero_tier"], 0) + 1
            by_category[h["hero_category"]] = by_category.get(h["hero_category"], 0) + 1
            by_provenance[h["provenance"]] = by_provenance.get(h["provenance"], 0) + 1
        return {
            "total": len(heroes),
            "por_tier": by_tier,
            "por_categoria": by_category,
            "por_provenance": by_provenance,
        }
