"""Arena — normalized cross-system/cross-strategy comparison (Campaign
Runner V2 follow-up). Never generates a candidate, never touches a
faction algorithm, never touches backtest_orchestrator.py. Operates
purely on core.services.backtest_campaign.GeneratorRunResult objects
already produced by run_system_campaign()/GENERATORS adapters.

The fundamental comparison unit is a CELL: (system, target, seed) —
never an aggregate across seeds. Seeds are independent experimental
repetitions; mixing candidates from different seeds before picking an
"official" key or an equal-budget sample would fabricate a run that
never happened and destroy exactly the seed-to-seed variability the
Arena exists to measure. Every function below that selects or samples
candidates operates within a single cell; aggregation across seeds
happens only afterwards, at the summary level (ArenaStrategySummary),
and is always expressed as counts/rates, never as pooled candidates.

A campaign with more than one `generations` value for a
has_generations system (e.g. Clerics run at both G20 and G100 in the
same spec) produces more than one GeneratorRunResult for the same
(system, target, seed) — this module treats that as ambiguous and
raises ValueError rather than silently picking or merging one: the
Arena compares one generations value at a time, exactly like it never
mixes seeds. Callers sweeping multiple generations values must run one
Arena analysis per value, filtering `results` first.

RNG discipline: every Arena-side random draw goes through _arena_rng(),
a single seed-derivation point using SHA-256 over an explicit,
namespaced payload — never Python's built-in hash() (randomised
per-process, not reproducible across runs). This is not for
cryptographic security; it is so two different kinds of Arena draws
(official_key vs. equal_budget:N for different N) can never collide by
accident, and so no Arena draw can ever read or perturb a generator's
own random/ctx['rng'] stream — a fresh random.Random instance is
constructed, used once, and discarded.

Extensibility: every function below discovers systems/strategies
dynamically from `results` (or, for category severity, from
[HEROIS_TIERS] in cfg) — never a closed enumeration. A future system
(Treefolks V2, Cyber-Anões, Superesqueletos, Ciclopes, Academia, ...)
needs zero changes here; it only needs a registered GeneratorAdapter
(core/services/backtest_generators.py) producing GeneratorRunResult
objects with the same shape every system here already has.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from collections.abc import Collection, Sequence
from dataclasses import dataclass

from core.services.backtest_campaign import GeneratorRunResult
from core.services.backtest_lab import BacktestTarget
from core.services.backtest_orchestrator import SimulatedBacktestCandidate
from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_performance import CandidatePerformanceSummary, summarize_candidate_performance
from core.services.candidate_provenance import CandidateKey
from core.services.hero_evaluation import HeroConfigError, load_hero_config


def _arena_rng(
    arena_seed: int, purpose: str, system: str, race: str | None,
    target: BacktestTarget, generator_seed: int,
) -> random.Random:
    """Single seed-derivation point for every Arena RNG draw. `purpose`
    namespaces the kind of draw ("official_key", "equal_budget:1",
    "equal_budget:2", "equal_budget:5", ...) so two different Arena
    draws never collide even when every other argument matches.
    """
    payload = "|".join([
        "arena", str(arena_seed), purpose, system, str(race), target.draw_id, str(generator_seed),
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return random.Random(digest)


def _assert_one_result_per_cell(results: Sequence[GeneratorRunResult]) -> None:
    seen = {}
    for r in results:
        cell = (r.system, r.target.draw_id, r.seed)
        if cell in seen:
            raise ValueError(
                f"multiple GeneratorRunResult for the same (system, target, seed)={cell!r} — "
                "likely more than one `generations` value swept for this system in this "
                "campaign; the Arena compares one generations value at a time, exactly like "
                "it never mixes seeds. Filter `results` to a single generations value first."
            )
        seen[cell] = r


def _cell_result(
    results: Sequence[GeneratorRunResult], system: str, target: BacktestTarget, generator_seed: int,
) -> GeneratorRunResult | None:
    matches = [
        r for r in results
        if r.system == system and r.target.draw_id == target.draw_id and r.seed == generator_seed
    ]
    if len(matches) > 1:
        raise ValueError(
            f"multiple GeneratorRunResult for (system={system!r}, target={target.draw_id!r}, "
            f"seed={generator_seed!r}) — likely more than one `generations` value swept for "
            "this system; filter `results` to a single generations value before comparing in "
            "the Arena, the same discipline already required for seeds."
        )
    return matches[0] if matches else None


def _candidates_in_cell(
    results: Sequence[GeneratorRunResult], system: str, race: str | None, target: BacktestTarget, generator_seed: int,
) -> list[tuple[SimulatedBacktestCandidate, CandidateEvaluation]]:
    """Every (candidate, evaluation) pair for this exact cell whose
    candidate.race == race — never pooled across seeds or generations.
    """
    result = _cell_result(results, system, target, generator_seed)
    if result is None:
        return []
    return [(c, e) for c, e in zip(result.candidates, result.evaluations) if c.candidate.race == race]


def official_key(
    results: Sequence[GeneratorRunResult],
    system: str,
    race: str | None,
    target: BacktestTarget,
    generator_seed: int,
    arena_seed: int,
) -> CandidateKey | None:
    """The Official Key of (system, race) for this single (target, seed)
    cell — considers only candidates from exactly that cell, never
    candidates from any other seed.

    Deduplicates to unique (numeros, estrelas) pairs, sorted
    canonically ascending, then picks uniformly among them via
    _arena_rng(arena_seed, "official_key", ...) — a fresh RNG instance,
    local to this call. Returns None (never fabricated) if the cell has
    zero candidates for this (system, race) — a legitimate abstention.

    No system in this V1 has its own explicit official-key mechanism;
    this neutral rule is the only one used. A future adapter wanting to
    supply its own selection would need a separate, explicit contract
    extension — never applied implicitly.
    """
    pairs = _candidates_in_cell(results, system, race, target, generator_seed)
    by_key: dict[tuple[tuple[int, ...], tuple[int, ...]], CandidateKey] = {}
    for candidate, _evaluation in pairs:
        key = (candidate.candidate.numeros, candidate.candidate.estrelas)
        by_key.setdefault(key, candidate.candidate)
    if not by_key:
        return None
    ordered_keys = sorted(by_key)
    rng = _arena_rng(arena_seed, "official_key", system, race, target, generator_seed)
    chosen = rng.choice(ordered_keys)
    return by_key[chosen]


def official_keys_by_cell(
    results: Sequence[GeneratorRunResult], system: str, race: str | None, arena_seed: int,
) -> dict[tuple[str, int], CandidateKey | None]:
    """{(target.draw_id, generator_seed): official_key(...)} for every
    cell where `system` was attempted in `results` — a cell with zero
    candidates for this race still appears, mapped to None, never
    silently omitted.
    """
    _assert_one_result_per_cell(results)
    target_by_draw_id: dict[str, BacktestTarget] = {}
    cells: set[tuple[str, int]] = set()
    for r in results:
        if r.system != system:
            continue
        target_by_draw_id[r.target.draw_id] = r.target
        cells.add((r.target.draw_id, r.seed))
    out = {}
    for draw_id, generator_seed in sorted(cells):
        target = target_by_draw_id[draw_id]
        out[(draw_id, generator_seed)] = official_key(results, system, race, target, generator_seed, arena_seed)
    return out


@dataclass(frozen=True)
class EqualBudgetResult:
    """n_used is always <= n_requested and is never padded to match —
    an under-budget cell is always visible by comparing the two, never
    silently presented as an equal comparison.
    """

    n_requested: int
    n_used: int
    candidates: tuple[SimulatedBacktestCandidate, ...]
    evaluations: tuple[CandidateEvaluation, ...]
    performance: CandidatePerformanceSummary


def sample_with_equal_budget(
    results: Sequence[GeneratorRunResult],
    system: str,
    race: str | None,
    target: BacktestTarget,
    generator_seed: int,
    n: int,
    arena_seed: int,
    relevant_categories: Collection[str],
) -> EqualBudgetResult:
    """Samples within the single (system, race, target, generator_seed)
    cell only — never mixes candidates from different seeds. Without
    replacement, via _arena_rng(arena_seed, f"equal_budget:{n}", ...) —
    a distinct purpose per N, so different budgets, and official_key(),
    never correlate with each other.
    """
    pairs = _candidates_in_cell(results, system, race, target, generator_seed)
    n_used = min(n, len(pairs))
    if n_used:
        rng = _arena_rng(arena_seed, f"equal_budget:{n}", system, race, target, generator_seed)
        indices = rng.sample(range(len(pairs)), n_used)
        sampled = [pairs[i] for i in indices]
    else:
        sampled = []
    candidates = tuple(c for c, _e in sampled)
    evaluations = tuple(e for _c, e in sampled)
    performance = summarize_candidate_performance(
        tuple(c.candidate for c in candidates), evaluations, relevant_categories,
    )
    return EqualBudgetResult(
        n_requested=n, n_used=n_used, candidates=candidates, evaluations=evaluations, performance=performance,
    )


@dataclass(frozen=True)
class ArenaSystemAttendance:
    """System-level attendance — always computable, with zero
    enumeration, even for a system that never once produces a
    candidate (total abstention, e.g. Axiomantes' Portal closed at
    every target). This is the only structure in this module that can
    detect that case; ArenaStrategySummary below depends on having
    observed at least one candidate to discover a (system, race) pair
    at all, the same structural limit core.services.backtest_campaign's
    own dynamic discovery already has.
    """

    system: str
    cells_attempted: int
    cells_with_any_candidate: int
    targets_observed: int
    targets_with_participation: int
    system_abstention_rate: float


@dataclass(frozen=True)
class ArenaStrategySummary:
    """cell = one (target, seed) run. cells_* counts every execution;
    targets_* counts distinct concursos, regardless of how many seeds
    ran for each — "participated in 12 of 15 runs" and "participated in
    4 of 5 concursos" are two different, both-reported numbers, never
    conflated.

    success_rate_when_participating is None (never 0.0) when
    cells_participated == 0 — an undefined rate must never be rendered
    as "0% success", which would misleadingly imply the strategy tried
    and failed rather than never tried at all.
    """

    system: str
    race: str | None
    cells_attempted: int
    cells_participated: int
    cells_succeeded: int
    targets_observed: int
    targets_with_participation: int
    participation_rate: float
    abstention_rate: float
    success_rate_when_participating: float | None
    success_rate_over_all_cells: float
    target_participation_rate: float


def summarize_system_attendance(results: Sequence[GeneratorRunResult]) -> dict[str, ArenaSystemAttendance]:
    """Discovers systems dynamically from `results` — never a fixed
    list. A system present in GENERATORS but never included in
    `results` (never run this campaign) simply never appears here,
    same as it never appearing anywhere else.
    """
    _assert_one_result_per_cell(results)
    by_system: dict[str, list[GeneratorRunResult]] = defaultdict(list)
    for r in results:
        by_system[r.system].append(r)

    out = {}
    for system, cells in by_system.items():
        cells_attempted = len(cells)
        cells_with_any = sum(1 for r in cells if r.candidates)
        targets = {r.target.draw_id for r in cells}
        targets_with_participation = {r.target.draw_id for r in cells if r.candidates}
        out[system] = ArenaSystemAttendance(
            system=system,
            cells_attempted=cells_attempted,
            cells_with_any_candidate=cells_with_any,
            targets_observed=len(targets),
            targets_with_participation=len(targets_with_participation),
            system_abstention_rate=1.0 - (cells_with_any / cells_attempted if cells_attempted else 0.0),
        )
    return out


def summarize_arena_participation(
    results: Sequence[GeneratorRunResult], relevant_categories: Collection[str],
) -> dict[tuple[str, str | None], ArenaStrategySummary]:
    """Discovers (system, race) pairs dynamically from `results`, two
    ways: from candidates actually produced (exactly like
    core.services.backtest_campaign.summarize_by_system_and_strategy()),
    and from each GeneratorRunResult.attempted_races — the set of
    race/strategy labels an adapter declares it deliberately tried this
    cell, whether or not it produced a candidate. This second source is
    what lets a strategy that abstains in every single cell (a
    conditional strategy whose participation threshold is never met at
    any target) still be discovered and reported honestly as 100%
    abstention, instead of silently disappearing for lack of a
    CandidateKey. A race declared by neither path (never produced a
    candidate and never listed in attempted_races anywhere) is still
    invisible here — captured instead, at the system level, by
    summarize_system_attendance() above.

    cells_attempted for a given (system, race) is that system's own
    cells_attempted (shared across every race of that system) — a
    race-specific "attempted" count isn't knowable without enumerating
    every race a system could ever produce, which this module refuses
    to do.
    """
    _assert_one_result_per_cell(results)
    attendance = summarize_system_attendance(results)
    relevant_set = set(relevant_categories)

    pairs_seen: set[tuple[str, str | None]] = set()
    for r in results:
        for c in r.candidates:
            pairs_seen.add((r.system, c.candidate.race))
        for race in r.attempted_races:
            pairs_seen.add((r.system, race))

    out = {}
    for system, race in pairs_seen:
        cells_attempted = attendance[system].cells_attempted
        cells_participated = 0
        cells_succeeded = 0
        targets_participated: set[str] = set()
        for r in results:
            if r.system != system:
                continue
            matched = [(c, e) for c, e in zip(r.candidates, r.evaluations) if c.candidate.race == race]
            if not matched:
                continue
            cells_participated += 1
            targets_participated.add(r.target.draw_id)
            if any(e.category in relevant_set for _c, e in matched):
                cells_succeeded += 1

        targets_observed = attendance[system].targets_observed
        targets_with_participation = len(targets_participated)
        participation_rate = cells_participated / cells_attempted if cells_attempted else 0.0

        out[(system, race)] = ArenaStrategySummary(
            system=system, race=race,
            cells_attempted=cells_attempted, cells_participated=cells_participated, cells_succeeded=cells_succeeded,
            targets_observed=targets_observed, targets_with_participation=targets_with_participation,
            participation_rate=participation_rate,
            abstention_rate=1.0 - participation_rate,
            success_rate_when_participating=(cells_succeeded / cells_participated) if cells_participated else None,
            success_rate_over_all_cells=(cells_succeeded / cells_attempted) if cells_attempted else 0.0,
            target_participation_rate=(targets_with_participation / targets_observed) if targets_observed else 0.0,
        )
    return out


def category_rank(category: str, cfg) -> tuple[int, int, int]:
    """(tier_order[category] from [HEROIS_TIERS], -matched_number_count,
    -matched_star_count) — lower sorts as better. Reuses
    core.services.hero_evaluation.load_hero_config() for the tier
    table; never redefines it. Raises HeroConfigError (re-exported
    unchanged) if [HEROIS_TIERS] is missing/malformed, or if `category`
    has no tier entry there — a category the project's own Hero tier
    table doesn't cover (e.g. very low categories excluded from
    [HEROIS_TIERS] in the real config.txt) is never silently ranked by
    guesswork.
    """
    hero_cfg = load_hero_config(cfg)
    tier_map = hero_cfg["tier_map"]
    tier_order = hero_cfg["tier_order"]
    if category not in tier_map:
        raise HeroConfigError(f"category {category!r} has no tier mapping in [HEROIS_TIERS]")
    matched_n_str, matched_e_str = category.split("+")
    return (tier_order[tier_map[category]], -int(matched_n_str), -int(matched_e_str))


def star_match_distribution(eb: EqualBudgetResult) -> dict[int, int]:
    """Prova das Estrelas — a lens deliberately separate from the
    Arena's normal success metric. {0,1,2} -> count of candidates in
    the equal-budget sample with that many matched stars. Reuses
    CandidateEvaluation.matched_star_count already computed by
    reveal_and_evaluate() — never recomputes correspondence, never
    reads relevant_categories at all. Always operates on an
    EqualBudgetResult (same N=1/2/5 budgeting as the rest of the
    Arena), never on unbudgeted raw candidates, so a comparison across
    systems at the same N stays honest.
    """
    distribution = {0: 0, 1: 0, 2: 0}
    for evaluation in eb.evaluations:
        distribution[evaluation.matched_star_count] += 1
    return distribution
