"""Temporal Ariadne source (Commit 23) — the pure building blocks that
let library/ariadne/engine.py:Ariadne be constructed with a
temporally-frozen collection of pergaminhos (scrolls), instead of
reading library/scrolls/ live off disk.

Deliberately not core.services.historical_simulation_source
(Commit 22) reused directly: that module's available_at() is typed for
a draw record (draw['horario']['timestamp_utc'], always that one
location). A pergaminho is a different shape, in one of two different
locations depending on year — reusing available_at() would either
raise (2026-format scrolls have no top-level 'horario') or silently
work by accident only for pre-2026 scrolls. Same discipline
(never infer availability from the date alone, strict <, no fallback
to unfiltered data), reimplemented for the shape that actually exists
here — consistent with the project's established preference for a
small, local duplication over a cross-shape dependency.

Only scroll-based data is covered here. library/indexes/*.json
(duplas.json, triplas.json, saidas_de_bolas_normalizado.json) have no
timestamp of any kind anywhere in their structure — confirmed by
inspection, not assumption — and are explicitly out of scope for
temporal certification in this commit. A temporal Ariadne instance
raises rather than silently answering from those files (see
library/ariadne/engine.py's _require_live_mode()).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

SCROLLS_ROOT = Path("library/scrolls")


def _require_timezone_aware(dt: datetime, label: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware, got a naive datetime: {dt!r}")


def pergaminho_available_at(scroll: Mapping[str, Any]) -> datetime:
    """The single source of truth for "when this pergaminho's draw
    became officially available". Two real, confirmed shapes:

      2026-format  — scroll['data'] is a dict; timestamp lives at
                     scroll['data']['timestamp_utc'].
      2004-2025 format — scroll['data'] is a plain date string;
                     timestamp lives at scroll['horario']['timestamp_utc'].

    Never inferred from the date string alone. Raises KeyError if the
    timestamp field is absent from wherever it should be for that
    shape, ValueError if it can't be parsed as an ISO datetime, and
    ValueError if it parses but is naive.
    """
    data_field = scroll["data"]
    if isinstance(data_field, dict):
        raw = data_field["timestamp_utc"]
    else:
        raw = scroll["horario"]["timestamp_utc"]
    dt = datetime.fromisoformat(raw)
    _require_timezone_aware(dt, "pergaminho timestamp_utc")
    return dt


def load_scrolls(scrolls_root: Path | str | None = None) -> tuple[Mapping[str, Any], ...]:
    """Loads every pergaminho across every year folder under
    library/scrolls/ (same directory shape Ariadne.full_history()
    already walks), sorted ascending by pergaminho_available_at().

    Raw scroll shape, untouched — no adaptation. Unlike
    library/ariadne/engine.py's ler_json(), a malformed JSON file here
    raises rather than being silently skipped — this loader is
    specifically for building a temporally-certified instance, and a
    silently-dropped scroll would be an unsignalled visibility change.

    Every year folder also contains one "indice.json" — a per-year
    manifest, not a pergaminho (confirmed against all 22 real
    occurrences: no 'id'/'data' shape a pergaminho has). Excluded by
    filename explicitly, the same file library/ariadne/engine.py's own
    full_history()/weekly_echoes() already silently tolerate via their
    `raw_data = p.get("data")` -> neither dict nor str -> skip branch.
    """
    root = Path(scrolls_root) if scrolls_root is not None else SCROLLS_ROOT
    if not root.exists():
        return ()
    all_scrolls: list[Mapping[str, Any]] = []
    for pasta_ano in sorted(root.iterdir()):
        if not pasta_ano.is_dir():
            continue
        for path in sorted(pasta_ano.glob("*.json")):
            if path.name == "indice.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                all_scrolls.append(data)
    return tuple(sorted(all_scrolls, key=pergaminho_available_at))


def visible_scrolls(
    scrolls: Sequence[Mapping[str, Any]],
    cutoff_datetime: datetime,
) -> tuple[Mapping[str, Any], ...]:
    """Filters `scrolls` (given order preserved, never reordered here)
    to only those with pergaminho_available_at(s) < cutoff_datetime
    (strict — a pergaminho available exactly at the cutoff instant is
    excluded). Raises ValueError if cutoff_datetime is naive. Never
    mutates `scrolls`. Nothing visible -> () — NEVER falls back to
    `scrolls` unfiltered.
    """
    _require_timezone_aware(cutoff_datetime, "cutoff_datetime")
    return tuple(s for s in scrolls if pergaminho_available_at(s) < cutoff_datetime)


def build_scrolls_for_backtest(
    cutoff_datetime: datetime,
    scrolls_root: Path | str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """load -> filter by cutoff, composed. Ready to pass directly as
    Ariadne(scrolls=...) — see library/ariadne/engine.py.
    """
    all_scrolls = load_scrolls(scrolls_root)
    return visible_scrolls(all_scrolls, cutoff_datetime)
