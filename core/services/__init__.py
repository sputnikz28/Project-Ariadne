"""Shared statistical services (scaffold — intentionally empty for now).

This package is where cross-faction statistical logic will eventually
live, so that factions consume a single shared implementation instead
of each re-computing the same numbers over historical draws.

Nothing here is implemented yet. This is an audit finding, not a
migration: today the same kinds of computation already exist,
independently, in several places — e.g. library/ariadne/engine.py
(pairs, triples, overdue_numbers, least_frequent_numbers),
core/evolution/statistics.py (frequencies, hot/cold, delays), and
several factions/chaos_cartographers/*.py modules (frequency,
delay/variance, gap, and hot/cold-adjacent computations of their own).
Consolidating those into the services below is future work, not part
of this scaffold.

Planned services (names indicative, one module each once implemented):

    StatisticsService   — shared entry point / facade over the others
    DelayService         — "how overdue is number N" (atraso)
    PairService           — two-number co-occurrence frequency
    TripleService          — three-number co-occurrence frequency
    EntropyService           — randomness / distribution-fit scoring
    TrendService               — hot/cold and rising/falling trends

Each future service should take a history list (the same shape
Ariadne.full_history() already returns) and expose pure, stateless
query methods — no faction-specific logic, no I/O beyond what Ariadne
already provides.
"""
