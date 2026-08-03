"""Tests for core/services/historical_astronomy.py — pinned against the
real astronomia values already confirmed in-session for draws 001-058 (see
project history for draws 059-061). Not byte-exact reproduction (that was
explicitly not required), but tight tolerances proving the same Meeus
low-precision methodology.
"""

import unittest

from core.services.historical_astronomy import (
    PHASE_NAMES,
    SYNODIC_MONTH,
    _phase_name_for_age,
    compute_astronomia,
)


class TestComputeAstronomia(unittest.TestCase):
    def test_draw_058_position_matches_known_real_values(self):
        # 058/2026, 2026-07-21T18:00:00 UTC — real astronomia block values.
        result = compute_astronomia(2026, 7, 21, 18, 0, 0)
        self.assertAlmostEqual(result["longitude_ecliptica_lua_graus"], 212.4198, delta=0.5)
        self.assertAlmostEqual(result["latitude_ecliptica_lua_graus"], -4.613147, delta=0.05)
        self.assertAlmostEqual(result["distancia_terra_lua_km_aprox"], 397094, delta=200)
        self.assertAlmostEqual(result["longitude_ecliptica_sol_graus"], 118.99997, delta=0.05)
        self.assertAlmostEqual(result["distancia_terra_sol_km_aprox"], 152000776, delta=50)
        self.assertAlmostEqual(result["elongacao_lua_sol_graus_aprox"], 93.42, delta=0.5)
        self.assertAlmostEqual(result["idade_lunar_dias_aprox"], 7.663, delta=0.05)
        self.assertEqual(result["fase_lua"], "Quarto crescente")

    def test_illumination_is_a_fraction_not_a_percentage(self):
        # Confirmed convention: 057/058 both used 0-1, not 0-100.
        result = compute_astronomia(2026, 7, 21, 18, 0, 0)
        self.assertGreaterEqual(result["iluminacao_lunar_percent_aprox"], 0.0)
        self.assertLessEqual(result["iluminacao_lunar_percent_aprox"], 1.0)
        self.assertAlmostEqual(result["iluminacao_lunar_percent_aprox"], 0.53, delta=0.02)

    def test_instante_utc_matches_input(self):
        result = compute_astronomia(2026, 8, 4, 18, 0, 0)
        self.assertEqual(result["instante_utc"], "2026-08-04T18:00:00+00:00")

    def test_eclipse_defaults_to_false(self):
        result = compute_astronomia(2026, 8, 4, 18, 0, 0)
        self.assertIs(result["eclipse_no_instante"], False)

    def test_metodo_mentions_meeus_and_stdlib(self):
        result = compute_astronomia(2026, 8, 4, 18, 0, 0)
        self.assertIn("Meeus", result["metodo"])
        self.assertIn("stdlib", result["metodo"])


class TestPhaseNameForAge(unittest.TestCase):
    # Empirically confirmed boundaries: 8 equal divisions of the synodic
    # month, centered on "Lua nova" at age 0 — verified against all 58 real
    # draws with 0 mismatches.
    def test_known_real_ages_map_to_the_canonical_phase(self):
        cases = [
            (0.395, "Lua nova"),
            (7.663, "Quarto crescente"),
            (10.376, "Gibosa crescente"),
            (13.976, "Lua cheia"),
            (16.769, "Gibosa minguante"),
        ]
        for age, expected in cases:
            with self.subTest(age=age):
                self.assertEqual(_phase_name_for_age(age), expected)

    def test_age_near_full_cycle_wraps_back_to_lua_nova(self):
        self.assertEqual(_phase_name_for_age(SYNODIC_MONTH - 0.5), "Lua nova")

    def test_returns_only_canonical_eight_phase_names(self):
        for age in [i * 0.7 for i in range(50)]:
            with self.subTest(age=age):
                self.assertIn(_phase_name_for_age(age), PHASE_NAMES)


if __name__ == "__main__":
    unittest.main()
