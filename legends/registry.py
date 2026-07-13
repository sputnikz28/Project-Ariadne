
import json
from pathlib import Path
from datetime import datetime, timezone


LIVRO = Path("lendas/livro_personagens_lendarias.json")


def ler():
    try:
        return json.loads(LIVRO.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"nome": "Livro das Personagens Lendárias", "personagens": []}


def guardar(dados):
    LIVRO.parent.mkdir(parents=True, exist_ok=True)
    LIVRO.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def grau(numeros, estrelas):
    if numeros == 5 and estrelas == 2:
        return "IMORTAL"
    if numeros == 5:
        return "DIVINO"
    if numeros == 4 and estrelas == 2:
        return "DIAMANTE"
    if numeros == 4:
        return "PLATINA"
    if numeros == 3 and estrelas == 2:
        return "OURO"
    if numeros == 3 and estrelas == 1:
        return "PRATA"
    return "BRONZE"


def registar_lendas(resultados, chave_real, min_numeros=3, min_estrelas=2):
    livro = ler()
    existentes = {(p.get("arquivo_id"), p.get("chave", {}).get("numeros", []).__str__()) for p in livro.get("personagens", [])}
    novas = []

    for r in resultados:
        if r["acertos_numeros"] < min_numeros or r["acertos_estrelas"] < min_estrelas:
            continue
        assinatura = (r.get("id"), str(r.get("numeros")))
        if assinatura in existentes:
            continue

        entrada = {
            "arquivo_id": r.get("id"),
            "nome": r.get("nome"),
            "classe": r.get("classe"),
            "origem": r.get("origem"),
            "geracao": r.get("geracao"),
            "grau": grau(r["acertos_numeros"], r["acertos_estrelas"]),
            "feito": f"{r['acertos_numeros']} números + {r['acertos_estrelas']} estrelas",
            "chave": {
                "numeros": r.get("numeros"),
                "estrelas": r.get("estrelas"),
            },
            "chave_real": chave_real,
            "registado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "estado": "ECO_LENDARIO",
        }
        livro.setdefault("personagens", []).append(entrada)
        novas.append(entrada)
        existentes.add(assinatura)

    livro["ultima_atualizacao"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    guardar(livro)
    return novas
