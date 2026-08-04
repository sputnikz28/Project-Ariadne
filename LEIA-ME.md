# Oráculos do Euromilhões — V13

Simulador narrativo e estatístico do Euromilhões. O projeto explora padrões históricos através de personagens, facções e uma Biblioteca viva — sem nunca pretender prever resultados.

> Padrões históricos não aumentam a probabilidade de prever um sorteio futuro. Uma chave simples tem sempre a mesma probabilidade matemática de 1 em 139.838.160.

---

## Estado Atual da Plataforma (V13)

Um mapa rápido do que existe realmente neste repositório hoje, separado de ideias — ver [Roadmap / Visão Futura](#roadmap--visão-futura) para o que ainda **não** está implementado.

- ✅ **Motor de simulação** — arquitetura de plugins (`core/registry.py`, `core/plugin_loader.py`, `core/strategy.py`), 21 facções votantes auto-descobertas, Ariadne como único ponto de acesso a dados, Conselho (filtro, votação ponderada, corrupção de Malphas), 21 raças (apenas lore), i18n (6 línguas).
- ✅ **Pipeline de dados históricos** — 1.968 sorteios reais do Euromilhões (2004–2026), datasets anuais imutáveis, mais `core/services/historical_dataset.py`, `historical_astronomy.py`, `historical_statistics.py`, `historical_scroll.py` e `historical_draw_generator.py` (usados por `register_official_draw.py`, um CLI transacional completo — staged → validado → instalado, com rollback — para registar novos sorteios oficiais).
- ✅ **Heroes & Legends** — registries `library/heroes/` e `library/legends/` (`entries/*.json` como fonte de verdade, índices derivados `LIVRO_DOS_HEROIS.json`/`LIVRO_DAS_LENDAS.json`), mais `core/services/hero_evaluation.py`/`legend_evaluation.py` e os respetivos CLIs (`evaluate_heroes.py`, `evaluate_legends.py`).
- ✅ **Dashboard Dataset** — `core/services/dashboard_data.py`, uma camada pura de montagem de dados: Heroes, Legends, Base de Chaves, Characters, Houses, Executive Summary, Economy e Categorias de Prémios estão todos implementados e testados contra dados reais (ver [Dashboard](#dashboard) abaixo). Ainda não existe camada de visualização — é apenas montagem de dados.
- ✅ **Biblioteca dos Artefactos** — `core/services/artifact_schema.py`, `artifact_registry.py` e `artifact_inspiration.py`; 15 artefactos narrativos fundadores, todos verificados sem qualquer efeito em algoritmos, resultados ou probabilidades (ver [Biblioteca dos Artefactos](#biblioteca-dos-artefactos) abaixo).
- ✅ **Testes** — 500 testes em 22 módulos (`python -m unittest discover -s tests`).

---

## Núcleo

- **Ariadne** — guardiã da Biblioteca; único ponto de acesso a dados para todas as facções;
- **Pergaminhos** — um ficheiro JSON por extração real (2004-2026, 1968 sorteios);
- **Livros** — conhecimento derivado: frequências, duplas, triplas, lua, cartógrafos;
- **Fontes** — datasets anuais imutáveis (2004-2026);
- **Consultas** — cache de respostas Ariadne reutilizáveis;
- **Ordem Élfica** — recupera relíquias e pergaminhos corrompidos;
- **Esquadrão Negro** — rouba livros e relíquias; cria grimório negro.

---

## Estrutura principal

```text
library/
├── ariadne/              ← engine.py — classe Ariadne
├── sources/              ← datasets anuais 2004-2026 (imutáveis)
├── scrolls/
│   ├── 2004/ … 2025/     ← formato compacto (1.929 pergaminhos)
│   └── 2026/             ← formato completo com astronomia (61 pergaminhos)
├── books/
│   └── cartographers/    ← 5 livros analíticos gerados pelos Cartógrafos
├── indexes/              ← duplas, triplas, frequências
├── heroes/                ← HeroRegistry — entries/ + LIVRO_DOS_HEROIS.json derivado
├── legends/                ← LegendRegistry — entries/ + LIVRO_DAS_LENDAS.json derivado
├── artifacts/              ← Biblioteca dos Artefactos — entries/ + LIVRO_DOS_ARTEFACTOS.json derivado
├── cache/                ← cache de consultas Ariadne
└── black_kors/
    └── papyri/           ← papiros semanais da Nyxara

core/services/            ← serviços partilhados, puros (sem I/O na maioria)
├── combinations.py, fitness.py            ← utilitários de chave partilhados
├── atomic_io.py                           ← escrita atómica de JSON
├── historical_dataset.py, historical_astronomy.py,
│   historical_statistics.py, historical_scroll.py,
│   historical_draw_generator.py           ← pipeline de registo de sorteios oficiais
├── hero_evaluation.py, legend_evaluation.py  ← classificação determinística de Heroes/Legends
├── run_manifest.py                        ← manifesto de proveniência por execução
├── dashboard_data.py                      ← Dashboard Dataset (ver abaixo)
└── artifact_schema.py, artifact_registry.py,
    artifact_inspiration.py                ← Biblioteca dos Artefactos (ver abaixo)

factions/
├── kors/                 ← Kors de Elarion (V7.2)
├── chaos_cartographers/  ← Cartógrafos do Caos (V8)
├── axiomantes/           ← Axiomantes de Nemerion (V8.1)
└── clerics/, ... (21 facções no total, ver README.md para a lista completa)

experiments/
└── axiomancers/
    └── runs/             ← relatórios JSON por execução do ritual

artifacts/                ← sistema MAIS ANTIGO e distinto: relíquias/amuletos mecânicos ligados ao estado da simulação (V4) — não confundir com library/artifacts/
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
| Preto | Nyxara das Sombras Semanais | Ecos da semana ISO · grava papiro em `library/black_kors/` |

### Cartógrafos do Caos (V8)
Cinco analistas que **não geram chaves** — produzem livros analíticos para consulta por outras facções. Correm antes de todos os outros e escrevem em `library/books/cartographers/`.

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
Experiência completa em `experiments/axiomancers/runs/experiencia_YYYYMMDD_HHMMSS.json`.

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
from library.ariadne.engine import Ariadne
a = Ariadne()

# Pergaminhos 2026
a.scroll_state(55)
a.search_moon("Lua cheia")

# Índices
a.pairs(limite=10)
a.triples(limite=10)

# Fontes normalizadas
a.numero(17)

# V7.2 — Kors
a.overdue_numbers(15)
a.least_frequent_numbers(20)
a.transition_pattern()
a.weekly_echoes(semana_iso=28)
a.create_papyrus(semana_iso=28, dados={...})

# V8 — Cartógrafos
a.full_history(desde="2020-01-01", ultimos=500)

# V8.1 — Axiomantes
a.last_known_key()
```

---

## Consultar Ariadne (CLI)

Os subcomandos do CLI mantêm-se em português mesmo com o nome do
ficheiro em inglês:

```bash
python query_ariadne.py lua "Lua cheia"
python query_ariadne.py numero 17
python query_ariadne.py duplas --limite 10
python query_ariadne.py triplas --limite 10
python query_ariadne.py pergaminho 55
```

---

## Executar

```bash
# Simulação principal
python main.py

# Campanha (múltiplas eras)
python campaign_v6.py

# Simulação alternativa V7
python simulate_v7.py

# Suite de testes
python -m unittest discover -s tests
```

---

## Dashboard

`core/services/dashboard_data.py` é uma camada pura de transformação de
dados para investigação/análise — nunca lê um ficheiro, nunca acede a um
Registry, nunca calcula aleatoriedade. Cada função recebe dados já
carregados (o resultado de `load_all()` de um Registry, ou um JSON de
dataset histórico já lido) e devolve-os como pequenas dataclasses
imutáveis (tuples, nunca lists).

| Linha / função | Produz | Fonte |
|---|---|---|
| `build_heroes_rows()` | `HeroRow` | `HeroRegistry().load_all()` |
| `build_legends_rows()` | `LegendRow` | `LegendRegistry().load_all()` |
| `build_key_base_rows()` | `DrawRow` | `sorteios` do dataset histórico de 2026 |
| `build_characters_rows()` | `CharacterRow` | `races/*/characters.json` |
| `build_houses()` | `HouseEntry` | `races/*/lineages.json` cruzado com o arquivo de população |
| `build_executive_summary()` | `ExecutiveSummary` | contagens de Heroes/Legends + Economy |
| `build_economy_rows()` / `build_economy_summary()` | `EconomyDrawRow` / `EconomySummary` | `estatisticas_financeiras`/`premios` do dataset de 2026 |
| `build_prize_category_rows()` / `build_prize_category_summary()` | `PrizeCategoryRow` / `PrizeCategorySummary` | `premios.categorias` do dataset de 2026 |
| `build_dashboard_dataset()` | `DashboardDataset` | compõe tudo o que está acima — nunca chama os construtores diretamente |

**Economy e Categorias de Prémios usam dados reais, nunca sintéticos.**
O dataset oficial de 2026 só tem dados financeiros/de categorias de
prémio completos em 15 dos seus 61 sorteios — confirmado pelas próprias
flags `qualidade_dados` do dataset, nunca inferido a partir de um valor
estar ou não a `null`. Toda a soma/média/mínimo/máximo em
`EconomySummary`/`PrizeCategorySummary` é calculada apenas sobre os
sorteios que realmente têm esse campo; um campo sem nenhuma observação
real resolve para `None`, nunca para um `0` inventado ou uma estimativa.
`PrizeCategoryRow` gera sempre exatamente 13 linhas por sorteio — a
tabela oficial fixa de escalões de prémio do Euromilhões, uma regra do
jogo e não um facto por sorteio — só os vencedores observados podem ser
`None`.

`GenerationRow`/`FrequenciesRow` já existem como contrato de dados no
módulo, mas ainda não têm função construtora — `DashboardDataset`
mantém-nos como tuples vazios por omissão. Ainda não existe um pacote
`dashboard/` de visualização — ver [Roadmap](#roadmap--visão-futura).

---

## Biblioteca dos Artefactos

Uma coleção **puramente narrativa e cerimonial**, distinta do sistema
mais antigo `artifacts/` (`ark.py`/`living.py`/`relics/`/`amulets/`,
era V4, mecanicamente ligado ao estado da simulação). `library/artifacts/`
nunca influencia uma chave, um voto ou uma probabilidade — cada uma das
15 entradas fundadoras tem `altera_algoritmo`, `altera_resultados` e
`altera_probabilidades` explicitamente `false`, verificado
estruturalmente em todas as camadas abaixo, não apenas afirmado em texto.

- **`library/artifacts/entries/*.json`** — a única fonte primária, 15 artefactos fundadores (Moeda de Midas, Joaninha de Sylvaris, Estrela de Lyra, Fragmento do Arco-Íris de Íris, Trevo de Aethoria, cinco Ferraduras, Daruma da Perseverança, Brandy da Vitória Imperial, Cuequinhas Azuis Celestiais, Lótus da Tranquilidade, Codex da Fortuna Eterna). Nunca reescrita por nenhum código desta camada.
- **`core/services/artifact_schema.py`** — `normalize_artifact()` converte qualquer uma das 15 formas de origem (genuinamente heterogéneas, escritas independentemente) num só `ArtifactRecord` pequeno: um núcleo fixo (id, nome, tipo, raridade, estado, criador, energia, lore, historia, tags…) mais duas válvulas de escape que garantem que nada se perde — `extras` (todo o campo não-núcleo, verbatim) e `raw` (o dict original intacto). Nunca inventa um valor por omissão para um campo ausente; ausente significa `None`, nunca uma suposição.
- **`core/services/artifact_registry.py`** — `load_all_artifacts()` (deteta id duplicado e desalinhamento nome-de-ficheiro/id), `ArtifactRegistry` (consultas `by_id`/`by_type`/`by_tag`/`by_creator`, sem aleatoriedade nenhuma), e `build_index()`/`write_index()`, que derivam `library/artifacts/LIVRO_DOS_ARTEFACTOS.json` — sempre regenerado a partir de `entries/`, nunca editado à mão, nunca fonte de verdade por si só.
- **`core/services/artifact_inspiration.py`** — `generate_inspiration(record, seed)`, um gerador determinístico (`random.Random(seed)`, nunca o `random` global) de "sementes de inspiração" narrativas para novos conceitos de personagem livremente inspirados num artefacto. Explicitamente proibido — e filtrado defensivamente, não apenas documentado — de sugerir números/estrelas, prever um sorteio, ou referir alterações a algoritmos/resultados/probabilidades; nunca cria ou altera um Hero ou uma Legend; não faz I/O de ficheiros.

---

## Roadmap / Visão Futura

Tudo o que se segue é uma ideia documentada, não código implementado —
nada aqui afeta a simulação, uma chave, um voto ou uma probabilidade
hoje. Ver [Estado Atual da Plataforma (V13)](#estado-atual-da-plataforma-v13) acima para o que existe de facto.

- **Pacote de visualização `dashboard/`** — o Dashboard Dataset (camada de dados, concluída) ainda não tem consumidor: sem exportação Excel, sem relatório CLI, sem gráfico. `requirements-dashboard.txt` (`openpyxl`) está preparado para isso.
- **Construtores de `GenerationRow`/`FrequenciesRow`** — os contratos já existem em `dashboard_data.py`; ainda não há função que leia dados reais de gerações/frequências para eles.
- **Novas facções** — Juízes do Conselho, Geómetras do Véu, Estatísticos Imperiais (já nomeadas no planeamento, ainda não implementadas).
- **Serviços estatísticos partilhados** — `StatisticsService`, `DelayService`, `PairService`, `TripleService`, `EntropyService`, `TrendService`, para eventualmente substituir lógica de frequências/atraso/gaps hoje duplicada em `core/evolution/statistics.py`, `factions/chaos_cartographers/*.py` e `factions/axiomantes/profile.py`.
- **Retrofit de `ctx['rng']`** — decidir se todas as facções devem usar o `ctx['rng']` partilhado e com seed (hoje só o Panteão, Esqueletos e Cronomantes o fazem; os Clérigos mantiveram deliberadamente o `random` global por razões de reprodutibilidade).
- **Runner de Benchmarks** — `benchmarks/` é apenas estrutura; ainda não existe nenhum executor.

---

## Changelog

| Versão | Destaque |
|---|---|
| V1 | Primeiro conselho de agentes |
| V2 | Estratégias distintas por agente |
| V3 | Campanhas, gerações, personagens lendárias |
| V4 | Conselho + corrupção de Malphas; amuletos; relíquias; biblioteca negra |
| V5 | Guerra das sombras — Esquadrão Negro vs Ordem Élfica; grimório aprende entre execuções |
| V6 | Campanhas multi-era; Escribas, crónicas, Atlas; mundos configuráveis |
| V7 | Biblioteca Eterna; Ariadne como único ponto de acesso a dados; Vampiros; Gárgulas |
| V7.2 | Kors de Elarion — quatro observadores nomeados, só consultam Ariadne |
| V8 | Cartógrafos do Caos — livros analíticos partilhados entre facções |
| V8.1 | Axiomantes de Nemerion — permutação Feistel sobre 139M combinações; pontuação por Perfil dos Ecos; i18n |
| V9 | Arquitetura de plugins — `FactionRegistry`, `CompatFaction`, `manifest.json` por facção; adicionar uma facção nunca toca em `main.py` |
| V10 | Mystics — 8 novas ordens (lore + scaffolding de plugin), abstêm-se sempre por design |
| V10.5 | Arquitetura completa — `races/` totalmente lore-only, primeiros serviços partilhados reais (`combinations.py`, `fitness.py`) |
| V11 | Clérigos migrados para a arquitetura de plugins (`races/legacy.py` retirado) — 21 facções votantes no total |
| V12.3 | Dashboard Dataset — Heroes, Legends, Base de Chaves, Characters, Houses, Executive Summary, Economy, Categorias de Prémios |
| V13 | Biblioteca dos Artefactos — schema, registry e gerador determinístico de inspiração narrativa; CLI de registo de sorteios oficiais |

---

## Dados incluídos

- **1968 sorteios reais** (2004-2026) em pergaminhos individuais;
- **61 pergaminhos 2026** com astronomia, estatísticas e assinatura SHA256;
- **Datasets anuais** 2004-2026 em `library/sources/`;
- **Excel "Saídas de Bolas"** com frequências históricas normalizadas;
- **Índices** de duplas e triplas mais frequentes.
