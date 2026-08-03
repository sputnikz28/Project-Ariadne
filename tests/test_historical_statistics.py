"""Tests for core/services/historical_statistics.py — pinned against the
real values already verified in-session (0 mismatches across the full
001-058 corpus) for draw 058/2026: numeros=[2,3,8,28,39], estrelas=[2,11].
"""

import unittest

from core.services.historical_statistics import (
    build_estatisticas_chave,
    build_historico_no_conjunto,
)


class TestBuildEstatisticasChave(unittest.TestCase):
    def setUp(self):
        self.stats = build_estatisticas_chave([2, 3, 8, 28, 39], [2, 11], [], [])

    def test_basic_sums_and_moments_match_058(self):
        self.assertEqual(self.stats["soma_numeros"], 80)
        self.assertEqual(self.stats["produto_numeros"], 52416)
        self.assertEqual(self.stats["media_numeros"], 16.0)
        self.assertEqual(self.stats["mediana_numeros"], 8)
        self.assertAlmostEqual(self.stats["desvio_padrao_populacional"], 14.846, places=3)
        self.assertEqual(self.stats["minimo"], 2)
        self.assertEqual(self.stats["maximo"], 39)
        self.assertEqual(self.stats["amplitude"], 37)

    def test_number_classifications_match_058(self):
        self.assertEqual(self.stats["quantidade_pares"], 3)
        self.assertEqual(self.stats["quantidade_impares"], 2)
        self.assertEqual(self.stats["primos"], [2, 3])
        self.assertEqual(self.stats["fibonacci"], [2, 3, 8])
        self.assertEqual(self.stats["quadrados_perfeitos"], [])
        self.assertEqual(self.stats["triangulares"], [3, 28])
        self.assertEqual(self.stats["multiplos_de_3"], [3, 39])
        self.assertEqual(self.stats["multiplos_de_5"], [])

    def test_distributions_match_058(self):
        self.assertEqual(
            self.stats["distribuicao_por_dezenas"],
            {"01-10": 3, "11-20": 0, "21-30": 1, "31-40": 1, "41-50": 0},
        )
        self.assertEqual(self.stats["distribuicao_por_colunas_mod_5"], {"1": 0, "2": 1, "3": 3, "4": 1, "5": 0})

    def test_gaps_match_058(self):
        self.assertEqual(self.stats["intervalos_ordenados"], [1, 5, 20, 11])
        self.assertEqual(self.stats["media_intervalos"], 9.25)
        self.assertEqual(self.stats["maior_intervalo"], 20)
        self.assertEqual(self.stats["menor_intervalo"], 1)

    def test_sequencias_consecutivas_are_adjacent_pairs_not_runs(self):
        # A run of 3 consecutive numbers must produce two overlapping pairs
        # — confirmed against real draws 010/2026 and 024/2026.
        stats = build_estatisticas_chave([1, 26, 27, 28, 45], [1, 2], [], [])
        self.assertEqual(stats["sequencias_consecutivas"], [[26, 27], [27, 28]])

    def test_estrela_stats_match_058(self):
        self.assertEqual(self.stats["soma_estrelas"], 13)
        self.assertEqual(self.stats["media_estrelas"], 6.5)
        self.assertEqual(self.stats["amplitude_estrelas"], 9)
        self.assertEqual(self.stats["estrelas_pares"], [2])
        self.assertEqual(self.stats["estrelas_impares"], [11])

    def test_vetores_binarios_match_058(self):
        vn = self.stats["vetor_binario_numeros_1_50"]
        self.assertEqual(len(vn), 50)
        self.assertEqual([i + 1 for i, v in enumerate(vn) if v], [2, 3, 8, 28, 39])
        ve = self.stats["vetor_binario_estrelas_1_12"]
        self.assertEqual(len(ve), 12)
        self.assertEqual([i + 1 for i, v in enumerate(ve) if v], [2, 11])

    def test_repetidos_sorteio_anterior_intersects_with_prev_key(self):
        stats = build_estatisticas_chave([1, 2, 3, 4, 5], [1, 2], [3, 4, 5, 6, 7], [2, 9])
        self.assertEqual(stats["repetidos_sorteio_anterior"], [3, 4, 5])
        self.assertEqual(stats["estrelas_repetidas_sorteio_anterior"], [2])

    def test_empty_previous_key_gives_no_repeats(self):
        stats = build_estatisticas_chave([1, 2, 3, 4, 5], [1, 2], [], [])
        self.assertEqual(stats["repetidos_sorteio_anterior"], [])
        self.assertEqual(stats["estrelas_repetidas_sorteio_anterior"], [])


class TestBuildHistoricoNoConjunto(unittest.TestCase):
    def _sorteio(self, numeros, estrelas):
        return {"chave": {"numeros": numeros, "estrelas": estrelas}}

    def test_first_occurrence_has_null_atraso(self):
        sorteios = [self._sorteio([1, 2, 3, 4, 5], [1, 2])]
        h = build_historico_no_conjunto(sorteios, 0)
        self.assertIsNone(h["atraso_numeros_em_sorteios"]["1"])
        self.assertEqual(h["frequencia_acumulada_numeros_ate_este_sorteio"]["1"], 1)

    def test_atraso_is_distance_to_prior_occurrence(self):
        sorteios = [
            self._sorteio([1, 2, 3, 4, 5], [1, 2]),
            self._sorteio([6, 7, 8, 9, 10], [3, 4]),
            self._sorteio([1, 11, 12, 13, 14], [1, 5]),
        ]
        h = build_historico_no_conjunto(sorteios, 2)
        self.assertEqual(h["atraso_numeros_em_sorteios"]["1"], 2)
        self.assertEqual(h["frequencia_acumulada_numeros_ate_este_sorteio"]["1"], 2)
        self.assertEqual(h["atraso_estrelas_em_sorteios"]["1"], 2)

    def test_indice_no_conjunto_matches_the_given_index(self):
        sorteios = [self._sorteio([1, 2, 3, 4, 5], [1, 2])] * 3
        h = build_historico_no_conjunto(sorteios, 2)
        self.assertEqual(h["indice_no_conjunto"], 2)


if __name__ == "__main__":
    unittest.main()
