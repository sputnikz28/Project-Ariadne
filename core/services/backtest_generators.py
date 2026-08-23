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

Astérias de Thalássia (Arena Temporada 2): two lineages sharing one
system, "asterias" — Astéria Abissal (purist conditional star-pair
transition, abstains under a fixed sample-size threshold) and Astéria
das Marés (same conditional model, explicit backoff to the marginal
star distribution instead of abstaining). The only hypothesis tested is
about stars; numeros are always neutral uniform sampling, the same
mechanism Acaso Puro uses. Both lineages always declare themselves via
GeneratorOutput.attempted_races, every cell, so a lineage that abstains
in 100% of cells is still discoverable and correctly reported as full
abstention by core.services.backtest_arena, never silently disappearing
for lack of a CandidateKey.

Treefolks V2 — As Grandes Florestas (Arena Temporada 3): one system,
"treefolks_v2", composed of five Florestas (Yggdrasil/LSTM,
Dodona/Bayes, Brocéliande/Markov, Tír na nÓg/Monte Carlo,
Fortuna/control) — see core/services/treefolks_v2/ for the full
per-Floresta contract. Sistema -> Floresta -> Treefolk is expressed
entirely through the existing CandidateKey shape: source_name is the
fixed constant "treefolks_v2" (same convention as every other system
here), and `race` is a single composed string "Floresta — Treefolk"
(e.g. "Yggdrasil — LSTM-v1") — no new field anywhere. Each Floresta
gets its OWN independently-namespaced RNG stream via
core.services.treefolks_v2.common.forest_rng() — never a single
sequential stream shared across Florestas — because Yggdrasil's
internal training consumes a variable amount of randomness that would
otherwise silently desynchronize every other Floresta's draws. Every
Floresta always declares itself in attempted_races, even in full
abstention (insufficient history, or — Yggdrasil only — PyTorch not
installed), reusing the exact same mechanism already proven for
Astérias, with zero extension. Fangorn/Ensemble is deliberately absent:
roadmap only, blocked until real Arena results exist for the other
five.
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
from core.services.treefolks_v2.broceliande import run_broceliande
from core.services.treefolks_v2.common import build_key_from_scores, forest_rng
from core.services.treefolks_v2.dodona import run_dodona
from core.services.treefolks_v2.fortuna import run_fortuna
from core.services.treefolks_v2.tirnanog import run_tirnanog
from core.services.treefolks_v2.yggdrasil import run_yggdrasil
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

    attempted_races is optional (defaults empty, fully backward
    compatible) — the set of race/strategy labels this call
    deliberately tried, whether or not each one produced a candidate.
    Only adapters with a fixed, small, self-known set of sub-strategies
    per cell need to populate it (Pantheon, Astérias) — never a
    central enumeration living outside the adapter itself. See
    core.services.backtest_campaign.GeneratorRunResult's docstring for
    why this exists: a strategy that abstains in every single cell
    would otherwise never be discoverable by
    core.services.backtest_arena.summarize_arena_participation().
    """

    candidates: tuple[CandidateKey, ...]
    run_id: str
    generations: int | None
    attempted_races: frozenset[str | None] = frozenset()


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


_ASTERIAS_ALPHA = 1
_ASTERIAS_MIN_OCCURRENCES = 5
_ASTERIAS_LINEAGES = (("abissal", "Astéria Abissal"), ("mares", "Astéria das Marés"))


def _star_pair(estrelas) -> tuple[int, int]:
    a, b = sorted(estrelas)
    return (a, b)


def _count_conditional_star_votes(historico, query_pair):
    """n(P), c(s,P) for s in 1..12 -- P = query_pair. The loop bound
    (len(historico) - 1) structurally excludes the last position as a
    "current" occurrence: that position IS query_pair by construction
    (see _run_asterias), so looking past it would require the target
    itself. This is what makes the target's instant unreachable here,
    the same way HistoricalBacktestBoundary has no numeros/estrelas
    field at all for Clerics.
    """
    n = 0
    counts = {s: 0 for s in range(1, 13)}
    for i in range(len(historico) - 1):
        if _star_pair(historico[i]["estrelas"]) == query_pair:
            n += 1
            for s in historico[i + 1]["estrelas"]:
                counts[s] += 1
    return n, counts


def _marginal_star_counts(historico):
    counts = {s: 0 for s in range(1, 13)}
    for draw in historico:
        for s in draw["estrelas"]:
            counts[s] += 1
    return counts


def _smoothed_probabilities(counts, total_votes, alpha=_ASTERIAS_ALPHA):
    """Laplace/additive smoothing, alpha fixed at 1 -- never tuned after
    seeing results. Sums to exactly 1 over the 12 stars whenever
    total_votes == sum(counts.values()), which both callers guarantee
    (2*n for the conditional table, 2*len(historico) for the marginal).
    """
    denom = total_votes + 12 * alpha
    return {s: (counts[s] + alpha) / denom for s in range(1, 13)}


def _sample_two_stars(probabilities, rng):
    """Weighted sampling without replacement, canonical ascending order
    (1..12) fed to the sampler every time -- reproducibility given a
    fixed rng state never depends on dict/set iteration order. Ties in
    probability are resolved by the weighted sampler itself (uniform
    among tied candidates), never by a separate tie-break rule.
    """
    stars = list(range(1, 13))
    first = rng.choices(stars, weights=[probabilities[s] for s in stars], k=1)[0]
    rest = [s for s in stars if s != first]
    second = rng.choices(rest, weights=[probabilities[s] for s in rest], k=1)[0]
    return tuple(sorted((first, second)))


def _asterias_distribution(historico, lineage):
    """Returns (probabilities, participates) for one lineage ("abissal"
    or "mares") at this cell. Pure -- no RNG, no side effects.
    """
    query_pair = _star_pair(historico[-1]["estrelas"])
    n, cond_counts = _count_conditional_star_votes(historico, query_pair)

    if n >= _ASTERIAS_MIN_OCCURRENCES:
        return _smoothed_probabilities(cond_counts, 2 * n), True

    if lineage == "abissal":
        return None, False

    # lineage == "mares": explicit backoff to the marginal distribution.
    if len(historico) >= _ASTERIAS_MIN_OCCURRENCES:
        marg_counts = _marginal_star_counts(historico)
        return _smoothed_probabilities(marg_counts, 2 * len(historico)), True

    return None, False


def asterias_distribution(historico, lineage):
    """Public wrapper over _asterias_distribution() -- same contract,
    exposed for reuse by analysis code outside this module (e.g.
    core.services.star_contribution_trial) that needs the exact same
    probabilities the real adapter would use, without duplicating the
    formula. _run_asterias() itself keeps calling the private name --
    this function is purely an external reuse seam.
    """
    return _asterias_distribution(historico, lineage)


def sample_two_stars(probabilities, rng):
    """Public wrapper over _sample_two_stars() -- same reuse rationale
    as asterias_distribution() above.
    """
    return _sample_two_stars(probabilities, rng)


def _run_asterias(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """Astéria Abissal (purist -- abstains when the conditional sample
    on the previous star pair has fewer than 5 historical occurrences)
    and Astéria das Marés (same conditional distribution, explicit
    backoff to the marginal star distribution when the sample is too
    small). The hypothesis is exclusively about stars -- numeros are
    always uniform/neutral sampling, the same mechanism Acaso Puro uses,
    never informed by the star-transition data.

    Only ctx['historico'] (already temporally cut, same as every other
    non-Ariadne adapter) -- no Ariadne, no persistent memory, VERIFIED-
    safe by construction, same class as Skeletons/Melforks/Pantheon.

    RNG: random.Random(seed), one instance per cell, constructed here --
    the same pattern _run_skeletons()/_run_pantheon() already use
    (ctx['rng'] is not populated by prepare_backtest_run() for the
    shared multi-system path; each adapter that needs one builds its
    own). Consumed sequentially: Abissal's `quantidade` candidates
    first, then Marés's -- same fixed-order convention as
    _run_pantheon().

    attempted_races always declares both lineage labels, every cell,
    regardless of which one (if any) actually abstains -- so a lineage
    that abstains in 100% of cells still gets discovered and reported
    honestly by summarize_arena_participation(), never disappearing
    for lack of a CandidateKey.
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:asterias", target_draw=boundary.draw_id)
    quantidade = cfg.getint("ARENA", "asterias_quantidade", fallback=20)
    historico = ctx["historico"]
    rng = random.Random(seed)

    candidates = []
    for lineage, race in _ASTERIAS_LINEAGES:
        probabilities, participates = _asterias_distribution(historico, lineage)
        if not participates:
            continue
        for i in range(quantidade):
            estrelas = _sample_two_stars(probabilities, rng)
            numeros = rng.sample(range(1, 51), 5)
            chave = normalize_candidate(numeros, list(estrelas), rng)
            record = {"nome": f"{race}-{i + 1}", "tipo": race, "chave": chave}
            candidates.append(_candidate_key_from_record(record, "external_generator", "asterias_thalassia", race))

    candidates = tuple(candidates)
    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(
        candidates=candidates, run_id=manifest["run_id"], generations=None,
        attempted_races=frozenset(race for _lineage, race in _ASTERIAS_LINEAGES),
    )


_TREEFOLKS_V2_FORESTS = (
    "Yggdrasil — LSTM-v1",
    "Dodona — Bayes-v1",
    "Brocéliande — Markov-v1",
    "Tír na nÓg — MonteCarlo-v1",
    "Fortuna — Controlo-v1",
)


def _treefolk_candidates(scores, rng, quantidade, race) -> list[CandidateKey]:
    """Turns one Floresta's TreefolkScores into `quantidade` candidates
    via the single shared common.build_key_from_scores() — the only
    place any Treefolk's score becomes an actual key, so differences
    in Arena performance come from the model, never the constructor.
    """
    out = []
    for i in range(quantidade):
        numeros, estrelas = build_key_from_scores(scores.number_scores, scores.star_scores, rng)
        chave = normalize_candidate(list(numeros), list(estrelas), rng)
        record = {"nome": f"{race}-{i + 1}", "tipo": race, "chave": chave}
        out.append(_candidate_key_from_record(record, "external_generator", "treefolks_v2", race))
    return out


def _run_treefolks_v2(cfg, ctx, ariadne_temporal, seed, boundary) -> GeneratorOutput:
    """Despacha as 5 Florestas em ordem fixa e documentada (Yggdrasil,
    Dodona, Brocéliande, Tír na nÓg, Fortuna). Cada Floresta recebe o
    seu próprio stream de RNG via forest_rng(seed, floresta, draw_id)
    — nunca um único random.Random(seed) sequencial partilhado (ver
    docstring do módulo). Todas as 5 declaram-se sempre em
    attempted_races, mesmo em abstenção total.

    Yggdrasil consome uma chamada do seu próprio stream para derivar
    um inteiro para torch.manual_seed() (getrandbits, determinístico
    dado o mesmo stream), depois reutiliza o MESMO stream (já avançado)
    para a construção final das chaves — consumo sequencial, ordem
    fixa, mesmo princípio já usado por Tír na nÓg (stream consumido
    primeiro nas simulações Monte Carlo internas, depois na construção
    final das chaves).
    """
    manifest = start_run(seed, _modo_semente(cfg), command="backtest_campaign:treefolks_v2", target_draw=boundary.draw_id)
    quantidade = cfg.getint("TREEFOLKS_V2", "quantidade_por_treefolk", fallback=20)
    historico = ctx["historico"]

    candidates: list[CandidateKey] = []

    yggdrasil_rng = forest_rng(seed, "yggdrasil", boundary.draw_id)
    yggdrasil_scores = run_yggdrasil(historico, yggdrasil_rng.getrandbits(63))
    if yggdrasil_scores is not None:
        candidates.extend(_treefolk_candidates(yggdrasil_scores, yggdrasil_rng, quantidade, _TREEFOLKS_V2_FORESTS[0]))

    dodona_rng = forest_rng(seed, "dodona", boundary.draw_id)
    dodona_scores = run_dodona(historico)
    candidates.extend(_treefolk_candidates(dodona_scores, dodona_rng, quantidade, _TREEFOLKS_V2_FORESTS[1]))

    broceliande_rng = forest_rng(seed, "broceliande", boundary.draw_id)
    broceliande_scores = run_broceliande(historico)
    if broceliande_scores is not None:
        candidates.extend(_treefolk_candidates(broceliande_scores, broceliande_rng, quantidade, _TREEFOLKS_V2_FORESTS[2]))

    tirnanog_rng = forest_rng(seed, "tirnanog", boundary.draw_id)
    tirnanog_scores = run_tirnanog(historico, tirnanog_rng)
    if tirnanog_scores is not None:
        candidates.extend(_treefolk_candidates(tirnanog_scores, tirnanog_rng, quantidade, _TREEFOLKS_V2_FORESTS[3]))

    fortuna_rng = forest_rng(seed, "fortuna", boundary.draw_id)
    fortuna_scores = run_fortuna(historico)
    candidates.extend(_treefolk_candidates(fortuna_scores, fortuna_rng, quantidade, _TREEFOLKS_V2_FORESTS[4]))

    candidates = tuple(candidates)
    manifest = complete_run(manifest, generated_record_count=len(candidates))
    return GeneratorOutput(
        candidates=candidates, run_id=manifest["run_id"], generations=None,
        attempted_races=frozenset(_TREEFOLKS_V2_FORESTS),
    )


GENERATORS: Mapping[str, GeneratorAdapter] = MappingProxyType({
    "clerics": GeneratorAdapter("clerics", True, _run_clerics),
    "skeletons": GeneratorAdapter("skeletons", False, _run_skeletons),
    "melforks": GeneratorAdapter("melforks", False, _run_melforks),
    "axiomantes": GeneratorAdapter("axiomantes", False, _run_axiomantes),
    "pantheon": GeneratorAdapter("pantheon", False, _run_pantheon),
    "acaso_puro": GeneratorAdapter("acaso_puro", False, _run_acaso_puro),
    "asterias": GeneratorAdapter("asterias", False, _run_asterias),
    "treefolks_v2": GeneratorAdapter("treefolks_v2", False, _run_treefolks_v2),
})
