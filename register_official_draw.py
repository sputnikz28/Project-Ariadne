"""Register one or more official Euromillions draws — a single command
covering the whole flow already validated manually for draws 059-061/2026.

    python register_official_draw.py \\
        --draw 062/2026 --date 2026-08-04 \\
        --numbers 1 2 3 4 5 --stars 1 2 \\
        --output-order-numbers 5 3 1 4 2 --output-order-stars 2 1

    python register_official_draw.py --batch draws.json --with-evaluations

Thin orchestration layer only: all schema/methodology logic lives in
core.services.historical_draw_generator, core.services.historical_astronomy,
core.services.historical_statistics, core.services.historical_scroll and
core.services.historical_dataset. This module never reimplements any of
that — it only reads, stages, validates, installs, and reports.

Never runs git add/commit/push.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from core.services.atomic_io import atomic_write_json
from core.services.historical_dataset import discover_datasets, load_dataset, validate_historical_dataset
from core.services.historical_draw_generator import (
    DrawInput,
    DrawValidationError,
    next_dataset_filename,
    register_draws,
)
from core.services.historical_scroll import build_scroll

DEFAULT_REPO_ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register one or more official Euromillions draws.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--draw", help="Draw number, e.g. 062/2026")
    mode.add_argument("--batch", help="Path to a JSON file with multiple draws")

    parser.add_argument("--date")
    parser.add_argument("--numbers", nargs=5, type=int)
    parser.add_argument("--stars", nargs=2, type=int)
    parser.add_argument("--output-order-numbers", nargs=5, type=int, dest="output_order_numbers")
    parser.add_argument("--output-order-stars", nargs=2, type=int, dest="output_order_stars")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--with-evaluations", action="store_true")
    parser.add_argument("--run-tests", action="store_true")

    args = parser.parse_args(argv)

    if args.draw is not None:
        required = [
            ("--date", args.date), ("--numbers", args.numbers), ("--stars", args.stars),
            ("--output-order-numbers", args.output_order_numbers),
            ("--output-order-stars", args.output_order_stars),
        ]
        missing = [name for name, value in required if value is None]
        if missing:
            parser.error(f"--draw requires {', '.join(missing)}")

    return args


def draw_input_from_single_flags(args: argparse.Namespace) -> DrawInput:
    return DrawInput(
        numero_sorteio=args.draw,
        data=args.date,
        numeros=tuple(args.numbers),
        estrelas=tuple(args.stars),
        ordem_numeros=tuple(args.output_order_numbers),
        ordem_estrelas=tuple(args.output_order_stars),
    )


def load_batch(path: Path) -> list[DrawInput]:
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        DrawInput(
            numero_sorteio=item["draw"],
            data=item["date"],
            numeros=tuple(item["numbers"]),
            estrelas=tuple(item["stars"]),
            ordem_numeros=tuple(item["output_order_numbers"]),
            ordem_estrelas=tuple(item["output_order_stars"]),
        )
        for item in items
    ]


def draw_inputs_from_args(args: argparse.Namespace) -> list[DrawInput]:
    if args.batch:
        return load_batch(Path(args.batch))
    return [draw_input_from_single_flags(args)]


# ---------------------------------------------------------------------------
# Locating the canonical dataset for a year
# ---------------------------------------------------------------------------

def locate_dataset_path(year: int, dataset_root: Path) -> Path:
    """Exactly one canonical dataset file per year. Ignores .preview.json,
    backups and temp files. Raises FileNotFoundError if zero or more than
    one candidate is found — never guesses.
    """
    candidates = sorted(
        p for p in discover_datasets(dataset_root)
        if p.parent.name == str(year)
        and not p.name.endswith(".preview.json")
        and ".backup" not in p.name
        and not p.name.startswith(".tmp")
    )
    if not candidates:
        raise FileNotFoundError(f"no canonical historical dataset found for year {year} under {dataset_root / str(year)}")
    if len(candidates) > 1:
        raise FileNotFoundError(f"multiple candidate datasets found for year {year}: {[p.name for p in candidates]}")
    return candidates[0]


def find_reference_scroll(scrolls_dir: Path) -> dict | None:
    if not scrolls_dir.is_dir():
        return None
    candidates = sorted(scrolls_dir.glob("*.json"), key=lambda p: p.stem)
    if not candidates:
        return None
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Staging (outside the repository) and validation
# ---------------------------------------------------------------------------

def stage_dataset_and_scrolls(
    updated_dataset: dict, new_sorteios: list[dict], staging_dir: Path,
) -> tuple[Path, dict[str, Path]]:
    dataset_path = staging_dir / "dataset.json"
    dataset_path.write_text(json.dumps(updated_dataset, indent=2, ensure_ascii=False), encoding="utf-8")

    scroll_paths: dict[str, Path] = {}
    for draw in new_sorteios:
        numero = draw["numero_sorteio"]
        scroll = build_scroll(draw)
        path = staging_dir / f"scroll_{numero.split('/')[0]}.json"
        path.write_text(json.dumps(scroll, indent=2, ensure_ascii=False), encoding="utf-8")
        scroll_paths[numero] = path

    return dataset_path, scroll_paths


def validate_staged(
    staged_dataset_path: Path, staged_scrolls: dict[str, Path], reference_scroll: dict | None,
) -> list[str]:
    problems: list[str] = []
    dataset = json.loads(staged_dataset_path.read_text(encoding="utf-8"))
    problems.extend(validate_historical_dataset(dataset))

    reference_keys = set(reference_scroll.keys()) if reference_scroll is not None else None
    sorteios_by_numero = {s["numero_sorteio"]: s for s in dataset.get("sorteios", [])}

    for numero, path in staged_scrolls.items():
        scroll = json.loads(path.read_text(encoding="utf-8"))
        if reference_keys is not None and set(scroll.keys()) != reference_keys:
            problems.append(f"scroll {numero}: schema differs from the reference scroll")
        draw = sorteios_by_numero.get(numero)
        expected_sha = draw["identificadores"]["sha256_chave"] if draw else None
        if scroll.get("assinatura", {}).get("sha256") != expected_sha:
            problems.append(f"scroll {numero}: assinatura.sha256 does not match identificadores.sha256_chave")

    return problems


# ---------------------------------------------------------------------------
# Installation (create-new-then-delete-old; never overwrites the old file)
# ---------------------------------------------------------------------------

def install(
    staged_dataset_path: Path,
    staged_scrolls: dict[str, Path],
    old_dataset_path: Path,
    year_dir: Path,
    scrolls_dir: Path,
    last_numero_sorteio: str,
) -> tuple[Path, list[Path]]:
    new_dataset_path = year_dir / next_dataset_filename(old_dataset_path.name, last_numero_sorteio)
    scroll_dest_paths = {
        numero: scrolls_dir / f"{numero.split('/')[0]}.json"
        for numero in staged_scrolls
    }

    if new_dataset_path.exists() and new_dataset_path != old_dataset_path:
        raise FileExistsError(f"install target already exists: {new_dataset_path}")
    for dest in scroll_dest_paths.values():
        if dest.exists():
            raise FileExistsError(f"install target already exists: {dest}")

    created: list[Path] = []
    try:
        dataset_content = json.loads(staged_dataset_path.read_text(encoding="utf-8"))
        atomic_write_json(new_dataset_path, dataset_content)
        created.append(new_dataset_path)

        for numero, staged_path in staged_scrolls.items():
            scroll_content = json.loads(staged_path.read_text(encoding="utf-8"))
            dest = scroll_dest_paths[numero]
            atomic_write_json(dest, scroll_content)
            created.append(dest)

        if new_dataset_path != old_dataset_path:
            old_dataset_path.unlink()

        return new_dataset_path, [scroll_dest_paths[n] for n in staged_scrolls]
    except Exception:
        for path in created:
            if path.exists():
                path.unlink()
        raise


# ---------------------------------------------------------------------------
# Evaluations and tests (isolated so tests can patch them directly)
# ---------------------------------------------------------------------------

def run_evaluations(repo_root: Path, numeros: list[str], python_executable: str) -> str:
    heroes_script = repo_root / "evaluate_heroes.py"
    for numero in numeros:
        result = subprocess.run([python_executable, str(heroes_script), "--sorteio", numero], cwd=str(repo_root))
        if result.returncode != 0:
            return f"PARTIAL FAILURE at evaluate_heroes.py --sorteio {numero} (exit {result.returncode})"

    legends_script = repo_root / "evaluate_legends.py"
    result = subprocess.run([python_executable, str(legends_script)], cwd=str(repo_root))
    if result.returncode != 0:
        return f"PARTIAL FAILURE at evaluate_legends.py (exit {result.returncode})"

    return "OK"


def run_tests_suite(repo_root: Path, python_executable: str) -> str:
    result = subprocess.run(
        [python_executable, "-m", "unittest", "tests.test_historical_dataset"],
        cwd=str(repo_root),
    )
    return "OK" if result.returncode == 0 else "FAILED"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

@dataclass
class RegistrationReport:
    success: bool
    draws_added: list[str]
    new_dataset_filename: str | None
    scrolls_created: list[str]
    validation_ok: bool
    dry_run: bool
    evaluations_status: str | None  # None=not requested, "OK", "PARTIAL FAILURE at ...", "SKIPPED (tests failed)"
    tests_status: str | None        # None=not requested, "OK", "FAILED"
    elapsed_seconds: float
    failure_reason: str | None


def _fail(draws_added, validation_ok, dry_run, start, reason) -> RegistrationReport:
    return RegistrationReport(
        success=False, draws_added=draws_added, new_dataset_filename=None, scrolls_created=[],
        validation_ok=validation_ok, dry_run=dry_run, evaluations_status=None, tests_status=None,
        elapsed_seconds=time.monotonic() - start, failure_reason=reason,
    )


def register_official_draws(
    draw_inputs: list[DrawInput],
    *,
    dry_run: bool = False,
    with_evaluations: bool = False,
    run_tests: bool = False,
    repo_root: Path | None = None,
    dataset_root: Path | None = None,
    scrolls_root: Path | None = None,
    python_executable: str | None = None,
) -> RegistrationReport:
    start = time.monotonic()
    repo_root = Path(repo_root) if repo_root is not None else DEFAULT_REPO_ROOT
    dataset_root = Path(dataset_root) if dataset_root is not None else repo_root / "datasets" / "historical" / "euromillions"
    scrolls_root = Path(scrolls_root) if scrolls_root is not None else repo_root / "library" / "scrolls"
    python_executable = python_executable or sys.executable

    if not draw_inputs:
        return _fail([], False, dry_run, start, "no draws given to register")

    years = {int(di.data[:4]) for di in draw_inputs}
    if len(years) != 1:
        return _fail([], False, dry_run, start, f"all draws in one run must share the same year, got {sorted(years)}")
    year = years.pop()

    try:
        dataset_path = locate_dataset_path(year, dataset_root)
    except FileNotFoundError as exc:
        return _fail([], False, dry_run, start, str(exc))

    dataset = load_dataset(dataset_path)

    try:
        updated_dataset = register_draws(dataset, draw_inputs)
    except DrawValidationError as exc:
        return _fail([], False, dry_run, start, str(exc))

    new_sorteios = updated_dataset["sorteios"][len(dataset["sorteios"]):]
    numero_sorteios = [s["numero_sorteio"] for s in new_sorteios]
    last_numero_sorteio = updated_dataset["sorteios"][-1]["numero_sorteio"]

    staging_dir = Path(tempfile.mkdtemp(prefix="register_official_draw_"))
    try:
        staged_dataset_path, staged_scrolls = stage_dataset_and_scrolls(updated_dataset, new_sorteios, staging_dir)

        scrolls_dir = scrolls_root / str(year)
        reference_scroll = find_reference_scroll(scrolls_dir)
        problems = validate_staged(staged_dataset_path, staged_scrolls, reference_scroll)

        if problems:
            return _fail(numero_sorteios, False, dry_run, start, "validation failed: " + "; ".join(problems))

        if dry_run:
            return RegistrationReport(
                success=True,
                draws_added=numero_sorteios,
                new_dataset_filename=next_dataset_filename(dataset_path.name, last_numero_sorteio),
                scrolls_created=[f"{n.split('/')[0]}.json" for n in numero_sorteios],
                validation_ok=True, dry_run=True,
                evaluations_status=None, tests_status=None,
                elapsed_seconds=time.monotonic() - start, failure_reason=None,
            )

        try:
            new_dataset_path, scroll_paths = install(
                staged_dataset_path, staged_scrolls, dataset_path,
                dataset_root / str(year), scrolls_dir, last_numero_sorteio,
            )
        except Exception as exc:
            return _fail(numero_sorteios, True, dry_run, start, f"install failed: {exc}")
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    # Tests run before evaluations by design: evaluations must never start
    # against a dataset the test suite has not (yet) confirmed structurally
    # sound relative to the whole historical corpus.
    tests_status = None
    evaluations_status = None

    if run_tests:
        tests_status = run_tests_suite(repo_root, python_executable)

    if with_evaluations:
        if run_tests and tests_status == "FAILED":
            evaluations_status = "SKIPPED (tests failed)"
        else:
            evaluations_status = run_evaluations(repo_root, numero_sorteios, python_executable)

    return RegistrationReport(
        success=True,
        draws_added=numero_sorteios,
        new_dataset_filename=new_dataset_path.name,
        scrolls_created=[p.name for p in scroll_paths],
        validation_ok=True,
        dry_run=False,
        evaluations_status=evaluations_status,
        tests_status=tests_status,
        elapsed_seconds=time.monotonic() - start,
        failure_reason=None,
    )


def format_report(report: RegistrationReport) -> str:
    lines = []
    if not report.success:
        lines.append("FALHOU")
        lines.append(f"motivo: {report.failure_reason}")
        lines.append(f"tempo total: {report.elapsed_seconds:.1f}s")
        return "\n".join(lines)

    lines.append(f"concursos adicionados: {', '.join(report.draws_added)}")
    if report.dry_run:
        lines.append("modo: --dry-run (nada foi escrito no repositório)")
        lines.append(f"novo nome do dataset (previsto): {report.new_dataset_filename}")
        lines.append(f"scrolls (previstos): {', '.join(report.scrolls_created)}")
    else:
        lines.append(f"novo nome do dataset: {report.new_dataset_filename}")
        lines.append(f"scrolls criados: {', '.join(report.scrolls_created)}")
    lines.append(f"validação: {'sucesso' if report.validation_ok else 'falhou'}")
    lines.append(f"testes: {report.tests_status if report.tests_status is not None else 'não pedidos'}")
    lines.append(f"avaliações: {report.evaluations_status if report.evaluations_status is not None else 'não pedidas'}")
    lines.append(f"tempo total: {report.elapsed_seconds:.1f}s")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        draw_inputs = draw_inputs_from_args(args)
    except (json.JSONDecodeError, KeyError, OSError) as exc:
        print(f"erro ao interpretar input: {exc}")
        return 1

    report = register_official_draws(
        draw_inputs,
        dry_run=args.dry_run,
        with_evaluations=args.with_evaluations,
        run_tests=args.run_tests,
    )
    print(format_report(report))

    if not report.success:
        return 1
    if report.dry_run:
        return 0

    tests_failed = report.tests_status == "FAILED"
    evaluations_not_ok = report.evaluations_status is not None and report.evaluations_status != "OK"

    if tests_failed and evaluations_not_ok:
        return 4
    if evaluations_not_ok:
        return 3
    if tests_failed:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
