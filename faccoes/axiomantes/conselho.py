"""
Conselho dos Axiomantes de Nemerion.
Integração com main.py: devolve lista de dicts com nome/chave/peso.
Só vota quando o Portal das Chaves Inéditas está aberto.
"""

from racas.antigas import normalizar
from .ritual import executar_ritual
from i18n.traducoes import t


def axiomantes(ariadne, seed, cfg=None):
    """
    Executa o ritual e devolve [(dict)] para o Conselho, ou [] se o Portal estiver fechado.

    Cada dict contém: nome, classe, tipo, chave, peso, e 'ritual' com todas as métricas.
    """
    resultado = executar_ritual(ariadne, seed, cfg)
    if not resultado:
        return []

    peso = 0.75
    if cfg:
        peso = cfg.getfloat('AXIOMANTES', 'peso_conselho', fallback=0.75)

    if not resultado['portal_aberto'] or not resultado['chave_proposta']:
        # Portal fechado: Axiomantes observam mas não votam
        return []

    nums, ests = resultado['chave_proposta']
    chave_norm = normalizar(nums, ests)

    return [{
        'nome': 'Axiomantes de Nemerion',
        'classe': 'Axiomante',
        'tipo': 'Axiomante',
        'chave': chave_norm,
        'peso': peso,
        'ritual': resultado,
        'doutrina': (
            f"[{resultado.get('lang','pt').upper()}] "
            f"Marco: {resultado['posicao_alvo']:,}/{resultado['universo_total']:,} · "
            f"Ecos: {resultado['n_ecos']} · Cobertura: {resultado['cobertura_pct']:.2f}% "
            f"(excesso: {resultado['excesso_pct']:+.2f}%) · "
            f"Score: {resultado.get('score_proposta', 0):.1f}/100 · "
            f"{resultado['veredicto']}"
        ),
    }]
