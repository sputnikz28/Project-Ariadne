"""Hero Evaluation Engine CLI.

    python evaluate_heroes.py --sorteio 056/2026
    python evaluate_heroes.py --sorteio 056/2026 --allow-unknown-provenance

Compares every archived prediction (datasets/generated/simulations/
arquivo_destino.json) against one official historical draw, classifies
each by temporal provenance (verified / legacy / ineligible / unresolved)
and recognition category, and registers qualifying Heroes into
library/heroes/. Heroes are only ever created here — never during
simulation, never at prediction time.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from configuration import load_config
from core.services.atomic_io import read_json
from core.services.historical_dataset import find_draw, validate_official_key, DrawLookupError
from core.services.run_manifest import load_all_runs
from core.services.hero_evaluation import load_hero_config, evaluate_record, summarize_deduplication, HeroConfigError
from library.heroes.registry import HeroRegistry

ARQUIVO_DESTINO = Path("datasets/generated/simulations/arquivo_destino.json")


def resolve_official_draw(sorteio_id):
    draw, dataset_path, dataset = find_draw(sorteio_id)
    validate_official_key(draw, dataset)
    draw_datetime = datetime.fromisoformat(draw["horario"]["timestamp_utc"])
    return draw, dataset_path, draw_datetime


def build_hero_record(result, draw, dataset_path, run_manifest):
    seed = run_manifest.get("seed") if run_manifest else None
    project_version = run_manifest.get("project_version") if run_manifest else None
    git_commit = run_manifest.get("git_commit") if run_manifest else None
    report_path = run_manifest.get("report_path") if run_manifest else None

    return {
        "hero_id": result["hero_id"],
        "dedup_hash": result["dedup_hash"],
        "source_prediction_id": result["source_prediction_id"],
        "entity_id": result["entity_id"],
        "entity_name": result["entity_name"],
        "race": result["race"],
        "generation": result["generation"],
        "run_id": result["run_id"],
        "provenance": result["provenance"],
        "simulation_seed": seed,
        "draw_id": draw["numero_sorteio"],
        "draw_date": draw["data"],
        "official_key": {"numeros": draw["chave"]["numeros"], "estrelas": draw["chave"]["estrelas"]},
        "predicted_key": {"numeros": result["predicted_numeros"], "estrelas": result["predicted_estrelas"]},
        "matched_numbers_count": len(result["matched_numbers"]),
        "matched_stars_count": len(result["matched_stars"]),
        "exact_matched_values": {"numeros": result["matched_numbers"], "estrelas": result["matched_stars"]},
        "missed_winning_values": {"numeros": result["missed_numbers"], "estrelas": result["missed_stars"]},
        "extra_predicted_values": {"numeros": result["extra_numbers"], "estrelas": result["extra_stars"]},
        "hero_category": result["category"],
        "hero_tier": result["tier"],
        "simulation_score": result["simulation_score"],
        "report_path": report_path,
        "project_version": project_version,
        "git_commit": git_commit,
        "dataset_path": str(dataset_path),
        "qualification_reason": (
            f"Matched {len(result['matched_numbers'])} main numbers and "
            f"{len(result['matched_stars'])} lucky stars against official draw "
            f"{draw['numero_sorteio']} (category {result['category']})."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate archived predictions against one official draw.")
    parser.add_argument("--sorteio", required=True, help="Official draw identifier, e.g. 056/2026")
    parser.add_argument(
        "--allow-unknown-provenance", action="store_true",
        help="Also evaluate records whose run_id can't be resolved to a manifest (rare; distinct from 'legacy').",
    )
    args = parser.parse_args()

    cfg = load_config("config.txt")
    try:
        hero_config = load_hero_config(cfg)
    except HeroConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    try:
        draw, dataset_path, draw_datetime = resolve_official_draw(args.sorteio)
    except DrawLookupError as e:
        print(f"Draw resolution error: {e}")
        sys.exit(1)

    official_numeros = draw["chave"]["numeros"]
    official_estrelas = draw["chave"]["estrelas"]

    archive = read_json(ARQUIVO_DESTINO, default=[])
    run_manifests = load_all_runs()

    counts = {"verified": 0, "legacy": 0, "ineligible": 0, "unresolved": 0}
    qualifying = []
    for record in archive:
        result = evaluate_record(
            record, args.sorteio, official_numeros, official_estrelas,
            run_manifests, draw_datetime, hero_config,
        )
        counts[result["provenance"]] += 1
        if not result["qualifies"]:
            continue
        if result["provenance"] == "ineligible":
            continue
        if result["provenance"] == "unresolved" and not args.allow_unknown_provenance:
            continue
        qualifying.append(result)

    dedup_summary = summarize_deduplication(qualifying)

    registry = HeroRegistry()
    new_heroes = []
    already_registered = []
    for result in qualifying:
        run_manifest = run_manifests.get(result["run_id"]) if result["run_id"] else None
        hero_record = build_hero_record(result, draw, dataset_path, run_manifest)
        stored, created = registry.register(hero_record)
        (new_heroes if created else already_registered).append(stored)

    registry.rebuild_index()

    total_evaluated = len(archive)
    total_recognised = len(new_heroes) + len(already_registered)

    lines = [
        "=" * 60,
        f"HERO EVALUATION — draw {draw['numero_sorteio']} ({draw['data']})",
        "=" * 60,
        "",
        f"Official key: {official_numeros} + {official_estrelas}",
        f"Dataset: {dataset_path}",
        "",
        f"Total archived predictions: {total_evaluated}",
        f"  verified:   {counts['verified']}",
        f"  legacy:     {counts['legacy']}",
        f"  ineligible: {counts['ineligible']} (excluded — proven to postdate the draw)",
        f"  unresolved: {counts['unresolved']} ({'included' if args.allow_unknown_provenance else 'excluded'} — broken run_id reference)",
        "",
        f"Heroes recognised: {total_recognised}",
        f"  new: {len(new_heroes)}",
        f"  already registered: {len(already_registered)}",
        "",
        f"Deduplication: {dedup_summary['qualifying_count']} qualifying records -> "
        f"{dedup_summary['unique_hero_id_count']} unique hero_id",
        f"  duplicate hero_id groups: {dedup_summary['duplicate_hero_id_groups']} "
        f"({dedup_summary['collapsed_record_count']} redundant records collapsed "
        f"— same entity/generation/key predicted more than once in the archive)",
        f"  rejected records: {dedup_summary['rejected_record_count']} "
        "(register() has no rejection path besides duplicate prevention, counted above)",
        "",
    ]

    if total_recognised:
        ranked = registry.rank(new_heroes + already_registered, hero_config["tier_order"])
        best = ranked[0]
        lines.append(f"Best category recognised: {best['hero_category']} ({best['hero_tier']}, provenance={best['provenance']})")
        lines.append(f"Highest Hero: {best['entity_name']} ({best['hero_id']})")
        lines.append("")
        lines.append("By tier, then category:")
        current_tier = None
        for h in ranked:
            if h["hero_tier"] != current_tier:
                current_tier = h["hero_tier"]
                lines.append(f"  [{current_tier}]")
            lines.append(
                f"    {h['hero_id']} | {h['entity_name']} | {h['race']} | "
                f"{h['hero_category']} | provenance={h['provenance']}"
            )

    report_text = "\n".join(lines)
    out_path = Path("experiments/reports/generated") / f"heroes_{args.sorteio.replace('/', '_')}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text, encoding="utf-8")

    print(report_text)
    print()
    print("Saved to:", out_path)


if __name__ == "__main__":
    main()
