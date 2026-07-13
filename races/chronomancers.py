import random
from races.antigas import normalize


def generate_temporal_key(name, extraction, world, indice=0):
    if not extraction.get('eventos'):
        return {
            'nome': name,
            'tipo': 'Cronomante',
            'chave': normalize(random.sample(range(1, 51), 5), random.sample(range(1, 13), 2)),
            'precisao_temporal': 0.0,
            'assinatura_temporal': [],
        }

    idade_lua = float(world.get('idade_lua', 0.0))
    assinatura = []
    numbers = []
    stars = []

    for evento in extraction['eventos'][:5]:
        energy = (
            evento['segundo']
            + (evento['milissegundo'] % 100)
            + idade_lua
            + indice * 3
        )
        valor = int(energy % 50) + 1
        assinatura.append(round(energy, 3))
        numbers.append(valor)

    for evento in extraction['eventos'][5:]:
        energy = evento['segundo'] + (evento['milissegundo'] % 12) + indice
        stars.append(int(energy % 12) + 1)

    key = normalize(numbers, stars)
    precisao = round(max(0.05, 0.65 - abs(extraction['atraso_arranque'] - 8.0) / 30.0), 3)
    return {
        'nome': name,
        'tipo': 'Cronomante',
        'chave': key,
        'precisao_temporal': precisao,
        'assinatura_temporal': assinatura,
    }


def create_chronomancers(cfg, extraction, world):
    quantidade = cfg.getint('EXTRACAO', 'quantidade_cronomantes', fallback=4)
    names = [
        'Aurel dos Segundos Perdidos',
        'Chrona da Ampulheta Partida',
        'Kairon do Último Instante',
        'Selvar, Guardião do Pulso',
        'Nym do Relógio Lunar',
    ]
    return [
        generate_temporal_key(names[i % len(names)], extraction, world, i)
        for i in range(quantidade)
    ]
