"""Conselho dos Clérigos.

Unlike every other faction, the Clerics genetic algorithm produces a
rich population object (`evo`) consumed by more than just the Council
vote — `world/engine/celestial_energy.py`'s Ritual Celeste also scores
souls from `evo['cemiterio']`/`evo['ressuscitados']`. Running the
genetic algorithm twice (once for the ritual, once for the Council)
would consume two different slices of the random stream and break
reproducibility, so `main.py` runs it once via
`factions.clerics.algorithm.execute(cfg, ctx)` and threads the result
through `ctx['clerics_evo']` before the FactionRegistry loop. This
function only reads that already-computed population — it never
re-runs the algorithm itself.
"""

FACTION_META = {
    'name': 'Clérigos',
    'origin': 'clerigo',
    'home': 'Templo dos Clérigos',
    'config_section': 'SIMULACAO',
    'weight_key': 'peso_conselho',
    'default_weight': 1.0,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    if cfg is None or ctx is None:
        return []
    evo = ctx.get('clerics_evo')
    if not evo:
        return []
    finalists = evo['populacao_final'][:cfg.getint('SIMULACAO', 'conselho_final')]
    return [
        {
            'nome': f'{h.name} ({h.raca})',
            'tipo': h.raca,
            'chave': (h.keys[-1]['numeros'], h.keys[-1]['estrelas']),
            'peso': 1.0,
        }
        for h in finalists if h.keys
    ]
