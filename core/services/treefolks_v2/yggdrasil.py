"""Bosque de Yggdrasil — real, small LSTM. Optional PyTorch dependency
isolated entirely to this module — no other file in the project
imports torch, directly or indirectly. If torch is not installed,
run_yggdrasil() returns None (abstention), exactly like insufficient
training data — the caller (core/services/backtest_generators.py)
never needs to know which of the two happened; both are represented
identically via attempted_races.

Encoding: each historical draw -> a 62-dim multi-hot vector (indices
0..49 = numbers 1..50 present/absent, indices 50..61 = stars 1..12
present/absent).

Causal windowing: a training pair is (window of W consecutive draws
ending at position i, label = draw at position i+1), for i ranging
over W-1 .. len(historico)-3 — the largest possible label index is
len(historico)-2 (historico[-2]). historico[-1] is NEVER read as a
label under any circumstance; it is reserved exclusively for the final
W-length inference window. This is one position stricter than
Astérias' range(len(historico)-1): here every pair also needs a full
W-length window ending strictly before its own label, so the loop
bound is len(historico)-2, not len(historico)-1.

min_training_pairs=60 is checked against the ACTUAL number of pairs
built by _build_causal_pairs() — never an assumed closed-form formula
— so the threshold is exact regardless of how the windowing logic
might be refined later.

All hyperparameters below are frozen V1 values, approved before any
code was written, never adjusted after seeing Arena/backtest results:
W=20, hidden_size=32, num_layers=1, epochs=25 (fixed, no early
stopping), min_training_pairs=60, Adam(lr=1e-3, betas=(0.9,0.999),
eps=1e-8, weight_decay=0), full-batch (no minibatching), no gradient
clipping, BCEWithLogitsLoss on raw logits (sigmoid applied only at
inference).

Validation split: the last 10% of the causal training pairs, by time
(never shuffled), held out from training entirely. Purely an internal,
testable diagnostic (_train_and_score() returns the validation BCE
loss alongside the scores) — it never influences epochs, learning
rate, or any other hyperparameter, and is NOT persisted or surfaced as
candidate metadata in this tranche (run_yggdrasil()'s public return
value is scores only).

Determinism: the caller derives a seed from Yggdrasil's own namespaced
RNG stream and passes it in as a plain int; torch.manual_seed(seed) is
set immediately before model construction. torch.use_deterministic_algorithms
is set for the duration of training+inference only. The previous
global `mode` (torch.are_deterministic_algorithms_enabled(), always
observable) is always restored in a try/finally. The previous global
`warn_only` sub-setting is ALSO restored, but only when the installed
PyTorch version exposes
torch.is_deterministic_algorithms_warn_only_enabled() to observe it
first — this module never fabricates a `warn_only=False` guess for a
state it could not actually read; when that getter is unavailable, only
`mode` is restored (via torch.use_deterministic_algorithms(prev_mode),
which itself defaults warn_only to False as that call's own documented
default, not a claim about what the caller's own prior warn_only was).
CPU only — torch.device("cpu") unconditionally, never detecting/using
CUDA even if present. RESIDUAL LIMIT, documented explicitly: even with
these settings, floating-point reduction order can differ across
different PyTorch builds/CPU architectures. The guarantee here is
"same machine, same environment, same result" — not bit-identical
across arbitrary hardware.
"""
from __future__ import annotations

from core.services.treefolks_v2.common import TreefolkScores

try:
    import torch
    from torch import nn

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

_W = 20
_HIDDEN_SIZE = 32
_NUM_LAYERS = 1
_EPOCHS = 25
_MIN_TRAINING_PAIRS = 60
_LEARNING_RATE = 1e-3
_ADAM_BETAS = (0.9, 0.999)
_ADAM_EPS = 1e-8
_ADAM_WEIGHT_DECAY = 0.0
_VAL_FRACTION = 0.10
_INPUT_SIZE = 62


def _encode_draw(draw) -> list:
    vector = [0.0] * _INPUT_SIZE
    for number in draw["numeros"]:
        vector[number - 1] = 1.0
    for star in draw["estrelas"]:
        vector[49 + star] = 1.0
    return vector


def _build_causal_pairs(historico):
    """(windows, labels) — see module docstring for the exact loop
    bound and why historico[-1] can never appear in `labels`.
    """
    total_draws = len(historico)
    encoded = [_encode_draw(draw) for draw in historico]
    windows, labels = [], []
    for i in range(_W - 1, total_draws - 2):
        windows.append(encoded[i - _W + 1: i + 1])
        labels.append(encoded[i + 1])
    return windows, labels


if HAS_TORCH:

    class _YggdrasilLSTM(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=_INPUT_SIZE, hidden_size=_HIDDEN_SIZE,
                num_layers=_NUM_LAYERS, batch_first=True,
            )
            self.numbers_head = nn.Linear(_HIDDEN_SIZE, 50)
            self.stars_head = nn.Linear(_HIDDEN_SIZE, 12)

        def forward(self, x):
            lstm_out, _ = self.lstm(x)
            last_hidden = lstm_out[:, -1, :]
            return self.numbers_head(last_hidden), self.stars_head(last_hidden)


def _train_and_score(historico, seed: int) -> tuple[TreefolkScores, float] | None:
    """Returns (scores, validation_bce_loss), or None on abstention
    (no torch, or fewer than _MIN_TRAINING_PAIRS actual causal pairs).
    Separated from run_yggdrasil() so the validation loss is directly
    testable without changing TreefolkScores' shape.
    """
    if not HAS_TORCH:
        return None

    windows, labels = _build_causal_pairs(historico)
    if len(windows) < _MIN_TRAINING_PAIRS:
        return None

    val_size = max(1, round(len(windows) * _VAL_FRACTION))
    train_windows, train_labels = windows[:-val_size], labels[:-val_size]
    val_windows, val_labels = windows[-val_size:], labels[-val_size:]

    torch.manual_seed(seed)

    prev_mode = torch.are_deterministic_algorithms_enabled()
    has_warn_only_getter = hasattr(torch, "is_deterministic_algorithms_warn_only_enabled")
    if has_warn_only_getter:
        prev_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()

    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
        device = torch.device("cpu")

        model = _YggdrasilLSTM().to(device)
        optimizer = torch.optim.Adam(
            model.parameters(), lr=_LEARNING_RATE, betas=_ADAM_BETAS,
            eps=_ADAM_EPS, weight_decay=_ADAM_WEIGHT_DECAY,
        )
        criterion = nn.BCEWithLogitsLoss()

        x_train = torch.tensor(train_windows, dtype=torch.float32, device=device)
        y_train = torch.tensor(train_labels, dtype=torch.float32, device=device)
        y_train_numbers, y_train_stars = y_train[:, :50], y_train[:, 50:]

        model.train()
        for _epoch in range(_EPOCHS):
            optimizer.zero_grad()
            numbers_logits, stars_logits = model(x_train)
            loss = criterion(numbers_logits, y_train_numbers) + criterion(stars_logits, y_train_stars)
            loss.backward()
            optimizer.step()

        x_val = torch.tensor(val_windows, dtype=torch.float32, device=device)
        y_val = torch.tensor(val_labels, dtype=torch.float32, device=device)
        model.eval()
        with torch.no_grad():
            val_numbers_logits, val_stars_logits = model(x_val)
            val_loss = (
                criterion(val_numbers_logits, y_val[:, :50])
                + criterion(val_stars_logits, y_val[:, 50:])
            ).item()

            inference_window = [_encode_draw(draw) for draw in historico[-_W:]]
            x_infer = torch.tensor([inference_window], dtype=torch.float32, device=device)
            numbers_logits, stars_logits = model(x_infer)
            number_probs = torch.sigmoid(numbers_logits)[0].tolist()
            star_probs = torch.sigmoid(stars_logits)[0].tolist()
    finally:
        if has_warn_only_getter:
            torch.use_deterministic_algorithms(prev_mode, warn_only=prev_warn_only)
        else:
            torch.use_deterministic_algorithms(prev_mode)

    number_scores = {num: number_probs[num - 1] for num in range(1, 51)}
    star_scores = {star: star_probs[star - 1] for star in range(1, 13)}
    return TreefolkScores(number_scores=number_scores, star_scores=star_scores), val_loss


def run_yggdrasil(historico, seed: int) -> TreefolkScores | None:
    result = _train_and_score(historico, seed)
    if result is None:
        return None
    scores, _val_loss = result
    return scores
