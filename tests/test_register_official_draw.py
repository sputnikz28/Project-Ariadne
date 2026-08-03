"""Integration tests for register_official_draw.py — always against a
temporary fake repository (never the real datasets/scrolls). Evaluations
and the test-suite step are exercised via patched run_evaluations()/
run_tests_suite() rather than real subprocess calls to the real scripts.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import register_official_draw as cli
from core.services.historical_draw_generator import DrawInput, register_draws
from core.services.historical_scroll import build_scroll

SEED_DATASET = {
    "schema_version": "3.0",
    "jogo": "Euromilhões",
    "regras_representadas": {
        "numeros_por_chave": 5, "intervalo_numeros": [1, 50],
        "estrelas_por_chave": 2, "intervalo_estrelas": [1, 12],
    },
    "intervalo": {},
    "estado_dataset": "",
    "resumo_conjunto": {},
    "notas_metodologicas": [],
    "sorteios": [],
}


def make_draw_input(**overrides):
    fields = dict(
        numero_sorteio="001/2026",
        data="2026-01-06",  # a Tuesday
        numeros=(1, 2, 3, 4, 5),
        estrelas=(1, 2),
        ordem_numeros=(5, 3, 1, 4, 2),
        ordem_estrelas=(2, 1),
    )
    fields.update(overrides)
    return DrawInput(**fields)


class RegisterOfficialDrawTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        self.repo_root = self.base / "repo"
        self.dataset_root = self.repo_root / "datasets" / "historical" / "euromillions"
        self.scrolls_root = self.repo_root / "library" / "scrolls"
        (self.dataset_root / "2026").mkdir(parents=True)
        (self.scrolls_root / "2026").mkdir(parents=True)

    def seed_repo(self, initial_draws):
        """Builds an initial dataset (via the real, already-trusted
        register_draws()) and matching scrolls (via build_scroll()), and
        writes them into the fake repo. Returns the dataset path.
        """
        dataset = register_draws(SEED_DATASET, initial_draws)
        last_numero = dataset["sorteios"][-1]["numero_sorteio"].split("/")[0]
        dataset_path = self.dataset_root / "2026" / f"euromilhoes_2026_001_{last_numero}_dataset_completo.json"
        dataset_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")

        for draw in dataset["sorteios"]:
            numero = draw["numero_sorteio"].split("/")[0]
            scroll = build_scroll(draw)
            (self.scrolls_root / "2026" / f"{numero}.json").write_text(
                json.dumps(scroll, indent=2, ensure_ascii=False), encoding="utf-8",
            )
        return dataset_path

    def snapshot(self):
        """{relative_path: content_bytes} for every file under repo_root —
        used to prove --dry-run and failed installs change nothing.
        """
        return {
            str(p.relative_to(self.repo_root)): p.read_bytes()
            for p in self.repo_root.rglob("*") if p.is_file()
        }

    def register(self, draw_inputs, **kwargs):
        kwargs.setdefault("repo_root", self.repo_root)
        kwargs.setdefault("dataset_root", self.dataset_root)
        kwargs.setdefault("scrolls_root", self.scrolls_root)
        return cli.register_official_draws(draw_inputs, **kwargs)


class TestSuccessfulRegistration(RegisterOfficialDrawTestCase):
    def test_single_draw_success(self):
        self.seed_repo([make_draw_input()])
        report = self.register([make_draw_input(numero_sorteio="002/2026", data="2026-01-09")])

        self.assertTrue(report.success)
        self.assertEqual(report.draws_added, ["002/2026"])
        self.assertEqual(report.new_dataset_filename, "euromilhoes_2026_001_002_dataset_completo.json")
        self.assertEqual(report.scrolls_created, ["002.json"])

        new_path = self.dataset_root / "2026" / report.new_dataset_filename
        self.assertTrue(new_path.exists())
        old_path = self.dataset_root / "2026" / "euromilhoes_2026_001_001_dataset_completo.json"
        self.assertFalse(old_path.exists())
        self.assertTrue((self.scrolls_root / "2026" / "002.json").exists())

        installed = json.loads(new_path.read_text(encoding="utf-8"))
        self.assertEqual(len(installed["sorteios"]), 2)

    def test_batch_success_registers_all_in_order(self):
        self.seed_repo([make_draw_input()])
        batch = [
            make_draw_input(numero_sorteio="002/2026", data="2026-01-09"),
            make_draw_input(
                numero_sorteio="003/2026", data="2026-01-13",
                numeros=(6, 7, 8, 9, 10), estrelas=(3, 4),
                ordem_numeros=(10, 9, 8, 7, 6), ordem_estrelas=(4, 3),
            ),
        ]
        report = self.register(batch)

        self.assertTrue(report.success)
        self.assertEqual(report.draws_added, ["002/2026", "003/2026"])
        self.assertEqual(report.new_dataset_filename, "euromilhoes_2026_001_003_dataset_completo.json")
        self.assertEqual(set(report.scrolls_created), {"002.json", "003.json"})


class TestDryRun(RegisterOfficialDrawTestCase):
    def test_dry_run_changes_nothing_on_disk(self):
        self.seed_repo([make_draw_input()])
        before = self.snapshot()
        report = self.register([make_draw_input(numero_sorteio="002/2026", data="2026-01-09")], dry_run=True)
        after = self.snapshot()

        self.assertTrue(report.success)
        self.assertTrue(report.dry_run)
        self.assertEqual(report.new_dataset_filename, "euromilhoes_2026_001_002_dataset_completo.json")
        self.assertEqual(before, after)


class TestIdempotencyAndDuplicates(RegisterOfficialDrawTestCase):
    def test_second_run_of_same_draw_fails_without_writing(self):
        self.seed_repo([make_draw_input()])
        first = self.register([make_draw_input(numero_sorteio="002/2026", data="2026-01-09")])
        self.assertTrue(first.success)

        before = self.snapshot()
        second = self.register([make_draw_input(numero_sorteio="002/2026", data="2026-01-09")])
        after = self.snapshot()

        self.assertFalse(second.success)
        self.assertIn("already exists", second.failure_reason)
        self.assertEqual(before, after)


class TestInstallRollback(RegisterOfficialDrawTestCase):
    def test_failure_between_dataset_and_scroll_install_rolls_back(self):
        self.seed_repo([make_draw_input()])
        old_path = self.dataset_root / "2026" / "euromilhoes_2026_001_001_dataset_completo.json"
        old_content_before = old_path.read_bytes()

        real_atomic_write_json = cli.atomic_write_json
        call_count = {"n": 0}

        def flaky_atomic_write_json(path, data):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("simulated failure writing the scroll")
            return real_atomic_write_json(path, data)

        with patch.object(cli, "atomic_write_json", side_effect=flaky_atomic_write_json):
            report = self.register([make_draw_input(numero_sorteio="002/2026", data="2026-01-09")])

        self.assertFalse(report.success)
        self.assertIn("install failed", report.failure_reason)

        # old dataset survives untouched
        self.assertTrue(old_path.exists())
        self.assertEqual(old_path.read_bytes(), old_content_before)
        # the new dataset file created by the first (successful) write was rolled back
        new_path = self.dataset_root / "2026" / "euromilhoes_2026_001_002_dataset_completo.json"
        self.assertFalse(new_path.exists())
        # no scroll was left behind either
        self.assertFalse((self.scrolls_root / "2026" / "002.json").exists())


class TestEvaluationsAndTestsOrdering(RegisterOfficialDrawTestCase):
    def test_evaluations_partial_failure_is_reported_without_failing_the_registration(self):
        self.seed_repo([make_draw_input()])
        with patch.object(cli, "run_evaluations", return_value="PARTIAL FAILURE at evaluate_heroes.py --sorteio 002/2026 (exit 1)") as mock_eval:
            report = self.register(
                [make_draw_input(numero_sorteio="002/2026", data="2026-01-09")],
                with_evaluations=True,
            )
        self.assertTrue(report.success)  # dataset+scrolls still succeeded
        self.assertTrue(mock_eval.called)
        self.assertTrue(report.evaluations_status.startswith("PARTIAL FAILURE"))

    def test_run_tests_is_optional_and_not_invoked_by_default(self):
        self.seed_repo([make_draw_input()])
        with patch.object(cli, "run_tests_suite") as mock_tests:
            report = self.register([make_draw_input(numero_sorteio="002/2026", data="2026-01-09")])
        self.assertTrue(report.success)
        self.assertIsNone(report.tests_status)
        mock_tests.assert_not_called()

    def test_tests_run_before_evaluations_and_evaluations_are_skipped_if_tests_fail(self):
        self.seed_repo([make_draw_input()])
        with patch.object(cli, "run_tests_suite", return_value="FAILED") as mock_tests, \
             patch.object(cli, "run_evaluations") as mock_eval:
            report = self.register(
                [make_draw_input(numero_sorteio="002/2026", data="2026-01-09")],
                run_tests=True, with_evaluations=True,
            )
        self.assertTrue(report.success)  # dataset+scrolls installation itself still succeeded
        self.assertEqual(report.tests_status, "FAILED")
        self.assertEqual(report.evaluations_status, "SKIPPED (tests failed)")
        mock_tests.assert_called_once()
        mock_eval.assert_not_called()

    def test_tests_pass_then_evaluations_run_normally(self):
        self.seed_repo([make_draw_input()])
        with patch.object(cli, "run_tests_suite", return_value="OK") as mock_tests, \
             patch.object(cli, "run_evaluations", return_value="OK") as mock_eval:
            report = self.register(
                [make_draw_input(numero_sorteio="002/2026", data="2026-01-09")],
                run_tests=True, with_evaluations=True,
            )
        self.assertEqual(report.tests_status, "OK")
        self.assertEqual(report.evaluations_status, "OK")
        mock_tests.assert_called_once()
        mock_eval.assert_called_once()


class TestExitCodes(unittest.TestCase):
    def _report(self, **overrides):
        fields = dict(
            success=True, draws_added=["002/2026"], new_dataset_filename="x.json",
            scrolls_created=["002.json"], validation_ok=True, dry_run=False,
            evaluations_status=None, tests_status=None, elapsed_seconds=0.1, failure_reason=None,
        )
        fields.update(overrides)
        return cli.RegistrationReport(**fields)

    def _exit_code_for(self, report):
        tests_failed = report.tests_status == "FAILED"
        evaluations_not_ok = report.evaluations_status is not None and report.evaluations_status != "OK"
        if tests_failed and evaluations_not_ok:
            return 4
        if evaluations_not_ok:
            return 3
        if tests_failed:
            return 2
        return 0

    def test_all_ok_is_zero(self):
        self.assertEqual(self._exit_code_for(self._report()), 0)

    def test_tests_failed_only_is_two(self):
        self.assertEqual(self._exit_code_for(self._report(tests_status="FAILED")), 2)

    def test_evaluations_failed_only_is_three(self):
        self.assertEqual(self._exit_code_for(self._report(evaluations_status="PARTIAL FAILURE at x")), 3)

    def test_both_failed_is_four(self):
        report = self._report(tests_status="FAILED", evaluations_status="SKIPPED (tests failed)")
        self.assertEqual(self._exit_code_for(report), 4)


class TestLocateDatasetPath(RegisterOfficialDrawTestCase):
    def test_ignores_preview_and_backup_files(self):
        dataset_path = self.seed_repo([make_draw_input()])
        (dataset_path.parent / "euromilhoes_2026_001_001_dataset_completo.preview.json").write_text("{}", encoding="utf-8")
        (dataset_path.parent / "euromilhoes_2026_001_001_dataset_completo.json.backup").write_text("{}", encoding="utf-8")
        (dataset_path.parent / ".tmp-abcxyz.json").write_text("{}", encoding="utf-8")

        found = cli.locate_dataset_path(2026, self.dataset_root)
        self.assertEqual(found, dataset_path)

    def test_raises_on_zero_candidates(self):
        with self.assertRaises(FileNotFoundError):
            cli.locate_dataset_path(2099, self.dataset_root)

    def test_raises_on_multiple_candidates(self):
        dataset_path = self.seed_repo([make_draw_input()])
        (dataset_path.parent / "euromilhoes_2026_001_999_dataset_completo.json").write_text(
            dataset_path.read_text(encoding="utf-8"), encoding="utf-8",
        )
        with self.assertRaises(FileNotFoundError):
            cli.locate_dataset_path(2026, self.dataset_root)


if __name__ == "__main__":
    unittest.main()
