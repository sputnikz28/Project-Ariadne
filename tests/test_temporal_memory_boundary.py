"""Tests for core/services/temporal_memory_boundary.py (Commit 24) and
its two forward-only consumers: orders/black_squad/black_mages.py:
tentar_ressuscitar_lenda() (legacy Legends, registado_em) and
evaluate_heroes.py:build_hero_record() (new Heroes, recognized_at).
All fixtures are synthetic; no real persistent-memory file is read or
written by any test here.
"""

import configparser
import random
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from core.services.temporal_memory_boundary import (
    classify_memory_availability,
    temporal_memory_view,
)

CUTOFF = datetime(2099, 6, 1, tzinfo=timezone.utc)
BEFORE = (CUTOFF - timedelta(days=1)).isoformat()
AFTER = (CUTOFF + timedelta(days=1)).isoformat()


class TestClassifyMemoryAvailability(unittest.TestCase):
    def test_before_cutoff_is_verified(self):
        self.assertEqual(classify_memory_availability(BEFORE, CUTOFF), "verified")

    def test_exactly_at_cutoff_is_ineligible(self):
        self.assertEqual(classify_memory_availability(CUTOFF.isoformat(), CUTOFF), "ineligible")

    def test_after_cutoff_is_ineligible(self):
        self.assertEqual(classify_memory_availability(AFTER, CUTOFF), "ineligible")

    def test_missing_timestamp_is_legacy(self):
        self.assertEqual(classify_memory_availability(None, CUTOFF), "legacy")

    def test_malformed_timestamp_is_unresolved(self):
        self.assertEqual(classify_memory_availability("not-a-timestamp", CUTOFF), "unresolved")

    def test_naive_timestamp_is_unresolved(self):
        self.assertEqual(classify_memory_availability("2099-01-01T00:00:00", CUTOFF), "unresolved")

    def test_naive_cutoff_raises(self):
        with self.assertRaises(ValueError):
            classify_memory_availability(BEFORE, datetime(2099, 6, 1))


class TestTemporalMemoryView(unittest.TestCase):
    def _by_ts(self, ts):
        return lambda r: r

    def test_default_view_is_verified_only(self):
        records = {"verified": BEFORE, "legacy": None, "unresolved": "bad", "ineligible": AFTER}
        result = temporal_memory_view(
            list(records.keys()), CUTOFF, get_raw_timestamp=lambda k: records[k],
        )
        self.assertEqual(result, ("verified",))

    def test_allow_legacy_includes_legacy_only(self):
        records = {"verified": BEFORE, "legacy": None, "unresolved": "bad", "ineligible": AFTER}
        result = temporal_memory_view(
            list(records.keys()), CUTOFF, get_raw_timestamp=lambda k: records[k], allow_legacy=True,
        )
        self.assertEqual(set(result), {"verified", "legacy"})

    def test_allow_unresolved_includes_unresolved_only(self):
        records = {"verified": BEFORE, "legacy": None, "unresolved": "bad", "ineligible": AFTER}
        result = temporal_memory_view(
            list(records.keys()), CUTOFF, get_raw_timestamp=lambda k: records[k], allow_unresolved=True,
        )
        self.assertEqual(set(result), {"verified", "unresolved"})

    def test_ineligible_never_included_even_with_both_overrides(self):
        records = {"verified": BEFORE, "legacy": None, "unresolved": "bad", "ineligible": AFTER}
        result = temporal_memory_view(
            list(records.keys()), CUTOFF, get_raw_timestamp=lambda k: records[k],
            allow_legacy=True, allow_unresolved=True,
        )
        self.assertNotIn("ineligible", result)
        self.assertEqual(set(result), {"verified", "legacy", "unresolved"})

    def test_identical_content_different_available_at_only_valid_one_included(self):
        record_old = {"content": "X", "ts": BEFORE}
        record_new = {"content": "X", "ts": AFTER}
        result = temporal_memory_view(
            [record_old, record_new], CUTOFF, get_raw_timestamp=lambda r: r["ts"],
        )
        self.assertEqual(result, (record_old,))

    def test_order_preserved(self):
        records = [{"ts": BEFORE, "i": i} for i in range(3)]
        result = temporal_memory_view(records, CUTOFF, get_raw_timestamp=lambda r: r["ts"])
        self.assertEqual([r["i"] for r in result], [0, 1, 2])

    def test_does_not_mutate_input(self):
        records = [{"ts": BEFORE}, {"ts": AFTER}]
        before = [dict(r) for r in records]
        temporal_memory_view(records, CUTOFF, get_raw_timestamp=lambda r: r["ts"])
        self.assertEqual(records, before)

    def test_altering_future_records_does_not_change_pre_cutoff_view(self):
        shared = {"id": "A", "ts": BEFORE}
        future_a = {"id": "B", "ts": AFTER, "payload": "original"}
        future_b = {"id": "B", "ts": AFTER, "payload": "completely different"}
        view_a = temporal_memory_view([shared, future_a], CUTOFF, get_raw_timestamp=lambda r: r["ts"])
        view_b = temporal_memory_view([shared, future_b], CUTOFF, get_raw_timestamp=lambda r: r["ts"])
        self.assertEqual(view_a, view_b)
        self.assertEqual(view_a, (shared,))


class TestUncertifiedModulesNeverClaimTemporalCertification(unittest.TestCase):
    """Grimório/estado da Ordem Élfica/Artefactos continuam sem
    contrato temporal — provado por ausência de import, não só
    documentado.
    """

    UNCERTIFIED_FILES = (
        "artifacts/living.py",
        "artifacts/ark.py",
        "orders/black_squad/persistence.py",
        "orders/elven_order/ninjas.py",
    )

    def test_uncertified_modules_never_import_temporal_memory_boundary(self):
        for rel_path in self.UNCERTIFIED_FILES:
            with self.subTest(path=rel_path):
                source = Path(rel_path).read_text(encoding="utf-8")
                self.assertNotIn("temporal_memory_boundary", source)


# ---------------------------------------------------------------------------
# Necromancy — orders/black_squad/black_mages.py:tentar_ressuscitar_lenda()
# ---------------------------------------------------------------------------

from orders.black_squad import black_mages  # noqa: E402


def make_config(chance_ressuscitar_lenda=1.0):
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        "LENDAS": {"permitir_necromancia": "true"},
        "ESQUADRAO_NEGRO": {"chance_ressuscitar_lenda": str(chance_ressuscitar_lenda)},
    })
    return cfg


def make_lenda(nome="Testauro Eclipse", registado_em=None):
    return {
        "nome": nome,
        "origem": "racas_antigas",
        "chave": {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
        "registado_em": registado_em,
    }


class _NecromancyHarness(unittest.TestCase):
    """Mocks every persistent side effect (grimoire load/save, ritual
    archive save, and the two docs/lore/legends/*.json reads) so no
    test here ever touches real repository state.
    """

    def setUp(self):
        self.grimoire = {"conhecimento": {"historico": True}, "lendas_ressuscitadas": []}
        self._candidates = {"personagens": [], "ecos": {"ecos": []}}

        self.patches = [
            mock.patch.object(black_mages, "load_grimoire", return_value=self.grimoire),
            mock.patch.object(black_mages, "save_grimoire"),
            mock.patch.object(black_mages, "save"),
            mock.patch.object(black_mages, "ler_json", side_effect=self._fake_ler_json),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def _fake_ler_json(self, path, default):
        if "livro_personagens_lendarias" in path:
            return {"personagens": self._personagens}
        if "ecos_ancestrais" in path:
            return {"ecos": []}
        return default

    def set_personagens(self, personagens):
        self._personagens = personagens


class TestNecromancyLiveModeUnchanged(_NecromancyHarness):
    def test_cutoff_none_ignores_registado_em_entirely(self):
        # a single candidate whose registado_em is deep in the future —
        # LIVE mode must still be able to resurrect it, proving it never
        # filters when cutoff_datetime is not given.
        self.set_personagens([make_lenda(registado_em=AFTER)])
        eco = black_mages.tentar_ressuscitar_lenda(make_config(), [], cutoff_datetime=None)
        self.assertIsNotNone(eco)
        self.assertEqual(eco["nome"], "Testauro Eclipse Eclipse")


class TestNecromancyTemporalMode(_NecromancyHarness):
    def test_legend_promoted_after_cutoff_is_never_resurrected(self):
        self.set_personagens([make_lenda(registado_em=AFTER)])
        eco = black_mages.tentar_ressuscitar_lenda(make_config(), [], cutoff_datetime=CUTOFF)
        self.assertIsNone(eco)

    def test_legend_promoted_before_cutoff_can_be_resurrected(self):
        self.set_personagens([make_lenda(registado_em=BEFORE)])
        eco = black_mages.tentar_ressuscitar_lenda(make_config(), [], cutoff_datetime=CUTOFF)
        self.assertIsNotNone(eco)

    def test_naive_cutoff_raises_before_any_rng_gate(self):
        self.set_personagens([make_lenda(registado_em=BEFORE)])
        with mock.patch("random.random", side_effect=AssertionError("RNG gate must not run before cutoff validation")):
            with self.assertRaises(ValueError):
                black_mages.tentar_ressuscitar_lenda(make_config(), [], cutoff_datetime=datetime(2099, 6, 1))

    def test_rng_call_count_is_the_same_regardless_of_pool_size(self):
        # Formulated as call-count parity, not equal outcomes: a smaller
        # (temporally-filtered) pool must consume random.random()/
        # random.choice()/random.uniform() the same number of times as
        # the full pool — never zero extra, never a skipped call.
        def run_and_count(personagens, cutoff_datetime):
            self.set_personagens(personagens)
            counts = {"random": 0, "choice": 0, "uniform": 0}

            def counted(name, real):
                def wrapper(*a, **kw):
                    counts[name] += 1
                    return real(*a, **kw)
                return wrapper

            with mock.patch("random.random", side_effect=counted("random", random.random)), \
                 mock.patch("random.choice", side_effect=counted("choice", random.choice)), \
                 mock.patch("random.uniform", side_effect=counted("uniform", random.uniform)):
                eco = black_mages.tentar_ressuscitar_lenda(make_config(), [], cutoff_datetime=cutoff_datetime)
            return eco, counts

        eco_full, counts_full = run_and_count(
            [make_lenda("A", BEFORE), make_lenda("B", BEFORE), make_lenda("C", BEFORE)], None,
        )
        eco_filtered, counts_filtered = run_and_count(
            [make_lenda("A", BEFORE), make_lenda("B", AFTER), make_lenda("C", AFTER)], CUTOFF,
        )
        self.assertIsNotNone(eco_full)
        self.assertIsNotNone(eco_filtered)
        self.assertEqual(counts_full, counts_filtered)


# ---------------------------------------------------------------------------
# recognized_at — evaluate_heroes.py:build_hero_record()
# ---------------------------------------------------------------------------

import evaluate_heroes  # noqa: E402


class TestRecognizedAtPropagation(unittest.TestCase):
    def test_recognized_at_is_propagated_verbatim_into_the_hero_record(self):
        result = {
            "hero_id": "HERO-2099-001-abcd1234", "dedup_hash": "abcd1234",
            "source_prediction_id": "sp-1", "entity_id": "H-1", "entity_name": "Test",
            "race": "Elfo", "generation": 1, "run_id": None, "provenance": "legacy",
            "predicted_numeros": [1, 2, 3, 4, 5], "predicted_estrelas": [1, 2],
            "matched_numbers": [1], "matched_stars": [], "missed_numbers": [2, 3, 4, 5],
            "missed_stars": [1, 2], "extra_numbers": [], "extra_stars": [],
            "category": "1+0", "tier": "TIER_5", "simulation_score": 10,
        }
        draw = {"numero_sorteio": "001/2099", "data": "2099-01-01", "chave": {"numeros": [2, 3, 4, 5, 6], "estrelas": [1, 2]}}
        recognized_at = "2099-06-15T12:00:00+00:00"

        record = evaluate_heroes.build_hero_record(result, draw, Path("fake.json"), None, recognized_at)

        self.assertEqual(record["recognized_at"], recognized_at)


if __name__ == "__main__":
    unittest.main()
