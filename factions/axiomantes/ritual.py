"""
Ritual dos Axiomantes — percurso pelo Labirinto de Nemerion.

Não itera 139M chaves. Calcula directamente a posição de cada chave
histórica via Feistel inverso (O(H)), depois avalia n_candidatos chaves
inéditas usando o perfil estatístico dos Ecos.
"""

import json
from datetime import date, datetime
from pathlib import Path

from .labirinto import UNIVERSE, key_position
from .profile import calculate_profile, choose_by_profile
from i18n.translations import t, lang_de_cfg

BASE_AXIOMANTES = Path(__file__).parent.parent.parent / "axiomantes"


def _save_experience(dados):
    pasta = BASE_AXIOMANTES / "experiencias"
    pasta.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = pasta / f"experiencia_{ts}.json"
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def execute_ritual(ariadne, seed, cfg=None):
    """
    Ritual dos Trinta Ecos:

    1. Marco = última chave conhecida — posição na sequência Feistel
    2. Ecos = sorteios históricos do período que ficam antes do marco
    3. Perfil do Labirinto — estatísticas dos Ecos
    4. Pontuação de n_candidatos chaves inéditas
    5. Chave escolhida = melhor score
    """
    period_years = 1
    coverage_threshold = 0.50
    min_excess = 0.0
    n_candidates = 50_000
    save_experience = True

    lang = lang_de_cfg(cfg)

    if cfg:
        period_years    = cfg.getint('AXIOMANTES', 'periodo_anos', fallback=1)
        coverage_threshold = cfg.getfloat('AXIOMANTES', 'limiar_cobertura', fallback=0.50)
        min_excess  = cfg.getfloat('AXIOMANTES', 'excesso_minimo', fallback=0.0)
        n_candidates    = cfg.getint('AXIOMANTES', 'n_candidatos', fallback=50_000)
        save_experience = cfg.getboolean('AXIOMANTES', 'guardar_experiencia', fallback=True)

    full_history = ariadne.full_history()
    if not full_history:
        return None

    # --- Marco ---
    alvo = full_history[-1]
    nums_alvo = alvo['numeros']
    ests_alvo = alvo['estrelas']
    pos_alvo = key_position(nums_alvo, ests_alvo, seed)
    universe_fraction = pos_alvo / UNIVERSE

    # --- Período de comparação ---
    data_alvo = date.fromisoformat(alvo['data'])
    data_inicio_str = f"{data_alvo.year - period_years + 1}-01-01"

    period_history = [
        h for h in full_history
        if h['data'] >= data_inicio_str and h['id'] != alvo['id']
    ]

    # --- Posições das chaves do período ---
    echoes = []          # chaves antes do marco (com dados completos)
    after_anchor = []        # posições depois do marco

    for h in period_history:
        pos = key_position(h['numeros'], h['estrelas'], seed)
        if pos < pos_alvo:
            echoes.append({
                'id': h['id'],
                'data': h['data'],
                'numeros': h['numeros'],
                'estrelas': h['estrelas'],
                'posicao': pos,
            })
        else:
            after_anchor.append(pos)

    total_period = len(period_history)
    n_echoes = len(echoes)
    coverage = n_echoes / total_period if total_period > 0 else 0.0
    excess = coverage - universe_fraction

    esperado_num = round(total_period * universe_fraction, 1)
    espaco_medio_obs = round(pos_alvo / (n_echoes + 1)) if n_echoes > 0 else None
    espaco_teorico = round(UNIVERSE / max(len(full_history), 1))

    # --- Veredicto ---
    if excess >= 0.10:
        verdict = t('veredicto_desvio', lang)
    elif excess >= 0.05:
        verdict = t('veredicto_ligeiro', lang)
    elif excess >= -0.05:
        verdict = t('veredicto_acaso', lang)
    else:
        verdict = t('veredicto_abaixo', lang)

    # --- Perfil dos Ecos ---
    profile = calculate_profile(echoes) if echoes else None

    # --- Portal das Chaves Inéditas ---
    portal_aberto = (coverage >= coverage_threshold) and (excess >= min_excess)

    selection = None
    if portal_aberto and profile:
        historical_keys = {
            (tuple(sorted(h['numeros'])), tuple(sorted(h['estrelas'])))
            for h in full_history
        }
        selection = choose_by_profile(
            pos_alvo, seed, profile, historical_keys, n_candidates
        )

    result = {
        'seed': seed,
        'chave_alvo': {
            'numeros': nums_alvo,
            'estrelas': ests_alvo,
            'data': alvo['data'],
            'id': alvo['id'],
        },
        'posicao_alvo': pos_alvo,
        'universo_total': UNIVERSE,
        'fracao_universo_pct': round(universe_fraction * 100, 4),
        'periodo_anos': period_years,
        'historico_comparacao': total_period,
        'n_ecos': n_echoes,
        'n_depois': len(after_anchor),
        'cobertura_pct': round(coverage * 100, 4),
        'esperado_num': esperado_num,
        'excesso_pct': round(excess * 100, 4),
        'espaco_medio_obs': espaco_medio_obs,
        'espaco_teorico': espaco_teorico,
        'veredicto': verdict,
        'portal_aberto': portal_aberto,
        'perfil': profile,
        'seleccao': selection,
        # campos de conveniência para main.py / conselho
        'chave_proposta': selection['chave'] if selection else None,
        'posicao_proposta': selection['posicao'] if selection else None,
        'score_proposta': selection['score'] if selection else None,
        'aviso': t('aviso', lang),
        'lang': lang,
        'criado_em': datetime.now().isoformat(timespec='seconds'),
    }

    if save_experience:
        result['experiencia_path'] = _save_experience(result)

    return result
