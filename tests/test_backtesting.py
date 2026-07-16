"""Tests for compare_result.py — the post-draw backtesting/scoring logic."""

import unittest

from compare_result import avaliar_registo, titulo


class TestTitulo(unittest.TestCase):
    def test_perfect_match(self):
        self.assertEqual(titulo(5, 2), "LENDA ETERNA")

    def test_five_numbers_without_both_stars(self):
        self.assertEqual(titulo(5, 0), "Aquele que Viu")
        self.assertEqual(titulo(5, 1), "Aquele que Viu")

    def test_four_numbers(self):
        self.assertEqual(titulo(4, 0), "Profeta Lunar")
        self.assertEqual(titulo(4, 2), "Profeta Lunar")

    def test_three_numbers_and_two_stars(self):
        self.assertEqual(titulo(3, 2), "ORÁCULO DE OURO")

    def test_three_numbers_without_both_stars(self):
        self.assertEqual(titulo(3, 0), "Mestre dos Ossos")
        self.assertEqual(titulo(3, 1), "Mestre dos Ossos")

    def test_two_numbers(self):
        self.assertEqual(titulo(2, 0), "Leitor dos Sinais")

    def test_one_number(self):
        self.assertEqual(titulo(1, 0), "Sussurrador do Destino")

    def test_zero_numbers_with_a_star(self):
        self.assertEqual(titulo(0, 1), "Observador Celeste")

    def test_zero_numbers_and_zero_stars(self):
        self.assertEqual(titulo(0, 0), "Errante das Sombras")


class TestAvaliarRegisto(unittest.TestCase):
    def test_perfect_match_scores_correctly(self):
        registo = {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "nome": "Herói"}
        resultado = avaliar_registo(registo, [1, 2, 3, 4, 5], [1, 2])
        self.assertEqual(resultado["acertos_numeros"], 5)
        self.assertEqual(resultado["acertos_estrelas"], 2)
        self.assertEqual(resultado["pontos_resultado"], 5 * 10 + 2 * 5 + 8 + 5)
        self.assertEqual(resultado["titulo_resultado"], "LENDA ETERNA")

    def test_no_match_scores_zero_with_correct_title(self):
        registo = {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "nome": "Herói"}
        resultado = avaliar_registo(registo, [6, 7, 8, 9, 10], [3, 4])
        self.assertEqual(resultado["acertos_numeros"], 0)
        self.assertEqual(resultado["acertos_estrelas"], 0)
        self.assertEqual(resultado["pontos_resultado"], 0)
        self.assertEqual(resultado["titulo_resultado"], "Errante das Sombras")

    def test_three_number_bonus_is_only_applied_from_three_matches_up(self):
        registo = {"numeros": [1, 2, 3, 40, 41], "estrelas": [1, 2], "nome": "Herói"}
        resultado = avaliar_registo(registo, [1, 2, 3, 4, 5], [9, 10])
        self.assertEqual(resultado["acertos_numeros"], 3)
        self.assertEqual(resultado["pontos_resultado"], 3 * 10 + 8)  # no star bonus, no 2-star bonus

    def test_original_registo_fields_are_preserved(self):
        registo = {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "nome": "Herói", "geracao": 3}
        resultado = avaliar_registo(registo, [1, 2, 3, 4, 5], [1, 2])
        self.assertEqual(resultado["nome"], "Herói")
        self.assertEqual(resultado["geracao"], 3)


if __name__ == "__main__":
    unittest.main()
