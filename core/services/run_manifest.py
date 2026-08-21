"""Run manifest — one persistent record per main.py execution, capturing
what a run needs to later prove (or admit it can't prove) that a
prediction existed before an official draw result. Individual prediction
records (arquivo_destino.json) reference a run by run_id instead of
duplicating this metadata on every entry.

Deliberately not retroactive: historical predictions that ran before this
module existed have no run_id and no manifest. That's what the "legacy"
provenance class (see core/services/hero_evaluation.py) is for — this
module never fabricates a manifest for them.

File naming doubles as the version-control policy (see .gitignore):
start_run() writes "<run_id>.incomplete.json" — a run that never finishes
(crash, interrupt) leaves only this, and it's gitignored by pattern, so
it can never be committed by accident. complete_run() writes the final
"<run_id>.json" and removes the incomplete file; that finished filename
is NOT gitignored, so a genuine, complete manifest can be committed
alongside the prediction records that reference its run_id — which is
what makes "verified" provenance reconstructible from a clean clone.

run_id collision handling (found during Commit 25's Backtest
Orchestrator, whose tests start multiple runs back-to-back much faster
than main.py's historical single-run-per-invocation usage pattern):
_run_id_from_timestamp() now includes microseconds, which makes a
same-run_id collision rare but NOT impossible — clock resolution on
some platforms is coarser than one microsecond, and nothing here
depends on wall-clock granularity as a uniqueness proof. Before ever
writing a run's files, start_run() checks whether a manifest (complete
or incomplete) already exists for the timestamp-derived run_id and, if
so, deterministically appends "-1", "-2", ... (never a random UUID —
the collision resolution is itself reproducible given the same
sequence of prior collisions) until it finds one that doesn't collide.
This never overwrites an existing manifest of either kind. It does not
close every theoretical multi-process race (check-then-write is not
atomic across processes) — it solves exactly the deterministic,
single-process, back-to-back-calls case this project actually has.
started_at/completed_at remain real, separately-stored timestamps —
classify_temporal_provenance() keeps reading completed_at, never the
run_id string, and is unmodified by this change.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from core.services.atomic_io import atomic_write_json, read_json

RUNS_DIR = Path("datasets/generated/simulations/runs")
VERSION_FILE = Path("VERSION")


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_id_from_timestamp(dt):
    return "RUN-" + dt.strftime("%Y%m%dT%H%M%S%fZ")


def _manifest_path(run_id):
    return RUNS_DIR / f"{run_id}.json"


def _incomplete_manifest_path(run_id):
    return RUNS_DIR / f"{run_id}.incomplete.json"


def _resolve_available_run_id(base_run_id):
    """base_run_id (already microsecond-precise) is returned unchanged
    if neither its complete nor incomplete manifest file exists yet.
    Otherwise appends "-1", "-2", ... — a deterministic local counter,
    never a random suffix — until an unused run_id is found. Never
    overwrites an existing manifest of either kind.
    """
    candidate = base_run_id
    suffix = 0
    while _incomplete_manifest_path(candidate).exists() or _manifest_path(candidate).exists():
        suffix += 1
        candidate = f"{base_run_id}-{suffix}"
    return candidate


def _read_project_version():
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _read_git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def start_run(seed, modo_semente, command="main.py", target_draw=None):
    """Create and persist a new run manifest. Returns the manifest dict
    (including its run_id) — callers hold onto this to pass run_id into
    prediction records and to call complete_run() later.
    """
    started_dt = datetime.now(timezone.utc)
    run_id = _resolve_available_run_id(_run_id_from_timestamp(started_dt))
    manifest = {
        "run_id": run_id,
        "started_at": started_dt.isoformat(timespec="seconds"),
        "completed_at": None,
        "seed": seed,
        "modo_semente": modo_semente,
        "project_version": _read_project_version(),
        "git_commit": _read_git_commit(),
        "report_path": None,
        "command": command,
        "target_draw": target_draw,
        "generated_record_count": None,
    }
    atomic_write_json(_incomplete_manifest_path(manifest["run_id"]), manifest)
    return manifest


def complete_run(manifest, report_path=None, generated_record_count=None):
    """Update an existing run manifest with completion details, and
    promote it from "<run_id>.incomplete.json" to the trackable
    "<run_id>.json". Mutates and re-persists the same manifest dict
    returned by start_run().
    """
    manifest["completed_at"] = _now_iso()
    manifest["report_path"] = str(report_path) if report_path is not None else None
    manifest["generated_record_count"] = generated_record_count
    atomic_write_json(_manifest_path(manifest["run_id"]), manifest)
    try:
        _incomplete_manifest_path(manifest["run_id"]).unlink()
    except FileNotFoundError:
        pass
    return manifest


def load_run(run_id):
    if not run_id:
        return None
    manifest = read_json(_manifest_path(run_id), default=None)
    if manifest is not None:
        return manifest
    return read_json(_incomplete_manifest_path(run_id), default=None)


def load_all_runs():
    """Returns {run_id: manifest} for every persisted run manifest,
    complete or incomplete. The glob "RUN-*.json" already matches both
    "RUN-<id>.json" and "RUN-<id>.incomplete.json" — both end in ".json".
    """
    if not RUNS_DIR.is_dir():
        return {}
    out = {}
    for path in RUNS_DIR.glob("RUN-*.json"):
        manifest = read_json(path, default=None)
        if manifest and manifest.get("run_id"):
            out[manifest["run_id"]] = manifest
    return out
