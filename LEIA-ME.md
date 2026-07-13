# Oráculos do Euromilhões V8.1 — Axiomantes de Nemerion

Simulador narrativo e estatístico do Euromilhões. O projeto explora padrões históricos através de personagens, facções e uma Biblioteca viva — sem nunca pretender prever resultados.

> Padrões históricos não aumentam a probabilidade de prever um sorteio futuro. Uma chave simples tem sempre a mesma probabilidade matemática de 5+2.

---

## Núcleo

- **Ariadne** — guardiã da Biblioteca; único ponto de acesso a dados para todas as facções;
- **Pergaminhos** — um ficheiro JSON por extração real (2004-2026, 1962 sorteios);
- **Livros** — conhecimento derivado: frequências, duplas, triplas, lua, cartógrafos;
- **Fontes** — datasets anuais imutáveis (2004-2026);
- **Consultas** — cache de respostas Ariadne reutilizáveis;
- **Ordem Élfica** — recupera relíquias e pergaminhos corrompidos;
- **Esquadrão Negro** — rouba livros e relíquias; cria grimório negro.

---

## Estrutura principal

```text
biblioteca/
├── ariadne/              ← motor.py — classe Ariadne (12 métodos)
├── fontes/               ← datasets anuais 2004-2026 (imutáveis)
├── scrolls/
│   ├── 2004/ … 2025/     ← formato compacto (data como string)
│   └── 2026/             ← formato completo (55 pergaminhos com astronomia)
├── books/
│   └── cartografos/      ← 5 livros analíticos gerados pelos Cartógrafos
├── indices/              ← duplas.json, triplas.json
├── cache/            ← cache de consultas Ariadne
└── black_kors/
    └── papiros/          ← papiros semanais da Nyxara (semana_01/ … semana_53/)

faccoes/
├── kors/                 ← Kors de Elarion (V7.2)
├── cartografos_caos/     ← Cartógrafos do Caos (V8)
└── axiomantes/           ← Axiomantes de Nemerion (V8.1)

axiomantes/
└── experiences/         ← relatórios JSON por execução do ritual
```

---

## Facções

### Clérigos
Algoritmo genético — 72 heróis evoluem durante 14 gerações.

### Melforks
Algoritmo genético especializado em geração de chaves equilibradas.

### Vampiros
Mestres das triplas:
- **Linhagem Sanguínea** — triplas frequentes e equilíbrio;
- **Linhagem Sombria** — triplas consecutivas e harmónicas.

### Gárgulas
Mestras das duplas:
- **Linhagem de Pedra** — duplas consistentes;
- **Linhagem do Espelho** — consecutivos e simetrias.

### Treefolks
Consultam Ariadne, formulam hipóteses e medem "fantasmas estatísticos" (confiança baixa em padrões com poucos dados).

### Kors de Elarion (V7.2)
Quatro observadores que consultam exclusivamente Ariadne — nunca lêem datasets directamente.

| Kor | Nome | Estratégia |
|-----|------|-----------|
| Branco | Aelyra dos Silêncios | 15 números mais atrasados |
| Vermelho | Kael da Chama Fria | Números menos frequentes no histórico completo |
| Verde | Sylvara das Passagens | Padrão penúltima→última chave (chegados, persistentes, vizinhos) |
| Preto | Nyxara das Sombras Semanais | Ecos da semana ISO · grava papiro em `biblioteca/black_kors/` |

### Cartógrafos do Caos (V8)
Cinco analistas que **não geram chaves** — produzem livros analíticos para consulta por outras facções. Correm antes de todos os outros e escrevem em `biblioteca/books/cartographers/`.

| Cartógrafo | Livro gerado | O que analisa |
|-----------|-------------|--------------|
| Eldran das Constelações | Livro das Constelações Numéricas | Rede de coocorrência, centralidade, top pares |
| Vesara dos Intervalos | Livro dos Ciclos Eternos | Atraso médio/máx/mín por número, ciclos completos dos 50 |
| Lirien das Correntes | Livro das Tendências e Correntes | Tendências por janela (50/100/200), baixos vs altos, dígitos finais, gaps |
| Thalvos do Acaso Esperado | Livro do Acaso Esperado | Monte Carlo (100K) — real vs esperado aleatório |
| Oryn dos Ecos Sequenciais | Livro dos Ecos Sequenciais | Transições Markov, vizinhança, sequências consecutivas |

### Axiomantes de Nemerion (V8.1)
Guardiões do Labirinto de 139.838.160 câmaras. Percorrem o universo combinatório completo do Euromilhões usando uma **permutação Feistel reproduzível** — sem repetições, sem guardar 139M entradas em memória. A posição de qualquer chave é calculada directamente via Feistel inverso em O(1).

**O ritual — Trinta Ecos:**
1. Pedem a Ariadne a última chave sorteada — o **marco**
2. Calculam a posição do marco na sequência Feistel (depende da semente da simulação)
3. Para cada sorteio do período: calculam posição → separam ecos (antes do marco) dos outros
4. Comparam a cobertura observada com o esperado num processo aleatório puro
5. **Portal das Chaves Inéditas** — abre se cobertura ≥ 50% e excesso ≥ 0%
6. Se o Portal abrir: calculam o **Perfil dos Ecos** e avaliam N chaves inéditas por score

**Perfil dos Ecos** (calculado a partir dos sorteios antes do marco):

| Dimensão | O que mede |
|---------|-----------|
| Soma média / desvio / faixa | Distribuição das somas das chaves |
| Paridades preferidas | Pares/ímpares mais comuns nos ecos |
| Baixos/altos preferidos | Proporção de números ≤25 e >25 |
| Números mais frequentes | Top 10 nos ecos |
| Estrelas mais frequentes | Top 6 nos ecos |
| Gap médio / amplitude média | Espaçamento interno médio |

**Pontuação da chave** (0–100 pts):

| Critério | Pts |
|---------|-----|
| Soma dentro da faixa preferida | 20 |
| Paridade dominante | 15 |
| Baixos/altos dominantes | 15 |
| Afinidade com os 5 números mais frequentes (pico em 3/5) | 20 |
| Afinidade com as estrelas mais frequentes | 15 |
| Gap médio próximo do perfil | 10 |
| Amplitude próxima do perfil | 5 |
| Bónus: 1-2 números raramente vistos | +5 |

**Matemática:**

| Conceito | Valor |
|---------|-------|
| Universo | C(50,5) × C(12,2) = 139.838.160 combinações |
| Algoritmo | Feistel (_H=11826, 4 rondas, Wang hash) |
| Complexidade | O(H) — H = nº sorteios históricos; sem iterar 139M chaves |
| Candidatos avaliados | 50.000 por defeito (configurável) |

**Exemplo de execução** (semente 2026, sorteios de 2026):
```
AXIOMANTES DE NEMERION — RITUAL DOS TRINTA ECOS
════════════════════════════════════════════════

Universo:       139.838.160 câmaras
Marco:          [2, 14, 28, 33, 48] + [8, 10]  (2026-07-10)
Posição:        66.401.431 de 139.838.160  (47,48% do universo)

Ecos históricos:  29 de 54 sorteios de 2026
Cobertura:        53,70%  (esperado: 25,6)  excesso: +6,22%
Veredicto:        LIGEIRAMENTE ACIMA DO ESPERADO
Portal:           ABERTO

PERFIL DOS ECOS (29 chaves)
  Soma média:    128,7     desvio: 24,9     faixa: [103, 153]
  Paridade:      2P/3Í e 3P/2Í (equilibrado)
  Baixos/altos:  2B/3A e 3B/2A (equilibrado)
  Nums + freq:   26  37  34  17  10  18  47  31  13  12
  Nums - freq:   39   8  22  32   9  25   3  36  48  50
  Estrelas:       9   2   5   4   8   6
  Gap médio:     8,4     Amplitude média: 33,7

50.000 candidatos avaliados — melhor score: 95,5 / 100

Chave escolhida:  9  10  31  34  37  ⭐  2  10
```
Experiência completa em `axiomantes/experiences/experiencia_YYYYMMDD_HHMMSS.json`.

> **Aviso:** A posição numa permutação pseudoaleatória não altera a probabilidade real de qualquer chave. Uma cobertura ≥ 50% é esperada quando se percorre ≥ 50% do universo. Isto é sempre compatível com o acaso.

### Outras facções
- **Esqueletos** — janela móvel de 25 números;
- **Cronomantes** — energia temporal dos eventos de extração;
- **Anões** — combinatória por clãs;
- **Fadas** — ponderação por números quotidianos;
- **Lobisomens** — Monte Carlo de aptidão (fase lunar);
- **Esquadrão Negro** — estratégia anti-popularidade com grimório roubado;
- **Ordem Élfica** — missões de recuperação.

---

## Ariadne — métodos disponíveis

```python
from library.ariadne.motor import Ariadne
a = Ariadne()

# Pergaminhos 2026
a.estado_pergaminho(55)
a.procurar_lua("Lua cheia")

# Índices
a.duplas(limite=10)
a.triplas(limite=10)

# Fontes normalizadas
a.numero(17)

# V7.2 — Kors
a.numeros_atrasados(15)
a.numeros_menos_frequentes(20)
a.padrao_transicao()
a.ecos_semanais(semana_iso=28)
a.criar_papiro(semana_iso=28, dados={...})

# V8 — Cartógrafos
a.historico_completo(desde="2020-01-01", ultimos=500)

# V8.1 — Axiomantes
a.ultima_chave_conhecida()
```

---

## Consultar Ariadne (CLI)

```bash
python consultar_ariadne.py lua "Lua cheia"
python consultar_ariadne.py numero 17
python consultar_ariadne.py duplas --limite 10
python consultar_ariadne.py triplas --limite 10
python consultar_ariadne.py pergaminho 55
```

---

## Executar

```bash
# Simulação principal
python main.py

# Campanha (múltiplas eras)
python campanha_v6.py

# Simulação alternativa V7
python simular_v7.py
```

---

## Dados incluídos

- **1962 sorteios reais** (2004-2026) em pergaminhos individuais;
- **55 pergaminhos 2026** com astronomia, estatísticas e assinatura SHA256;
- **Datasets anuais** 2004-2026 em `biblioteca/fontes/`;
- **Excel "Saídas de Bolas"** com frequências históricas normalizadas;
- **Índices** de duplas e triplas mais frequentes.
