"""
Ritual dos Axiomantes — percurso pelo Labirinto de Nemerion.

Não itera 139M chaves. Calcula directamente a posição de cada chave
histórica via Feistel inverso (O(H)), depois avalia n_candidatos chaves
inéditas usando o perfil estatístico dos Ecos.
"""

import json
from datetime import date, datetime
from pathlib import Path

from .labirinto import UNIVERSO, posicao_de_chave
from .perfil import calcular_perfil, escolher_por_perfil
from i18n.traducoes import t, lang_de_cfg

BASE_AXIOMANTES = Path(__file__).parent.parent.parent / "axiomantes"


def _salvar_experiencia(dados):
    pasta = BASE_AXIOMANTES / "experiencias"
    pasta.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = pasta / f"experiencia_{ts}.json"
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def executar_ritual(ariadne, seed, cfg=None):
    """
    Ritual dos Trinta Ecos:

    1. Marco = última chave conhecida — posição na sequência Feistel
    2. Ecos = sorteios históricos do período que ficam antes do marco
    3. Perfil do Labirinto — estatísticas dos Ecos
    4. Pontuação de n_candidatos chaves inéditas
    5. Chave escolhida = melhor score
    """
    periodo_anos = 1
    limiar_cobertura = 0.50
    excesso_minimo = 0.0
    n_candidatos = 50_000
    guardar_experiencia = True

    lang = lang_de_cfg(cfg)

    if cfg:
        periodo_anos    = cfg.getint('AXIOMANTES', 'periodo_anos', fallback=1)
        limiar_cobertura = cfg.getfloat('AXIOMANTES', 'limiar_cobertura', fallback=0.50)
        excesso_minimo  = cfg.getfloat('AXIOMANTES', 'excesso_minimo', fallback=0.0)
        n_candidatos    = cfg.getint('AXIOMANTES', 'n_candidatos', fallback=50_000)
        guardar_experiencia = cfg.getboolean('AXIOMANTES', 'guardar_experiencia', fallback=True)

    historico_completo = ariadne.historico_completo()
    if not historico_completo:
        return None

    # --- Marco ---
    alvo = historico_completo[-1]
    nums_alvo = alvo['numeros']
    ests_alvo = alvo['estrelas']
    pos_alvo = posicao_de_chave(nums_alvo, ests_alvo, seed)
    fracao_universo = pos_alvo / UNIVERSO

    # --- Período de comparação ---
    data_alvo = date.fromisoformat(alvo['data'])
    data_inicio_str = f"{data_alvo.year - periodo_anos + 1}-01-01"

    historico_periodo = [
        h for h in historico_completo
        if h['data'] >= data_inicio_str and h['id'] != alvo['id']
    ]

    # --- Posições das chaves do período ---
    ecos = []          # chaves antes do marco (com dados completos)
    depois = []        # posições depois do marco

    for h in historico_periodo:
        pos = posicao_de_chave(h['numeros'], h['estrelas'], seed)
        if pos < pos_alvo:
            ecos.append({
                'id': h['id'],
                'data': h['data'],
                'numeros': h['numeros'],
                'estrelas': h['estrelas'],
                'posicao': pos,
            })
        else:
            depois.append(pos)

    total_periodo = len(historico_periodo)
    n_ecos = len(ecos)
    cobertura = n_ecos / total_periodo if total_periodo > 0 else 0.0
    excesso = cobertura - fracao_universo

    esperado_num = round(total_periodo * fracao_universo, 1)
    espaco_medio_obs = round(pos_alvo / (n_ecos + 1)) if n_ecos > 0 else None
    espaco_teorico = round(UNIVERSO / max(len(historico_completo), 1))

    # --- Veredicto ---
    if excesso >= 0.10:
        veredicto = t('veredicto_desvio', lang)
    elif excesso >= 0.05:
        veredicto = t('veredicto_ligeiro', lang)
    elif excesso >= -0.05:
        veredicto = t('veredicto_acaso', lang)
    else:
        veredicto = t('veredicto_abaixo', lang)

    # --- Perfil dos Ecos ---
    perfil = calcular_perfil(ecos) if ecos else None

    # --- Portal das Chaves Inéditas ---
    portal_aberto = (cobertura >= limiar_cobertura) and (excesso >= excesso_minimo)

    seleccao = None
    if portal_aberto and perfil:
        chaves_historicas = {
            (tuple(sorted(h['numeros'])), tuple(sorted(h['estrelas'])))
            for h in historico_completo
        }
        seleccao = escolher_por_perfil(
            pos_alvo, seed, perfil, chaves_historicas, n_candidatos
        )

    resultado = {
        'seed': seed,
        'chave_alvo': {
            'numeros': nums_alvo,
            'estrelas': ests_alvo,
            'data': alvo['data'],
            'id': alvo['id'],
        },
        'posicao_alvo': pos_alvo,
        'universo_total': UNIVERSO,
        'fracao_universo_pct': round(fracao_universo * 100, 4),
        'periodo_anos': periodo_anos,
        'historico_comparacao': total_periodo,
        'n_ecos': n_ecos,
        'n_depois': len(depois),
        'cobertura_pct': round(cobertura * 100, 4),
        'esperado_num': esperado_num,
        'excesso_pct': round(excesso * 100, 4),
        'espaco_medio_obs': espaco_medio_obs,
        'espaco_teorico': espaco_teorico,
        'veredicto': veredicto,
        'portal_aberto': portal_aberto,
        'perfil': perfil,
        'seleccao': seleccao,
        # campos de conveniência para main.py / conselho
        'chave_proposta': seleccao['chave'] if seleccao else None,
        'posicao_proposta': seleccao['posicao'] if seleccao else None,
        'score_proposta': seleccao['score'] if seleccao else None,
        'aviso': t('aviso', lang),
        'lang': lang,
        'criado_em': datetime.now().isoformat(timespec='seconds'),
    }

    if guardar_experiencia:
        resultado['experiencia_path'] = _salvar_experiencia(resultado)

    return resultado
