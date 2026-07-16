
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


def save_json(path, dados):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def criar_pergaminho(draw):
    numero = draw["numero_sorteio"].split("/")[0]
    key = draw["chave"]
    stats = draw.get("estatisticas_chave") or {}
    astronomia = draw.get("astronomia") or {}
    horario = draw.get("horario") or {}
    premios = draw.get("premios") or {}

    scroll = {
        "id": f"PERG-2026-{numero}",
        "titulo": f"Pergaminho da Extração {draw['numero_sorteio']}",
        "biblioteca": "Grande Grimório das Extrações",
        "estado": "SELADO",
        "raridade": "Sagrado",
        "data": {
            "extracao": draw["data"],
            "dia_semana": draw.get("dia_semana"),
            "hora_paris": horario.get("hora_paris"),
            "hora_portugal": horario.get("hora_portugal"),
            "timestamp_utc": horario.get("timestamp_utc"),
        },
        "extracao": {
            "numero_sorteio": draw["numero_sorteio"],
            "numeros": key["numeros"],
            "estrelas": key["estrelas"],
            "ordem_saida": draw.get("ordem_saida"),
            "ordem_saida_disponivel": draw.get("ordem_saida_disponivel", False),
        },
        "estatisticas": {
            "soma": stats.get("soma_numeros"),
            "media": stats.get("media_numeros"),
            "mediana": stats.get("mediana_numeros"),
            "desvio_padrao": stats.get("desvio_padrao_populacional"),
            "amplitude": stats.get("amplitude"),
            "pares": stats.get("quantidade_pares"),
            "impares": stats.get("quantidade_impares"),
            "gaps": stats.get("intervalos_ordenados"),
            "distribuicao_dezenas": stats.get("distribuicao_por_dezenas"),
            "repetidos_anterior": stats.get("repetidos_sorteio_anterior", []),
            "estrelas_repetidas_anterior": stats.get("estrelas_repetidas_sorteio_anterior", []),
        },
        "astronomia": {
            "fase_lua": astronomia.get("fase_lua"),
            "iluminacao_percent": astronomia.get("iluminacao_lunar_percent_aprox"),
            "idade_lunar_dias": astronomia.get("idade_lunar_dias_aprox"),
            "eclipse": astronomia.get("eclipse_no_instante"),
        },
        "premios": premios,
        "qualidade_dados": draw.get("qualidade_dados"),
        "assinatura": {
            "escriba": "Orion dos Arquivos",
            "selo": "Biblioteca Eterna",
            "sha256": hashlib.sha256(
                json.dumps(key, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "integridade": "100%",
        },
        "anotacoes": [],
    }
    return scroll


def importar_dataset(caminho_dataset, pasta_destino):
    dataset = json.loads(Path(caminho_dataset).read_text(encoding="utf-8"))
    criados = []
    for draw in dataset.get("sorteios", []):
        scroll = criar_pergaminho(draw)
        numero = draw["numero_sorteio"].split("/")[0]
        path = Path(pasta_destino) / f"{numero}.json"
        save_json(path, scroll)
        criados.append(path)
    return criados
