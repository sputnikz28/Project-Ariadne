import random
from collections import Counter
from datetime import date
from races.legacy import normalize


def kors_preto(ariadne, semana_iso=None):
    if semana_iso is None:
        semana_iso = date.today().isocalendar()[1]

    ecos_resp = ariadne.weekly_echoes(semana_iso)
    all_echoes = ecos_resp.get("ecos", [])

    if all_echoes:
        cnt_nums = Counter()
        cnt_ests = Counter()
        for eco in all_echoes:
            for n in eco.get("numeros", []):
                cnt_nums[n] += 1
            for e in eco.get("estrelas", []):
                cnt_ests[e] += 1

        top_nums = cnt_nums.most_common(20)
        if len(top_nums) >= 5:
            pool = [n for n, _ in top_nums]
            weights = [f for _, f in top_nums]
            escolhidos = set()
            t = 0
            while len(escolhidos) < 5 and t < 300:
                escolhidos.add(random.choices(pool, weights=weights, k=1)[0])
                t += 1
            if len(escolhidos) < 5:
                restantes = [n for n in pool if n not in escolhidos]
                escolhidos.update(restantes[: 5 - len(escolhidos)])
            nums = sorted(escolhidos)[:5]
        else:
            encontrados = [n for n, _ in top_nums]
            restante = [n for n in range(1, 51) if n not in encontrados]
            random.shuffle(restante)
            nums = sorted((encontrados + restante)[:5])

        top_ests = cnt_ests.most_common(5)
        if len(top_ests) >= 2:
            pool_e = [e for e, _ in top_ests]
            pesos_e = [f for _, f in top_ests]
            ests = set()
            t = 0
            while len(ests) < 2 and t < 100:
                ests.add(random.choices(pool_e, weights=pesos_e, k=1)[0])
                t += 1
            if len(ests) < 2:
                restantes_e = [e for e in pool_e if e not in ests]
                ests.update(restantes_e[: 2 - len(ests)])
            stars = sorted(ests)
        else:
            stars = sorted(random.sample(range(1, 13), 2))

        confianca = min(0.25, len(all_echoes) / 100.0)
        interpretation = (
            f"Semana ISO {semana_iso} ressoa {len(all_echoes)} eco(s) histórico(s)."
        )
    else:
        nums = sorted(random.sample(range(1, 51), 5))
        stars = sorted(random.sample(range(1, 13), 2))
        confianca = 0.01
        interpretation = (
            f"Semana ISO {semana_iso} não possui ecos registados. "
            "A Nyxara convoca do vazio."
        )

    key = normalize(nums, stars)

    dados_papiro = {
        "entidade": "Nyxara das Sombras Semanais",
        "total_ecos": len(all_echoes),
        "confianca": confianca,
        "interpretacao": interpretation,
        "chave_proposta": {"numeros": key[0], "estrelas": key[1]},
        "ecos_resumo": [{"id": e["id"], "data": e["data"]} for e in all_echoes],
        "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
    }
    caminho_papiro = ariadne.create_papyrus(semana_iso, dados_papiro)

    return {
        "nome": "Nyxara das Sombras Semanais",
        "classe": "Kor Preto",
        "tipo": "Kor Preto",
        "chave": key,
        "peso": 1.0,
        "doutrina": "A semana que foi é o eco do que será.",
        "semana_iso": semana_iso,
        "total_ecos": len(all_echoes),
        "confianca": confianca,
        "interpretacao": interpretation,
        "papiro": caminho_papiro,
    }
