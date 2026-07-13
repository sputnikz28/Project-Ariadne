
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


def guardar_json(path, dados):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def criar_pergaminho(sorteio):
    numero = sorteio["numero_sorteio"].split("/")[0]
    chave = sorteio["chave"]
    stats = sorteio.get("estatisticas_chave") or {}
    astronomia = sorteio.get("astronomia") or {}
    horario = sorteio.get("horario") or {}
    premios = sorteio.get("premios") or {}

    pergaminho = {
        "id": f"PERG-2026-{numero}",
        "titulo": f"Pergaminho da Extração {sorteio['numero_sorteio']}",
        "biblioteca": "Grande Grimório das Extrações",
        "estado": "SELADO",
        "raridade": "Sagrado",
        "data": {
            "extracao": sorteio["data"],
            "dia_semana": sorteio.get("dia_semana"),
            "hora_paris": horario.get("hora_paris"),
            "hora_portugal": horario.get("hora_portugal"),
            "timestamp_utc": horario.get("timestamp_utc"),
        },
        "extracao": {
            "numero_sorteio": sorteio["numero_sorteio"],
            "numeros": chave["numeros"],
            "estrelas": chave["estrelas"],
            "ordem_saida": sorteio.get("ordem_saida"),
            "ordem_saida_disponivel": sorteio.get("ordem_saida_disponivel", False),
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
        "qualidade_dados": sorteio.get("qualidade_dados"),
        "assinatura": {
            "escriba": "Orion dos Arquivos",
            "selo": "Biblioteca Eterna",
            "sha256": hashlib.sha256(
                json.dumps(chave, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "integridade": "100%",
        },
        "anotacoes": [],
    }
    return pergaminho


def importar_dataset(caminho_dataset, pasta_destino):
    dataset = json.loads(Path(caminho_dataset).read_text(encoding="utf-8"))
    criados = []
    for sorteio in dataset.get("sorteios", []):
        pergaminho = criar_pergaminho(sorteio)
        numero = sorteio["numero_sorteio"].split("/")[0]
        path = Path(pasta_destino) / f"{numero}.json"
        guardar_json(path, pergaminho)
        criados.append(path)
    return criados
