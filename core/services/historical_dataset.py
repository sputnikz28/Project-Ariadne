"""Shared access to datasets/historical/euromillions/**/*.json — used by
both tests/test_historical_dataset.py and evaluate_heroes.py, so there is
one source of truth for "how do we discover and validate the historical
record" instead of two copies drifting apart.
"""

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

DATASET_ROOT = Path("datasets/historical/euromillions")

# Fields every draw entry must have, regardless of which year it's from —
# the intersection observed across the 2004-2026 files (some later years add
# extra fields like "fonte_ordem_saida", which isn't required here). This is
# the production source of truth for the shape of a draw record —
# validate_historical_dataset() below is the production validator built on
# top of it; callers (including tests) should import this constant or call
# that function rather than keeping a second copy.
REQUIRED_DRAW_FIELDS = frozenset({
    "numero_sorteio", "data", "dia_semana", "horario", "calendario",
    "chave", "ordem_saida", "ordem_saida_disponivel", "estatisticas_chave",
    "historico_no_conjunto", "estatisticas_financeiras", "premios",
    "astronomia", "identificadores", "qualidade_dados",
})


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


def _resolve_range_pair(regras, key, default):
    """Returns (lo, hi) for regras[key], falling back to the known
    Euromillions rule `default` when the field is missing or malformed —
    same fallback convention already used by validate_official_key() above
    — plus a problem string to report (None if regras[key] was fine).
    """
    value = regras.get(key)
    if isinstance(value, list) and len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
        return tuple(value), None
    return default, f"regras_representadas.{key} missing or malformed, defaulted to {default}"


def _validate_key_component(numero_sorteio, values, expected_count, lo, hi, label, problems):
    """Validates one chave component (numeros or estrelas): must be a list
    of `expected_count` distinct numbers within [lo, hi]. Appends problem
    strings to `problems`; never raises.
    """
    if not isinstance(values, list):
        problems.append(f"{numero_sorteio}: '{label}' must be a list, got {type(values).__name__}")
        return
    if len(values) != expected_count or not all(isinstance(v, (int, float)) and lo <= v <= hi for v in values):
        problems.append(f"{numero_sorteio}: invalid {label} range {values!r}")
        return
    if len(values) != len(set(values)):
        problems.append(f"{numero_sorteio}: duplicate {label} within draw {values}")


def validate_historical_dataset(dataset):
    """Pure structural validation of one already-loaded historical dataset
    dict (the content of one datasets/historical/euromillions/<year>/*.json
    file). Returns a list of human-readable problem descriptions; an empty
    list means the dataset is structurally sound. Encodes the same rules
    tests/test_historical_dataset.py enforces (duplicates, chronological
    order, schema consistency, required fields, valid ranges, interval
    metadata), so production callers such as register_official_draw.py
    don't have to re-derive them.

    Never raises: a malformed dataset always produces problem entries
    instead of an exception. Malformed structure is reported as its own
    explicit problem and validation continues with whatever can still be
    checked (falling back to the known Euromillions rules for number/star
    ranges when regras_representadas itself is missing or malformed,
    mirroring validate_official_key()'s existing fallback) — nothing is
    silently skipped. No file or network I/O.
    """
    problems = []

    if not isinstance(dataset, Mapping):
        problems.append(f"dataset must be a mapping, got {type(dataset).__name__}")
        return problems

    sorteios = dataset.get("sorteios")
    if not isinstance(sorteios, list):
        problems.append(f"dataset['sorteios'] must be a list, got {type(sorteios).__name__}")
        return problems

    if len(sorteios) == 0:
        problems.append("dataset contains no sorteios")
        return problems

    malformed_indices = [i for i, s in enumerate(sorteios) if not isinstance(s, Mapping)]
    if malformed_indices:
        problems.append(f"sorteios entries not a mapping at indices: {malformed_indices}")
    valid_sorteios = [s for s in sorteios if isinstance(s, Mapping)]
    if not valid_sorteios:
        return problems

    numero_ids = [s.get("numero_sorteio") for s in valid_sorteios]
    dup_ids = {n for n, count in Counter(numero_ids).items() if count > 1}
    if dup_ids:
        problems.append(f"duplicate numero_sorteio: {sorted(dup_ids, key=str)}")

    datas = [s.get("data") for s in valid_sorteios]
    dup_datas = {d for d, count in Counter(datas).items() if count > 1}
    if dup_datas:
        problems.append(f"duplicate data: {sorted(dup_datas, key=str)}")

    parsed = []
    for s in valid_sorteios:
        try:
            parsed.append(datetime.strptime(s.get("data"), "%Y-%m-%d"))
        except (TypeError, ValueError):
            parsed.append(None)
    if any(p is None for p in parsed):
        problems.append("one or more sorteios has an unparsable or missing 'data'")
    elif not all(parsed[i] < parsed[i + 1] for i in range(len(parsed) - 1)):
        problems.append("sorteios not strictly chronologically ordered")

    keysets = {frozenset(s.keys()) for s in valid_sorteios}
    if len(keysets) > 1:
        problems.append(f"inconsistent draw schemas across sorteios (found {len(keysets)} distinct key sets)")

    for s in valid_sorteios:
        missing = REQUIRED_DRAW_FIELDS - s.keys()
        if missing:
            problems.append(f"{s.get('numero_sorteio')}: missing fields {sorted(missing)}")

    regras = dataset.get("regras_representadas")
    if not isinstance(regras, Mapping):
        problems.append("dataset['regras_representadas'] is missing or not a mapping")
        regras = {}

    numero_range, range_problem = _resolve_range_pair(regras, "intervalo_numeros", (1, 50))
    if range_problem:
        problems.append(range_problem)
    numero_count = regras.get("numeros_por_chave")
    if not isinstance(numero_count, int):
        problems.append("regras_representadas.numeros_por_chave missing or not an int, defaulted to 5")
        numero_count = 5

    estrela_range, range_problem = _resolve_range_pair(regras, "intervalo_estrelas", (1, 12))
    if range_problem:
        problems.append(range_problem)
    estrela_count = regras.get("estrelas_por_chave")
    if not isinstance(estrela_count, int):
        problems.append("regras_representadas.estrelas_por_chave missing or not an int, defaulted to 2")
        estrela_count = 2

    for s in valid_sorteios:
        numero_sorteio = s.get("numero_sorteio")
        chave = s.get("chave")
        if not isinstance(chave, Mapping):
            problems.append(f"{numero_sorteio}: 'chave' missing or not a mapping")
            continue
        _validate_key_component(numero_sorteio, chave.get("numeros"), numero_count, *numero_range, "numeros", problems)
        _validate_key_component(numero_sorteio, chave.get("estrelas"), estrela_count, *estrela_range, "estrelas", problems)

    intervalo = dataset.get("intervalo")
    if intervalo is not None and not isinstance(intervalo, Mapping):
        problems.append("dataset['intervalo'] is not a mapping")
    elif isinstance(intervalo, Mapping):
        first, last = valid_sorteios[0], valid_sorteios[-1]
        if intervalo.get("quantidade_sorteios") != len(valid_sorteios):
            problems.append("intervalo.quantidade_sorteios mismatch")
        if intervalo.get("primeiro_sorteio") != first.get("numero_sorteio"):
            problems.append("intervalo.primeiro_sorteio mismatch")
        if intervalo.get("ultimo_sorteio") != last.get("numero_sorteio"):
            problems.append("intervalo.ultimo_sorteio mismatch")
        if intervalo.get("data_inicio") != first.get("data"):
            problems.append("intervalo.data_inicio mismatch")
        if intervalo.get("data_fim") != last.get("data"):
            problems.append("intervalo.data_fim mismatch")

    return problems
