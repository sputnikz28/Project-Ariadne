"""Tests for core/services/backtest_lab.py. All targets/candidates are
synthetic — none reuses 14/08/2026 or any other real draw. DRAW_DT is a
deliberately far-future, made-up instant so nothing here can ever be
confused with a real historical result.
"""

import inspect
import unittest
from datetime import datetime, timedelta, timezone

from core.services.backtest_lab import (
    BacktestTarget,
    FrozenCandidate,
    evaluate_backtest_candidates,
    freeze_backtest_candidates,
    summarize_backtest,
)
from core.services.candidate_evaluation import CandidateEvaluation
from core.services.candidate_provenance import normalize_candidate_record

DRAW_DT = datetime(2099, 3, 10, 20, 0, 0, tzinfo=timezone.utc)
BEFORE = (DRAW_DT - timedelta(days=1)).isoformat()
AFTER = (DRAW_DT + timedelta(days=1)).isoformat()


def make_record(origem="racas_antigas", run_id=None, **overrides):
    record = {
        "geracao": 5, "id": "H-00001", "nome": "Testauro",
        "classe": "Elfo", "casa": "Casa Lunar",
        "numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2],
        "origem": origem,
    }
    if run_id is not None:
        record["run_id"] = run_id
    record.update(overrides)
    return record


def make_candidate(**kwargs):
    return normalize_candidate_record(make_record(**kwargs))


def manifest(run_id, completed_at):
    return {"run_id": run_id, "completed_at": completed_at}


def make_target(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2)):
    return BacktestTarget(draw_id="T-001/2099", draw_datetime=DRAW_DT, numeros=numeros, estrelas=estrelas)


class TestBacktestTargetValidation(unittest.TestCase):
    def test_naive_draw_datetime_raises(self):
        with self.assertRaises(ValueError):
            BacktestTarget(
                draw_id="T-001/2099", draw_datetime=datetime(2099, 3, 10, 20, 0, 0),
                numeros=(1, 2, 3, 4, 5), estrelas=(1, 2),
            )

    def test_tz_aware_draw_datetime_is_accepted(self):
        target = make_target()
        self.assertEqual(target.draw_datetime, DRAW_DT)


class TestFreezeSignatureNeverSeesTarget(unittest.TestCase):
    def test_freeze_backtest_candidates_has_no_target_numeros_or_estrelas_parameter(self):
        params = set(inspect.signature(freeze_backtest_candidates).parameters)
        self.assertNotIn("target", params)
        self.assertNotIn("numeros", params)
        self.assertNotIn("estrelas", params)
        self.assertNotIn("target_numeros", params)
        self.assertNotIn("target_estrelas", params)
        self.assertEqual(
            params,
            {"candidates", "official_draw_datetime", "run_manifests_by_id", "allow_unresolved", "allow_mixed_runs"},
        )


class TestFreezeNaiveDatetimeRejected(unittest.TestCase):
    def test_naive_official_draw_datetime_raises(self):
        with self.assertRaises(ValueError):
            freeze_backtest_candidates([], datetime(2099, 3, 10, 20, 0, 0), {})


class TestFreezeProvenancePolicy(unittest.TestCase):
    def test_verified_candidate_is_included(self):
        candidate = make_candidate(run_id="RUN-A")
        manifests = {"RUN-A": manifest("RUN-A", BEFORE)}
        result = freeze_backtest_candidates([candidate], DRAW_DT, manifests)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].provenance, "verified")
        self.assertEqual(result[0].run_id, "RUN-A")

    def test_legacy_candidate_is_included_and_never_promoted(self):
        candidate = make_candidate()  # no run_id at all
        result = freeze_backtest_candidates([candidate], DRAW_DT, {})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].provenance, "legacy")
        self.assertIsNone(result[0].run_id)

    def test_ineligible_candidate_raises_and_produces_no_frozen_candidate(self):
        candidate = make_candidate(run_id="RUN-A")
        manifests = {"RUN-A": manifest("RUN-A", AFTER)}
        with self.assertRaises(ValueError):
            freeze_backtest_candidates([candidate], DRAW_DT, manifests)

    def test_multiple_ineligible_candidates_are_all_reported_in_one_error(self):
        c1 = make_candidate(id="H-1", nome="One", run_id="RUN-A")
        c2 = make_candidate(id="H-2", nome="Two", run_id="RUN-B")
        manifests = {
            "RUN-A": manifest("RUN-A", AFTER),
            "RUN-B": manifest("RUN-B", AFTER),
        }
        with self.assertRaises(ValueError) as ctx:
            freeze_backtest_candidates([c1, c2], DRAW_DT, manifests)
        message = str(ctx.exception)
        self.assertIn("One", message)
        self.assertIn("Two", message)

    def test_unresolved_excluded_by_default(self):
        candidate = make_candidate(run_id="RUN-ghost")
        result = freeze_backtest_candidates([candidate], DRAW_DT, {})
        self.assertEqual(result, ())

    def test_unresolved_included_with_explicit_override(self):
        candidate = make_candidate(run_id="RUN-ghost")
        result = freeze_backtest_candidates([candidate], DRAW_DT, {}, allow_unresolved=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].provenance, "unresolved")


class TestFreezeRunIdConsistency(unittest.TestCase):
    def test_all_legacy_together_never_creates_an_artificial_common_run(self):
        candidates = [make_candidate(id=f"H-{i}", nome=f"N{i}") for i in range(5)]
        result = freeze_backtest_candidates(candidates, DRAW_DT, {})
        self.assertEqual(len(result), 5)
        self.assertTrue(all(fc.run_id is None for fc in result))
        self.assertTrue(all(fc.provenance == "legacy" for fc in result))

    def test_legacy_mixed_with_one_verified_run_does_not_count_as_mixed_runs(self):
        legacy = make_candidate(id="H-legacy", nome="Legacy")
        verified = make_candidate(id="H-verified", nome="Verified", run_id="RUN-A")
        manifests = {"RUN-A": manifest("RUN-A", BEFORE)}
        result = freeze_backtest_candidates([legacy, verified], DRAW_DT, manifests)
        self.assertEqual(len(result), 2)

    def test_two_verified_runs_without_override_raises(self):
        c1 = make_candidate(id="H-1", nome="One", run_id="RUN-A")
        c2 = make_candidate(id="H-2", nome="Two", run_id="RUN-B")
        manifests = {
            "RUN-A": manifest("RUN-A", BEFORE),
            "RUN-B": manifest("RUN-B", BEFORE),
        }
        with self.assertRaises(ValueError):
            freeze_backtest_candidates([c1, c2], DRAW_DT, manifests)

    def test_two_verified_runs_with_allow_mixed_runs_succeeds(self):
        c1 = make_candidate(id="H-1", nome="One", run_id="RUN-A")
        c2 = make_candidate(id="H-2", nome="Two", run_id="RUN-B")
        manifests = {
            "RUN-A": manifest("RUN-A", BEFORE),
            "RUN-B": manifest("RUN-B", BEFORE),
        }
        result = freeze_backtest_candidates([c1, c2], DRAW_DT, manifests, allow_mixed_runs=True)
        self.assertEqual(len(result), 2)

    def test_order_is_preserved(self):
        c1 = make_candidate(id="H-1", nome="One")
        c2 = make_candidate(id="H-2", nome="Two")
        result = freeze_backtest_candidates([c1, c2], DRAW_DT, {})
        self.assertEqual(result[0].candidate.entity_name, "One")
        self.assertEqual(result[1].candidate.entity_name, "Two")

    def test_does_not_mutate_candidates_or_manifests(self):
        candidate = make_candidate(run_id="RUN-A")
        manifests = {"RUN-A": manifest("RUN-A", BEFORE)}
        candidates = [candidate]
        before_candidates = list(candidates)
        before_manifests = dict(manifests)
        freeze_backtest_candidates(candidates, DRAW_DT, manifests)
        self.assertEqual(candidates, before_candidates)
        self.assertEqual(manifests, before_manifests)


class TestEvaluateBacktestCandidates(unittest.TestCase):
    def test_matches_evaluate_candidates_and_preserves_order(self):
        matching = make_candidate(id="H-1", nome="Match", numeros=[1, 2, 3, 4, 5], estrelas=[1, 2])
        missing = make_candidate(id="H-2", nome="Miss", numeros=[10, 20, 30, 40, 50], estrelas=[10, 11])
        frozen = freeze_backtest_candidates([matching, missing], DRAW_DT, {})
        target = make_target()
        evaluations = evaluate_backtest_candidates(frozen, target)
        self.assertEqual(len(evaluations), 2)
        self.assertEqual(evaluations[0].category, "5+2")
        self.assertEqual(evaluations[1].category, "0+0")
        self.assertIsInstance(evaluations[0], CandidateEvaluation)

    def test_empty_frozen_candidates_returns_empty_tuple(self):
        self.assertEqual(evaluate_backtest_candidates((), make_target()), ())


class TestSummarizeBacktest(unittest.TestCase):
    def test_empty_input_does_not_fail(self):
        summary = summarize_backtest((), (), relevant_categories=())
        self.assertEqual(summary.total_candidates, 0)

    def test_relevant_categories_can_be_compared_without_reevaluating(self):
        matching = make_candidate(id="H-1", nome="Match", numeros=[1, 2, 3, 4, 5], estrelas=[1, 2])
        frozen = freeze_backtest_candidates([matching], DRAW_DT, {})
        target = make_target()
        evaluations = evaluate_backtest_candidates(frozen, target)

        strict = summarize_backtest(frozen, evaluations, relevant_categories=("5+2",))
        loose = summarize_backtest(frozen, evaluations, relevant_categories=("0+0", "5+2"))

        self.assertEqual(strict.relevant_rate, 1.0)
        self.assertEqual(loose.relevant_rate, 1.0)
        none_relevant = summarize_backtest(frozen, evaluations, relevant_categories=())
        self.assertEqual(none_relevant.relevant_rate, 0.0)


class TestProvenanceTaxonomyNoSpecialCasing(unittest.TestCase):
    def test_minotauro_is_a_plain_evolutionary_individual(self):
        candidate = make_candidate(origem="racas_antigas", classe="Minotauro")
        frozen = freeze_backtest_candidates([candidate], DRAW_DT, {})
        self.assertEqual(frozen[0].candidate.source_type, "evolutionary_individual")
        self.assertEqual(frozen[0].candidate.race, "Minotauro")

    def test_dwarf_is_a_plain_external_generator(self):
        candidate = make_candidate(origem="cla_anao")
        frozen = freeze_backtest_candidates([candidate], DRAW_DT, {})
        self.assertEqual(frozen[0].candidate.source_type, "external_generator")

    def test_council_and_malphas_stay_separate_sources(self):
        conselho = make_candidate(origem="chave_conselho", id="Conselho", nome="Conselho")
        malphas = make_candidate(origem="corrupcao_final", id="Malphas", nome="Malphas")
        frozen = freeze_backtest_candidates([conselho, malphas], DRAW_DT, {})
        self.assertEqual(len(frozen), 2)
        self.assertEqual(frozen[0].candidate.source_type, "aggregator")
        self.assertEqual(frozen[1].candidate.source_type, "transformer")
        self.assertNotEqual(frozen[0].candidate.source_name, frozen[1].candidate.source_name)

    def test_no_minotauro_string_appears_in_backtest_lab_source(self):
        import core.services.backtest_lab as backtest_lab_module
        with open(backtest_lab_module.__file__, "r", encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("Minotauro", source)


class TestFrozenCandidateShape(unittest.TestCase):
    def test_frozen_candidate_is_the_documented_dataclass(self):
        candidate = make_candidate()
        result = freeze_backtest_candidates([candidate], DRAW_DT, {})
        self.assertIsInstance(result[0], FrozenCandidate)

    def test_frozen_candidate_dataclass_itself_is_frozen(self):
        candidate = make_candidate()
        result = freeze_backtest_candidates([candidate], DRAW_DT, {})
        with self.assertRaises(Exception):
            result[0].provenance = "verified"


if __name__ == "__main__":
    unittest.main()
