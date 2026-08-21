"""Historical Simulation Source / Temporal Dataset Boundary (Commit 22)
— the missing bridge between the versioned, immutable historical
dataset (datasets/historical/euromillions/, already the source of
truth for core.services.historical_dataset, dashboard_data,
hero_evaluation and backtest_lab) and the legacy flat draw shape that
world/engine/builder.py, core/evolution/statistics.py and the
ctx['historico']-consuming factions (Clerics, Melforks, Dwarves,
Faeries, Werewolves) already expect.

Two temporal modes exist in this project, represented architecturally
as two entirely separate code paths rather than as a runtime flag:

  LIVE/NORMAL   — core/data/loaders.py:get_history() (live API or
                  local cache) + world/engine/builder.py:build().
                  Completely untouched by this module.
  HISTORICAL/BACKTEST — this module. Dataset-only, cutoff mandatory,
                  timezone-aware mandatory, zero fallback to the live
                  API, zero fallback to unfiltered history.

Nothing here is wired into main.py, world/engine/builder.py, or
core/data/loaders.py — this is a standalone, pure service. Wiring it
into an actual backtest orchestrator, and into the Backtest Lab
(Commit 20), is deliberately deferred.

The single public pipeline is:

    load_versioned_history()  -- raw modern draw records, sorted
            |
    visible_draws(..., cutoff_datetime)  -- temporal policy: strict <
            |
    adapt_to_legacy_draw(...)  -- shape compatibility only
            |
    build_historical_context_for_backtest()  -- composes all three

Callers should use build_historical_context_for_backtest() rather than
recomposing the three steps by hand — the composed path is the one
that is structurally hard to use incorrectly (impossible to forget the
cutoff, impossible to accidentally adapt before filtering).

Field mapping honesty (adapt_to_legacy_draw)
--------------------------------------------------------------------
Only "data", "numeros", "estrelas", "jackpot" and "vencedores" are
ever read from a legacy draw by world/engine/builder.py,
core/evolution/statistics.py or the factions above (confirmed by
exhaustive reading, not assumption) — nothing else is lost that was
actually used.

  numeros/estrelas <- chave.numeros/chave.estrelas (direct flatten)
  jackpot   <- estatisticas_financeiras.previsao_1_premio_com_jackpot_eur,
               falling back to 0 when null/absent — mirroring
               core/data/loaders.py:get_history()'s OWN existing
               convention for the same field
               (int(x.get('jackpot') or 0)), not a new interpretation.
  vencedores <- premios.houve_vencedor_1_premio_total, mapped to 1/0.
               NOTE: the legacy field was a raw winner COUNT from the
               live API; the modern dataset only has a boolean "was
               there a category-1 winner" flag for the ~25% of draws
               with financial data at all. 0/1 is the most honest
               available mapping — it is not a literal count, but it
               satisfies the only real consumer
               (world/engine/builder.py's `== 0` no-winner-streak
               check), which never reads the field as a count.

Ordering / tie-break invariant
--------------------------------------------------------------------
load_versioned_history() sorts strictly by available_at(draw). No
secondary tie-break key is implemented: the real dataset guarantees a
unique timestamp_utc per draw (verified against all 1,971 real draws
across datasets/historical/euromillions/2004-2026: 1,971 unique
timestamps, zero duplicates, zero missing — see
TestRealDatasetTimestampsAreUnique in the test suite). If this
invariant is ever violated by a future dataset, Python's sort is
stable, so draws with an equal available_at() keep their original
scan order (file-sorted, then in-file chronological order, both
already deterministic) — never silently reordered, never a crash.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from core.services.historical_dataset import discover_datasets, load_dataset


def _require_timezone_aware(dt: datetime, label: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware, got a naive datetime: {dt!r}")


def available_at(draw: Mapping[str, Any]) -> datetime:
    """The single source of truth for "when this draw's result became
    officially available" — never inferred from draw['data'] alone.

    Raises KeyError if draw['horario']['timestamp_utc'] is absent,
    ValueError if it can't be parsed as an ISO datetime, and ValueError
    if it parses but is naive (a timestamp_utc without a timezone is
    invalid data for this service, never silently interpreted).
    """
    raw = draw["horario"]["timestamp_utc"]
    dt = datetime.fromisoformat(raw)
    _require_timezone_aware(dt, "draw['horario']['timestamp_utc']")
    return dt


def load_versioned_history(root: Path | str | None = None) -> tuple[Mapping[str, Any], ...]:
    """Loads every draw from every dataset file under
    datasets/historical/euromillions/ (via
    core.services.historical_dataset.discover_datasets/load_dataset),
    sorted ascending by available_at() — never trusts file/directory
    order alone.

    Returns the modern draw records exactly as loaded — no flattening,
    no adaptation, no mutation. That is adapt_to_legacy_draw()'s job,
    never this function's. Does not re-run
    validate_historical_dataset() — trusts the already-registered,
    already-validated dataset, the same way dashboard_data.py does.
    """
    all_draws: list[Mapping[str, Any]] = []
    for path in discover_datasets(root):
        dataset = load_dataset(path)
        all_draws.extend(dataset.get("sorteios", []))
    return tuple(sorted(all_draws, key=available_at))


def visible_draws(
    draws: Sequence[Mapping[str, Any]],
    cutoff_datetime: datetime,
) -> tuple[Mapping[str, Any], ...]:
    """Filters `draws` (given order preserved, never reordered here —
    load_versioned_history() already establishes the canonical order)
    to only those with available_at(d) < cutoff_datetime (strict —
    a draw available exactly at the cutoff instant is excluded).

    Raises ValueError if cutoff_datetime is naive. Never mutates
    `draws`. If nothing qualifies, returns () — NEVER falls back to
    returning `draws` unfiltered.
    """
    _require_timezone_aware(cutoff_datetime, "cutoff_datetime")
    return tuple(d for d in draws if available_at(d) < cutoff_datetime)


def adapt_to_legacy_draw(draw: Mapping[str, Any]) -> dict[str, Any]:
    """Converts one modern draw record into the flat shape
    world/engine/builder.py, core/evolution/statistics.py and
    ctx['historico']-consuming factions already expect:
    {"data", "numeros", "estrelas", "jackpot", "vencedores"}. See
    module docstring for the exact, documented honesty compromises on
    jackpot/vencedores. Never mutates `draw`.
    """
    financeiras = draw.get("estatisticas_financeiras") or {}
    premios = draw.get("premios") or {}
    return {
        "data": draw["data"],
        "numeros": list(draw["chave"]["numeros"]),
        "estrelas": list(draw["chave"]["estrelas"]),
        "jackpot": int(financeiras.get("previsao_1_premio_com_jackpot_eur") or 0),
        "vencedores": int(bool(premios.get("houve_vencedor_1_premio_total"))),
    }


def build_historical_context_for_backtest(
    cutoff_datetime: datetime,
    root: Path | str | None = None,
) -> tuple[dict[str, Any], ...]:
    """The one public entry point: load -> filter by cutoff -> adapt.
    No logic beyond composing the three functions above — a caller who
    calls this instead of recomposing the steps by hand cannot forget
    the cutoff or accidentally adapt before filtering.

    Ready to pass directly as `hist` to
    core.evolution.statistics.calculate() or as ctx['historico'].
    """
    all_draws = load_versioned_history(root)
    visible = visible_draws(all_draws, cutoff_datetime)
    return tuple(adapt_to_legacy_draw(d) for d in visible)
