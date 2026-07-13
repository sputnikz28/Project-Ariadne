from .white import kors_branco
from .red import kors_vermelho
from .green import kors_verde
from .black import kors_preto

FACTION_META = {
    'name': 'Kors de Elarion',
    'origin': 'kors_elarion',
    'home': 'Elarion',
    'config_section': 'KORS',
    'weight_key': 'peso_conselho',
    'default_weight': 1.0,
}


def kors_council(ariadne, semana_iso=None):
    """Return list of Kor dicts ready for main.py candidate list."""
    kors = []
    for fn in (
        lambda: kors_branco(ariadne),
        lambda: kors_vermelho(ariadne),
        lambda: kors_verde(ariadne),
        lambda: kors_preto(ariadne, semana_iso),
    ):
        result = fn()
        if result:
            kors.append(result)
    return kors


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    return kors_council(ariadne)
