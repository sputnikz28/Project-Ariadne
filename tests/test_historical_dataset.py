"""Tests for datasets/historical/euromillions/**/*.json — the canonical,
immutable historical draw records. Every check runs independently against
each discovered yearly file, so a bad update to any one of them fails
locally here instead of silently corrupting the historical record.
"""

import unittest
from datetime import datetime

from core.services.historical_dataset import (
    DATASET_ROOT,
    REQUIRED_DRAW_FIELDS,
    discover_datasets,
    load_dataset,
    validate_historical_dataset,
)


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


def make_valid_draw(**overrides):
    # Every REQUIRED_DRAW_FIELDS key gets a placeholder value, so this
    # fixture never drifts out of sync with the production field list —
    # only the fields these tests actually inspect are given real values.
    draw = {field: {} for field in REQUIRED_DRAW_FIELDS}
    draw.update({
        "numero_sorteio": "001/2099",
        "data": "2099-01-06",
        "dia_semana": "terça-feira",
        "chave": {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2]},
        "ordem_saida_disponivel": True,
    })
    draw.update(overrides)
    return draw


def make_valid_dataset(sorteios):
    return {
        "regras_representadas": {
            "intervalo_numeros": [1, 50],
            "numeros_por_chave": 5,
            "intervalo_estrelas": [1, 12],
            "estrelas_por_chave": 2,
        },
        "intervalo": {
            "quantidade_sorteios": len(sorteios),
            "primeiro_sorteio": sorteios[0]["numero_sorteio"],
            "ultimo_sorteio": sorteios[-1]["numero_sorteio"],
            "data_inicio": sorteios[0]["data"],
            "data_fim": sorteios[-1]["data"],
        },
        "sorteios": sorteios,
    }


class TestValidateHistoricalDataset(unittest.TestCase):
    def test_valid_dataset_has_no_problems(self):
        dataset = make_valid_dataset([make_valid_draw()])
        self.assertEqual(validate_historical_dataset(dataset), [])

    def test_duplicate_numero_sorteio_is_reported(self):
        dataset = make_valid_dataset([
            make_valid_draw(numero_sorteio="001/2099", data="2099-01-06"),
            make_valid_draw(numero_sorteio="001/2099", data="2099-01-09", dia_semana="sexta-feira"),
        ])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("duplicate numero_sorteio" in p for p in problems))

    def test_duplicate_data_is_reported(self):
        dataset = make_valid_dataset([
            make_valid_draw(numero_sorteio="001/2099", data="2099-01-06"),
            make_valid_draw(numero_sorteio="002/2099", data="2099-01-06", dia_semana="sexta-feira"),
        ])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("duplicate data" in p for p in problems))

    def test_non_chronological_order_is_reported(self):
        dataset = make_valid_dataset([
            make_valid_draw(numero_sorteio="002/2099", data="2099-01-09", dia_semana="sexta-feira"),
            make_valid_draw(numero_sorteio="001/2099", data="2099-01-06"),
        ])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("chronologically ordered" in p for p in problems))

    def test_inconsistent_schema_across_draws_is_reported(self):
        draw1 = make_valid_draw()
        draw2 = make_valid_draw(numero_sorteio="002/2099", data="2099-01-09", dia_semana="sexta-feira")
        del draw2["astronomia"]
        dataset = make_valid_dataset([draw1, draw2])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("inconsistent draw schemas" in p for p in problems))

    def test_missing_required_field_is_reported(self):
        draw = make_valid_draw()
        del draw["identificadores"]
        dataset = make_valid_dataset([draw])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("missing fields" in p and "identificadores" in p for p in problems))

    def test_interval_mismatch_is_reported(self):
        dataset = make_valid_dataset([make_valid_draw()])
        dataset["intervalo"]["quantidade_sorteios"] = 99
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("intervalo.quantidade_sorteios mismatch" in p for p in problems))

    def test_number_out_of_range_is_reported(self):
        draw = make_valid_draw(chave={"numeros": [1, 2, 3, 4, 99], "estrelas": [1, 2]})
        dataset = make_valid_dataset([draw])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("invalid numeros range" in p for p in problems))

    def test_star_out_of_range_is_reported(self):
        draw = make_valid_draw(chave={"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 13]})
        dataset = make_valid_dataset([draw])
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("invalid estrelas range" in p for p in problems))

    def test_empty_sorteios_is_reported_not_silently_valid(self):
        dataset = {"sorteios": [], "regras_representadas": {}, "intervalo": {}}
        problems = validate_historical_dataset(dataset)
        self.assertIn("dataset contains no sorteios", problems)

    def test_non_mapping_dataset_never_raises(self):
        for bad in (None, "not-a-dict", 123, ["a", "list"]):
            with self.subTest(bad=bad):
                problems = validate_historical_dataset(bad)
                self.assertGreaterEqual(len(problems), 1)

    def test_malformed_regras_representadas_still_validates_ranges_via_default(self):
        draw = make_valid_draw(chave={"numeros": [1, 2, 3, 4, 99], "estrelas": [1, 2]})
        dataset = make_valid_dataset([draw])
        del dataset["regras_representadas"]
        problems = validate_historical_dataset(dataset)
        self.assertTrue(any("regras_representadas" in p for p in problems))
        self.assertTrue(any("invalid numeros range" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
