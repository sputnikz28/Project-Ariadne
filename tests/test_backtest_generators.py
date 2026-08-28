"""Tests for core/services/backtest_generators.py (Campaign Runner V2).
All historical/scroll fixtures are synthetic; core.services.run_manifest.
RUNS_DIR is always patched to a temp directory so no test here ever
writes to the real datasets/generated/simulations/runs/, and
[AXIOMANTES].guardar_experiencia is proven forced off so no test ever
writes to experiments/axiomancers/runs/.
"""

import configparser
import json
import random
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from core.services.academia.tyche import TYCHE_IDENTITY, run_tyche
from core.services.atomic_io import atomic_create_json, atomic_write_json
from core.services.backtest_generators import GENERATORS
from core.services.backtest_orchestrator import HistoricalBacktestBoundary, prepare_backtest_run
from library.academy.enrollments.registry import AcademyEnrollmentRegistry
from library.academy.students.registry import AcademyStudentRegistry

FUTURE_DT_1 = datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc)
BOUNDARY = HistoricalBacktestBoundary(draw_id="T-A/2099", draw_datetime=FUTURE_DT_1)


def make_dataset_draw(numero_sorteio, data, timestamp_utc, numeros=None, estrelas=None):
    return {
        "numero_sorteio": numero_sorteio, "data": data,
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
        "id": scroll_id, "data": {"extracao": extracao_data, "timestamp_utc": timestamp_utc},
        "extracao": {"numeros": numeros or [1, 2, 3, 4, 5], "estrelas": estrelas or [1, 2]},
        "estatisticas": {"soma": sum(numeros or [1, 2, 3, 4, 5])},
        "astronomia": {"fase_lua": "Lua cheia"}, "estado": "SELADO", "assinatura": {"integridade": "100%"},
    }


def write_scroll(root, year, filename, scroll):
    year_dir = Path(root) / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    (year_dir / filename).write_text(json.dumps(scroll, ensure_ascii=False), encoding="utf-8")


def make_minimal_cfg(**overrides):
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        "SIMULACAO": {"populacao_inicial": "8", "geracoes": "3", "sobreviventes": "4", "modo_semente": "fixo"},
        "CAMINHO_1000_ALMAS": {"ativo": "false"},
        "ARTEFACTOS_VIVOS": {"ativo": "false"},
        "ARCA_ARTEFACTOS": {"permitir_redescoberta": "false", "ativa": "false"},
        "MONGES_E_ESCRIBAS": {
            "acesso_total": "", "acesso_quentes_frios": "", "acesso_historico": "",
            "acesso_pares_trios": "", "acesso_gaps": "",
        },
        "MUNDO": {"timezone": "Europe/Paris"},
        "ESQUELETOS": {"ativos": "true", "quantidade_externa": "3", "largura_numeros": "25", "largura_estrelas": "6"},
        "MELFORKS": {"ativo": "true", "populacao_chaves": "10", "geracoes_chaves": "3", "elite": "3", "representantes": "3"},
        "AXIOMANTES": {
            "peso_conselho": "0.75", "periodo_anos": "1", "limiar_cobertura": "0.0",
            "excesso_minimo": "-1.0", "n_candidatos": "50", "guardar_experiencia": "true",
        },
    })
    for section, keys in overrides.items():
        if not cfg.has_section(section):
            cfg.add_section(section)
        for k, v in keys.items():
            cfg.set(section, k, v)
    return cfg


def _cfg_with_section(cfg, section, values):
    """A COPY of `cfg` (never mutates the caller's cfg) with one extra
    section/values merged in — the same small pattern already used by
    core.services.backtest_generators._cfg_with_generations()/
    _cfg_copy(), duplicated here deliberately rather than importing a
    private production helper into test code.
    """
    copy = configparser.ConfigParser()
    for existing_section in cfg.sections():
        copy[existing_section] = dict(cfg[existing_section])
    if not copy.has_section(section):
        copy.add_section(section)
    for k, v in values.items():
        copy.set(section, k, v)
    return copy


class _GeneratorFixture(unittest.TestCase):
    """Shared synthetic historical_root/scrolls_root, ctx/ariadne_temporal
    built once per test via the real prepare_backtest_run() (Commit 25,
    unmodified) — every adapter test operates on the same honestly-cut
    context every other backtest consumer would get.

    academia_students_root/academia_enrollments_root are isolated,
    always-empty-by-default tmp dirs — run_adapter_isolated() injects
    them as [ACADEMIA] whenever the caller's cfg doesn't already
    specify one, so any test that loops over every registered system
    (e.g. TestNoDiskArtefacts) never falls back to the real
    library/academy/students, library/academy/enrollments paths.
    """

    def setUp(self):
        self.hist_root = tempfile.TemporaryDirectory()
        self.scrolls_root = tempfile.TemporaryDirectory()
        self.academia_students_root = tempfile.TemporaryDirectory()
        self.academia_enrollments_root = tempfile.TemporaryDirectory()
        write_historical_dataset(self.hist_root.name, 2099, "a.json", [
            make_dataset_draw("001/2099", "2099-01-01", "2099-01-01T20:00:00+00:00", numeros=[1, 2, 3, 4, 5]),
            make_dataset_draw("002/2099", "2099-01-08", "2099-01-08T20:00:00+00:00", numeros=[6, 7, 8, 9, 10]),
        ])
        write_scroll(
            self.scrolls_root.name, 2099, "001.json",
            make_scroll("PERG-2099-001", "2099-01-01", "2099-01-01T20:00:00+00:00"),
        )
        self.addCleanup(self.hist_root.cleanup)
        self.addCleanup(self.scrolls_root.cleanup)
        self.addCleanup(self.academia_students_root.cleanup)
        self.addCleanup(self.academia_enrollments_root.cleanup)

    def build_ctx(self, cfg, mode="verified"):
        return prepare_backtest_run(
            cfg, BOUNDARY, mode=mode, historical_root=self.hist_root.name, scrolls_root=self.scrolls_root.name,
        )

    def run_adapter_isolated(self, system, cfg, seed, mode="verified"):
        ctx, ariadne_temporal = self.build_ctx(cfg, mode=mode)
        if not cfg.has_section("ACADEMIA"):
            cfg = _cfg_with_section(cfg, "ACADEMIA", {
                "students_root": self.academia_students_root.name,
                "enrollments_root": self.academia_enrollments_root.name,
            })
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            return GENERATORS[system].run(cfg, ctx, ariadne_temporal, seed, BOUNDARY)


class TestGeneratorsRegistry(_GeneratorFixture):
    def test_exactly_the_nine_approved_systems_are_registered(self):
        self.assertEqual(
            set(GENERATORS),
            {
                "clerics", "skeletons", "melforks", "axiomantes", "pantheon",
                "acaso_puro", "asterias", "treefolks_v2", "academia",
            },
        )

    def test_blocked_systems_are_never_registered(self):
        for blocked in ("vampiros", "vampires", "gargulas", "gargoyles", "lobisomens", "werewolves", "kor_vermelho", "kors"):
            self.assertNotIn(blocked, GENERATORS)

    def test_only_clerics_declares_a_generations_axis(self):
        self.assertEqual(
            {system for system, adapter in GENERATORS.items() if adapter.has_generations},
            {"clerics"},
        )


class TestNoLiveApiOrLookAhead(_GeneratorFixture):
    def test_skeletons_never_touches_get_history_or_builder(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")), \
             tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            output = GENERATORS["skeletons"].run(cfg, ctx, ariadne_temporal, 1, BOUNDARY)
        self.assertTrue(output.candidates)

    def test_melforks_never_touches_get_history_or_builder(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")), \
             tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            output = GENERATORS["melforks"].run(cfg, ctx, ariadne_temporal, 1, BOUNDARY)
        self.assertTrue(output.candidates)

    def test_pantheon_never_touches_get_history_or_builder(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")), \
             tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            output = GENERATORS["pantheon"].run(cfg, ctx, ariadne_temporal, 1, BOUNDARY)
        self.assertTrue(output.candidates)

    def test_axiomantes_never_touches_get_history_or_builder(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")), \
             tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            GENERATORS["axiomantes"].run(cfg, ctx, ariadne_temporal, 1, BOUNDARY)  # portal open/closed both fine

    def test_acaso_puro_never_touches_get_history_or_builder(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")), \
             tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            output = GENERATORS["acaso_puro"].run(cfg, ctx, ariadne_temporal, 1, BOUNDARY)
        self.assertTrue(output.candidates)

    def test_acaso_puro_never_touches_ctx_at_all(self):
        cfg = make_minimal_cfg()
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            output = GENERATORS["acaso_puro"].run(cfg, {}, None, 1, BOUNDARY)
        self.assertTrue(output.candidates)

    def test_axiomantes_receives_the_temporal_ariadne_instance_never_a_live_one(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        with mock.patch("core.services.backtest_generators.execute_ritual", return_value=None) as spy, \
             tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            GENERATORS["axiomantes"].run(cfg, ctx, ariadne_temporal, 1, BOUNDARY)
        received_ariadne = spy.call_args[0][0]
        self.assertIs(received_ariadne, ariadne_temporal)


class TestNoDiskArtefacts(_GeneratorFixture):
    def test_axiomantes_never_saves_experience_regardless_of_cfg(self):
        cfg = make_minimal_cfg(AXIOMANTES={
            "peso_conselho": "0.75", "periodo_anos": "1", "limiar_cobertura": "0.0",
            "excesso_minimo": "-1.0", "n_candidatos": "50", "guardar_experiencia": "true",
        })
        with mock.patch(
            "factions.axiomantes.ritual._save_experience",
            side_effect=AssertionError("must never write an experience file during a campaign"),
        ):
            self.run_adapter_isolated("axiomantes", cfg, seed=1)

    def test_every_adapter_leaves_the_real_runs_dir_untouched(self):
        real_runs_dir = Path("datasets/generated/simulations/runs")
        real_students_dir = Path("library/academy/students/entries")
        real_enrollments_dir = Path("library/academy/enrollments/entries")
        before = set(real_runs_dir.glob("*.json")) if real_runs_dir.exists() else set()
        before_students = set(real_students_dir.glob("*.json")) if real_students_dir.exists() else set()
        before_enrollments = set(real_enrollments_dir.glob("*.json")) if real_enrollments_dir.exists() else set()
        cfg = make_minimal_cfg()
        for system in GENERATORS:
            self.run_adapter_isolated(system, cfg, seed=1)
        after = set(real_runs_dir.glob("*.json")) if real_runs_dir.exists() else set()
        after_students = set(real_students_dir.glob("*.json")) if real_students_dir.exists() else set()
        after_enrollments = set(real_enrollments_dir.glob("*.json")) if real_enrollments_dir.exists() else set()
        self.assertEqual(before, after)
        self.assertEqual(before_students, after_students)
        self.assertEqual(before_enrollments, after_enrollments)


class TestDeterminism(_GeneratorFixture):
    def _strip(self, output):
        return [(c.race, c.numeros, c.estrelas) for c in output.candidates]

    def test_skeletons_same_seed_gives_same_output(self):
        cfg = make_minimal_cfg()
        out1 = self.run_adapter_isolated("skeletons", cfg, seed=777)
        out2 = self.run_adapter_isolated("skeletons", cfg, seed=777)
        self.assertEqual(self._strip(out1), self._strip(out2))

    def test_melforks_same_seed_gives_same_output(self):
        cfg = make_minimal_cfg()
        out1 = self.run_adapter_isolated("melforks", cfg, seed=777)
        out2 = self.run_adapter_isolated("melforks", cfg, seed=777)
        self.assertEqual(self._strip(out1), self._strip(out2))

    def test_pantheon_same_seed_gives_same_output(self):
        cfg = make_minimal_cfg()
        out1 = self.run_adapter_isolated("pantheon", cfg, seed=777)
        out2 = self.run_adapter_isolated("pantheon", cfg, seed=777)
        self.assertEqual(self._strip(out1), self._strip(out2))

    def test_axiomantes_same_seed_gives_same_output(self):
        cfg = make_minimal_cfg()
        out1 = self.run_adapter_isolated("axiomantes", cfg, seed=777)
        out2 = self.run_adapter_isolated("axiomantes", cfg, seed=777)
        self.assertEqual(self._strip(out1), self._strip(out2))

    def test_acaso_puro_same_seed_gives_same_output(self):
        cfg = make_minimal_cfg()
        out1 = self.run_adapter_isolated("acaso_puro", cfg, seed=777)
        out2 = self.run_adapter_isolated("acaso_puro", cfg, seed=777)
        self.assertEqual(self._strip(out1), self._strip(out2))


class TestRngContractPreserved(_GeneratorFixture):
    def test_skeletons_output_is_independent_of_global_random_state(self):
        import random
        cfg = make_minimal_cfg()
        random.seed(111)
        out1 = self.run_adapter_isolated("skeletons", cfg, seed=42)
        random.seed(999)
        out2 = self.run_adapter_isolated("skeletons", cfg, seed=42)
        self.assertEqual(self._strip_local(out1), self._strip_local(out2))

    def test_melforks_never_reads_a_ctx_rng_key(self):
        cfg = make_minimal_cfg()
        ctx, ariadne_temporal = self.build_ctx(cfg)
        ctx_without_rng = dict(ctx)
        ctx_with_bogus_rng = {**ctx, "rng": "not-a-real-rng-object"}
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            import random
            random.seed(55)
            out1 = GENERATORS["melforks"].run(cfg, ctx_without_rng, ariadne_temporal, 55, BOUNDARY)
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            random.seed(55)
            out2 = GENERATORS["melforks"].run(cfg, ctx_with_bogus_rng, ariadne_temporal, 55, BOUNDARY)
        self.assertEqual(self._strip_local(out1), self._strip_local(out2))

    def _strip_local(self, output):
        return [(c.race, c.numeros, c.estrelas) for c in output.candidates]


class TestPantheonGranularity(_GeneratorFixture):
    def test_mago_druida_djinn_aion_are_all_distinguishable_in_one_cell(self):
        cfg = make_minimal_cfg()
        output = self.run_adapter_isolated("pantheon", cfg, seed=1)
        races = {c.race for c in output.candidates}
        self.assertEqual(races, {"Mago", "Druida", "Djinn", "Aion"})

    def test_aion_is_the_only_aggregator_source_type(self):
        cfg = make_minimal_cfg()
        output = self.run_adapter_isolated("pantheon", cfg, seed=1)
        by_race = {c.race: c.source_type for c in output.candidates}
        self.assertEqual(by_race["Aion"], "aggregator")
        for archetype in ("Mago", "Druida", "Djinn"):
            self.assertEqual(by_race[archetype], "external_generator")

    def test_all_share_source_name_ser_superior_except_aion(self):
        cfg = make_minimal_cfg()
        output = self.run_adapter_isolated("pantheon", cfg, seed=1)
        by_race = {c.race: c.source_name for c in output.candidates}
        self.assertEqual(by_race["Mago"], "ser_superior")
        self.assertEqual(by_race["Druida"], "ser_superior")
        self.assertEqual(by_race["Djinn"], "ser_superior")
        self.assertEqual(by_race["Aion"], "deus")


class TestGenerationsHonesty(_GeneratorFixture):
    def test_clerics_reports_a_real_generations_value(self):
        cfg = make_minimal_cfg()
        output = self.run_adapter_isolated("clerics", cfg, seed=1)
        self.assertEqual(output.generations, 3)

    def test_skeletons_axiomantes_pantheon_acaso_puro_report_none(self):
        cfg = make_minimal_cfg()
        for system in ("skeletons", "axiomantes", "pantheon", "acaso_puro"):
            output = self.run_adapter_isolated(system, cfg, seed=1)
            self.assertIsNone(output.generations, f"{system} must report generations=None, not a fabricated value")

    def test_melforks_reports_its_own_real_geracoes_chaves_not_none(self):
        cfg = make_minimal_cfg()
        output = self.run_adapter_isolated("melforks", cfg, seed=1)
        self.assertEqual(output.generations, 3)

    def test_acaso_puro_reports_configured_quantity(self):
        cfg = make_minimal_cfg(ARENA={"acaso_puro_quantidade": "7"})
        output = self.run_adapter_isolated("acaso_puro", cfg, seed=1)
        self.assertEqual(len(output.candidates), 7)

    def test_acaso_puro_defaults_to_20_when_unconfigured(self):
        cfg = make_minimal_cfg()
        output = self.run_adapter_isolated("acaso_puro", cfg, seed=1)
        self.assertEqual(len(output.candidates), 20)


class TestVerifiedModeGate(_GeneratorFixture):
    def test_verified_mode_rejects_uncertified_memory_cfg_for_every_system(self):
        cfg = make_minimal_cfg(ARTEFACTOS_VIVOS={"ativo": "true"})
        for system in GENERATORS:
            with self.subTest(system=system):
                with self.assertRaises(ValueError):
                    self.build_ctx(cfg, mode="verified")


# ---------------------------------------------------------------------------
# Astérias de Thalássia — Astéria Abissal (purist) / Astéria das Marés
# (backoff). Pure-math tests operate on hand-verified synthetic histories,
# never through the full campaign fixture (too small, only 2 draws) — the
# adapter tests below build ctx['historico'] directly for precise control.
# ---------------------------------------------------------------------------

def _star_draw(estrelas):
    return {"numeros": [1, 2, 3, 4, 5], "estrelas": estrelas}


# n(P)=5 exactly at the Abissal threshold, P=(1,2) -- hand-verified:
# counts={3:4,4:4,5:1,6:1}, all others 0; probs sum to 1 with alpha=1.
_RICH_HISTORICO = [
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([1, 2]), _star_draw([5, 6]),
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([1, 2]), _star_draw([3, 4]),
    _star_draw([7, 8]),
    _star_draw([1, 2]),
]

# Same structure as _RICH_HISTORICO, but the "next" stars are swapped to
# 9/10 instead of 3/4 -- same participation pattern (both lineages
# participate), different resulting star probabilities.
_RICH_HISTORICO_ALT = [
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([1, 2]), _star_draw([5, 6]),
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([1, 2]), _star_draw([9, 10]),
    _star_draw([7, 8]),
    _star_draw([1, 2]),
]

# P=(1,2) never occurred earlier -- Abissal abstains, Marés backs off to
# the marginal (len(historico)=6 >= 5, each star appears exactly once).
_SPARSE_HISTORICO = [
    _star_draw([5, 6]), _star_draw([7, 8]), _star_draw([9, 10]),
    _star_draw([11, 12]), _star_draw([3, 4]), _star_draw([1, 2]),
]

# len(historico)=3 < 5 -- even the marginal backoff is too sparse; both
# lineages abstain.
_TOO_SHORT_HISTORICO = [
    _star_draw([9, 10]), _star_draw([11, 12]), _star_draw([1, 2]),
]


class TestAsteriasMath(unittest.TestCase):
    def test_query_pair_is_unordered(self):
        from core.services.backtest_generators import _star_pair
        self.assertEqual(_star_pair([9, 3]), (3, 9))
        self.assertEqual(_star_pair([3, 9]), (3, 9))

    def test_last_position_never_used_as_a_current_occurrence(self):
        # A single-draw history: if the last position could match
        # itself, n would be 1 -- it must be 0. The target's own
        # instant is structurally unreachable, by construction of the
        # loop bound, not by convention.
        from core.services.backtest_generators import _count_conditional_star_votes, _star_pair
        historico = [_star_draw([1, 2])]
        n, _counts = _count_conditional_star_votes(historico, _star_pair(historico[-1]["estrelas"]))
        self.assertEqual(n, 0)

    def test_conditional_distribution_at_exact_threshold(self):
        from core.services.backtest_generators import _asterias_distribution
        probs, participates = _asterias_distribution(_RICH_HISTORICO, "abissal")
        self.assertTrue(participates)
        self.assertAlmostEqual(sum(probs.values()), 1.0)
        self.assertAlmostEqual(probs[3], 5 / 22)
        self.assertAlmostEqual(probs[4], 5 / 22)
        self.assertAlmostEqual(probs[5], 2 / 22)
        self.assertAlmostEqual(probs[6], 2 / 22)
        for s in (1, 2, 7, 8, 9, 10, 11, 12):
            self.assertAlmostEqual(probs[s], 1 / 22)

    def test_abissal_abstains_below_threshold(self):
        from core.services.backtest_generators import _asterias_distribution
        probs, participates = _asterias_distribution(_SPARSE_HISTORICO, "abissal")
        self.assertFalse(participates)
        self.assertIsNone(probs)

    def test_mares_backs_off_to_marginal_below_threshold(self):
        from core.services.backtest_generators import _asterias_distribution
        probs, participates = _asterias_distribution(_SPARSE_HISTORICO, "mares")
        self.assertTrue(participates)
        self.assertAlmostEqual(sum(probs.values()), 1.0)
        for s in range(1, 13):
            self.assertAlmostEqual(probs[s], 2 / 24)

    def test_mares_abstains_when_history_itself_too_short(self):
        from core.services.backtest_generators import _asterias_distribution
        _probs, participates = _asterias_distribution(_TOO_SHORT_HISTORICO, "mares")
        self.assertFalse(participates)


class TestAsteriasAdapter(unittest.TestCase):
    def make_cfg(self, **overrides):
        return make_minimal_cfg(**overrides)

    def make_ctx(self, historico):
        return {"historico": historico, "estatisticas": {}, "mundo": {}}

    def run_isolated(self, historico, cfg, seed):
        ctx = self.make_ctx(historico)
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            return GENERATORS["asterias"].run(cfg, ctx, None, seed, BOUNDARY)

    def test_never_touches_get_history_or_builder(self):
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "3"})
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")):
            output = self.run_isolated(_RICH_HISTORICO, cfg, seed=1)
        self.assertTrue(output.candidates)

    def test_produces_both_lineages_when_both_participate(self):
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "5"})
        output = self.run_isolated(_RICH_HISTORICO, cfg, seed=1)
        races = {c.race for c in output.candidates}
        self.assertEqual(races, {"Astéria Abissal", "Astéria das Marés"})
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Astéria Abissal"), 5)
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Astéria das Marés"), 5)

    def test_attempted_races_always_declared_even_when_abissal_abstains(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_SPARSE_HISTORICO, cfg, seed=1)
        self.assertEqual(output.attempted_races, frozenset({"Astéria Abissal", "Astéria das Marés"}))
        races = {c.race for c in output.candidates}
        self.assertEqual(races, {"Astéria das Marés"})
        self.assertNotIn("Astéria Abissal", races)

    def test_both_lineages_abstain_when_history_too_short(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_TOO_SHORT_HISTORICO, cfg, seed=1)
        self.assertEqual(output.candidates, ())
        self.assertEqual(output.attempted_races, frozenset({"Astéria Abissal", "Astéria das Marés"}))
        self.assertIsNone(output.generations)

    def test_numeros_never_depend_on_star_transition_data(self):
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "3"})
        out_a = self.run_isolated(_RICH_HISTORICO, cfg, seed=42)
        out_b = self.run_isolated(_RICH_HISTORICO_ALT, cfg, seed=42)
        for race in ("Astéria Abissal", "Astéria das Marés"):
            ca = [c for c in out_a.candidates if c.race == race]
            cb = [c for c in out_b.candidates if c.race == race]
            self.assertEqual(len(ca), len(cb))
            for x, y in zip(ca, cb):
                self.assertEqual(x.numeros, y.numeros, "numeros must be identical regardless of star history")
        all_stars_a = [c.estrelas for c in out_a.candidates]
        all_stars_b = [c.estrelas for c in out_b.candidates]
        self.assertNotEqual(all_stars_a, all_stars_b, "different star histories must produce different star picks")

    def test_deterministic_given_same_seed(self):
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "4"})
        out1 = self.run_isolated(_RICH_HISTORICO, cfg, seed=777)
        out2 = self.run_isolated(_RICH_HISTORICO, cfg, seed=777)
        strip = lambda o: [(c.race, c.numeros, c.estrelas) for c in o.candidates]
        self.assertEqual(strip(out1), strip(out2))

    def test_output_independent_of_global_random_state(self):
        import random
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "3"})
        random.seed(111)
        out1 = self.run_isolated(_RICH_HISTORICO, cfg, seed=42)
        random.seed(999)
        out2 = self.run_isolated(_RICH_HISTORICO, cfg, seed=42)
        strip = lambda o: [(c.race, c.numeros, c.estrelas) for c in o.candidates]
        self.assertEqual(strip(out1), strip(out2))

    def test_generations_is_always_none(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_RICH_HISTORICO, cfg, seed=1)
        self.assertIsNone(output.generations)

    def test_provenance_source_type_and_name(self):
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "2"})
        output = self.run_isolated(_RICH_HISTORICO, cfg, seed=1)
        for c in output.candidates:
            self.assertEqual(c.source_type, "external_generator")
            self.assertEqual(c.source_name, "asterias_thalassia")
            self.assertIn(c.race, ("Astéria Abissal", "Astéria das Marés"))

    def test_respects_configured_quantidade(self):
        cfg = self.make_cfg(ARENA={"asterias_quantidade": "7"})
        output = self.run_isolated(_RICH_HISTORICO, cfg, seed=1)
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Astéria Abissal"), 7)
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Astéria das Marés"), 7)

    def test_defaults_to_20_when_unconfigured(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_RICH_HISTORICO, cfg, seed=1)
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Astéria Abissal"), 20)


# ---------------------------------------------------------------------------
# Treefolks V2 — As Grandes Florestas. PyTorch is not installed in this
# environment (no installation authorized this tranche), so Yggdrasil
# abstains structurally in every test below — the same abstention path
# already covered by tests/test_treefolks_v2_yggdrasil.py's
# TestHasTorchAbstention. Dodona/Brocéliande/Tír na nÓg/Fortuna are the
# four Florestas exercised for real here.
# ---------------------------------------------------------------------------

_TREEFOLKS_V2_HISTORICO = [
    {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
    {"numeros": [6, 7, 8, 9, 10], "estrelas": [3, 4]},
    {"numeros": [11, 12, 13, 14, 15], "estrelas": [5, 6]},
    {"numeros": [16, 17, 18, 19, 20], "estrelas": [7, 8]},
    {"numeros": [21, 22, 23, 24, 25], "estrelas": [9, 10]},
    {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
    {"numeros": [26, 27, 28, 29, 30], "estrelas": [11, 12]},
    {"numeros": [6, 7, 8, 9, 10], "estrelas": [3, 4]},
]

_TREEFOLKS_V2_RACES = (
    "Yggdrasil — LSTM-v1",
    "Dodona — Bayes-v1",
    "Brocéliande — Markov-v1",
    "Tír na nÓg — MonteCarlo-v1",
    "Fortuna — Controlo-v1",
)


class TestTreefolksV2Adapter(unittest.TestCase):
    def make_cfg(self, **overrides):
        return make_minimal_cfg(**overrides)

    def make_ctx(self, historico):
        return {"historico": historico, "estatisticas": {}, "mundo": {}}

    def run_isolated(self, historico, cfg, seed):
        ctx = self.make_ctx(historico)
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            return GENERATORS["treefolks_v2"].run(cfg, ctx, None, seed, BOUNDARY)

    def test_never_touches_get_history_or_builder(self):
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "3"})
        with mock.patch("core.data.loaders.get_history", side_effect=AssertionError("must never be called")), \
             mock.patch("world.engine.builder.build", side_effect=AssertionError("must never be called")):
            output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        self.assertTrue(output.candidates)

    def test_attempted_races_always_declares_all_five_florestas(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        self.assertEqual(output.attempted_races, frozenset(_TREEFOLKS_V2_RACES))

    def test_yggdrasil_abstains_without_torch_but_others_participate(self):
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "4"})
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        races_with_candidates = {c.race for c in output.candidates}
        self.assertNotIn("Yggdrasil — LSTM-v1", races_with_candidates)
        for race in ("Dodona — Bayes-v1", "Brocéliande — Markov-v1", "Tír na nÓg — MonteCarlo-v1", "Fortuna — Controlo-v1"):
            self.assertIn(race, races_with_candidates)
            self.assertEqual(sum(1 for c in output.candidates if c.race == race), 4)

    def test_full_abstention_still_visible_via_attempted_races_when_history_too_short_for_broceliande(self):
        cfg = self.make_cfg()
        output = self.run_isolated([_TREEFOLKS_V2_HISTORICO[0]], cfg, seed=1)  # len==1 -> Brocéliande abstains too
        races_with_candidates = {c.race for c in output.candidates}
        self.assertNotIn("Brocéliande — Markov-v1", races_with_candidates)
        self.assertNotIn("Yggdrasil — LSTM-v1", races_with_candidates)
        self.assertIn("Brocéliande — Markov-v1", output.attempted_races)  # still discoverable
        self.assertIn("Yggdrasil — LSTM-v1", output.attempted_races)
        # Dodona/Fortuna/Tír na nÓg have no such threshold -- still participate.
        self.assertIn("Dodona — Bayes-v1", races_with_candidates)
        self.assertIn("Fortuna — Controlo-v1", races_with_candidates)
        self.assertIn("Tír na nÓg — MonteCarlo-v1", races_with_candidates)

    def test_provenance_source_type_and_name(self):
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "2"})
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        for c in output.candidates:
            self.assertEqual(c.source_type, "external_generator")
            self.assertEqual(c.source_name, "treefolks_v2")
            self.assertIn(c.race, _TREEFOLKS_V2_RACES)
            self.assertIn(" — ", c.race)  # "Floresta — Treefolk" composed string

    def test_respects_configured_quantidade(self):
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "6"})
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Fortuna — Controlo-v1"), 6)

    def test_defaults_to_20_when_unconfigured(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        self.assertEqual(sum(1 for c in output.candidates if c.race == "Fortuna — Controlo-v1"), 20)

    def test_deterministic_given_same_seed(self):
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "5"})
        out1 = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=777)
        out2 = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=777)
        strip = lambda o: [(c.race, c.numeros, c.estrelas) for c in o.candidates]
        self.assertEqual(strip(out1), strip(out2))

    def test_output_independent_of_global_random_state(self):
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "3"})
        random.seed(111)
        out1 = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=42)
        random.seed(999)
        out2 = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=42)
        strip = lambda o: [(c.race, c.numeros, c.estrelas) for c in o.candidates]
        self.assertEqual(strip(out1), strip(out2))

    def test_different_florestas_produce_different_keys_same_cell(self):
        # Proves the 5 Florestas don't collapse onto the same output
        # (e.g. by accidentally sharing one RNG stream) -- Dodona and
        # Fortuna, in particular, should differ given Dodona's
        # historically-informed scores vs. Fortuna's uniform ones.
        cfg = self.make_cfg(TREEFOLKS_V2={"quantidade_por_treefolk": "10"})
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        dodona_keys = {(c.numeros, c.estrelas) for c in output.candidates if c.race == "Dodona — Bayes-v1"}
        fortuna_keys = {(c.numeros, c.estrelas) for c in output.candidates if c.race == "Fortuna — Controlo-v1"}
        self.assertNotEqual(dodona_keys, fortuna_keys)

    def test_generations_is_always_none(self):
        cfg = self.make_cfg()
        output = self.run_isolated(_TREEFOLKS_V2_HISTORICO, cfg, seed=1)
        self.assertIsNone(output.generations)


# ---------------------------------------------------------------------------
# Academia Arcana de Nemerion — Foundation V1, commit 4/5. Only Cátedra de
# Tyche exists as an executable classroom/doctrine. Every test here uses its
# own isolated tempfile students_root/enrollments_root (via make_cfg()'s
# [ACADEMIA] override) — never the real library/academy/.
# ---------------------------------------------------------------------------


class TestAcademiaAdapter(unittest.TestCase):
    def setUp(self):
        self._students_tmp = tempfile.TemporaryDirectory()
        self._enrollments_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._students_tmp.cleanup)
        self.addCleanup(self._enrollments_tmp.cleanup)
        self.student_registry = AcademyStudentRegistry(base=self._students_tmp.name)
        self.enrollment_registry = AcademyEnrollmentRegistry(base=self._enrollments_tmp.name)

    def make_cfg(self, **overrides):
        cfg = make_minimal_cfg(**overrides)
        if not cfg.has_section("ACADEMIA"):
            cfg.add_section("ACADEMIA")
        cfg.set("ACADEMIA", "students_root", self._students_tmp.name)
        cfg.set("ACADEMIA", "enrollments_root", self._enrollments_tmp.name)
        return cfg

    def make_ctx(self, historico):
        return {"historico": historico, "estatisticas": {}, "mundo": {}}

    def run_isolated(self, historico, cfg, seed):
        ctx = self.make_ctx(historico)
        with tempfile.TemporaryDirectory() as tmp, mock.patch("core.services.run_manifest.RUNS_DIR", Path(tmp)):
            return GENERATORS["academia"].run(cfg, ctx, None, seed, BOUNDARY)

    def _enroll(self, student_id, **overrides):
        args = dict(
            student_id=student_id,
            classroom_id=TYCHE_IDENTITY.classroom_id,
            doctrine_id=TYCHE_IDENTITY.doctrine_id,
            doctrine_version=TYCHE_IDENTITY.doctrine_version,
            student_registry=self.student_registry,
        )
        args.update(overrides)
        return self.enrollment_registry.create(**args)

    def _enroll_active_student(self, name="Aurelia Vance", species=None):
        student = self.student_registry.create(name=name, species=species)
        self._enroll(student.student_id)
        return student

    # -- eligibility (case A/B/C) ---------------------------------------

    def test_active_student_active_enrollment_participates(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(len(output.candidates), 1)

    def test_inactive_student_does_not_participate(self):
        cfg = self.make_cfg()
        student = self.student_registry.create(name="Ghost", status="inactive")
        self._enroll(student.student_id)
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_graduated_student_does_not_participate(self):
        cfg = self.make_cfg()
        student = self.student_registry.create(name="Ghost", status="graduated")
        self._enroll(student.student_id)
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_expelled_student_does_not_participate(self):
        cfg = self.make_cfg()
        student = self.student_registry.create(name="Ghost", status="expelled")
        self._enroll(student.student_id)
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_withdrawn_enrollment_does_not_participate(self):
        cfg = self.make_cfg()
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student.student_id, status="withdrawn")
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_completed_enrollment_does_not_participate(self):
        cfg = self.make_cfg()
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student.student_id, status="completed")
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_enrollment_for_another_classroom_does_not_run_tyche(self):
        cfg = self.make_cfg()
        student = self.student_registry.create(name="Aurelia Vance")
        self._enroll(student.student_id, classroom_id="rebeldes", doctrine_id="alguma_doutrina")
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_unknown_student_reference_is_handled_without_crashing(self):
        entries_dir = Path(self._enrollments_tmp.name) / "entries"
        atomic_create_json(entries_dir / "NEM-ENR-000001.json", {
            "enrollment_id": "NEM-ENR-000001", "student_id": "NEM-STU-999999",
            "institution_id": TYCHE_IDENTITY.institution_id, "classroom_id": TYCHE_IDENTITY.classroom_id,
            "doctrine_id": TYCHE_IDENTITY.doctrine_id, "doctrine_version": TYCHE_IDENTITY.doctrine_version,
            "status": "active", "enrolled_at": "2026-01-01T00:00:00+00:00",
        })
        cfg = self.make_cfg()
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    # -- eligibility (case D) + attempted_races --------------------------

    def test_no_eligible_students_produces_no_candidates(self):
        cfg = self.make_cfg()
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates, ())

    def test_attempted_races_empty_when_no_eligible_participants(self):
        cfg = self.make_cfg()
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.attempted_races, frozenset())

    def test_attempted_races_declares_tyche_when_participants_exist(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.attempted_races, frozenset({"Cátedra de Tyche — Fundamentos do Acaso"}))

    def test_attempted_races_has_a_single_entry_regardless_of_student_count(self):
        cfg = self.make_cfg()
        for i in range(5):
            self._enroll_active_student(name=f"Student {i}")
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(len(output.attempted_races), 1)

    # -- multi-student ----------------------------------------------------

    def test_one_candidate_per_eligible_student(self):
        cfg = self.make_cfg()
        for i in range(5):
            self._enroll_active_student(name=f"Student {i}")
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(len(output.candidates), 5)

    def test_same_race_different_entity_id(self):
        cfg = self.make_cfg()
        s1 = self._enroll_active_student(name="Aurelia Vance")
        s2 = self._enroll_active_student(name="Bram Ostergren")
        output = self.run_isolated([], cfg, seed=1)
        races = {c.race for c in output.candidates}
        self.assertEqual(races, {"Cátedra de Tyche — Fundamentos do Acaso"})
        entity_ids = {c.entity_id for c in output.candidates}
        self.assertEqual(entity_ids, {s1.student_id, s2.student_id})

    def test_entity_name_correct_per_student(self):
        cfg = self.make_cfg()
        self._enroll_active_student(name="Aurelia Vance")
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(output.candidates[0].entity_name, "Aurelia Vance")

    def test_independent_rng_streams_per_student(self):
        cfg = self.make_cfg()
        self._enroll_active_student(name="Aurelia Vance")
        self._enroll_active_student(name="Bram Ostergren")
        output = self.run_isolated([], cfg, seed=1)
        keys = [(c.numeros, c.estrelas) for c in output.candidates]
        self.assertNotEqual(keys[0], keys[1])

    def test_reexecution_is_reproducible(self):
        cfg = self.make_cfg()
        self._enroll_active_student(name="Aurelia Vance")
        self._enroll_active_student(name="Bram Ostergren")
        out1 = self.run_isolated([], cfg, seed=777)
        out2 = self.run_isolated([], cfg, seed=777)
        strip = lambda o: sorted((c.entity_id, c.numeros, c.estrelas) for c in o.candidates)
        self.assertEqual(strip(out1), strip(out2))

    # -- Campaign Runner integration ---------------------------------------

    def test_generators_academia_exists(self):
        self.assertIn("academia", GENERATORS)

    def test_smoke_one_cell(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        output = self.run_isolated([], cfg, seed=1)
        self.assertEqual(len(output.candidates), 1)
        c = output.candidates[0]
        self.assertEqual(c.source_type, "external_generator")
        self.assertEqual(c.source_name, "academia")

    def test_generations_is_always_none(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        output = self.run_isolated([], cfg, seed=1)
        self.assertIsNone(output.generations)

    def test_produced_candidate_key_has_valid_shape(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        output = self.run_isolated([], cfg, seed=1)
        c = output.candidates[0]
        self.assertEqual(len(c.numeros), 5)
        self.assertEqual(len(set(c.numeros)), 5)
        self.assertEqual(len(c.estrelas), 2)
        self.assertEqual(len(set(c.estrelas)), 2)

    def test_metadata_carries_the_authorizing_enrollment_id(self):
        cfg = self.make_cfg()
        student = self._enroll_active_student()
        enrollment = next(e for e in self.enrollment_registry.load_all() if e.student_id == student.student_id)
        output = self.run_isolated([], cfg, seed=1)
        c = output.candidates[0]
        self.assertEqual(c.metadata["enrollment_id"], enrollment.enrollment_id)

    def test_no_persistent_write_during_generation(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        before_students = set(Path(self._students_tmp.name, "entries").glob("*.json"))
        before_enrollments = set(Path(self._enrollments_tmp.name, "entries").glob("*.json"))
        self.run_isolated([], cfg, seed=1)
        after_students = set(Path(self._students_tmp.name, "entries").glob("*.json"))
        after_enrollments = set(Path(self._enrollments_tmp.name, "entries").glob("*.json"))
        self.assertEqual(before_students, after_students)
        self.assertEqual(before_enrollments, after_enrollments)

    # -- isolation: statistical historico never influences Tyche ----------

    def test_changing_statistical_historico_never_changes_tyche_output(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        historico_a = [{"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}]
        historico_b = [{"numeros": [46, 47, 48, 49, 50], "estrelas": [11, 12]}] * 20
        out_a = self.run_isolated(historico_a, cfg, seed=555)
        out_b = self.run_isolated(historico_b, cfg, seed=555)
        strip = lambda o: [(c.numeros, c.estrelas) for c in o.candidates]
        self.assertEqual(strip(out_a), strip(out_b))

    def test_academic_history_never_influences_output(self):
        cfg = self.make_cfg()
        student = self._enroll_active_student()
        out_empty_history = self.run_isolated([], cfg, seed=555)

        entry_path = Path(self._students_tmp.name) / "entries" / f"{student.student_id}.json"
        record = json.loads(entry_path.read_text(encoding="utf-8"))
        record["historico"] = [{
            "event_type": "test_participation", "occurred_at": "2020-01-01T00:00:00+00:00",
            "extra": {"suspicious_arbitrary_data": True},
        }]
        atomic_write_json(entry_path, record)

        out_with_history = self.run_isolated([], cfg, seed=555)
        strip = lambda o: [(c.numeros, c.estrelas) for c in o.candidates]
        self.assertEqual(strip(out_empty_history), strip(out_with_history))

    def test_run_tyche_is_called_with_only_an_rng_argument(self):
        cfg = self.make_cfg()
        self._enroll_active_student()
        with mock.patch("core.services.backtest_generators.run_tyche", wraps=run_tyche) as spy:
            self.run_isolated([{"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]}], cfg, seed=1)
        spy.assert_called_once()
        args, kwargs = spy.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(kwargs, {})
        self.assertIsInstance(args[0], random.Random)


if __name__ == "__main__":
    unittest.main()
