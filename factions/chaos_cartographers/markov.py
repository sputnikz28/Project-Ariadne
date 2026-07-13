from collections import Counter, defaultdict
from .base import CartographerOfChaos


class OracleDeMarkov(CartographerOfChaos):
    name = "Oryn dos Ecos Sequenciais"
    especialidade = "Transições entre sorteios, vizinhança, sequências consecutivas"

    def analisar(self, history):
        total = len(history)
        if total < 2:
            return {"titulo": "Livro dos Ecos Sequenciais", "total_sorteios": total}

        # Markov transitions: after number X in draw i, who appears in draw i+1?
        transitions = defaultdict(Counter)
        for i in range(total - 1):
            for a in history[i]["numeros"]:
                for b in history[i + 1]["numeros"]:
                    transitions[a][b] += 1

        # Same-draw neighbourhood (who appears together with X most often?)
        vizinhanca = defaultdict(Counter)
        for draw in history:
            nums = draw["numeros"]
            for n in nums:
                for m in nums:
                    if m != n:
                        vizinhanca[n][m] += 1

        # Consecutive sequences in same draw
        consecutive_pairs = Counter()
        consecutive_triples = Counter()
        for draw in history:
            s = sorted(draw["numeros"])
            for i in range(len(s) - 1):
                if s[i + 1] == s[i] + 1:
                    consecutive_pairs[(s[i], s[i + 1])] += 1
                    if i < len(s) - 2 and s[i + 2] == s[i] + 2:
                        consecutive_triples[(s[i], s[i + 1], s[i + 2])] += 1

        # Proportion of draws with at least one consecutive pair
        com_consec = sum(
            1 for draw in history
            if any(
                sorted(draw["numeros"])[j + 1] == sorted(draw["numeros"])[j] + 1
                for j in range(4)
            )
        )

        return {
            "titulo": "Livro dos Ecos Sequenciais",
            "total_sorteios": total,
            "transicoes": {
                str(n): [{"numero": m, "contagem": c} for m, c in transitions[n].most_common(5)]
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
                    for d, c in consecutive_pairs.most_common(20)
                ],
                "top_triplas": [
                    {"tripla": list(t), "contagem": c}
                    for t, c in consecutive_triples.most_common(10)
                ],
            },
        }
