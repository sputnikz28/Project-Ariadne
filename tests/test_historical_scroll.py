"""Tests for core/services/historical_scroll.py — build_scroll() must match
orders.librarians.converter.criar_pergaminho() everywhere except
assinatura.sha256, which must use the confirmed real convention
(identificadores.sha256_chave), not criar_pergaminho()'s own formula
(verified in-session to diverge — see verify_scroll_058.py history).
"""

import unittest

from core.services.historical_scroll import build_scroll
from orders.librarians.converter import criar_pergaminho


def make_draw_record(**overrides):
    draw = {
        "numero_sorteio": "062/2026",
        "data": "2026-08-04",
        "dia_semana": "terça-feira",
        "horario": {
            "hora_paris": "20:00:00",
            "hora_portugal": "19:00:00",
            "timestamp_utc": "2026-08-04T18:00:00+00:00",
        },
        "chave": {"numeros": [1, 2, 3, 4, 5], "estrelas": [1, 2], "formato": "1 2 3 4 5 + 1 2"},
        "ordem_saida": {"numeros": [5, 3, 1, 4, 2], "estrelas": [2, 1], "formato": "5 3 1 4 2 + 2 1"},
        "ordem_saida_disponivel": True,
        "estatisticas_chave": {
            "soma_numeros": 15, "media_numeros": 3.0, "mediana_numeros": 3,
            "desvio_padrao_populacional": 1.414, "amplitude": 4,
            "quantidade_pares": 2, "quantidade_impares": 3,
            "intervalos_ordenados": [1, 1, 1, 1],
            "distribuicao_por_dezenas": {"01-10": 5, "11-20": 0, "21-30": 0, "31-40": 0, "41-50": 0},
            "repetidos_sorteio_anterior": [], "estrelas_repetidas_sorteio_anterior": [],
        },
        "premios": {
            "categorias": None, "houve_vencedor_1_premio_total": None,
            "houve_vencedor_1_premio_portugal": None,
            "total_vencedores_todas_categorias": None,
            "total_vencedores_portugal_todas_categorias": None,
        },
        "astronomia": {
            "fase_lua": "Lua nova", "iluminacao_lunar_percent_aprox": 0.02,
            "idade_lunar_dias_aprox": 0.5, "eclipse_no_instante": False,
        },
        "identificadores": {
            "chave_canonica": "1-2-3-4-5+1-2",
            "sha256_chave": "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778a",
            "id_composto": "euromilhoes-062-2026",
        },
        "qualidade_dados": {
            "fonte_resultado": "texto fornecido pelo utilizador",
            "transcricao_manual": True, "ordem_saida_confirmada": True,
            "dados_financeiros_disponiveis": False, "categorias_premio_disponiveis": False,
            "campos_em_falta": [],
        },
    }
    draw.update(overrides)
    return draw


class TestBuildScroll(unittest.TestCase):
    def test_sha256_uses_identificadores_sha256_chave(self):
        draw = make_draw_record()
        scroll = build_scroll(draw)
        self.assertEqual(scroll["assinatura"]["sha256"], draw["identificadores"]["sha256_chave"])

    def test_sha256_differs_from_criar_pergaminho_own_formula(self):
        # Documents exactly why the override exists: criar_pergaminho()'s
        # own hash does NOT match the real convention for this fixture.
        draw = make_draw_record()
        raw = criar_pergaminho(draw)
        scroll = build_scroll(draw)
        self.assertNotEqual(raw["assinatura"]["sha256"], scroll["assinatura"]["sha256"])

    def test_rest_of_scroll_matches_criar_pergaminho_exactly(self):
        draw = make_draw_record()
        raw = criar_pergaminho(draw)
        scroll = build_scroll(draw)

        raw_rest = dict(raw)
        scroll_rest = dict(scroll)
        raw_rest["assinatura"] = {k: v for k, v in raw_rest["assinatura"].items() if k != "sha256"}
        scroll_rest["assinatura"] = {k: v for k, v in scroll_rest["assinatura"].items() if k != "sha256"}
        self.assertEqual(raw_rest, scroll_rest)

    def test_original_draw_record_is_not_mutated(self):
        draw = make_draw_record()
        snapshot = make_draw_record()  # independent deep-ish copy built the same way
        build_scroll(draw)
        self.assertEqual(draw, snapshot)

    def test_scroll_numero_sorteio_matches_draw(self):
        draw = make_draw_record(numero_sorteio="063/2026")
        scroll = build_scroll(draw)
        self.assertEqual(scroll["extracao"]["numero_sorteio"], "063/2026")


if __name__ == "__main__":
    unittest.main()
