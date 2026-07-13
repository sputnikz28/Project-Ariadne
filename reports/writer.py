from pathlib import Path
from datetime import datetime
from races.legacy import gaps


def fmt(ch):
    return f"{' - '.join(map(str, ch[0]))} | Estrelas: {' - '.join(map(str, ch[1]))}"


def barra(valor, maximo, largura=20):
    if maximo <= 0:
        return ''
    cheios = max(0, min(largura, round(valor / maximo * largura)))
    return '█' * cheios


def motivo_eliminacao(heroi):
    motivos = {
        'Bruxa': [
            'O caldeirão explodiu ao misturar demasiados números quentes.',
            'A névoa engoliu a receita antes da última estrela.',
            'Um ingrediente frio recusou obedecer ao círculo mágico.',
        ],
        'Vidente': [
            'Acordou no instante decisivo e esqueceu a visão.',
            'Confundiu um número verdadeiro com o eco de um sonho antigo.',
            'O Véu do Destino fechou-se antes da última imagem.',
        ],
        'Chefe Tribal': [
            'Os ossos ficaram silenciosos perante a Lua.',
            'O corvo roubou o quinto símbolo do ritual.',
            'A fogueira apagou-se antes do conselho ancestral.',
        ],
        'Elfo': [
            'A harmonia da chave quebrou-se num gap demasiado brusco.',
            'A floresta rejeitou uma soma sem equilíbrio.',
            'A folha da primeira árvore caiu fora do círculo.',
        ],
        'Goblin': [
            'Tentou roubar o jackpot antes do sorteio e foi amaldiçoado.',
            'A ganância empurrou demasiados números para o topo da montanha.',
            'Perdeu a Moeda Partida numa aposta impossível.',
        ],
        'Shaman': [
            'Os espíritos mudaram de ciclo durante o transe.',
            'A Lua deslocou os sinais para a direção errada.',
            'O tambor ancestral repetiu uma chave esquecida.',
        ],
    }
    base = heroi.raca.replace('Renascido ', '')
    options = motivos.get(base, ['O destino escolheu outro caminho.'])
    indice = sum(ord(c) for c in heroi.id) % len(options)
    return options[indice]


def gerar_lore(ctx):
    world = ctx['mundo']
    hist = ctx['historico']
    ultima = hist[-1]
    pop = ctx['evolucao']['populacao_final']
    melhor = max(pop, key=lambda h: h.pontos)
    linhas = []
    a = linhas.append

    a('╔════════════════════════════════════════════════════╗')
    a('              🌌 O LIVRO DO DESTINO')
    a('╚════════════════════════════════════════════════════╝')
    a('')
    a(f"No dia {world['data']}, em {world['local']}, o relógio marcou {world['hora']}.")
    a(f"Era {world['dia']}, durante o {world['estacao']}, sob uma Lua {world['fase_lua']}.")
    a('Os portões do Grande Conselho abriram-se poucos instantes antes da extração.')
    a('')
    a('A última chave conhecida pelos antigos era:')
    a(fmt((ultima['numeros'], ultima['estrelas'])))
    a('')
    a('A chave seguinte permanecia escondida atrás do Véu do Destino.')
    a('Nenhuma criatura podia consultar resultados posteriores à data configurada.')
    a('')
    a('╔════════════════════════════════════════════════════╗')
    a(f"  🌌 CONSELHO DO EUROMILHÕES — TEMPLO DE {world['local'].upper()}")
    a('╚════════════════════════════════════════════════════╝')
    a('')
    a(f"O jackpot de {world['jackpot']:,} moedas de ouro chamou os Goblins das cavernas.".replace(',', '.'))
    a(f"A pressão do destino já durava {world['pressao_destino']} sorteios sem vencedor.")
    a('')

    videntes = [h for h in pop if h.raca.endswith('Vidente') and h.keys]
    tribais = [h for h in pop if h.raca.endswith('Chefe Tribal') and h.keys]
    bruxas = [h for h in pop if h.raca.endswith('Bruxa') and h.keys]
    elfos = [h for h in pop if h.raca.endswith('Elfo') and h.keys]
    goblins = [h for h in pop if h.raca.endswith('Goblin') and h.keys]
    shamans = [h for h in pop if h.raca.endswith('Shaman') and h.keys]

    if videntes:
        h = max(videntes, key=lambda x: x.pontos)
        ch = h.keys[-1]
        a('🔮 AS VIDENTES ENTRAM EM TRANSE')
        a(f'{h.name} fecha os olhos e murmura:')
        a('"Vejo uma pedra antiga... mas a sua sombra move-se quando tento lembrar."')
        a(f"Visão incompleta: {fmt((ch['numeros'], ch['estrelas']))}")
        a(f"Clareza do sonho: {round(h.genoma.get('clareza', 0) * 100)}%")
        a('')

    if bruxas:
        h = max(bruxas, key=lambda x: x.pontos)
        ch = h.keys[-1]
        a('🧙 O CÍRCULO DAS BRUXAS')
        a(f'{h.name} lança ao caldeirão dois números quentes, dois frios e uma gota de caos.')
        a(f"Da névoa surge: {fmt((ch['numeros'], ch['estrelas']))}")
        a('')

    if tribais:
        h = max(tribais, key=lambda x: x.pontos)
        ch = h.keys[-1]
        ossos = h.genoma.get('ossos', [])
        a('🦴 OS CHEFES TRIBAIS LANÇAM OS OSSOS')
        a(f'{h.name} atira cinco ossos sobre a pedra ancestral.')
        if ossos:
            a('Símbolos revelados: ' + ' · '.join(ossos))
        a(f"Os espíritos respondem: {fmt((ch['numeros'], ch['estrelas']))}")
        a('')

    if elfos:
        h = max(elfos, key=lambda x: x.pontos)
        ch = h.keys[-1]
        a('🧝 A HARMONIA DOS ELFOS')
        a(f'{h.name} procura equilíbrio entre baixos, altos, pares, ímpares e gaps.')
        a(f"Chave harmonizada: {fmt((ch['numeros'], ch['estrelas']))}")
        a(f"Soma {sum(ch['numeros'])} | gaps {gaps(ch['numeros'])}")
        a('')

    if goblins:
        h = max(goblins, key=lambda x: x.pontos)
        ch = h.keys[-1]
        ganancia = min(99, round(30 + world['jackpot'] / 3_000_000))
        a('👹 A FEBRE DO TESOURO GOBLIN')
        a(f'Ganância: {barra(ganancia, 100)} {ganancia}%')
        a(f'{h.name} escolhe: {fmt((ch["numeros"], ch["estrelas"]))}')
        a('')

    if shamans:
        h = max(shamans, key=lambda x: x.pontos)
        ch = h.keys[-1]
        a('🪶 O RITUAL DOS SHAMANS')
        a(f'{h.name} escuta a última chave através do ciclo lunar.')
        a(f"Eco transformado: {fmt((ch['numeros'], ch['estrelas']))}")
        a('')

    a('☁️ O CAMINHO DAS 1000 ALMAS')
    a(f"Durante a evolução, {len(ctx['evolucao']['cemiterio'])} almas permaneceram no caminho.")
    a(f"{len(ctx['evolucao']['ressuscitados'])} regressaram ao mundo dos vivos.")
    if ctx['evolucao']['ressuscitados']:
        r = ctx['evolucao']['ressuscitados'][0]
        a(f"A primeira a regressar foi {r.name}, agora conhecida como {r.raca}.")
    a('')

    ritual = ctx.get('ritual', {})
    if ritual.get('ativo'):
        a('🧬✨ O RITUAL DA CONVERGÊNCIA CELESTE')
        a(f"Os Clérigos iniciaram a oração às {ritual['inicio'].split('T')[-1]}.")
        a(f"A libertação foi selada para {ritual['libertacao'].split('T')[-1]}, após {ritual['duracao_horas']} horas.")
        a(f"Almas presentes: {ritual['almas_presentes']}")
        a(f"Score espiritual total: {ritual['score_total']}")
        a(f"Score médio por alma: {ritual['score_medio']}")
        a(f"Energia acumulada: {ritual['energia_total']:.6f} ✨")
        a('Cada alma doou: score × energia_por_ponto × título × estado × amuletos.')
        a(f"Chave humana consagrada: {fmt(ritual['chave_humana'])}")
        if ritual.get('top_contribuidores'):
            a('Maiores doadores de energia:')
            for pos, alma in enumerate(ritual['top_contribuidores'][:5], 1):
                a(
                    f"  {pos}. {alma['nome']} | score {alma['score']:.0f} | "
                    f"{alma['titulo']} | energia +{alma['energia']:.6f}"
                )
        a('')


    if ctx['evolucao'].get('eventos_artefactos'):
        a('💍 A FORJA DOS AMULETOS VIVOS')
        for ev in ctx['evolucao']['eventos_artefactos'][:8]:
            art=ev['artefacto']
            if ev['evento']=='FORJA':
                a(f"{ev['dono']} forjou {art['nome']} [{art['raridade']}] na geração {ev['geracao']}.")
            elif ev['evento']=='HERANCA':
                a(f"{ev['origem']} deixou {art.get('nome')} a {ev['destino']}.")
            elif ev['evento']=='REDESCOBERTA_PERSISTENTE':
                a(f"{ev['dono']} reencontrou {art.get('nome')} [{art.get('raridade')}] na geração {ev['geracao']}.")
            else:
                a(f"Evento {ev['evento']}: {art.get('nome')}.")
        a('')
    if ctx['evolucao'].get('eventos_virus'):
        a('🦠 AS SOMBRAS DE MALPHAS')
        a(f"Infeções registadas: {len(ctx['evolucao']['eventos_virus'])}")
        for ev in ctx['evolucao']['eventos_virus'][:8]:a(f"Geração {ev['geracao']}: {ev['nome']} recebeu {ev['virus']} (oculto={ev['oculto']}).")
        a('')
    guerra=ctx.get('guerra_conselho')
    if guerra:
        a('⚔️ A GUERRA DO CONSELHO')
        a(guerra.get('resultado',''))
        if guerra.get('portador'):a(f"Portador: {guerra['portador']} | Vírus: {guerra.get('virus')}")
        if guerra.get('chance_purificacao') is not None:a(f"Chance de purificação: {guerra['chance_purificacao']}")
        if guerra.get('energia_gasta'):a(f"Energia celeste gasta: {guerra['energia_gasta']}")
        a('')


    a('🌑 A BIBLIOTECA SOMBRIA')
    grimoire=ctx.get('grimorio_negro',{})
    a(f"Nível do Grimório Negro: {grimoire.get('nivel',1)}")
    a(f"Livros copiados: {len(grimoire.get('livros_copiados',[]))}")
    a(f"Relíquias roubadas ainda em posse: {len(grimoire.get('reliquias_roubadas',[]))}")
    for ev in ctx.get('eventos_sombrios',[])[:8]:
        if ev.get('tipo')=='COPIA_LIVRO':
            a(f"{ev['mago']} criou {ev['copia']} a partir de {ev['livro']} com corrupção {ev['corrupcao']:.2%}.")
        elif ev.get('tipo')=='ROUBO_RELIQUIA':
            a(f"{ev['mago']} roubou {ev['artefacto'].get('nome')}.")
        elif ev.get('tipo')=='RESSURREICAO':
            eco=ev['eco']
            a(f"{eco['ressuscitado_por']} trouxe {eco['nome']} de outra era.")
    for mago in ctx.get('magos_negros',[])[:3]:
        a(f"{mago['nome']} propôs: {fmt(mago['chave'])} | score negro {mago['score']}")
    a('')

    a('🥷🌿 A ORDEM DAS SOMBRAS ÉLFICAS')
    estado=ctx.get('estado_ordem_elfica',{})
    a(f"Missões históricas: {estado.get('missoes',0)} | sucessos {estado.get('sucessos',0)} | falhas {estado.get('falhas',0)}")
    for ev in ctx.get('eventos_elficos',[])[:8]:
        a(f"{ev['id']} | {', '.join(ev['equipa'])} | alvo {ev['alvo']} | {ev['resultado']}")
        if ev.get('ninja_corrompido'):
            a(f"Uma sombra ficou para trás: {ev['ninja_corrompido']}.")
    a('')


    a('💀 AS CATACUMBAS NUMÉRICAS')
    for esq in ctx.get('esqueletos',[])[:5]:
        ritual=esq['ritual']
        a(
            f"{esq['nome']} abriu uma janela de {ritual['inicio_numeros']} a "
            f"{ritual['fim_numeros']} e escolheu {fmt(esq['chave'])}."
        )
    a('')

    conv=ctx.get('conviccao_sombria',{})
    if conv.get('ativo'):
        a('😈 O RITUAL DA CONVICÇÃO SOMBRIA')
        a(f"{conv['entidade']} acreditou com intensidade {conv['intensidade']:.1%}.")
        a(f"Número obsessivo: {conv['numero_obsessivo']}")
        a(f"Invocações totais: {conv['total_invocacoes']}")
        for mantra in conv.get('mantras',[])[:20]:
            a(mantra)
        if len(conv.get('mantras',[]))>20:
            a('... o mantra continuou até ao fecho do Véu.')
        a('')

    a('🏛️ O CONSELHO FECHA AS PORTAS')
    a(f"O herói dominante era {melhor.name}, da raça {melhor.raca}, com {melhor.pontos} pontos.")
    a(f"A chave original escolhida foi: {fmt(ctx['corr']['chave_original'])}")
    a('')
    a('😈 NO ÚLTIMO SEGUNDO, O PORTAL ABRE-SE')
    a(f"Surge {ctx['corr']['entidade']}.")
    for alt in ctx['corr']['alteracoes_numeros']:
        a(f"Número {alt['original']} {alt['deslocamento']:+d} → {alt['novo']}")
    for alt in ctx['corr']['alteracoes_estrelas']:
        a(f"Estrela {alt['original']} {alt['deslocamento']:+d} → {alt['novo']}")
    a('')
    a('🔥 LINHA TEMPORAL CORROMPIDA')
    a(fmt(ctx['corr']['chave_corrompida']))
    a('')
    a('O Arquivo do Destino foi selado. Depois do sorteio, todas as chaves — até as dos seres comuns e eliminados — poderão ser comparadas com a vencedora.')
    return linhas


def generate(ctx, path):
    l = []
    a = l.append
    l.extend(gerar_lore(ctx))
    a('\n\n')
    a('╔════════════════════════════════════════════════════╗')
    a('       📊 RELATÓRIO TÉCNICO DA SIMULAÇÃO')
    a('╚════════════════════════════════════════════════════╝\n')

    a('🌍 MUNDO')
    for k, v in ctx['mundo'].items():
        a(f'- {k}: {v}')

    a('\n🧬 GERAÇÕES')
    for r in ctx['evolucao']['resumo']:
        a(f"Geração {r['geracao']}: {r['melhor']} | {r['raca']} | {r['pontos']} pontos | eliminados {r['eliminados']} | ressuscitados {r['ressuscitados']}")

    a('\n🏆 MELHORES HERÓIS')
    for h in sorted(ctx['evolucao']['populacao_final'], key=lambda x: x.pontos, reverse=True)[:15]:
        a(f'{h.id} | {h.name} | {h.raca} | {h.casa} | {h.pontos} | {h.titulo} | amuletos: {h.amuletos}')

    a('\n☁️ CAMINHO DAS 1000 ALMAS')
    a(f"Almas: {len(ctx['evolucao']['cemiterio'])} | Ressuscitados: {len(ctx['evolucao']['ressuscitados'])}")
    for h in ctx['evolucao']['ressuscitados'][:20]:
        a(f'- {h.name} regressou como {h.raca} após {h.treinos} treinos')

    ritual = ctx.get('ritual', {})
    if ritual.get('ativo'):
        a('\n🧬✨ RITUAL CELESTE — ENERGIA DAS ALMAS')
        a(f"Semente do universo: {ctx.get('seed')}")
        a(f"Início: {ritual['inicio']} | Libertação: {ritual['libertacao']}")
        a(f"Almas presentes: {ritual['almas_presentes']}")
        a(f"Score total: {ritual['score_total']} | Score médio: {ritual['score_medio']}")
        a(f"Energia por ponto: {ritual['energia_por_ponto']}")
        a(f"Energia total: {ritual['energia_total']:.6f}")
        a(f"Chave humana consagrada: {fmt(ritual['chave_humana'])}")
        a(f"Peso da chave humana no Conselho: {ritual['peso_no_conselho']}")
        a('TOP CONTRIBUIDORES:')
        for pos, alma in enumerate(ritual['top_contribuidores'], 1):
            a(
                f"{pos:>2}. {alma['id']} | {alma['nome']} | {alma['raca']} | "
                f"estado {alma['estado']} | score {alma['score']:.0f} | "
                f"mult título {alma['multiplicador_titulo']} | "
                f"mult estado {alma['multiplicador_estado']} | "
                f"mult amuletos {alma['multiplicador_amuletos']} | "
                f"energia {alma['energia']:.6f}"
            )

    a('\n🧙🌳🧞 SERES SUPERIORES')
    for v in ctx['visoes']:
        a(f"{v['tipo']} {v['nome']}: {fmt(v['chave'])}")
    a(f"Deus {ctx['deus']['nome']}: {fmt(ctx['deus']['chave'])}")

    a('\n⛏️ CLÃS ANÕES')
    for c in ctx['anoes']:
        a(f"{c['nome']} | {c['lider']} | pool {c['pool']} | estrelas {c['estrelas_pool']}")
        for ch in c['carteira']:
            a('  - ' + fmt(ch))

    a('\n🧚 FADAS')
    for x in ctx['fadas']:
        a(f"{x['nome']}: {fmt(x['chave'])}")

    a('\n🌳 TREEFOLKS')
    for x in ctx['tree']:
        a(f"{x['nome']} | {x['modelo']} | treino {x['treino']} | teste {x['teste']} | fantasma {x['fantasma']} | {fmt(x['chave'])}")

    a('\n🧬 MELFORKS')
    for x in ctx['melf']:
        a(f"{x['nome']} | fitness {x['fitness']} | {fmt(x['chave'])}")

    a('\n🐺 LOBISOMENS')
    a(f"Ativos: {ctx['lob']['ativo']} | simulações: {ctx['lob']['simulacoes']}")
    for x in ctx['lob']['finalistas']:
        a(f"{x['nome']} | fitness {x['fitness']} | {fmt(x['chave'])}")

    a('\n🧟 ZOMBIES')
    for x in ctx['eventos_z'][:30]:
        a(f"{x['origem']}: {fmt(x['antes'])} -> {fmt(x['depois'])}")

    a('\n🕷️ ARACNOMANTES')
    a(f"Rejeitadas: {len(ctx['rej_a'])}")
    for x in ctx['rej_a'][:30]:
        a(f"{x['origem']} | {fmt(x['chave'])} | gaps {x['gaps']} | energia {x['energia']}")


    a('\n💍 ARTEFACTOS VIVOS')
    a(f"Eventos de artefactos: {len(ctx['evolucao'].get('eventos_artefactos', []))}")
    for ev in ctx['evolucao'].get('eventos_artefactos', [])[:30]:
        art=ev.get('artefacto',{})
        a(f"{ev['evento']} | geração {ev['geracao']} | {art.get('id')} | {art.get('nome')} | raridade {art.get('raridade')} | energia {art.get('energia_acumulada')} | donos {art.get('donos')}")
    a('\n🦠 VÍRUS DE MALPHAS')
    a(f"Infeções: {len(ctx['evolucao'].get('eventos_virus', []))}")
    for ev in ctx['evolucao'].get('eventos_virus', [])[:50]:a(f"Geração {ev['geracao']} | {ev['id']} | {ev['nome']} | {ev['raca']} | {ev['virus']} | oculto={ev['oculto']}")
    guerra=ctx.get('guerra_conselho')
    if guerra:
        a('\n⚔️ GUERRA DO CONSELHO')
        for k,v in guerra.items():
            if k!='corrupcao':a(f"{k}: {v}")

    a('\n🏛️ CONSELHO FINAL')
    a(f"Votos números: {ctx['resultado']['votos_numeros'][:10]}")
    a(f"Votos estrelas: {ctx['resultado']['votos_estrelas'][:6]}")
    o = ctx['corr']['chave_original']
    c = ctx['corr']['chave_corrompida']
    a('\n✨ CHAVE ORIGINAL ✨')
    a(fmt(o))
    a(f'Soma {sum(o[0])} | gaps {gaps(o[0])}')
    a('\n😈 CORRUPTOR')
    a(ctx['corr']['entidade'])
    for x in ctx['corr']['alteracoes_numeros']:
        a(f"Número {x['original']} {x['deslocamento']:+d} -> {x['novo']}")
    for x in ctx['corr']['alteracoes_estrelas']:
        a(f"Estrela {x['original']} {x['deslocamento']:+d} -> {x['novo']}")
    a('\n🔥 CHAVE CORROMPIDA 🔥')
    a(fmt(c))
    a(f'Soma {sum(c[0])} | gaps {gaps(c[0])}')

    a('\n╔════════════════════════════════════════════════════╗')
    a('   📚 ARQUIVO COMPLETO DE TODOS OS INDIVÍDUOS')
    a('╚════════════════════════════════════════════════════╝')
    todos = sorted(ctx['evolucao']['todos'].values(), key=lambda h: (h.generation, h.id))
    total_chaves = sum(len(h.keys) for h in todos)
    a(f'Total de indivíduos únicos: {len(todos)}')
    a(f'Total de chaves das raças antigas: {total_chaves}')
    a('Inclui vivos, eliminados, almas, ressuscitados e indivíduos comuns.')

    for h in todos:
        a('\n' + '━' * 52)
        a(f'ID: {h.id}')
        a(f'Nome: {h.name}')
        a(f'Raça: {h.raca}')
        a(f'Casa: {h.casa}')
        a(f'Estado final: {h.estado}')
        a(f'Geração de nascimento: {h.generation}')
        a(f'Pais: {h.pais if h.pais else "—"}')
        a(f'Pontuação acumulada: {h.pontos}')
        a(f'Título máximo/registado: {h.titulo}')
        a(f'Amuletos: {h.amuletos if h.amuletos else "nenhum"}')
        a(f'Treinos espirituais: {h.treinos}')
        if h.estado != 'VIVO':
            a(f'Motivo narrativo da eliminação: {motivo_eliminacao(h)}')
        a(f'Número de chaves geradas: {len(h.keys)}')
        for ch in h.keys:
            a(
                f"  Geração {ch['geracao']:>3}: "
                f"{fmt((ch['numeros'], ch['estrelas']))} | "
                f"soma {sum(ch['numeros'])} | gaps {gaps(ch['numeros'])}"
            )

    a('\n╔════════════════════════════════════════════════════╗')
    a('   🌐 ARQUIVO DAS ENTIDADES ESTRANGEIRAS AO CLÃ')
    a('╚════════════════════════════════════════════════════╝')
    for reg in ctx.get('registos_externos', []):
        a(f"{reg['origem']} | {reg['nome']} | {fmt((reg['numeros'], reg['estrelas']))}")

    a('\nAVISO: simulação criativa. Não prevê resultados.')
    Path(path).write_text('\n'.join(l), encoding='utf-8')
