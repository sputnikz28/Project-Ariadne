
from collections import Counter
from itertools import combinations
from pathlib import Path
from datetime import datetime

from amuletos.persistencia import guardar_livro, guardar_json, FUTURAS
from amuletos.fontes.web_estatisticas import descarregar


def _normalizar_historico(historico):
    vistos = set()
    saida = []
    for item in historico:
        try:
            data = str(item["data"])[:10]
            nums = tuple(sorted(int(n) for n in item["numeros"]))
            ests = tuple(sorted(int(e) for e in item["estrelas"]))
        except (KeyError, TypeError, ValueError):
            continue
        assinatura = (data, nums, ests)
        if len(nums) == 5 and len(set(nums)) == 5 and len(ests) == 2 and len(set(ests)) == 2 and assinatura not in vistos:
            vistos.add(assinatura)
            saida.append({
                "data": data,
                "numeros": list(nums),
                "estrelas": list(ests),
                "jackpot": int(item.get("jackpot", 0) or 0),
                "vencedores": int(item.get("vencedores", 0) or 0),
            })
    return sorted(saida, key=lambda x: x["data"])


def sincronizar_fontes(config):
    if not config.getboolean("BIBLIOTECA_OCULTA", "ativa", fallback=True):
        return []
    if not config.getboolean("BIBLIOTECA_OCULTA", "atualizar_ao_arrancar", fallback=False):
        return [{"estado": "ignorado", "motivo": "atualizar_ao_arrancar=false"}]

    timeout = config.getint("BIBLIOTECA_OCULTA", "timeout_segundos", fallback=8)
    fontes = [
        ("jogos_santa_casa", config.get("BIBLIOTECA_OCULTA", "fonte_jogos_santa_casa", fallback="")),
        ("euromillones_com", config.get("BIBLIOTECA_OCULTA", "fonte_euromillones", fallback="")),
        ("euro_millions_com", config.get("BIBLIOTECA_OCULTA", "fonte_euro_millions", fallback="")),
    ]
    return [descarregar(nome, url, timeout) for nome, url in fontes]


def construir_livros(config, historico, mundo):
    historico = _normalizar_historico(historico)
    freq_n = Counter()
    freq_e = Counter()
    pares = Counter()
    trios = Counter()
    gaps = Counter()
    ultima_n = {n: None for n in range(1, 51)}
    ultima_e = {e: None for e in range(1, 13)}

    for idx, sorteio in enumerate(historico):
        nums = sorteio["numeros"]
        ests = sorteio["estrelas"]
        freq_n.update(nums)
        freq_e.update(ests)
        pares.update(combinations(nums, 2))
        trios.update(combinations(nums, 3))
        gaps.update(nums[i + 1] - nums[i] for i in range(4))
        for n in nums:
            ultima_n[n] = idx
        for e in ests:
            ultima_e[e] = idx

    total = len(historico)
    atrasos_n = {
        n: total if ultima_n[n] is None else total - 1 - ultima_n[n]
        for n in range(1, 51)
    }
    atrasos_e = {
        e: total if ultima_e[e] is None else total - 1 - ultima_e[e]
        for e in range(1, 13)
    }

    ranking_quentes = sorted(range(1, 51), key=lambda n: (-freq_n[n], n))
    ranking_frios = sorted(range(1, 51), key=lambda n: (freq_n[n], -atrasos_n[n], n))

    livros = {}

    livros["grimorio_extracoes.json"] = {
        "nome": "Grimório de Todas as Extrações",
        "tipo": "historico_completo",
        "total_extracoes": total,
        "extracoes": historico,
        "nota": "Fonte canónica local usada para reconstruir os restantes livros.",
    }
    livros["livro_numeros_quentes.json"] = {
        "nome": "Livro das Chamas Frequentes",
        "tipo": "numeros_quentes",
        "numeros": [
            {"numero": n, "frequencia": freq_n[n], "atraso": atrasos_n[n]}
            for n in ranking_quentes
        ],
    }
    livros["livro_numeros_frios.json"] = {
        "nome": "Livro dos Esquecidos",
        "tipo": "numeros_frios",
        "numeros": [
            {"numero": n, "frequencia": freq_n[n], "atraso": atrasos_n[n]}
            for n in ranking_frios
        ],
    }
    livros["livro_pares_sagrados.json"] = {
        "nome": "Livro dos Pares Sagrados",
        "tipo": "pares_mais_frequentes",
        "pares": [
            {"numeros": list(par), "vezes": vezes}
            for par, vezes in pares.most_common(100)
        ],
    }
    livros["livro_trios_proibidos.json"] = {
        "nome": "Livro dos Trios Proibidos",
        "tipo": "trios_mais_frequentes",
        "trios": [
            {"numeros": list(trio), "vezes": vezes}
            for trio, vezes in trios.most_common(100)
        ],
    }
    livros["livro_estrelas.json"] = {
        "nome": "Atlas das Doze Luzes",
        "tipo": "estatisticas_estrelas",
        "estrelas": [
            {"estrela": e, "frequencia": freq_e[e], "atraso": atrasos_e[e]}
            for e in sorted(range(1, 13), key=lambda e: (-freq_e[e], e))
        ],
    }
    livros["livro_atrasos.json"] = {
        "nome": "Crónica dos Números Ausentes",
        "tipo": "atrasos",
        "numeros": [
            {"numero": n, "atraso": atrasos_n[n], "frequencia": freq_n[n]}
            for n in sorted(range(1, 51), key=lambda n: (-atrasos_n[n], n))
        ],
        "estrelas": [
            {"estrela": e, "atraso": atrasos_e[e], "frequencia": freq_e[e]}
            for e in sorted(range(1, 13), key=lambda e: (-atrasos_e[e], e))
        ],
    }
    livros["livro_gaps.json"] = {
        "nome": "Geometria Secreta da Teia",
        "tipo": "gaps",
        "gaps": [{"gap": g, "vezes": v} for g, v in gaps.most_common()],
    }

    ultima = historico[-1] if historico else None
    proxima = {
        "livro": "Livro das Extrações por Cumprir",
        "data": mundo["data"],
        "hora_local": mundo["hora"],
        "local": mundo["local"],
        "timezone": mundo["timezone"],
        "estado": "aguarda_extracao",
        "jackpot": mundo.get("jackpot", 0),
        "ultima_chave_conhecida": ultima,
        "chave_real": None,
        "confirmada_por": [],
        "conselho": {
            "chave_original": None,
            "estrelas_originais": None,
            "chave_corrompida": None,
            "estrelas_corrompidas": None,
        },
    }
    livros["livro_proximas_extracoes.json"] = {
        "nome": "Livro das Extrações por Cumprir",
        "extracoes": [proxima],
    }

    for nome, conteudo in livros.items():
        guardar_livro(nome, conteudo)

    identificador = f"{mundo['data']}_{mundo['local'].lower().replace(' ', '_')}_{mundo['hora'].replace(':', '')}.json"
    guardar_json(FUTURAS / identificador, proxima)

    return {
        "total_extracoes": total,
        "livros_criados": list(livros),
        "quentes_top10": ranking_quentes[:10],
        "frios_top10": ranking_frios[:10],
        "pares_top10": [{"numeros": list(p), "vezes": v} for p, v in pares.most_common(10)],
        "trios_top10": [{"numeros": list(t), "vezes": v} for t, v in trios.most_common(10)],
        "proxima_extracao": proxima,
    }


def atualizar_livro_proxima_extracao(mundo, resultado, corrupcao):
    identificador = f"{mundo['data']}_{mundo['local'].lower().replace(' ', '_')}_{mundo['hora'].replace(':', '')}.json"
    path = FUTURAS / identificador
    from amuletos.persistencia import ler_json
    registo = ler_json(path, {})
    if not registo:
        return
    registo["conselho"] = {
        "chave_original": resultado["chave"][0],
        "estrelas_originais": resultado["chave"][1],
        "chave_corrompida": corrupcao["chave_corrompida"][0],
        "estrelas_corrompidas": corrupcao["chave_corrompida"][1],
    }
    guardar_json(path, registo)
