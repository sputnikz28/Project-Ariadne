from collections import Counter
from .base import CartografoDoCaos


class CartografoDasTendencias(CartografoDoCaos):
    nome = "Lirien das Correntes"
    especialidade = "Tendências por janela, baixos vs altos, dígitos finais"

    def analisar(self, historico):
        total = len(historico)
        if total == 0:
            return {"titulo": "Livro das Tendências e Correntes", "total_sorteios": 0}

        def freq_janela(n):
            recentes = historico[-n:] if n < total else historico
            cnt = Counter()
            for draw in recentes:
                for num in draw["numeros"]:
                    cnt[num] += 1
            return cnt

        f50 = freq_janela(50)
        f100 = freq_janela(100)
        f200 = freq_janela(200)
        f_total = freq_janela(total)

        # Trend per number: freq in last 50 vs historical average in a 50-draw window
        tendencias = {}
        for n in range(1, 51):
            hist_por_50 = f_total.get(n, 0) / total * 50
            tendencias[n] = {
                "ultimos_50": f50.get(n, 0),
                "ultimos_100": f100.get(n, 0),
                "ultimos_200": f200.get(n, 0),
                "historico_total": f_total.get(n, 0),
                "tendencia": round(f50.get(n, 0) - hist_por_50, 2),
            }

        em_subida = sorted(range(1, 51), key=lambda n: tendencias[n]["tendencia"], reverse=True)[:10]
        em_descida = sorted(range(1, 51), key=lambda n: tendencias[n]["tendencia"])[:10]

        # Baixos (1-25) vs Altos (26-50)
        baixos = sum(1 for draw in historico for n in draw["numeros"] if n <= 25)
        altos = total * 5 - baixos
        dist_ba = Counter()
        for draw in historico:
            b = sum(1 for n in draw["numeros"] if n <= 25)
            dist_ba[f"{b}B-{5-b}A"] += 1

        # Dígito final
        digitos = Counter(n % 10 for draw in historico for n in draw["numeros"])

        # Gaps histogram (across all draws)
        all_gaps = []
        for draw in historico:
            s = sorted(draw["numeros"])
            all_gaps.extend(s[i + 1] - s[i] for i in range(4))
        gap_hist = Counter(all_gaps)
        gap_media = round(sum(all_gaps) / len(all_gaps), 2) if all_gaps else None
        gap_max_freq = gap_hist.most_common(5)

        return {
            "titulo": "Livro das Tendências e Correntes",
            "total_sorteios": total,
            "tendencias_por_numero": {str(n): v for n, v in tendencias.items()},
            "em_subida": em_subida,
            "em_descida": em_descida,
            "baixos_vs_altos": {
                "baixos_1_25": baixos,
                "altos_26_50": altos,
                "pct_baixos": round(baixos / (total * 5) * 100, 1),
                "pct_altos": round(altos / (total * 5) * 100, 1),
                "distribuicao_por_sorteio": {k: v for k, v in dist_ba.most_common()},
            },
            "digitos_finais": {str(d): digitos.get(d, 0) for d in range(10)},
            "gaps": {
                "media": gap_media,
                "mais_frequentes": [{"gap": g, "contagem": c} for g, c in gap_max_freq],
            },
        }
