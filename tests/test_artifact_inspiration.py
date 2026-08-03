"""Tests for core/services/artifact_inspiration.py.

Uses library/artifacts/entries/ read-only (never written to) to exercise
generate_inspiration() against the 15 real artifacts.
"""

import copy
import json
import random
import re
import unittest
from pathlib import Path

from core.services.artifact_inspiration import generate_inspiration
from core.services.artifact_registry import load_all_artifacts

ENTRIES_DIR = Path("library/artifacts/entries")

_FORBIDDEN_SUBSTRINGS = (
    "algoritmo",
    "probabilidad",
    "resultado",
    "resultados",
    "previsao",
    "previsão",
    "prever",
    "profecia",
    "numero",
    "número",
    "numeros",
    "números",
)

_DIGIT_RE = re.compile(r"\d")

_EXPECTED_STRUCTURE_KEYS = {
    "tracos_sugeridos",
    "valores",
    "contradicoes",
    "aparencia_inspirada",
    "simbolos",
    "conflito_possivel",
    "missao_possivel",
    "relacao_sugerida_com_artefacto",
}


def _load_records():
    return {r.id: r for r in load_all_artifacts(ENTRIES_DIR)}


def _all_strings(value):
    """Yield every string leaf inside a nested dict/list/tuple structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _all_strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _all_strings(v)


class TestGenerateInspirationDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _load_records()

    def test_same_record_same_seed_is_identical(self):
        record = self.records["ART-LOTUS-TRANQUILIDADE-0001"]
        first = generate_inspiration(record, 123)
        second = generate_inspiration(record, 123)
        self.assertEqual(first, second)

    def test_different_seeds_can_produce_different_results(self):
        record = self.records["ART-CODEX-FORTUNA-ETERNA-0001"]
        results = [generate_inspiration(record, seed) for seed in range(20)]
        self.assertTrue(
            any(results[i] != results[0] for i in range(1, len(results))),
            "expected at least one of 20 different seeds to change the result",
        )

    def test_does_not_use_global_random_state(self):
        record = self.records["ART-STAR-LYRA-0001"]
        random.seed(1)
        state_before = random.getstate()
        generate_inspiration(record, 7)
        state_after = random.getstate()
        self.assertEqual(state_before, state_after)

    def test_no_timestamps_in_output(self):
        record = self.records["ART-BRANDY-NAPOLEON-0001"]
        result = generate_inspiration(record, 4)
        serialized = json.dumps(result, ensure_ascii=False)
        # ISO-8601-ish timestamp shape, e.g. 2026-07-30T18:00:00
        self.assertNotRegex(serialized, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_does_not_depend_on_entries_directory_order(self):
        # Loading the same record via two independently-sorted paths must
        # still produce identical inspiration for the same seed.
        records_forward = load_all_artifacts(ENTRIES_DIR)
        records_reversed = list(reversed(records_forward))
        record_a = next(r for r in records_forward if r.id == "ART-DARUMA-0001")
        record_b = next(r for r in records_reversed if r.id == "ART-DARUMA-0001")
        self.assertEqual(generate_inspiration(record_a, 9), generate_inspiration(record_b, 9))


class TestGenerateInspirationStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _load_records()

    def test_artifact_id_matches_record(self):
        for record in self.records.values():
            result = generate_inspiration(record, 1)
            self.assertEqual(result["artifact_id"], record.id)

    def test_top_level_keys_are_exact(self):
        record = self.records["ART-COIN-MIDAS-0001"]
        result = generate_inspiration(record, 1)
        self.assertEqual(set(result.keys()), {"artifact_id", "inspiration_aspects", "generated_seed"})

    def test_generated_seed_keys_are_exact(self):
        record = self.records["ART-COIN-MIDAS-0001"]
        result = generate_inspiration(record, 1)
        self.assertEqual(set(result["generated_seed"].keys()), _EXPECTED_STRUCTURE_KEYS)

    def test_inspiration_aspects_is_nonempty_list(self):
        for record in self.records.values():
            result = generate_inspiration(record, 2)
            self.assertIsInstance(result["inspiration_aspects"], list)
            self.assertGreater(len(result["inspiration_aspects"]), 0)

    def test_list_fields_are_lists_of_strings(self):
        record = self.records["ART-RAINBOW-IRIS-0001"]
        result = generate_inspiration(record, 3)
        seed = result["generated_seed"]
        for key in ("tracos_sugeridos", "valores", "contradicoes", "aparencia_inspirada", "simbolos"):
            self.assertIsInstance(seed[key], list)
            self.assertTrue(all(isinstance(v, str) for v in seed[key]))
        self.assertGreater(len(seed["contradicoes"]), 0)

    def test_string_fields_are_nonempty_strings(self):
        record = self.records["ART-RAINBOW-IRIS-0001"]
        result = generate_inspiration(record, 3)
        seed = result["generated_seed"]
        for key in ("conflito_possivel", "missao_possivel", "relacao_sugerida_com_artefacto"):
            self.assertIsInstance(seed[key], str)
            self.assertGreater(len(seed[key].strip()), 0)

    def test_works_for_all_fifteen_real_artifacts(self):
        self.assertEqual(len(self.records), 15)
        for record in self.records.values():
            result = generate_inspiration(record, 42)
            self.assertEqual(set(result["generated_seed"].keys()), _EXPECTED_STRUCTURE_KEYS)
            self.assertGreater(len(result["inspiration_aspects"]), 0)


class TestGenerateInspirationPartialAndContradictory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _load_records()

    def test_is_not_a_direct_copy_of_the_full_record(self):
        record = self.records["ART-CLOVER-AETHORIA-0001"]
        result = generate_inspiration(record, 6)
        serialized = json.dumps(result, ensure_ascii=False)
        raw_serialized = json.dumps(dict(record.raw), ensure_ascii=False)
        self.assertNotEqual(serialized, raw_serialized)

    def test_at_least_one_contradiction_present(self):
        for record in self.records.values():
            result = generate_inspiration(record, 8)
            self.assertGreaterEqual(len(result["generated_seed"]["contradicoes"]), 1)


class TestGenerateInspirationDoesNotMutateInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _load_records()

    def test_record_raw_and_extras_are_unchanged(self):
        record = self.records["ART-HORSESHOE-ASTERION-0001"]
        raw_before = copy.deepcopy(dict(record.raw))
        extras_before = copy.deepcopy(dict(record.extras))
        generate_inspiration(record, 15)
        generate_inspiration(record, 16)
        self.assertEqual(dict(record.raw), raw_before)
        self.assertEqual(dict(record.extras), extras_before)

    def test_never_creates_or_alters_files_on_disk(self):
        before = {p: p.stat().st_mtime for p in Path(".").rglob("*") if p.is_file()}
        record = self.records["ART-LADYBUG-SYLVARIS-0001"]
        for seed in range(5):
            generate_inspiration(record, seed)
        after = {p: p.stat().st_mtime for p in Path(".").rglob("*") if p.is_file()}
        self.assertEqual(before, after)


class TestGenerateInspirationSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _load_records()

    def test_no_forbidden_terms_across_all_real_artifacts_and_many_seeds(self):
        for record in self.records.values():
            for seed in range(6):
                result = generate_inspiration(record, seed)
                for text in _all_strings(result["inspiration_aspects"]):
                    self._assert_clean(record.id, seed, text)
                for text in _all_strings(result["generated_seed"]):
                    self._assert_clean(record.id, seed, text)

    def _assert_clean(self, artifact_id, seed, text):
        lowered = text.lower()
        for term in _FORBIDDEN_SUBSTRINGS:
            self.assertNotIn(
                term, lowered,
                f"{artifact_id}/seed={seed}: forbidden term {term!r} found in {text!r}",
            )
        self.assertIsNone(
            _DIGIT_RE.search(text),
            f"{artifact_id}/seed={seed}: digit found in {text!r} (could read as a number/star pick)",
        )

    def test_does_not_touch_forbidden_directories(self):
        # Structural guarantee: the module performs no filesystem writes at
        # all (verified by TestGenerateInspirationDoesNotMutateInput), so
        # these directories can never be touched. Confirm they still don't
        # exist / remain empty of anything this call could have created.
        for forbidden in ("library/heroes", "library/legends", "datasets", "library/scrolls"):
            path = Path(forbidden)
            if not path.exists():
                continue
            before = sorted(str(p) for p in path.rglob("*"))
            record = self.records["ART-COIN-MIDAS-0001"]
            generate_inspiration(record, 1)
            after = sorted(str(p) for p in path.rglob("*"))
            self.assertEqual(before, after)


class TestGenerateInspirationSpecificArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _load_records()

    def _flat_text(self, result):
        return " ".join(_all_strings(result["inspiration_aspects"])) + " " + \
            " ".join(_all_strings(result["generated_seed"]))

    def test_lotus_uses_serenity_and_evolution_without_recommending_luck(self):
        record = self.records["ART-LOTUS-TRANQUILIDADE-0001"]
        serenity_words = {"serenidade", "calma", "equilibrio", "clareza", "esperanca"}
        seen = set()
        for seed in range(10):
            result = generate_inspiration(record, seed)
            text = self._flat_text(result).lower()
            seen.update(w for w in serenity_words if w in text)
            self.assertNotIn("recomend", text)
        self.assertTrue(seen, "expected at least one serenity-related word across 10 seeds")

    def test_codex_uses_memory_and_wisdom_without_prophecy(self):
        record = self.records["ART-CODEX-FORTUNA-ETERNA-0001"]
        knowledge_words = {"sabedoria", "memoria", "pagina"}
        seen = set()
        for seed in range(10):
            result = generate_inspiration(record, seed)
            text = self._flat_text(result).lower()
            for w in knowledge_words:
                if w in text:
                    seen.add(w)
            self.assertNotIn("profecia", text)
            self.assertNotRegex(text, r"previs[aã]o")
            self.assertNotRegex(text, r"\bprever\b")
        self.assertTrue(seen, "expected at least one memory/wisdom-related word across 10 seeds")

    def test_daruma_uses_perseverance_and_objective(self):
        record = self.records["ART-DARUMA-0001"]
        seen_perseveranca = False
        seen_objetivo = False
        for seed in range(10):
            result = generate_inspiration(record, seed)
            text = self._flat_text(result).lower()
            if "persever" in text:
                seen_perseveranca = True
            if "objetivo" in text:
                seen_objetivo = True
        self.assertTrue(seen_perseveranca, "expected 'perseveranca' to appear across 10 seeds")
        self.assertTrue(seen_objetivo, "expected 'objetivo' to appear across 10 seeds")

    def test_brandy_uses_celebration_but_never_activation_by_prediction(self):
        record = self.records["ART-BRANDY-NAPOLEON-0001"]
        seen_celebration = False
        for seed in range(10):
            result = generate_inspiration(record, seed)
            text = self._flat_text(result).lower()
            if any(w in text for w in ("celebra", "fogos", "confettis", "brinde", "comemorativo")):
                seen_celebration = True
            self.assertNotIn("ativa", text)
            self.assertNotIn("condicao_ativacao", text)
            self.assertNotRegex(text, r"\bprever\b")
            self.assertNotRegex(text, r"previs[aã]o")
        self.assertTrue(seen_celebration, "expected a celebration-related word across 10 seeds")

    def test_cuequinhas_preserves_humor_without_offensive_content(self):
        record = self.records["ART-7A3F91C2BE"]
        _OFFENSIVE_TERMS = ("sexual", "nudez", "palavrao", "insulto", "ofensiv")
        for seed in range(10):
            result = generate_inspiration(record, seed)
            text = self._flat_text(result).lower()
            for term in _OFFENSIVE_TERMS:
                self.assertNotIn(term, text)


if __name__ == "__main__":
    unittest.main()
