
import json
from pathlib import Path
from datetime import datetime, timezone


LIVRO = Path("legends/livro_personagens_lendarias.json")


def ler():
    try:
        return json.loads(LIVRO.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"nome": "Livro das Personagens Lendárias", "personagens": []}


def save(dados):
    LIVRO.parent.mkdir(parents=True, exist_ok=True)
    LIVRO.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def grau(numbers, stars):
    if numbers == 5 and stars == 2:
        return "IMORTAL"
    if numbers == 5:
        return "DIVINO"
    if numbers == 4 and stars == 2:
        return "DIAMANTE"
    if numbers == 4:
        return "PLATINA"
    if numbers == 3 and stars == 2:
        return "OURO"
    if numbers == 3 and stars == 1:
        return "PRATA"
    return "BRONZE"


def registar_lendas(results, actual_key, min_numbers=3, min_stars=2):
    livro = ler()
    existentes = {(p.get("arquivo_id"), p.get("chave", {}).get("numeros", []).__str__()) for p in livro.get("personagens", [])}
    novas = []

    for r in results:
        if r["acertos_numeros"] < min_numbers or r["acertos_estrelas"] < min_stars:
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
            "chave_real": actual_key,
            "registado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "estado": "ECO_LENDARIO",
        }
        livro.setdefault("personagens", []).append(entrada)
        novas.append(entrada)
        existentes.add(assinatura)

    livro["ultima_atualizacao"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save(livro)
    return novas
