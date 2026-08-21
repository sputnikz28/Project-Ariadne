"""Temporal Persistent Memory (Commit 24) — the same verified/legacy/
ineligible/unresolved taxonomy hero_evaluation.py's
classify_temporal_provenance() already established (Commits 17/20-23),
resolved from a DIRECT timestamp field already on a persisted memory
record (registado_em/promoted_at/recognized_at), never from run_id ->
manifest indirection. Different families of memory, different honest
signal, same taxonomy and same default policy.

Covers: legacy Legends (docs/lore/legends/livro_personagens_lendarias.json,
registado_em — real, present on 95/95 real entries), and, forward-only,
new Heroes (recognized_at) and new Legends (promoted_at) once
evaluate_heroes.py/evaluate_legends.py start persisting them. Existing
Hero/Legend entries have neither field and stay `legacy` forever — no
migration, no retroactive dating.

Explicitly NOT covered, and explicitly not certifiable by this module:
the Grimório (orders/black_squad/dark_library/grimorio_negro.json) and
the Elven Order's estado_ordem.json. Both are cumulative aggregates
with zero timestamp at any level — individual events feeding them
(book copies, thefts, missions) do carry a real timestamp, but the
aggregate facts actually consulted during generation (grimoire['nivel'],
grimoire['conhecimento'][x]) do not, and cannot be reconstructed here
without inventing one. artifacts/living.py, artifacts/ark.py,
orders/black_squad/persistence.py and orders/elven_order/ninjas.py
never import this module — see
TestUncertifiedModulesNeverClaimTemporalCertification in the test
suite for a standing, structural proof of that.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, Literal

MemoryAvailability = Literal["verified", "legacy", "ineligible", "unresolved"]


def _require_timezone_aware(dt: datetime, label: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware, got a naive datetime: {dt!r}")


def classify_memory_availability(raw_timestamp: Any, cutoff_datetime: datetime) -> MemoryAvailability:
    """raw_timestamp: whatever raw value the record's own timestamp
    field holds — a string, or None/missing. Never inferred from any
    other field (generation, draw_id, filename, run order, mtime).

      verified   - raw_timestamp parses to a tz-aware datetime,
                   < cutoff_datetime (strict).
      legacy     - raw_timestamp is None — the field is genuinely
                   absent, not just malformed.
      ineligible - raw_timestamp parses to a tz-aware datetime,
                   >= cutoff_datetime.
      unresolved - raw_timestamp is present but can't be parsed as a
                   timezone-aware datetime (malformed string, or a
                   naive one).

    Raises ValueError if cutoff_datetime itself is naive.
    """
    _require_timezone_aware(cutoff_datetime, "cutoff_datetime")

    if raw_timestamp is None:
        return "legacy"

    try:
        dt = datetime.fromisoformat(raw_timestamp)
    except (TypeError, ValueError):
        return "unresolved"

    if dt.tzinfo is None or dt.utcoffset() is None:
        return "unresolved"

    return "verified" if dt < cutoff_datetime else "ineligible"


def temporal_memory_view(
    records: Sequence[Any],
    cutoff_datetime: datetime,
    *,
    get_raw_timestamp: Callable[[Any], Any],
    allow_legacy: bool = False,
    allow_unresolved: bool = False,
) -> tuple[Any, ...]:
    """Applies classify_memory_availability() to every record (via
    get_raw_timestamp(record), since different families store their
    timestamp under different keys) and keeps only what's permitted:

      verified   - always included
      legacy     - included only if allow_legacy=True
      unresolved - included only if allow_unresolved=True
      ineligible - NEVER included — no override exists, none is ever
                   added

    Filters silently rather than raising on ineligible entries (unlike
    core.services.backtest_lab.freeze_backtest_candidates): the raw
    collection here naturally contains future-relative-to-cutoff
    entries as an ordinary fact (the memory store keeps growing), not
    as a caller mistake — same reasoning as
    historical_simulation_source.visible_draws()/
    historical_ariadne_source.visible_scrolls().

    Order preserved, `records` never mutated.
    """
    allowed: set[MemoryAvailability] = {"verified"}
    if allow_legacy:
        allowed.add("legacy")
    if allow_unresolved:
        allowed.add("unresolved")

    return tuple(
        record for record in records
        if classify_memory_availability(get_raw_timestamp(record), cutoff_datetime) in allowed
    )
