"""Statistical Window Profile (Commit 15) — pure composition of the
Commit 12 (core.services.statistical_profiles) and Commit 13
(core.services.rolling_windows) primitives over a single RollingWindow.
Introduces zero new statistical formulas: every field is either a
direct call to statistical_profiles, or a straightforward reshape
(full-universe padding, per-draw alignment, simple aggregation) of
those calls' results. Never reads a file, never computes randomness,
never generates a key, never scores, predicts, or classifies anything
(no hot/cold/new, no Jaccard — deliberately out of scope, see
CLAUDE.md).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from core.services.rolling_windows import RollingWindow
from core.services.statistical_profiles import (
    absolute_frequency,
    current_delay,
    decade_bucket,
    key_gaps,
    low_high,
    parity,
    relative_frequency,
    repeated_values,
)

# Duplicated deliberately from core/services/dashboard_data.py rather
# than imported from it — dashboard_data.py is the Dashboard's own
# assembly layer and already depends on this services layer (since
# Commit 14); importing back from it here would invert that dependency.
# This is a trivial constant (the game's fixed number/star universe),
# not logic.
_ALL_NUMEROS: tuple[int, ...] = tuple(range(1, 51))
_ALL_ESTRELAS: tuple[int, ...] = tuple(range(1, 13))
_DECADE_BUCKETS: tuple[str, ...] = ("01-10", "11-20", "21-30", "31-40", "41-50")


@dataclass(frozen=True)
class StatisticalWindowProfile:
    """A read-only statistical summary of one already-selected
    RollingWindow. Every field is derived exclusively from
    window.draws/numero_occurrences/estrela_occurrences via
    core.services.statistical_profiles — this dataclass computes
    nothing itself beyond straightforward reshaping/aggregation.
    Mapping fields are MappingProxyType — genuinely read-only, not just
    frozen-by-convention.

    numero_delays/estrela_delays are scoped to THIS window only — "0"
    means "appeared in the window's own most recent draw", never a
    project-wide historical delay (see
    dashboard_data.py:build_frequencies_rows for that — a different,
    unrelated computation over whatever draw_records its own caller
    supplies).

    *_by_draw fields are tuples aligned index-for-index with
    window.draws (index i corresponds to window.draws[i]).
    repeated_*_between_draws[i] compares window.draws[i+1] against
    window.draws[i] — length is always max(0, actual_size - 1); a
    window with 0 or 1 draws has no consecutive pair, so this is
    naturally empty, never a fabricated comparison against something
    outside the window.
    """

    label: str
    requested_size: int
    actual_size: int

    numero_absolute_frequencies: Mapping[int, int]
    numero_relative_frequencies: Mapping[int, float]
    estrela_absolute_frequencies: Mapping[int, int]
    estrela_relative_frequencies: Mapping[int, float]

    numero_delays: Mapping[int, int | None]
    estrela_delays: Mapping[int, int | None]

    parity_by_draw: tuple[tuple[int, int], ...]
    low_high_by_draw: tuple[tuple[int, int], ...]

    decade_distribution: Mapping[str, int]

    numero_gaps_by_draw: tuple[tuple[int, ...], ...]
    estrela_gaps_by_draw: tuple[tuple[int, ...], ...]

    repeated_numeros_between_draws: tuple[tuple[int, ...], ...]
    repeated_estrelas_between_draws: tuple[tuple[int, ...], ...]


def build_statistical_window_profile(window: RollingWindow) -> StatisticalWindowProfile:
    """Pure — no I/O, no random, no datetime.now(). window's given
    order is authoritative throughout (inherited unchanged from
    core.services.rolling_windows — never re-sorted, never
    date-validated here).
    """
    numero_abs = absolute_frequency(window.numero_occurrences)
    estrela_abs = absolute_frequency(window.estrela_occurrences)
    numero_rel = relative_frequency(numero_abs, window.actual_size)
    estrela_rel = relative_frequency(estrela_abs, window.actual_size)

    numero_absolute_frequencies = MappingProxyType({n: numero_abs.get(n, 0) for n in _ALL_NUMEROS})
    numero_relative_frequencies = MappingProxyType({n: numero_rel.get(n, 0.0) for n in _ALL_NUMEROS})
    estrela_absolute_frequencies = MappingProxyType({e: estrela_abs.get(e, 0) for e in _ALL_ESTRELAS})
    estrela_relative_frequencies = MappingProxyType({e: estrela_rel.get(e, 0.0) for e in _ALL_ESTRELAS})

    numero_delays = MappingProxyType(
        {n: current_delay(window.numero_occurrences, n) for n in _ALL_NUMEROS}
    )
    estrela_delays = MappingProxyType(
        {e: current_delay(window.estrela_occurrences, e) for e in _ALL_ESTRELAS}
    )

    parity_by_draw = tuple(parity(draw) for draw in window.numero_occurrences)
    low_high_by_draw = tuple(low_high(draw) for draw in window.numero_occurrences)

    decade_counts = {bucket: 0 for bucket in _DECADE_BUCKETS}
    for draw in window.numero_occurrences:
        for n in draw:
            decade_counts[decade_bucket(n)] += 1
    decade_distribution = MappingProxyType(decade_counts)

    numero_gaps_by_draw = tuple(key_gaps(draw) for draw in window.numero_occurrences)
    estrela_gaps_by_draw = tuple(key_gaps(draw) for draw in window.estrela_occurrences)

    repeated_numeros_between_draws = tuple(
        repeated_values(window.numero_occurrences[i + 1], window.numero_occurrences[i])
        for i in range(window.actual_size - 1)
    )
    repeated_estrelas_between_draws = tuple(
        repeated_values(window.estrela_occurrences[i + 1], window.estrela_occurrences[i])
        for i in range(window.actual_size - 1)
    )

    return StatisticalWindowProfile(
        label=window.label,
        requested_size=window.requested_size,
        actual_size=window.actual_size,
        numero_absolute_frequencies=numero_absolute_frequencies,
        numero_relative_frequencies=numero_relative_frequencies,
        estrela_absolute_frequencies=estrela_absolute_frequencies,
        estrela_relative_frequencies=estrela_relative_frequencies,
        numero_delays=numero_delays,
        estrela_delays=estrela_delays,
        parity_by_draw=parity_by_draw,
        low_high_by_draw=low_high_by_draw,
        decade_distribution=decade_distribution,
        numero_gaps_by_draw=numero_gaps_by_draw,
        estrela_gaps_by_draw=estrela_gaps_by_draw,
        repeated_numeros_between_draws=repeated_numeros_between_draws,
        repeated_estrelas_between_draws=repeated_estrelas_between_draws,
    )
