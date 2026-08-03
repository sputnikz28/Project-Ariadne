"""Tests for core/services/artifact_registry.py.

Real-collection tests use library/artifacts/entries/ read-only (never
written to). Error-path tests (invalid JSON, filename/id mismatch,
duplicate id) use temporary directories built per-test, never the real
collection.
"""

import json
import tempfile
import unittest
from pathlib import Path

from core.services.artifact_registry import (
    ArtifactLoadError,
    ArtifactRegistry,
    build_index,
    load_all_artifacts,
    write_index,
)
from core.services.artifact_schema import normalize_artifact

ENTRIES_DIR = Path("library/artifacts/entries")


def make_raw(id_, **overrides):
    raw = {
        "id": id_,
        "nome": {"pt": f"Nome de {id_}"},
        "tipo": "TIPO_TESTE",
        "raridade": "COMUM",
        "estado": "ESTADO_TESTE",
        "criador": {"id": f"{id_}-CRIADOR", "nome": f"Criador de {id_}"},
        "universo_origem": 123,
        "energia_acumulada": 1.0,
        "vezes_encontrado": 0,
        "execucoes_sobrevividas": 0,
        "efeitos": {"altera_algoritmo": False, "altera_resultados": False, "altera_probabilidades": False},
        "lore": {"descricao": {"pt": "lore de teste"}},
        "historia": [],
        "tags": ["teste"],
    }
    raw.update(overrides)
    return raw


class TempEntriesDir:
    """Context manager: a throwaway entries_dir with the given raw dicts
    written as <id>.json, unless a different filename is given.
    """

    def __init__(self, entries):
        self.entries = entries  # list of (filename_stem, raw_dict)
        self._tmp = None

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        path = Path(self._tmp.name)
        for filename_stem, raw in self.entries:
            (path / f"{filename_stem}.json").write_text(
                json.dumps(raw, ensure_ascii=False), encoding="utf-8",
            )
        return path

    def __exit__(self, *exc_info):
        self._tmp.cleanup()


class TestLoadAllArtifactsRealCollection(unittest.TestCase):
    def test_loads_exactly_fifteen(self):
        records = load_all_artifacts(ENTRIES_DIR)
        self.assertEqual(len(records), 15)

    def test_ids_are_unique(self):
        records = load_all_artifacts(ENTRIES_DIR)
        ids = [r.id for r in records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_filenames_match_ids(self):
        for path in sorted(ENTRIES_DIR.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["id"], path.stem, f"{path}")

    def test_deterministic_order_by_id(self):
        records = load_all_artifacts(ENTRIES_DIR)
        ids = [r.id for r in records]
        self.assertEqual(ids, sorted(ids))

    def test_never_mutates_entry_files_on_disk(self):
        before = {p: p.read_bytes() for p in ENTRIES_DIR.glob("*.json")}
        load_all_artifacts(ENTRIES_DIR)
        after = {p: p.read_bytes() for p in ENTRIES_DIR.glob("*.json")}
        self.assertEqual(before, after)


class TestLoadAllArtifactsErrorPaths(unittest.TestCase):
    def test_invalid_json_raises_with_file_path(self):
        with TempEntriesDir([]) as tmp:
            bad_path = tmp / "ART-BROKEN-0001.json"
            bad_path.write_text("{ not valid json", encoding="utf-8")
            with self.assertRaises(ArtifactLoadError) as ctx:
                load_all_artifacts(tmp)
            self.assertIn(str(bad_path), str(ctx.exception))

    def test_filename_id_mismatch_raises(self):
        with TempEntriesDir([("ART-WRONG-NAME-0001", make_raw("ART-ACTUAL-ID-0001"))]) as tmp:
            with self.assertRaises(ArtifactLoadError) as ctx:
                load_all_artifacts(tmp)
            self.assertIn("filename does not match id", str(ctx.exception))
            self.assertIn("ART-WRONG-NAME-0001", str(ctx.exception))

    def test_duplicate_id_across_two_correctly_named_files_raises(self):
        # The FIRST file (alphabetically) must have filename == its own
        # id, so it loads cleanly and lands in seen_ids. The SECOND file
        # declares the SAME id under a different filename — this is what
        # must trigger the duplicate-id error, not a filename-mismatch
        # error, proving the duplicate check really does run first.
        entries = [
            ("ART-AAA-DUP-0001", make_raw("ART-AAA-DUP-0001")),
            ("ART-ZZZ-DUP-0001", make_raw("ART-AAA-DUP-0001")),
        ]
        with TempEntriesDir(entries) as tmp:
            with self.assertRaises(ArtifactLoadError) as ctx:
                load_all_artifacts(tmp)
            self.assertIn("duplicate artifact id", str(ctx.exception))
            self.assertIn("ART-AAA-DUP-0001", str(ctx.exception))


class TestArtifactRegistryQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_all_artifacts(ENTRIES_DIR)
        cls.registry = ArtifactRegistry(cls.records)

    def test_all_returns_every_record_in_deterministic_order(self):
        ids = [r.id for r in self.registry.all()]
        self.assertEqual(len(ids), 15)
        self.assertEqual(ids, sorted(ids))

    def test_all_results_are_artifact_records(self):
        from core.services.artifact_schema import ArtifactRecord
        for record in self.registry.all():
            self.assertIsInstance(record, ArtifactRecord)

    def test_by_id_found(self):
        record = self.registry.by_id("ART-DARUMA-0001")
        self.assertIsNotNone(record)
        self.assertEqual(record.id, "ART-DARUMA-0001")

    def test_by_id_not_found_returns_none(self):
        self.assertIsNone(self.registry.by_id("ART-DOES-NOT-EXIST"))

    def test_by_type_exact_match(self):
        result = self.registry.by_type("FERRADURA")
        self.assertEqual(
            {r.id for r in result},
            {
                "ART-HORSESHOE-TRAPALHAO-0001", "ART-HORSESHOE-TOBIAS-0001",
                "ART-HORSESHOE-TEMPESTADE-0001", "ART-HORSESHOE-VALENTE-0001",
                "ART-HORSESHOE-ASTERION-0001",
            },
        )

    def test_by_type_no_match_returns_empty(self):
        self.assertEqual(self.registry.by_type("TIPO_INEXISTENTE"), ())

    def test_by_tag_case_insensitive_and_trims_spaces(self):
        exact = self.registry.by_tag("mitico")
        upper = self.registry.by_tag("MITICO")
        padded = self.registry.by_tag("  Mitico  ")
        self.assertTrue(len(exact) > 0)
        self.assertEqual({r.id for r in exact}, {r.id for r in upper})
        self.assertEqual({r.id for r in exact}, {r.id for r in padded})

    def test_by_creator_matches_by_id(self):
        result = self.registry.by_creator("KING-MIDAS-0001")
        self.assertEqual({r.id for r in result}, {"ART-COIN-MIDAS-0001"})

    def test_by_creator_matches_by_name(self):
        result = self.registry.by_creator("Midas, o Rei Dourado")
        self.assertEqual({r.id for r in result}, {"ART-COIN-MIDAS-0001"})

    def test_by_creator_no_match_returns_empty(self):
        self.assertEqual(self.registry.by_creator("Ninguém"), ())


class TestArtifactRegistryDuplicateRejection(unittest.TestCase):
    def test_constructing_with_duplicate_ids_raises_not_silently_overwrites(self):
        a = normalize_artifact(make_raw("ART-DUP-0001", energia_acumulada=1.0))
        b = normalize_artifact(make_raw("ART-DUP-0001", energia_acumulada=99.0))
        with self.assertRaises(ArtifactLoadError):
            ArtifactRegistry([a, b])


class TestBuildIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_all_artifacts(ENTRIES_DIR)

    def test_total_artifacts_is_fifteen(self):
        index = build_index(self.records)
        self.assertEqual(index["total_artifacts"], 15)

    def test_artifact_ids_match_loaded_records(self):
        index = build_index(self.records)
        self.assertEqual(set(index["artifact_ids"]), {r.id for r in self.records})

    def test_por_tipo_counts_match_records(self):
        index = build_index(self.records)
        self.assertEqual(index["por_tipo"]["FERRADURA"], 5)
        self.assertEqual(sum(index["por_tipo"].values()), 15)

    def test_por_estado_uses_codigo_not_full_object(self):
        index = build_index(self.records)
        self.assertIn("LACRADO", index["por_estado"])  # BRANDY-NAPOLEON's estado.codigo

    def test_por_criador_prefers_id_over_nome(self):
        index = build_index(self.records)
        self.assertIn("KING-MIDAS-0001", index["por_criador"])

    def test_missing_values_grouped_as_desconhecido_not_invented(self):
        index = build_index(self.records)
        # HORSESHOE-* entries have no universo_origem:
        self.assertIn("DESCONHECIDO", index["por_universo"])

    def test_rankings_are_sorted_descending_with_id_tiebreak(self):
        index = build_index(self.records)
        energias = [row["energia_acumulada"] for row in index["ranking_energia"]]
        self.assertEqual(energias, sorted(energias, reverse=True))
        # explicit tie-break check: synthesize equal-energy records
        tied = [
            normalize_artifact(make_raw("ART-TIE-B-0001", energia_acumulada=5.0)),
            normalize_artifact(make_raw("ART-TIE-A-0001", energia_acumulada=5.0)),
        ]
        tied_index = build_index(tied)
        self.assertEqual(
            [row["id"] for row in tied_index["ranking_energia"]],
            ["ART-TIE-A-0001", "ART-TIE-B-0001"],
        )

    def test_second_call_differs_only_in_atualizado_em(self):
        first = build_index(self.records)
        second = build_index(self.records)
        first_without_ts = {k: v for k, v in first.items() if k != "atualizado_em"}
        second_without_ts = {k: v for k, v in second.items() if k != "atualizado_em"}
        self.assertEqual(first_without_ts, second_without_ts)

    def test_counts_are_order_independent(self):
        reversed_records = list(reversed(self.records))
        index_forward = build_index(self.records)
        index_reversed = build_index(reversed_records)
        for key in ("por_tipo", "por_raridade", "por_estado", "por_criador", "por_universo", "por_tag"):
            self.assertEqual(index_forward[key], index_reversed[key])

    def test_never_mutates_entry_files_on_disk(self):
        before = {p: p.read_bytes() for p in ENTRIES_DIR.glob("*.json")}
        build_index(self.records)
        after = {p: p.read_bytes() for p in ENTRIES_DIR.glob("*.json")}
        self.assertEqual(before, after)


class TestWriteIndex(unittest.TestCase):
    def test_roundtrip(self):
        records = load_all_artifacts(ENTRIES_DIR)
        index = build_index(records)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "LIVRO_DOS_ARTEFACTOS.json"
            write_index(index, path)
            self.assertTrue(path.exists())
            reloaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(reloaded, index)

    def test_creates_missing_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a" / "b" / "c" / "index.json"
            write_index({"x": 1}, path)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
