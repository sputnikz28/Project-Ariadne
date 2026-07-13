from collections import Counter, defaultdict
from .base import CartografoDoCaos


class OracleDeMarkov(CartografoDoCaos):
    nome = "Oryn dos Ecos Sequenciais"
    especialidade = "Transições entre sorteios, vizinhança, sequências consecutivas"

    def analisar(self, historico):
        total = len(historico)
        if total < 2:
            return {"titulo": "Livro dos Ecos Sequenciais", "total_sorteios": total}

        # Markov transitions: after number X in draw i, who appears in draw i+1?
        transicoes = defaultdict(Counter)
        for i in range(total - 1):
            for a in historico[i]["numeros"]:
                for b in historico[i + 1]["numeros"]:
                    transicoes[a][b] += 1

        # Same-draw neighbourhood (who appears together with X most often?)
        vizinhanca = defaultdict(Counter)
        for draw in historico:
            nums = draw["numeros"]
            for n in nums:
                for m in nums:
                    if m != n:
                        vizinhanca[n][m] += 1

        # Consecutive sequences in same draw
        duplas_consec = Counter()
        triplas_consec = Counter()
        for draw in historico:
            s = sorted(draw["numeros"])
            for i in range(len(s) - 1):
                if s[i + 1] == s[i] + 1:
                    duplas_consec[(s[i], s[i + 1])] += 1
                    if i < len(s) - 2 and s[i + 2] == s[i] + 2:
                        triplas_consec[(s[i], s[i + 1], s[i + 2])] += 1

        # Proportion of draws with at least one consecutive pair
        com_consec = sum(
            1 for draw in historico
            if any(
                sorted(draw["numeros"])[j + 1] == sorted(draw["numeros"])[j] + 1
                for j in range(4)
            )
        )

        return {
            "titulo": "Livro dos Ecos Sequenciais",
            "total_sorteios": total,
            "transicoes": {
                str(n): [{"numero": m, "contagem": c} for m, c in transicoes[n].most_common(5)]
                for n in range(1, 51)
            },
            "vizinhanca": {
                str(n): [{"numero": m, "contagem": c} for m, c in vizinhanca[n].most_common(5)]
                for n in range(1, 51)
            },
            "consecutivas": {
                "sorteios_com_par_consecutivo": com_consec,
                "pct_com_consecutivo": round(com_consec / total * 100, 1),
                "top_duplas": [
                    {"dupla": list(d), "contagem": c}
                    for d, c in duplas_consec.most_common(20)
                ],
                "top_triplas": [
                    {"tripla": list(t), "contagem": c}
                    for t, c in triplas_consec.most_common(10)
                ],
            },
        }
