
from library.ariadne.motor import Ariadne


def investigar_lua_cheia():
    ariadne = Ariadne()
    resposta = ariadne.search_moon("Lua cheia")
    quantidade = resposta["scrolls_encontrados"]
    confianca = min(0.20, quantidade / 1000.0)
    return {
        "nome": "Grande Carvalho Ancestral",
        "classe": "Treefolk Investigador",
        "hipotese": "A fase lunar altera padrões observados nas extrações.",
        "consulta": resposta,
        "confianca": round(confianca, 4),
        "fantasma_estatistico": round(1.0 - confianca, 4),
        "conclusao": (
            "Amostra insuficiente para inferência."
            if quantidade < 30
            else "Padrões apenas descritivos; validação temporal necessária."
        ),
    }
