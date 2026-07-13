from collections import Counter, defaultdict
from .base import CartographerOfChaos


class CartografoDasConstelacoes(CartographerOfChaos):
    name = "Eldran das Constelações"
    especialidade = "Rede de coocorrência e centralidade entre números"

    def analisar(self, history):
        cooc = defaultdict(Counter)
        for draw in history:
            nums = sorted(draw["numeros"])
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    a, b = nums[i], nums[j]
                    cooc[a][b] += 1
                    cooc[b][a] += 1

        # Degree centrality: total cooccurrences per number
        centralidade = {n: sum(cooc[n].values()) for n in range(1, 51)}
        top_central = sorted(centralidade.items(), key=lambda x: x[1], reverse=True)

        # Top 5 neighbours per number
        vizinhos = {
            n: [{"numero": m, "cooc": c} for m, c in cooc[n].most_common(5)]
            for n in range(1, 51)
        }

        # Global top pairs (deduplicated)
        vistos = set()
        top_pares = []
        for a in range(1, 51):
            for b, cnt in cooc[a].most_common(10):
                par = (min(a, b), max(a, b))
                if par not in vistos:
                    vistos.add(par)
                    top_pares.append({"par": list(par), "cooc": cnt})
        top_pares.sort(key=lambda x: x["cooc"], reverse=True)

        return {
            "titulo": "Livro das Constelações Numéricas",
            "total_sorteios": len(history),
            "top_centralidade": [{"numero": n, "peso": c} for n, c in top_central[:20]],
            "top_pares": top_pares[:30],
            "vizinhos": {str(n): viz for n, viz in vizinhos.items()},
        }
