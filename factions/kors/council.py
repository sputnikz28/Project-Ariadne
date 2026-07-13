from .branco import kors_branco
from .vermelho import kors_vermelho
from .verde import kors_verde
from .preto import kors_preto


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
