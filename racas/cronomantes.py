import random
from racas.antigas import normalizar


def gerar_chave_temporal(nome, extracao, mundo, indice=0):
    if not extracao.get('eventos'):
        return {
            'nome': nome,
            'tipo': 'Cronomante',
            'chave': normalizar(random.sample(range(1, 51), 5), random.sample(range(1, 13), 2)),
            'precisao_temporal': 0.0,
            'assinatura_temporal': [],
        }

    idade_lua = float(mundo.get('idade_lua', 0.0))
    assinatura = []
    numeros = []
    estrelas = []

    for evento in extracao['eventos'][:5]:
        energia = (
            evento['segundo']
            + (evento['milissegundo'] % 100)
            + idade_lua
            + indice * 3
        )
        valor = int(energia % 50) + 1
        assinatura.append(round(energia, 3))
        numeros.append(valor)

    for evento in extracao['eventos'][5:]:
        energia = evento['segundo'] + (evento['milissegundo'] % 12) + indice
        estrelas.append(int(energia % 12) + 1)

    chave = normalizar(numeros, estrelas)
    precisao = round(max(0.05, 0.65 - abs(extracao['atraso_arranque'] - 8.0) / 30.0), 3)
    return {
        'nome': nome,
        'tipo': 'Cronomante',
        'chave': chave,
        'precisao_temporal': precisao,
        'assinatura_temporal': assinatura,
    }


def criar_cronomantes(cfg, extracao, mundo):
    quantidade = cfg.getint('EXTRACAO', 'quantidade_cronomantes', fallback=4)
    nomes = [
        'Aurel dos Segundos Perdidos',
        'Chrona da Ampulheta Partida',
        'Kairon do Último Instante',
        'Selvar, Guardião do Pulso',
        'Nym do Relógio Lunar',
    ]
    return [
        gerar_chave_temporal(nomes[i % len(nomes)], extracao, mundo, i)
        for i in range(quantidade)
    ]
