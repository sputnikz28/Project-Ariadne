"""LegendRegistry — permanent, append-only storage of Legends.

entries/<source_prediction_id>.json are the source of truth, keyed by
source_prediction_id (the same draw-independent identity Heroes already
use) rather than by legend_id — this keeps the registry itself decoupled
from legend_evaluation.py's derivation formula for legend_id; it only
ever persists whatever record dict it is given, keyed by the field the
record already carries.

Unlike HeroRegistry, a Legend is not fully immutable from the moment of
creation: a fixed set of "frozen" fields (promotion_draw,
promotion_draw_date, promotion_threshold, promotion_tier,
criteria_version, promotion_hero_ids, and the representative entity
fields) are written once by register() and never touched again. A small,
explicit allowlist of "accumulative" fields (hero_count, qualified_draws,
contributing_hero_ids, provenance, last_reevaluated_at) may be updated
later via refresh() as more Heroes accumulate for the same identity.
There is no delete(), remove() or prune() — once promoted, a Legend is
permanent, full stop.

This is a pure persistence layer: it never calls datetime.now() itself.
Any timestamp it needs to store (last_reevaluated_at, the index's
atualizado_em) is supplied by the caller (evaluate_legends.py), which
decides "now" once per run.

Writes go through core/services/atomic_io.py, exactly like HeroRegistry
— no separate temp-file/fsync logic is reimplemented here.

This module never imports library/heroes/registry.py, never reads
datasets/generated/simulations/arquivo_destino.json, and never touches
simulation_score — it only ever receives already-built Legend record
dicts from its caller and persists them.
"""

from pathlib import Path

from core.services.atomic_io import atomic_write_json, read_json

BASE = Path("library/legends")


class LegendIntegrityError(ValueError):
    """Raised when a stored entry's source_prediction_id does not match
    the source_prediction_id implied by its own filename — a corruption
    or tampering signal, not something to silently paper over.
    """


class LegendAlreadyExistsError(RuntimeError):
    """Raised by register() when a Legend already exists for this
    source_prediction_id. This is an API-usage error: the orchestration
    layer must check existence (or catch this) before deciding whether
    to promote or refresh — register() never silently no-ops and never
    overwrites.
    """


class LegendRegistry:
    # Everything NOT in this set is frozen forever after register().
    # refresh() enforces that boundary itself, not just by convention.
    MUTABLE_FIELDS = {"hero_count", "qualified_draws", "contributing_hero_ids", "provenance", "last_reevaluated_at"}

    def __init__(self, base=None):
        self.base = Path(base) if base is not None else BASE
        self.entries_dir = self.base / "entries"
        self.index_path = self.base / "LIVRO_DAS_LENDAS.json"

    # -- persistence --------------------------------------------------

    def _entry_path(self, source_prediction_id):
        return self.entries_dir / f"{source_prediction_id}.json"

    def exists(self, source_prediction_id):
        return self._entry_path(source_prediction_id).exists()

    def _load_and_verify(self, path):
        """Reads one entry file. Returns None if it isn't valid JSON
        (skipped — consistent with HeroRegistry's tolerance of transient
        corruption). Raises LegendIntegrityError if it IS valid JSON but
        its source_prediction_id doesn't match the filename it's stored
        under — that specific mismatch is never silently accepted.
        """
        record = read_json(path, default=None)
        if record is None:
            return None
        expected_key = path.stem
        actual_key = record.get("source_prediction_id")
        if actual_key != expected_key:
            raise LegendIntegrityError(
                f"{path.name}: content source_prediction_id={actual_key!r} "
                f"does not match filename-derived key {expected_key!r}"
            )
        return record

    def get(self, source_prediction_id):
        path = self._entry_path(source_prediction_id)
        if not path.exists():
            return None
        return self._load_and_verify(path)

    def load_all(self):
        if not self.entries_dir.is_dir():
            return []
        legends = []
        for path in sorted(self.entries_dir.glob("*.json")):
            legend = self._load_and_verify(path)
            if legend is not None:
                legends.append(legend)
        return legends

    def register(self, legend_record):
        """Create a brand-new, permanent Legend — the only way a Legend
        file is ever created. Raises LegendAlreadyExistsError if one
        already exists for this source_prediction_id — calling
        register() twice for the same identity is a usage error, not a
        normal outcome; the caller decides promote vs. refresh by
        checking existence first.
        """
        source_prediction_id = legend_record["source_prediction_id"]
        if self.exists(source_prediction_id):
            raise LegendAlreadyExistsError(
                f"Legend already exists for source_prediction_id={source_prediction_id!r} — "
                "use refresh() to update accumulative fields; register() never overwrites."
            )
        atomic_write_json(self._entry_path(source_prediction_id), legend_record)
        return legend_record

    def refresh(self, source_prediction_id, updates, reevaluated_at):
        """Update only the whitelisted accumulative fields of an
        EXISTING Legend.

        updates: only the substantive accumulative fields (hero_count,
        qualified_draws, contributing_hero_ids, provenance) — never
        last_reevaluated_at, which is supplied separately via
        reevaluated_at and only actually written if updates changes
        something real. Raises ValueError for any field outside the
        substantive allowlist. Raises KeyError if no Legend is
        registered yet for this identity — refresh() never creates one.

        Returns (record, changed); changed=False and NO disk write if
        every field in updates already matches what's stored.
        """
        substantive_fields = self.MUTABLE_FIELDS - {"last_reevaluated_at"}
        disallowed = set(updates) - substantive_fields
        if disallowed:
            raise ValueError(f"refresh() cannot modify frozen field(s) {disallowed} — only {substantive_fields}")

        existing = self.get(source_prediction_id)
        if existing is None:
            raise KeyError(f"no Legend registered yet for source_prediction_id={source_prediction_id!r}")

        if all(existing.get(k) == v for k, v in updates.items()):
            return existing, False

        updated = dict(existing)
        updated.update(updates)
        updated["last_reevaluated_at"] = reevaluated_at
        atomic_write_json(self._entry_path(source_prediction_id), updated)
        return updated, True

    # -- index — fully derived, never a second source of truth --------

    def rebuild_index(self, generated_at, tier_order=None):
        """Regenerate LIVRO_DAS_LENDAS.json purely from entries/. Never
        writes to entries/ — only ever touches index_path, and only
        when the substantive content (everything except atualizado_em)
        actually differs from what's on disk. If nothing changed, the
        existing file — including its old atualizado_em — is returned
        untouched; no write happens.
        """
        legends = self.load_all()
        legends_sorted = self.rank(legends, tier_order)

        by_tier, by_provenance = {}, {}
        for l in legends_sorted:
            by_tier.setdefault(l["promotion_tier"], []).append(l["legend_id"])
            by_provenance[l["provenance"]] = by_provenance.get(l["provenance"], 0) + 1

        candidate = {
            "nome": "Livro das Lendas",
            "total_legends": len(legends_sorted),
            "por_tier": {tier: len(ids) for tier, ids in by_tier.items()},
            "por_provenance": by_provenance,
            "ranking": [l["legend_id"] for l in legends_sorted],
        }

        existing = read_json(self.index_path, default=None)
        if existing is not None:
            existing_without_timestamp = {k: v for k, v in existing.items() if k != "atualizado_em"}
            if existing_without_timestamp == candidate:
                return existing

        index = {**candidate, "atualizado_em": generated_at}
        atomic_write_json(self.index_path, index)
        return index

    # -- lookup / stats -------------------------------------------------

    def all(self):
        return self.load_all()

    def count(self):
        return len(self.load_all())

    TIER_RANK_FALLBACK = 999

    @staticmethod
    def rank(legends, tier_order=None):
        """Deterministic ranking — tier asc, qualified_draws desc,
        hero_count desc, entity_id asc, legend_id asc. No timestamps.
        """
        def key(l):
            tier_rank = (tier_order or {}).get(l["promotion_tier"], LegendRegistry.TIER_RANK_FALLBACK)
            return (tier_rank, -l["qualified_draws"], -l["hero_count"], str(l.get("entity_id") or ""), l["legend_id"])
        return sorted(legends, key=key)

    def statistics(self):
        legends = self.load_all()
        by_tier, by_provenance = {}, {}
        for l in legends:
            by_tier[l["promotion_tier"]] = by_tier.get(l["promotion_tier"], 0) + 1
            by_provenance[l["provenance"]] = by_provenance.get(l["provenance"], 0) + 1
        return {"total": len(legends), "por_tier": by_tier, "por_provenance": by_provenance}
