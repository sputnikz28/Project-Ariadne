"""Hero Evaluation Engine — deterministic, side-effect-free classification
of archived predictions against one official draw.

Never consumes random numbers. Never touches disk directly (callers pass
in already-loaded data); the only exception is config validation, which
reads the ConfigParser object the caller already loaded.

Recognition uses exact matched-number/matched-star counts only.
simulation_score is computed for display but never influences
qualification, tier, category, ranking or deduplication — enforced
structurally: score is computed in a separate function that classification
never calls into.
"""

import hashlib
import json
import re
from collections import Counter
from datetime import datetime

CATEGORY_PATTERN = re.compile(r"^([0-5])\+([0-2])$")


class HeroConfigError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_hero_config(cfg):
    """Parse and validate [HEROIS] / [HEROIS_TIERS] from config.txt.

    Raises HeroConfigError on any inconsistency — never silently ignores
    a malformed category or an unmapped tier.
    """
    if not cfg.has_section("HEROIS"):
        raise HeroConfigError("config.txt is missing [HEROIS] section")

    raw = cfg.get("HEROIS", "categorias", fallback="")
    raw_categories = [c.strip() for c in raw.split(",") if c.strip()]
    incluir_2_0 = cfg.getboolean("HEROIS", "incluir_2_0", fallback=False)

    if not raw_categories:
        raise HeroConfigError("config.txt [HEROIS] categorias is empty or missing")

    seen = set()
    for cat in raw_categories:
        if not CATEGORY_PATTERN.match(cat):
            raise HeroConfigError(f"invalid category syntax in [HEROIS] categorias: {cat!r}")
        if cat in seen:
            raise HeroConfigError(f"duplicate category in [HEROIS] categorias: {cat!r}")
        seen.add(cat)
        if cat == "2+0":
            raise HeroConfigError(
                "'2+0' must not be listed directly in categorias — enable it via incluir_2_0=true instead"
            )

    enabled_categories = list(raw_categories)
    if incluir_2_0:
        enabled_categories.append("2+0")

    if not cfg.has_section("HEROIS_TIERS"):
        raise HeroConfigError("config.txt is missing [HEROIS_TIERS] section")

    tier_map = {}
    for cat, tier in cfg.items("HEROIS_TIERS"):
        cat = cat.strip()
        tier = tier.strip()
        if not CATEGORY_PATTERN.match(cat):
            raise HeroConfigError(f"invalid category syntax in [HEROIS_TIERS]: {cat!r}")
        if not tier:
            raise HeroConfigError(f"empty tier for category {cat!r} in [HEROIS_TIERS]")
        tier_map[cat] = tier

    for cat in enabled_categories:
        if cat not in tier_map:
            raise HeroConfigError(f"enabled category {cat!r} has no tier mapping in [HEROIS_TIERS]")

    tier_order = {}
    for tier in tier_map.values():
        if tier not in tier_order:
            tier_order[tier] = len(tier_order)

    return {
        "enabled_categories": set(enabled_categories),
        "tier_map": tier_map,
        "tier_order": tier_order,
        "incluir_2_0": incluir_2_0,
    }


# ---------------------------------------------------------------------------
# Recognition (matched numbers/stars only)
# ---------------------------------------------------------------------------

def matched_values(predicted_numbers, predicted_stars, official_numbers, official_stars):
    matched_n = sorted(set(predicted_numbers) & set(official_numbers))
    matched_e = sorted(set(predicted_stars) & set(official_stars))
    missed_n = sorted(set(official_numbers) - set(predicted_numbers))
    missed_e = sorted(set(official_stars) - set(predicted_stars))
    extra_n = sorted(set(predicted_numbers) - set(official_numbers))
    extra_e = sorted(set(predicted_stars) - set(official_stars))
    return {
        "matched_numbers": matched_n,
        "matched_stars": matched_e,
        "missed_numbers": missed_n,
        "missed_stars": missed_e,
        "extra_numbers": extra_n,
        "extra_stars": extra_e,
    }


def category_for(matched_n_count, matched_e_count):
    return f"{matched_n_count}+{matched_e_count}"


def simulation_score(matched_n_count, matched_e_count):
    """Reuses compare_result.py's existing score formula verbatim.
    Descriptive only — never an input to qualification/tier/ranking/dedup.
    """
    return (
        matched_n_count * 10 + matched_e_count * 5
        + (8 if matched_n_count >= 3 else 0)
        + (5 if matched_e_count == 2 else 0)
    )


# ---------------------------------------------------------------------------
# Source prediction identity (see docs discussion — best available, hashed
# from the full canonical fingerprint since no existing field is reliably
# unique on its own across all record origins)
# ---------------------------------------------------------------------------

def _canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def compute_source_prediction_id(record):
    fingerprint = {
        "origem": record.get("origem"),
        "id": record.get("id"),
        "geracao": record.get("geracao"),
        "numeros": sorted(record.get("numeros", [])),
        "estrelas": sorted(record.get("estrelas", [])),
        "classe": record.get("classe"),
        "casa": record.get("casa"),
    }
    return hashlib.sha256(_canonical_json(fingerprint).encode("utf-8")).hexdigest()


def compute_dedup_hash(draw_id, source_prediction_id):
    return hashlib.sha256(_canonical_json({
        "draw_id": draw_id,
        "source_prediction_id": source_prediction_id,
    }).encode("utf-8")).hexdigest()


def hero_display_id(draw_id, dedup_hash):
    # draw_id looks like "056/2026" -> "HERO-2026-056-<8 hex>"
    num, year = draw_id.split("/")
    return f"HERO-{year}-{num}-{dedup_hash[:8]}"


# ---------------------------------------------------------------------------
# Temporal provenance — verified / legacy / ineligible / unresolved
# ---------------------------------------------------------------------------

def classify_temporal_provenance(record, run_manifests_by_id, official_draw_datetime):
    """Returns one of: "verified", "legacy", "ineligible", "unresolved".

    verified    — run_id resolves to a manifest completed before the draw.
    legacy      — no run_id at all: predates the provenance system entirely.
                  Permitted to become a Hero, permanently tagged legacy,
                  never auto-upgraded to verified.
    ineligible  — run_id resolves to a manifest completed AT/AFTER the draw:
                  proven too late. Never becomes a Hero, no override.
    unresolved  — a run_id is present but can't be resolved to a usable
                  manifest (missing file, missing completed_at). Distinct
                  from "legacy" — this record claims provenance-system
                  membership but we can't verify it. Excluded by default;
                  only included with the explicit CLI override.
    """
    run_id = record.get("run_id")
    if run_id is None:
        return "legacy"

    manifest = run_manifests_by_id.get(run_id)
    if manifest is None:
        return "unresolved"

    completed_at = manifest.get("completed_at")
    if not completed_at:
        return "unresolved"

    try:
        completed_dt = datetime.fromisoformat(completed_at)
    except ValueError:
        return "unresolved"

    if completed_dt < official_draw_datetime:
        return "verified"
    return "ineligible"


# ---------------------------------------------------------------------------
# Full evaluation of one record
# ---------------------------------------------------------------------------

def evaluate_record(record, draw_id, official_numbers, official_stars,
                     run_manifests_by_id, official_draw_datetime, hero_config):
    """Classify a single archive record. Returns a dict describing the
    outcome regardless of whether it qualifies as a Hero — callers decide
    what to do with non-qualifying / ineligible / unresolved results.
    """
    provenance = classify_temporal_provenance(record, run_manifests_by_id, official_draw_datetime)

    matches = matched_values(
        record.get("numeros", []), record.get("estrelas", []),
        official_numbers, official_stars,
    )
    matched_n = len(matches["matched_numbers"])
    matched_e = len(matches["matched_stars"])
    category = category_for(matched_n, matched_e)
    score = simulation_score(matched_n, matched_e)

    qualifies = category in hero_config["enabled_categories"]
    tier = hero_config["tier_map"].get(category) if qualifies else None

    source_prediction_id = compute_source_prediction_id(record)
    dedup_hash = compute_dedup_hash(draw_id, source_prediction_id)

    return {
        "source_prediction_id": source_prediction_id,
        "dedup_hash": dedup_hash,
        "hero_id": hero_display_id(draw_id, dedup_hash),
        "provenance": provenance,
        "category": category,
        "tier": tier,
        "qualifies": qualifies,
        "simulation_score": score,
        **matches,
        "run_id": record.get("run_id"),
        "entity_id": record.get("id"),
        "entity_name": record.get("nome"),
        "race": record.get("classe"),
        "generation": record.get("geracao"),
        "predicted_numeros": sorted(record.get("numeros", [])),
        "predicted_estrelas": sorted(record.get("estrelas", [])),
    }


# ---------------------------------------------------------------------------
# Deduplication summary — makes the qualifying-records vs unique-hero_id
# collapse visible and auditable instead of a silent difference between
# two report counters.
# ---------------------------------------------------------------------------

def summarize_deduplication(qualifying_results):
    """Given the list of per-record evaluate_record() outputs that passed
    the qualification/provenance filters, explain how many distinct Hero
    identities (hero_id / dedup_hash) they collapse into.

    Two qualifying records collapse into the same hero_id when they share
    identical (origem, id, geracao, numeros, estrelas, classe, casa) — i.e.
    the archive recorded the same predicted entity+key more than once
    (repeated runs, repeated generations, or a slot id reused with an
    identical prediction). This is expected archive behaviour, not data
    loss: register() treats every occurrence past the first as a no-op.

    Returns a dict with:
      qualifying_count          — len(qualifying_results)
      unique_hero_id_count      — distinct dedup_hash values
      duplicate_hero_id_groups  — how many dedup_hash values had >1 record
      collapsed_record_count    — qualifying_count - unique_hero_id_count
                                   (redundant records absorbed into an
                                   existing hero_id, not rejected/dropped)
      rejected_record_count     — always 0 today: register() has no
                                   rejection path other than duplicate
                                   prevention, which is already accounted
                                   for above.
    """
    hash_counts = Counter(r["hero_id"] for r in qualifying_results)
    unique_hero_id_count = len(hash_counts)
    duplicate_hero_id_groups = sum(1 for c in hash_counts.values() if c > 1)
    return {
        "qualifying_count": len(qualifying_results),
        "unique_hero_id_count": unique_hero_id_count,
        "duplicate_hero_id_groups": duplicate_hero_id_groups,
        "collapsed_record_count": len(qualifying_results) - unique_hero_id_count,
        "rejected_record_count": 0,
    }
