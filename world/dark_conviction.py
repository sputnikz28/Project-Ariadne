
import random


def criar_mantra(config, chave, entidade, energia_sombria=0.0):
    if not config.getboolean("CONVICCAO_SOMBRIA", "ativa", fallback=True):
        return {"ativo": False, "mantras": []}

    rep_n = config.getint("CONVICCAO_SOMBRIA", "repeticoes_por_numero", fallback=5)
    rep_e = config.getint("CONVICCAO_SOMBRIA", "repeticoes_por_estrela", fallback=7)
    rep_obs = config.getint("CONVICCAO_SOMBRIA", "numero_obsessivo_repeticoes", fallback=15)
    intensidade = random.uniform(
        config.getfloat("CONVICCAO_SOMBRIA", "intensidade_min", fallback=0.60),
        config.getfloat("CONVICCAO_SOMBRIA", "intensidade_max", fallback=1.00),
    )
    intensidade = min(1.0, intensidade + energia_sombria / 1000.0)
    obsessivo = random.choice(chave[0])

    mantras = []
    for numero in chave[0]:
        mantras.extend([f"SAI {numero}!"] * rep_n)
    for estrela in chave[1]:
        mantras.extend([f"ESTRELA {estrela}, APARECE!"] * rep_e)
    mantras.extend([f"SAI {obsessivo}!"] * rep_obs)

    return {
        "ativo": True,
        "entidade": entidade,
        "intensidade": round(intensidade, 3),
        "numero_obsessivo": obsessivo,
        "total_invocacoes": len(mantras),
        "mantras": mantras,
    }
