import json
import random
import time
from configparser import ConfigParser
from configuration import load_config
from datetime import datetime
from pathlib import Path

from world.builder import build
from world.extraction import simulate_draw
from world.celestial_energy import calculate_ritual
from world.malphas_virus import choose_carrier
from world.council_war import resolve
from evolution.statistics import calculate
from evolution.genetic import execute
from races.extras import dwarves, faeries, melforks, werewolves, treefolks, superiors
from races.chronomancers import create_chronomancers
from races.skeletons import create_representatives as criar_esqueletos
from council.council import filter_candidates, vote, corrupt
from reports.writer import generate
from amulets.books import synchronize_sources, build_books, update_next_draw_book
from artefacts.ark import prepare_new_run, load_all
from black_squad.black_mages import create_mages, tentar_ressuscitar_lenda
from elven_order.ninjas import create_ninjas, execute_missions
from black_squad.persistence import load_grimoire
from world.dark_conviction import create_mantra
from library.ariadne.engine import Ariadne
from factions.kors.council import kors_council
from factions.chaos_cartographers.council import execute_cartographers
from factions.axiomantes.council import axiomantes as axiomantes_ritual
from factions.vampires.council import vampires as vampires_faction
from factions.gargoyles.council import gargoyles as gargoyles_faction
from i18n.translations import t, lang_de_cfg


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
    ctx = {'mundo': world, 'historico': hist, 'estatisticas': est, 'extracao': extraction, 'biblioteca': biblioteca, 'seed': seed}

    evo = execute(cfg, ctx)
    ritual = calculate_ritual(cfg, world, evo)
    vis, deus = superiors(ctx)
    ac = dwarves(cfg, ctx)
    fs = faeries(cfg, ctx)
    ms = melforks(cfg, ctx)
    lob = werewolves(cfg, ctx)
    tr = treefolks(cfg, ctx)
    cronos = create_chronomancers(cfg, extraction, world)
    esqueletos = criar_esqueletos(cfg, ctx)

    dark_events = []
    magos_negros, black_grimoire = create_mages(cfg, ctx, dark_events)
    eco_ressuscitado = tentar_ressuscitar_lenda(cfg, dark_events)

    elven_events = []
    ninjas_elficos = create_ninjas(cfg)
    estado_ordem = execute_missions(cfg, ninjas_elficos, elven_events)

    ariadne = Ariadne()
    cartografos = execute_cartographers(ariadne, cfg)
    kors = kors_council(ariadne)
    ax = axiomantes_ritual(ariadne, seed, cfg)
    vampiros = vampires_faction(ariadne, seed, cfg)
    gargulas = gargoyles_faction(ariadne, seed, cfg)

    cand = []
    externos = []

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
            cfg.getint('SIMULACAO', 'geracoes'),
            'Templo dos Clérigos',
            {
                'energia_total': ritual['energia_total'],
                'almas_presentes': ritual['almas_presentes'],
                'peso_no_conselho': ritual['peso_no_conselho'],
            },
        ))
    final_generation = cfg.getint('SIMULACAO', 'geracoes')

    for h in evo['populacao_final'][:cfg.getint('SIMULACAO', 'conselho_final')]:
        if h.keys:
            u = h.keys[-1]
            cand.append((f'{h.name} ({h.raca})', (u['numeros'], u['estrelas']), 1.0))

    for v in vis:
        cand.append((v['nome'], v['chave'], 1.0))
        externos.append(registo_externo(v['nome'], v['tipo'], v['chave'], 'ser_superior', final_generation, 'Panteão'))

    cand.append((deus['nome'], deus['chave'], 1.4))
    externos.append(registo_externo(deus['nome'], deus['tipo'], deus['chave'], 'deus', final_generation, 'Panteão'))

    for c in ac:
        for i, ch in enumerate(c['carteira']):
            name = f"{c['nome']} #{i + 1}"
            cand.append((name, ch, .35))
            externos.append(registo_externo(name, 'Clã Anão', ch, 'cla_anao', final_generation, c['nome'], {'lider': c['lider']}))

    for x in fs:
        cand.append((x['nome'], x['chave'], 1.0))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'fada', final_generation))

    for x in ms:
        cand.append((x['nome'], x['chave'], 1.0))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'melfork', final_generation, extra={'fitness': x['fitness']}))

    for x in lob['finalistas']:
        cand.append((x['nome'], x['chave'], .8))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'lobisomem', final_generation, extra={'fitness': x['fitness']}))

    for x in tr:
        cand.append((x['nome'], x['chave'], x['peso']))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'treefolk', final_generation, extra={
            'modelo': x['modelo'], 'treino': x['treino'], 'teste': x['teste'], 'fantasma': x['fantasma']
        }))


    for x in cronos:
        cand.append((x['nome'], x['chave'], 1.0))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'cronomante', final_generation, 'Ordem do Tempo', {
            'precisao_temporal': x['precisao_temporal'],
            'assinatura_temporal': x['assinatura_temporal'],
            'eventos_extracao': extraction['eventos'],
        }))

    for x in esqueletos:
        peso_esqueleto = cfg.getfloat('ESQUELETOS', 'peso_conselho', fallback=0.80)
        cand.append((x['nome'], x['chave'], peso_esqueleto))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'esqueleto',
            final_generation, 'Catacumbas Numéricas',
            {'ritual_osseo': x['ritual']}
        ))

    peso_kors = cfg.getfloat('KORS', 'peso_conselho', fallback=1.0)
    for x in kors:
        cand.append((x['nome'], x['chave'], peso_kors))
        extra_kor = {k: v for k, v in x.items() if k not in ('nome', 'classe', 'tipo', 'chave', 'peso')}
        externos.append(registo_externo(
            x['nome'], x['classe'], x['chave'], 'kors_elarion',
            final_generation, 'Elarion', extra_kor,
        ))

    for x in ax:
        cand.append((x['nome'], x['chave'], x['peso']))
        extra_ax = {k: v for k, v in x.items() if k not in ('nome', 'classe', 'tipo', 'chave', 'peso')}
        externos.append(registo_externo(
            x['nome'], x['classe'], x['chave'], 'axiomantes_nemerion',
            final_generation, 'Cidadela de Nemerion', extra_ax,
        ))

    peso_vampiros = cfg.getfloat('VAMPIROS', 'peso_conselho', fallback=0.90)
    for x in vampiros:
        cand.append((x['nome'], x['chave'], peso_vampiros))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'vampiro',
            final_generation, 'Cripta Eterna', {'linhagem': x['linhagem']}
        ))

    peso_gargulas = cfg.getfloat('GARGULAS', 'peso_conselho', fallback=0.85)
    for x in gargulas:
        cand.append((x['nome'], x['chave'], peso_gargulas))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'gargula',
            final_generation, 'Torreão de Pedra', {'linhagem': x['linhagem']}
        ))

    for x in magos_negros:
        peso_negro = cfg.getfloat('ESQUADRAO_NEGRO', 'peso_conselho', fallback=0.85)
        cand.append((x['nome'], x['chave'], peso_negro))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'esquadrao_negro',
            final_generation, 'Biblioteca Sombria',
            {'score_negro': x['score'], 'nivel_grimorio': x['nivel_grimorio']}
        ))

    if eco_ressuscitado:
        echo_key = (list(eco_ressuscitado['chave'][0]), list(eco_ressuscitado['chave'][1]))
        cand.append((eco_ressuscitado['nome'], echo_key, 0.75))
        externos.append(registo_externo(
            eco_ressuscitado['nome'], eco_ressuscitado['classe'], echo_key,
            'necromancia_estatistica', final_generation, 'Ritual Negro',
            {'corrupcao': eco_ressuscitado['corrupcao'], 'ressuscitado_por': eco_ressuscitado['ressuscitado_por']}
        ))

    ace, events, rej = filter_candidates(cand)
    res = vote(ace)
    herois_conselho=evo['populacao_final'][:cfg.getint('SIMULACAO','conselho_final')]
    portador=choose_carrier(cfg,herois_conselho)
    guerra=resolve(cfg,res['chave'],portador,ritual)
    corr=guerra['corrupcao'] if guerra and guerra.get('corrupcao') else corrupt(cfg,res['chave'])
    conviction = create_mantra(
        cfg, res['chave'], corr['entidade'],
        dark_energy=black_grimoire.get('nivel', 1) * 10
    )

    update_next_draw_book(world,res,corr)

    externos.append(registo_externo('Conselho Original', 'Conselho Final', res['chave'], 'chave_conselho', final_generation, 'Conselho'))
    externos.append(registo_externo(corr['entidade'], 'Entidade Maléfica', corr['chave_corrompida'], 'corrupcao_final', final_generation, 'Abismo'))

    arq = readj('data/arquivo_destino.json', [])
    arq.extend(evo['registos'])
    arq.extend(externos)
    writej('data/arquivo_destino.json', arq)

    mem = readj('data/memoria_conselhos.json', [])
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
    writej('data/memoria_conselhos.json', mem)
    writej('data/populacao_final.json', [h.to_dict() for h in evo['populacao_final']])
    writej('data/todos_individuos.json', [h.to_dict() for h in sorted(evo['todos'].values(), key=lambda x: x.id)])

    rel = Path('reports/generated') / f"relatorio_v4_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    generate({
        'mundo': world,
        'historico': hist,
        'evolucao': evo,
        'visoes': vis,
        'deus': deus,
        'anoes': ac,
        'fadas': fs,
        'tree': tr,
        'melf': ms,
        'lob': lob,
        'cronomantes': cronos,
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
        'esqueletos': esqueletos,
        'conviccao_sombria': conviction,
        'kors': kors,
        'cartografos': cartografos,
        'axiomantes': ax,
        'vampiros': vampiros,
        'gargulas': gargulas,
    }, rel)

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
    print(f"{t('esqueletos', lang)}:", len(esqueletos))
    print(f"{t('invocacoes', lang)}:", conviction.get('total_invocacoes', 0))
    print(f"{t('kors', lang)}:", len(kors))
    print("Vampiros de Elarion:", len(vampiros))
    print("Gárgulas do Torreão:", len(gargulas))
    livros_criados = [c['livro_path'] for c in cartografos if c.get('livro_path')]
    print(f"{t('cartografos', lang)}:", len(cartografos),
          f"| {t('livros_label', lang)}:", len(livros_criados))
    if ax:
        r = ax[0]['ritual']
        print(f"Axiomantes de Nemerion: {t('portal_aberto_msg', lang)} "
              f"| Cobertura {r['cobertura_pct']:.2f}% | {r['veredicto']}")
    else:
        print(f"Axiomantes de Nemerion: {t('portal_fechado_msg', lang)}")


if __name__ == '__main__':
    main()
