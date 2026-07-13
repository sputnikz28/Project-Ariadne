from .constelacoes import CartografoDasConstelacoes
from .ciclos import CronistaDoCiclos
from .tendencias import CartografoDasTendencias
from .aleatoriedade import MongeDoAcaso
from .markov import OracleDeMarkov


def execute_cartographers(ariadne, cfg=None):
    """Load historico once, run all 5 Cartógrafos, return list of results."""
    history = ariadne.full_history()

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
        MongeDoAcaso(ariadne, n_simulations=n_mc),
        OracleDeMarkov(ariadne),
    ]

    results = []
    for c in cartografos:
        try:
            results.append(c.execute(history))
        except Exception as e:
            results.append({"cartografo": c.name, "erro": str(e), "livro_path": None})

    return results
