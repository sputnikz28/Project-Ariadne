"""Tests for datasets/historical/euromillions/**/*.json — the canonical,
immutable historical draw records. Every check runs independently against
each discovered yearly file, so a bad update to any one of them fails
locally here instead of silently corrupting the historical record.
"""

import json
import unittest
from datetime import datetime
from pathlib import Path

DATASET_ROOT = Path(__file__).resolve().parent.parent / "datasets" / "historical" / "euromillions"

# Fields every draw entry must have, regardless of which year it's from —
# the intersection observed across the 2004-2026 files (some later years add
# extra fields like "fonte_ordem_saida", which isn't required here).
REQUIRED_DRAW_FIELDS = {
    "numero_sorteio", "data", "dia_semana", "horario", "calendario",
    "chave", "ordem_saida", "ordem_saida_disponivel", "estatisticas_chave",
    "historico_no_conjunto", "estatisticas_financeiras", "premios",
    "astronomia", "identificadores", "qualidade_dados",
}


def discover_datasets():
    return sorted(DATASET_ROOT.glob("*/*.json"))


def load_dataset(path):
    return json.loads(path.read_text(encoding="utf-8"))


class TestHistoricalDatasets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = discover_datasets()
        cls.datasets = {p: load_dataset(p) for p in cls.paths}

    def test_at_least_one_dataset_discovered(self):
        self.assertGreater(len(self.paths), 0, f"no dataset files found under {DATASET_ROOT}")

    def test_unique_draw_numbers(self):
        for path, d in self.datasets.items():
            numeros = [s["numero_sorteio"] for s in d["sorteios"]]
            with self.subTest(file=path.name):
                dups = {n for n in numeros if numeros.count(n) > 1}
                self.assertFalse(dups, f"duplicate numero_sorteio in {path.name}: {dups}")

    def test_unique_draw_dates(self):
        for path, d in self.datasets.items():
            datas = [s["data"] for s in d["sorteios"]]
            with self.subTest(file=path.name):
                dups = {x for x in datas if datas.count(x) > 1}
                self.assertFalse(dups, f"duplicate data in {path.name}: {dups}")

    def test_chronological_ordering(self):
        for path, d in self.datasets.items():
            datas = [datetime.strptime(s["data"], "%Y-%m-%d") for s in d["sorteios"]]
            with self.subTest(file=path.name):
                self.assertTrue(
                    all(datas[i] < datas[i + 1] for i in range(len(datas) - 1)),
                    f"{path.name} is not strictly chronologically ordered",
                )

    def test_schema_consistency_across_draws(self):
        for path, d in self.datasets.items():
            keysets = {frozenset(s.keys()) for s in d["sorteios"]}
            with self.subTest(file=path.name):
                self.assertEqual(len(keysets), 1, f"{path.name} has inconsistent draw schemas: {keysets}")

    def test_required_fields_present(self):
        for path, d in self.datasets.items():
            for s in d["sorteios"]:
                missing = REQUIRED_DRAW_FIELDS - s.keys()
                with self.subTest(file=path.name, draw=s.get("numero_sorteio")):
                    self.assertFalse(missing, f"{path.name} draw {s.get('numero_sorteio')} missing fields: {missing}")

    def test_valid_number_ranges(self):
        for path, d in self.datasets.items():
            lo, hi = d["regras_representadas"]["intervalo_numeros"]
            count = d["regras_representadas"]["numeros_por_chave"]
            for s in d["sorteios"]:
                nums = s["chave"]["numeros"]
                with self.subTest(file=path.name, draw=s["numero_sorteio"]):
                    self.assertEqual(len(nums), count, f"expected {count} numbers")
                    self.assertTrue(
                        all(lo <= n <= hi for n in nums),
                        f"number out of [{lo},{hi}] in {s['numero_sorteio']}: {nums}",
                    )

    def test_valid_star_ranges(self):
        for path, d in self.datasets.items():
            lo, hi = d["regras_representadas"]["intervalo_estrelas"]
            count = d["regras_representadas"]["estrelas_por_chave"]
            for s in d["sorteios"]:
                ests = s["chave"]["estrelas"]
                with self.subTest(file=path.name, draw=s["numero_sorteio"]):
                    self.assertEqual(len(ests), count, f"expected {count} stars")
                    self.assertTrue(
                        all(lo <= e <= hi for e in ests),
                        f"star out of [{lo},{hi}] in {s['numero_sorteio']}: {ests}",
                    )

    def test_no_duplicate_numbers_within_draw(self):
        for path, d in self.datasets.items():
            for s in d["sorteios"]:
                nums = s["chave"]["numeros"]
                with self.subTest(file=path.name, draw=s["numero_sorteio"]):
                    self.assertEqual(len(nums), len(set(nums)), f"duplicate number within {s['numero_sorteio']}: {nums}")

    def test_no_duplicate_stars_within_draw(self):
        for path, d in self.datasets.items():
            for s in d["sorteios"]:
                ests = s["chave"]["estrelas"]
                with self.subTest(file=path.name, draw=s["numero_sorteio"]):
                    self.assertEqual(len(ests), len(set(ests)), f"duplicate star within {s['numero_sorteio']}: {ests}")

    def test_interval_metadata_consistency(self):
        for path, d in self.datasets.items():
            sorteios = d["sorteios"]
            intervalo = d["intervalo"]
            with self.subTest(file=path.name):
                self.assertEqual(intervalo["quantidade_sorteios"], len(sorteios))
                self.assertEqual(intervalo["primeiro_sorteio"], sorteios[0]["numero_sorteio"])
                self.assertEqual(intervalo["ultimo_sorteio"], sorteios[-1]["numero_sorteio"])
                self.assertEqual(intervalo["data_inicio"], sorteios[0]["data"])
                self.assertEqual(intervalo["data_fim"], sorteios[-1]["data"])


if __name__ == "__main__":
    unittest.main()
