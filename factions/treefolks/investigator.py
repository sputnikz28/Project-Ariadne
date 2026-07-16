from library.ariadne.engine import Ariadne


def investigate_full_moon():
    ariadne = Ariadne()
    response = ariadne.search_moon("Lua cheia")
    quantity = response["scrolls_encontrados"]
    confidence = min(0.20, quantity / 1000.0)
    return {
        "nome": "Grande Carvalho Ancestral",
        "classe": "Treefolk Investigador",
        "hipotese": "A fase lunar altera padrões observados nas extrações.",
        "consulta": response,
        "confianca": round(confidence, 4),
        "fantasma_estatistico": round(1.0 - confidence, 4),
        "conclusao": (
            "Amostra insuficiente para inferência."
            if quantity < 30
            else "Padrões apenas descritivos; validação temporal necessária."
        ),
    }
