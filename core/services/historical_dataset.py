"""Shared access to datasets/historical/euromillions/**/*.json — used by
both tests/test_historical_dataset.py and evaluate_heroes.py, so there is
one source of truth for "how do we discover and validate the historical
record" instead of two copies drifting apart.
"""

import json
from pathlib import Path

DATASET_ROOT = Path("datasets/historical/euromillions")


class DrawLookupError(ValueError):
    pass


def discover_datasets(root=None):
    root = Path(root) if root is not None else DATASET_ROOT
    return sorted(root.glob("*/*.json"))


def load_dataset(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_draw(sorteio_id, root=None):
    """Search every discovered dataset file for numero_sorteio == sorteio_id.

    Returns (draw_dict, dataset_path, dataset). Raises DrawLookupError if
    the draw is missing, or if it appears more than once across files
    (should be structurally impossible given test_historical_dataset.py's
    uniqueness checks, but this is re-validated defensively here rather
    than trusted blindly).
    """
    matches = []
    for path in discover_datasets(root):
        dataset = load_dataset(path)
        for draw in dataset.get("sorteios", []):
            if draw.get("numero_sorteio") == sorteio_id:
                matches.append((draw, path, dataset))

    if not matches:
        raise DrawLookupError(f"draw {sorteio_id!r} not found in any historical dataset")
    if len(matches) > 1:
        found_in = [str(p) for _, p, _ in matches]
        raise DrawLookupError(f"draw {sorteio_id!r} found in multiple dataset files: {found_in}")
    return matches[0]


def validate_official_key(draw, dataset):
    """Validate a resolved draw's key against its own dataset's declared
    rules (regras_representadas) — not a hardcoded global assumption.
    """
    regras = dataset.get("regras_representadas", {})
    lo, hi = regras.get("intervalo_numeros", [1, 50])
    count_n = regras.get("numeros_por_chave", 5)
    lo_e, hi_e = regras.get("intervalo_estrelas", [1, 12])
    count_e = regras.get("estrelas_por_chave", 2)

    numeros = draw["chave"]["numeros"]
    estrelas = draw["chave"]["estrelas"]

    if len(numeros) != count_n or not all(lo <= n <= hi for n in numeros) or len(set(numeros)) != len(numeros):
        raise DrawLookupError(f"draw {draw.get('numero_sorteio')!r} has an invalid main-number key: {numeros}")
    if len(estrelas) != count_e or not all(lo_e <= e <= hi_e for e in estrelas) or len(set(estrelas)) != len(estrelas):
        raise DrawLookupError(f"draw {draw.get('numero_sorteio')!r} has an invalid star key: {estrelas}")
