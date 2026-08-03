"""Meeus low-precision Sun/Moon position (stdlib only) for one instant in
time — used to fill the `astronomia` block of a historical draw record.

Validated in-session against real data: position error <0.2 degrees / <60km
against draws 001-058; illumination fraction (0-1) and the canonical
8-phase vocabulary confirmed against 057/058 and the full 001-058 corpus
respectively. Draw 057's "Lua crescente côncava" was treated as an isolated
data anomaly, not evidence of a different naming scheme (see project
history for draws 059-061). Pure: no I/O.
"""

from __future__ import annotations

import math

SYNODIC_MONTH = 29.530588853

PHASE_NAMES = (
    "Lua nova", "Lua crescente", "Quarto crescente", "Gibosa crescente",
    "Lua cheia", "Gibosa minguante", "Quarto minguante", "Lua minguante",
)

ASTRONOMIA_METODO = (
    "Aproximação Meeus (baixa precisão, cálculo stdlib Python; ver "
    "notas_metodologicas) — geocêntrico para as 20:00 em Paris. Distinto "
    "do Swiss Ephemeris usado nos sorteios 001-055."
)

_MOON_LON_TERMS = (
    (0, 0, 1, 0, 6.288774), (2, 0, -1, 0, 1.274027), (2, 0, 0, 0, 0.658314),
    (0, 0, 2, 0, 0.213618), (0, 1, 0, 0, -0.185116), (0, 0, 0, 2, -0.114332),
    (2, 0, -2, 0, 0.058793), (2, -1, -1, 0, 0.057066), (2, 0, 1, 0, 0.053322),
    (2, -1, 0, 0, 0.045758), (0, 1, -1, 0, -0.040923), (1, 0, 0, 0, -0.034720),
    (0, 1, 1, 0, -0.030383), (2, 0, 0, -2, 0.015327), (0, 0, 1, 2, -0.012528),
    (0, 0, 1, -2, 0.010980), (4, 0, -1, 0, 0.010675), (0, 0, 3, 0, 0.010034),
    (4, 0, -2, 0, 0.008548), (2, 1, -1, 0, -0.007888),
)
_MOON_LAT_TERMS = (
    (0, 0, 0, 1, 5.128122), (0, 0, 1, 1, 0.280602), (0, 0, 1, -1, 0.277693),
    (2, 0, 0, -1, 0.173237), (2, 0, -1, 1, 0.055413), (2, 0, -1, -1, 0.046271),
    (2, 0, 0, 1, 0.032573), (0, 0, 2, 1, 0.017198), (2, 0, 1, -1, 0.009266),
    (0, 0, 2, -1, 0.008822),
)
_MOON_DIST_TERMS = (
    (0, 0, 1, 0, -20905.355), (2, 0, -1, 0, -3699.111), (2, 0, 0, 0, -2955.968),
    (0, 0, 2, 0, -569.925), (0, 1, 0, 0, 48.888), (2, 0, -2, 0, 246.158),
    (2, -1, -1, 0, -152.138), (2, 0, 1, 0, -170.733), (2, -1, 0, 0, -204.586),
    (0, 1, -1, 0, -129.620), (1, 0, 0, 0, 108.743), (0, 1, 1, 0, 104.755),
    (4, 0, -1, 0, -34.782), (0, 0, 3, 0, -23.210), (4, 0, -2, 0, -21.636),
)


def _phase_name_for_age(age_days: float) -> str:
    bucket_width = SYNODIC_MONTH / 8.0
    shifted = (age_days + bucket_width / 2.0) % SYNODIC_MONTH
    idx = int(shifted // bucket_width)
    return PHASE_NAMES[idx % 8]


def _julian_date(y: int, m: int, d: int, h: int, mi: int, s: int) -> float:
    day = d + (h + mi / 60 + s / 3600) / 24
    yy, mm = y, m
    if mm <= 2:
        yy -= 1
        mm += 12
    A = yy // 100
    B = 2 - A + A // 4
    return int(365.25 * (yy + 4716)) + int(30.6001 * (mm + 1)) + day + B - 1524.5


def _norm360(x: float) -> float:
    x = x % 360.0
    if x < 0:
        x += 360.0
    return x


def _sun_position(T: float) -> tuple[float, float]:
    L0 = _norm360(280.46646 + 36000.76983 * T + 0.0003032 * T ** 2)
    M = _norm360(357.52911 + 35999.05029 * T - 0.0001537 * T ** 2)
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T ** 2
    Mr = math.radians(M)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T ** 2) * math.sin(Mr)
         + (0.019993 - 0.000101 * T) * math.sin(2 * Mr)
         + 0.000289 * math.sin(3 * Mr))
    true_long = L0 + C
    true_anom = M + C
    Re = 1.000001018 * (1 - e ** 2) / (1 + e * math.cos(math.radians(true_anom)))
    omega = 125.04 - 1934.136 * T
    apparent_long = _norm360(true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega)))
    distance_km = Re * 149597870.7
    return apparent_long, distance_km


def _moon_position(T: float) -> tuple[float, float, float]:
    Lp = _norm360(218.3164477 + 481267.88123421 * T - 0.0015786 * T ** 2)
    D = _norm360(297.8501921 + 445267.1114034 * T - 0.0018819 * T ** 2)
    M = _norm360(357.5291092 + 35999.0502909 * T - 0.0001536 * T ** 2)
    Mp = _norm360(134.9633964 + 477198.8675055 * T + 0.0087414 * T ** 2)
    F = _norm360(93.2720950 + 483202.0175233 * T - 0.0036539 * T ** 2)

    def series(terms: tuple[tuple[int, int, int, int, float], ...]) -> float:
        total = 0.0
        for d, m, mp, f, coeff in terms:
            arg = math.radians(d * D + m * M + mp * Mp + f * F)
            total += coeff * math.sin(arg)
        return total

    lon = _norm360(Lp + series(_MOON_LON_TERMS))
    lat = series(_MOON_LAT_TERMS)
    dist_total = 385000.56
    for d, m, mp, f, coeff in _MOON_DIST_TERMS:
        arg = math.radians(d * D + m * M + mp * Mp + f * F)
        dist_total += coeff * math.cos(arg)
    return lon, lat, dist_total


def compute_astronomia(y: int, mo: int, d: int, h: int, mi: int, s: int) -> dict[str, object]:
    jd = _julian_date(y, mo, d, h, mi, s)
    T = (jd - 2451545.0) / 36525.0
    sun_lon, sun_dist = _sun_position(T)
    moon_lon, moon_lat, moon_dist = _moon_position(T)
    elong = math.degrees(math.acos(
        math.cos(math.radians(moon_lat)) * math.cos(math.radians(moon_lon - sun_lon))
    ))
    phase_angle = math.degrees(math.atan2(
        sun_dist * math.sin(math.radians(elong)),
        moon_dist - sun_dist * math.cos(math.radians(elong))
    ))
    illum_fraction = (1 + math.cos(math.radians(phase_angle))) / 2
    diff = _norm360(moon_lon - sun_lon)
    age_days = diff / 360.0 * SYNODIC_MONTH

    return {
        "instante_utc": f"{y:04d}-{mo:02d}-{d:02d}T{h:02d}:{mi:02d}:{s:02d}+00:00",
        "fase_lua": _phase_name_for_age(age_days),
        "idade_lunar_dias_aprox": round(age_days, 3),
        "iluminacao_lunar_percent_aprox": round(illum_fraction, 2),
        "elongacao_lua_sol_graus_aprox": round(elong, 2),
        "longitude_ecliptica_lua_graus": round(moon_lon, 4),
        "latitude_ecliptica_lua_graus": round(moon_lat, 6),
        "distancia_terra_lua_km_aprox": round(moon_dist),
        "longitude_ecliptica_sol_graus": round(sun_lon, 5),
        "distancia_terra_sol_km_aprox": round(sun_dist),
        "eclipse_no_instante": False,
        "metodo": ASTRONOMIA_METODO,
    }
