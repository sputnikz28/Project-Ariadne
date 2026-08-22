"""Backtest Campaign Runner / Race Performance V1 (Commit 27) — runs a
grid of independent historical backtests over target x seed x
generations, using core.services.backtest_orchestrator (Commit 25)
unmodified, and aggregates the pooled results by race.

Every cell of the grid is a genuinely independent run: its own
run_id, its own random.seed(seed), its own call to
factions.clerics.algorithm.execute(). G20 and G100 for the same
target+seed are two entirely separate calls — G20 is never a prefix
or truncation of G100.

Never touches factions/clerics/algorithm.py, archetypes.py, fitness.py,
or any service from Commits 15-26 — this module only composes
already-existing, already-tested functions:
  core.services.backtest_orchestrator — prepare_backtest_run,
    run_clerics_backtest, freeze_simulated_candidates,
    reveal_and_evaluate, summarize (all Commit 25, unmodified)
  core.services.candidate_performance.summarize_candidate_performance
    (Commit 18, unmodified) — reused directly for the race-level
    unique_keys/repeat_rate/category_counts/relevant_count/
    relevant_rate; this module never reimplements diversity or
    category counting.

No race enumeration anywhere in this module. summarize_by_race() and
summarize_by_race_and_generations() discover race values dynamically
from whatever CandidateKey.race actually contains — including a
genuine None (source_type != "evolutionary_individual", never
reachable in V1's Clerics-only orchestrator but honestly typed anyway)
and including "Renascido X" (a resurrected individual, CAMINHO_1000_ALMAS)
as its own, never-merged bucket, distinct from "X". Neither is
special-cased; both simply fall out of grouping by the literal,
unmodified value of CandidateKey.race.
"""

from __future__ import annotations

import configparser
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from core.services.backtest_generators import GENERATORS, GeneratorAdapter
from core.services.backtest_lab import BacktestTarget
from core.services.backtest_orchestrator import (
    BacktestRunRecord,
    HistoricalBacktestBoundary,
    SimulatedBacktestCandidate,
    freeze_simulated_candidates,
    prepare_backtest_run,
    reveal_and_evaluate,
    run_clerics_backtest,
    summarize,
)
from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_performance import CandidatePerformanceSummary, summarize_candidate_performance
from core.services.historical_dataset import find_draw, validate_official_key


@dataclass(frozen=True)
class CampaignSpec:
    """The grid to run. targets/seeds/generations are each a tuple —
    order matters (see run_campaign()'s documented iteration order),
    duplicates are the caller's responsibility, never deduplicated
    here (a caller repeating a seed on purpose is a legitimate use
    case this module never second-guesses).
    """

    targets: tuple[BacktestTarget, ...]
    seeds: tuple[int, ...]
    generations: tuple[int, ...]
    mode: Literal["verified", "exploratory"]
    relevant_categories: frozenset[str]


@dataclass(frozen=True)
class CampaignRunResult:
    """One grid cell. `generations` here is the campaign axis (which
    G-value this cell ran) — NEVER the same thing as an individual
    CandidateKey.generation (which generation, 1..generations, WITHIN
    this run produced a given candidate). The two numbers share a
    name by coincidence of English/Portuguese vocabulary, never by
    meaning — see RacePerformanceSummary.best_category_generation for
    where the per-individual one actually appears.
    """

    target: BacktestTarget
    seed: int
    generations: int
    run: BacktestRunRecord
    candidates: tuple[SimulatedBacktestCandidate, ...]
    evaluations: tuple[CandidateEvaluation, ...]


@dataclass(frozen=True)
class RacePerformanceSummary:
    """Descriptive statistics for one race, pooled across every cell
    of a campaign that contains it. Every rate/average here is
    normalized by this race's own total_keys — never compare two
    races' raw counts when they had different total_keys.

    best_category_observed: the lexicographic maximum of
    (matched_number_count, matched_star_count) among this race's
    evaluations — i.e. "most numbers matched, ties broken by most
    stars matched". This is a deterministic DESCRIPTION of the single
    best observed hit, using only the two raw counts every
    CandidateEvaluation already carries. It is explicitly NOT a
    score, NOT a tier, NOT a monetary value, and NOT a claim that any
    one category is inherently "better" than another in general (see
    Commit 18's audit: config.txt's [HEROIS_TIERS] itself proves no
    single agreed ordering exists across all 18 categories — e.g.
    3+0/3+1/2+2 share a tier, 4+0/3+2 share a tier). This field only
    ever orders by the two counts directly, never by category label.

    best_category_generation: CandidateKey.generation of whichever
    individual produced best_category_observed — the per-individual
    generation WITHIN its run, never the campaign's `generations` axis.
    """

    race: str | None
    total_keys: int
    unique_keys: int
    repeat_rate: float
    avg_matched_numbers: float
    avg_matched_stars: float
    avg_matched_total: float
    category_counts: Mapping[str, int]
    relevant_count: int
    relevant_rate: float
    best_category_observed: str | None
    best_category_generation: int | None
    targets_observed: int
    targets_with_relevant_key: int


def resolve_targets_from_draw_ids(
    draw_ids: Sequence[str], historical_root=None,
) -> tuple[BacktestTarget, ...]:
    """Convenience only — never required. Resolves each draw_id (e.g.
    "065/2026") via core.services.historical_dataset.find_draw()/
    validate_official_key(), the same mechanism evaluate_heroes.py
    already uses, into a BacktestTarget. No draw_id is ever hardcoded
    here — this function is generic over whatever draw_ids it's given.
    """
    targets = []
    for draw_id in draw_ids:
        draw, _dataset_path, dataset = find_draw(draw_id, historical_root)
        validate_official_key(draw, dataset)
        draw_datetime = datetime.fromisoformat(draw["horario"]["timestamp_utc"])
        targets.append(BacktestTarget(
            draw_id=draw_id,
            draw_datetime=draw_datetime,
            numeros=tuple(draw["chave"]["numeros"]),
            estrelas=tuple(draw["chave"]["estrelas"]),
        ))
    return tuple(targets)


def _cfg_with_generations(cfg: configparser.ConfigParser, generations: int) -> configparser.ConfigParser:
    """A COPY of `cfg` (never mutates the caller's cfg) with
    [SIMULACAO].geracoes overridden — the campaign's ONLY per-cell
    config override. population_inicial/sobreviventes and every other
    section come from the caller's base cfg, unchanged, for every cell.
    """
    cell_cfg = configparser.ConfigParser()
    for section in cfg.sections():
        cell_cfg[section] = dict(cfg[section])
    if not cell_cfg.has_section("SIMULACAO"):
        cell_cfg.add_section("SIMULACAO")
    cell_cfg.set("SIMULACAO", "geracoes", str(generations))
    return cell_cfg


def run_campaign(
    cfg: configparser.ConfigParser,
    spec: CampaignSpec,
    *,
    historical_root=None,
    scrolls_root=None,
) -> tuple[CampaignRunResult, ...]:
    """Iterates target x seed x generations in a fixed, documented
    order: targets outermost, then seeds, then generations innermost.
    This is one arbitrary but STABLE order, chosen so repeated calls
    and tests are reproducible — not the only valid order.

    Every cell calls prepare_backtest_run() / run_clerics_backtest() /
    freeze_simulated_candidates() / reveal_and_evaluate() / summarize()
    from core.services.backtest_orchestrator, completely unmodified.
    Each call to run_clerics_backtest() starts a brand-new run_manifest
    (Commit 25) — every cell gets its own run_id, structurally, never
    reused or derived from another cell.
    """
    results = []
    for target in spec.targets:
        boundary = HistoricalBacktestBoundary(draw_id=target.draw_id, draw_datetime=target.draw_datetime)
        for seed in spec.seeds:
            for generations in spec.generations:
                cell_cfg = _cfg_with_generations(cfg, generations)
                ctx, _ariadne_temporal = prepare_backtest_run(
                    cell_cfg, boundary, mode=spec.mode,
                    historical_root=historical_root, scrolls_root=scrolls_root,
                )
                evo, run_manifest = run_clerics_backtest(cell_cfg, ctx, seed, boundary)
                frozen = freeze_simulated_candidates(evo)
                evaluations = reveal_and_evaluate(frozen, target)
                performance = summarize(frozen, evaluations, spec.relevant_categories)

                run_record = BacktestRunRecord(
                    run_id=run_manifest["run_id"],
                    target=target,
                    mode=spec.mode,
                    temporal_basis="historical_input_boundary",
                    generations=generations,
                    candidate_count=len(frozen),
                    relevant_categories=frozenset(spec.relevant_categories),
                    performance=performance,
                )
                results.append(CampaignRunResult(
                    target=target, seed=seed, generations=generations,
                    run=run_record, candidates=frozen, evaluations=evaluations,
                ))
    return tuple(results)


def _pool(results: Sequence[CampaignRunResult], relevant_categories: Collection[str], key_fn) -> dict:
    """Shared grouping core for both summarize_by_race() and
    summarize_by_race_and_generations() — key_fn(result, candidate)
    decides the group key (just race, or (race, result.generations)).
    Never enumerates races; a group only ever appears if at least one
    candidate produced that key. Tracks, per group, every distinct
    target draw_id observed and every distinct draw_id where at least
    one relevant-category evaluation occurred — both computed directly
    during this single pass, never inferred afterward.
    """
    relevant_set = set(relevant_categories)
    pooled: dict = defaultdict(lambda: {
        "candidates": [], "evaluations": [], "draw_ids": set(), "draw_ids_relevant": set(),
    })
    for result in results:
        draw_id = result.target.draw_id
        for candidate, evaluation in zip(result.candidates, result.evaluations):
            group = pooled[key_fn(result, candidate)]
            group["candidates"].append(candidate)
            group["evaluations"].append(evaluation)
            group["draw_ids"].add(draw_id)
            if evaluation.category in relevant_set:
                group["draw_ids_relevant"].add(draw_id)
    return pooled


def _build_race_summary(group: dict, relevant_categories: Collection[str], race_value) -> RacePerformanceSummary:
    candidates = group["candidates"]
    evaluations = group["evaluations"]
    total = len(evaluations)

    performance = summarize_candidate_performance(
        tuple(c.candidate for c in candidates), tuple(evaluations), relevant_categories,
    )

    avg_numbers = sum(e.matched_number_count for e in evaluations) / total
    avg_stars = sum(e.matched_star_count for e in evaluations) / total
    avg_total = sum(e.matched_number_count + e.matched_star_count for e in evaluations) / total

    best_candidate, best_evaluation = None, None
    for candidate, evaluation in zip(candidates, evaluations):
        if best_evaluation is None or (
            (evaluation.matched_number_count, evaluation.matched_star_count)
            > (best_evaluation.matched_number_count, best_evaluation.matched_star_count)
        ):
            best_candidate, best_evaluation = candidate, evaluation

    return RacePerformanceSummary(
        race=race_value,
        total_keys=performance.total_candidates,
        unique_keys=performance.unique_full_keys,
        repeat_rate=1.0 - performance.full_key_diversity_rate,
        avg_matched_numbers=avg_numbers,
        avg_matched_stars=avg_stars,
        avg_matched_total=avg_total,
        category_counts=performance.category_counts,
        relevant_count=performance.relevant_count,
        relevant_rate=performance.relevant_rate,
        best_category_observed=best_evaluation.category if best_evaluation else None,
        best_category_generation=best_candidate.candidate.generation if best_candidate else None,
        targets_observed=len(group["draw_ids"]),
        targets_with_relevant_key=len(group["draw_ids_relevant"]),
    )


def summarize_by_race(
    results: Sequence[CampaignRunResult], relevant_categories: Collection[str],
) -> dict[str | None, RacePerformanceSummary]:
    """Pools every (candidate, evaluation) pair across every cell in
    `results`, grouped by CandidateKey.race exactly as provided —
    never merges "Renascido X" into "X", never fabricates a race for
    a genuine None, never enumerates a fixed race list. relevant_categories
    is always explicit — recomputable with a different set without
    re-running the campaign.
    """
    pooled = _pool(results, relevant_categories, key_fn=lambda result, candidate: candidate.candidate.race)
    return {race: _build_race_summary(group, relevant_categories, race) for race, group in pooled.items()}


def summarize_by_race_and_generations(
    results: Sequence[CampaignRunResult], relevant_categories: Collection[str],
) -> dict[tuple[str | None, int], RacePerformanceSummary]:
    """Same as summarize_by_race() but grouped by (race, generations)
    where `generations` is CampaignRunResult.generations — the campaign
    axis (which G-value that cell ran) — NEVER CandidateKey.generation
    (the per-individual generation within a run). This is exactly the
    view needed to compare a race across G20/G25/G100/G520 regimes.
    """
    pooled = _pool(
        results, relevant_categories,
        key_fn=lambda result, candidate: (candidate.candidate.race, result.generations),
    )
    return {key: _build_race_summary(group, relevant_categories, key[0]) for key, group in pooled.items()}


# ---------------------------------------------------------------------------
# Campaign Runner V2 — multi-system campaigns (Clerics, Skeletons, Melforks,
# Axiomantes, Pantheon in this tranche). Everything above this line is
# Commit 27, untouched — CampaignSpec/CampaignRunResult/run_campaign()/
# summarize_by_race()/summarize_by_race_and_generations() keep behaving
# exactly as they did, Clerics-only, byte-for-byte. What follows is
# purely additive: a second, parallel spec/result family that composes
# core.services.backtest_generators's adapters instead of hardcoding
# factions.clerics.algorithm.execute() the way run_campaign() does.
#
# No faction algorithm and no line of backtest_orchestrator.py changed
# to make this possible — see backtest_generators.py's module docstring
# for the per-system RNG/Ariadne/persistence contract each adapter
# preserves.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MultiSystemCampaignSpec:
    """systems is an explicit, caller-chosen tuple of generator ids —
    looked up in the `generators` mapping passed to
    run_system_campaign() (GENERATORS by default). Never auto-discovered
    from factions/*: adding a system here is always a deliberate,
    one-line registration in that mapping, never automatic — this is
    what keeps Vampires/Gargoyles/Kor Vermelho/Werewolves (all
    look-ahead- or provenance-blocked, per the Campaign Runner V2 audit)
    out unless and until someone explicitly adds a vetted adapter for
    them.

    generations applies ONLY to systems whose adapter declares
    has_generations=True (only Clerics in this tranche) — systems
    without that axis simply never enter the inner generations loop;
    their results carry generations=None, never a value from this
    tuple repurposed to mean something else.
    """

    targets: tuple[BacktestTarget, ...]
    seeds: tuple[int, ...]
    systems: tuple[str, ...]
    generations: tuple[int, ...]
    mode: Literal["verified", "exploratory"]
    relevant_categories: frozenset[str]


@dataclass(frozen=True)
class GeneratorRunResult:
    """One grid cell for one system. Unlike CampaignRunResult, there is
    no nested BacktestRunRecord — this type never touches
    backtest_orchestrator.BacktestRunRecord (whose `generations: int`
    field is not optional, and changing that would mean editing
    Commit 25 code for the sake of systems that aren't Clerics).
    `generations` here is honest per system: a real int for Clerics
    (and, if reported by its own adapter, Melforks), None for every
    system without that concept — never invented to fit a uniform
    shape.

    attempted_races is optional (defaults to an empty frozenset, fully
    backward compatible with every adapter that predates it) — the set
    of race/strategy labels this cell's adapter deliberately tried,
    whether or not each one produced a candidate. Exists so a strategy
    that abstains in every single cell (e.g. Astéria Abissal when the
    conditional sample is always too small) can still be discovered and
    correctly reported as 100% abstention by
    core.services.backtest_arena.summarize_arena_participation(),
    instead of silently disappearing because no CandidateKey with that
    race was ever produced. Populated only by adapters with a fixed,
    small, self-known set of sub-strategies per cell (Pantheon, Astérias)
    — never a central enumeration; Clerics' population-driven races are
    never declared this way, by design.
    """

    system: str
    target: BacktestTarget
    seed: int
    generations: int | None
    run_id: str
    candidates: tuple[SimulatedBacktestCandidate, ...]
    evaluations: tuple[CandidateEvaluation, ...]
    performance: CandidatePerformanceSummary
    attempted_races: frozenset[str | None] = frozenset()


def _build_generator_run_result(
    system: str, target: BacktestTarget, seed: int, output, relevant_categories: frozenset[str],
) -> GeneratorRunResult:
    frozen = tuple(
        SimulatedBacktestCandidate(candidate=c, temporal_basis="historical_input_boundary", run_id=output.run_id)
        for c in output.candidates
    )
    evaluations = reveal_and_evaluate(frozen, target)
    performance = summarize(frozen, evaluations, relevant_categories)
    return GeneratorRunResult(
        system=system, target=target, seed=seed, generations=output.generations,
        run_id=output.run_id, candidates=frozen, evaluations=evaluations, performance=performance,
        attempted_races=output.attempted_races,
    )


def run_system_campaign(
    cfg: configparser.ConfigParser,
    spec: MultiSystemCampaignSpec,
    *,
    generators: Mapping[str, GeneratorAdapter] = GENERATORS,
    historical_root=None,
    scrolls_root=None,
) -> tuple[GeneratorRunResult, ...]:
    """Iterates systems x targets x seeds x (generations, only for
    systems that have that axis) in that order. ctx/ariadne_temporal
    are built once per (system, target, seed) via
    prepare_backtest_run() — the same call that already performs the
    one, shared VERIFIED-mode check (backtest_orchestrator.
    _validate_verified_mode) for every system in the campaign; this
    function never duplicates that check itself.

    An unknown system in spec.systems raises ValueError immediately —
    never silently skipped. A system with has_generations=True and an
    empty spec.generations raises ValueError — silently producing zero
    cells for a requested system would be a footgun, not honest
    "not applicable" behaviour (that's what generations=None on the
    result is for, not an empty grid).
    """
    for system in spec.systems:
        if system not in generators:
            raise ValueError(f"unknown system {system!r} — registered systems: {sorted(generators)}")
        if generators[system].has_generations and not spec.generations:
            raise ValueError(f"system {system!r} has a generations axis but spec.generations is empty")

    results = []
    for system in spec.systems:
        adapter = generators[system]
        for target in spec.targets:
            boundary = HistoricalBacktestBoundary(draw_id=target.draw_id, draw_datetime=target.draw_datetime)
            for seed in spec.seeds:
                ctx, ariadne_temporal = prepare_backtest_run(
                    cfg, boundary, mode=spec.mode,
                    historical_root=historical_root, scrolls_root=scrolls_root,
                )
                if adapter.has_generations:
                    for generations in spec.generations:
                        cell_cfg = _cfg_with_generations(cfg, generations)
                        output = adapter.run(cell_cfg, ctx, ariadne_temporal, seed, boundary)
                        results.append(_build_generator_run_result(system, target, seed, output, spec.relevant_categories))
                else:
                    output = adapter.run(cfg, ctx, ariadne_temporal, seed, boundary)
                    results.append(_build_generator_run_result(system, target, seed, output, spec.relevant_categories))
    return tuple(results)


def summarize_by_system_and_strategy(
    results: Sequence[GeneratorRunResult], relevant_categories: Collection[str],
) -> dict[tuple[str, str | None], RacePerformanceSummary]:
    """Pools every (candidate, evaluation) pair across every cell in
    `results`, grouped by (result.system, CandidateKey.race) exactly as
    each adapter produced them — never a fixed list of systems or
    strategies anywhere in this function. A future system (e.g. a
    "cyber_anoes" adapter someone registers later) appears automatically
    the moment its GeneratorRunResult.system value shows up in
    `results`, with zero changes here.
    """
    pooled = _pool(
        results, relevant_categories,
        key_fn=lambda result, candidate: (result.system, candidate.candidate.race),
    )
    return {key: _build_race_summary(group, relevant_categories, key[1]) for key, group in pooled.items()}


def summarize_by_system_strategy_and_generations(
    results: Sequence[GeneratorRunResult], relevant_categories: Collection[str],
) -> dict[tuple[str, str | None, int | None], RacePerformanceSummary]:
    """Same as summarize_by_system_and_strategy() but grouped by
    (system, race, generations) — generations is None for every system
    without that axis, so e.g. ("skeletons", "Esqueleto", None) is a
    perfectly valid, expected key, never coerced into a fake int.
    """
    pooled = _pool(
        results, relevant_categories,
        key_fn=lambda result, candidate: (result.system, candidate.candidate.race, result.generations),
    )
    return {key: _build_race_summary(group, relevant_categories, key[1]) for key, group in pooled.items()}
