import json
import random
import time
from configparser import ConfigParser
from configuration import carregar_config
from datetime import datetime
from pathlib import Path

from world.construtor import construir
from world.extracao import simular_extracao
from world.energia_celeste import calcular_ritual
from world.virus_malphas import escolher_portador
from world.guerra_conselho import resolver
from evolution.estatisticas import calcular
from evolution.genetico import executar
from races.extras import anoes, fadas, melforks, lobisomens, treefolks, superiores
from races.cronomantes import criar_cronomantes
from races.esqueletos import criar_representantes as criar_esqueletos
from council.conselho import filtrar, votar, corromper
from reports.escritor import gerar
from amulets.biblioteca import sincronizar_fontes, construir_livros, atualizar_livro_proxima_extracao
from artefacts.arca import preparar_nova_execucao, carregar_todos
from black_squad.magos_negros import criar_magos, tentar_ressuscitar_lenda
from elven_order.ninjas import criar_ninjas, executar_missoes
from black_squad.persistencia import carregar_grimorio
from world.conviccao_sombria import criar_mantra
from library.ariadne.motor import Ariadne
from factions.kors.conselho import conselho_kors
from factions.cartografos_caos.conselho import executar_cartografos
from factions.axiomantes.conselho import axiomantes as axiomantes_ritual
from i18n.translations import t, lang_de_cfg


def readj(p, d):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception:
        return d


def writej(p, d):
    Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')


def registo_externo(nome, classe, chave, origem, geracao, casa=None, extra=None):
    r = {
        'geracao': geracao,
        'id': nome,
        'nome': nome,
        'classe': classe,
        'casa': casa or classe,
        'numeros': chave[0],
        'estrelas': chave[1],
        'origem': origem,
    }
    if extra:
        r.update(extra)
    return r


def main():
    cfg = carregar_config('config.txt')
    modo_semente = cfg.get('SIMULACAO', 'modo_semente', fallback='fixo').strip().lower()
    seed = cfg.getint('SIMULACAO', 'semente') if modo_semente == 'fixo' else time.time_ns()
    random.seed(seed)
    preparar_nova_execucao(cfg)

    mundo, hist = construir(cfg)
    est = calcular(hist)
    extracao = simular_extracao(cfg, mundo)
    fontes_biblioteca = sincronizar_fontes(cfg)
    biblioteca = construir_livros(cfg, hist, mundo)
    ctx = {'mundo': mundo, 'historico': hist, 'estatisticas': est, 'extracao': extracao, 'biblioteca': biblioteca, 'seed': seed}

    evo = executar(cfg, ctx)
    ritual = calcular_ritual(cfg, mundo, evo)
    vis, deus = superiores(ctx)
    ac = anoes(cfg, ctx)
    fs = fadas(cfg, ctx)
    ms = melforks(cfg, ctx)
    lob = lobisomens(cfg, ctx)
    tr = treefolks(cfg, ctx)
    cronos = criar_cronomantes(cfg, extracao, mundo)
    esqueletos = criar_esqueletos(cfg, ctx)

    eventos_sombrios = []
    magos_negros, grimorio_negro = criar_magos(cfg, ctx, eventos_sombrios)
    eco_ressuscitado = tentar_ressuscitar_lenda(cfg, eventos_sombrios)

    eventos_elficos = []
    ninjas_elficos = criar_ninjas(cfg)
    estado_ordem = executar_missoes(cfg, ninjas_elficos, eventos_elficos)

    ariadne = Ariadne()
    cartografos = executar_cartografos(ariadne, cfg)
    kors = conselho_kors(ariadne)
    ax = axiomantes_ritual(ariadne, seed, cfg)

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
    geracao_final = cfg.getint('SIMULACAO', 'geracoes')

    for h in evo['populacao_final'][:cfg.getint('SIMULACAO', 'conselho_final')]:
        if h.chaves:
            u = h.chaves[-1]
            cand.append((f'{h.nome} ({h.raca})', (u['numeros'], u['estrelas']), 1.0))

    for v in vis:
        cand.append((v['nome'], v['chave'], 1.0))
        externos.append(registo_externo(v['nome'], v['tipo'], v['chave'], 'ser_superior', geracao_final, 'Panteão'))

    cand.append((deus['nome'], deus['chave'], 1.4))
    externos.append(registo_externo(deus['nome'], deus['tipo'], deus['chave'], 'deus', geracao_final, 'Panteão'))

    for c in ac:
        for i, ch in enumerate(c['carteira']):
            nome = f"{c['nome']} #{i + 1}"
            cand.append((nome, ch, .35))
            externos.append(registo_externo(nome, 'Clã Anão', ch, 'cla_anao', geracao_final, c['nome'], {'lider': c['lider']}))

    for x in fs:
        cand.append((x['nome'], x['chave'], 1.0))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'fada', geracao_final))

    for x in ms:
        cand.append((x['nome'], x['chave'], 1.0))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'melfork', geracao_final, extra={'fitness': x['fitness']}))

    for x in lob['finalistas']:
        cand.append((x['nome'], x['chave'], .8))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'lobisomem', geracao_final, extra={'fitness': x['fitness']}))

    for x in tr:
        cand.append((x['nome'], x['chave'], x['peso']))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'treefolk', geracao_final, extra={
            'modelo': x['modelo'], 'treino': x['treino'], 'teste': x['teste'], 'fantasma': x['fantasma']
        }))


    for x in cronos:
        cand.append((x['nome'], x['chave'], 1.0))
        externos.append(registo_externo(x['nome'], x['tipo'], x['chave'], 'cronomante', geracao_final, 'Ordem do Tempo', {
            'precisao_temporal': x['precisao_temporal'],
            'assinatura_temporal': x['assinatura_temporal'],
            'eventos_extracao': extracao['eventos'],
        }))

    for x in esqueletos:
        peso_esqueleto = cfg.getfloat('ESQUELETOS', 'peso_conselho', fallback=0.80)
        cand.append((x['nome'], x['chave'], peso_esqueleto))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'esqueleto',
            geracao_final, 'Catacumbas Numéricas',
            {'ritual_osseo': x['ritual']}
        ))

    peso_kors = cfg.getfloat('KORS', 'peso_conselho', fallback=1.0)
    for x in kors:
        cand.append((x['nome'], x['chave'], peso_kors))
        extra_kor = {k: v for k, v in x.items() if k not in ('nome', 'classe', 'tipo', 'chave', 'peso')}
        externos.append(registo_externo(
            x['nome'], x['classe'], x['chave'], 'kors_elarion',
            geracao_final, 'Elarion', extra_kor,
        ))

    for x in ax:
        cand.append((x['nome'], x['chave'], x['peso']))
        extra_ax = {k: v for k, v in x.items() if k not in ('nome', 'classe', 'tipo', 'chave', 'peso')}
        externos.append(registo_externo(
            x['nome'], x['classe'], x['chave'], 'axiomantes_nemerion',
            geracao_final, 'Cidadela de Nemerion', extra_ax,
        ))

    for x in magos_negros:
        peso_negro = cfg.getfloat('ESQUADRAO_NEGRO', 'peso_conselho', fallback=0.85)
        cand.append((x['nome'], x['chave'], peso_negro))
        externos.append(registo_externo(
            x['nome'], x['tipo'], x['chave'], 'esquadrao_negro',
            geracao_final, 'Biblioteca Sombria',
            {'score_negro': x['score'], 'nivel_grimorio': x['nivel_grimorio']}
        ))

    if eco_ressuscitado:
        chave_eco = (list(eco_ressuscitado['chave'][0]), list(eco_ressuscitado['chave'][1]))
        cand.append((eco_ressuscitado['nome'], chave_eco, 0.75))
        externos.append(registo_externo(
            eco_ressuscitado['nome'], eco_ressuscitado['classe'], chave_eco,
            'necromancia_estatistica', geracao_final, 'Ritual Negro',
            {'corrupcao': eco_ressuscitado['corrupcao'], 'ressuscitado_por': eco_ressuscitado['ressuscitado_por']}
        ))

    ace, eventos, rej = filtrar(cand)
    res = votar(ace)
    herois_conselho=evo['populacao_final'][:cfg.getint('SIMULACAO','conselho_final')]
    portador=escolher_portador(cfg,herois_conselho)
    guerra=resolver(cfg,res['chave'],portador,ritual)
    corr=guerra['corrupcao'] if guerra and guerra.get('corrupcao') else corromper(cfg,res['chave'])
    conviccao = criar_mantra(
        cfg, res['chave'], corr['entidade'],
        energia_sombria=grimorio_negro.get('nivel', 1) * 10
    )

    atualizar_livro_proxima_extracao(mundo,res,corr)

    externos.append(registo_externo('Conselho Original', 'Conselho Final', res['chave'], 'chave_conselho', geracao_final, 'Conselho'))
    externos.append(registo_externo(corr['entidade'], 'Entidade Maléfica', corr['chave_corrompida'], 'corrupcao_final', geracao_final, 'Abismo'))

    arq = readj('data/arquivo_destino.json', [])
    arq.extend(evo['registos'])
    arq.extend(externos)
    writej('data/arquivo_destino.json', arq)

    mem = readj('data/memoria_conselhos.json', [])
    mem.append({
        'data_execucao': datetime.now().isoformat(timespec='seconds'),
        'mundo': mundo,
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
    gerar({
        'mundo': mundo,
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
        'extracao': extracao,
        'ritual': ritual,
        'guerra_conselho': guerra,
        'seed': seed,
        'eventos_z': eventos,
        'rej_a': rej,
        'resultado': res,
        'corr': corr,
        'registos_externos': externos,
        'biblioteca_oculta': biblioteca,
        'fontes_biblioteca': fontes_biblioteca,
        'reliquias_persistentes': carregar_todos(),
        'magos_negros': magos_negros,
        'grimorio_negro': grimorio_negro,
        'eventos_sombrios': eventos_sombrios,
        'eco_ressuscitado': eco_ressuscitado,
        'ninjas_elficos': ninjas_elficos,
        'eventos_elficos': eventos_elficos,
        'estado_ordem_elfica': estado_ordem,
        'esqueletos': esqueletos,
        'conviccao_sombria': conviccao,
        'kors': kors,
        'cartografos': cartografos,
        'axiomantes': ax,
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
    print(f"{t('reliquias', lang)}:", len(carregar_todos()))
    print('Nível do Grimório Negro:', carregar_grimorio().get('nivel'))
    print(f"{t('magos_negros', lang)}:", len(magos_negros))
    print(f"{t('missoes_elficas', lang)}:", len(eventos_elficos))
    print(f"{t('esqueletos', lang)}:", len(esqueletos))
    print(f"{t('invocacoes', lang)}:", conviccao.get('total_invocacoes', 0))
    print(f"{t('kors', lang)}:", len(kors))
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
