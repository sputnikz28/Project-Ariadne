import random
from collections import Counter
from .base import CartographerOfChaos


class MongeDoAcaso(CartographerOfChaos):
    name = "Thalvos do Acaso Esperado"
    especialidade = "Monte Carlo — compara o real com o esperado aleatório"

    def __init__(self, ariadne, n_simulations=100_000):
        super().__init__(ariadne)
        self.n_simulations = n_simulations

    def analisar(self, history):
        total = len(history)
        if total == 0:
            return {"titulo": "Livro do Acaso Esperado", "total_sorteios": 0}

        # Real stats
        freq_real = Counter()
        somas_reais = []
        baixos_reais = 0
        pares_reais = 0
        for draw in history:
            nums = draw["numeros"]
            for n in nums:
                freq_real[n] += 1
                if n <= 25:
                    baixos_reais += 1
                if n % 2 == 0:
                    pares_reais += 1
            somas_reais.append(sum(nums))

        # Monte Carlo
        freq_sim = Counter()
        somas_sim = []
        baixos_sim = 0
        pares_sim = 0
        n = self.n_simulations
        for _ in range(n):
            nums = random.sample(range(1, 51), 5)
            for num in nums:
                freq_sim[num] += 1
                if num <= 25:
                    baixos_sim += 1
                if num % 2 == 0:
                    pares_sim += 1
            somas_sim.append(sum(nums))

        total_nums_real = total * 5
        total_nums_sim = n * 5

        # Per-number deviation
        deviations = []
        for num in range(1, 51):
            pct_real = freq_real.get(num, 0) / total_nums_real * 100
            pct_sim = freq_sim.get(num, 0) / total_nums_sim * 100
            deviations.append({
                "numero": num,
                "freq_real": freq_real.get(num, 0),
                "pct_real": round(pct_real, 3),
                "pct_esperada": round(pct_sim, 3),
                "desvio": round(pct_real - pct_sim, 3),
            })
        deviations.sort(key=lambda x: abs(x["desvio"]), reverse=True)

        soma_media_real = round(sum(somas_reais) / total, 2)
        soma_media_sim = round(sum(somas_sim) / n, 2)

        # Soma distribution buckets
        def bucket(somas, total_s):
            cnt = Counter(s // 10 * 10 for s in somas)
            return {str(k): round(v / total_s * 100, 1) for k, v in sorted(cnt.items())}

        return {
            "titulo": "Livro do Acaso Esperado",
            "total_sorteios": total,
            "simulacoes": n,
            "top_desvios": deviations[:20],
            "soma": {
                "media_real": soma_media_real,
                "media_simulada": soma_media_sim,
                "desvio": round(soma_media_real - soma_media_sim, 2),
                "dist_real_pct": bucket(somas_reais, total),
                "dist_simulada_pct": bucket(somas_sim, n),
            },
            "baixos_vs_altos": {
                "pct_baixos_real": round(baixos_reais / total_nums_real * 100, 1),
                "pct_baixos_simulado": round(baixos_sim / total_nums_sim * 100, 1),
                "desvio": round(
                    baixos_reais / total_nums_real * 100 - baixos_sim / total_nums_sim * 100, 2
                ),
            },
            "pares_impares": {
                "pct_pares_real": round(pares_reais / total_nums_real * 100, 1),
                "pct_pares_simulado": round(pares_sim / total_nums_sim * 100, 1),
                "desvio": round(
                    pares_reais / total_nums_real * 100 - pares_sim / total_nums_sim * 100, 2
                ),
            },
        }
