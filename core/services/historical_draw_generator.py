"""Orchestrates the registration of new official Euromillions draws into
the canonical historical dataset — the schema and methodology consolidated
for draws 059-061/2026, generalized to any future draw.

Pure: no file or network I/O anywhere in this module. Statistics and
history come from core.services.historical_statistics; astronomy comes
from core.services.historical_astronomy; scroll generation is deliberately
NOT done here — that's core.services.historical_scroll.build_scroll(),
called by the CLI (register_official_draw.py), not by this module.
"""

from __future__ import annotations

import copy
import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from core.services.historical_astronomy import compute_astronomia
from core.services.historical_statistics import build_estatisticas_chave, build_historico_no_conjunto

DIAS_SEMANA_PT = (
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
)
# date.weekday(): Monday=0 ... Sunday=6. Euromillions draws Tuesday and Friday.
VALID_DRAW_WEEKDAYS = {1, 4}

_MES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}
_CAMPOS_EM_FALTA = (
    "receita_liquida_apostas_eur",
    "montante_para_premios_eur",
    "categorias_premio",
    "previsao_1_premio_com_jackpot_eur",
)
_NUMERO_SORTEIO_RE = re.compile(r"^(\d{3})/(\d{4})$")


@dataclass(frozen=True)
class DrawInput:
    numero_sorteio: str
    data: str  # "YYYY-MM-DD"
    numeros: tuple[int, ...]
    estrelas: tuple[int, ...]
    ordem_numeros: tuple[int, ...]
    ordem_estrelas: tuple[int, ...]


class DrawValidationError(ValueError):
    """A DrawInput failed validation against the existing dataset (or
    against other DrawInputs already accepted earlier in the same batch).
    Always raised before anything is generated — never mid-write.
    """


def dia_semana_for(d: date) -> str:
    return DIAS_SEMANA_PT[d.weekday()]


def _last_sunday(year: int, month: int) -> date:
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    offset = (last_day.weekday() - 6) % 7  # weekday(): Sunday=6
    return last_day - timedelta(days=offset)


def _is_eu_summer_time(d: date) -> bool:
    """Whether `d` is under EU summer time (DST), evaluated for this
    project's fixed evening draw time (18:00-19:00 UTC) — not a general
    time-of-day-aware check. The real transition instant is 01:00 UTC on
    the last Sunday of March (start) and the last Sunday of October (end);
    by evening on either transition day the new rule is already in effect,
    so comparing plain dates against those two Sundays (inclusive start,
    exclusive end) is exact for this project's draw time, though not for
    arbitrary times before 01:00 UTC on the transition day itself.
    """
    return _last_sunday(d.year, 3) <= d < _last_sunday(d.year, 10)


def validate_draw_input(draw_input: DrawInput, existing_sorteios: list[dict]) -> None:
    """Validates one DrawInput against the sorteios accumulated so far
    (pre-existing dataset entries plus any earlier DrawInputs already
    appended this run — see register_draws()). Raises DrawValidationError
    with a specific reason on the first problem found.
    """
    numero = draw_input.numero_sorteio

    if any(s.get("numero_sorteio") == numero for s in existing_sorteios):
        raise DrawValidationError(f"draw {numero} already exists in the dataset")

    try:
        draw_date = datetime.strptime(draw_input.data, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise DrawValidationError(f"draw {numero}: invalid date {draw_input.data!r}: {exc}") from exc

    if existing_sorteios:
        last_date = datetime.strptime(existing_sorteios[-1]["data"], "%Y-%m-%d").date()
        if draw_date <= last_date:
            raise DrawValidationError(
                f"draw {numero}: date {draw_input.data} is not strictly after the last "
                f"known draw date {existing_sorteios[-1]['data']}"
            )

    match = _NUMERO_SORTEIO_RE.match(numero)
    if not match:
        raise DrawValidationError(f"draw {numero}: numero_sorteio must match 'NNN/YYYY' format")
    ano_sorteio = int(match.group(2))
    if ano_sorteio != draw_date.year:
        raise DrawValidationError(
            f"draw {numero}: year in numero_sorteio ({ano_sorteio}) does not match "
            f"year in date {draw_input.data} ({draw_date.year})"
        )

    if draw_date.weekday() not in VALID_DRAW_WEEKDAYS:
        raise DrawValidationError(
            f"draw {numero}: date {draw_input.data} falls on a {dia_semana_for(draw_date)}, "
            f"Euromillions only draws on Tuesdays and Fridays"
        )

    if len(draw_input.numeros) != 5 or len(set(draw_input.numeros)) != 5 or not all(1 <= n <= 50 for n in draw_input.numeros):
        raise DrawValidationError(f"draw {numero}: numbers must be 5 distinct values in [1,50], got {draw_input.numeros}")

    if len(draw_input.estrelas) != 2 or len(set(draw_input.estrelas)) != 2 or not all(1 <= e <= 12 for e in draw_input.estrelas):
        raise DrawValidationError(f"draw {numero}: stars must be 2 distinct values in [1,12], got {draw_input.estrelas}")

    if set(draw_input.ordem_numeros) != set(draw_input.numeros) or len(draw_input.ordem_numeros) != len(draw_input.numeros):
        raise DrawValidationError(
            f"draw {numero}: output_order_numbers {draw_input.ordem_numeros} is not a permutation of numbers {draw_input.numeros}"
        )

    if set(draw_input.ordem_estrelas) != set(draw_input.estrelas) or len(draw_input.ordem_estrelas) != len(draw_input.estrelas):
        raise DrawValidationError(
            f"draw {numero}: output_order_stars {draw_input.ordem_estrelas} is not a permutation of stars {draw_input.estrelas}"
        )


def _build_horario(y: int, mo: int, d: int, summer: bool) -> dict[str, object]:
    paris_offset = "+02:00" if summer else "+01:00"
    portugal_offset = "+01:00" if summer else "+00:00"
    utc_hour = 18 if summer else 19
    return {
        "hora_paris": "20:00:00",
        "fuso_paris": "Europe/Paris",
        "timestamp_paris": f"{y:04d}-{mo:02d}-{d:02d}T20:00:00{paris_offset}",
        "hora_portugal": "19:00:00",
        "fuso_portugal": "Europe/Lisbon",
        "timestamp_portugal": f"{y:04d}-{mo:02d}-{d:02d}T19:00:00{portugal_offset}",
        "hora_utc": f"{utc_hour:02d}:00:00",
        "timestamp_utc": f"{y:04d}-{mo:02d}-{d:02d}T{utc_hour:02d}:00:00+00:00",
    }


def _build_calendario(y: int, mo: int, d: int, utc_hour: int) -> dict[str, object]:
    dt = date(y, mo, d)
    iso_year, iso_week, _ = dt.isocalendar()
    utc_dt = datetime(y, mo, d, utc_hour, 0, 0, tzinfo=timezone.utc)
    return {
        "ano": y,
        "mes": mo,
        "dia": d,
        "dia_do_ano": dt.timetuple().tm_yday,
        "semana_iso": iso_week,
        "ano_iso": iso_year,
        "trimestre": (mo - 1) // 3 + 1,
        "semestre": 1 if mo <= 6 else 2,
        "fim_de_semana": dt.weekday() >= 5,
        "timestamp_unix_utc": int(utc_dt.timestamp()),
    }


def build_draw_record(existing_sorteios: list[dict], draw_input: DrawInput) -> dict[str, object]:
    """Pure — builds the full draw record for draw_input, in the schema
    consolidated for 059-061. Does not append it anywhere and does not
    compute historico_no_conjunto (that needs the record's own index once
    appended — see register_draws()).
    """
    y, mo, d = (int(x) for x in draw_input.data.split("-"))
    dt = date(y, mo, d)
    summer = _is_eu_summer_time(dt)
    utc_hour = 18 if summer else 19

    numeros_sorted = sorted(draw_input.numeros)
    estrelas_sorted = sorted(draw_input.estrelas)
    chave_formato = f"{numeros_sorted[0]} {numeros_sorted[1]} {numeros_sorted[2]} {numeros_sorted[3]} {numeros_sorted[4]} + {estrelas_sorted[0]} {estrelas_sorted[1]}"
    ordem_n = list(draw_input.ordem_numeros)
    ordem_e = list(draw_input.ordem_estrelas)
    ordem_formato = f"{ordem_n[0]} {ordem_n[1]} {ordem_n[2]} {ordem_n[3]} {ordem_n[4]} + {ordem_e[0]} {ordem_e[1]}"

    if existing_sorteios:
        prev_numeros = existing_sorteios[-1]["chave"]["numeros"]
        prev_estrelas = existing_sorteios[-1]["chave"]["estrelas"]
    else:
        prev_numeros, prev_estrelas = [], []

    chave_canonica = f"{numeros_sorted[0]}-{numeros_sorted[1]}-{numeros_sorted[2]}-{numeros_sorted[3]}-{numeros_sorted[4]}+{estrelas_sorted[0]}-{estrelas_sorted[1]}"
    numero_part = draw_input.numero_sorteio.split("/")[0]

    return {
        "numero_sorteio": draw_input.numero_sorteio,
        "data": draw_input.data,
        "dia_semana": dia_semana_for(dt),
        "horario": _build_horario(y, mo, d, summer),
        "calendario": _build_calendario(y, mo, d, utc_hour),
        "chave": {"numeros": numeros_sorted, "estrelas": estrelas_sorted, "formato": chave_formato},
        "ordem_saida": {"numeros": ordem_n, "estrelas": ordem_e, "formato": ordem_formato},
        "ordem_saida_disponivel": True,
        "fonte_ordem_saida": "texto fornecido pelo utilizador",
        "estatisticas_chave": build_estatisticas_chave(numeros_sorted, estrelas_sorted, prev_numeros, prev_estrelas),
        "historico_no_conjunto": None,  # filled in by register_draws() once appended
        "estatisticas_financeiras": {
            "receita_liquida_apostas_eur": None,
            "montante_para_premios_eur": None,
            "percentagem_receita_para_premios": None,
            "previsao_1_premio_com_jackpot_eur": None,
            "registos_portugal": None,
            "combinacoes_registadas_portugal": None,
            "apostas_registadas_portugal": None,
            "combinacoes_por_registo": None,
            "apostas_por_registo": None,
            "receita_media_por_aposta_eur": None,
        },
        "premios": {
            "categorias": None,
            "houve_vencedor_1_premio_total": None,
            "houve_vencedor_1_premio_portugal": None,
            "total_vencedores_todas_categorias": None,
            "total_vencedores_portugal_todas_categorias": None,
        },
        "astronomia": compute_astronomia(y, mo, d, utc_hour, 0, 0),
        "identificadores": {
            "chave_canonica": chave_canonica,
            "sha256_chave": hashlib.sha256(chave_canonica.encode("utf-8")).hexdigest(),
            "id_composto": f"euromilhoes-{numero_part}-{y}",
        },
        "qualidade_dados": {
            "fonte_resultado": "texto fornecido pelo utilizador",
            "transcricao_manual": True,
            "ordem_saida_confirmada": True,
            "dados_financeiros_disponiveis": False,
            "categorias_premio_disponiveis": False,
            "campos_em_falta": list(_CAMPOS_EM_FALTA),
        },
    }


def _update_top_level_metadata(dataset: dict, novos_numeros: list[str]) -> None:
    sorteios = dataset["sorteios"]
    last = sorteios[-1]
    first = sorteios[0]
    dataset["intervalo"]["primeiro_sorteio"] = first["numero_sorteio"]
    dataset["intervalo"]["data_inicio"] = first["data"]
    dataset["intervalo"]["ultimo_sorteio"] = last["numero_sorteio"]
    dataset["intervalo"]["data_fim"] = last["data"]
    dataset["intervalo"]["quantidade_sorteios"] = len(sorteios)
    dataset["estado_dataset"] = (
        f"parcial para {last['data'][:4]}; inclui os sorteios 001 a {last['numero_sorteio'].split('/')[0]}, "
        f"até {int(last['data'][8:10])} de {_MES_PT[int(last['data'][5:7])]} de {last['data'][:4]}"
    )

    freq_n = {str(n): 0 for n in range(1, 51)}
    freq_e = {str(e): 0 for e in range(1, 13)}
    counts = Counter()
    for s in sorteios:
        for n in s["chave"]["numeros"]:
            freq_n[str(n)] += 1
        for e in s["chave"]["estrelas"]:
            freq_e[str(e)] += 1
        counts["com_ordem" if s.get("ordem_saida_disponivel") else "sem_ordem"] += 1
        if s["qualidade_dados"].get("dados_financeiros_disponiveis"):
            counts["com_financeiro"] += 1

    resumo = dataset["resumo_conjunto"]
    resumo["frequencia_numeros"] = freq_n
    resumo["frequencia_estrelas"] = freq_e
    resumo["ranking_numeros"] = sorted(
        ({"numero": int(k), "frequencia": v} for k, v in freq_n.items()),
        key=lambda x: (-x["frequencia"], x["numero"]),
    )
    resumo["ranking_estrelas"] = sorted(
        ({"estrela": int(k), "frequencia": v} for k, v in freq_e.items()),
        key=lambda x: (-x["frequencia"], x["estrela"]),
    )
    resumo["sorteios_com_ordem_saida"] = counts["com_ordem"]
    resumo["sorteios_sem_ordem_saida"] = counts["sem_ordem"]
    resumo["sorteios_com_dados_financeiros"] = counts["com_financeiro"]

    # Appends one cumulative note per registration run — matches the
    # convention already established in the real dataset (notas 5 and 8
    # in the committed 001-058 file each documented a coverage extension
    # the same way, without replacing earlier notes).
    dataset.setdefault("notas_metodologicas", []).append(
        f"O ficheiro cobre {last['data'][:4]} até ao sorteio {last['numero_sorteio']} "
        f"({int(last['data'][8:10])} de {_MES_PT[int(last['data'][5:7])]} de {last['data'][:4]}). "
        f"Os sorteios {', '.join(novos_numeros)} usam a mesma metodologia consolidada "
        f"em 059-061/2026 (Meeus para astronomia; iluminacao_lunar_percent_aprox em "
        f"fração 0-1; nomenclatura canónica de 8 fases lunares)."
    )


def register_draws(dataset: dict, draw_inputs: list[DrawInput]) -> dict[str, object]:
    """Pure — returns a NEW dataset dict (deep copy of `dataset`) with every
    draw_input appended in the given order and all top-level metadata
    (intervalo, estado_dataset, resumo_conjunto, notas_metodologicas)
    recomputed. Never mutates the `dataset` argument. Raises
    DrawValidationError on the first invalid input — nothing is returned
    partially in that case.
    """
    if not draw_inputs:
        raise DrawValidationError("no draws given to register")

    new_dataset = copy.deepcopy(dataset)
    sorteios = new_dataset["sorteios"]

    for draw_input in draw_inputs:
        validate_draw_input(draw_input, sorteios)
        record = build_draw_record(sorteios, draw_input)
        sorteios.append(record)
        record["historico_no_conjunto"] = build_historico_no_conjunto(sorteios, len(sorteios) - 1)

    _update_top_level_metadata(new_dataset, [di.numero_sorteio for di in draw_inputs])
    return new_dataset


def next_dataset_filename(current_name: str, last_numero_sorteio: str) -> str:
    """euromilhoes_2026_001_058_dataset_completo.json + "061/2026"
    -> euromilhoes_2026_001_061_dataset_completo.json
    """
    last_number = last_numero_sorteio.split("/")[0]
    new_name, count = re.subn(
        r"_\d{3}_dataset_completo\.json$",
        f"_{last_number}_dataset_completo.json",
        current_name,
    )
    if count != 1:
        raise ValueError(f"could not compute next dataset filename from {current_name!r}")
    return new_name
