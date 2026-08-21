# CLAUDE.md

# Oráculos do Euromilhões — Especificação do Projeto (V1 → V13)

> Documento de contexto para desenvolvimento contínuo.
> **Open source:** https://github.com/tsilva28/Project-Ariadne (MIT License)

## Objetivo

Criar um universo narrativo em torno da análise histórica do
Euromilhões. O projeto **não pretende prever resultados**, mas explorar
estratégias, estatísticas, simulações e personagens que consultam uma
Biblioteca de conhecimento.

---

# V1 — V6 (resumo)

- **V1** — Conselho inicial de personagens; geração de chaves; relatórios.
- **V2** — Estratégias distintas por personagem; Conselho escolhe chave final.
- **V3** — Campanhas, gerações e evolução; personagens lendárias; ranking histórico.
- **V4** — Amuletos vivos; Artefactos; Relíquias persistentes; Biblioteca com livros proibidos; Esquadrão Negro; Ordem Élfica.
- **V5** — Ariadne concebida como guardiã; Pergaminhos; Crónicas; Treefolks; Vampiros; Gárgulas.
- **V6** — Configuração por `config.txt`; campanhas multi-era; Esqueletos; Vilão Malphas.

---

# Universo

## Facções geradoras de chaves

| Facção | Módulo | Estratégia |
|--------|--------|-----------|
| Clérigos | `factions/clerics/algorithm.py` + `archetypes.py` | Algoritmo genético, 14 gerações, 9 arquétipos ancestrais (V11; Minotauro — persistência de chave — adicionado no Commit 19) |
| Melforks | `factions/melforks/algorithm.py` | Algoritmo genético especializado |
| Anões | `factions/dwarves/algorithm.py` | Combinatória por clãs (3 × 15 chaves) |
| Fadas | `factions/faeries/algorithm.py` | Ponderação por números quotidianos |
| Lobisomens | `factions/werewolves/algorithm.py` | Monte Carlo de aptidão (fase lunar) |
| Treefolks | `factions/treefolks/algorithm.py` | Mede fantasmas estatísticos |
| Vampiros | `factions/vampires/` | Triplas frequentes via Ariadne (V8) |
| Gárgulas | `factions/gargoyles/` | Duplas frequentes via Ariadne (V8) |
| Cronomantes | `factions/chronomancers/` ← `races/chronomancers.py` | Energia dos eventos de extração |
| Esqueletos | `factions/skeletons/` ← `races/skeletons.py` | Janela móvel de 25 números |
| Esquadrão Negro | `orders/black_squad/` | Anti-popularidade; grimório roubado |
| Ordem Élfica | `orders/elven_order/` | Missões de recuperação (não vota directamente) |
| Kors de Elarion | `factions/kors/` | Observação via Ariadne (V7.2) |
| Axiomantes de Nemerion | `factions/axiomantes/` | Labirinto combinatório + Feistel (V8.1) |
| Druids | `factions/druids/` ← `races/mystics/nature/druids/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |
| Moon Priests | `factions/moon_priests/` ← `races/mystics/nature/moon_priests/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |
| Star Gazers | `factions/star_gazers/` ← `races/mystics/nature/star_gazers/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |
| Shamans | `factions/shamans/` ← `races/mystics/prophecy/shamans/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |
| Witches | `factions/witches/` ← `races/mystics/prophecy/witches/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |
| Seers | `factions/seers/` ← `races/mystics/prophecy/seers/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |
| Oracles | `factions/oracles/` ← `races/mystics/prophecy/oracles/` | Placeholder — não gera chaves por design; abstém-se sempre (V10) |
| Bone Readers | `factions/bone_readers/` ← `races/mystics/prophecy/bone_readers/` | Placeholder — sem algoritmo; abstém-se sempre (V10) |

## Facções analíticas (não geram chaves)

| Facção | Módulo | O que produz |
|--------|--------|-------------|
| Cartógrafos do Caos | `factions/chaos_cartographers/` | 5 livros analíticos em `library/books/cartographers/` (V8) |
| Monges e Escribas | `artifacts/amulets/books.py` | Livros reconstruíveis, índices |

## Vilões e mecânicas narrativas

- **Malphas** — corrompe a chave final com deslocamentos aleatórios
- **Vírus de Malphas** — infecta heróis; bónus de score mas revelado no Conselho
- **Guerra do Conselho** — Ordem Élfica tenta purificar; Malphas corrompe
- **Convicção Sombria** — mantra que reforça simbolicamente a chave

---

## Internacionalização (`i18n/`)

Módulo `i18n/translations.py` — 6 línguas × 25 chaves para os 9 países participantes do Euromilhões.

### Configuração

`config.txt` → secção `[MUNDO]`:

```ini
lang = pt   # pt · es · fr · nl · de · en · gb (gb=alias de en; inválido→pt)
```

| Código | Língua | Países |
|--------|--------|--------|
| `pt` | Português | Portugal 🇵🇹 |
| `es` | Español | España 🇪🇸 |
| `fr` | Français | France 🇫🇷 · Belgique 🇧🇪 · Luxembourg 🇱🇺 · Suisse 🇨🇭 |
| `nl` | Nederlands | België 🇧🇪 |
| `de` | Deutsch | Österreich 🇦🇹 · Schweiz 🇨🇭 · Luxemburg 🇱🇺 |
| `en` / `gb` | English | UK 🇬🇧 · Ireland 🇮🇪 |

### API pública

```python
from i18n.translations import t, lang_de_cfg

lang = lang_de_cfg(cfg)          # lê e valida lang do ConfigParser; fallback 'pt'
t('veredicto_acaso', lang)       # devolve string traduzida; fallback pt se chave ausente
```

### Tabela de chaves de tradução (25 chaves)

| Chave | Utilizado em | Descrição |
|-------|-------------|-----------|
| `veredicto_acaso` | `ritual.py` | Excesso ∈ [-5%, +5%] |
| `veredicto_ligeiro` | `ritual.py` | Excesso ∈ [+5%, +10%] |
| `veredicto_desvio` | `ritual.py` | Excesso ≥ +10% |
| `veredicto_abaixo` | `ritual.py` | Excesso < -5% |
| `portal_aberto` | `ritual.py` | Status curto: "ABERTO" / "OPEN" / etc. |
| `portal_fechado` | `ritual.py` | Status curto: "FECHADO" / "CLOSED" / etc. |
| `portal_aberto_msg` | `council.py`, `main.py` | Mensagem longa: "Portal ABERTO" |
| `portal_fechado_msg` | `council.py`, `main.py` | Mensagem longa com nota de abstenção |
| `aviso` | `ritual.py` | Disclaimer obrigatório (parágrafo longo) |
| `simulacao_concluida` | `main.py` | Linha de fim de simulação |
| `semente` | `main.py` | Label da semente do universo |
| `chave_original` | `main.py` | Label da chave antes da corrupção |
| `chave_corrompida` | `main.py` | Label da chave após Malphas |
| `relatorio` | `main.py` | Label do ficheiro de relatório |
| `individuos_unicos` | `main.py` | Contagem de heróis gerados |
| `registos_externos` | `main.py` | Contagem de registos no arquivo |
| `livros_proibidos` | `main.py` | Livros da Biblioteca Negra |
| `reliquias` | `main.py` | Relíquias persistentes |
| `magos_negros` | `main.py` | Contagem do Esquadrão Negro |
| `missoes_elficas` | `main.py` | Missões da Ordem Élfica |
| `esqueletos` | `main.py` | Representantes dos Esqueletos |
| `invocacoes` | `main.py` | Invocações da Convicção Sombria |
| `kors` | `main.py` | Label para Kors de Elarion |
| `cartografos` | `main.py` | Label para Cartógrafos do Caos |
| `livros_label` | `main.py` | Palavra "Livros" no sumário |

### O que NÃO se traduz

Nomes próprios do universo narrativo ficam sempre em português/original:
Kors de Elarion · Axiomantes de Nemerion · Ariadne · Malphas · Ordem Élfica · Esquadrão Negro · Cartógrafos do Caos · etc.

O campo `lang` é gravado em cada experiência JSON dos Axiomantes (`ritual.py → result['lang']`).

---

## Referência: métodos Ariadne (`library/ariadne/engine.py`)

| Método | Introduzido | O que faz |
|--------|-------------|----------|
| `scroll_state(n)` | V7 | Estado e integridade do pergaminho N de 2026 |
| `search_moon(fase)` | V7 | Frequências nos sorteios com dada fase lunar |
| `pairs(limite)` | V7 | Duplas mais frequentes de `indices/duplas.json` |
| `triples(limite)` | V7 | Triplas mais frequentes de `indices/triplas.json` |
| `numero(n)` | V7 | Frequência histórica de um número (normalizado) |
| `overdue_numbers(limite)` | V7.2 | Números com maior atraso nos pergaminhos 2026 |
| `least_frequent_numbers(limite)` | V7.2 | Menos frequentes no histórico completo normalizado |
| `transition_pattern()` | V7.2 | Análise penúltima→última chave (chegados, saídos, persistentes) |
| `weekly_echoes(semana_iso)` | V7.2 | Sorteios da mesma semana ISO em todos os anos |
| `create_papyrus(semana_iso, dados)` | V7.2 | Grava papiro em `library/black_kors/papyri/` |
| `full_history(desde, ate, ultimos)` | V8 | Todos os sorteios de todos os anos (1962 draws, 2004–2026) |
| `last_known_key()` | V8.1 | Último sorteio registado (data, numeros, estrelas) |

**Nota sobre formatos de pergaminho:**
- 2026: `"data": {"extracao": "YYYY-MM-DD", "timestamp_utc": "..."}` (dict com astronomia completa)
- 2004-2025: `"data": "YYYY-MM-DD"` (string directa) + `"horario": {"timestamp_utc": "..."}`

Ariadne trata ambos os formatos de forma transparente.

**Modo temporal (Commit 23):** `Ariadne(scrolls=<coleção já carregada e cortada por cutoff>)` — quando `scrolls` é fornecido, `scroll_state`/`search_moon`/`overdue_numbers`/`transition_pattern`/`full_history`/`weekly_echoes`/`last_known_key` operam exclusivamente sobre essa coleção congelada, sem qualquer leitura adicional de `library/scrolls/`. Sem `scrolls` (omisso), o comportamento é exatamente o de sempre (modo LIVE/NORMAL). `pairs`/`triples`/`numero`/`least_frequent_numbers` (baseados em `library/indexes/*.json`, sem qualquer timestamp) levantam `RuntimeError` numa instância temporal — nunca respondem silenciosamente a partir de um índice global sem corte temporal. Ver `core/services/historical_ariadne_source.py` e a secção "Fronteira Temporal" abaixo.

---

# V7 — Biblioteca Eterna

Estrutura da `library/`:

```
library/
├── ariadne/       ← engine.py (Ariadne)
├── sources/       ← datasets anuais imutáveis 2004–2026
├── scrolls/       ← pergaminhos JSON (1962 sorteios)
├── books/         ← livros reconstruíveis
│   └── cartographers/ ← 5 livros analíticos (Cartógrafos)
├── indices/       ← duplas, triplas, frequências, fases lunares
├── catalogue/     ← catálogo e inventário V7
├── cache/         ← consultas Ariadne em cache
└── black_kors/
    └── papyri/    ← papiros semanais de Nyxara
```

---

# V7.2 — Kors de Elarion

Facção em `factions/kors/`. Toda a informação flui exclusivamente através de Ariadne.

| Kor | Ficheiro | Estratégia |
|-----|---------|-----------|
| Branco — Aelyra dos Silêncios | `factions/kors/white.py` | `ariadne.overdue_numbers(15)` → 15 mais atrasados |
| Vermelho — Kael da Chama Fria | `factions/kors/red.py` | `ariadne.least_frequent_numbers(20)` → menos frequentes |
| Verde — Sylvara das Passagens | `factions/kors/green.py` | `ariadne.transition_pattern()` → padrão penúltima→última |
| Preto — Nyxara das Sombras | `factions/kors/black.py` | `ariadne.weekly_echoes(semana_iso)` + cria papiros |

### Integração

- `factions/kors/council.py` → `kors_council(ariadne)` chamado em `main.py`
- Origem no arquivo: `kors_elarion`
- Peso configurável em `[KORS] peso_conselho` em `config.txt`

---

# V8 — Cartógrafos do Caos

Cinco analistas em `factions/chaos_cartographers/`. Não geram chaves — produzem livros analíticos em `library/books/cartographers/`.

| Cartógrafo | Ficheiro | Livro gerado |
|-----------|---------|-------------|
| Eldran das Constelações | `constellations.py` | Livro das Constelações Numéricas |
| Vesara dos Intervalos | `cycles.py` | Livro dos Ciclos Eternos |
| Lirien das Correntes | `trends.py` | Livro das Tendências e Correntes |
| Thalvos do Acaso Esperado | `randomness.py` | Livro do Acaso Esperado |
| Oryn dos Ecos Sequenciais | `markov.py` | Livro dos Ecos Sequenciais |

### Novos métodos Ariadne (V8)

- `full_history(desde, ate, ultimos)` — todos os sorteios 2004–2026; suporta ambos os formatos de pergaminho

### Integração

- `factions/chaos_cartographers/council.py` → `execute_cartographers(ariadne, cfg)` chamado em `main.py`
- Corre antes dos Kors (mesma instância Ariadne)
- Monte Carlo configurável em `[CARTOGRAFOS_CAOS] monte_carlo_simulacoes`

---

# V8.1 — Axiomantes de Nemerion

Facção em `factions/axiomantes/`. Percorrem o Labirinto de 139.838.160 câmaras usando uma permutação Feistel reproduzível.

### Matemática

- **Universo**: C(50,5) × C(12,2) = 2.118.760 × 66 = **139.838.160 combinações**
- **Rank/unrank** (algoritmo combinádico):
  - `rank_key([2,14,28,33,48], [8,10])` → inteiro único em [0, 139.838.159]
  - `unrank_key(103.811.641)` → ([2,14,28,33,48], [8,10])
- **Feistel (_H = 11826, 4 rondas)**: bijecção sobre [0, _H²-1]; cycle-walk para valores ≥ UNIVERSE
  - `key_position(nums, ests, seed)` — posição via Feistel⁻¹; O(1)
  - `key_at_position(pos, seed)` — chave via Feistel; O(1)

### Ritual dos Trinta Ecos (`factions/axiomantes/ritual.py → execute_ritual`)

1. `ariadne.full_history()` → anchor = último sorteio registado (`ariadne.last_known_key()`)
2. `key_position(anchor, seed)` → posição do anchor na sequência Feistel
3. Para cada sorteio do período (`periodo_anos` em config): calcula posição → separa **echoes** (antes do anchor) dos restantes
4. Métricas: `coverage%`, `universe_fraction%`, `excess%`, `espaco_medio_obs`, `espaco_teorico`
5. **Portal aberto** se `coverage >= coverage_threshold AND excess >= min_excess`
6. Se portal aberto:
   - `calculate_profile(echoes)` → perfil estatístico dos ecos
   - `choose_by_profile(...)` → avalia `n_candidates` chaves inéditas por score
   - Devolve a chave com maior pontuação

### Perfil dos Ecos (`factions/axiomantes/profile.py → calculate_profile`)

| Campo | Como se calcula |
|-------|----------------|
| `soma_media`, `sum_deviation` | média e desvio-padrão das somas dos 5 números |
| `faixa_soma_preferida` | `[media - desvio, media + desvio]` |
| `paridades_preferidas` | top-2 combinações (nPares, nÍmpares) por frequência |
| `baixos_altos_preferidos` | top-2 combinações (n≤25, n>25) por frequência |
| `numeros_mais_frequentes` | top-10 números por ocorrências nos ecos |
| `numeros_menos_frequentes` | 10 números com menos ocorrências |
| `estrelas_mais_frequentes` | top-6 estrelas por ocorrências nos ecos |
| `gap_medio` | média dos gaps consecutivos por chave, depois média global |
| `amplitude_media` | média de (max - min) por chave |

### Pontuação de chaves (`profile.py → score_key`) — 0 a 100 pts

| Dimensão | Pts máx | Lógica |
|---------|---------|--------|
| Soma dentro da faixa preferida | 20 | 20 se ∈ faixa; decai 0.5 pt por unidade fora |
| Paridade dominante | 15 | 15 se 1.ª preferida; 10 se 2.ª |
| Baixos/altos dominantes | 15 | 15 se 1.ª preferida; 10 se 2.ª |
| Afinidade com top-5 nums frequentes | 20 | pico 20 em 3 matches; penaliza ≥4 (16/10 pts) |
| Afinidade com top-3 estrelas frequentes | 15 | 7.5 pts por estrela coincidente |
| Gap médio próximo do perfil | 10 | decai 0.8 pt por unidade de diferença |
| Amplitude próxima do perfil | 5 | decai 0.15 pt por unidade de diferença |
| Bónus: 1-2 números raramente vistos | +5 | fomenta diversidade; cap final 100 |

### Parâmetros de config (`[AXIOMANTES]` em `config.txt`)

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `peso_conselho` | 0.75 | Peso no Conselho (só vota quando portal aberto) |
| `periodo_anos` | 1 | Anos de sorteios usados como ecos de comparação |
| `limiar_cobertura` | 0.50 | Cobertura mínima para abrir o Portal |
| `excesso_minimo` | 0.0 | Excesso mínimo sobre o esperado |
| `n_candidatos` | 50000 | Chaves inéditas avaliadas (50K ≈ 1.5s; 250K ≈ 4s) |
| `guardar_experiencia` | true | Grava JSON em `experiments/axiomancers/runs/` |

### Estrutura de ficheiros

| Ficheiro | Conteúdo |
|---------|---------|
| `factions/axiomantes/labyrinth.py` | rank/unrank + Feistel permutation |
| `factions/axiomantes/profile.py` | Perfil dos Ecos + pontuação de chaves |
| `factions/axiomantes/ritual.py` | análise completa + Trinta Ecos + grava experiência |
| `factions/axiomantes/council.py` | ponto de entrada para `main.py` |
| `factions/axiomantes/config.json` | metadados e linhagens |
| `experiments/axiomancers/runs/` | relatórios JSON por execução |

### Integração

- `factions/axiomantes/council.py` → `axiomantes(ariadne, seed, cfg)` chamado em `main.py`
- Recebe o mesmo `seed` da simulação → ritual reproduzível
- Só vota quando portal aberto (caso contrário devolve `[]`)
- Peso configurável em `[AXIOMANTES] peso_conselho` em `config.txt`

---

# V10 — Mystics (arquitetura, lore e skeletons — sem algoritmos)

Nova raça `races/mystics/` que recupera o espírito original da V1: intuição, rituais e tradição ancestral a par da matemática e da estatística. Dividida em duas linhagens:

| Linhagem | Filosofia | Ordens |
|---|---|---|
| Nature Mystics | Harmonia com a natureza — ciclos lunares, estações, ciclos celestes | Druids, Moon Priests, Star Gazers |
| Prophecy Mystics | Interpretação do destino através de símbolos e rituais | Shamans, Witches, Seers, Oracles, Bone Readers |

**Ficheiros de dados** (`races/mystics/`): `lore.md` (história completa), `orders.json` (8 ordens), `characters.json` (16 personagens, 2 por ordem), `artifacts.json` (16 artefactos, 2 por ordem), mais uma pasta `nature/<ordem>/` ou `prophecy/<ordem>/` por ordem com um `README.md` próprio.

**Plugins** (`factions/{druids,moon_priests,star_gazers,shamans,witches,seers,oracles,bone_readers}/`): cada um com `manifest.json`, `council.py` (caminho activo, regista-se via `FactionRegistry`), `strategy.py` (skeleton nativo `core.strategy.Faction`, ainda não referenciado em `manifest.json`) e `README.md`. **Todos os `council()` devolvem sempre `[]`** — abstenção válida, não erro — até existir algoritmo real.

**Oracles** são um caso especial: por design nunca geram chaves — interpretam as propostas do Conselho. Por agora registam-se e abstêm-se como as restantes; a meta-análise fica para trabalho futuro (ver `factions/oracles/council.py`).

**Princípio inegociável:** nenhuma ordem mística deve, por design, superar as facções matemáticas — todas passam pelos mesmos Juízes e pelo mesmo motor de Backtesting. A crença nunca substitui a estatística (ver `races/mystics/lore.md`).

**Zero alterações a `main.py`** — o resumo de facções já era genérico (`# Plugin factions summary — auto-generated, no hardcoded names`), por isso as 8 novas ordens aparecem automaticamente assim que `FactionRegistry.discover("factions")` as encontra.

---

# Architecture

Project Ariadne follows a layered architecture. Each layer depends only on the layers above it in this list — never the reverse.

```
core/
    Framework services, plugin registry, evaluation, shared algorithms
        ↓
library/
    Persistent knowledge and registries — Ariadne (data broker), Scrolls,
    Heroes/Legends registries, Biblioteca dos Artefactos
        ↓
factions/
    Executable candidate-generation methodologies (one plugin per faction)
        ↓
orders/
    Narrative organizations and special systems (Pantheon, Black Squad, Elven Order)
        ↓
races/
    Lore only — characters, artifacts, lineages/orders. No executable code.
        ↓
datasets/
    Historical Euromillions data (immutable)
        ↓
experiments/
    Generated simulation outputs, reports, backtesting results
        ↓
dashboard/ (Excel export implemented; no CLI/wiring yet)
    Visualisation and analysis. dashboard/excel_export.py (Commit 9)
    consumes an already-built DashboardDataset and writes an .xlsx
    workbook — pure in memory, touches disk only in export_to_excel().
    core/services/dashboard_data.py (V12.3) is the data-assembly layer
    that feeds it (see V12.3 section below). No script yet assembles a
    real DashboardDataset from live Heroes/Legends/datasets/races and
    calls the exporter — that wiring remains unbuilt.
```

| Layer | Responsibility |
|---|---|
| `core/` | Generic, reusable framework: plugin registry, proposal model, shared algorithms, shared services (`core/services/`) |
| `library/` | Persistent knowledge and registries: Ariadne, Scrolls, Heroes, Legends, Biblioteca dos Artefactos |
| `factions/` | Candidate-generation strategies — one plugin per faction |
| `orders/` | Narrative organisations and special systems, outside Council voting by design |
| `races/` | Lore, characters and world-building — documentation only |
| `datasets/` | Historical knowledge (immutable source data) |
| `experiments/` | Generated outputs (simulations, backtests, reports) |
| `dashboard/` | Excel export implemented (`dashboard/excel_export.py`, Commit 9); no CLI/wiring yet — its data layer (`core/services/dashboard_data.py`) already exists |

## Faction → Algorithm → Race map (selection)

| Faction | Algorithm | Race |
|---|---|---|
| Clerics | Genetic Algorithm — `factions/clerics/algorithm.py` (engine) + `archetypes.py` (9-lineage dispatcher; Minotauro's key-persistence lineage added Commit 19) (V11) | Clerics (`races/clerics/`) |
| Dwarves | Mountain-forge combinatorics (`factions/dwarves/algorithm.py`) | Dwarves (`races/dwarves/`) |
| Werewolves | Monte Carlo (`factions/werewolves/algorithm.py`) | Werewolves (`races/werewolves/`) |
| Vampires | Triple frequencies (`factions/vampires/algorithm.py`, `council.py`) | Vampires (`races/vampires/`) |
| Gargoyles | Frequent pairs (`factions/gargoyles/algorithm.py`, `council.py`) | Gargoyles (`races/gargoyles/`) |
| Kors | Multi-order statistical analysis (`factions/kors/`) | Kors (`races/kors/`) |
| Mystics (Druids, Moon Priests, Star Gazers, Bone Readers, Oracles, Seers, Shamans, Witches) | Ritual strategies — placeholders, no algorithm yet | Mystics (`races/mystics/`) |
| Chronomancers | Temporal energy (`factions/chronomancers/algorithm.py`); also generates the Pantheon's Aion (`representatives.py`) | Chronomancers (`races/chronomancers/`) |
| Chaos Cartographers | Chaos geometry — analytical, does not vote | Chaos Cartographers (`races/chaos_cartographers/`) |

Every faction under `factions/` maps to exactly one race package under `races/` — 21 factions in total as of V11 (the original 20 plus Clerics).

---

# Arquitetura V9 (Plugin Architecture — implementado)

## Módulo `core/`

```
core/
    __init__.py
    strategy.py      ← Proposal dataclass + Faction ABC
    registry.py      ← FactionRegistry (discover + register + all)
    plugin_loader.py ← CompatFaction wrapper + load_faction()
    evolution/       ← genetic algorithm engine (V10: moved from root evolution/)
    i18n/            ← translations.py (V10: moved from root i18n/)
    data/            ← loaders.py — historical/jackpot/moon data access (V10: moved from root sources/)
```

### `Proposal` e `Faction` (`core/strategy.py`)

```python
@dataclass
class Proposal:
    name: str
    key: tuple          # ([nums], [stars])
    weight: float
    origin: str = ""    # campo 'origem' no arquivo_destino
    home: str = ""      # campo 'casa' no registo_externo
    faction_class: str = ""
    extra: dict = field(default_factory=dict)

class Faction(ABC):
    manifest: dict = {}
    @abstractmethod
    def propose(self, context: dict) -> list[Proposal]: ...
```

### `FactionRegistry` (`core/registry.py`)

```python
registry = FactionRegistry().discover("factions")
for faction in registry.all():
    proposals = faction.propose(context)
```

`discover()` percorre `factions/<name>/` por ordem alfabética. Pastas começadas por `_` são ignoradas.

### Resolução por pasta (`core/plugin_loader.py → load_faction`)

1. `manifest.json` com `"class"` + `strategy.py` → instancia a classe (futuro nativo)
2. `council.py` com `FACTION_META` + `council()` → envolve num `CompatFaction`
3. Caso contrário → `None` (pasta ignorada)

`CompatFaction.propose()` trata 3 formatos de retorno de `council()`:
- Lista de dicts simples `{'nome', 'chave', 'peso', ...}`
- Estrutura de clãs anões: dict com `'carteira'` (lista de chaves)
- Dict de lobisomens: `{'ativo', 'simulacoes', 'finalistas'}`

### `manifest.json` (por facção)

```json
{
  "id": "vampiro",
  "name": "Vampiros de Elarion",
  "version": "1.0",
  "home": "Cripta Eterna",
  "config_section": "VAMPIROS",
  "weight_key": "peso_conselho",
  "default_weight": 0.90,
  "votes": true,
  "description": "..."
}
```

`"votes": false` → facção analítica (chaos_cartographers); excluída do Conselho.

## Facções no sistema de plugins

```
factions/
    axiomantes/           ✅ V8.1 + manifest.json
    chaos_cartographers/  ✅ V8   manifest.json (votes: false) — analítico
    clerics/              ✅ V11  algorithm.py (genetic engine) + archetypes.py (9 lineages, incl.
                                   Minotauro's key-persistence lineage, Commit 19) — the oldest
                                   methodology, migrated from races/legacy.py + core/evolution/genetic.py
    chronomancers/        ✅ V11  algorithm.py (temporal key) + representatives.py (Aion, Pantheon)
    dwarves/              ✅ V11  algorithm.py (self-contained; races/ tree is lore-only)
    faeries/              ✅ V11  algorithm.py (self-contained; races/ tree is lore-only)
    gargoyles/            ✅ V11  lineages.py migrated from races/gargoyles/ (self-contained)
    kors/                 ✅ V7.2 + manifest.json
    melforks/             ✅ V11  algorithm.py (self-contained; races/ tree is lore-only)
    skeletons/            ✅ V11  algorithm.py migrated from races/skeletons.py (self-contained)
    treefolks/            ✅ V11  algorithm.py + investigator.py (self-contained)
    vampires/             ✅ V11  lineages.py migrated from races/vampires/ (self-contained)
    werewolves/           ✅ V11  algorithm.py (self-contained; races/ tree is lore-only)
    druids/               ✅ V10  placeholder (races/mystics/nature/druids/) — abstém-se
    moon_priests/         ✅ V10  placeholder (races/mystics/nature/moon_priests/) — abstém-se
    star_gazers/          ✅ V10  placeholder (races/mystics/nature/star_gazers/) — abstém-se
    shamans/              ✅ V10  placeholder (races/mystics/prophecy/shamans/) — abstém-se
    witches/              ✅ V10  placeholder (races/mystics/prophecy/witches/) — abstém-se
    seers/                ✅ V10  placeholder (races/mystics/prophecy/seers/) — abstém-se
    oracles/              ✅ V10  placeholder (races/mystics/prophecy/oracles/) — não gera chaves por design
    bone_readers/         ✅ V10  placeholder (races/mystics/prophecy/bone_readers/) — abstém-se
    loader.py             ✅ V9   discover_factions() (compat legacy)
```

## `main.py` — sem lógica de facção

```python
context = {**ctx, 'ariadne': ariadne, 'cfg': cfg}  # cfg obrigatório
registry = FactionRegistry().discover("factions")
all_proposals = []
for faction in registry.all():
    all_proposals.extend(faction.propose(context))
```

Adicionar uma nova facção = criar `factions/<nova>/council.py` + `manifest.json`.
**Zero alterações a `main.py`.**

**Excepção documentada — Clérigos:** `main.py` ainda importa `factions.clerics.algorithm.execute()` explicitamente, uma única vez, porque o Ritual Celeste (`world/engine/celestial_energy.py`) precisa da população completa (`evo['cemiterio']`/`evo['ressuscitados']`), não apenas das propostas finais ao Conselho. Correr o algoritmo genético uma segunda vez dentro de `council()` consumiria uma fatia diferente do stream aleatório e quebraria a reprodutibilidade. O resultado é guardado em `ctx['clerics_evo']`; `factions/clerics/council.py` apenas lê esse valor — nunca recalcula. Nenhuma lógica de registo de candidatos (peso, formatação) permanece em `main.py`; isso já passa pelo loop genérico de `all_proposals`.

## Ainda fora do sistema de plugins (por design)

- **Esquadrão Negro** — estado persistente (grimório, eventos)
- **Ordem Élfica** — não vota directamente
- **Panteão** (`orders/pantheon/`) — Magos, Druidas, Djinns e Aion; chamados explicitamente por `main.py`, fora do `FactionRegistry` por design (não são facções do Conselho)
- **Cartógrafos do Caos** — analítico; chamado explicitamente via `execute_cartographers()`

## Candidatos (por priorizar — ver Roadmap)

- Entropia — medir o "caos" dos sorteios por ano (candidato a `EntropyService`, ver abaixo)
- Heatmaps — matriz visual de pares/triplas (CSV/JSON para visualização)
- Treefolks consultando os livros dos Cartógrafos directamente
- Ranking em ascensão por janela temporal
- `experiments/reports/writer.py` consumindo `Proposal` directamente (remover `_rebuild_report_factions`)

---

# Testes (`tests/`)

Suite `unittest` da stdlib (sem dependências externas — consistente com `requirements.txt`). Correr com:

```bash
python -m unittest discover -s tests
```

846 testes em 34 módulos (`tests/test_*.py`), verificado no Commit 24 (Temporal Persistent Memory).

| Ficheiro | Cobre |
|---------|------|
| `test_models.py` | `core/strategy.py` — `Proposal` (defaults, isolamento de `extra`) e `Faction` (ABC, propriedades `name`/`origin`/`home`) |
| `test_registry.py` | `core/registry.py` — `register`/`all`/`count`, `discover()` (skip de `_prefixo`, skip de não-diretórios, contagem real de 21 facções votantes, exclusão das analíticas) |
| `test_plugin_loader.py` | `core/plugin_loader.py` — `_load_manifest`, `load_faction` (ordem de resolução), `CompatFaction.propose()` para as 3 formas de retorno (lista simples, anões com `carteira`, lobisomens com `ativo`/`finalistas`) |
| `test_council.py` | `council/council.py` — `filter_candidates` (mutação de soma fora do intervalo, rejeição por baixa energia), `vote` (agregação ponderada), `corrupt` (limites válidos, preservação da chave original) |
| `test_backtesting.py` | `compare_result.py` — `titulo()` (todas as combinações), `avaliar_registo()` (pontuação, preservação de campos) |
| `test_hero_registry.py` | `library/heroes/registry.py` — persistência, deduplicação, ranking, segurança de escrita atómica, independência de ordem |
| `test_legend_registry.py` | `library/legends/registry.py` — persistência append-only, disciplina de campos congelados vs. acumulativos, verificação de integridade, reconstrução idempotente do índice |
| `test_hero_evaluation.py` | `core/services/hero_evaluation.py` — Hero Evaluation Engine, classificação determinística contra um sorteio oficial |
| `test_temporal_eligibility.py` | `core/services/hero_evaluation.py` — modelo de proveniência temporal (`verified`/`legacy`/`ineligible`/`unresolved`) |
| `test_legend_evaluation.py` | `core/services/legend_evaluation.py` — agregação determinística de promoções a Legend |
| `test_evaluate_legends_integration.py` | `evaluate_legends.py` — testes de integração do CLI real contra `config.txt`/`LegendRegistry`/`HeroRegistry` reais, redirecionados para diretórios temporários |
| `test_run_manifest.py` | `core/services/run_manifest.py` — manifesto de proveniência por execução de `main.py` |
| `test_historical_dataset.py` | `core/services/historical_dataset.py` — carregamento e validação partilhada do dataset histórico |
| `test_historical_astronomy.py` | `core/services/historical_astronomy.py` — posição Sol/Lua de baixa precisão (algoritmo de Meeus) |
| `test_historical_statistics.py` | `core/services/historical_statistics.py` — `estatisticas_chave`/`historico_no_conjunto` por sorteio |
| `test_historical_scroll.py` | `core/services/historical_scroll.py` — geração do pergaminho de um sorteio histórico |
| `test_historical_draw_generator.py` | `core/services/historical_draw_generator.py` — pipeline transacional de registo de sorteios oficiais |
| `test_register_official_draw.py` | `register_official_draw.py` — CLI de registo de sorteios oficiais (staged → validado → instalado, rollback, códigos de saída) |
| `test_dashboard_data.py` | `core/services/dashboard_data.py` — Heroes, Legends, Base de Chaves, Characters, Houses, Economy, Categorias de Prémios, Gerações, Frequências, `DashboardDataset` (inclui testes contra o dataset real de 2026 e contra `arquivo_destino.json`) |
| `test_artifact_schema.py` | `core/services/artifact_schema.py` — `normalize_artifact()`/`ArtifactRecord`, validado contra os 15 artefactos reais |
| `test_artifact_registry.py` | `core/services/artifact_registry.py` — `load_all_artifacts()`, `ArtifactRegistry`, `build_index()`/`write_index()` |
| `test_artifact_inspiration.py` | `core/services/artifact_inspiration.py` — `generate_inspiration()`, determinismo, segurança narrativa (nunca sugere números/estrelas/previsões) |
| `test_dashboard_excel_export.py` | `dashboard/excel_export.py` — construção do workbook a partir de um `DashboardDataset` já feito, sem recalcular dados; determinismo semântico, `None` nunca vira `0`, dataset vazio, Economy/Prize Categories ausentes, exportação sempre em `tempfile` |
| `test_statistical_profiles.py` | `core/services/statistical_profiles.py` — `absolute_frequency`, `relative_frequency`, `current_delay`, `parity`, `low_high`, `decade_bucket`, `key_gaps`, `repeated_values`; proteção explícita números/estrelas nunca misturados; testes contra o dataset real de 2026 |
| `test_rolling_windows.py` | `core/services/rolling_windows.py` — `last_n_draws`/`last_n_draws_on_weekday`, seleção por data (nunca por texto `dia_semana`), ordem dada preservada, composição direta com `statistical_profiles.py`, teste contra o dataset real (últimas 5 terças) |
| `test_statistical_window_profile.py` | `core/services/statistical_window_profile.py` — composição pura de `statistical_profiles.py`/`rolling_windows.py` sobre uma `RollingWindow`; padding de universo completo, alinhamento `*_by_draw`, ausência de Jaccard/hot-cold |
| `test_candidate_provenance.py` | `core/services/candidate_provenance.py` — `normalize_candidate_record()`/`CandidateKey` contra os 18 `origem` reais de `arquivo_destino.json` (fixtures sintéticas + registos reais do arquivo), `ValueError` em origem desconhecida, exclusão de campos canónicos de `metadata` |
| `test_candidate_evaluation.py` | `core/services/candidate_evaluation.py` — `evaluate_candidate`/`evaluate_candidates`, todas as 18 categorias `n+e`, números/estrelas nunca misturados, sem influência de `[HEROIS]`, alvos sempre sintéticos (nunca um sorteio real hardcoded) |
| `test_candidate_performance.py` | `core/services/candidate_performance.py` — `summarize_candidate_performance()`, diversidade por `frozenset` (chave completa vs. conjunto de números), as 18 categorias sempre presentes, ausência de `best_category`/agrupamentos nativos |
| `test_minotauros.py` | `factions/clerics/archetypes.py` (persistência via `h.keys[-1]`, nascimento fundador, ausência de `aplicar_conhecimento()`) e `factions/clerics/algorithm.py` (herança `chave_herdada` no ciclo de reprodução, precedência p1/p2, sem aliasing mutável) — ver secção própria abaixo |
| `test_backtest_lab.py` | `core/services/backtest_lab.py` (Commit 20) — `BacktestTarget`/`FrozenCandidate`, `freeze_backtest_candidates`/`evaluate_backtest_candidates`/`summarize_backtest`; assinatura de `freeze_backtest_candidates()` provada por `inspect.signature` a nunca receber a chave vencedora |
| `test_historical_simulation_source.py` | `core/services/historical_simulation_source.py` (Commit 22) — `available_at`/`load_versioned_history`/`visible_draws`/`adapt_to_legacy_draw`/`build_historical_context_for_backtest`; invariante A/B (alterar X e posteriores nunca muda a vista pré-X); integração real com `core.evolution.statistics.calculate()` |
| `test_historical_ariadne_source.py` | `core/services/historical_ariadne_source.py` + modo temporal de `library/ariadne/engine.py:Ariadne` (Commit 23) — `pergaminho_available_at`/`load_scrolls`/`visible_scrolls`/`build_scrolls_for_backtest`; prova por `mock.patch` de que os 7 métodos baseados em pergaminhos nunca tocam o disco em modo temporal; `pairs`/`triples`/`numero`/`least_frequent_numbers` levantam `RuntimeError` numa instância temporal |
| `test_temporal_memory_boundary.py` | `core/services/temporal_memory_boundary.py` (Commit 24) — `classify_memory_availability`/`temporal_memory_view`; Necromancia (`tentar_ressuscitar_lenda`) temporalmente segura via `registado_em`; prova estrutural de que Grimório/Artefactos/Ordem Élfica nunca importam este módulo |

**Filosofia:** os testes cobrem a *framework* e os serviços partilhados reais (registry, plugin_loader, council, modelos partilhados, pontuação do backtesting, pipeline histórico, Heroes/Legends, Dashboard Dataset, Dashboard Excel Export, Biblioteca dos Artefactos), não a lógica narrativa de cada facção — um refactor da arquitetura de plugins deve falhar aqui, localmente, em vez de partir silenciosamente uma facção três camadas depois. As 21 facções em `factions/*/` não têm testes dedicados; a sua "correção" é maioritariamente narrativa, não mecânica.

# Serviços partilhados (`core/services/`)

20 ficheiros, a maioria com lógica real e testada (não scaffold) — cresceu bastante desde V10.5/V11:

| Ficheiro | Estado | O que faz |
|---|---|---|
| `combinations.py` | ✅ real | `normalize_candidate`, `gaps` — migrado de `races/legacy.py` em V11 |
| `fitness.py` | ✅ real | `fitness` — pontuação do algoritmo genético |
| `atomic_io.py` | ✅ real | `atomic_write_json`/`read_json` — escrita atómica (temp + `os.replace`); usado por `library/heroes/registry.py`, `library/legends/registry.py`, `historical_draw_generator.py`, `artifact_registry.py` |
| `historical_dataset.py` | ✅ real | carregamento/validação partilhada de `datasets/historical/euromillions/**/*.json` |
| `historical_astronomy.py` | ✅ real | posição Sol/Lua de baixa precisão (Meeus) para o bloco `astronomia` de um sorteio |
| `historical_statistics.py` | ✅ real | `estatisticas_chave`/`historico_no_conjunto` de um sorteio histórico |
| `historical_scroll.py` | ✅ real | geração do pergaminho (scroll) de um sorteio histórico |
| `historical_draw_generator.py` | ✅ real | pipeline transacional de registo de novos sorteios oficiais — ver secção própria abaixo |
| `hero_evaluation.py` | ✅ real | Hero Evaluation Engine — classificação determinística contra um sorteio oficial |
| `legend_evaluation.py` | ✅ real | Legend Evaluation Engine — agregação determinística de promoções |
| `run_manifest.py` | ✅ real | manifesto de proveniência por execução de `main.py` |
| `dashboard_data.py` | ✅ real | Dashboard Dataset — ver secção V12.3 abaixo |
| `statistical_profiles.py` | ✅ real | Primitivas estatísticas partilhadas (Commit 12) — `absolute_frequency`, `relative_frequency`, `current_delay`, `parity`, `low_high`, `decade_bucket`, `key_gaps`, `repeated_values`; puras, sem I/O, números/estrelas nunca misturados |
| `rolling_windows.py` | ✅ real | Seleção de janelas temporais (Commit 13) — `last_n_draws`/`last_n_draws_on_weekday`; só seleciona/extrai, nunca calcula métricas (delega sempre a `statistical_profiles.py`); ainda sem consumidor de produção — só a sua própria suite de testes o usa |
| `statistical_window_profile.py` | ✅ real | `StatisticalWindowProfile`/`build_statistical_window_profile()` (Commit 15) — compõe `statistical_profiles.py` + `rolling_windows.py` sobre uma única `RollingWindow`; zero fórmulas novas, sem Jaccard/hot-cold (deliberadamente fora de âmbito) |
| `candidate_provenance.py` | ✅ real | `CandidateKey`/`normalize_candidate_record()` (Commit 16) — normaliza registos já persistidos em `arquivo_destino.json` para uma taxonomia fechada de `SourceType` (18 `origem` reais); nunca gera, avalia ou pontua um candidato |
| `candidate_evaluation.py` | ✅ real | `CandidateEvaluation`/`evaluate_candidate()`/`evaluate_candidates()` (Commit 17) — mede um `CandidateKey` contra um alvo explicitamente fornecido pelo chamador; puramente retrospetivo, sem noção de "concurso"/data, ver Fronteira Temporal abaixo |
| `candidate_performance.py` | ✅ real | `CandidatePerformanceSummary`/`summarize_candidate_performance()` (Commit 18) — agregação pura de pares `(CandidateKey, CandidateEvaluation)` já produzidos; sem agrupamento nativo por origem/raça/geração (decisão deliberada, ver secção própria) |
| `backtest_lab.py` | ✅ real | `BacktestTarget`/`FrozenCandidate`, `freeze_backtest_candidates`/`evaluate_backtest_candidates`/`summarize_backtest` (Commit 20) — certifica a Fronteira B (candidato existia antes da revelação do alvo); reutiliza `hero_evaluation.classify_temporal_provenance` sem alterações; ver secção própria abaixo |
| `historical_simulation_source.py` | ✅ real | `available_at`/`load_versioned_history`/`visible_draws`/`adapt_to_legacy_draw`/`build_historical_context_for_backtest` (Commit 22) — ponte entre `datasets/historical/euromillions/` e a forma legada que `world/engine/builder.py`/`core/evolution/statistics.py` esperam; ainda não ligado a `main.py`; ver secção própria abaixo |
| `historical_ariadne_source.py` | ✅ real | `pergaminho_available_at`/`load_scrolls`/`visible_scrolls`/`build_scrolls_for_backtest` (Commit 23) — equivalente do anterior para `library/scrolls/`, alimenta `Ariadne(scrolls=...)`; ver secção própria abaixo |
| `temporal_memory_boundary.py` | ✅ real | `classify_memory_availability`/`temporal_memory_view` (Commit 24) — mesma taxonomia `verified`/`legacy`/`ineligible`/`unresolved`, resolvida a partir de um campo de timestamp já no próprio registo; ver secção própria abaixo |
| `artifact_schema.py`, `artifact_registry.py`, `artifact_inspiration.py` | ✅ real | Biblioteca dos Artefactos — ver secção própria abaixo |

Nenhum destes substitui ainda a lógica estatística por-facção (frequências, quentes/frios, atraso, pares/triplas) — continua duplicada em vários pontos:

| Duplicação encontrada | Onde |
|---|---|
| Contagem de frequências (`Counter` sobre sorteios) | `core/evolution/statistics.py`, `factions/chaos_cartographers/{trends,randomness,cycles}.py`, `factions/axiomantes/profile.py` |
| Quentes/frios | `core/evolution/statistics.py` vs `factions/chaos_cartographers/trends.py` vs `Ariadne.least_frequent_numbers()` — 3 fontes de verdade inconsistentes |
| Atraso/"overdue" | `Ariadne.overdue_numbers()` (só pergaminhos 2026) vs `core/evolution/statistics.py` (histórico completo) vs `factions/chaos_cartographers/cycles.py` (mais detalhado: médio/máx/mín/variância) |
| Gaps intra-chave | `core/services/combinations.py:gaps` ✅ já centralizado (V11); ainda recomputado independentemente em `factions/chaos_cartographers/trends.py`, `factions/axiomantes/profile.py` |
| Pares/triplas | `Ariadne.pairs()/triples()` vs recomputação em `factions/chaos_cartographers/constellations.py` e `markov.py`; `factions/vampires/algorithm.py` e `factions/gargoyles/algorithm.py` leem `library/indexes/*.json` diretamente em vez de usar `Ariadne` |
| Baixos/altos, pares/ímpares | `factions/chaos_cartographers/{trends,randomness}.py`, `factions/axiomantes/profile.py` |

Serviços previstos (nomes indicativos): as capacidades inicialmente previstas sob os nomes indicativos `StatisticsService`/`DelayService` começaram a ser implementadas nos Commits 12-13 através de `statistical_profiles.py`/`rolling_windows.py` — esses nomes indicativos nunca chegaram a ser criados como serviços/classes concretos, e `statistical_profiles.py`/`rolling_windows.py` **não substituem** a lógica duplicada por-facção listada acima, coexistem deliberadamente com ela. O Commit 15 (`statistical_window_profile.py`) compôs estas duas primitivas numa única `StatisticalWindowProfile` por janela — continua sem substituir a duplicação por-facção nem introduzir fórmulas novas (Jaccard/hot-cold ficam deliberadamente fora). `PairService`, `TripleService`, `EntropyService`, `TrendService` continuam **sem nenhuma implementação** — sem fonte de dados fresca (`library/indexes/duplas.json`/`triplas.json` obsoletos) ou sem definição canónica (entropia, tendências). Migração da lógica por-facção fica para depois — **não implementar já**.

## Known Issues / Dívida Técnica

- **`library/ariadne/engine.py` — leitura ambígua de `saidas_de_bolas_normalizado.json`** (achado do Commit 11, não corrigido): este índice mistura números (1-50) e estrelas (1-12) na mesma lista, reaproveitando a chave `"numero"` sem nenhum campo `"tipo"` a distinguir — só a posição (índice <50 vs ≥50) permite separar. Isto provoca comportamento ambíguo/incorreto em dois métodos:
  - `Ariadne.numero(n)` — o `for...return` para no primeiro match; para `n` ≤ 12 devolve sempre a entrada de **número**, nunca a de estrela (inatingível).
  - `Ariadne.least_frequent_numbers()` — ordena a lista inteira por `aparicoes_totais`, incluindo as estrelas misturadas como se fossem números.
- **`library/indexes/frequencias_numeros.json`/`frequencias_estrelas.json`** — órfãos (nenhum código do projeto os lê) e obsoletos (a soma das frequências implica só 55 sorteios indexados — não bate nem com "2026 sozinho" (64) nem com o histórico completo; `git log` confirma que não são tocados desde a reorganização V10).
- `core/services/dashboard_data.py:build_frequencies_rows()` (Commit 11) não depende de nenhum destes três ficheiros — conta diretamente sobre `draw_records` já carregados pelo chamador, evitando tanto a ambiguidade como a obsolescência.
- **`VERSION` desalinhado**: o ficheiro `VERSION` na raiz contém `"V12"`, mas este documento (e o `README.md`) já descrevem funcionalidade pós-V13 como completa. Registado como achado; não corrigido — fora do âmbito destes commits.
- **Bifurcação de fonte de dados histórica** (achado do Commit 21, não corrigido): `main.py`/`world/engine/builder.py` nunca leem `datasets/historical/euromillions/` — usam `core/data/loaders.py:get_history()` (API ao vivo por omissão, ou `datasets/generated/temporary/historico_cache.json`), uma fonte completamente independente da usada por `historical_dataset.py`/Dashboard/Hero Evaluation/Backtest Lab. `core/services/historical_simulation_source.py` (Commit 22) já liga a fonte versionada a um cutoff, mas não está ligado a `main.py`/`builder.py`.
- **Footgun em `world/engine/builder.py`** (achado do Commit 21, não corrigido): `if not visivel: visivel = hist` desativa silenciosamente o corte temporal quando a data configurada não produz nenhum sorteio visível, revertendo para o histórico completo sem aviso — um risco real de look-ahead, priorizado mas não corrigido.
- **Ariadne — métodos baseados em `library/indexes/*.json`** (`pairs`/`triples`/`numero`/`least_frequent_numbers`): sem qualquer timestamp nos ficheiros de origem; permanecem não certificáveis mesmo numa instância `Ariadne(scrolls=...)` (Commit 23) — levantam `RuntimeError` em vez de responder sem corte temporal.
- **Grimório do Esquadrão Negro / `estado_ordem.json` da Ordem Élfica** (achado do Commit 21/24, não corrigido): estado agregado, cumulativo, sem qualquer timestamp a qualquer nível — impossível de certificar temporalmente sem reescrever o esquema de persistência.

# Benchmarks (`benchmarks/` e `experiments/benchmarks/`)

Estrutura só, sem runner. `benchmarks/random/` (baseline aleatório), `benchmarks/reports/` (relatórios legíveis), `benchmarks/rankings/` (leaderboards em JSON). `experiments/benchmarks/` é para sessões de investigação ad-hoc, distinto do `benchmarks/` de topo (resultados duradouros/canónicos). Nenhum destes gera conteúdo automaticamente hoje.

---

# Princípios

- As fontes históricas originais são imutáveis (`datasets/historical/euromillions/`).
- Pergaminhos são vistas (`library/scrolls/`).
- Livros são reconstruíveis (`library/books/`).
- Consultas funcionam como cache (`library/cache/`).
- Todo o conhecimento passa por Ariadne (`library/ariadne/engine.py`).
- O projeto é um simulador estatístico e narrativo; os padrões históricos não aumentam a probabilidade matemática de prever um sorteio futuro.

---

# Roadmap

## V10.5 — Architecture Complete

- ✅ `races/` tree is lore-only except `races/legacy.py` (Clerics — deferred by design, see audit)
- ✅ Every faction algorithm lives under `factions/<name>/` (`algorithm.py`, `representatives.py`, or `council.py`-inline)
- ✅ Pantheon consolidated into `orders/pantheon/` (Magos, Druidas, Djinns, Aion) — not fragmented into standalone faction plugins
- ✅ `core/services/combinations.py` (`normalize_candidate`) and `core/services/fitness.py` (`fitness`) — first real shared services, `ctx['rng']`-based
- ✅ Full test suite (54 tests), `compileall`, `FactionRegistry` discovery (19 voting factions), `main.py`, `simulate_v7.py`, `compare_result.py` all green
- ✅ `races/legacy.py` audited — dependency graph + target architecture produced (no code moved)
- ✅ `docs/lore/` canon bible (10 files) + lore for all 20 races complete
- ✅ Commit + tag `v10.5`, `v10.5-lore-complete`

## V11 — Clerics migration (complete) + New Factions (not started)

- ✅ Migração dos Clérigos: `races/legacy.py` + `core/evolution/genetic.py` → `factions/clerics/` (`algorithm.py`, `archetypes.py`, `council.py`, `strategy.py`, `manifest.json`); `races/clerics/` lore package
- ✅ `races/legacy.py` removed — `races/` is now **fully lore-only** (no exceptions)
- ✅ `gaps()` moved from `races/legacy.py` into `core/services/combinations.py`, fixing the inverted `core/` → `races/` dependency in `core/services/fitness.py`
- ✅ All 13 external callers of the old `normalize()` repointed to `core.services.combinations.normalize_candidate(nums, ests, random)` — same global-random behaviour, single source of truth
- ✅ Clerics auto-discovered by `FactionRegistry` (21 voting factions, up from 20) — verified via direct `load_faction()` probe, not just the registry count
- ✅ Deterministic before/after comparison: population, cemetery, resurrected heroes, per-generation summary, and the isolated Council-proposal shape are byte-identical between the pre- and post-migration engine, and the ending `random.getstate()` matches exactly — proof of zero additional random draws
- Known, documented side effect: Clerics finalists now flow through the generic "all plugin factions" loop in `main.py` instead of a hardcoded early-position block, so they're interleaved alphabetically with other factions in the final candidate list (previously they held a fixed early slot) — this changes tie-breaking in `council/council.py::vote()` and mutation order in `filter_candidates()`, so the *final Council-selected key* for a full `main.py` run can differ from before, even though the Clerics algorithm itself is unchanged. Also, Clerics finalists are now registered in the external chronicle (`externos`/`registo_externo`) for the first time, consistent with every other faction — previously they were the only voting faction excluded from that registration.
- Completar o lore das 20 raças — ✅ done in V10.5
- Novas facções: Juízes do Conselho, Geómetras do Véu, Estatísticos Imperiais
- `dashboard/` — visualização e análise
- Rng retrofit decision: estender `ctx['rng']` a todas as facções (hoje só Panteão + Skeletons + Chronomancers), ou manter `random` global nas restantes — Clerics migration deliberately kept global `random` to guarantee determinism (see above)

## V12.3 — Dashboard Dataset (complete)

- ✅ `core/services/dashboard_data.py` — camada pura de montagem de dados (Commits 1-14, ver secção própria abaixo): Heroes, Legends, Base de Chaves, Characters, Houses, Executive Summary, Economy, Categorias de Prémios, Gerações, Frequências
- ✅ `library/heroes/` + `library/legends/` — registries persistentes, mais `hero_evaluation.py`/`legend_evaluation.py` e os CLIs `evaluate_heroes.py`/`evaluate_legends.py`
- ✅ Pipeline de registo de sorteios oficiais — `historical_draw_generator.py` + `register_official_draw.py` (ver secção própria abaixo)
- ✅ `dashboard/excel_export.py` — exportação Excel do `DashboardDataset` (Commit 9, ver secção própria abaixo)
- ✅ `core/services/statistical_profiles.py` + `rolling_windows.py` — primitivas estatísticas partilhadas e seleção de janelas temporais (Commits 12-13); infraestrutura pura, **não geram chaves nem são estratégia preditiva** — só reshape/contagem/seleção sobre dados já carregados
- ✅ `FrequenciesRow.atraso_atual` preenchido via `current_delay()` (Commit 14) — `0` no sorteio mais recente, `N` sorteios atrás, `None` se nunca observado ou input vazio; exige `draw_records` cronologicamente ordenado (mais antigo → mais recente), sem validação de datas interna
- Ainda por fazer: nenhum script monta um `DashboardDataset` real a partir de Heroes/Legends/datasets/races ao vivo e chama o exportador; `jaccard_medio_vs_geracao_anterior` (`GenerationRow`) continua `None` — sem definição canónica ainda; `fitness_medio/maximo/minimo` (`GenerationRow`) continuam `None` — estruturalmente irrecuperáveis; `rolling_windows.py` ainda sem consumidor de produção — ver Próximo Passo na secção V12.3 abaixo

## V13 — Biblioteca dos Artefactos (complete)

- ✅ `core/services/artifact_schema.py` + `artifact_registry.py` + `artifact_inspiration.py` — ver secção própria abaixo
- ✅ 15 artefactos narrativos fundadores em `library/artifacts/entries/`, todos com `altera_algoritmo`/`altera_resultados`/`altera_probabilidades` explicitamente `false`
- ✅ `library/artifacts/LIVRO_DOS_ARTEFACTOS.json` — índice sempre derivado de `entries/`, nunca fonte de verdade

## Commits 15–19 — Camada de Proveniência/Avaliação/Desempenho de Candidatos & Minotauros (complete)

- ✅ `core/services/statistical_window_profile.py` — `StatisticalWindowProfile` (Commit 15), composição pura de `statistical_profiles.py`/`rolling_windows.py`
- ✅ `core/services/candidate_provenance.py` — `CandidateKey`/`normalize_candidate_record()` (Commit 16), taxonomia fechada dos 18 `origem` reais
- ✅ `core/services/candidate_evaluation.py` — `evaluate_candidate`/`evaluate_candidates` (Commit 17), estritamente retrospetivo — ver Fronteira Temporal abaixo
- ✅ `core/services/candidate_performance.py` — `summarize_candidate_performance()` (Commit 18), agregação pura sem agrupamento nativo
- ✅ Minotauro — nova raça de Clérigos com persistência de chave (Commit 19, `77b69b9`) — ver secção própria abaixo
- Nenhum destes substitui a lógica per-facção duplicada listada na tabela "Duplicação encontrada"; `candidate_evaluation.py`/`candidate_performance.py` não têm ainda nenhum consumidor de produção — só as suas próprias suites de teste os usam
- Ver secção "Camada de Proveniência, Avaliação e Desempenho de Candidatos (Commits 15–19)" no final deste documento para o detalhe completo, incluindo a Fronteira Temporal e a especificação do Minotauro

## Commits 20–24 — Backtest Lab & Fronteira Temporal (complete)

- ✅ `core/services/backtest_lab.py` — `freeze_backtest_candidates`/`evaluate_backtest_candidates`/`summarize_backtest` (Commit 20), certifica a Fronteira B
- ✅ Commit 21 — auditoria completa (sem alterações de código) que identificou a Fronteira A como o problema estrutural maior: `main.py` nunca lê `datasets/historical/euromillions/`, Ariadne lê `library/scrolls/`/`library/indexes/` sem cutoff, e memória persistente (Grimório/Lendas/Artefactos/Ordem Élfica) sem proveniência temporal
- ✅ `core/services/historical_simulation_source.py` — cutoff timezone-aware sobre o dataset versionado (Commit 22), ainda não ligado a `main.py`/`world/engine/builder.py`
- ✅ `library/ariadne/engine.py` ganhou um modo temporal explícito (`Ariadne(scrolls=...)`, Commit 23) para os métodos baseados em pergaminhos; métodos baseados em índices continuam não certificáveis, por design
- ✅ `core/services/temporal_memory_boundary.py` (Commit 24) — mesma taxonomia `verified`/`legacy`/`ineligible`/`unresolved`; Necromancia legada (`docs/lore/legends/livro_personagens_lendarias.json`) passa a poder ser temporalmente cortada via `registado_em`; `recognized_at`/`promoted_at` passam a ser persistidos em novos Heroes/Legends (forward-only, sem retrodatar registos antigos)
- Continua por fazer: nenhuma destas peças está ligada a `main.py`/a um orquestrador de backtest real; Grimório, `estado_ordem.json` e o replay temporal de Artefactos continuam sem certificação possível — ver secção "Fronteira Temporal" no final deste documento

# Dependências opcionais

## Dashboard (`dashboard/excel_export.py`)

`dashboard/excel_export.py` (Commit 9) exporta um `DashboardDataset` já
construído (produzido por `core/services/dashboard_data.py`, ver V12.3
abaixo) para `.xlsx`, usando `openpyxl`, que não é uma dependência
obrigatória do núcleo do projeto (ver `requirements.txt`). Instalar
apenas quando for necessário gerar o workbook de investigação:

```bash
pip install -r requirements-dashboard.txt
```

# Dashboard V12.3 – Estado Atual

## Progresso

Commit 1
- requirements-dashboard.txt
- documentação inicial do Dashboard

Commit 2
- criação de core/services/dashboard_data.py
- dataclasses base
- build_heroes_rows()
- build_legends_rows()
- testes
- 202/202 OK

Commit 3
- build_key_base_rows()
- build_characters_rows()
- filtro por calendario.ano
- testes ampliados
- 217/217 OK

Commit 4
- build_houses()
- _normalize_individual_record() / _normalize_archive() — normalização genérica de registos de população, nunca levanta exceção
- cruzamento de casas declaradas (races/*/lineages.json) vs. casas observadas na população
- testes ampliados

Commit 5
- build_executive_summary()
- build_dashboard_dataset()
- economia resolvida uma única vez e partilhada, byte-a-byte, entre ExecutiveSummary.economia e DashboardDataset.economy
- testes ampliados

Commit 6
- suporte a aliases name/generation, com regras de precedência explícitas (canónico ganha mesmo se vazio; alias só é consultado se a chave canónica estiver totalmente ausente)
- validate_historical_dataset() extraído para core/services/historical_dataset.py, sem alterar os testes existentes além da linha de import
- testes ampliados

Commit 7 — Economy
- EconomyDrawRow, EconomySummary — estruturas novas e aditivas, nunca alteram EconomyPlaceholder/economia/economy
- build_economy_rows(), build_economy_summary()
- dados financeiros reais de 2026: 15 de 61 sorteios têm estatisticas_financeiras/premios completos, confirmado por qualidade_dados.dados_financeiros_disponiveis — nunca inferido a partir de um valor ser ou não None
- soma/média/mínimo/máximo ignoram None; um campo sem observação real resolve para None, nunca 0 ou uma estimativa
- percentagem_sorteios_com_vencedor_1_premio_total usa como denominador só os sorteios em que a flag não é None (nunca o total de sorteios — None não é False)
- 478/478 OK

Commit 8 — Categorias de Prémios
- PrizeCategoryRow, PrizeCategoryAggregate, PrizeCategorySummary — estruturas novas e aditivas
- build_prize_category_rows(), build_prize_category_summary()
- _PRIZE_CATEGORY_LABELS — tabela oficial fixa dos 13 escalões de prémio do Euromilhões (regra do jogo, não facto por sorteio), validada nos testes contra os 15 sorteios reais com dado
- exatamente 13 linhas por sorteio, sempre; só os campos variáveis (vencedores_portugal/vencedores_total/percentagem_portugal_no_total) ficam None quando o sorteio não tem premios.categorias real
- categorias_disponiveis vem sempre de qualidade_dados.categorias_premio_disponiveis, nunca inferido
- 500/500 OK

Commit 9 — Excel Export
- dashboard/__init__.py, dashboard/excel_export.py
- build_workbook() (puro, em memória, nunca toca em disco) + export_to_excel() (único ponto de escrita)
- 8 folhas: Executive Summary, Heroes, Legends, Characters, Houses, Key Base, Economy, Prize Categories — cada uma lida apenas dos campos correspondentes do DashboardDataset já construído, nunca recalculada
- Economy/Prize Categories usam exclusivamente economy_draws/economy_summary e prize_category_rows/prize_category_summary
- None nunca vira 0/False; tuplos formatados como string só para exibição, nunca reordenados
- project_version/generated_at injetados verbatim pelo chamador — nunca lidos de VERSION nem de datetime.now() dentro do exportador
- Validação funcional adicional contra o DashboardDataset real do projeto (Heroes/Legends/sorteios/Characters/Houses/Economy/Prize Categories reais), workbook reaberto com openpyxl e comparado campo a campo — sem freeze panes/autofilter/number_format custom (âmbito mínimo deliberado)
- 523/523 OK

Commit 10 — Generation Rows
- build_generations_rows() — agrupa por geracao um conjunto de registos já pertencentes a uma única execução coerente, fornecido pelo chamador; nunca decidido aqui
- chaves_unicas/cobertura_numeros/cobertura_estrelas/taxa_diversidade — contagens/rácio sobre numeros/estrelas, que a fonte real (arquivo_destino.json) garante estarem sempre pré-ordenados ascendentemente (verificado: 42527/42527 registos)
- fitness_medio/fitness_maximo/fitness_minimo: sempre None — a fonte real nunca persistiu o score (pontos) por indivíduo, estruturalmente irrecuperável
- jaccard_medio_vs_geracao_anterior: sempre None — o campo existe no contrato, mas a definição estatística canónica fica deliberadamente por decidir nos futuros serviços estatísticos partilhados
- Achado documentado (não corrigido): arquivo_destino.json não tem run_id em nenhum registo real ainda, e mistura dezenas de execuções distintas de main.py sob os mesmos valores de geracao — build_generations_rows() nunca lê esse ficheiro diretamente nem agrupa por geracao sozinho
- 536/536 OK

Commit 11 — Frequencies Rows
- build_frequencies_rows() — conta ocorrências de números (1-50) e estrelas (1-12) sobre draw_records já carregados (o mesmo `sorteios` que os outros builders de sorteios recebem); sem filtro de ano interno — histórico completo vs. um subconjunto é decisão exclusiva do chamador
- Emite sempre 62 rows (regra fixa do jogo, mesmo espírito de _PRIZE_CATEGORY_LABELS); valores nunca vistos ficam com frequencia_absoluta=0/frequencia_relativa=0.0, nunca omitidos
- frequencia_relativa no intervalo [0,1]
- atraso_atual: sempre None — depende de um "agora" ordenado no tempo (rolling window), deliberadamente adiado
- Achado documentado (não corrigido): frequencias_numeros.json/frequencias_estrelas.json órfãos e obsoletos; saidas_de_bolas_normalizado.json atualizado mas mistura números e estrelas sem campo "tipo" — build_frequencies_rows() ignora os três, conta direto sobre sorteios
- 547/547 OK

Commit 12 — Shared Statistical Primitives
- core/services/statistical_profiles.py — absolute_frequency, relative_frequency, current_delay, parity, low_high, decade_bucket, key_gaps, repeated_values
- Todas puras, sem I/O, sem random; operam sobre Sequence[int] já extraído pelo chamador — nenhuma função conhece os universos 1-50/1-12, nunca mistura números e estrelas
- current_delay(): 0 se o valor está no elemento mais recente, N sorteios atrás, None se nunca aparece (incl. sequência vazia) — semântica canónica decidida explicitamente (não len(occurrences) como limite inferior)
- key_gaps() generaliza combinations.gaps() (hardcoded a 5 valores) para qualquer tamanho, incl. estrelas (2)
- Não substitui nenhuma lógica existente em facções/Ariadne/core/evolution — coexistem deliberadamente
- 588/588 OK

Commit 13 — Rolling Window Selection
- core/services/rolling_windows.py — RollingWindow (dataclass), last_n_draws(), last_n_draws_on_weekday()
- Só seleciona/extrai sorteios — nunca calcula métricas; quem consome uma RollingWindow chama statistical_profiles.py diretamente sobre numero_occurrences/estrela_occurrences
- Terça/sexta determinadas exclusivamente por date.fromisoformat(draw["data"]).weekday() (TUESDAY=1, FRIDAY=4) — nunca pelo campo de texto dia_semana; verificado ao vivo contra o dataset real (0 mismatches, mas a robustez vem de nunca depender do texto)
- Confia inteiramente na ordem dada pelo chamador — nunca reordena, nunca valida datas
- n <= 0 ou input vazio -> janela vazia; menos sorteios que requested_size é permitido e fica visível via actual_size; weekday fora de 0-6 -> ValueError
- 608/608 OK

Commit 14 — Frequencies Delay
- build_frequencies_rows() (dashboard_data.py) passa a preencher atraso_atual via current_delay() do Commit 12 — primeira vez que dashboard_data.py importa de statistical_profiles.py
- frequencia_absoluta/frequencia_relativa mantidas exatamente como estavam (Counter manual, sem refactor) — o diff funcional é atribuível só a atraso_atual
- Mudança de contrato documentada: draw_records tem agora de estar cronologicamente ordenado para atraso_atual ser correto; frequencia_absoluta/relativa continuam order-agnostic
- jaccard_medio_vs_geracao_anterior (GenerationRow) continua None — Commits 12/13 não definiram Jaccard, decisão inalterada
- 614/614 OK

## Decisões Arquiteturais

- dashboard_data.py é exclusivamente uma camada de transformação.
- Nunca lê ficheiros.
- Nunca acede diretamente aos Registry.
- Recebe apenas dados já carregados pelo chamador.
- Dataclasses são frozen.
- Coleções expostas como tuples.
- Base de Chaves limitada aos sorteios oficiais de 2026.
- O filtro utiliza calendario.ano como fonte de verdade.
- build_characters_rows utiliza apenas o contrato comum validado dos characters.json.
- Campos opcionais são lidos com .get().
- Economy (Commit 7) e Categorias de Prémios (Commit 8) usam dados reais do dataset de 2026, nunca sintéticos — qualidade_dados é sempre a fonte de verdade sobre "há dado real", nunca inferida a partir de um valor estar ou não a None.
- economy_draws/economy_summary/prize_category_rows/prize_category_summary são campos aditivos em DashboardDataset (default ()/None) — nunca alteram economy/economia (EconomyPlaceholder), que se mantém inalterado, apenas complementado.
- Exploration vs Exploitation permanece adiado.
- A normalização continua privada dentro de dashboard_data.py até existir necessidade real de extração.
- dashboard/excel_export.py só lê o DashboardDataset já construído — nunca Heroes/Legends/datasets/registries diretamente; só toca em disco em export_to_excel(), nunca em build_workbook().
- build_generations_rows()/build_frequencies_rows() seguem a mesma disciplina de build_key_base_rows: o âmbito (que execução, que sorteios) é sempre decidido pelo chamador, nunca inferido nem reconstruído a partir de registos legacy sem run_id.
- Campos sem fonte real honesta ficam sempre None, nunca recalculados com o estado atual do projeto: fitness_medio/maximo/minimo e jaccard_medio_vs_geracao_anterior (GenerationRow). atraso_atual (FrequenciesRow) deixou de estar nesta lista desde o Commit 14 — tem fonte honesta (current_delay() sobre draw_records já ordenado pelo chamador).
- statistical_profiles.py/rolling_windows.py: primitivas puras, sem I/O, sem random, sem leitura de library/indexes/ — nunca conhecem os universos 1-50/1-12 nem misturam números/estrelas; ordem temporal é sempre responsabilidade do chamador, nunca validada internamente.

## Fluxo de Trabalho

- Um commit por objetivo.
- Não aumentar o âmbito de um commit.
- Mostrar sempre o diff completo.
- Executar testes específicos.
- Executar a suite completa.
- Nunca executar git commit sem aprovação explícita.
- Nunca executar git push sem pedido explícito.

## Próximo Passo

Commits 1–14 concluídos — Dashboard Dataset completo (incl. atraso_atual real), Excel Export, e a primeira camada de serviços estatísticos partilhados (statistical_profiles.py, rolling_windows.py), 614/614 OK. Sem objetivo de Commit 15 definido ainda; candidatos em aberto (ver também Roadmap):

- Definição estatística canónica de `jaccard_medio_vs_geracao_anterior` (`GenerationRow`) — ainda por decidir; `atraso_atual` já resolvido no Commit 14.
- `rolling_windows.py` ainda sem nenhum consumidor de produção — nada em `DashboardDataset` tem hoje um campo "janelado" para preencher.
- CLI/script de wiring que monta um `DashboardDataset` real a partir de Heroes/Legends/datasets/races/economy/prize categories ao vivo e chama `export_to_excel()` — hoje só a suite de testes e uma validação manual ad-hoc constroem um dataset real; não há nenhum ponto de entrada do projeto que o faça.
- Categorias de prémio detalhadas por linha (breakdown dos 13 escalões por sorteio — hoje só agregado por categoria) — candidato natural de âmbito único.
- Folha "Generations"/"Frequencies" no Excel Export — `dataset.generations`/`dataset.frequencies` já podem ter dados reais desde os Commits 10/11, mas `excel_export.py` ainda só cobre as 8 folhas do Commit 9.

---

# Biblioteca dos Artefactos (V13)

Coleção puramente narrativa e cerimonial em `library/artifacts/`, distinta do sistema mais antigo `artifacts/` (`ark.py`/`living.py`/`relics/`/`amulets/`, V4, mecanicamente ligado ao estado da simulação). Nunca influencia uma chave, um voto ou uma probabilidade.

## Fonte de verdade

- `library/artifacts/entries/*.json` — 15 artefactos fundadores, única fonte primária. Nunca reescritos por código desta camada.
- `library/artifacts/LIVRO_DOS_ARTEFACTOS.json` — sempre derivado de `entries/` via `build_index()`/`write_index()`; nunca editado à mão, nunca fonte de verdade.

## `core/services/artifact_schema.py`

- `normalize_artifact(raw) -> ArtifactRecord` — núcleo fixo pequeno (id, nome, tipo, raridade, estado, criador, universo_origem, energia_acumulada, vezes_encontrado, execucoes_sobrevividas, efeitos, lore, historia, tags) + `extras` (todo o campo não-núcleo, verbatim) + `raw` (dict original intacto).
- Nunca inventa um default semântico para um campo ausente — ausente é sempre `None`; só defaults neutros de contagem são aceitáveis (`energia_acumulada=0.0`, `vezes_encontrado=0`, `execucoes_sobrevividas=0`, `tags=()`, `historia=()`).
- `validate_artifact_record(record) -> list[str]` — nunca levanta exceção; verifica `altera_algoritmo`/`altera_resultados`/`altera_probabilidades` (em `efeitos` ou em `extras["principios_narrativos"]`).

## `core/services/artifact_registry.py`

- `load_all_artifacts(entries_dir) -> list[ArtifactRecord]` — deteta id duplicado (verificado antes do mismatch de nome de ficheiro, para que ambos os erros sejam realmente alcançáveis) e desalinhamento nome-de-ficheiro/id; ordem determinística por id.
- `ArtifactRegistry` — `by_id`/`by_type`/`by_tag` (case-insensitive)/`by_creator` (id ou nome); rejeita ids duplicados na construção (nunca sobrescreve silenciosamente); sem `random()` em lado nenhum.
- `build_index(records) -> dict` — todos os agregados (`por_tipo`, `por_raridade`, `por_estado`, `por_criador`, `por_universo`, `por_tag`) ordenados deterministicamente; rankings com tie-break explícito por id; `atualizado_em` é o único campo não-determinístico, por design.
- `write_index(index, path) -> None` — usa `atomic_write_json` (já cria diretórios pai).

## `core/services/artifact_inspiration.py`

- `generate_inspiration(record, seed) -> dict` — gerador narrativo determinístico ("semente de inspiração") para um NOVO conceito de personagem, livremente inspirado num artefacto.
- `random.Random(seed)` sempre; nunca o `random` global. Mesmo `(record, seed)` → mesmo resultado; seeds diferentes podem variar.
- Extrai apenas de campos já existentes no `ArtifactRecord` (nome, tipo, raridade, estado, criador, efeitos, lore, historia, tags, extras) — nunca inventa poderes mecânicos.
- Filtro de segurança ativo (não só documentado): bloqueia qualquer frase com dígitos ou com algoritmo/probabilidade/resultado/previsão/prever/profecia/número(s) antes de chegar ao resultado; `artifact_id` fica fora do filtro (é um identificador, não conteúdo narrativo).
- Nunca cria/altera um Hero ou uma Legend; sem I/O de ficheiros; nunca escreve em `library/heroes/`, `library/legends/`, `datasets/`, `library/scrolls/`.

## Testes

`tests/test_artifact_schema.py` (32), `tests/test_artifact_registry.py` (31), `tests/test_artifact_inspiration.py` (23) — os 3 juntos cobrem os 15 artefactos reais, casos de erro (JSON inválido, id duplicado, mismatch de nome), determinismo, e ausência de qualquer termo proibido em centenas de combinações (artefacto × seed).

---

# Pipeline de Registo de Sorteios Oficiais (V12.3/V13)

`register_official_draw.py` — CLI transacional único para registar um ou mais sorteios oficiais no dataset histórico canónico, generalizando o fluxo validado manualmente para os sorteios 059-061/2026.

## Módulos

- `core/services/historical_astronomy.py` — posição Sol/Lua de baixa precisão (Meeus), preenche o bloco `astronomia`.
- `core/services/historical_statistics.py` — `estatisticas_chave` e `historico_no_conjunto` (atraso, frequência acumulada) de um sorteio.
- `core/services/historical_scroll.py` — gera o pergaminho (scroll) correspondente.
- `core/services/historical_draw_generator.py` — orquestra tudo o que precede + atualização dos metadados de topo do dataset (`intervalo.primeiro_sorteio`/`ultimo_sorteio`, etc.).
- `core/services/historical_dataset.py` — `validate_historical_dataset()`, partilhado com a suite de testes.

## Fluxo transacional

1. Staging — os novos sorteios são construídos e validados fora do repositório (`tempfile.mkdtemp()`).
2. Testes correm antes de qualquer avaliação de Heroes/Legends.
3. Instalação — criar-novo-depois-apagar-antigo (nunca sobrescrever-depois-renomear); rollback limitado a dataset + pergaminhos (Opção A) se algo falhar a meio.
4. Escrita sempre via `atomic_write_json` (`core/services/atomic_io.py`).
5. Idempotência verificada — re-registar o mesmo sorteio não duplica nem corrompe o dataset.

## Códigos de saída

`0` — sucesso · `1`–`4` — falhas em diferentes fases do pipeline (validação, staging, testes, instalação).

## Testes

`tests/test_historical_astronomy.py` (8), `tests/test_historical_dataset.py` (23), `tests/test_historical_scroll.py` (5), `tests/test_historical_statistics.py` (12), `tests/test_historical_draw_generator.py` (30), `tests/test_register_official_draw.py` (16).

---

# Camada de Proveniência, Avaliação e Desempenho de Candidatos (Commits 15–19)

Cinco commits sequenciais, distintos do Dashboard Dataset (V12.3) e da Biblioteca dos Artefactos (V13) — não pertencem a nenhuma das duas iniciativas, por isso ficam documentados nesta secção própria. Nenhum introduz uma nova versão formal do projeto (ver "VERSION desalinhado" em Known Issues — deliberadamente não agravado aqui com mais um número de versão inventado).

## Commit 15 — Statistical Window Profiles

`core/services/statistical_window_profile.py` — `StatisticalWindowProfile` (dataclass frozen, 14 campos, `Mapping` sempre `MappingProxyType`) + `build_statistical_window_profile(window)`. Compõe exclusivamente `statistical_profiles.py` (Commit 12) e `rolling_windows.py` (Commit 13) sobre uma única `RollingWindow` já selecionada pelo chamador — zero fórmulas novas, zero I/O, zero random. Jaccard e classificação hot/cold ficam deliberadamente fora de âmbito (sem definição canónica ainda). `numero_delays`/`estrela_delays` são sempre relativos à janela em causa ("0" = apareceu no sorteio mais recente *da janela*), nunca ao histórico completo do projeto — uma noção diferente e não relacionada com `atraso_atual` (`dashboard_data.py`, Commit 14).

## Commit 16 — Candidate Provenance Inventory

`core/services/candidate_provenance.py` — `CandidateKey` (frozen) + `normalize_candidate_record(record)`. Normaliza um registo já persistido em `arquivo_destino.json` para uma taxonomia fechada de `SourceType` (`Literal["evolutionary_individual", "external_generator", "aggregator", "transformer", "configured_candidate"]`), cobrindo os 18 valores reais de `origem` confirmados contra o arquivo real durante a auditoria do Commit 16:

| `source_type` | `origem` |
|---|---|
| `evolutionary_individual` | `racas_antigas` (Clérigos — único com `generation`/`entity_id`/`race` reais) |
| `external_generator` | `cla_anao`, `fada`, `melfork`, `treefolk`, `cronomante`, `esqueleto`, `vampiro`, `gargula`, `kors_elarion`, `axiomantes_nemerion`, `esquadrao_negro`, `ser_superior` |
| `aggregator` | `chave_conselho`, `deus` |
| `transformer` | `corrupcao_final`, `necromancia_estatistica` |
| `configured_candidate` | `ritual_celeste` |

Um `origem` fora desta tabela levanta `ValueError` — nunca é adivinhado. `metadata` nunca contém um campo canónico (`origem`/`numeros`/`estrelas`/`geracao`/`id`/`nome`/`classe`), mesmo quando esse campo não é promovido a atributo próprio — nomeadamente `classe` nunca aparece em `metadata` para nenhum `source_type`, mesmo fora de `racas_antigas`. Não existe `candidate_id`/`derived_from` — nenhuma fonte no arquivo real fornece honestamente um id estável ou uma ligação persistida a um progenitor (`registo_externo()` não tem parâmetro `id` próprio).

**Achado relevante para o Commit 19**: `necromancia_estatistica` já é o mecanismo de ressurreição de Lendas do próprio `main.py` (`eco_ressuscitado`, casa "Ritual Negro", campos `corrupcao`/`ressuscitado_por`) — classificado `transformer`. Qualquer conceito futuro de "Necromante" tem de ser auditado contra isto primeiro (ver Roadmap desta secção).

## Commit 17 — Candidate Evaluation (e a fronteira temporal obrigatória)

`core/services/candidate_evaluation.py` — `CandidateEvaluation` (frozen) + `evaluate_candidate(candidate, target_numeros, target_estrelas)` + `evaluate_candidates(...)`. Mede um `CandidateKey` já produzido contra um alvo explicitamente fornecido pelo chamador — `category` é `f"{matched_number_count}+{matched_star_count}"`, todas as 18 combinações de "0+0" a "5+2" são resultados válidos e não gated por `[HEROIS].categorias` (essa config pertence exclusivamente ao Hero Evaluation Engine, `core/services/hero_evaluation.py` — não é lida aqui). Duplica deliberadamente, em 3 linhas, a mesma interseção que `hero_evaluation.py:matched_values()`/`category_for()` já calculam — reutilizar essas funções obrigaria a arrastar concerns exclusivos de Heroes (config `[HEROIS]`, hashing de deduplicação, proveniência temporal) para um avaliador que tem de continuar agnóstico de domínio.

### Fronteira temporal (regra vinculativa)

```
histórico até X-1 → treino/evolução/geração → candidatos congelados → revelar resultado X → CandidateEvaluation → CandidatePerformanceSummary
```

`candidate_evaluation.py` e `candidate_performance.py` **não têm nenhuma noção de "concurso"/sorteio/data** — nunca leem um dataset, nunca sabem que dia é hoje, nunca podem "olhar para a frente": o alvo é sempre e apenas o que o chamador já resolveu e passou explicitamente. Isto é o que torna estruturalmente impossível o look-ahead aqui — ao contrário de `hero_evaluation.py:classify_temporal_provenance()`, que continua a ser o único sítio do projeto que decide se uma previsão podia honestamente ter existido antes do sorteio-alvo (`verified`/`legacy`/`ineligible`/`unresolved`). Estes dois módulos **nunca influenciam geração, fitness, o Conselho ou a seleção de uma chave** — são estritamente retrospetivos/experimentais, chamados sempre depois de os candidatos já estarem congelados.

## Commit 18 — Candidate Performance Analysis

`core/services/candidate_performance.py` — `CandidatePerformanceSummary` (frozen) + `summarize_candidate_performance(candidates, evaluations, relevant_categories)`. Agregação pura sobre pares `(CandidateKey, CandidateEvaluation)` já produzidos e emparelhados por posição — levanta `ValueError` em comprimentos diferentes. Diversidade calculada internamente via `frozenset(numeros)`/`frozenset(estrelas)` (deduplicação, nunca reordena os `CandidateKey` expostos). `category_counts` cobre sempre as 18 categorias fixas (`_ALL_CATEGORIES`), mesmo as não observadas (ficam a 0) — nunca lido de `[HEROIS]`. `relevant_categories` não tem default nem é lido de configuração — o chamador decide sempre, explicitamente, o que conta como "relevante". Deliberadamente **sem** `best_category` (não existe uma ordenação canónica de categorias no projeto — `config.txt [HEROIS_TIERS]` prova isso: `3+0`/`3+1`/`2+2` partilham `TIER_4`, `4+0`/`3+2` partilham `TIER_3`) e **sem** agrupamento nativo por `source_name`/`source_type`/`race`/`generation` — o chamador filtra os pares zipados e chama a função uma vez por grupo, evitando que este módulo tenha de decidir o que significa `generation=None`/`race=None`, ou confundir o Cronomante-raça-evolutiva com o `cronomante`-`origem`-externa (a mesma ambiguidade que motivou este desenho já aparece de forma real em `RACAS`, ver Commit 19 abaixo).

## Commit 19 — Minotauros V1 (`77b69b9`)

Nova raça dos Clérigos (`RACAS` em `factions/clerics/algorithm.py`, agora com 9 entradas) representando **persistência de chave**, em contraste deliberado com todas as outras linhagens (exploratórias/convergentes). Regras V1:

- **Não é uma nova facção/plugin** — é uma raça dentro da população evolutiva já existente dos Clérigos. Não regista `manifest.json`, não é descoberta por `FactionRegistry`, **não acrescenta um voto/facção ao Conselho**. O Conselho continua a ver os finalistas de Clérigos exatamente como já via.
- **Sobreviventes mantêm exatamente a última chave** — `archetypes.py:generate()`, ramo `if raca == "Minotauro"`: se `h.keys` já tem entradas, devolve `h.keys[-1]` (números e estrelas), sempre como cópias novas (`list(...)`) — gerações consecutivas nunca partilham o mesmo objeto lista, apesar de terem os mesmos valores.
- **Descendentes Minotauro podem herdar a chave de um progenitor Minotauro** — a herança acontece no ciclo de reprodução (`execute()` em `algorithm.py`), não em `generate()`: quando o filho nasce Minotauro, o código lê `p1.keys[-1]`/`p2.keys[-1]` do progenitor Minotauro elegível e guarda a chave em `f.genoma["chave_herdada"]`.
- **Se ambos os progenitores forem Minotauro elegíveis, p1 tem precedência determinística** — `if p1_raca == "Minotauro" and p1.keys: ... elif p2_raca == "Minotauro" and p2.keys: ...`, sem nenhum `random.choice()` adicional para decidir entre os dois.
- **Filhos não-Minotauro nunca herdam a chave** — o bloco de herança só corre quando `f.raca == "Minotauro"`, mesmo que um dos progenitores seja Minotauro.
- **Fundadores sem chave herdada geram chave própria** — `random.sample(range(1,51),5)` + `random.sample(range(1,13),2)` + `normalize_candidate()`, o mesmo padrão já usado por outras raças (ex. Goblin).
- **Números e estrelas são sempre preservados juntos** — a chave (numeros + estrelas) persiste/herda como uma unidade, nunca parcialmente.
- **A herança evita aliasing mutável** — `f.genoma["chave_herdada"] = (tuple(origem_chave["numeros"]), tuple(origem_chave["estrelas"]))` em `algorithm.py` (cópia imutável no momento da reprodução); `generate()` devolve sempre `list(...)` a partir daí (nunca a mesma lista/tupla armazenada).
- **Minotauros nunca passam por `aplicar_conhecimento()`** — nem no ramo de persistência, nem no ramo de herança fundadora; só o ramo "fundador sem herança" usa `normalize_candidate()` (não `aplicar_conhecimento()`) — conhecimento oculto de artefactos nunca altera a chave de um Minotauro, em nenhum dos três caminhos.
- **Provenance inalterado** — continua `origem="racas_antigas"` → `source_type="evolutionary_individual"` em `normalize_candidate_record()`; `classe="Minotauro"` mapeia para `race="Minotauro"` como qualquer outra raça de Clérigos. Zero alterações a `candidate_provenance.py`.
- **Fitness/eliminação/config inalterados** — `avaliar()` não foi tocado; Minotauros competem, morrem e ressuscitam pelas mesmas regras (`CAMINHO_1000_ALMAS`) que qualquer outra raça; não existe secção `[MINOTAUROS]` em `config.txt` — zero configuração nova.
- **Diversidade nominal, sem efeito algorítmico**: `NAMES` (10→26) e `TITULOS` (6→22) foram ampliados no mesmo commit para dar mais variedade a *todas* as raças (não só Minotauro) — mesmo mecanismo de `create()`, sem novas chamadas `random.*`, sem regras por raça. Isto muda os nomes/títulos concretos produzidos com uma seed fixa em relação a versões anteriores (esperado — o requisito de determinismo é só "mesma versão + mesma seed → mesmo resultado", nunca reprodutibilidade entre versões).

`tests/test_minotauros.py` (20 testes): persistência entre gerações (números+estrelas, tipos `list`, sem partilha de objeto), nascimento fundador (com e sem `chave_herdada`, determinismo com seed fixa), ausência comprovada de `aplicar_conhecimento()` nos três caminhos, proveniência (`race="Minotauro"`), ausência de qualquer import de `candidate_evaluation`/`candidate_performance` em `algorithm.py`/`archetypes.py`, e os 6 cenários de reprodução/herança (p1 herda, só-p2 herda, precedência p1 com ambos elegíveis, filho não-Minotauro não herda, Minotauro sem progenitor Minotauro não herda, cópia sem aliasing mutável).

## Ideias futuras / não implementadas (ver também Roadmap principal)

**Atualizado no Commit 24** — o Backtest Experiment Lab já não está nesta lista: existe desde o Commit 20 (`core/services/backtest_lab.py`), reutilizado por `historical_simulation_source.py`/`historical_ariadne_source.py`/`temporal_memory_boundary.py` nos Commits 22-24. Nada do resto desta lista existe hoje como código, especificação fechada ou funcionalidade — são apenas nomes/conceitos registados para decisão futura:

- **Zombies** — possível nova raça/facção explorando Monte Carlo territorial/local; apenas um nome, sem desenho.
- **Auditoria da memória/Cripta** — feita parcialmente no Commit 21/24 (Heroes, Legends, Grimório, Artefactos, Ordem Élfica) — ver a secção "Fronteira Temporal" abaixo para o inventário completo; o que ficou identificado como "irremediavelmente legado" (Grimório, `estado_ordem.json`) continua por resolver.
- **Futuras linhagens de Necromantes** — a Necromancia legada já está parcialmente resolvida (Commit 24, via `registado_em`); antes de desenhar uma linhagem nova, continua obrigatório auditar `necromancia_estatistica` (Commit 16) para evitar duplicação conceptual com o mecanismo de ressurreição de Lendas já existente em `main.py`.
- **Laboratório / superespécie** — conceito experimental de raça híbrida; apenas um nome, sem desenho.
- **Ligar o Backtest Lab/Fronteira Temporal a `main.py`** — nenhuma das peças dos Commits 20-24 é chamada automaticamente hoje; um orquestrador de backtest real fica para um commit próprio.
- **Replay temporal de Artefactos/Relíquias** — os eventos (`historia[].momento`) já têm timestamp real; reconstruir o estado "como estava em X" por replay é possível mas fica para um commit posterior (ver secção "Fronteira Temporal" abaixo).
- **Certificação temporal do Grimório/`estado_ordem.json`** — auditado no Commit 24 e considerado estruturalmente impossível sem reescrever esses ficheiros para registarem eventos datados em vez de flags acumulados; fora de âmbito indefinidamente, salvo decisão explícita de redesenhar a persistência.

---

# Fronteira Temporal — Backtest Lab & Segurança Temporal (Commits 20–24)

Cinco commits sequenciais, distintos da Camada de Proveniência (Commits 15-19) — respondem a uma pergunta diferente: dado um alvo histórico X já revelado, como construir e medir uma experiência sem deixar informação posterior a X influenciar o resultado. Nenhum introduz uma nova versão formal do projeto (mesma razão do bloco anterior).

## Duas fronteiras distintas (vocabulário vinculativo, usado em todos os commits abaixo)

- **Fronteira A** — "treino/evolução/fitness/Conselho só viram histórico estritamente anterior a X". Nenhum destes commits certifica isto — é um problema a montante (`world/engine/builder.py`), auditado no Commit 21, não corrigido.
- **Fronteira B** — "o candidato/memória provadamente existia antes da revelação oficial de X". É isto que todos os commits abaixo certificam, estruturalmente, reutilizando sempre a mesma disciplina: `< cutoff_datetime` (nunca `<=`), cutoff sempre timezone-aware (`ValueError` se naive), nunca inferir disponibilidade a partir de outra coisa (geração, nome, ordem do ficheiro, `mtime`, data do sorteio a que a memória se refere).

## Commit 20 — Backtest Experiment Lab

`core/services/backtest_lab.py` — `BacktestTarget` (frozen, `draw_datetime` validado timezone-aware em `__post_init__`), `FrozenCandidate` (`provenance` só pode ser `verified`/`legacy`/`unresolved` — `ineligible` nunca produz um `FrozenCandidate`, só um `ValueError`), `freeze_backtest_candidates()`/`evaluate_backtest_candidates()`/`summarize_backtest()`. Reutiliza `hero_evaluation.classify_temporal_provenance()` sem alterações. `freeze_backtest_candidates()` nunca recebe `target`/`numeros`/`estrelas` como parâmetro — só `official_draw_datetime` — garantia estrutural, não de convenção, de que a chave vencedora não pode vazar para a fase de congelamento (provado por `inspect.signature` no teste). `legacy` aceite por omissão (o arquivo real é 100% legacy — 0/42.527 registos têm `run_id`); `unresolved` excluído por omissão; múltiplos `run_id` não-`None` levantam `ValueError` salvo `allow_mixed_runs=True`; candidatos `legacy` nunca contam para essa verificação (sem `run_id` para comparar).

## Commit 21 — Auditoria da Fronteira A (sem alterações de código)

Auditoria pura de `library/ariadne/engine.py` e de tudo o que consome, mais toda a memória persistente (Grimório, Artefactos, Ordem Élfica, Lendas). Achados principais: `main.py` nunca lê `datasets/historical/euromillions/`; `Ariadne()` lê `library/scrolls/`/`library/indexes/` sem qualquer cutoff; o footgun `if not visivel: visivel = hist`; e um bug de look-ahead real e concreto na Necromancia (`tentar_ressuscitar_lenda()` podia ressuscitar uma Lenda registada depois do alvo do backtest). Nenhum destes foi corrigido nesse commit — motivaram os Commits 22-24.

## Commit 22 — Historical Simulation Source

`core/services/historical_simulation_source.py` — `available_at(draw)` (lê `draw['horario']['timestamp_utc']`), `load_versioned_history()` (todos os anos de `datasets/historical/euromillions/`, ordenado por `available_at`), `visible_draws(draws, cutoff_datetime)`, `adapt_to_legacy_draw(draw)` (achata `chave.numeros`/`chave.estrelas` para a forma plana que `world/engine/builder.py`/`core/evolution/statistics.py` esperam; `jackpot`/`vencedores` só têm equivalente parcial no dataset moderno — mapeados com a mesma convenção `None`→`0` que `get_history()` já usava), `build_historical_context_for_backtest(cutoff_datetime)` (compõe as três). **Não ligado a `main.py`/`builder.py`** — modo LIVE/NORMAL inteiramente preservado, este é um caminho novo e paralelo.

## Commit 23 — Temporal Ariadne

`core/services/historical_ariadne_source.py` — `pergaminho_available_at(scroll)` (dois locais possíveis consoante o ano: `scroll['data']['timestamp_utc']` em 2026, `scroll['horario']['timestamp_utc']` em 2004-2025; exclui explicitamente os `indice.json` por pasta de ano — não são pergaminhos), `load_scrolls()`, `visible_scrolls()`, `build_scrolls_for_backtest()`. `library/ariadne/engine.py:Ariadne` ganhou `__init__(self, scrolls=None)`: sem `scrolls`, comportamento LIVE inalterado; com `scrolls`, os 7 métodos baseados em pergaminhos (`scroll_state`/`search_moon`/`overdue_numbers`/`transition_pattern`/`full_history`/`weekly_echoes`/`last_known_key`) passam a usar exclusivamente essa coleção congelada — e, pela primeira vez, todos veem a mesma coisa (antes do Commit 23, `search_moon`/`overdue_numbers`/`transition_pattern` só viam 2026 via `self.scrolls`, enquanto `full_history`/`weekly_echoes` percorriam todos os anos frescos a cada chamada; essa inconsistência mantém-se em modo LIVE por design, só desaparece em modo temporal). `pairs`/`triples`/`numero`/`least_frequent_numbers` levantam `RuntimeError` numa instância temporal.

## Commit 24 — Temporal Persistent Memory

`core/services/temporal_memory_boundary.py` — mesma taxonomia `verified`/`legacy`/`ineligible`/`unresolved` de `classify_temporal_provenance`, mas resolvida a partir de um campo de timestamp já no próprio registo (`registado_em`/`promoted_at`/`recognized_at`), não de `run_id`→manifesto. `classify_memory_availability(raw_timestamp, cutoff_datetime)` + `temporal_memory_view(records, cutoff_datetime, get_raw_timestamp=..., allow_legacy=False, allow_unresolved=False)` — vista por omissão só `verified`; `ineligible` nunca tem override, sob nenhuma flag.

Distinção vinculativa auditada: `candidate existed_at` (quando a chave prevista foi gerada) ≠ `recognition/promoted_at` (quando o sistema reconheceu que era boa) ≠ `memory_record available_at` (quando esse reconhecimento foi escrito em disco) — nenhum sistema do projeto tinha o terceiro campo antes deste commit.

**Necromancia** (`orders/black_squad/black_mages.py:tentar_ressuscitar_lenda(config, events, cutoff_datetime=None)`): `cutoff_datetime=None` preserva o comportamento LIVE exato; fornecido, filtra os candidatos (`docs/lore/legends/livro_personagens_lendarias.json` + `ecos_ancestrais.json`) por `registado_em` antes de `random.choice()` — nenhuma Lenda registada depois do cutoff pode ser ressuscitada. `ecos_ancestrais.json` (lore estático, sem `registado_em`) classifica sempre `legacy` e fica excluído por omissão, sem caso especial. Cutoff naive levanta `ValueError` **antes** de qualquer gate de RNG. Consumo de RNG idêntico independentemente do tamanho da pool (contagem de chamadas, nunca o valor escolhido).

**`recognized_at`/`promoted_at`** — forward-only, sem migração: `evaluate_heroes.py` passa a escrever `recognized_at` (um `datetime.now()` por execução do CLI) em cada novo Hero; `core/services/legend_evaluation.py:evaluate_group()` ganhou o parâmetro obrigatório `promoted_at` (nunca calculado internamente — mantém a pureza já documentada do módulo), escrito só em registos `"promote"` novos. Registos antigos (todos os Heroes e Legends já persistidos) não têm estes campos e continuam `legacy` para sempre — nenhuma retrodatação.

**Explicitamente fora de certificação, por decisão, não por esquecimento**: Grimório (`orders/black_squad/dark_library/grimorio_negro.json`), `estado_ordem.json` (Ordem Élfica), e o estado atual (campos de topo) de Artefactos/Relíquias — todos sem qualquer timestamp ao nível do facto agregado realmente consultado durante a geração, apesar de os eventos individuais que os alimentam (cópias de livros, roubos, missões, `historia[]` dos artefactos) terem `momento`/`criado_em` reais. `artifacts/living.py`, `artifacts/ark.py`, `orders/black_squad/persistence.py` e `orders/elven_order/ninjas.py` nunca importam `temporal_memory_boundary` — provado estruturalmente por teste, não só documentado.

## Testes (Commits 20-24)

`tests/test_backtest_lab.py` (26), `tests/test_historical_simulation_source.py` (29), `tests/test_historical_ariadne_source.py` (39), `tests/test_temporal_memory_boundary.py` (22) + 1 teste adicional em `tests/test_legend_evaluation.py` (`promoted_at`) — 117 testes novos no total.

## O que fica para commits futuros

Ligar qualquer peça destes 5 commits a `main.py`/a um orquestrador de backtest real; corrigir o footgun de `world/engine/builder.py`; repontar `core/data/loaders.py:get_history()` para o dataset versionado; certificar temporalmente `pairs`/`triples`/`numero`/`least_frequent_numbers` (exigiria regenerar os índices a partir de um subconjunto de pergaminhos já cortado); replay temporal de Artefactos/Relíquias a partir do seu `historia[]`; qualquer tentativa de tornar o Grimório/`estado_ordem.json` temporalmente certificáveis (exigiria redesenhar o esquema de persistência, não só acrescentar um campo).
