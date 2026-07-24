# CLAUDE.md

# Oráculos do Euromilhões — Especificação do Projeto (V1 → V8.1)

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
| Clérigos | `factions/clerics/algorithm.py` + `archetypes.py` | Algoritmo genético, 14 gerações, 8 arquétipos ancestrais (V11) |
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
- 2026: `"data": {"extracao": "YYYY-MM-DD", ...}` (dict com astronomia completa)
- 2004-2025: `"data": "YYYY-MM-DD"` (string directa)

Ariadne trata ambos os formatos de forma transparente.

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
dashboard/ (planned — V11)
    Visualisation and analysis
```

| Layer | Responsibility |
|---|---|
| `core/` | Generic, reusable framework: plugin registry, proposal model, shared algorithms |
| `factions/` | Candidate-generation strategies — one plugin per faction |
| `orders/` | Narrative organisations and special systems, outside Council voting by design |
| `races/` | Lore, characters and world-building — documentation only |
| `datasets/` | Historical knowledge (immutable source data) |
| `experiments/` | Generated outputs (simulations, backtests, reports) |
| `dashboard/` | Visualisation and analysis (planned, V11) |

## Faction → Algorithm → Race map (selection)

| Faction | Algorithm | Race |
|---|---|---|
| Clerics | Genetic Algorithm — `factions/clerics/algorithm.py` (engine) + `archetypes.py` (8-lineage dispatcher) (V11) | Clerics (`races/clerics/`) |
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
    clerics/              ✅ V11  algorithm.py (genetic engine) + archetypes.py (8 lineages) — the oldest
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

| Ficheiro | Cobre |
|---------|------|
| `test_models.py` | `core/strategy.py` — `Proposal` (defaults, isolamento de `extra`) e `Faction` (ABC, propriedades `name`/`origin`/`home`) |
| `test_registry.py` | `core/registry.py` — `register`/`all`/`count`, `discover()` (skip de `_prefixo`, skip de não-diretórios, contagem real de 20 facções votantes, exclusão das analíticas) |
| `test_plugin_loader.py` | `core/plugin_loader.py` — `_load_manifest`, `load_faction` (ordem de resolução), `CompatFaction.propose()` para as 3 formas de retorno (lista simples, anões com `carteira`, lobisomens com `ativo`/`finalistas`) |
| `test_council.py` | `council/council.py` — `filter_candidates` (mutação de soma fora do intervalo, rejeição por baixa energia), `vote` (agregação ponderada), `corrupt` (limites válidos, preservação da chave original) |
| `test_backtesting.py` | `compare_result.py` — `titulo()` (todas as combinações), `avaliar_registo()` (pontuação, preservação de campos) |

**Filosofia:** os testes cobrem a *framework* (registry, plugin_loader, council, modelos partilhados, pontuação do backtesting), não a lógica narrativa de cada facção — um refactor da arquitetura de plugins deve falhar aqui, localmente, em vez de partir silenciosamente uma facção three camadas depois. As 21 facções em `factions/*/` não têm testes dedicados; a sua "correção" é maioritariamente narrativa, não mecânica.

# Serviços partilhados (`core/services/`)

`combinations.py` (`normalize_candidate`, `gaps`) e `fitness.py` (`fitness`) já têm lógica real, migrada durante a limpeza de arquitetura de V10.5 e a migração dos Clérigos em V11. O resto continua scaffold/auditoria — existe hoje lógica estatística duplicada em vários pontos que estes serviços deverão eventualmente substituir:

| Duplicação encontrada | Onde |
|---|---|
| Contagem de frequências (`Counter` sobre sorteios) | `core/evolution/statistics.py`, `factions/chaos_cartographers/{trends,randomness,cycles}.py`, `factions/axiomantes/profile.py` |
| Quentes/frios | `core/evolution/statistics.py` vs `factions/chaos_cartographers/trends.py` vs `Ariadne.least_frequent_numbers()` — 3 fontes de verdade inconsistentes |
| Atraso/"overdue" | `Ariadne.overdue_numbers()` (só pergaminhos 2026) vs `core/evolution/statistics.py` (histórico completo) vs `factions/chaos_cartographers/cycles.py` (mais detalhado: médio/máx/mín/variância) |
| Gaps intra-chave | `core/services/combinations.py:gaps` ✅ já centralizado (V11); ainda recomputado independentemente em `factions/chaos_cartographers/trends.py`, `factions/axiomantes/profile.py` |
| Pares/triplas | `Ariadne.pairs()/triples()` vs recomputação em `factions/chaos_cartographers/constellations.py` e `markov.py`; `factions/vampires/algorithm.py` e `factions/gargoyles/algorithm.py` leem `library/indexes/*.json` diretamente em vez de usar `Ariadne` |
| Baixos/altos, pares/ímpares | `factions/chaos_cartographers/{trends,randomness}.py`, `factions/axiomantes/profile.py` |

Serviços previstos (nomes indicativos): `StatisticsService`, `DelayService`, `PairService`, `TripleService`, `EntropyService`, `TrendService`. Migração fica para depois — **não implementar já**.

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
- ✅ Clerics auto-discovered by `FactionRegistry` (20 voting factions, up from 19) — verified via direct `load_faction()` probe, not just the registry count
- ✅ Deterministic before/after comparison: population, cemetery, resurrected heroes, per-generation summary, and the isolated Council-proposal shape are byte-identical between the pre- and post-migration engine, and the ending `random.getstate()` matches exactly — proof of zero additional random draws
- Known, documented side effect: Clerics finalists now flow through the generic "all plugin factions" loop in `main.py` instead of a hardcoded early-position block, so they're interleaved alphabetically with other factions in the final candidate list (previously they held a fixed early slot) — this changes tie-breaking in `council/council.py::vote()` and mutation order in `filter_candidates()`, so the *final Council-selected key* for a full `main.py` run can differ from before, even though the Clerics algorithm itself is unchanged. Also, Clerics finalists are now registered in the external chronicle (`externos`/`registo_externo`) for the first time, consistent with every other faction — previously they were the only voting faction excluded from that registration.
- Completar o lore das 20 raças — ✅ done in V10.5
- Novas facções: Juízes do Conselho, Geómetras do Véu, Estatísticos Imperiais
- `dashboard/` — visualização e análise
- Rng retrofit decision: estender `ctx['rng']` a todas as facções (hoje só Panteão + Skeletons + Chronomancers), ou manter `random` global nas restantes — Clerics migration deliberately kept global `random` to guarantee determinism (see above)

# Dependências opcionais

## Dashboard (V12.3 — em desenvolvimento)

O módulo `dashboard/` (exportação para Excel) usa `openpyxl`, que não é uma
dependência obrigatória do núcleo do projeto (ver `requirements.txt`).
Instalar apenas se for necessário gerar o workbook de investigação:

```bash
pip install -r requirements-dashboard.txt
```
