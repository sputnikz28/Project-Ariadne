"""Tests for core/services/backtest_orchestrator.py (Commit 25). All
historical/scroll fixtures are synthetic (tempfile.TemporaryDirectory());
core.services.run_manifest.RUNS_DIR is always patched to a temp
directory so no test here ever writes to the real
datasets/generated/simulations/runs/. No test uses 14/08/2026 or any
other real draw as its target.
"""

import configparser
import inspect
import json
import tempfile
import typing
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from core.services.backtest_lab import BacktestTarget
from core.services.backtest_orchestrator import (
    BacktestRunRecord,
    HistoricalBacktestBoundary,
    SimulatedBacktestCandidate,
    _derive_mundo_cfg,
    _validate_verified_mode,
    freeze_simulated_candidates,
    prepare_backtest_run,
    reveal_and_evaluate,
    run_clerics_backtest,
    summarize,
)
from core.services.candidate_provenance import normalize_candidate_record
from library.ariadne.engine import Ariadne

FUTURE_DRAW_DT = datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc)


def make_boundary(draw_id="T-001/2099", draw_datetime=FUTURE_DRAW_DT):
    return HistoricalBacktestBoundary(draw_id=draw_id, draw_datetime=draw_datetime)


def make_target(draw_id="T-001/2099", draw_datetime=FUTURE_DRAW_DT, numeros=(1, 2, 3, 4, 5), estrelas=(1, 2)):
    return BacktestTarget(draw_id=draw_id, draw_datetime=draw_datetime, numeros=numeros, estrelas=estrelas)


def make_minimal_cfg(**overrides):
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        "SIMULACAO": {"populacao_inicial": "6", "geracoes": "3", "sobreviventes": "3", "modo_semente": "fixo"},
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


class TestHistoricalBacktestBoundary(unittest.TestCase):
    def test_naive_draw_datetime_raises(self):
        with self.assertRaises(ValueError):
            HistoricalBacktestBoundary(draw_id="T-001/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0))

    def test_has_no_numeros_or_estrelas_field(self):
        boundary = make_boundary()
        for field_name in ("numeros", "estrelas"):
            self.assertFalse(hasattr(boundary, field_name))


class TestSignatureNeverSeesTarget(unittest.TestCase):
    def test_prepare_backtest_run_signature(self):
        params = inspect.signature(prepare_backtest_run).parameters
        self.assertNotIn("target", params)
        self.assertNotIn("numeros", params)
        self.assertNotIn("estrelas", params)
        self.assertIn("boundary", params)
        hints = typing.get_type_hints(prepare_backtest_run)
        self.assertEqual(hints.get("boundary"), HistoricalBacktestBoundary)
        self.assertNotEqual(hints.get("boundary"), BacktestTarget)

    def test_run_clerics_backtest_signature(self):
        params = inspect.signature(run_clerics_backtest).parameters
        self.assertNotIn("target", params)
        self.assertNotIn("numeros", params)
        self.assertNotIn("estrelas", params)
        self.assertIn("boundary", params)
        hints = typing.get_type_hints(run_clerics_backtest)
        self.assertEqual(hints.get("boundary"), HistoricalBacktestBoundary)
        self.assertNotEqual(hints.get("boundary"), BacktestTarget)

    def test_reveal_and_evaluate_is_the_only_one_that_takes_a_target(self):
        hints = typing.get_type_hints(reveal_and_evaluate)
        self.assertEqual(hints.get("target"), BacktestTarget)


class TestChangingTargetKeyNeverAffectsPrepareOrSimulate(unittest.TestCase):
    def test_wildly_different_target_keys_same_boundary_produce_identical_context(self):
        target_a = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        target_b = make_target(numeros=(46, 47, 48, 49, 50), estrelas=(11, 12))
        boundary_a = HistoricalBacktestBoundary(draw_id=target_a.draw_id, draw_datetime=target_a.draw_datetime)
        boundary_b = HistoricalBacktestBoundary(draw_id=target_b.draw_id, draw_datetime=target_b.draw_datetime)

        with tempfile.TemporaryDirectory() as hist_root, tempfile.TemporaryDirectory() as scrolls_root:
            write_historical_dataset(hist_root, 2099, "a.json", [
                make_dataset_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00"),
            ])
            write_scroll(scrolls_root, 2099, "001.json", make_scroll("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00"))

            cfg = make_minimal_cfg()
            ctx_a, ariadne_a = prepare_backtest_run(cfg, boundary_a, mode="verified", historical_root=hist_root, scrolls_root=scrolls_root)
            ctx_b, ariadne_b = prepare_backtest_run(cfg, boundary_b, mode="verified", historical_root=hist_root, scrolls_root=scrolls_root)

        self.assertEqual(ctx_a["historico"], ctx_b["historico"])
        self.assertEqual(ctx_a["mundo"], ctx_b["mundo"])
        self.assertEqual(ctx_a["estatisticas"], ctx_b["estatisticas"])


class TestValidateVerifiedMode(unittest.TestCase):
    def test_fully_compliant_cfg_does_not_raise(self):
        _validate_verified_mode(make_minimal_cfg())

    def test_artefactos_vivos_ativo_true_raises_naming_it(self):
        cfg = make_minimal_cfg(ARTEFACTOS_VIVOS={"ativo": "true"})
        with self.assertRaises(ValueError) as ctx:
            _validate_verified_mode(cfg)
        self.assertIn("ARTEFACTOS_VIVOS", str(ctx.exception))
        self.assertIn("ativo", str(ctx.exception))

    def test_arca_permitir_redescoberta_true_raises_naming_it(self):
        cfg = make_minimal_cfg(ARCA_ARTEFACTOS={"permitir_redescoberta": "true", "ativa": "false"})
        with self.assertRaises(ValueError) as ctx:
            _validate_verified_mode(cfg)
        self.assertIn("permitir_redescoberta", str(ctx.exception))

    def test_arca_ativa_true_raises_even_if_permitir_redescoberta_false(self):
        cfg = make_minimal_cfg(ARCA_ARTEFACTOS={"permitir_redescoberta": "false", "ativa": "true"})
        with self.assertRaises(ValueError) as ctx:
            _validate_verified_mode(cfg)
        self.assertIn("[ARCA_ARTEFACTOS] ativa", str(ctx.exception))

    def test_monges_e_escribas_access_key_raises_naming_it(self):
        cfg = make_minimal_cfg(MONGES_E_ESCRIBAS={"acesso_quentes_frios": "Bruxa,Shaman"})
        with self.assertRaises(ValueError) as ctx:
            _validate_verified_mode(cfg)
        self.assertIn("acesso_quentes_frios", str(ctx.exception))

    def test_all_violations_listed_together(self):
        cfg = make_minimal_cfg(
            ARTEFACTOS_VIVOS={"ativo": "true"},
            ARCA_ARTEFACTOS={"permitir_redescoberta": "true", "ativa": "true"},
            MONGES_E_ESCRIBAS={"acesso_gaps": "Elfo"},
        )
        with self.assertRaises(ValueError) as ctx:
            _validate_verified_mode(cfg)
        message = str(ctx.exception)
        for fragment in ("ARTEFACTOS_VIVOS", "permitir_redescoberta", "[ARCA_ARTEFACTOS] ativa", "acesso_gaps"):
            self.assertIn(fragment, message)

    def test_missing_sections_default_to_the_unsafe_real_defaults_and_raise(self):
        # mirrors the real production fallbacks (ativo/permitir_redescoberta/
        # ativa all default True in the real code) — an absent section is
        # NOT automatically safe.
        cfg = configparser.ConfigParser()
        with self.assertRaises(ValueError):
            _validate_verified_mode(cfg)


class TestDeriveMundoCfg(unittest.TestCase):
    def test_missing_timezone_raises(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({"MUNDO": {}})
        with self.assertRaises(ValueError):
            _derive_mundo_cfg(cfg, make_boundary())

    def test_invalid_timezone_raises(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({"MUNDO": {"timezone": "Not/AZone"}})
        with self.assertRaises(ValueError):
            _derive_mundo_cfg(cfg, make_boundary())

    def test_converts_to_configured_timezone_local_time(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({"MUNDO": {"timezone": "Europe/Paris"}})
        boundary = HistoricalBacktestBoundary(
            draw_id="T/2099", draw_datetime=datetime(2099, 7, 14, 18, 0, 0, tzinfo=timezone.utc),
        )
        derived = _derive_mundo_cfg(cfg, boundary)
        # 18:00 UTC in July (CEST, UTC+2) -> 20:00 Europe/Paris local
        self.assertEqual(derived["MUNDO"]["data"], "2099-07-14")
        self.assertEqual(derived["MUNDO"]["hora"], "20:00")

    def test_never_mutates_original_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({"MUNDO": {"timezone": "Europe/Paris", "data": "2000-01-01", "hora": "00:00"}})
        _derive_mundo_cfg(cfg, make_boundary())
        self.assertEqual(cfg["MUNDO"]["data"], "2000-01-01")
        self.assertEqual(cfg["MUNDO"]["hora"], "00:00")


class TestPrepareBacktestRun(unittest.TestCase):
    def setUp(self):
        self.hist_root = tempfile.TemporaryDirectory()
        self.scrolls_root = tempfile.TemporaryDirectory()
        write_historical_dataset(self.hist_root.name, 2099, "a.json", [
            make_dataset_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5]),
            make_dataset_draw("002/2099", "2099-03-10", "2099-03-10T20:00:00+00:00", numeros=[6, 7, 8, 9, 10]),  # >= boundary, must be excluded
        ])
        write_scroll(self.scrolls_root.name, 2099, "001.json", make_scroll("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00"))
        self.addCleanup(self.hist_root.cleanup)
        self.addCleanup(self.scrolls_root.cleanup)

    def test_returns_ctx_and_temporal_ariadne(self):
        cfg = make_minimal_cfg()
        ctx, ariadne = prepare_backtest_run(
            cfg, make_boundary(), mode="verified",
            historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name,
        )
        self.assertIn("historico", ctx)
        self.assertIn("estatisticas", ctx)
        self.assertIn("mundo", ctx)
        self.assertIn("fase_lua", ctx["mundo"])
        self.assertIn("jackpot", ctx["mundo"])
        self.assertIsInstance(ariadne, Ariadne)
        self.assertTrue(ariadne._temporal)

    def test_historico_never_includes_draws_at_or_after_boundary(self):
        cfg = make_minimal_cfg()
        ctx, _ariadne = prepare_backtest_run(
            cfg, make_boundary(), mode="verified",
            historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name,
        )
        ids = [d["data"] for d in ctx["historico"]]
        self.assertNotIn("2099-03-10", ids)

    def test_verified_mode_rejects_unsafe_cfg_before_touching_sources(self):
        cfg = make_minimal_cfg(ARTEFACTOS_VIVOS={"ativo": "true"})
        with self.assertRaises(ValueError):
            prepare_backtest_run(
                cfg, make_boundary(), mode="verified",
                historical_root="/nonexistent/path/that/would/fail/differently",
                scrolls_root=self.scrolls_root.name,
            )

    def test_exploratory_mode_allows_unsafe_cfg(self):
        cfg = make_minimal_cfg(ARTEFACTOS_VIVOS={"ativo": "true"})
        ctx, _ariadne = prepare_backtest_run(
            cfg, make_boundary(), mode="exploratory",
            historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name,
        )
        self.assertIn("historico", ctx)

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            prepare_backtest_run(make_minimal_cfg(), make_boundary(), mode="fast")


def _patched_runs_dir(tmpdir):
    return mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmpdir))


class TestRunClericsBacktest(unittest.TestCase):
    def setUp(self):
        self.cfg = make_minimal_cfg()
        self.ctx = {
            "historico": [{"data": "2099-01-01", "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "jackpot": 0, "vencedores": 0}],
            "estatisticas": {
                "quentes": list(range(1, 51)), "frios": list(range(50, 0, -1)),
                "estrelas_quentes": list(range(1, 13)), "estrelas_frias": list(range(12, 0, -1)),
            },
            "mundo": {"fase_lua": "Lua cheia", "jackpot": 0},
        }
        self.boundary = make_boundary()

    def test_produces_run_id_stamped_records_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            evo, manifest = run_clerics_backtest(self.cfg, dict(self.ctx), seed=2026, boundary=self.boundary)
        self.assertTrue(evo["registos"])
        for record in evo["registos"]:
            self.assertEqual(record["run_id"], manifest["run_id"])
        self.assertEqual(manifest["target_draw"], self.boundary.draw_id)
        self.assertIsNotNone(manifest["completed_at"])

    def test_manifest_timestamps_are_real_wall_clock_not_the_historical_instant(self):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            _evo, manifest = run_clerics_backtest(self.cfg, dict(self.ctx), seed=2026, boundary=self.boundary)
        started = datetime.fromisoformat(manifest["started_at"])
        self.assertNotEqual(started.year, self.boundary.draw_datetime.year)
        self.assertLess(abs((started - datetime.now(timezone.utc)).total_seconds()), 60)

    def test_same_seed_same_cfg_same_ctx_reproduces_identical_records(self):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            evo1, _m1 = run_clerics_backtest(self.cfg, dict(self.ctx), seed=999, boundary=self.boundary)
        with tempfile.TemporaryDirectory() as tmp2, _patched_runs_dir(tmp2):
            evo2, _m2 = run_clerics_backtest(self.cfg, dict(self.ctx), seed=999, boundary=self.boundary)

        strip = lambda regs: [{k: v for k, v in r.items() if k != "run_id"} for r in regs]
        self.assertEqual(strip(evo1["registos"]), strip(evo2["registos"]))

    def test_different_seed_can_change_output(self):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            evo1, _m1 = run_clerics_backtest(self.cfg, dict(self.ctx), seed=1, boundary=self.boundary)
        with tempfile.TemporaryDirectory() as tmp2, _patched_runs_dir(tmp2):
            evo2, _m2 = run_clerics_backtest(self.cfg, dict(self.ctx), seed=2, boundary=self.boundary)

        strip = lambda regs: [{k: v for k, v in r.items() if k != "run_id"} for r in regs]
        self.assertNotEqual(strip(evo1["registos"]), strip(evo2["registos"]))

    def test_g20_and_g100_are_independent_runs_not_prefixes(self):
        # Structural guarantee only, deliberately not tied to any
        # internal mechanism (e.g. CAMINHO_1000_ALMAS's g<gens gating)
        # that might change later: two separate calls produce two
        # separate manifests/run_ids, and the longer run reaches
        # generations the shorter one structurally never computes at
        # all -- proof G20 cannot be obtained by truncating G100,
        # without asserting anything about content matching or
        # diverging at a shared generation number.
        cfg_short = make_minimal_cfg(SIMULACAO={"populacao_inicial": "6", "geracoes": "5", "sobreviventes": "3", "modo_semente": "fixo"})
        cfg_long = make_minimal_cfg(SIMULACAO={"populacao_inicial": "6", "geracoes": "12", "sobreviventes": "3", "modo_semente": "fixo"})

        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            evo_short, manifest_short = run_clerics_backtest(cfg_short, dict(self.ctx), seed=42, boundary=self.boundary)
        with tempfile.TemporaryDirectory() as tmp2, _patched_runs_dir(tmp2):
            evo_long, manifest_long = run_clerics_backtest(cfg_long, dict(self.ctx), seed=42, boundary=self.boundary)

        self.assertNotEqual(manifest_short["run_id"], manifest_long["run_id"])
        self.assertEqual(manifest_short["generated_record_count"], len(evo_short["registos"]))
        self.assertEqual(manifest_long["generated_record_count"], len(evo_long["registos"]))

        generations_short = {r["geracao"] for r in evo_short["registos"]}
        generations_long = {r["geracao"] for r in evo_long["registos"]}
        self.assertEqual(generations_short, set(range(1, 6)))
        self.assertEqual(generations_long, set(range(1, 13)))
        self.assertTrue(generations_long - generations_short)

    def test_failure_leaves_incomplete_manifest_and_never_completes(self):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            with mock.patch(
                "core.services.backtest_orchestrator._run_clerics_algorithm",
                side_effect=RuntimeError("simulated crash"),
            ), mock.patch("core.services.backtest_orchestrator.complete_run") as spy_complete:
                with self.assertRaises(RuntimeError):
                    run_clerics_backtest(self.cfg, dict(self.ctx), seed=2026, boundary=self.boundary)
                spy_complete.assert_not_called()

            incomplete_files = list(Path(tmp).glob("*.incomplete.json"))
            complete_files = list(Path(tmp).glob("RUN-*.json"))
            self.assertEqual(len(incomplete_files), 1)
            self.assertEqual(len([f for f in complete_files if not f.name.endswith(".incomplete.json")]), 0)

    def test_never_calls_get_history_or_builder(self):
        with tempfile.TemporaryDirectory() as tmp, _patched_runs_dir(tmp):
            with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("get_history must never be called")), \
                 mock.patch("world.engine.builder.build", side_effect=AssertionError("builder.build must never be called")):
                evo, _manifest = run_clerics_backtest(self.cfg, dict(self.ctx), seed=2026, boundary=self.boundary)
        self.assertTrue(evo["registos"])


class TestFreezeSimulatedCandidates(unittest.TestCase):
    def test_wraps_each_record_with_temporal_basis_and_run_id(self):
        evo = {"registos": [
            {"geracao": 1, "id": "H-1", "nome": "Test", "classe": "Elfo", "casa": "Casa Lunar",
             "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "origem": "racas_antigas", "run_id": "RUN-X"},
        ]}
        frozen = freeze_simulated_candidates(evo)
        self.assertEqual(len(frozen), 1)
        self.assertIsInstance(frozen[0], SimulatedBacktestCandidate)
        self.assertEqual(frozen[0].temporal_basis, "historical_input_boundary")
        self.assertEqual(frozen[0].run_id, "RUN-X")
        self.assertEqual(frozen[0].candidate.source_type, "evolutionary_individual")

    def test_minotauro_enters_as_plain_evolutionary_individual(self):
        evo = {"registos": [
            {"geracao": 1, "id": "H-1", "nome": "Test", "classe": "Minotauro", "casa": "Casa Lunar",
             "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "origem": "racas_antigas", "run_id": "RUN-X"},
        ]}
        frozen = freeze_simulated_candidates(evo)
        self.assertEqual(frozen[0].candidate.race, "Minotauro")
        self.assertEqual(frozen[0].candidate.source_type, "evolutionary_individual")

    def test_does_not_mutate_evo(self):
        record = {"geracao": 1, "id": "H-1", "nome": "Test", "classe": "Elfo", "casa": "Casa Lunar",
                   "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "origem": "racas_antigas", "run_id": "RUN-X"}
        evo = {"registos": [record]}
        before = dict(record)
        freeze_simulated_candidates(evo)
        self.assertEqual(record, before)


class TestRevealEvaluateSummarizeStaySourceAgnostic(unittest.TestCase):
    def _wrap(self, record, run_id="RUN-X"):
        return SimulatedBacktestCandidate(
            candidate=normalize_candidate_record(record),
            temporal_basis="historical_input_boundary",
            run_id=run_id,
        )

    def test_anao_stays_external_generator(self):
        record = {"geracao": 5, "id": "Anao#1", "nome": "Anao#1", "classe": "Cla Anao", "casa": "Montanha",
                   "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "origem": "cla_anao"}
        wrapped = self._wrap(record)
        self.assertEqual(wrapped.candidate.source_type, "external_generator")

    def test_conselho_and_malphas_stay_distinct_sources(self):
        conselho = self._wrap({"geracao": 5, "id": "Conselho", "nome": "Conselho", "classe": "Conselho Final",
                                "casa": "Conselho", "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "origem": "chave_conselho"})
        malphas = self._wrap({"geracao": 5, "id": "Malphas", "nome": "Malphas", "classe": "Entidade Maléfica",
                               "casa": "Abismo", "numeros": [6, 7, 8, 9, 10], "estrelas": [3, 4], "origem": "corrupcao_final"})
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        evaluations = reveal_and_evaluate([conselho, malphas], target)
        summary = summarize([conselho, malphas], evaluations, relevant_categories=("5+2",))

        self.assertEqual(conselho.candidate.source_type, "aggregator")
        self.assertEqual(malphas.candidate.source_type, "transformer")
        self.assertNotEqual(conselho.candidate.source_name, malphas.candidate.source_name)
        self.assertEqual(summary.total_candidates, 2)

    def test_reveal_and_evaluate_matches_evaluate_candidates(self):
        matching = self._wrap({"geracao": 1, "id": "H-1", "nome": "M", "classe": "Elfo", "casa": "C",
                                 "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "origem": "racas_antigas"})
        target = make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))
        evaluations = reveal_and_evaluate([matching], target)
        self.assertEqual(evaluations[0].category, "5+2")

    def test_summarize_empty_input(self):
        summary = summarize([], [], relevant_categories=())
        self.assertEqual(summary.total_candidates, 0)


if __name__ == "__main__":
    unittest.main()
