"""
Conselho dos Axiomantes de Nemerion.
Integração com main.py: devolve lista de dicts com nome/chave/peso.
Só vota quando o Portal das Chaves Inéditas está aberto.
"""

from races.antigas import normalize
from .ritual import execute_ritual
from i18n.translations import t


def axiomantes(ariadne, seed, cfg=None):
    """
    Executa o ritual e devolve [(dict)] para o Conselho, ou [] se o Portal estiver fechado.

    Cada dict contém: nome, classe, tipo, chave, peso, e 'ritual' com todas as métricas.
    """
    result = execute_ritual(ariadne, seed, cfg)
    if not result:
        return []

    weight = 0.75
    if cfg:
        weight = cfg.getfloat('AXIOMANTES', 'peso_conselho', fallback=0.75)

    if not result['portal_aberto'] or not result['chave_proposta']:
        # Portal fechado: Axiomantes observam mas não votam
        return []

    nums, ests = result['chave_proposta']
    chave_norm = normalize(nums, ests)

    return [{
        'nome': 'Axiomantes de Nemerion',
        'classe': 'Axiomante',
        'tipo': 'Axiomante',
        'chave': chave_norm,
        'peso': weight,
        'ritual': result,
        'doutrina': (
            f"[{result.get('lang','pt').upper()}] "
            f"Marco: {result['posicao_alvo']:,}/{result['universo_total']:,} · "
            f"Ecos: {result['n_ecos']} · Cobertura: {result['cobertura_pct']:.2f}% "
            f"(excesso: {result['excesso_pct']:+.2f}%) · "
            f"Score: {result.get('score_proposta', 0):.1f}/100 · "
            f"{result['veredicto']}"
        ),
    }]
