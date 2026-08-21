"""Backtest Orchestrator V1 (Commit 25) — the first minimal, real
end-to-end historical backtest: given a historical instant (never the
winning key), builds a temporally-scoped context (Commit 22), a
temporal Ariadne (Commit 23, constructed but not yet consumed), runs
the real, unmodified Clerics genetic algorithm
(factions.clerics.algorithm.execute) over it, freezes the result, and
only THEN reveals the target's key for evaluation (Commits 17-18).

V1 scope is deliberately narrow: Clerics only. It is the one
methodology confirmed, by direct reading, to be free of Ariadne and of
uncertified persistent memory *except* for two config-gated paths
inside its own generation loop (tentar_encontrar/ARCA_ARTEFACTOS,
forjar->maybe_materialize/ARTEFACTOS_VIVOS, conceder_audiencia/
MONGES_E_ESCRIBAS) — VERIFIED mode requires all of them disabled (see
_validate_verified_mode). Every other faction, the Council, Malphas,
the Black Squad and the Elven Order are out of scope for V1.

Never calls main.py, world/engine/builder.py, or
core.data.loaders.get_history() — historico/mundo are built exclusively
from core.services.historical_simulation_source (Commit 22) and the
pure obter_lua()/obter_jackpot() helpers, never from a live API/cache
fallback.

Two temporal guarantees, never conflated:
  Fronteira B (core.services.backtest_lab.freeze_backtest_candidates)
    — for candidates of UNKNOWN provenance pulled from the persisted
    archive: proves a run's manifest completed before the target's
    reveal. NOT used here.
  Fronteira A (this module) — for candidates FRESHLY GENERATED in this
    same run: their honesty comes from prepare_backtest_run() never
    having given the simulation anything at or after the target's
    instant, never from a manifest-timestamp check (which would be
    structurally impossible to satisfy for a deliberate retrospective
    computation run today, about a target in the past). Marked
    explicitly via SimulatedBacktestCandidate.temporal_basis =
    "historical_input_boundary" — never presented as, or mistaken for,
    Fronteira-B-verified.

The target's key is structurally unreachable during preparation and
simulation: prepare_backtest_run()/run_clerics_backtest() accept only
a HistoricalBacktestBoundary (draw_id + draw_datetime, no numeros/
estrelas field exists on that type at all) — not a BacktestTarget.
Only reveal_and_evaluate() receives the full BacktestTarget.
"""

from __future__ import annotations

import configparser
import random
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.data.loaders import obter_jackpot, obter_lua
from core.evolution.statistics import calculate
from core.services.backtest_lab import BacktestTarget
from core.services.candidate_evaluation import CandidateEvaluation, evaluate_candidates
from core.services.candidate_performance import CandidatePerformanceSummary, summarize_candidate_performance
from core.services.candidate_provenance import CandidateKey, normalize_candidate_record
from core.services.historical_ariadne_source import build_scrolls_for_backtest
from core.services.historical_simulation_source import build_historical_context_for_backtest
from core.services.run_manifest import complete_run, start_run
from factions.clerics.algorithm import execute as _run_clerics_algorithm
from library.ariadne.engine import Ariadne


def _require_timezone_aware(dt: datetime, label: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware, got a naive datetime: {dt!r}")


@dataclass(frozen=True)
class HistoricalBacktestBoundary:
    """The only historical instant prepare_backtest_run()/
    run_clerics_backtest() ever see. Deliberately has no numeros/
    estrelas field — there is no attribute on this type the winning
    key could be read from, structurally, not just by convention.
    """

    draw_id: str
    draw_datetime: datetime

    def __post_init__(self) -> None:
        _require_timezone_aware(self.draw_datetime, "HistoricalBacktestBoundary.draw_datetime")


@dataclass(frozen=True)
class SimulatedBacktestCandidate:
    """One candidate generated in this run, over a context already
    bounded to < boundary.draw_datetime. temporal_basis is a closed
    Literal (currently one value) — never "verified"/"legacy"/etc.,
    the Fronteira-B vocabulary from backtest_lab.py, which does not
    apply here (see module docstring).
    """

    candidate: CandidateKey
    temporal_basis: Literal["historical_input_boundary"]
    run_id: str


@dataclass(frozen=True)
class BacktestRunRecord:
    """Minimal summary of one backtest run. run_id (from run_manifest,
    when the computation actually happened) and target.draw_datetime
    (the historical instant it studies) are deliberately two separate
    fields — never conflated into one timestamp.
    """

    run_id: str
    target: BacktestTarget
    mode: Literal["verified", "exploratory"]
    temporal_basis: Literal["historical_input_boundary"]
    generations: int
    candidate_count: int
    relevant_categories: frozenset
    performance: CandidatePerformanceSummary


_VERIFIED_MODE_GATES = (
    ("ARTEFACTOS_VIVOS", "ativo", False),
    ("ARCA_ARTEFACTOS", "permitir_redescoberta", False),
    ("ARCA_ARTEFACTOS", "ativa", False),
)
_MONGES_E_ESCRIBAS_ACCESS_KEYS = (
    "acesso_total", "acesso_quentes_frios", "acesso_historico", "acesso_pares_trios", "acesso_gaps",
)


def _validate_verified_mode(cfg: configparser.ConfigParser) -> None:
    """Raises ValueError listing every violation if `cfg` would let
    factions.clerics.algorithm.execute() reach any uncertified
    persistent memory:

      - ARTEFACTOS_VIVOS.ativo — gates forjar()/evoluir()/herdar()/
        marcar_perdido(), which read AND write artifacts/relics/*.json.
      - ARCA_ARTEFACTOS.permitir_redescoberta — gates
        tentar_encontrar()'s own read of artifacts/relics/*.json,
        called unconditionally every generation regardless of
        ARTEFACTOS_VIVOS.
      - ARCA_ARTEFACTOS.ativa — gates maybe_materialize() (only
        reachable via forjar(), i.e. already behind ARTEFACTOS_VIVOS
        above) — required anyway, as defense in depth, exactly per
        audited principle: no executable path to uncertified memory,
        not just the one path known today.
      - MONGES_E_ESCRIBAS's five acesso_* keys — conceder_audiencia()
        is called unconditionally for every hero every generation;
        livros_permitidos() only ever returns [] for every race (and
        so never reads artifacts/amulets/books/*.json) when all five
        are empty. The real config.txt today lists Bruxa/Shaman/Elfo/
        Cronomante under some of these — verified live, not assumed.
    """
    violations = []
    for section, key, required in _VERIFIED_MODE_GATES:
        if cfg.getboolean(section, key, fallback=True) != required:
            violations.append(f"[{section}] {key} must be {str(required).lower()}")
    for key in _MONGES_E_ESCRIBAS_ACCESS_KEYS:
        if cfg.get("MONGES_E_ESCRIBAS", key, fallback="").strip():
            violations.append(f"[MONGES_E_ESCRIBAS] {key} must be empty")
    if violations:
        raise ValueError(
            "VERIFIED backtest mode requires uncertified persistent memory to be "
            "structurally unreachable, not just unlikely — found: " + "; ".join(violations)
        )


def _derive_mundo_cfg(cfg: configparser.ConfigParser, boundary: HistoricalBacktestBoundary) -> configparser.ConfigParser:
    """A COPY of `cfg` (never mutates the caller's cfg) with [MUNDO].data/
    hora overridden to boundary.draw_datetime converted into
    [MUNDO].timezone's local time — never the ambient config value
    (which could be "today"), never the real clock. Required in
    both modes: this has nothing to do with the verified/exploratory
    persistent-memory distinction, and a silently-different, weaker
    behavior in exploratory mode would be exactly the kind of hidden
    permissive default this project has repeatedly ruled out.
    """
    tz_name = cfg.get("MUNDO", "timezone", fallback="").strip()
    if not tz_name:
        raise ValueError("[MUNDO].timezone is required to derive an honest historical local time — none configured")
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as e:
        raise ValueError(f"[MUNDO].timezone={tz_name!r} is not a recognized timezone") from e

    local_dt = boundary.draw_datetime.astimezone(tz)

    mundo_cfg = configparser.ConfigParser()
    for section in cfg.sections():
        mundo_cfg[section] = dict(cfg[section])
    if not mundo_cfg.has_section("MUNDO"):
        mundo_cfg.add_section("MUNDO")
    mundo_cfg.set("MUNDO", "data", local_dt.strftime("%Y-%m-%d"))
    mundo_cfg.set("MUNDO", "hora", local_dt.strftime("%H:%M"))
    return mundo_cfg


def prepare_backtest_run(
    cfg: configparser.ConfigParser,
    boundary: HistoricalBacktestBoundary,
    *,
    mode: Literal["verified", "exploratory"],
    historical_root=None,
    scrolls_root=None,
) -> tuple[dict, Ariadne]:
    """Never receives a BacktestTarget — only `boundary` (draw_id +
    draw_datetime). Builds and returns (ctx, ariadne_temporal); ctx is
    ready to pass to run_clerics_backtest(). ariadne_temporal is built
    (Commit 23) but not consumed by V1's Clerics-only simulation step —
    available for a future commit.

    Never calls world/engine/builder.py:build() or
    core.data.loaders.get_history() — historico comes exclusively from
    core.services.historical_simulation_source (Commit 22); mundo is
    built from the pure obter_lua()/obter_jackpot() helpers only.

    mode="verified" raises ValueError (see _validate_verified_mode) if
    `cfg` would let the simulation reach any uncertified persistent
    memory. mode="exploratory" skips that check — never silently, the
    caller opted in explicitly via `mode`.
    """
    if mode not in ("verified", "exploratory"):
        raise ValueError(f"mode must be 'verified' or 'exploratory', got {mode!r}")
    if mode == "verified":
        _validate_verified_mode(cfg)

    historico = build_historical_context_for_backtest(boundary.draw_datetime, historical_root)
    mundo_cfg = _derive_mundo_cfg(cfg, boundary)
    lua = obter_lua(mundo_cfg)
    jackpot, _fonte = obter_jackpot(cfg, historico)
    mundo = {"fase_lua": lua["fase"], "jackpot": jackpot}
    estatisticas = calculate(historico)

    ctx = {"historico": historico, "estatisticas": estatisticas, "mundo": mundo}

    scrolls = build_scrolls_for_backtest(boundary.draw_datetime, scrolls_root)
    ariadne_temporal = Ariadne(scrolls=scrolls)

    return ctx, ariadne_temporal


def run_clerics_backtest(
    cfg: configparser.ConfigParser,
    ctx: dict,
    seed: int,
    boundary: HistoricalBacktestBoundary,
) -> tuple[dict, dict]:
    """Never receives a BacktestTarget — only `boundary`. Seeds the
    global random module (same convention as main.py), starts a real
    run manifest (target_draw=boundary.draw_id — the first real use of
    that pre-existing, previously-always-None parameter), runs the
    real, unmodified factions.clerics.algorithm.execute(), stamps
    run_id onto every produced record (same pattern as main.py), and
    only THEN completes the manifest.

    Deliberately no try/except around execute(): if it raises, this
    function raises too, complete_run() is never called, and the
    "<run_id>.incomplete.json" file start_run() already wrote to disk
    remains as-is — standing evidence of the attempt, never silently
    promoted to a completed/successful manifest.
    """
    modo_semente = cfg.get("SIMULACAO", "modo_semente", fallback="fixo").strip().lower()
    random.seed(seed)
    run_manifest = start_run(seed, modo_semente, command="backtest_orchestrator", target_draw=boundary.draw_id)

    # ctx['rng'] is required (bracket access, not .get()) by the
    # Cronomante branch of factions/clerics/archetypes.py — same
    # construction main.py already does at seeding time. A copy, never
    # mutating the caller's ctx.
    clerics_ctx = {**ctx, "seed": seed, "rng": random.Random(seed)}
    evo = _run_clerics_algorithm(cfg, clerics_ctx)

    for record in evo["registos"]:
        record["run_id"] = run_manifest["run_id"]

    run_manifest = complete_run(run_manifest, generated_record_count=len(evo["registos"]))
    return evo, run_manifest


def freeze_simulated_candidates(evo: dict) -> tuple[SimulatedBacktestCandidate, ...]:
    """evo['registos'] (already run_id-stamped by run_clerics_backtest)
    -> normalize_candidate_record() each -> SimulatedBacktestCandidate.
    Deliberately NOT core.services.backtest_lab.freeze_backtest_candidates()
    — see module docstring on Fronteira A vs. B. Never mutates `evo`.
    """
    return tuple(
        SimulatedBacktestCandidate(
            candidate=normalize_candidate_record(record),
            temporal_basis="historical_input_boundary",
            run_id=record["run_id"],
        )
        for record in evo["registos"]
    )


def reveal_and_evaluate(
    candidates: Sequence[SimulatedBacktestCandidate],
    target: BacktestTarget,
) -> tuple[CandidateEvaluation, ...]:
    """The only function in this module that receives the winning key
    — always after prepare/simulate/freeze already ran without it. Thin
    wrapper over core.services.candidate_evaluation.evaluate_candidates();
    no matching logic lives here.
    """
    return evaluate_candidates(
        tuple(c.candidate for c in candidates), target.numeros, target.estrelas,
    )


def summarize(
    candidates: Sequence[SimulatedBacktestCandidate],
    evaluations: Sequence[CandidateEvaluation],
    relevant_categories: Collection[str],
) -> CandidatePerformanceSummary:
    """Thin wrapper over
    core.services.candidate_performance.summarize_candidate_performance();
    no category/diversity/relevance logic lives here.
    """
    return summarize_candidate_performance(
        tuple(c.candidate for c in candidates), evaluations, relevant_categories,
    )
