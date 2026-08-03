"""Tests for core/services/historical_draw_generator.py — the orchestrator
that validates and builds new historical draw records. Uses small synthetic
fixtures, never the real repository dataset.
"""

import copy
import unittest

from core.services.historical_draw_generator import (
    DrawInput,
    DrawValidationError,
    build_draw_record,
    dia_semana_for,
    next_dataset_filename,
    register_draws,
    validate_draw_input,
)


def make_draw_input(**overrides):
    fields = dict(
        numero_sorteio="062/2026",
        data="2026-08-04",  # a Tuesday
        numeros=(1, 2, 3, 4, 5),
        estrelas=(1, 2),
        ordem_numeros=(5, 3, 1, 4, 2),
        ordem_estrelas=(2, 1),
    )
    fields.update(overrides)
    return DrawInput(**fields)


def make_existing_sorteio(numero_sorteio="061/2026", data="2026-07-31", numeros=(10, 24, 25, 31, 45), estrelas=(4, 5)):
    return {
        "numero_sorteio": numero_sorteio,
        "data": data,
        "chave": {"numeros": list(numeros), "estrelas": list(estrelas)},
        "qualidade_dados": {"dados_financeiros_disponiveis": False},
        "ordem_saida_disponivel": True,
    }


def make_dataset(sorteios):
    return {
        "intervalo": {
            "primeiro_sorteio": sorteios[0]["numero_sorteio"],
            "ultimo_sorteio": sorteios[-1]["numero_sorteio"],
            "data_inicio": sorteios[0]["data"],
            "data_fim": sorteios[-1]["data"],
            "quantidade_sorteios": len(sorteios),
        },
        "estado_dataset": "placeholder",
        "resumo_conjunto": {
            "frequencia_numeros": {}, "frequencia_estrelas": {},
            "ranking_numeros": [], "ranking_estrelas": [],
            "sorteios_com_ordem_saida": 0, "sorteios_sem_ordem_saida": 0,
            "sorteios_com_dados_financeiros": 0,
        },
        "notas_metodologicas": ["nota inicial"],
        "sorteios": sorteios,
    }


class TestDiaSemanaFor(unittest.TestCase):
    def test_known_dates(self):
        from datetime import date
        self.assertEqual(dia_semana_for(date(2026, 7, 31)), "sexta-feira")
        self.assertEqual(dia_semana_for(date(2026, 7, 28)), "terça-feira")


class TestValidateDrawInput(unittest.TestCase):
    def test_valid_input_raises_nothing(self):
        existing = [make_existing_sorteio()]
        validate_draw_input(make_draw_input(), existing)  # no exception

    def test_duplicate_numero_sorteio_is_rejected(self):
        existing = [make_existing_sorteio(numero_sorteio="062/2026")]
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numero_sorteio="062/2026"), existing)

    def test_non_chronological_date_is_rejected(self):
        existing = [make_existing_sorteio(data="2026-08-04")]
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numero_sorteio="063/2026", data="2026-08-04"), existing)

    def test_wrong_weekday_is_rejected(self):
        # 2026-08-05 is a Wednesday
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(data="2026-08-05"), [])

    def test_year_mismatch_between_numero_sorteio_and_data_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numero_sorteio="062/2027"), [])

    def test_malformed_numero_sorteio_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numero_sorteio="62/2026"), [])

    def test_wrong_number_count_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numeros=(1, 2, 3, 4), ordem_numeros=(1, 2, 3, 4)), [])

    def test_number_out_of_range_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numeros=(1, 2, 3, 4, 51), ordem_numeros=(1, 2, 3, 4, 51)), [])

    def test_duplicate_number_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(numeros=(1, 1, 3, 4, 5), ordem_numeros=(1, 1, 3, 4, 5)), [])

    def test_ordem_numeros_not_a_permutation_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(ordem_numeros=(9, 8, 7, 6, 5)), [])

    def test_ordem_estrelas_not_a_permutation_is_rejected(self):
        with self.assertRaises(DrawValidationError):
            validate_draw_input(make_draw_input(ordem_estrelas=(9, 8)), [])

    def test_first_draw_ever_is_accepted_with_no_existing_sorteios(self):
        validate_draw_input(make_draw_input(), [])  # no exception


class TestBuildDrawRecord(unittest.TestCase):
    def test_record_uses_sorted_key_and_original_order(self):
        record = build_draw_record([], make_draw_input(numeros=(5, 1, 3, 2, 4), ordem_numeros=(5, 3, 1, 4, 2)))
        self.assertEqual(record["chave"]["numeros"], [1, 2, 3, 4, 5])
        self.assertEqual(record["ordem_saida"]["numeros"], [5, 3, 1, 4, 2])

    def test_summer_draw_uses_dst_offsets(self):
        record = build_draw_record([], make_draw_input(data="2026-08-04"))
        self.assertEqual(record["horario"]["timestamp_paris"], "2026-08-04T20:00:00+02:00")
        self.assertEqual(record["horario"]["timestamp_utc"], "2026-08-04T18:00:00+00:00")

    def test_winter_draw_uses_standard_time_offsets(self):
        # 2026-01-06 is a Tuesday, well outside EU summer time.
        record = build_draw_record([], make_draw_input(numero_sorteio="002/2026", data="2026-01-06"))
        self.assertEqual(record["horario"]["timestamp_paris"], "2026-01-06T20:00:00+01:00")
        self.assertEqual(record["horario"]["timestamp_portugal"], "2026-01-06T19:00:00+00:00")
        self.assertEqual(record["horario"]["timestamp_utc"], "2026-01-06T19:00:00+00:00")

    def test_id_composto_uses_the_draws_own_year_not_hardcoded(self):
        record = build_draw_record([], make_draw_input(numero_sorteio="001/2031", data="2031-08-05"))
        self.assertEqual(record["identificadores"]["id_composto"], "euromilhoes-001-2031")

    def test_sha256_chave_matches_confirmed_convention(self):
        import hashlib
        record = build_draw_record([], make_draw_input())
        expected = hashlib.sha256(record["identificadores"]["chave_canonica"].encode("utf-8")).hexdigest()
        self.assertEqual(record["identificadores"]["sha256_chave"], expected)

    def test_repetidos_sorteio_anterior_uses_the_immediately_previous_draw(self):
        existing = [make_existing_sorteio(numeros=(1, 2, 3, 4, 5), estrelas=(1, 2))]
        record = build_draw_record(existing, make_draw_input(numeros=(1, 2, 6, 7, 8), ordem_numeros=(1, 2, 6, 7, 8)))
        self.assertEqual(record["estatisticas_chave"]["repetidos_sorteio_anterior"], [1, 2])

    def test_first_ever_draw_has_no_previous_key_to_repeat(self):
        record = build_draw_record([], make_draw_input())
        self.assertEqual(record["estatisticas_chave"]["repetidos_sorteio_anterior"], [])

    def test_historico_no_conjunto_is_left_as_placeholder(self):
        # register_draws() fills this in once the record has its own index
        # in the sorteios list; build_draw_record() alone cannot know it.
        record = build_draw_record([], make_draw_input())
        self.assertIsNone(record["historico_no_conjunto"])


class TestRegisterDraws(unittest.TestCase):
    def test_appends_record_and_returns_new_dict(self):
        dataset = make_dataset([make_existing_sorteio()])
        original_snapshot = copy.deepcopy(dataset)
        result = register_draws(dataset, [make_draw_input()])
        self.assertEqual(len(result["sorteios"]), 2)
        self.assertEqual(result["sorteios"][-1]["numero_sorteio"], "062/2026")
        self.assertEqual(dataset, original_snapshot)  # original never mutated

    def test_historico_no_conjunto_is_filled_in_after_append(self):
        dataset = make_dataset([make_existing_sorteio()])
        result = register_draws(dataset, [make_draw_input()])
        self.assertEqual(result["sorteios"][-1]["historico_no_conjunto"]["indice_no_conjunto"], 1)

    def test_top_level_metadata_is_updated(self):
        dataset = make_dataset([make_existing_sorteio()])
        result = register_draws(dataset, [make_draw_input()])
        self.assertEqual(result["intervalo"]["ultimo_sorteio"], "062/2026")
        self.assertEqual(result["intervalo"]["quantidade_sorteios"], 2)
        self.assertEqual(len(result["notas_metodologicas"]), 2)  # appended, not replaced

    def test_intervalo_primeiro_sorteio_and_data_inicio_are_always_set(self):
        # Regression: _update_top_level_metadata() must set these even
        # when starting from a dataset that never had them (e.g. a fresh
        # seed), not just refresh them assuming they already exist.
        dataset = make_dataset([make_existing_sorteio(numero_sorteio="061/2026", data="2026-07-31")])
        dataset["intervalo"].pop("primeiro_sorteio", None)
        dataset["intervalo"].pop("data_inicio", None)
        result = register_draws(dataset, [make_draw_input()])
        self.assertEqual(result["intervalo"]["primeiro_sorteio"], "061/2026")
        self.assertEqual(result["intervalo"]["data_inicio"], "2026-07-31")

    def test_multiple_draws_registered_in_chronological_order(self):
        dataset = make_dataset([make_existing_sorteio()])
        inputs = [
            make_draw_input(numero_sorteio="062/2026", data="2026-08-04"),
            make_draw_input(
                numero_sorteio="063/2026", data="2026-08-07",
                numeros=(6, 7, 8, 9, 10), estrelas=(3, 4),
                ordem_numeros=(10, 9, 8, 7, 6), ordem_estrelas=(4, 3),
            ),
        ]
        result = register_draws(dataset, inputs)
        self.assertEqual([s["numero_sorteio"] for s in result["sorteios"]], ["061/2026", "062/2026", "063/2026"])

    def test_invalid_draw_in_batch_raises_and_nothing_is_returned(self):
        dataset = make_dataset([make_existing_sorteio()])
        inputs = [make_draw_input(numero_sorteio="061/2026")]  # duplicate
        with self.assertRaises(DrawValidationError):
            register_draws(dataset, inputs)

    def test_empty_draw_list_is_rejected(self):
        dataset = make_dataset([make_existing_sorteio()])
        with self.assertRaises(DrawValidationError):
            register_draws(dataset, [])


class TestNextDatasetFilename(unittest.TestCase):
    def test_replaces_only_the_draw_number_segment(self):
        result = next_dataset_filename("euromilhoes_2026_001_058_dataset_completo.json", "061/2026")
        self.assertEqual(result, "euromilhoes_2026_001_061_dataset_completo.json")

    def test_raises_on_unrecognised_filename_pattern(self):
        with self.assertRaises(ValueError):
            next_dataset_filename("not_a_recognised_name.json", "061/2026")


if __name__ == "__main__":
    unittest.main()
