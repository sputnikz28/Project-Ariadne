"""Shared statistical primitives (Commit 12) — pure, deterministic, no
I/O, no random, no reading of files/indices/registries. Every function
operates on already-extracted Sequence[int] values (numeros OR
estrelas, never mixed) handed in by the caller; none of them knows
about the 1-50/1-12 universes, which draws belong together, or what
"now" means — that responsibility always stays with the caller, the
same discipline core/services/dashboard_data.py's builders already
follow.

These primitives do not replace any existing per-faction logic,
core/evolution/statistics.py, or the Ariadne/library/indexes readers —
they coexist deliberately. See CLAUDE.md ("Duplicação encontrada" /
"Known Issues / Dívida Técnica") for the pre-existing duplication this
module intentionally leaves untouched.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence


def absolute_frequency(occurrences: Sequence[Sequence[int]]) -> Counter[int]:
    """occurrences: one already-extracted list of values per draw — all
    numeros, or all estrelas, never mixed within a single call. Counts
    occurrences of each value across every draw. Never mutates any
    element of `occurrences`. A value that never appears simply has no
    entry in the result (this function does not know the universe of
    possible values, so it cannot zero-pad it).
    """
    counts: Counter[int] = Counter()
    for draw in occurrences:
        counts.update(draw)
    return counts


def relative_frequency(absolute: Mapping[int, int], total_draws: int) -> dict[int, float]:
    """absolute: typically the result of absolute_frequency(). Returns
    one ratio per key already present in `absolute` — never invents
    entries for values absolute doesn't mention.

    total_draws == 0 -> every value maps to 0.0 (never a
    ZeroDivisionError, never fabricated as if some draws existed).
    total_draws < 0 -> raises ValueError; a negative draw count can
    never be real input, so this is a caller bug, not a data gap.
    """
    if total_draws < 0:
        raise ValueError(f"total_draws must be >= 0, got {total_draws!r}")
    if total_draws == 0:
        return {value: 0.0 for value in absolute}
    return {value: count / total_draws for value, count in absolute.items()}


def current_delay(occurrences: Sequence[Sequence[int]], value: int) -> int | None:
    """occurrences: ordered oldest -> newest — trusted completely as
    given; this function never inspects dates or reorders anything.

    Returns 0 if `value` appears in the most recent draw (the last
    element of `occurrences`), N if its last appearance was N draws
    before that, or None if `value` never appears anywhere in
    `occurrences` — including when `occurrences` is empty. None here is
    an exact "undefined", never a lower-bound number standing in for
    "at least this many draws" (that would be a different, weaker
    claim than an exact delay).
    """
    for offset, draw in enumerate(reversed(occurrences)):
        if value in draw:
            return offset
    return None


def parity(numeros: Sequence[int]) -> tuple[int, int]:
    """(pares, ímpares) for a single already-extracted key."""
    pares = sum(1 for n in numeros if n % 2 == 0)
    return pares, len(numeros) - pares


def low_high(numeros: Sequence[int], threshold: int = 25) -> tuple[int, int]:
    """(baixos, altos) for a single already-extracted key. baixo means
    <= threshold — the same 2-bucket split already used consistently by
    axiomantes/profile.py and chaos_cartographers/{trends,randomness}.py
    (threshold=25 there too). Only meaningful for the numeros universe.
    """
    baixos = sum(1 for n in numeros if n <= threshold)
    return baixos, len(numeros) - baixos


def decade_bucket(n: int) -> str:
    """"01-10".."41-50" for a single number. A deliberately small
    reimplementation of historical_statistics.py:_decade_bucket (private
    there, never reexported) rather than reaching into another module's
    private helper. Only meaningful for the numeros universe (1-50) —
    never call this with an estrela value.
    """
    if n <= 10:
        return "01-10"
    if n <= 20:
        return "11-20"
    if n <= 30:
        return "21-30"
    if n <= 40:
        return "31-40"
    return "41-50"


def key_gaps(values: Sequence[int]) -> tuple[int, ...]:
    """Consecutive differences after sorting — generic, unlike
    core.services.combinations.gaps() (hardcoded to exactly 5 values,
    so it cannot serve a 2-element estrelas key). Works for numeros (5),
    estrelas (2), or any other length. Length 0 or 1 -> () — there is no
    gap to report. Never mutates `values` (sorts into a new list).
    """
    ordered = sorted(values)
    return tuple(ordered[i + 1] - ordered[i] for i in range(len(ordered) - 1))


def repeated_values(key_a: Sequence[int], key_b: Sequence[int]) -> tuple[int, ...]:
    """Sorted, de-duplicated intersection of two already-extracted keys
    — generalises historical_statistics.py:repetidos_sorteio_anterior
    (which is hardcoded to "this draw vs. the previous one") to any two
    keys the caller chooses to compare. Duplicate values within either
    input never produce duplicate entries in the result. Never mutates
    `key_a`/`key_b`.
    """
    return tuple(sorted(set(key_a) & set(key_b)))
