from .constelacoes import CartografoDasConstelacoes
from .ciclos import CronistaDoCiclos
from .tendencias import CartografoDasTendencias
from .aleatoriedade import MongeDoAcaso
from .markov import OracleDeMarkov


def executar_cartografos(ariadne, cfg=None):
    """Load historico once, run all 5 Cartógrafos, return list of results."""
    historico = ariadne.historico_completo()

    n_mc = 100_000
    if cfg:
        try:
            n_mc = cfg.getint("CARTOGRAFOS_CAOS", "monte_carlo_simulacoes", fallback=100_000)
        except Exception:
            pass

    cartografos = [
        CartografoDasConstelacoes(ariadne),
        CronistaDoCiclos(ariadne),
        CartografoDasTendencias(ariadne),
        MongeDoAcaso(ariadne, n_simulacoes=n_mc),
        OracleDeMarkov(ariadne),
    ]

    resultados = []
    for c in cartografos:
        try:
            resultados.append(c.executar(historico))
        except Exception as e:
            resultados.append({"cartografo": c.nome, "erro": str(e), "livro_path": None})

    return resultados
