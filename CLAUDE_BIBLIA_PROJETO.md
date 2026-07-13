# CLAUDE.md

# Oráculos do Euromilhões

## Bíblia do Projeto --- V1 → V7.1

> Este documento serve como contexto permanente para qualquer assistente
> de desenvolvimento.

# 1. Filosofia

O projeto é um simulador narrativo e estatístico inspirado no
Euromilhões.

Objetivos:

-   construir um universo de fantasia vivo;
-   experimentar estratégias estatísticas;
-   criar personagens com filosofias distintas;
-   preservar conhecimento numa Biblioteca Eterna.

**Regra de ouro**

Os padrões históricos **não aumentam a probabilidade matemática** de
prever um sorteio futuro. Toda a análise é descritiva e experimental.

------------------------------------------------------------------------

# 2. Evolução do projeto

## V1

-   Conselho inicial.
-   Geração de chaves.
-   Relatórios.

## V2

-   Estratégias por personagem.
-   Conselho escolhe uma chave.

## V3

-   Gerações.
-   Ranking.
-   Personagens lendárias.

## V4

-   Artefactos.
-   Amuletos.
-   Relíquias persistentes.
-   Livros proibidos.
-   Monges e Escribas.
-   Esquadrão Negro.
-   Ordem Élfica.

## V5

-   Biblioteca Eterna.
-   Ariadne.
-   Inventário persistente.
-   Treefolks.
-   Vampiros.
-   Gárgulas.

## V6

-   Configuração em ficheiro.
-   Múltiplas rondas.
-   Estratégia dos Esqueletos.
-   Inventários.
-   Campanhas.

## V7

-   Biblioteca reorganizada.
-   Pergaminhos.
-   Livros.
-   Índices.
-   Dataset 2026.
-   Excel "Saídas de Bolas".
-   55 pergaminhos.

## V7.1

-   Ariadne Fonte‑Viva.
-   Fontes anuais preservadas.
-   Livros reconstruíveis.
-   Consultas em cache.
-   Pergaminhos como vistas das fontes.

------------------------------------------------------------------------

# 3. Arquitetura

``` text
Personagens
      │
      ▼
   Ariadne
      │
      ▼
 Consultas (cache)
      │
      ▼
 Livros reconstruíveis
      │
      ▼
 Pergaminhos
      │
      ▼
 Fontes Originais
```

------------------------------------------------------------------------

# 4. Estrutura

``` text
biblioteca/
    fontes/
    scrolls/
    books/
    cache/
    indices/
    artefactos/
    reliquias/
    amuletos/
    cronicas/
```

------------------------------------------------------------------------

# 5. Biblioteca

## Fontes

Contêm datasets completos.

Nunca são alteradas.

## Pergaminhos

Representam um sorteio.

Guardam:

-   id
-   chave
-   referência à fonte
-   índice do sorteio
-   hash

## Livros

Conhecimento derivado:

-   frequências
-   duplas
-   triplas
-   lua
-   números atrasados

São sempre reconstruíveis.

## Consultas

Cache produzida por Ariadne.

------------------------------------------------------------------------

# 6. Personagens

## Clérigos

Algoritmo genético.

## Melforks

Estratégia híbrida original.

## Vampiros

Especialistas em triplas.

Linhagens:

-   Sanguínea
-   Sombria

## Gárgulas

Especialistas em duplas.

Linhagens:

-   Pedra
-   Espelho

## Treefolks

Investigadores.

Validam hipóteses.

Procuram fantasmas estatísticos.

## Monges

Protegem livros.

## Escribas

Catalogam conhecimento.

## Ordem Élfica

Recupera relíquias roubadas.

## Esquadrão Negro

Rouba livros, pergaminhos e artefactos.

------------------------------------------------------------------------

# 7. Artefactos

Os artefactos podem tornar-se persistentes.

Algumas classes podem encontrá-los em execuções futuras.

------------------------------------------------------------------------

# 8. Personagens Lendárias

São preservadas em livros.

Nunca desaparecem.

Podem regressar através de eventos especiais.

------------------------------------------------------------------------

# 9. Ariadne

Responsabilidades:

-   consultar fontes;
-   reconstruir livros;
-   responder perguntas;
-   gerar consultas;
-   validar integridade.

Nunca prevê sorteios.

------------------------------------------------------------------------

# 10. Dados

Datasets:

-   2004 → 2026

Excel:

-   Saídas de Bolas

Cada ano permanece preservado integralmente.

------------------------------------------------------------------------

# 11. Facções futuras

## Kors de Elarion

### Brancos

Deusa Aelyra.

15 números mais atrasados.

### Vermelhos

Números menos frequentes.

### Verdes

Padrões entre penúltima e última chave.

### Pretos

Deusa Nyxara.

Estudam semanas ISO.

Criam papiros.

------------------------------------------------------------------------

# 12. Papiros

Estrutura:

``` text
biblioteca/
    black_kors/
        papiros/
            semana_01/
            ...
            semana_53/
```

Cada papiro contém:

-   semana ISO
-   anos analisados
-   ecos
-   interpretação
-   confiança
-   referências

------------------------------------------------------------------------

# 13. Roadmap

## V7.2

Introduzir Kors.

## V8

Arquitetura por plugins:

``` text
faccoes/
    clerigos/
    melforks/
    vampiros/
    gargulas/
    kors/
    treefolks/
    esquadrao_negro/
```

Cada facção possui:

-   config.json
-   estrategia.py
-   personagens.json
-   livros_permitidos.json
-   reliquias.json

------------------------------------------------------------------------

# 14. Regras para futuros programadores

1.  Nunca alterar fontes originais.
2.  Nunca duplicar lógica estatística.
3.  Toda a informação passa por Ariadne.
4.  Livros são reconstruíveis.
5.  Pergaminhos são vistas.
6.  Consultas são cache.
7.  Novas facções devem ser modulares.
8.  Manter compatibilidade com versões anteriores.
9.  Separar claramente narrativa e análise estatística.
10. Não apresentar estratégias como métodos comprovados de previsão.

------------------------------------------------------------------------

# 15. Visão

O objetivo final é criar um universo vivo onde personagens, livros,
campanhas e conhecimento evoluem continuamente sobre uma base histórica
consistente.
