"""Tests for core/services/backtest_campaign.py (Commit 27). All
historical/scroll fixtures are synthetic (tempfile.TemporaryDirectory());
core.services.run_manifest.RUNS_DIR is always patched to a temp
directory so no test here ever writes to the real
datasets/generated/simulations/runs/. No test uses 14/08/2026, or
065/066/067/2026, or any other real draw as its target.
"""

import configparser
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from unittest import mock

from core.services.backtest_campaign import (
    CampaignRunResult,
    CampaignSpec,
    GeneratorRunResult,
    MultiSystemCampaignSpec,
    RacePerformanceSummary,
    run_campaign,
    run_system_campaign,
    summarize_by_race,
    summarize_by_race_and_generations,
    summarize_by_system_and_strategy,
    summarize_by_system_strategy_and_generations,
)
from core.services.backtest_generators import GENERATORS
from core.services.backtest_lab import BacktestTarget
from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_provenance import CandidateKey
from core.services.backtest_orchestrator import SimulatedBacktestCandidate

FUTURE_DT_1 = datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc)
FUTURE_DT_2 = datetime(2099, 3, 17, 20, 0, 0, tzinfo=timezone.utc)


def make_target(draw_id="T-001/2099", draw_datetime=FUTURE_DT_1, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2)):
    return BacktestTarget(draw_id=draw_id, draw_datetime=draw_datetime, numeros=numeros, estrelas=estrelas)


def make_minimal_cfg(**overrides):
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        "SIMULACAO": {"populacao_inicial": "8", "geracoes": "3", "sobreviventes": "4", "modo_semente": "fixo"},
        "CAMINHO_1000_ALMAS": {"ativo": "false"},
        "ARTEFACTOS_VIVOS": {"ativo": "false"},
        "ARCA_ARTEFACTOS": {"permitir_redescoberta": "false", "ativa": "false"},
        "MUNDO": {"timezone": "Europe/Paris"},
    })
    for section, keys in overrides.items():
        if not cfg.has_section(section):
            cfg.add_section(section)
        for k, v in keys.items():
            cfg.set(section, k, v)
    return cfg


def make_dataset_draw(numero_sorteio, data, timestamp_utc, numeros=None, estrelas=None):
    return {
        "numero_sorteio": numero_sorteio,
        "data": data,
        "horario": {"timestamp_utc": timestamp_utc},
        "chave": {"numeros": numeros or [1, 2, 3, 4, 5], "estrelas": estrelas or [1, 2]},
        "estatisticas_financeiras": {"previsao_1_premio_com_jackpot_eur": None},
        "premios": {"houve_vencedor_1_premio_total": None},
    }


def write_historical_dataset(root, year, filename, draws):
    year_dir = Path(root) / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    (year_dir / filename).write_text(json.dumps({"sorteios": draws}, ensure_ascii=False), encoding="utf-8")


def make_scroll(scroll_id, extracao_data, timestamp_utc, numeros=None, estrelas=None):
    return {
        "id": scroll_id,
        "data": {"extracao": extracao_data, "timestamp_utc": timestamp_utc},
        "extracao": {"numeros": numeros or [1, 2, 3, 4, 5], "estrelas": estrelas or [1, 2]},
        "estatisticas": {"soma": sum(numeros or [1, 2, 3, 4, 5])},
        "astronomia": {"fase_lua": "Lua cheia"},
        "estado": "SELADO",
        "assinatura": {"integridade": "100%"},
    }


def write_scroll(root, year, filename, scroll):
    year_dir = Path(root) / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    (year_dir / filename).write_text(json.dumps(scroll, ensure_ascii=False), encoding="utf-8")


def _patched_runs_dir(tmpdir):
    return mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmpdir))


class _CampaignFixture(unittest.TestCase):
    """Shared synthetic historical_root/scrolls_root with two draws
    strictly before both targets used in these tests.
    """

    def setUp(self):
        self.hist_root = tempfile.TemporaryDirectory()
        self.scrolls_root = tempfile.TemporaryDirectory()
        write_historical_dataset(self.hist_root.name, 2099, "a.json", [
            make_dataset_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5]),
            make_dataset_draw("002/2099", "2099-01-08", "2099-01-08T20:00:00+00:00", numeros=[6, 7, 8, 9, 10]),
        ])
        write_scroll(self.scrolls_root.name, 2099, "001.json", make_scroll("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00"))
        self.addCleanup(self.hist_root.cleanup)
        self.addCleanup(self.scrolls_root.cleanup)

    def run_campaign_isolated(self, cfg, spec):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            return run_campaign(cfg, spec, historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name)


class TestRunCampaignGridShape(_CampaignFixture):
    def test_number_of_runs_equals_targets_times_seeds_times_generations(self):
        spec = CampaignSpec(
            targets=(make_target("T-A/2099"), make_target("T-B/2099")),
            seeds=(1, 2, 3),
            generations=(2, 3),
            mode="verified", relevant_categories=frozenset(),
        )
        results = self.run_campaign_isolated(make_minimal_cfg(), spec)
        self.assertEqual(len(results), 2 * 3 * 2)

    def test_run_ids_are_all_distinct(self):
        spec = CampaignSpec(
            targets=(make_target(),), seeds=(1, 2), generations=(2, 3),
            mode="verified", relevant_categories=frozenset(),
        )
        results = self.run_campaign_isolated(make_minimal_cfg(), spec)
        run_ids = [r.run.run_id for r in results]
        self.assertEqual(len(run_ids), len(set(run_ids)))

    def test_order_is_targets_then_seeds_then_generations(self):
        target_a, target_b = make_target("T-A/2099"), make_target("T-B/2099")
        spec = CampaignSpec(
            targets=(target_a, target_b), seeds=(10, 20), generations=(2, 3),
            mode="verified", relevant_categories=frozenset(),
        )
        results = self.run_campaign_isolated(make_minimal_cfg(), spec)
        coords = [(r.target.draw_id, r.seed, r.generations) for r in results]
        expected = [
            ("T-A/2099", 10, 2), ("T-A/2099", 10, 3),
            ("T-A/2099", 20, 2), ("T-A/2099", 20, 3),
            ("T-B/2099", 10, 2), ("T-B/2099", 10, 3),
            ("T-B/2099", 20, 2), ("T-B/2099", 20, 3),
        ]
        self.assertEqual(coords, expected)

    def test_g20_and_g_larger_are_never_related_by_truncation(self):
        spec_short = CampaignSpec(targets=(make_target(),), seeds=(5,), generations=(2,), mode="verified", relevant_categories=frozenset())
        spec_long = CampaignSpec(targets=(make_target(),), seeds=(5,), generations=(5,), mode="verified", relevant_categories=frozenset())
        results_short = self.run_campaign_isolated(make_minimal_cfg(), spec_short)
        results_long = self.run_campaign_isolated(make_minimal_cfg(), spec_long)
        self.assertNotEqual(results_short[0].run.run_id, results_long[0].run.run_id)
        gens_short = {c.candidate.generation for c in results_short[0].candidates}
        gens_long = {c.candidate.generation for c in results_long[0].candidates}
        self.assertTrue(gens_long - gens_short)


class TestRunCampaignDeterminism(_CampaignFixture):
    def _strip(self, results):
        out = []
        for r in results:
            for c, e in zip(r.candidates, r.evaluations):
                out.append((
                    c.candidate.race, c.candidate.generation, c.candidate.numeros, c.candidate.estrelas,
                    e.category, e.matched_numbers, e.matched_stars,
                ))
        return out

    def test_same_spec_same_seed_gives_same_candidates_and_evaluations(self):
        spec = CampaignSpec(targets=(make_target(),), seeds=(777,), generations=(3,), mode="verified", relevant_categories=frozenset())
        results1 = self.run_campaign_isolated(make_minimal_cfg(), spec)
        results2 = self.run_campaign_isolated(make_minimal_cfg(), spec)
        self.assertEqual(self._strip(results1), self._strip(results2))

    def test_changing_target_key_never_changes_pre_reveal_generation(self):
        target_a = make_target(draw_id="T-X/2099", numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        target_b = make_target(draw_id="T-X/2099", numeros=(46, 47, 48, 49, 50), estrelas=(11, 12))
        spec_a = CampaignSpec(targets=(target_a,), seeds=(42,), generations=(3,), mode="verified", relevant_categories=frozenset())
        spec_b = CampaignSpec(targets=(target_b,), seeds=(42,), generations=(3,), mode="verified", relevant_categories=frozenset())
        results_a = self.run_campaign_isolated(make_minimal_cfg(), spec_a)
        results_b = self.run_campaign_isolated(make_minimal_cfg(), spec_b)
        candidates_a = [(c.candidate.race, c.candidate.numeros, c.candidate.estrelas) for c in results_a[0].candidates]
        candidates_b = [(c.candidate.race, c.candidate.numeros, c.candidate.estrelas) for c in results_b[0].candidates]
        self.assertEqual(candidates_a, candidates_b)


class TestNoLiveApiOrBuilder(_CampaignFixture):
    def test_never_calls_get_history_or_builder(self):
        spec = CampaignSpec(targets=(make_target(),), seeds=(1,), generations=(2,), mode="verified", relevant_categories=frozenset())
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
                 mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")):
                results = run_campaign(make_minimal_cfg(), spec, historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name)
        self.assertTrue(results[0].candidates)

    def test_verified_mode_rejects_uncertified_memory_cfg(self):
        spec = CampaignSpec(targets=(make_target(),), seeds=(1,), generations=(2,), mode="verified", relevant_categories=frozenset())
        cfg = make_minimal_cfg(ARTEFACTOS_VIVOS={"ativo": "true"})
        with self.assertRaises(ValueError):
            self.run_campaign_isolated(cfg, spec)


# ---------------------------------------------------------------------------
# Race aggregation — built directly over synthetic CampaignRunResult objects,
# never via a real run_campaign() call, so races (including races that don't
# exist anywhere in the real project) can be injected freely.
# ---------------------------------------------------------------------------

def make_candidate_key(race, generation=1, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2), entity_id="H-1"):
    return CandidateKey(
        source_type="evolutionary_individual", source_name="racas_antigas",
        numeros=numeros, estrelas=estrelas, generation=generation,
        entity_id=entity_id, entity_name=entity_id, race=race,
        metadata=MappingProxyType({}),
    )


def make_sim_candidate(race, generation=1, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2), entity_id="H-1", run_id="RUN-X"):
    return SimulatedBacktestCandidate(
        candidate=make_candidate_key(race, generation, numeros, estrelas, entity_id),
        temporal_basis="historical_input_boundary", run_id=run_id,
    )


def make_evaluation(target_numeros, target_estrelas, candidate_numeros, candidate_estrelas):
    matched_n = tuple(sorted(set(candidate_numeros) & set(target_numeros)))
    matched_e = tuple(sorted(set(candidate_estrelas) & set(target_estrelas)))
    return CandidateEvaluation(
        matched_numbers=matched_n, matched_stars=matched_e,
        matched_number_count=len(matched_n), matched_star_count=len(matched_e),
        category=f"{len(matched_n)}+{len(matched_e)}",
    )


def make_run_result(target, generations, race_numeros_pairs):
    """race_numeros_pairs: list of (race, generation, numeros, estrelas)."""
    candidates = tuple(
        make_sim_candidate(race, generation, numeros, estrelas, entity_id=f"H-{i}")
        for i, (race, generation, numeros, estrelas) in enumerate(race_numeros_pairs)
    )
    evaluations = tuple(
        make_evaluation(target.numeros, target.estrelas, c.candidate.numeros, c.candidate.estrelas)
        for c in candidates
    )
    return CampaignRunResult(
        target=target, seed=1, generations=generations,
        run=None, candidates=candidates, evaluations=evaluations,
    )


class TestSummarizeByRaceDynamicDiscovery(unittest.TestCase):
    def test_synthetic_races_never_seen_in_the_real_project_appear_automatically(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Cyber-Anão", 1, (1, 2, 3, 4, 5), (1, 2)),
            ("Superesqueleto Experimental", 2, (1, 2, 6, 7, 8), (1, 9)),
        ])
        summary = summarize_by_race([result], relevant_categories=("5+2",))
        self.assertIn("Cyber-Anão", summary)
        self.assertIn("Superesqueleto Experimental", summary)
        self.assertEqual(summary["Cyber-Anão"].total_keys, 1)
        self.assertEqual(summary["Cyber-Anão"].best_category_observed, "5+2")

    def test_renascido_prefix_is_never_merged_with_base_race(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 3, 4, 5), (1, 2)),
            ("Renascido Elfo", 2, (1, 2, 3, 6, 7), (1, 9)),
        ])
        summary = summarize_by_race([result], relevant_categories=())
        self.assertIn("Elfo", summary)
        self.assertIn("Renascido Elfo", summary)
        self.assertEqual(summary["Elfo"].total_keys, 1)
        self.assertEqual(summary["Renascido Elfo"].total_keys, 1)

    def test_race_none_is_grouped_under_none_never_fabricated(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            (None, None, (1, 2, 3, 4, 5), (1, 2)),
        ])
        summary = summarize_by_race([result], relevant_categories=())
        self.assertIn(None, summary)
        self.assertEqual(summary[None].race, None)

    def test_race_absent_from_results_never_appears_with_fake_zeros(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 3, 4, 5), (1, 2)),
        ])
        summary = summarize_by_race([result], relevant_categories=())
        self.assertNotIn("Zombie", summary)
        self.assertNotIn("Minotauro", summary)
        self.assertEqual(set(summary.keys()), {"Elfo"})


class TestSummarizeByRaceMetrics(unittest.TestCase):
    def test_pools_exactly_the_individual_candidate_count(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 3, 4, 5), (1, 2)),
            ("Elfo", 2, (10, 11, 12, 13, 14), (5, 6)),
            ("Bruxa", 1, (1, 2, 3, 4, 5), (1, 2)),
        ])
        summary = summarize_by_race([result], relevant_categories=())
        total_pooled = sum(s.total_keys for s in summary.values())
        self.assertEqual(total_pooled, len(result.candidates))
        self.assertEqual(summary["Elfo"].total_keys, 2)
        self.assertEqual(summary["Bruxa"].total_keys, 1)

    def test_duplicate_keys_never_inflate_unique_count(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 3, 4, 5), (1, 2)),
            ("Elfo", 2, (1, 2, 3, 4, 5), (1, 2)),  # identical key
            ("Elfo", 3, (10, 11, 12, 13, 14), (5, 6)),
        ])
        summary = summarize_by_race([result], relevant_categories=())
        self.assertEqual(summary["Elfo"].total_keys, 3)
        self.assertEqual(summary["Elfo"].unique_keys, 2)
        self.assertAlmostEqual(summary["Elfo"].repeat_rate, 1 / 3)

    def test_matched_numbers_and_stars_counted_separately(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 3, 40, 41), (1, 11)),  # 3 numbers, 1 star
        ])
        summary = summarize_by_race([result], relevant_categories=())
        self.assertEqual(summary["Elfo"].avg_matched_numbers, 3.0)
        self.assertEqual(summary["Elfo"].avg_matched_stars, 1.0)
        self.assertEqual(summary["Elfo"].avg_matched_total, 4.0)
        self.assertEqual(summary["Elfo"].category_counts["3+1"], 1)

    def test_averages_normalize_by_total_keys_not_raw_counts(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        small_race = make_run_result(target, 20, [("Rare", 1, (1, 2, 3, 4, 5), (1, 2))])  # 1 candidate, 5+2
        big_race = make_run_result(target, 20, [
            ("Common", i, (10, 11, 12, 13, 14), (5, 6)) for i in range(1, 11)  # 10 candidates, 0+0 each
        ])
        summary = summarize_by_race([small_race, big_race], relevant_categories=())
        self.assertEqual(summary["Rare"].avg_matched_total, 7.0)
        self.assertEqual(summary["Common"].avg_matched_total, 0.0)

    def test_best_category_observed_is_lexicographic_max_of_numbers_then_stars(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 40, 41, 42), (1, 2)),   # 2+2
            ("Elfo", 5, (1, 2, 3, 40, 41), (11, 12)),  # 3+0 -- more numbers wins over more stars
        ])
        summary = summarize_by_race([result], relevant_categories=())
        self.assertEqual(summary["Elfo"].best_category_observed, "3+0")
        self.assertEqual(summary["Elfo"].best_category_generation, 5)

    def test_relevant_count_and_rate_use_caller_supplied_categories(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[
            ("Elfo", 1, (1, 2, 3, 4, 5), (1, 2)),        # 5+2
            ("Elfo", 2, (10, 11, 12, 13, 14), (5, 6)),   # 0+0
        ])
        strict = summarize_by_race([result], relevant_categories=("5+2",))
        loose = summarize_by_race([result], relevant_categories=("5+2", "0+0"))
        self.assertEqual(strict["Elfo"].relevant_count, 1)
        self.assertAlmostEqual(strict["Elfo"].relevant_rate, 0.5)
        self.assertEqual(loose["Elfo"].relevant_count, 2)
        self.assertAlmostEqual(loose["Elfo"].relevant_rate, 1.0)

    def test_targets_observed_and_targets_with_relevant_key(self):
        target_a = make_target(draw_id="T-A/2099", numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        target_b = make_target(draw_id="T-B/2099", numeros=(46, 47, 48, 49, 50), estrelas=(11, 12))
        result_a = make_run_result(target_a, 20, [("Elfo", 1, (1, 2, 3, 4, 5), (1, 2))])   # 5+2 vs target_a
        result_b = make_run_result(target_b, 20, [("Elfo", 1, (1, 2, 3, 4, 5), (1, 2))])   # 0+0 vs target_b
        summary = summarize_by_race([result_a, result_b], relevant_categories=("5+2",))
        self.assertEqual(summary["Elfo"].targets_observed, 2)
        self.assertEqual(summary["Elfo"].targets_with_relevant_key, 1)


class TestSummarizeByRaceAndGenerations(unittest.TestCase):
    def test_groups_by_race_and_campaign_generations_axis(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result_g20 = make_run_result(target, generations=20, race_numeros_pairs=[("Elfo", 5, (1, 2, 3, 4, 5), (1, 2))])
        result_g100 = make_run_result(target, generations=100, race_numeros_pairs=[("Elfo", 90, (10, 11, 12, 13, 14), (5, 6))])
        summary = summarize_by_race_and_generations([result_g20, result_g100], relevant_categories=())
        self.assertIn(("Elfo", 20), summary)
        self.assertIn(("Elfo", 100), summary)
        self.assertEqual(summary[("Elfo", 20)].total_keys, 1)
        self.assertEqual(summary[("Elfo", 100)].total_keys, 1)

    def test_never_conflates_campaign_generations_with_individual_generation(self):
        # individual CandidateKey.generation (90) is deliberately far from
        # the campaign axis value (20) to make any accidental conflation
        # produce an obviously wrong key.
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        result = make_run_result(target, generations=20, race_numeros_pairs=[("Elfo", 90, (1, 2, 3, 4, 5), (1, 2))])
        summary = summarize_by_race_and_generations([result], relevant_categories=())
        self.assertIn(("Elfo", 20), summary)
        self.assertNotIn(("Elfo", 90), summary)
        self.assertEqual(summary[("Elfo", 20)].best_category_generation, 90)


# ---------------------------------------------------------------------------
# Campaign Runner V2 — multi-system campaigns (run_system_campaign(),
# MultiSystemCampaignSpec, GeneratorRunResult, summarize_by_system_*()).
# Everything above this line covers Commit 27 exactly as before — these
# classes are purely additive.
# ---------------------------------------------------------------------------


def make_v2_cfg(**overrides):
    return make_minimal_cfg(
        ESQUELETOS={"ativos": "true", "quantidade_externa": "3", "largura_numeros": "25", "largura_estrelas": "6"},
        MELFORKS={"ativo": "true", "populacao_chaves": "10", "geracoes_chaves": "3", "elite": "3", "representantes": "3"},
        AXIOMANTES={
            "peso_conselho": "0.75", "periodo_anos": "1", "limiar_cobertura": "0.0",
            "excesso_minimo": "-1.0", "n_candidatos": "50", "guardar_experiencia": "true",
        },
        **overrides,
    )


class _MultiSystemFixture(_CampaignFixture):
    def run_system_campaign_isolated(self, cfg, spec):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            return run_system_campaign(cfg, spec, historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name)


class TestRunSystemCampaignGridShape(_MultiSystemFixture):
    def test_grid_size_is_honest_about_generations_axis(self):
        spec = MultiSystemCampaignSpec(
            targets=(make_target(),), seeds=(1,), systems=("clerics", "skeletons"),
            generations=(3, 4), mode="verified", relevant_categories=frozenset(),
        )
        results = self.run_system_campaign_isolated(make_v2_cfg(), spec)
        # 2 clerics cells (one per generations value) + 1 skeletons cell
        # (no generations axis) = 3, never a fake 2x2=4 cross product.
        self.assertEqual(len(results), 3)
        clerics_results = [r for r in results if r.system == "clerics"]
        skeletons_results = [r for r in results if r.system == "skeletons"]
        self.assertEqual(len(clerics_results), 2)
        self.assertEqual(len(skeletons_results), 1)
        self.assertEqual({r.generations for r in clerics_results}, {3, 4})
        self.assertEqual({r.generations for r in skeletons_results}, {None})

    def test_systems_without_generations_axis_run_exactly_once_per_target_seed(self):
        spec = MultiSystemCampaignSpec(
            targets=(make_target("T-A/2099"), make_target("T-B/2099")), seeds=(1, 2),
            systems=("skeletons", "melforks", "axiomantes", "pantheon"),
            generations=(), mode="verified", relevant_categories=frozenset(),
        )
        results = self.run_system_campaign_isolated(make_v2_cfg(), spec)
        self.assertEqual(len(results), 4 * 2 * 2)  # 4 systems x 2 targets x 2 seeds
        self.assertTrue(all(r.generations is None for r in results if r.system != "melforks"))

    def test_unknown_system_raises_value_error(self):
        spec = MultiSystemCampaignSpec(
            targets=(make_target(),), seeds=(1,), systems=("cyber_anoes",),
            generations=(), mode="verified", relevant_categories=frozenset(),
        )
        with self.assertRaises(ValueError):
            self.run_system_campaign_isolated(make_v2_cfg(), spec)

    def test_generations_axis_system_with_empty_generations_raises_value_error(self):
        spec = MultiSystemCampaignSpec(
            targets=(make_target(),), seeds=(1,), systems=("clerics",),
            generations=(), mode="verified", relevant_categories=frozenset(),
        )
        with self.assertRaises(ValueError):
            self.run_system_campaign_isolated(make_v2_cfg(), spec)


class TestRunSystemCampaignDeterminism(_MultiSystemFixture):
    def test_same_spec_same_seed_gives_same_results(self):
        spec = MultiSystemCampaignSpec(
            targets=(make_target(),), seeds=(777,), systems=("clerics", "skeletons", "melforks", "axiomantes", "pantheon"),
            generations=(3,), mode="verified", relevant_categories=frozenset(),
        )
        cfg = make_v2_cfg()
        results1 = self.run_system_campaign_isolated(cfg, spec)
        results2 = self.run_system_campaign_isolated(cfg, spec)
        strip = lambda results: [
            (r.system, r.generations, [(c.candidate.race, c.candidate.numeros, c.candidate.estrelas) for c in r.candidates])
            for r in results
        ]
        self.assertEqual(strip(results1), strip(results2))


class TestRunSystemCampaignVerifiedGate(_MultiSystemFixture):
    def test_verified_mode_rejects_uncertified_memory_cfg(self):
        cfg = make_v2_cfg(ARTEFACTOS_VIVOS={"ativo": "true"})
        spec = MultiSystemCampaignSpec(
            targets=(make_target(),), seeds=(1,), systems=("clerics", "skeletons"),
            generations=(3,), mode="verified", relevant_categories=frozenset(),
        )
        with self.assertRaises(ValueError):
            self.run_system_campaign_isolated(cfg, spec)


class TestRunSystemCampaignPantheonGranularity(_MultiSystemFixture):
    def test_pantheon_produces_four_distinguishable_races_in_one_campaign(self):
        spec = MultiSystemCampaignSpec(
            targets=(make_target(),), seeds=(1,), systems=("pantheon",),
            generations=(), mode="verified", relevant_categories=frozenset(),
        )
        results = self.run_system_campaign_isolated(make_v2_cfg(), spec)
        races = {c.candidate.race for r in results for c in r.candidates}
        self.assertEqual(races, {"Mago", "Druida", "Djinn", "Aion"})

        summary = summarize_by_system_and_strategy(results, frozenset())
        self.assertEqual(
            {key for key in summary if key[0] == "pantheon"},
            {("pantheon", "Mago"), ("pantheon", "Druida"), ("pantheon", "Djinn"), ("pantheon", "Aion")},
        )


class TestSummarizeBySystemAndStrategyDynamicDiscovery(unittest.TestCase):
    """Built directly over synthetic GeneratorRunResult objects — never
    via a real run_system_campaign() call — so a system that does not
    exist in the real GENERATORS registry can be injected freely,
    proving the aggregator never enumerates systems or strategies.
    """

    def test_a_system_never_registered_in_generators_is_still_aggregated(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        candidate = make_sim_candidate("Cyber-Anão", generation=None, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        evaluation = make_evaluation(target.numeros, target.estrelas, candidate.candidate.numeros, candidate.candidate.estrelas)
        result = GeneratorRunResult(
            system="cyber_anoes", target=target, seed=1, generations=None, run_id="RUN-X",
            candidates=(candidate,), evaluations=(evaluation,), performance=None,
        )
        summary = summarize_by_system_and_strategy([result], relevant_categories=frozenset())
        self.assertIn(("cyber_anoes", "Cyber-Anão"), summary)
        self.assertNotIn("cyber_anoes", GENERATORS)

    def test_summarize_by_system_strategy_and_generations_handles_none_generations(self):
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        candidate = make_sim_candidate("Esqueleto", generation=None, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        evaluation = make_evaluation(target.numeros, target.estrelas, candidate.candidate.numeros, candidate.candidate.estrelas)
        result = GeneratorRunResult(
            system="skeletons", target=target, seed=1, generations=None, run_id="RUN-X",
            candidates=(candidate,), evaluations=(evaluation,), performance=None,
        )
        summary = summarize_by_system_strategy_and_generations([result], relevant_categories=frozenset())
        self.assertIn(("skeletons", "Esqueleto", None), summary)


if __name__ == "__main__":
    unittest.main()
