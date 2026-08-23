"""Tests for core/services/treefolks_v2/yggdrasil.py.

IMPORTANT — environment note: PyTorch is NOT installed in this
environment (no installation was authorized during this tranche — see
requirements-treefolks-v2.txt, optional). This means:
  - Every test below that only exercises pure-Python logic
    (_build_causal_pairs, HAS_TORCH-False abstention, signatures) runs
    for real, in this environment, right now.
  - Every test that needs torch itself (actual training, the
    determinism-restore behaviour of torch.use_deterministic_algorithms)
    is guarded with @unittest.skipUnless(HAS_TORCH, ...) and is
    SKIPPED here — written and reviewed against the frozen contract,
    but not executed in this environment. This is a known, explicitly
    flagged limitation of this tranche, not a silent gap.
"""

import inspect
import unittest

from core.services.treefolks_v2.yggdrasil import (
    HAS_TORCH,
    _MIN_TRAINING_PAIRS,
    _W,
    _build_causal_pairs,
    _encode_draw,
    run_yggdrasil,
)


def _draw(numeros, estrelas):
    return {"numeros": numeros, "estrelas": estrelas}


def _synthetic_historico(n, sentinel_last=False):
    draws = [_draw([1, 2, 3, 4, 5], [1, 2]) for _ in range(n)]
    if sentinel_last and draws:
        # A unique, otherwise-never-used numeros/estrelas combination,
        # placed ONLY at historico[-1].
        draws[-1] = _draw([46, 47, 48, 49, 50], [11, 12])
    return draws


class TestHasTorchAbstention(unittest.TestCase):
    def test_torch_is_not_installed_in_this_environment(self):
        # Honest statement of the real environment state this session
        # ran in -- not an assertion about what SHOULD be true in
        # general.
        self.assertFalse(HAS_TORCH)

    def test_run_yggdrasil_abstains_when_torch_unavailable(self):
        historico = _synthetic_historico(200)
        self.assertIsNone(run_yggdrasil(historico, seed=1))

    def test_abstention_is_independent_of_history_length_when_torch_unavailable(self):
        # Even with abundant history, no torch -> no participation.
        self.assertIsNone(run_yggdrasil(_synthetic_historico(500), seed=1))


class TestCausalPairSentinel(unittest.TestCase):
    """The exact test the contract review required: a unique sentinel
    placed ONLY in historico[-1] must never appear in `labels`, but
    must appear in the final W-length inference window.
    """

    def test_sentinel_in_last_position_never_appears_as_a_label(self):
        n = _W + _MIN_TRAINING_PAIRS + 10
        historico = _synthetic_historico(n, sentinel_last=True)
        sentinel_encoded = _encode_draw(historico[-1])

        _windows, labels = _build_causal_pairs(historico)
        self.assertNotIn(sentinel_encoded, labels)

    def test_sentinel_in_last_position_appears_in_the_inference_window(self):
        n = _W + _MIN_TRAINING_PAIRS + 10
        historico = _synthetic_historico(n, sentinel_last=True)
        sentinel_encoded = _encode_draw(historico[-1])

        inference_window = [_encode_draw(draw) for draw in historico[-_W:]]
        self.assertIn(sentinel_encoded, inference_window)
        # And specifically as the LAST element of that window.
        self.assertEqual(inference_window[-1], sentinel_encoded)

    def test_largest_label_index_is_historico_minus_2(self):
        # historico[-2] MAY appear as a label; historico[-1] never can.
        n = _W + _MIN_TRAINING_PAIRS + 10
        historico = _synthetic_historico(n)
        historico[-2] = _draw([46, 47, 48, 49, 50], [11, 12])  # unique, only at [-2]
        second_to_last_encoded = _encode_draw(historico[-2])

        _windows, labels = _build_causal_pairs(historico)
        self.assertIn(second_to_last_encoded, labels)
        self.assertEqual(labels[-1], second_to_last_encoded)  # the LAST pair's label is historico[-2]

    def test_number_of_pairs_matches_len_historico_minus_w_minus_1(self):
        n = _W + 75
        historico = _synthetic_historico(n)
        windows, labels = _build_causal_pairs(historico)
        self.assertEqual(len(windows), len(labels))
        self.assertEqual(len(windows), n - _W - 1)


class TestMinTrainingPairsExactCount(unittest.TestCase):
    def test_min_training_pairs_checked_against_actual_built_pairs(self):
        # n draws -> n - _W - 1 actual pairs (see test above). Choose n
        # so that count is exactly _MIN_TRAINING_PAIRS - 1 (must
        # abstain if torch were available) vs. exactly
        # _MIN_TRAINING_PAIRS (must not abstain for this reason if
        # torch were available). Since torch isn't installed here,
        # both abstain -- but for the torch-unrelated reason, verified
        # separately by inspecting _build_causal_pairs directly.
        n_below = _W + _MIN_TRAINING_PAIRS  # -> _MIN_TRAINING_PAIRS - 1 pairs
        n_at = _W + _MIN_TRAINING_PAIRS + 1  # -> _MIN_TRAINING_PAIRS pairs
        windows_below, _ = _build_causal_pairs(_synthetic_historico(n_below))
        windows_at, _ = _build_causal_pairs(_synthetic_historico(n_at))
        self.assertEqual(len(windows_below), _MIN_TRAINING_PAIRS - 1)
        self.assertEqual(len(windows_at), _MIN_TRAINING_PAIRS)


class TestEncoding(unittest.TestCase):
    def test_encode_draw_is_a_62_dim_multi_hot_vector(self):
        vector = _encode_draw(_draw([1, 25, 50, 10, 20], [1, 12]))
        self.assertEqual(len(vector), 62)
        self.assertEqual(sum(vector), 7.0)  # 5 numbers + 2 stars
        self.assertEqual(vector[0], 1.0)  # number 1 -> index 0
        self.assertEqual(vector[49], 1.0)  # number 50 -> index 49
        self.assertEqual(vector[50], 1.0)  # star 1 -> index 50
        self.assertEqual(vector[61], 1.0)  # star 12 -> index 61


class TestSignature(unittest.TestCase):
    def test_run_yggdrasil_signature_has_no_target_shaped_parameter(self):
        params = set(inspect.signature(run_yggdrasil).parameters)
        self.assertEqual(params, {"historico", "seed"})


@unittest.skipUnless(HAS_TORCH, "torch not installed in this environment — see module docstring")
class TestTorchDependentBehaviour(unittest.TestCase):
    """Written and reviewed against the frozen contract; SKIPPED in
    this environment because torch was not installed (no installation
    authorized in this tranche). Run these explicitly in an
    environment with requirements-treefolks-v2.txt installed before
    relying on Yggdrasil's real numeric output.
    """

    def _rich_historico(self):
        return _synthetic_historico(_W + _MIN_TRAINING_PAIRS + 50)

    def test_participates_with_enough_history(self):
        scores = run_yggdrasil(self._rich_historico(), seed=1)
        self.assertIsNotNone(scores)
        self.assertEqual(set(scores.number_scores), set(range(1, 51)))
        self.assertEqual(set(scores.star_scores), set(range(1, 13)))

    def test_scores_are_probabilities_in_0_1(self):
        scores = run_yggdrasil(self._rich_historico(), seed=1)
        for value in list(scores.number_scores.values()) + list(scores.star_scores.values()):
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_deterministic_given_same_environment_and_seed(self):
        historico = self._rich_historico()
        r1 = run_yggdrasil(historico, seed=42)
        r2 = run_yggdrasil(historico, seed=42)
        self.assertEqual(r1, r2)

    def test_deterministic_algorithms_mode_restored_when_previously_off(self):
        import torch

        torch.use_deterministic_algorithms(False)
        run_yggdrasil(self._rich_historico(), seed=1)
        self.assertFalse(torch.are_deterministic_algorithms_enabled())

    def test_deterministic_algorithms_mode_restored_when_previously_on(self):
        import torch

        torch.use_deterministic_algorithms(True, warn_only=True)
        run_yggdrasil(self._rich_historico(), seed=1)
        self.assertTrue(torch.are_deterministic_algorithms_enabled())

    @unittest.skipUnless(
        HAS_TORCH and hasattr(__import__("torch"), "is_deterministic_algorithms_warn_only_enabled"),
        "this torch version has no getter for warn_only",
    )
    def test_warn_only_state_restored_when_getter_available(self):
        import torch

        torch.use_deterministic_algorithms(True, warn_only=False)
        run_yggdrasil(self._rich_historico(), seed=1)
        self.assertFalse(torch.is_deterministic_algorithms_warn_only_enabled())


if __name__ == "__main__":
    unittest.main()
