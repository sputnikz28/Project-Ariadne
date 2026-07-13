from collections import defaultdict
from .base import CartografoDoCaos


class CronistaDoCiclos(CartografoDoCaos):
    nome = "Vesara dos Intervalos"
    especialidade = "Atrasos históricos, médias, máximos, ciclos completos"

    def analisar(self, historico):
        total = len(historico)

        # Per-number: list of draw indices where it appeared
        aparicoes = defaultdict(list)
        for idx, draw in enumerate(historico):
            for n in draw["numeros"]:
                aparicoes[n].append(idx)

        analise = {}
        for n in range(1, 51):
            idxs = aparicoes.get(n, [])
            if not idxs:
                analise[n] = {
                    "aparicoes": 0,
                    "atraso_atual": total,
                    "atraso_medio": None,
                    "atraso_max": None,
                    "atraso_min": None,
                    "variancia": None,
                }
                continue

            gaps = []
            if idxs[0] > 0:
                gaps.append(idxs[0])
            for i in range(1, len(idxs)):
                gaps.append(idxs[i] - idxs[i - 1])
            atraso_atual = total - 1 - idxs[-1]
            media = sum(gaps) / len(gaps) if gaps else None

            analise[n] = {
                "aparicoes": len(idxs),
                "atraso_atual": atraso_atual,
                "atraso_medio": round(media, 1) if media is not None else None,
                "atraso_max": max(gaps) if gaps else None,
                "atraso_min": min(gaps) if gaps else None,
                "variancia": round(
                    sum((g - media) ** 2 for g in gaps) / len(gaps), 1
                ) if len(gaps) > 1 else None,
            }

        # Complete cycles: how many draws until all 50 numbers appear at least once
        ciclos = []
        vistos = set()
        inicio = 0
        for idx, draw in enumerate(historico):
            for n in draw["numeros"]:
                vistos.add(n)
            if len(vistos) == 50:
                ciclos.append(idx - inicio + 1)
                vistos = set()
                inicio = idx + 1

        return {
            "titulo": "Livro dos Ciclos Eternos",
            "total_sorteios": total,
            "analise_por_numero": {str(n): v for n, v in analise.items()},
            "ciclos_completos": {
                "quantidade": len(ciclos),
                "media_sorteios": round(sum(ciclos) / len(ciclos), 1) if ciclos else None,
                "menor_ciclo": min(ciclos) if ciclos else None,
                "maior_ciclo": max(ciclos) if ciclos else None,
                "lista": ciclos,
            },
        }
