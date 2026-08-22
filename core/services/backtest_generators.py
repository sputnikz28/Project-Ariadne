"""Backtest Generator Adapters (Campaign Runner V2) — external adapters
that let core.services.backtest_campaign.run_system_campaign() drive
generators other than Clerics, without altering any faction algorithm
and without altering core/services/backtest_orchestrator.py (Commit 25).

Architectural principle: every adapter below calls the ORIGINAL faction
function exactly as it exists today (factions/skeletons/algorithm.py,
factions/melforks/algorithm.py, factions/axiomantes/ritual.py,
orders/pantheon/*.py) — same signature, same RNG contract, same
"no closed-memory access" guarantee already audited for each of them.
No faction file is imported for its side effects to be changed, only
called.

RNG contract is preserved PER GENERATOR, never uniformised:
  - Clerics (via backtest_orchestrator.run_clerics_backtest, untouched)
    and Skeletons/Pantheon: ctx['rng'] (random.Random(seed)) — the
    exact contract those algorithms already expect.
  - Melforks: global `random` module, seeded once per cell via
    random.seed(seed) — never given a ctx['rng'] it would never read.
  - Axiomantes: no RNG at all for the core Feistel walk — `seed` is a
    structural permutation parameter (core.services.fitness is not
    involved); the one incidental `normalize_candidate(..., random)`
    call at the end (same call factions/axiomantes/council.py already
    makes) only ever touches global `random` state if the chosen key
    were short, which never happens for a real Axiomantes selection.

Every candidate produced here is fresh (never read from
datasets/generated/simulations/arquivo_destino.json), so none of these
adapters go through core.services.candidate_provenance.
normalize_candidate_record() — that function's closed origem taxonomy
is irrelevant here. CandidateKey objects are built directly, honestly:
`race` is always forwarded verbatim from whatever the original
function already labelled its own output as ('tipo', or 'nome' for
Aion specifically — see _run_pantheon) — never a new enumeration,
never invented here. `source_name` mirrors the real, already-audited
origem string for that system (e.g. "esqueleto", "melfork",
"axiomantes_nemerion", "ser_superior", "deus") so provenance stays
traceable to the same vocabulary the real archive already uses, even
though these records never get persisted there.

No look-ahead: every adapter is called by
core.services.backtest_campaign.run_system_campaign() with a `ctx`/
`ariadne_temporal` pair already built by
core.services.backtest_orchestrator.prepare_backtest_run(), which is
what performs the one, shared VERIFIED-mode check
(backtest_orchestrator._validate_verified_mode) for every system in a
campaign — this module never duplicates that check, and never
constructs a live Ariadne() itself. Axiomantes is the one adapter here
that consults Ariadne at all; it is passed `ariadne_temporal` and
never anything else.

No disk artefacts: run_manifest.start_run()/complete_run() (Commit 25,
generic, unmodified) give every cell, in every system, a real run_id —
the same core.services.run_manifest.RUNS_DIR isolation already used by
Commit 27's tests covers all systems uniformly. Axiomantes'
[AXIOMANTES] guardar_experiencia is unconditionally forced to false
inside _run_axiomantes() — no campaign, test, or smoke test ever
writes to experiments/axiomancers/runs/.

Acaso Puro (Arena baseline, added alongside the Arena layer in
core/services/backtest_arena.py): the structurally safest generator
here — touches nothing from ctx/ariadne_temporal at all, only
[ARENA].acaso_puro_quantidade and a fresh random.Random(seed). Reserved
as a baseline since the project's own benchmarks/random/README.md
("statistical floor every real faction/strategy should be compared
against"), never implemented until now.
"""

from __future__ import annotations

import configparser
import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from core.services.backtest_orchestrator import (
    HistoricalBacktestBoundary,
    freeze_simulated_candidates,
    run_clerics_backtest,
)
from core.services.candidate_provenance import CandidateKey
from core.services.combinations import normalize_candidate
from core.services.run_manifest import complete_run, start_run
from factions.axiomantes.ritual import execute_ritual
from factions.melforks.algorithm import melforks
from factions.skeletons.algorithm import create_representatives
from library.ariadne.engine import Ariadne
from orders.pantheon.aion import create_aion
from orders.pantheon.djinns import create_djinn_representatives
from orders.pantheon.druids import create_druid_representatives
from orders.pantheon.mages import create_mage_representatives


@dataclass(frozen=True)
class GeneratorOutput:
    """What one adapter invocation produces for one campaign cell.
    generations is None whenever the system has no meaningful
    generations axis for this integration — never fabricated, never
    forced to 0/-1 to fit a uniform schema.
    """

    candidates: tuple[CandidateKey, ...]
    run_id: str
    generations: int | None


@dataclass(frozen=True)
class GeneratorAdapter:
    """system is the stable identifier used as the grouping key in
    core.services.backtest_campaign's aggregators — never enumerated
    there, only ever read from whatever GeneratorRunResult.system a
    caller's registry actually produced.

    has_generations decides whether core.services.backtest_campaign.
    run_system_campaign() sweeps spec.generations for this system at
    all — false means the system's cells never enter that loop, and
    every GeneratorOutput it returns carries generations=None.
    """

    system: str
    has_generations: bool
    run: Callable[
        [configparser.ConfigParser, dict, Ariadne, int, HistoricalBacktestBoundary],
        GeneratorOutput,
    ]


_RECORD_METADATA_EXCLUDED_KEYS = frozenset({"nome", "tipo", "classe", "chave"})


def _candidate_key_from_record(record: dict, source_type: str, source_name: str, race) -> CandidateKey:
    """Builds a CandidateKey directly from a raw {'nome','tipo','chave',...}
    dict, the exact shape every adapted function already returns.
    generation/entity_id stay None — none of these systems have a
    genuine per-individual generation number the way Clerics does.
    """
    numeros, estrelas = record["chave"]
    metadata = {k: v for k, v in record.items() if k not in _RECORD_METADATA_EXCLUDED_KEYS}
    return CandidateKey(
        source_type=source_type,
        source_name=source_name,
        numeros=tuple(sorted(numeros)),
        estrelas=tuple(sorted(estrelas)),
        generation=None,
        entity_id=None,
        entity_name=record.get("nome"),
        race=race,
        metadata=MappingProxyType(metadata),
    )


def _cfg_copy(cfg: configparser.ConfigParser) -> configparser.ConfigParser:
    copy = configparser.ConfigParser()
    for section in cfg.sections():
        copy[section] = dict(cfg[section])
    return copy


def _modo_semente(cfg: configparser.ConfigParser) -> str:
    return cfg.get("SIMULACAO", "modo_semente", fallback="fixo").strip().lower()


def _run_clerics(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """Delegates entirely to backtest_orchestrator.run_clerics_backtest()
    (Commit 25, untouched) — the only adapter that does not build its
    own run_manifest entry, since that function already does.
    """
    evo, run_manifest = run_clerics_backtest(cfg, ctx, seed, boundary)
    frozen = freeze_simulated_candidates(evo)
    candidates = tuple(f.candidate for f in frozen)
    generations = cfg.getint("SIMULACAO", "geracoes")
    return GeneratorOutput(candidates=candidates, run_id=run_manifest["run_id"], generations=generations)


def _run_skeletons(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """factions/skeletons/algorithm.py:create_representatives() reads
    only ctx['rng'] — never global `random`, never ctx['historico']/
    ctx['estatisticas']. That contract is preserved exactly: no
    random.seed(seed) call here, since the original function never
    consumes global random state either.
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:skeletons", target_draw=boundary.draw_id)
    rng = random.Random(seed)
    records = create_representatives(cfg, {**ctx, "rng": rng})
    candidates = tuple(
        _candidate_key_from_record(r, "external_generator", "esqueleto", r.get("tipo"))
        for r in records
    )
    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(candidates=candidates, run_id=manifest["run_id"], generations=None)


def _run_melforks(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """factions/melforks/algorithm.py:melforks() reads only
    ctx['estatisticas'] and the global `random` module — ctx['rng'] is
    never constructed or passed, preserving that contract exactly.

    generations reports [MELFORKS].geracoes_chaves honestly (Melforks
    does have its own real generations concept) but is never swept as
    a campaign axis in this tranche — only Clerics' generations is
    spec-controlled; Melforks always runs its own configured value.
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:melforks", target_draw=boundary.draw_id)
    random.seed(seed)
    records = melforks(cfg, ctx)
    candidates = tuple(
        _candidate_key_from_record(r, "external_generator", "melfork", r.get("tipo"))
        for r in records
    )
    generations = cfg.getint("MELFORKS", "geracoes_chaves", fallback=None)
    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(candidates=candidates, run_id=manifest["run_id"], generations=generations)


def _run_axiomantes(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """factions/axiomantes/ritual.py:execute_ritual() is called with
    `ariadne_temporal` — never a live Ariadne() — so full_history()/
    last_known_key() only ever see draws strictly before
    boundary.draw_datetime, exactly like every other consumer of
    prepare_backtest_run()'s temporal Ariadne.

    [AXIOMANTES].guardar_experiencia is unconditionally forced to
    "false" on a COPY of cfg — the caller's cfg is never mutated, and
    experiments/axiomancers/runs/ is never written by a campaign,
    regardless of what the real config.txt says.

    Portal fechado (no candidate this cell) is a legitimate, honest
    outcome — identical to factions/axiomantes/council.py's own
    behaviour — never an error.
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:axiomantes", target_draw=boundary.draw_id)
    axiomantes_cfg = _cfg_copy(cfg)
    if not axiomantes_cfg.has_section("AXIOMANTES"):
        axiomantes_cfg.add_section("AXIOMANTES")
    axiomantes_cfg.set("AXIOMANTES", "guardar_experiencia", "false")

    result = execute_ritual(ariadne_temporal, seed, axiomantes_cfg)

    candidates: tuple[CandidateKey, ...] = ()
    if result and result.get("chave_proposta"):
        nums, ests = result["chave_proposta"]
        chave = normalize_candidate(nums, ests, random)
        record = {"nome": "Axiomantes de Nemerion", "tipo": "Axiomante", "chave": chave}
        candidates = (_candidate_key_from_record(record, "external_generator", "axiomantes_nemerion", "Axiomante"),)

    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(candidates=candidates, run_id=manifest["run_id"], generations=None)


def _run_pantheon(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """orders/pantheon/{mages,druids,djinns,aion}.py already use
    ctx['rng'] (V10.5 RNG retrofit) — preserved exactly.

    Granularity fix, scoped only to this adapter: Mago/Druida/Djinn
    are registered in the REAL archive under the single collapsed
    origem="ser_superior" (main.py:registo_externo, unmodified) — this
    adapter never touches that. It instead forwards each function's
    own, already-honest 'tipo' label ("Mago"/"Druida"/"Djinn") into
    CandidateKey.race, which is what core.services.backtest_campaign's
    aggregators group by — no enumeration of archetypes exists here,
    it is whatever the three functions happen to return this call.
    Aion is the one exception: its 'tipo' is the tier label "Deus"
    (shared, in principle, with any other future aggregator); its
    'nome' ("Aion") is what actually identifies it as this specific
    aggregator, so race=aion['nome'] here, by deliberate choice, not
    by the same "always forward tipo" rule the other three follow.
    source_type="aggregator" for Aion mirrors the real taxonomy's
    origem="deus" classification exactly.
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:pantheon", target_draw=boundary.draw_id)
    rng = random.Random(seed)
    pantheon_ctx = {**ctx, "rng": rng}

    vis = (
        create_mage_representatives(pantheon_ctx)
        + create_druid_representatives(pantheon_ctx)
        + create_djinn_representatives(pantheon_ctx)
    )
    aion = create_aion(vis, pantheon_ctx)

    candidates = tuple(
        _candidate_key_from_record(v, "external_generator", "ser_superior", v.get("tipo"))
        for v in vis
    ) + (
        _candidate_key_from_record(aion, "aggregator", "deus", aion.get("nome")),
    )

    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(candidates=candidates, run_id=manifest["run_id"], generations=None)


def _run_acaso_puro(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """Touches nothing from ctx or ariadne_temporal — no history, no
    statistics, no Ariadne of any kind. Pure uniform sampling over the
    two universes, [ARENA].acaso_puro_quantidade candidates (fallback
    20), seeded once via random.Random(seed). The Arena's control —
    every other system's performance is meant to be read relative to
    this one, never in isolation.
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:acaso_puro", target_draw=boundary.draw_id)
    quantidade = cfg.getint("ARENA", "acaso_puro_quantidade", fallback=20)
    rng = random.Random(seed)
    candidates = []
    for i in range(quantidade):
        chave = normalize_candidate(rng.sample(range(1, 51), 5), rng.sample(range(1, 13), 2), rng)
        record = {"nome": f"Acaso Puro-{i + 1}", "tipo": "Acaso Puro", "chave": chave}
        candidates.append(_candidate_key_from_record(record, "external_generator", "acaso_puro", "Acaso Puro"))
    candidates = tuple(candidates)
    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(candidates=candidates, run_id=manifest["run_id"], generations=None)


GENERATORS: Mapping[str, GeneratorAdapter] = MappingProxyType({
    "clerics": GeneratorAdapter("clerics", True, _run_clerics),
    "skeletons": GeneratorAdapter("skeletons", False, _run_skeletons),
    "melforks": GeneratorAdapter("melforks", False, _run_melforks),
    "axiomantes": GeneratorAdapter("axiomantes", False, _run_axiomantes),
    "pantheon": GeneratorAdapter("pantheon", False, _run_pantheon),
    "acaso_puro": GeneratorAdapter("acaso_puro", False, _run_acaso_puro),
})
