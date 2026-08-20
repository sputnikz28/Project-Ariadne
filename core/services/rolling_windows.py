"""Rolling window selection (Commit 13) — pure, deterministic, no I/O,
no random. Selects and extracts subsets of an already-loaded,
chronologically-ordered `sorteios` sequence; never computes a metric
itself. Every metric (frequency, delay, parity, low/high, gaps,
repeated values, decade buckets) already exists in
core/services/statistical_profiles.py — callers compose those
functions directly over a RollingWindow's numero_occurrences/
estrela_occurrences rather than this module wrapping each one
redundantly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

# date.weekday(): Monday=0 .. Sunday=6 — the same convention already
# used by core/services/historical_draw_generator.py's
# VALID_DRAW_WEEKDAYS = {1, 4}. Defined locally here, not imported from
# there, to avoid a dependency from this pure analysis layer onto the
# official-draw write pipeline.
TUESDAY = 1
FRIDAY = 4


@dataclass(frozen=True)
class RollingWindow:
    """draws: the raw sorteio records selected, in the same order they
    were given — never reordered. numero_occurrences/estrela_occurrences
    are the same draws with just chave.numeros/chave.estrelas already
    extracted (one tuple per draw), ready to feed straight into
    statistical_profiles.py. This dataclass never computes a metric
    itself.
    """

    label: str
    draws: tuple[Mapping, ...]
    requested_size: int
    numero_occurrences: tuple[tuple[int, ...], ...]
    estrela_occurrences: tuple[tuple[int, ...], ...]

    @property
    def actual_size(self) -> int:
        return len(self.draws)


def _build_window(selected: Sequence[Mapping], requested_size: int, label: str) -> RollingWindow:
    draws = tuple(selected)
    return RollingWindow(
        label=label,
        draws=draws,
        requested_size=requested_size,
        numero_occurrences=tuple(tuple(d["chave"]["numeros"]) for d in draws),
        estrela_occurrences=tuple(tuple(d["chave"]["estrelas"]) for d in draws),
    )


def last_n_draws(sorteios: Sequence[Mapping], n: int, label: str | None = None) -> RollingWindow:
    """sorteios: already loaded and chronologically ordered (oldest ->
    newest) by the caller — never reordered or date-validated here.

    Returns the last `n` draws, preserving their given order. `n <= 0`
    or an empty `sorteios` produce an empty window — never an error,
    never padding. `len(sorteios) < n` returns whatever exists; compare
    `.actual_size` to `.requested_size` to detect this. Never mutates
    `sorteios`.
    """
    resolved_label = label if label is not None else f"last_{n}_draws"
    if n <= 0 or not sorteios:
        return _build_window([], n, resolved_label)
    return _build_window(sorteios[-n:], n, resolved_label)


def last_n_draws_on_weekday(
    sorteios: Sequence[Mapping], weekday: int, n: int, label: str | None = None,
) -> RollingWindow:
    """weekday: date.weekday() convention (Monday=0 .. Sunday=6) — e.g.
    TUESDAY (1) or FRIDAY (4). Raises ValueError if weekday is outside
    0-6 (a caller bug, not a data gap) — checked before anything else.

    Determines each draw's weekday exclusively from
    date.fromisoformat(draw["data"]).weekday() — never from the
    dia_semana text field, which is locale-specific and not trusted for
    filtering. Filters `sorteios` to that weekday, preserving the given
    order (never re-sorted by date), then applies the same last-n rule
    as last_n_draws. Never mutates `sorteios`.
    """
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday must be 0-6 (Monday=0..Sunday=6), got {weekday!r}")

    resolved_label = label if label is not None else f"last_{n}_draws_weekday_{weekday}"
    if n <= 0 or not sorteios:
        return _build_window([], n, resolved_label)

    matching = [d for d in sorteios if date.fromisoformat(d["data"]).weekday() == weekday]
    if not matching:
        return _build_window([], n, resolved_label)
    return _build_window(matching[-n:], n, resolved_label)
