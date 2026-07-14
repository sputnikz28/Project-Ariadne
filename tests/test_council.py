"""Tests for council/council.py — filter_candidates, vote, corrupt."""

import random
import unittest
from configparser import ConfigParser

from council.council import corrupt, filter_candidates, vote


class TestFilterCandidates(unittest.TestCase):
    def test_candidate_already_in_sum_range_passes_through_unchanged(self):
        key = ([1, 10, 20, 30, 40], [3, 7])
        accepted, events, rejected = filter_candidates([("Origem", key, 1.0)])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0], ("Origem", key, 1.0))
        self.assertEqual(events, [])
        self.assertEqual(rejected, [])

    def test_low_energy_candidate_in_range_is_rejected(self):
        # gaps = [1,1,1,31] -> 3+ gaps of 1 and a gap > 25 -> energy < 50
        key = ([10, 11, 12, 13, 44], [1, 2])
        self.assertEqual(sum(key[0]), 90)  # stays in the [90,170] window untouched
        accepted, events, rejected = filter_candidates([("Origem", key, 1.0)])
        self.assertEqual(accepted, [])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["origem"], "Origem")
        self.assertLess(self._energy_of(rejected[0]["gaps"]), 50)

    def test_out_of_range_candidate_is_mutated_into_range(self):
        random.seed(42)
        key = ([1, 2, 3, 4, 5], [1, 2])
        self.assertLess(sum(key[0]), 90)
        accepted, events, rejected = filter_candidates([("Origem", key, 1.0)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["origem"], "Origem")
        self.assertEqual(events[0]["antes"], key)
        mutated_sum = sum(events[0]["depois"][0])
        self.assertTrue(90 <= mutated_sum <= 170)
        # the mutated candidate ends up either accepted (marked [infectada]) or rejected
        self.assertEqual(len(accepted) + len(rejected), 1)
        if accepted:
            self.assertTrue(accepted[0][0].endswith("[infectada]"))

    @staticmethod
    def _energy_of(gaps):
        return (100 - (70 if gaps.count(1) >= 3 else 0)
                - (35 if max(gaps) > 25 else 0)
                - (40 if max(gaps) <= 3 else 0)
                + (10 if len(set(gaps)) >= 3 else 0))


class TestVote(unittest.TestCase):
    def test_picks_the_five_most_voted_numbers_and_two_most_voted_stars(self):
        candidatos = [
            ("A", ([1, 2, 3, 4, 5], [1, 2]), 10.0),
            ("B", ([1, 2, 3, 4, 6], [1, 3]), 5.0),
            ("C", ([1, 2, 3, 4, 7], [1, 4]), 1.0),
        ]
        resultado = vote(candidatos)
        nums, ests = resultado["chave"]
        self.assertEqual(nums, [1, 2, 3, 4, 5])
        self.assertEqual(ests, [1, 2])

    def test_votos_numeros_reflects_weighted_totals(self):
        candidatos = [
            ("A", ([1, 2, 3, 4, 5], [1, 2]), 10.0),
            ("B", ([1, 2, 3, 4, 6], [1, 3]), 5.0),
        ]
        resultado = vote(candidatos)
        votos = dict(resultado["votos_numeros"])
        self.assertEqual(votos[1], 15.0)
        self.assertEqual(votos[5], 10.0)
        self.assertEqual(votos[6], 5.0)


class TestCorrupt(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigParser()
        self.cfg.add_section("CORRUPTOR")
        self.cfg.set("CORRUPTOR", "ativo", "true")
        self.cfg.set("CORRUPTOR", "nome", "Malphas, o Quebra-Conselhos")
        self.cfg.set("CORRUPTOR", "range_numeros", "-3,3")
        self.cfg.set("CORRUPTOR", "range_estrelas", "-1,1")

    def test_corrupted_key_stays_within_valid_bounds(self):
        random.seed(7)
        chave = ([10, 20, 30, 40, 50], [5, 10])
        resultado = corrupt(self.cfg, chave)
        nums, ests = resultado["chave_corrompida"]
        self.assertEqual(len(nums), 5)
        self.assertEqual(len(ests), 2)
        self.assertTrue(all(1 <= n <= 50 for n in nums))
        self.assertTrue(all(1 <= e <= 12 for e in ests))

    def test_preserves_original_key_and_entity_name(self):
        random.seed(7)
        chave = ([10, 20, 30, 40, 50], [5, 10])
        resultado = corrupt(self.cfg, chave)
        self.assertEqual(resultado["chave_original"], chave)
        self.assertEqual(resultado["entidade"], "Malphas, o Quebra-Conselhos")

    def test_records_one_displacement_per_number_and_star(self):
        random.seed(7)
        chave = ([10, 20, 30, 40, 50], [5, 10])
        resultado = corrupt(self.cfg, chave)
        self.assertEqual(len(resultado["alteracoes_numeros"]), 5)
        self.assertEqual(len(resultado["alteracoes_estrelas"]), 2)
        for alteracao in resultado["alteracoes_numeros"]:
            self.assertEqual(alteracao["novo"], max(1, min(50, alteracao["original"] + alteracao["deslocamento"])))


if __name__ == "__main__":
    unittest.main()
