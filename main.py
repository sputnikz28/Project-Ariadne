import json
import random
import time
from configparser import ConfigParser
from configuration import load_config
from datetime import datetime
from pathlib import Path

from world.engine.builder import build
from world.engine.extraction import simulate_draw
from world.engine.celestial_energy import calculate_ritual
from world.engine.malphas_virus import choose_carrier
from world.engine.council_war import resolve
from core.evolution.statistics import calculate
from core.evolution.genetic import execute
from races.extras import superiors
from council.council import filter_candidates, vote, corrupt
from experiments.reports.writer import generate
from artifacts.amulets.books import synchronize_sources, build_books, update_next_draw_book
from artifacts.ark import prepare_new_run, load_all
from orders.black_squad.black_mages import create_mages, tentar_ressuscitar_lenda
from orders.elven_order.ninjas import create_ninjas, execute_missions
from orders.black_squad.persistence import load_grimoire
from world.engine.dark_conviction import create_mantra
from library.ariadne.engine import Ariadne
from factions.chaos_cartographers.council import execute_cartographers
from core.registry import FactionRegistry
from core.i18n.translations import t, lang_de_cfg


def readj(p, d):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception:
        return d


def writej(p, d):
    Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')


def registo_externo(name, faction_class, key, origem, generation, casa=None, extra=None):
    r = {
        'geracao': generation,
        'id': name,
        'nome': name,
        'classe': faction_class,
        'casa': casa or faction_class,
        'numeros': key[0],
        'estrelas': key[1],
        'origem': origem,
    }
    if extra:
        r.update(extra)
    return r


def _rebuild_report_factions(proposals):
    """Reconstruct faction-specific data for the legacy report writer.

    Can be removed once reports/writer.py is updated to consume Proposal objects
    directly instead of faction-keyed dicts.
    """
    result = {key: [] for key in ('fadas', 'tree', 'melf', 'cronomantes', 'esqueletos')}

    for p in proposals:
        d = {'nome': p.name, 'tipo': p.faction_class, 'chave': p.key, **p.extra}
        if p.origin == 'fada':
            result['fadas'].append(d)
        elif p.origin == 'treefolk':
            result['tree'].append(d)
        elif p.origin == 'melfork':
            result['melf'].append(d)
        elif p.origin == 'cronomante':
            result['cronomantes'].append(d)
        elif p.origin == 'esqueleto':
            result['esqueletos'].append(d)

    # Dwarves — reconstruct nested clan structure
    clans: dict = {}
    for p in proposals:
        if p.origin != 'cla_anao':
            continue
        cn = p.extra.get('clan_nome', '')
        if cn not in clans:
            clans[cn] = {
                'nome': cn,
                'lider': p.extra.get('lider', ''),
                'pool': p.extra.get('pool', []),
                'estrelas_pool': p.extra.get('estrelas_pool', []),
                'carteira': [],
            }
        clans[cn]['carteira'].append(p.key)
    result['anoes'] = list(clans.values())

    # Werewolves — reconstruct {'ativo', 'simulacoes', 'finalistas'}
    lob_props = [p for p in proposals if p.origin == 'lobisomem']
    result['lob'] = {
        'ativo': bool(lob_props),
        'simulacoes': lob_props[0].extra.get('simulacoes', 0) if lob_props else 0,
        'finalistas': [
            {'nome': p.name, 'tipo': p.faction_class, 'chave': p.key,
             'fitness': p.extra.get('fitness', 0)}
            for p in lob_props
        ],
    }
    return result


def main():
    cfg = load_config('config.txt')
    modo_semente = cfg.get('SIMULACAO', 'modo_semente', fallback='fixo').strip().lower()
    seed = cfg.getint('SIMULACAO', 'semente') if modo_semente == 'fixo' else time.time_ns()
    random.seed(seed)
    prepare_new_run(cfg)

    world, hist = build(cfg)
    est = calculate(hist)
    extraction = simulate_draw(cfg, world)
    fontes_biblioteca = synchronize_sources(cfg)
    biblioteca = build_books(cfg, hist, world)
    ctx = {
        'mundo': world, 'historico': hist, 'estatisticas': est,
        'extracao': extraction, 'biblioteca': biblioteca, 'seed': seed,
    }
    ariadne = Ariadne()

    # ── Genetic algorithm (Clerics) ─────────────────────────────────────────
    evo = execute(cfg, ctx)
    ritual = calculate_ritual(cfg, world, evo)

    # ── Superiors (complex dual return — explicit) ───────────────────────────
    vis, deus = superiors(ctx)

    # ── Black Squad & Elven Order (stateful — explicit) ──────────────────────
    dark_events = []
    magos_negros, black_grimoire = create_mages(cfg, ctx, dark_events)
    eco_ressuscitado = tentar_ressuscitar_lenda(cfg, dark_events)

    elven_events = []
    ninjas_elficos = create_ninjas(cfg)
    estado_ordem = execute_missions(cfg, ninjas_elficos, elven_events)

    # ── Analytical faction (does not vote — explicit) ────────────────────────
    cartografos = execute_cartographers(ariadne, cfg)

    # ── Auto-discover and run all voter factions via registry ─────────────────
    context = {**ctx, 'ariadne': ariadne, 'cfg': cfg}
    registry = FactionRegistry().discover("factions")

    all_proposals = []
    for faction in registry.all():
        try:
            all_proposals.extend(faction.propose(context))
        except Exception as e:
            print(f"Warning: {faction.name} failed: {e}")

    # ── Build candidate list and external registry ────────────────────────────
    cand = []
    externos = []
    final_generation = cfg.getint('SIMULACAO', 'geracoes')

    # Celestial ritual (human key from clerics)
    if ritual.get('ativo') and ritual.get('chave_humana'):
        cand.append((
            'Escolha Humana Consagrada pelos Clérigos',
            ritual['chave_humana'],
            ritual['peso_no_conselho'],
        ))
        externos.append(registo_externo(
            'Escolha Humana Consagrada pelos Clérigos',
            'Chave Humana Ritual',
            ritual['chave_humana'],
            'ritual_celeste',
            final_generation,
            'Templo dos Clérigos',
            {
                'energia_total': ritual['energia_total'],
                'almas_presentes': ritual['almas_presentes'],
                'peso_no_conselho': ritual['peso_no_conselho'],
            },
        ))

    # Genetic algorithm finalists (Clerics)
    for h in evo['populacao_final'][:cfg.getint('SIMULACAO', 'conselho_final')]:
        if h.keys:
            u = h.keys[-1]
            cand.append((f'{h.name} ({h.raca})', (u['numeros'], u['estrelas']), 1.0))

    # Superiors
    for v in vis:
        cand.append((v['nome'], v['chave'], 1.0))
        externos.append(registo_externo(v['nome'], v['tipo'], v['chave'], 'ser_superior', final_generation, 'Panteão'))

    cand.append((deus['nome'], deus['chave'], 1.4))
    externos.append(registo_externo(deus['nome'], deus['tipo'], deus['chave'], 'deus', final_generation, 'Panteão'))

    # All plugin factions (unified loop — no faction-specific code here)
    for p in all_proposals:
        cand.append((p.name, p.key, p.weight))
        externos.append(registo_externo(
            p.name, p.faction_class or p.origin, p.key,
            p.origin, final_generation, p.home, p.extra or None,
        ))

    # Black Squad
    peso_negro = cfg.getfloat('ESQUADRAO_NEGRO', 'peso_conselho', fallback=0.85)
    for x in magos_negros:
        cand.append((x['nome'], x['chave'], peso_negro))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'esquadrao_negro',
            final_generation, 'Biblioteca Sombria',
            {'score_negro': x['score'], 'nivel_grimorio': x['nivel_grimorio']},
        ))

    if eco_ressuscitado:
        echo_key = (list(eco_ressuscitado['chave'][0]), list(eco_ressuscitado['chave'][1]))
        cand.append((eco_ressuscitado['nome'], echo_key, 0.75))
        externos.append(registo_externo(
            eco_ressuscitado['nome'], eco_ressuscitado['classe'], echo_key,
            'necromancia_estatistica', final_generation, 'Ritual Negro',
            {'corrupcao': eco_ressuscitado['corrupcao'], 'ressuscitado_por': eco_ressuscitado['ressuscitado_por']},
        ))

    # ── Council vote ──────────────────────────────────────────────────────────
    ace, events, rej = filter_candidates(cand)
    res = vote(ace)
    herois_conselho = evo['populacao_final'][:cfg.getint('SIMULACAO', 'conselho_final')]
    portador = choose_carrier(cfg, herois_conselho)
    guerra = resolve(cfg, res['chave'], portador, ritual)
    corr = guerra['corrupcao'] if guerra and guerra.get('corrupcao') else corrupt(cfg, res['chave'])
    conviction = create_mantra(
        cfg, res['chave'], corr['entidade'],
        dark_energy=black_grimoire.get('nivel', 1) * 10,
    )

    update_next_draw_book(world, res, corr)

    externos.append(registo_externo('Conselho Original', 'Conselho Final', res['chave'], 'chave_conselho', final_generation, 'Conselho'))
    externos.append(registo_externo(corr['entidade'], 'Entidade Maléfica', corr['chave_corrompida'], 'corrupcao_final', final_generation, 'Abismo'))

    # ── Persist data ──────────────────────────────────────────────────────────
    arq = readj('datasets/generated/simulations/arquivo_destino.json', [])
    arq.extend(evo['registos'])
    arq.extend(externos)
    writej('datasets/generated/simulations/arquivo_destino.json', arq)

    mem = readj('datasets/generated/simulations/memoria_conselhos.json', [])
    mem.append({
        'data_execucao': datetime.now().isoformat(timespec='seconds'),
        'mundo': world,
        'original': res['chave'],
        'corrompida': corr['chave_corrompida'],
        'entidade': corr['entidade'],
        'total_individuos': len(evo['todos']),
        'total_chaves_racas_antigas': len(evo['registos']),
        'total_registos_externos': len(externos),
    })
    writej('datasets/generated/simulations/memoria_conselhos.json', mem)
    writej('datasets/generated/world_state/populacao_final.json', [h.to_dict() for h in evo['populacao_final']])
    writej('datasets/generated/world_state/todos_individuos.json', [h.to_dict() for h in sorted(evo['todos'].values(), key=lambda x: x.id)])

    # ── Generate report ───────────────────────────────────────────────────────
    report_factions = _rebuild_report_factions(all_proposals)
    rel = Path('experiments/reports/generated') / f"relatorio_v4_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    generate({
        'mundo': world,
        'historico': hist,
        'evolucao': evo,
        'visoes': vis,
        'deus': deus,
        'anoes': report_factions['anoes'],
        'fadas': report_factions['fadas'],
        'tree': report_factions['tree'],
        'melf': report_factions['melf'],
        'lob': report_factions['lob'],
        'extracao': extraction,
        'ritual': ritual,
        'guerra_conselho': guerra,
        'seed': seed,
        'eventos_z': events,
        'rej_a': rej,
        'resultado': res,
        'corr': corr,
        'registos_externos': externos,
        'biblioteca_oculta': biblioteca,
        'fontes_biblioteca': fontes_biblioteca,
        'reliquias_persistentes': load_all(),
        'magos_negros': magos_negros,
        'grimorio_negro': black_grimoire,
        'eventos_sombrios': dark_events,
        'eco_ressuscitado': eco_ressuscitado,
        'ninjas_elficos': ninjas_elficos,
        'eventos_elficos': elven_events,
        'estado_ordem_elfica': estado_ordem,
        'esqueletos': report_factions['esqueletos'],
        'conviccao_sombria': conviction,
        'cartografos': cartografos,
    }, rel)

    # ── Summary ───────────────────────────────────────────────────────────────
    lang = lang_de_cfg(cfg)
    print(t('simulacao_concluida', lang))
    print(f"{t('semente', lang)}:", seed)
    print('Energia celeste:', ritual.get('energia_total', 0.0))
    print('Almas no ritual:', ritual.get('almas_presentes', 0))
    print(f"{t('relatorio', lang)}:", rel)
    print(f"{t('individuos_unicos', lang)}:", len(evo['todos']))
    print('Chaves das raças antigas:', len(evo['registos']))
    print(f"{t('registos_externos', lang)}:", len(externos))
    print(f"{t('chave_original', lang)}:", res['chave'])
    print(f"{t('chave_corrompida', lang)}:", corr['chave_corrompida'])
    print(f"{t('livros_proibidos', lang)}:", len(biblioteca.get('livros_criados', [])))
    print(f"{t('reliquias', lang)}:", len(load_all()))
    print('Nível do Grimório Negro:', load_grimoire().get('nivel'))
    print(f"{t('magos_negros', lang)}:", len(magos_negros))
    print(f"{t('missoes_elficas', lang)}:", len(elven_events))
    print(f"{t('invocacoes', lang)}:", conviction.get('total_invocacoes', 0))

    # Plugin factions summary — auto-generated, no hardcoded names
    for faction in registry.all():
        n = len([p for p in all_proposals if p.origin == faction.origin])
        if n:
            print(f"{faction.name}: {n}")

    # Axiomantes portal status (special message)
    ax_proposals = [p for p in all_proposals if p.origin == 'axiomantes_nemerion']
    if ax_proposals:
        r = ax_proposals[0].extra.get('ritual', {})
        print(f"Axiomantes de Nemerion: {t('portal_aberto_msg', lang)} "
              f"| Cobertura {r.get('cobertura_pct', 0):.2f}% | {r.get('veredicto', '?')}")
    else:
        print(f"Axiomantes de Nemerion: {t('portal_fechado_msg', lang)}")

    livros_criados = [c['livro_path'] for c in cartografos if c.get('livro_path')]
    print(f"{t('cartografos', lang)}:", len(cartografos),
          f"| {t('livros_label', lang)}:", len(livros_criados))


if __name__ == '__main__':
    main()
