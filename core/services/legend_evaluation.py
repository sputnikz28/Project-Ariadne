"""Legend Evaluation Engine — deterministic, side-effect-free aggregation
of already-registered Heroes (library/heroes/entries/) into permanent
Legend promotions.

A Legend is never derived from a raw prediction and never derived from a
single draw. It only exists once the same source_prediction_id has been
recognised as a Hero across multiple official draws, per the thresholds
in [REGISTO_LENDAS]/[REGISTO_LENDAS_TIERS].

Never touches disk directly (callers pass in already-loaded Hero
records); the only exception is config validation, which reads the
ConfigParser object the caller already loaded. Never imports random or
secrets — qualification depends only on chronological draw membership,
never on simulation_score, entity_name, or evaluation order.
"""


class LegendConfigError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_legend_config(cfg):
    """Parse and validate [REGISTO_LENDAS] / [REGISTO_LENDAS_TIERS] from
    config.txt.

    Raises LegendConfigError on any inconsistency — never silently
    ignores a malformed threshold or an unmapped tier in either
    direction: every threshold in `limiares` must have a tier, and every
    tier entry must correspond to a threshold actually listed in
    `limiares` (no dead/orphaned configuration).
    """
    if not cfg.has_section("REGISTO_LENDAS"):
        raise LegendConfigError("config.txt is missing [REGISTO_LENDAS] section")

    criteria_version = cfg.get("REGISTO_LENDAS", "criteria_version", fallback="").strip()
    if not criteria_version:
        raise LegendConfigError("config.txt [REGISTO_LENDAS] criteria_version is empty or missing")

    raw = cfg.get("REGISTO_LENDAS", "limiares", fallback="")
    raw_thresholds = [t.strip() for t in raw.split(",") if t.strip()]
    if not raw_thresholds:
        raise LegendConfigError("config.txt [REGISTO_LENDAS] limiares is empty or missing")

    thresholds = []
    seen = set()
    for raw_t in raw_thresholds:
        if not raw_t.isdigit() or int(raw_t) <= 0:
            raise LegendConfigError(f"invalid threshold in [REGISTO_LENDAS] limiares: {raw_t!r} (must be a positive integer)")
        t = int(raw_t)
        if t in seen:
            raise LegendConfigError(f"duplicate threshold in [REGISTO_LENDAS] limiares: {t!r}")
        seen.add(t)
        thresholds.append(t)

    if not cfg.has_section("REGISTO_LENDAS_TIERS"):
        raise LegendConfigError("config.txt is missing [REGISTO_LENDAS_TIERS] section")

    tier_map = {}
    for raw_key, raw_tier in cfg.items("REGISTO_LENDAS_TIERS"):
        raw_key = raw_key.strip()
        tier = raw_tier.strip()
        if not raw_key.isdigit() or int(raw_key) <= 0:
            raise LegendConfigError(f"invalid threshold key in [REGISTO_LENDAS_TIERS]: {raw_key!r}")
        if not tier:
            raise LegendConfigError(f"empty tier for threshold {raw_key!r} in [REGISTO_LENDAS_TIERS]")
        tier_map[int(raw_key)] = tier

    thresholds_set = set(thresholds)
    for t in thresholds:
        if t not in tier_map:
            raise LegendConfigError(f"threshold {t!r} in [REGISTO_LENDAS] limiares has no tier mapping in [REGISTO_LENDAS_TIERS]")
    for t in tier_map:
        if t not in thresholds_set:
            raise LegendConfigError(
                f"[REGISTO_LENDAS_TIERS] has threshold {t!r} with no corresponding entry in "
                f"[REGISTO_LENDAS] limiares — remove it or add {t!r} to limiares"
            )

    # Rank tiers best-first by descending threshold (a higher bar cleared
    # is rarer/better); first-seen tier at a given rank wins so repeated
    # tiers (e.g. two thresholds both mapping to the same top tier)
    # collapse to one rank.
    tier_order = {}
    for t in sorted(thresholds, reverse=True):
        tier = tier_map[t]
        if tier not in tier_order:
            tier_order[tier] = len(tier_order)

    return {
        "criteria_version": criteria_version,
        "thresholds": sorted(thresholds),
        "tier_map": tier_map,
        "tier_order": tier_order,
    }


# ---------------------------------------------------------------------------
# Grouping — Legends are keyed by the same draw-independent identity Heroes
# already carry (source_prediction_id), never by hero_id (which is
# per-draw) and never by entity_name/entity_id (unstable, as established
# for Heroes in V12).
# ---------------------------------------------------------------------------

def group_heroes_by_source_prediction(heroes):
    groups = {}
    for hero in heroes:
        groups.setdefault(hero["source_prediction_id"], []).append(hero)
    return groups


def compute_conservative_provenance(heroes_in_group):
    """"verified" only if every contributing Hero is verified; "legacy"
    if any single one is legacy. Structurally, heroes_in_group can never
    contain "ineligible"/"unresolved" — HeroRegistry never stores those.
    """
    if all(h["provenance"] == "verified" for h in heroes_in_group):
        return "verified"
    return "legacy"


def legend_display_id(source_prediction_id):
    # source_prediction_id is already a sha256 digest — reuse it
    # directly, exactly as hero_display_id reuses dedup_hash, rather
    # than hashing it a second time.
    return "LEGEND-" + source_prediction_id[:8]


# ---------------------------------------------------------------------------
# Chronological first-promotion detection (regras (a) e (b))
#
# promotion_draw / promotion_draw_date / promotion_threshold /
# promotion_tier / promotion_hero_ids are derived exclusively from the
# real chronology of official draws (draw_date, with draw_id as a
# deterministic tie-break for same-date draws) — never from the order in
# which evaluate_legends.py happens to run, and never from a shortcut
# like min(thresholds) applied after the fact. The walk below reuses the
# exact same "was a threshold crossed at this step" check at every step,
# so it would keep working correctly even if a future criterion stopped
# being a simple monotonic draw count.
#
# promotion_draw_date is a plain "YYYY-MM-DD" date (the historical
# dataset's own "data" field, propagated onto every Hero record as
# draw_date) — not a full timestamp. No hour/timezone is invented here.
# ---------------------------------------------------------------------------

def _threshold_reached(distinct_draw_count_so_far, legend_config):
    """Returns the threshold reached exactly at this step, or None.

    Only returns a value when distinct_draw_count_so_far is itself one
    of the configured thresholds — not "the smallest threshold already
    satisfied by now". That distinction matters: this function must be
    correct standalone, independent of being called from a loop that
    stops at the first non-None result. Because find_first_promotion()
    advances the walk by exactly one distinct draw per step, at most one
    threshold can be newly reached at any given step anyway, so this is
    never ambiguous.
    """
    if distinct_draw_count_so_far in legend_config["thresholds"]:
        return distinct_draw_count_so_far
    return None


def find_first_promotion(heroes_in_group, legend_config):
    """Walks the group's distinct draws in real chronological order and
    returns the first step that reaches a configured threshold — i.e.
    the first chronological moment this identity ever qualified.

    Returns None if the group's current membership never qualifies.
    Otherwise returns a dict: promotion_draw, promotion_draw_date,
    promotion_threshold, promotion_tier, promotion_hero_ids (sorted,
    exactly the Heroes of the draws up to and including the qualifying
    one — not every Hero present at evaluation time).
    """
    by_draw = {}
    for hero in heroes_in_group:
        by_draw.setdefault(hero["draw_id"], []).append(hero)

    distinct_draws = sorted(
        by_draw.keys(),
        key=lambda draw_id: (by_draw[draw_id][0]["draw_date"], draw_id),
    )

    for k in range(1, len(distinct_draws) + 1):
        threshold = _threshold_reached(k, legend_config)
        if threshold is not None:
            promotion_draw = distinct_draws[k - 1]
            promotion_draw_date = by_draw[promotion_draw][0]["draw_date"]
            prefix_draw_ids = set(distinct_draws[:k])
            promotion_hero_ids = sorted(
                h["hero_id"] for h in heroes_in_group if h["draw_id"] in prefix_draw_ids
            )
            return {
                "promotion_draw": promotion_draw,
                "promotion_draw_date": promotion_draw_date,
                "promotion_threshold": threshold,
                "promotion_tier": legend_config["tier_map"][threshold],
                "promotion_hero_ids": promotion_hero_ids,
            }
    return None


# ---------------------------------------------------------------------------
# Representative entity fields — deterministic, chosen from the founding
# evidence (promotion_hero_ids), never from the full current group, since
# these fields are frozen at promotion.
# ---------------------------------------------------------------------------

def _representative_hero(heroes_in_group, promotion_hero_ids):
    candidates = [h for h in heroes_in_group if h["hero_id"] in set(promotion_hero_ids)]
    return min(candidates, key=lambda h: h["hero_id"])


# ---------------------------------------------------------------------------
# Accumulative fields — recomputed from the full, current group every run.
# ---------------------------------------------------------------------------

def compute_accumulative_fields(heroes_in_group):
    distinct_draw_ids = {h["draw_id"] for h in heroes_in_group}
    return {
        "hero_count": len(heroes_in_group),
        "qualified_draws": len(distinct_draw_ids),
        "contributing_hero_ids": sorted(h["hero_id"] for h in heroes_in_group),
        "provenance": compute_conservative_provenance(heroes_in_group),
    }


def would_change(existing_legend, updates):
    return any(existing_legend.get(k) != v for k, v in updates.items())


# ---------------------------------------------------------------------------
# Full evaluation of one group (pure — no disk I/O)
# ---------------------------------------------------------------------------

def evaluate_group(source_prediction_id, heroes_in_group, legend_config,
                    existing_legend, project_version, git_commit):
    """Decide what should happen to one source_prediction_id group.

    Returns one of:
      {"action": "not_yet_qualified"}
      {"action": "promote", "record": {...}}
      {"action": "refresh_candidate", "updates": {...}}
    """
    if existing_legend is None:
        promotion = find_first_promotion(heroes_in_group, legend_config)
        if promotion is None:
            return {"action": "not_yet_qualified"}

        rep = _representative_hero(heroes_in_group, promotion["promotion_hero_ids"])
        accumulative = compute_accumulative_fields(heroes_in_group)

        record = {
            "legend_id": legend_display_id(source_prediction_id),
            "source_prediction_id": source_prediction_id,

            "promotion_draw": promotion["promotion_draw"],
            "promotion_draw_date": promotion["promotion_draw_date"],
            "promotion_threshold": promotion["promotion_threshold"],
            "promotion_tier": promotion["promotion_tier"],
            "criteria_version": legend_config["criteria_version"],
            "promotion_hero_ids": promotion["promotion_hero_ids"],
            "project_version": project_version,
            "git_commit": git_commit,
            "qualification_reason": (
                f"Promoted to Legend at draw {promotion['promotion_draw']} "
                f"({promotion['promotion_draw_date']}) by reaching "
                f"{promotion['promotion_threshold']} distinct qualifying draws as Hero "
                f"(criteria_version: {legend_config['criteria_version']})."
            ),

            "entity_id": rep["entity_id"],
            "entity_name": rep["entity_name"],
            "race": rep["race"],
            "generation": rep["generation"],
            "predicted_numeros": rep["predicted_key"]["numeros"],
            "predicted_estrelas": rep["predicted_key"]["estrelas"],

            **accumulative,
            "last_reevaluated_at": None,
        }
        return {"action": "promote", "record": record}

    updates = compute_accumulative_fields(heroes_in_group)
    return {"action": "refresh_candidate", "updates": updates}


# ---------------------------------------------------------------------------
# Auditability — mirrors hero_evaluation.py's summarize_deduplication()
# ---------------------------------------------------------------------------

def summarize_legend_evaluation(decisions):
    """decisions: iterable of the dicts returned by evaluate_group()."""
    summary = {"groups_evaluated": 0, "not_yet_qualified": 0, "promote_candidates": 0, "refresh_candidates": 0}
    for d in decisions:
        summary["groups_evaluated"] += 1
        if d["action"] == "not_yet_qualified":
            summary["not_yet_qualified"] += 1
        elif d["action"] == "promote":
            summary["promote_candidates"] += 1
        elif d["action"] == "refresh_candidate":
            summary["refresh_candidates"] += 1
    return summary
