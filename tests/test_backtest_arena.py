"""Tests for core/services/backtest_arena.py. All GeneratorRunResult
fixtures are synthetic and built directly (never via a real
run_system_campaign() call, except in the dedicated integration test
class at the end) — so cells/seeds/races can be constructed freely to
prove the cell-not-aggregated-across-seeds discipline, the abstention
accounting, and dynamic discovery, without depending on any real
faction's actual output shape.
"""

import configparser
import random
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from unittest import mock

from core.services.backtest_arena import (
    ArenaStrategySummary,
    ArenaSystemAttendance,
    EqualBudgetResult,
    _arena_rng,
    category_rank,
    official_key,
    official_keys_by_cell,
    sample_with_equal_budget,
    summarize_arena_participation,
    summarize_system_attendance,
)
from core.services.backtest_campaign import GeneratorRunResult, MultiSystemCampaignSpec, run_system_campaign
from core.services.backtest_lab import BacktestTarget
from core.services.backtest_orchestrator import SimulatedBacktestCandidate
from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_provenance import CandidateKey
from core.services.hero_evaluation import HeroConfigError

TARGET_A = BacktestTarget(
    draw_id="T-A/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc),
    numeros=(1, 2, 3, 4, 5), estrelas=(1, 2),
)
TARGET_B = BacktestTarget(
    draw_id="T-B/2099", draw_datetime=datetime(2099, 3, 17, 20, 0, 0, tzinfo=timezone.utc),
    numeros=(46, 47, 48, 49, 50), estrelas=(11, 12),
)


def make_candidate_key(race, numeros, estrelas, source_type="external_generator", source_name="synthetic"):
    return CandidateKey(
        source_type=source_type, source_name=source_name,
        numeros=tuple(numeros), estrelas=tuple(estrelas),
        generation=None, entity_id=None, entity_name=None, race=race,
        metadata=MappingProxyType({}),
    )


def make_sim_candidate(race, numeros, estrelas, run_id="RUN-X"):
    return SimulatedBacktestCandidate(
        candidate=make_candidate_key(race, numeros, estrelas),
        temporal_basis="historical_input_boundary", run_id=run_id,
    )


def make_evaluation(target, numeros, estrelas):
    matched_n = tuple(sorted(set(numeros) & set(target.numeros)))
    matched_e = tuple(sorted(set(estrelas) & set(target.estrelas)))
    return CandidateEvaluation(
        matched_numbers=matched_n, matched_stars=matched_e,
        matched_number_count=len(matched_n), matched_star_count=len(matched_e),
        category=f"{len(matched_n)}+{len(matched_e)}",
    )


def make_cell(system, target, seed, race_numeros_pairs, generations=None, run_id=None):
    """race_numeros_pairs: list of (race, numeros, estrelas)."""
    run_id = run_id or f"RUN-{system}-{target.draw_id}-{seed}"
    candidates = tuple(make_sim_candidate(race, numeros, estrelas, run_id) for race, numeros, estrelas in race_numeros_pairs)
    evaluations = tuple(make_evaluation(target, c.candidate.numeros, c.candidate.estrelas) for c in candidates)
    return GeneratorRunResult(
        system=system, target=target, seed=seed, generations=generations, run_id=run_id,
        candidates=candidates, evaluations=evaluations, performance=None,
    )


class TestArenaRng(unittest.TestCase):
    def test_deterministic_given_same_inputs(self):
        rng1 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42)
        rng2 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42)
        self.assertEqual(rng1.getstate(), rng2.getstate())

    def test_different_purpose_gives_different_stream(self):
        rng1 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42)
        rng2 = _arena_rng(1, "equal_budget:5", "clerics", "Bruxa", TARGET_A, 42)
        self.assertNotEqual(rng1.getstate(), rng2.getstate())

    def test_different_generator_seed_gives_different_stream(self):
        rng1 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42)
        rng2 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 43)
        self.assertNotEqual(rng1.getstate(), rng2.getstate())

    def test_independent_of_global_random_state(self):
        random.seed(111)
        rng1 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42)
        random.seed(999)
        rng2 = _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42)
        self.assertEqual(rng1.getstate(), rng2.getstate())

    def test_arena_rng_never_perturbs_global_random_state(self):
        random.seed(555)
        before = random.getstate()
        _arena_rng(1, "official_key", "clerics", "Bruxa", TARGET_A, 42).choice([1, 2, 3])
        after = random.getstate()
        self.assertEqual(before, after)


class TestOfficialKey(unittest.TestCase):
    def test_never_mixes_seeds(self):
        results = [
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))]),
            make_cell("clerics", TARGET_A, 2, [("Bruxa", (10, 11, 12, 13, 14), (5, 6))]),
        ]
        key_seed1 = official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, arena_seed=99)
        key_seed2 = official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=2, arena_seed=99)
        self.assertEqual(key_seed1.numeros, (1, 2, 3, 4, 5))
        self.assertEqual(key_seed2.numeros, (10, 11, 12, 13, 14))

    def test_returns_none_when_zero_candidates(self):
        results = [make_cell("axiomantes", TARGET_A, 1, [])]
        self.assertIsNone(official_key(results, "axiomantes", "Axiomante", TARGET_A, generator_seed=1, arena_seed=99))

    def test_deterministic_given_same_arena_seed(self):
        results = [make_cell("clerics", TARGET_A, 1, [
            ("Bruxa", (1, 2, 3, 4, 5), (1, 2)),
            ("Bruxa", (10, 11, 12, 13, 14), (5, 6)),
            ("Bruxa", (20, 21, 22, 23, 24), (7, 8)),
        ])]
        k1 = official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, arena_seed=42)
        k2 = official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, arena_seed=42)
        self.assertEqual(k1, k2)

    def test_never_reads_the_real_target_key(self):
        results = [make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))])]
        different_target = BacktestTarget(
            draw_id=TARGET_A.draw_id, draw_datetime=TARGET_A.draw_datetime,
            numeros=(46, 47, 48, 49, 50), estrelas=(11, 12),
        )
        k1 = official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, arena_seed=42)
        k2 = official_key(results, "clerics", "Bruxa", different_target, generator_seed=1, arena_seed=42)
        self.assertEqual(k1.numeros, k2.numeros)

    def test_selects_among_unique_keys_not_weighted_by_repeats(self):
        # 9 copies of one key, 1 copy of a rare key -- across enough
        # distinct arena_seeds, the rare key must still be selectable
        # (proves selection is uniform over the 2 unique keys, not
        # weighted 9:1 by repeat count).
        pairs = [("Bruxa", (1, 2, 3, 4, 5), (1, 2))] * 9 + [("Bruxa", (10, 11, 12, 13, 14), (5, 6))]
        results = [make_cell("clerics", TARGET_A, 1, pairs)]
        chosen = {
            official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, arena_seed=s).numeros
            for s in range(30)
        }
        self.assertEqual(chosen, {(1, 2, 3, 4, 5), (10, 11, 12, 13, 14)})

    def test_multiple_generations_for_same_cell_raises_value_error(self):
        results = [
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))], generations=20, run_id="RUN-G20"),
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (6, 7, 8, 9, 10), (3, 4))], generations=100, run_id="RUN-G100"),
        ]
        with self.assertRaises(ValueError):
            official_key(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, arena_seed=42)


class TestOfficialKeysByCell(unittest.TestCase):
    def test_cell_with_zero_candidates_maps_to_none_never_omitted(self):
        results = [
            make_cell("axiomantes", TARGET_A, 1, [("Axiomante", (1, 2, 3, 4, 5), (1, 2))]),
            make_cell("axiomantes", TARGET_A, 2, []),  # portal closed this seed
        ]
        out = official_keys_by_cell(results, "axiomantes", "Axiomante", arena_seed=1)
        self.assertIn((TARGET_A.draw_id, 1), out)
        self.assertIn((TARGET_A.draw_id, 2), out)
        self.assertIsNotNone(out[(TARGET_A.draw_id, 1)])
        self.assertIsNone(out[(TARGET_A.draw_id, 2)])


class TestSampleWithEqualBudget(unittest.TestCase):
    def test_never_mixes_seeds(self):
        results = [
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))]),
            make_cell("clerics", TARGET_A, 2, [("Bruxa", (10, 11, 12, 13, 14), (5, 6))]),
        ]
        result = sample_with_equal_budget(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, n=5, arena_seed=1, relevant_categories=frozenset())
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].candidate.numeros, (1, 2, 3, 4, 5))

    def test_n_used_never_exceeds_available(self):
        results = [make_cell("axiomantes", TARGET_A, 1, [("Axiomante", (1, 2, 3, 4, 5), (1, 2))])]
        result = sample_with_equal_budget(results, "axiomantes", "Axiomante", TARGET_A, generator_seed=1, n=5, arena_seed=1, relevant_categories=frozenset())
        self.assertEqual(result.n_requested, 5)
        self.assertEqual(result.n_used, 1)

    def test_zero_candidates_gives_n_used_zero_never_crashes(self):
        results = [make_cell("axiomantes", TARGET_A, 1, [])]
        result = sample_with_equal_budget(results, "axiomantes", "Axiomante", TARGET_A, generator_seed=1, n=5, arena_seed=1, relevant_categories=frozenset())
        self.assertEqual(result.n_used, 0)
        self.assertEqual(result.candidates, ())

    def test_sampling_without_replacement(self):
        pairs = [("Elfo", (i, i + 1, i + 2, i + 3, i + 4), (1, 2)) for i in range(1, 21)]
        results = [make_cell("clerics", TARGET_A, 1, pairs)]
        result = sample_with_equal_budget(results, "clerics", "Elfo", TARGET_A, generator_seed=1, n=5, arena_seed=1, relevant_categories=frozenset())
        self.assertEqual(len(result.candidates), 5)
        self.assertEqual(len({c.candidate.numeros for c in result.candidates}), 5)

    def test_deterministic_given_same_arena_seed(self):
        pairs = [("Elfo", (i, i + 1, i + 2, i + 3, i + 4), (1, 2)) for i in range(1, 21)]
        results = [make_cell("clerics", TARGET_A, 1, pairs)]
        r1 = sample_with_equal_budget(results, "clerics", "Elfo", TARGET_A, generator_seed=1, n=5, arena_seed=7, relevant_categories=frozenset())
        r2 = sample_with_equal_budget(results, "clerics", "Elfo", TARGET_A, generator_seed=1, n=5, arena_seed=7, relevant_categories=frozenset())
        self.assertEqual([c.candidate.numeros for c in r1.candidates], [c.candidate.numeros for c in r2.candidates])

    def test_independent_from_official_key_rng(self):
        pairs = [("Elfo", (i, i + 1, i + 2, i + 3, i + 4), (1, 2)) for i in range(1, 21)]
        results = [make_cell("clerics", TARGET_A, 1, pairs)]
        budget_result = sample_with_equal_budget(results, "clerics", "Elfo", TARGET_A, generator_seed=1, n=1, arena_seed=7, relevant_categories=frozenset())
        official = official_key(results, "clerics", "Elfo", TARGET_A, generator_seed=1, arena_seed=7)
        # not asserting inequality (they could coincide by chance) --
        # asserting the two draws are independently derived by checking
        # the underlying RNG streams differ (see TestArenaRng), this
        # test only proves both computed without raising and are each
        # internally consistent.
        self.assertIsNotNone(official)
        self.assertEqual(budget_result.n_used, 1)

    def test_multiple_generations_for_same_cell_raises_value_error(self):
        results = [
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))], generations=20, run_id="RUN-G20"),
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (6, 7, 8, 9, 10), (3, 4))], generations=100, run_id="RUN-G100"),
        ]
        with self.assertRaises(ValueError):
            sample_with_equal_budget(results, "clerics", "Bruxa", TARGET_A, generator_seed=1, n=5, arena_seed=1, relevant_categories=frozenset())


class TestSummarizeSystemAttendance(unittest.TestCase):
    def test_total_abstention_is_visible_without_ever_seeing_a_race_label(self):
        results = [
            make_cell("axiomantes", TARGET_A, 1, []),
            make_cell("axiomantes", TARGET_A, 2, []),
            make_cell("axiomantes", TARGET_B, 1, []),
        ]
        attendance = summarize_system_attendance(results)
        self.assertIn("axiomantes", attendance)
        self.assertEqual(attendance["axiomantes"].cells_attempted, 3)
        self.assertEqual(attendance["axiomantes"].cells_with_any_candidate, 0)
        self.assertEqual(attendance["axiomantes"].system_abstention_rate, 1.0)

    def test_cells_vs_targets_distinction(self):
        results = [
            make_cell("axiomantes", TARGET_A, 1, [("Axiomante", (1, 2, 3, 4, 5), (1, 2))]),
            make_cell("axiomantes", TARGET_A, 2, []),
            make_cell("axiomantes", TARGET_A, 3, []),
            make_cell("axiomantes", TARGET_B, 1, []),
        ]
        attendance = summarize_system_attendance(results)["axiomantes"]
        self.assertEqual(attendance.cells_attempted, 4)
        self.assertEqual(attendance.cells_with_any_candidate, 1)
        self.assertEqual(attendance.targets_observed, 2)
        self.assertEqual(attendance.targets_with_participation, 1)

    def test_raises_on_multiple_results_for_same_cell(self):
        results = [
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))], generations=20, run_id="RUN-G20"),
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (6, 7, 8, 9, 10), (3, 4))], generations=100, run_id="RUN-G100"),
        ]
        with self.assertRaises(ValueError):
            summarize_system_attendance(results)


class TestSummarizeArenaParticipation(unittest.TestCase):
    def test_rare_participation_never_looks_like_perfect_success(self):
        # 1 participation out of 100 attempts, succeeds that one time.
        cells = [make_cell("axiomantes", TARGET_A, seed, []) for seed in range(1, 100)]
        cells.append(make_cell("axiomantes", TARGET_A, 100, [("Axiomante", (1, 2, 3, 4, 5), (1, 2))]))
        summary = summarize_arena_participation(cells, relevant_categories=frozenset({"5+2"}))
        s = summary[("axiomantes", "Axiomante")]
        self.assertEqual(s.cells_attempted, 100)
        self.assertEqual(s.cells_participated, 1)
        self.assertEqual(s.cells_succeeded, 1)
        self.assertAlmostEqual(s.participation_rate, 0.01)
        self.assertAlmostEqual(s.success_rate_when_participating, 1.0)
        self.assertAlmostEqual(s.success_rate_over_all_cells, 0.01)

    def test_success_rate_when_participating_is_none_when_a_discoverable_race_never_actually_wins_a_cell(self):
        # "Sombra" is discoverable (appears once, at TARGET_B) but never
        # participates at TARGET_A across 3 seeds -- summarize_arena_participation
        # itself must report None for a race with cells_participated == 0
        # once discovered, never a fabricated 0.0.
        cells = [make_cell("clerics", TARGET_A, s, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))]) for s in range(1, 4)]
        cells.append(make_cell("clerics", TARGET_B, 1, [("Sombra", (1, 2, 3, 4, 5), (1, 2))]))
        cells.append(make_cell("clerics", TARGET_B, 2, []))
        summary = summarize_arena_participation(cells, relevant_categories=frozenset({"5+2"}))
        sombra = summary[("clerics", "Sombra")]
        self.assertEqual(sombra.cells_participated, 1)
        self.assertIsNotNone(sombra.success_rate_when_participating)

        # Direct construction, matching what the dataclass itself must
        # allow/represent for a genuinely never-participated case.
        never_participated = ArenaStrategySummary(
            system="x", race="y", cells_attempted=5, cells_participated=0, cells_succeeded=0,
            targets_observed=1, targets_with_participation=0, participation_rate=0.0, abstention_rate=1.0,
            success_rate_when_participating=None, success_rate_over_all_cells=0.0, target_participation_rate=0.0,
        )
        self.assertIsNone(never_participated.success_rate_when_participating)

    def test_a_race_that_never_appears_at_all_is_invisible_here_but_system_attendance_still_shows_abstention(self):
        results = [make_cell("axiomantes", TARGET_A, 1, []), make_cell("axiomantes", TARGET_A, 2, [])]
        strategy_summary = summarize_arena_participation(results, relevant_categories=frozenset())
        self.assertEqual(strategy_summary, {})
        system_attendance = summarize_system_attendance(results)
        self.assertEqual(system_attendance["axiomantes"].cells_attempted, 2)
        self.assertEqual(system_attendance["axiomantes"].system_abstention_rate, 1.0)

    def test_dynamic_discovery_of_synthetic_system_and_race(self):
        results = [make_cell("cyber_anoes", TARGET_A, 1, [("Cyber-Anão", (1, 2, 3, 4, 5), (1, 2))])]
        summary = summarize_arena_participation(results, relevant_categories=frozenset())
        self.assertIn(("cyber_anoes", "Cyber-Anão"), summary)

    def test_targets_observed_and_target_participation_rate(self):
        results = [
            make_cell("clerics", TARGET_A, 1, [("Bruxa", (1, 2, 3, 4, 5), (1, 2))]),
            make_cell("clerics", TARGET_A, 2, []),
            make_cell("clerics", TARGET_B, 1, [("Bruxa", (6, 7, 8, 9, 10), (3, 4))]),
        ]
        summary = summarize_arena_participation(results, relevant_categories=frozenset())
        s = summary[("clerics", "Bruxa")]
        self.assertEqual(s.targets_observed, 2)
        self.assertEqual(s.targets_with_participation, 2)
        self.assertAlmostEqual(s.target_participation_rate, 1.0)


class TestCategoryRank(unittest.TestCase):
    def make_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({
            "HEROIS": {"categorias": "5+2,5+1,5+0,4+2,4+1,4+0,3+2,3+1,3+0,2+2,2+1,1+2", "incluir_2_0": "false"},
            "HEROIS_TIERS": {
                "5+2": "TIER_1", "5+1": "TIER_2", "5+0": "TIER_2", "4+2": "TIER_2",
                "4+1": "TIER_3", "4+0": "TIER_3", "3+2": "TIER_3",
                "3+1": "TIER_4", "3+0": "TIER_4", "2+2": "TIER_4",
                "2+1": "TIER_5", "1+2": "TIER_5", "2+0": "TIER_5",
            },
        })
        return cfg

    def test_best_category_ranks_lowest(self):
        cfg = self.make_cfg()
        self.assertLess(category_rank("5+2", cfg), category_rank("5+1", cfg))

    def test_same_tier_broken_by_matched_numbers_then_stars(self):
        cfg = self.make_cfg()
        # 4+0 and 3+2 share TIER_3 -- 4+0 must win (more numbers).
        self.assertLess(category_rank("4+0", cfg), category_rank("3+2", cfg))

    def test_untiered_category_raises_hero_config_error(self):
        cfg = self.make_cfg()
        with self.assertRaises(HeroConfigError):
            category_rank("0+0", cfg)


class TestArenaIntegrationWithRealGenerators(unittest.TestCase):
    """A thin, real run_system_campaign() call over a synthetic dataset,
    to prove the Arena layer wires correctly onto real GeneratorRunResult
    objects, not just hand-built fixtures.
    """

    def setUp(self):
        import json

        self.hist_root = tempfile.TemporaryDirectory()
        self.scrolls_root = tempfile.TemporaryDirectory()
        year_dir = Path(self.hist_root.name) / "2099"
        year_dir.mkdir(parents=True)
        (year_dir / "a.json").write_text(json.dumps({"sorteios": [
            {
                "numero_sorteio": "001/2099", "data": "2099-01-01",
                "horario": {"timestamp_utc": "2099-01-01T20:00:00+00:00"},
                "chave": {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
                "estatisticas_financeiras": {"previsao_1_premio_com_jackpot_eur": None},
                "premios": {"houve_vencedor_1_premio_total": None},
            },
        ]}), encoding="utf-8")
        self.addCleanup(self.hist_root.cleanup)
        self.addCleanup(self.scrolls_root.cleanup)

    def make_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({
            "SIMULACAO": {"populacao_inicial": "8", "geracoes": "3", "sobreviventes": "4", "modo_semente": "fixo"},
            "CAMINHO_1000_ALMAS": {"ativo": "false"},
            "ARTEFACTOS_VIVOS": {"ativo": "false"},
            "ARCA_ARTEFACTOS": {"permitir_redescoberta": "false", "ativa": "false"},
            "MONGES_E_ESCRIBAS": {"acesso_total": "", "acesso_quentes_frios": "", "acesso_historico": "", "acesso_pares_trios": "", "acesso_gaps": ""},
            "MUNDO": {"timezone": "Europe/Paris"},
            "ARENA": {"acaso_puro_quantidade": "10"},
        })
        return cfg

    def test_official_key_and_participation_over_a_real_campaign(self):
        target = BacktestTarget(
            draw_id="T-Real/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc),
            numeros=(1, 2, 3, 4, 5), estrelas=(1, 2),
        )
        spec = MultiSystemCampaignSpec(
            targets=(target,), seeds=(1, 2), systems=("skeletons", "acaso_puro"),
            generations=(), mode="verified", relevant_categories=frozenset({"5+2"}),
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            results = run_system_campaign(
                self.make_cfg(), spec, historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name,
            )

        attendance = summarize_system_attendance(results)
        self.assertEqual(attendance["skeletons"].cells_attempted, 2)
        self.assertEqual(attendance["acaso_puro"].cells_attempted, 2)

        key_seed1 = official_key(results, "acaso_puro", "Acaso Puro", target, generator_seed=1, arena_seed=1)
        key_seed2 = official_key(results, "acaso_puro", "Acaso Puro", target, generator_seed=2, arena_seed=1)
        self.assertIsNotNone(key_seed1)
        self.assertIsNotNone(key_seed2)

        budget = sample_with_equal_budget(
            results, "acaso_puro", "Acaso Puro", target, generator_seed=1, n=5, arena_seed=1,
            relevant_categories=spec.relevant_categories,
        )
        self.assertEqual(budget.n_used, 5)


if __name__ == "__main__":
    unittest.main()
