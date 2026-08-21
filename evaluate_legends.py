"""Legend Evaluation Engine CLI.

    python evaluate_legends.py
    python evaluate_legends.py --dry-run

Aggregates every already-registered Hero (library/heroes/entries/) by
their draw-independent source_prediction_id and promotes qualifying
identities to permanent Legend records in library/legends/. Legends are
only ever created here — never during simulation, never during Hero
evaluation, never from raw predictions in arquivo_destino.json.
Promotion is permanent: once created, a Legend's founding fields are
frozen forever, regardless of future config changes or additional
Heroes accumulating for the same identity. Nothing is ever deleted,
demoted, or silently re-derived.

Execution is split into two phases:
  preflight — every read happens here (one LegendRegistry.load_all(),
              one HeroRegistry.load_all()), and a full execution plan
              plus the resulting projected Legend state are computed
              purely in memory. No disk write of any kind happens in
              this phase, including for --dry-run.
  apply     — only entered when NOT --dry-run. Executes the plan
              (register()/refresh()) and then rebuilds the index. Any
              LegendIntegrityError/LegendAlreadyExistsError raised here
              — including from rebuild_index()'s own internal
              load_all() — aborts with a non-zero exit code and an
              explicit statement of how many operations were already
              written, never a silent partial success. Writing the
              human-readable report file is protected the same way,
              though by that point the registry itself is already
              durably persisted — only the report text could still fail
              to save.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from configuration import load_config
from core.services.legend_evaluation import (
    LegendConfigError,
    load_legend_config,
    group_heroes_by_source_prediction,
    evaluate_group,
    would_change,
)
from library.heroes.registry import HeroRegistry
from library.legends.registry import LegendRegistry, LegendIntegrityError, LegendAlreadyExistsError

VERSION_FILE = Path("VERSION")

# Module-level so tests can redirect it (patch.object(evaluate_legends,
# "REPORT_PATH", tmp_path)), exactly like HeroRegistry/LegendRegistry
# below — never hardcoded inline inside main().
REPORT_PATH = Path("experiments/reports/generated") / "legends_evaluation.txt"


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


def preflight(heroes, legend_config, project_version, git_commit, existing_legends, promoted_at):
    """Pure — no disk I/O. existing_legends is the result of a single,
    already-completed LegendRegistry.load_all() call; every "does this
    already exist" lookup below uses that in-memory map, never a fresh
    read, so this function cannot itself raise a registry error.

    Returns a plan (list of pending operations) and projected_by_source
    — the full Legend state (existing + promoted + refreshed) IF the
    plan were applied, without applying it. Legends whose
    source_prediction_id has no group in the currently loaded Heroes are
    seeded into projected_by_source from existing_by_source and never
    touched — they are never dropped from the picture.

    promoted_new / refreshed_existing / unchanged_existing are three
    distinct concepts, not one number derived ad hoc from another:
      promoted_new       — identities with no prior Legend that just
                            crossed their first threshold this run.
      refreshed_existing  — identities that already had a Legend and
                            whose accumulative fields actually changed.
      unchanged_existing  — every OTHER already-existing Legend: exactly
                            len(existing_by_source) - refreshed_existing.
    """
    existing_by_source = {l["source_prediction_id"]: l for l in existing_legends}
    projected_by_source = dict(existing_by_source)
    groups = group_heroes_by_source_prediction(heroes)

    plan = []
    not_yet_qualified = []

    for source_prediction_id, heroes_in_group in sorted(groups.items()):
        existing = existing_by_source.get(source_prediction_id)
        decision = evaluate_group(
            source_prediction_id, heroes_in_group, legend_config,
            existing, project_version, git_commit, promoted_at,
        )

        if decision["action"] == "not_yet_qualified":
            not_yet_qualified.append(source_prediction_id)

        elif decision["action"] == "promote":
            plan.append({"op": "promote", "source_prediction_id": source_prediction_id, "record": decision["record"]})
            projected_by_source[source_prediction_id] = decision["record"]

        elif decision["action"] == "refresh_candidate":
            updates = decision["updates"]
            if would_change(existing, updates):
                plan.append({"op": "refresh", "source_prediction_id": source_prediction_id, "updates": updates})
                projected_by_source[source_prediction_id] = {**existing, **updates}
            # else: no real change — projected_by_source already holds
            # `existing` untouched from the initial copy, no plan entry.

    promoted_new = sum(1 for op in plan if op["op"] == "promote")
    refreshed_existing = sum(1 for op in plan if op["op"] == "refresh")
    unchanged_existing = len(existing_by_source) - refreshed_existing

    return {
        "plan": plan,
        "projected_by_source": projected_by_source,
        "not_yet_qualified": not_yet_qualified,
        "groups_count": len(groups),
        "promoted_new": promoted_new,
        "refreshed_existing": refreshed_existing,
        "unchanged_existing": unchanged_existing,
    }


def main():
    parser = argparse.ArgumentParser(description="Promote qualifying Heroes to permanent Legends.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compute and print the exact same plan/projected state as a real run, without writing entries, the index, or the report file.",
    )
    args = parser.parse_args()

    cfg = load_config("config.txt")
    try:
        legend_config = load_legend_config(cfg)
    except LegendConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # One "now" for this entire run — every refresh() and rebuild_index()
    # call below reuses exactly this value.
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    project_version = _read_project_version()
    git_commit = _read_git_commit()

    legend_registry = LegendRegistry()

    # -- preflight: every read happens here, nothing is written ---------
    try:
        existing_legends = legend_registry.load_all()
    except LegendIntegrityError as e:
        print(f"Legend registry integrity error while loading existing Legends: {e}")
        print("Aborting before any evaluation — nothing was written.")
        sys.exit(1)

    heroes = HeroRegistry().load_all()
    result = preflight(heroes, legend_config, project_version, git_commit, existing_legends, now)
    plan = result["plan"]
    projected_by_source = result["projected_by_source"]

    # -- apply: only real writes happen here, only when not --dry-run ---
    applied = []
    if not args.dry_run:
        try:
            for operation in plan:
                if operation["op"] == "promote":
                    stored = legend_registry.register(operation["record"])
                    applied.append(("promoted", stored))
                elif operation["op"] == "refresh":
                    stored, changed = legend_registry.refresh(
                        operation["source_prediction_id"], operation["updates"], now,
                    )
                    applied.append(("refreshed" if changed else "unchanged", stored))
            legend_registry.rebuild_index(now, tier_order=legend_config["tier_order"])
        except (LegendIntegrityError, LegendAlreadyExistsError) as e:
            print(f"Legend registry error while applying the plan: {e}")
            print(
                f"{len(applied)} of {len(plan)} planned operations were written before this failure. "
                "The index was NOT rebuilt. Treat library/legends/ as needing manual inspection, "
                "not as a completed evaluation."
            )
            sys.exit(1)

    # -- report: identical shape for dry-run and real runs, built from --
    # -- projected_by_source, which already reflects the full plan ------
    ranked = LegendRegistry.rank(list(projected_by_source.values()), legend_config["tier_order"])

    lines = [
        "=" * 60,
        "LEGEND EVALUATION" + ("  [DRY RUN — nothing written]" if args.dry_run else ""),
        "=" * 60,
        "",
        f"criteria_version: {legend_config['criteria_version']}",
        f"limiares: {legend_config['thresholds']}",
        "",
        f"Heroes considered: {len(heroes)} across {result['groups_count']} distinct predictions",
        f"Legends known before this run: {len(existing_legends)}",
        "",
        f"Promoted (new):        {result['promoted_new']}",
        f"Refreshed (existing):  {result['refreshed_existing']}",
        f"Unchanged (existing):  {result['unchanged_existing']}",
        f"Not yet qualified:     {len(result['not_yet_qualified'])}",
        "",
        f"Total Legends (projected): {len(projected_by_source)}",
        "",
    ]

    if ranked:
        lines.append("Legends, by tier:")
        current_tier = None
        for l in ranked:
            if l["promotion_tier"] != current_tier:
                current_tier = l["promotion_tier"]
                lines.append(f"  [{current_tier}]")
            lines.append(
                f"    {l['legend_id']} | {l['entity_name']} | {l['race']} | "
                f"qualified_draws={l['qualified_draws']} | provenance={l['provenance']} | "
                f"promoted at {l['promotion_draw']} ({l['promotion_draw_date']})"
            )

    report_text = "\n".join(lines)
    print(report_text)

    if not args.dry_run:
        out_path = REPORT_PATH
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report_text, encoding="utf-8")
        except OSError as e:
            print(f"Failed to write report to {out_path}: {e}")
            print(
                "The Legend registry (entries/ and the index) already completed successfully before "
                "this failure — only the human-readable report file failed to save."
            )
            sys.exit(1)
        print()
        print("Saved to:", out_path)


if __name__ == "__main__":
    main()
