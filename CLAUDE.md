# CLAUDE.md

# Oráculos do Euromilhões --- Especificação do Projeto (V1 → V8)

> Documento de contexto para desenvolvimento contínuo.

## Objetivo

Criar um universo narrativo em torno da análise histórica do
Euromilhões. O projeto **não pretende prever resultados**, mas explorar
estratégias, estatísticas, simulações e personagens que consultam uma
Biblioteca de conhecimento.

------------------------------------------------------------------------

# V1

-   Conselho inicial de personagens.
-   Geração de chaves.
-   Relatórios.

# V2

-   Introdução de estratégias distintas por personagem.
-   Conselho escolhe chave final.

# V3

-   Campanhas, gerações e evolução das personagens.
-   Personagens lendárias.
-   Ranking histórico.

# V4

## V4.4

-   Amuletos vivos.
-   Artefactos.
-   Relíquias persistentes.

## Biblioteca

-   Livros proibidos.
-   Monges e Escribas.
-   Apenas algumas classes podem consultar certos livros.

## Esquadrão Negro

-   Roubo de livros.
-   Biblioteca Negra.

## Ordem Élfica

-   Missões para recuperar livros e relíquias.

# V5

## Biblioteca Eterna

-   Ariadne concebida como guardiã.
-   Pergaminhos.
-   Crónicas.
-   Artefactos persistentes.
-   Livros de estatísticas.

## Novas classes

-   Treefolks investigadores.
-   Vampiros (triplas).
-   Gárgulas (duplas).

# V6

-   Configuração por ficheiro config.
-   Número de rondas configurável.
-   Inventário de artefactos.
-   Estratégia dos Esqueletos (janela de 25 números).
-   Vilão que incentiva simbolicamente os números escolhidos.

# V7

## Biblioteca Eterna

Estrutura:

-   fontes
-   pergaminhos
-   livros
-   consultas
-   índices
-   artefactos
-   relíquias
-   amuletos

### Ariadne

Consulta: - pergaminhos - índices - livros

### Dados

-   Dataset 2026
-   Excel "Saídas de Bolas"
-   55 pergaminhos

### Livros

-   Livro das Pedras Eternas
-   Livro dos Pactos de Pedra
-   Livro do Sangue Triplo
-   Livro Lunar

### Vampiros

-   Linhagem Sanguínea
-   Linhagem Sombria

### Gárgulas

-   Pedra
-   Espelho

### Treefolks

Investigação estatística e deteção de "fantasmas estatísticos".

# V7.1

## Ariadne Fonte-Viva

Mudança arquitetural principal:

Personagens → Ariadne → Consultas → Livros reconstruíveis → Fontes
originais

### Fontes

Cada ano possui um dataset completo preservado.

    biblioteca/fontes/
        2004/
        ...
        2026/

### Pergaminhos

São vistas leves. Referenciam: - fonte original - índice do sorteio -
hash da chave

### Livros reconstruíveis

-   Frequências
-   Duplas
-   Triplas
-   Lua

Reconstruídos automaticamente.

### Cache

Consultas reutilizadas quando possível.

------------------------------------------------------------------------

# Universo

## Facções geradoras de chaves

| Facção | Módulo | Estratégia |
|--------|--------|-----------|
| Clérigos | `racas/antigas.py` + `evolucao/` | Algoritmo genético, 14 gerações |
| Melforks | `racas/extras.py` | Algoritmo genético especializado |
| Anões | `racas/extras.py` | Combinatória por clãs (3 × 15 chaves) |
| Fadas | `racas/extras.py` | Ponderação por números quotidianos |
| Lobisomens | `racas/extras.py` | Monte Carlo de aptidão (fase lunar) |
| Treefolks | `treefolks/` | Consulta Ariadne; mede fantasmas estatísticos |
| Vampiros | `vampiros/` | Triplas frequentes e consecutivas |
| Gárgulas | `gargulas/` | Duplas frequentes e consecutivas |
| Cronomantes | `racas/cronomantes.py` | Energia dos eventos de extração |
| Esqueletos | `racas/esqueletos.py` | Janela móvel de 25 números |
| Esquadrão Negro | `esquadrao_negro/` | Anti-popularidade; grimório roubado |
| Ordem Élfica | `ordem_elfica/` | Missões de recuperação (não vota directamente) |
| Kors de Elarion | `faccoes/kors/` | Observação via Ariadne (V7.2) |
| Axiomantes de Nemerion | `faccoes/axiomantes/` | Labirinto combinatório + Feistel (V8.1) |

## Facções analíticas (não geram chaves)

| Facção | Módulo | O que produz |
|--------|--------|-------------|
| Cartógrafos do Caos | `faccoes/cartografos_caos/` | 5 livros analíticos em `biblioteca/books/cartographers/` (V8) |
| Monges e Escribas | `amuletos/biblioteca.py` | Livros reconstruíveis, índices |

## Vilões e mecânicas narrativas

- **Malphas** — corrompe a chave final com deslocamentos aleatórios
- **Vírus de Malphas** — infecciona heróis; bónus de score mas revelado no Conselho
- **Guerra do Conselho** — Ordem Élfica tenta purificar; Malphas corrompe
- **Convicção Sombria** — mantra que reforça simbolicamente a chave

------------------------------------------------------------------------

## Internacionalização (`i18n/`)

Módulo `i18n/traducoes.py` — 6 línguas × 25 chaves para os 9 países participantes do Euromilhões.

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

### Tabela de chaves de tradução

| Chave | Utilizado em | Descrição |
|-------|-------------|-----------|
| `veredicto_acaso` | `ritual.py` | Excesso ∈ [-5%, +5%] |
| `veredicto_ligeiro` | `ritual.py` | Excesso ∈ [+5%, +10%] |
| `veredicto_desvio` | `ritual.py` | Excesso ≥ +10% |
| `veredicto_abaixo` | `ritual.py` | Excesso < -5% |
| `portal_aberto` | `ritual.py` | Status curto: "ABERTO" / "OPEN" / etc. |
| `portal_fechado` | `ritual.py` | Status curto: "FECHADO" / "CLOSED" / etc. |
| `portal_aberto_msg` | `conselho.py`, `main.py` | Mensagem longa: "Portal ABERTO" |
| `portal_fechado_msg` | `conselho.py`, `main.py` | Mensagem longa com nota de abstenção |
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

Nomes próprios do universo narrativo ficam sempre em português:
Kors de Elarion · Axiomantes de Nemerion · Ariadne · Malphas · Ordem Élfica · Esquadrão Negro · Cartógrafos do Caos · etc.

O campo `lang` é gravado em cada experiência JSON dos Axiomantes (`ritual.py → resultado['lang']`).

------------------------------------------------------------------------

## Referência: métodos Ariadne (`biblioteca/ariadne/motor.py`)

| Método | Introduzido | O que faz |
|--------|-------------|----------|
| `estado_pergaminho(n)` | V7 | Estado e integridade do pergaminho N de 2026 |
| `procurar_lua(fase)` | V7 | Frequências nos sorteios com dada fase lunar |
| `duplas(limite)` | V7 | Duplas mais frequentes de `indices/duplas.json` |
| `triplas(limite)` | V7 | Triplas mais frequentes de `indices/triplas.json` |
| `numero(n)` | V7 | Frequência histórica de um número (normalizado) |
| `numeros_atrasados(limite)` | V7.2 | Números com maior atraso nos pergaminhos 2026 |
| `numeros_menos_frequentes(limite)` | V7.2 | Menos frequentes no histórico completo normalizado |
| `padrao_transicao()` | V7.2 | Análise penúltima→última chave (chegados, saídos, persistentes) |
| `ecos_semanais(semana_iso)` | V7.2 | Sorteios da mesma semana ISO em todos os anos |
| `criar_papiro(semana_iso, dados)` | V7.2 | Grava papiro em `biblioteca/black_kors/papyri/` |
| `historico_completo(desde, ate, ultimos)` | V8 | Todos os sorteios de todos os anos (1962 draws, 2004-2026) |
| `ultima_chave_conhecida()` | V8.1 | Último sorteio registado (data, numeros, estrelas) |

**Nota sobre formatos de pergaminho:**
- 2026: `"data": {"extracao": "YYYY-MM-DD", ...}` (dict com astronomia completa)
- 2004-2025: `"data": "YYYY-MM-DD"` (string directa)

Ariadne trata ambos os formatos de forma transparente.

------------------------------------------------------------------------

# V7.2

## Kors de Elarion

Facção implementada em `faccoes/kors/`. Toda a informação flui exclusivamente
através de Ariadne — os Kors nunca lêem datasets diretamente.

### Kor Branco — Aelyra dos Silêncios

Estratégia: `ariadne.numeros_atrasados(15)` → 15 números mais atrasados,
seleção ponderada pelo atraso.

### Kor Vermelho — Kael da Chama Fria

Estratégia: `ariadne.numeros_menos_frequentes(20)` → números menos frequentes
no histórico completo, seleção inversa à frequência.

### Kor Verde — Sylvara das Passagens

Estratégia: `ariadne.padrao_transicao()` → padrão entre penúltima e última
chave (números chegados, persistentes, vizinhos).

### Kor Preto — Nyxara das Sombras Semanais

Estratégia: `ariadne.ecos_semanais(semana_iso)` → sorteios da mesma semana
ISO em todos os anos disponíveis. Cria papiros em:

    biblioteca/black_kors/papyri/week_XX/

### Novos métodos Ariadne (biblioteca/ariadne/motor.py)

-   `numeros_atrasados(limite)` — atraso por número nos pergaminhos 2026
-   `numeros_menos_frequentes(limite)` — frequência histórica de saidas_de_bolas_normalizado.json
-   `padrao_transicao()` — análise penúltima → última chave
-   `ecos_semanais(semana_iso)` — sorteios da mesma semana ISO em todos os anos
-   `criar_papiro(semana_iso, dados)` — grava papiro em biblioteca/black_kors/papyri/

### Integração

-   `faccoes/kors/conselho.py` → `conselho_kors(ariadne)` chamado em `main.py`
-   Origem no arquivo: `kors_elarion`
-   Peso configurável em `[KORS] peso_conselho` em config.txt

------------------------------------------------------------------------

# V8

## Cartógrafos do Caos

Cinco analistas implementados em `faccoes/cartografos_caos/`. Não geram chaves —
produzem livros analíticos em `biblioteca/books/cartographers/` para consulta por
outras facções (Treefolks, Kors, Vampiros).

Todo o acesso a dados é via `ariadne.historico_completo()` — nunca directo aos fontes.

| Cartógrafo | Ficheiro | Livro gerado |
|-----------|---------|-------------|
| Eldran das Constelações | `constelacoes.py` | Livro das Constelações Numéricas |
| Vesara dos Intervalos | `ciclos.py` | Livro dos Ciclos Eternos |
| Lirien das Correntes | `tendencias.py` | Livro das Tendências e Correntes |
| Thalvos do Acaso Esperado | `aleatoriedade.py` | Livro do Acaso Esperado |
| Oryn dos Ecos Sequenciais | `markov.py` | Livro dos Ecos Sequenciais |

### Novos métodos Ariadne (V8)

- `historico_completo(desde, ate, ultimos)` — todos os sorteios de todos os anos (2004-2026); suporta ambos os formatos de pergaminho (string e dict)

### Integração

- `faccoes/cartografos_caos/conselho.py` → `executar_cartografos(ariadne, cfg)` chamado em `main.py`
- Corre antes dos Kors (usa a mesma instância Ariadne)
- Monte Carlo configurável em `[CARTOGRAFOS_CAOS] monte_carlo_simulacoes`

------------------------------------------------------------------------

# V8.1

## Axiomantes de Nemerion

Facção implementada em `faccoes/axiomantes/`. Percorrem o Labirinto de 139.838.160
câmaras usando uma permutação Feistel reproduzível — sem repetições, sem guardar 139M linhas
em memória. A posição de qualquer chave é calculada em O(1) via Feistel inverso.

### Matemática

- **Universo**: C(50,5) × C(12,2) = 2.118.760 × 66 = **139.838.160 combinações**
- **Rank/unrank**: combinatório → índice e vice-versa (algoritmo combinádico)
  - `rank_chave([2,14,28,33,48], [8,10])` → inteiro único em [0, 139.838.159]
  - `unrank_chave(103.811.641)` → ([2,14,28,33,48], [8,10])
- **Feistel (_H = 11826, 4 rondas)**: bijecção sobre [0, _H²-1]; cycle-walk para valores ≥ UNIVERSO
  - `posicao_de_chave(nums, ests, seed)` — posição via Feistel⁻¹; O(1)
  - `chave_na_posicao(pos, seed)` — chave via Feistel; O(1)

### Ritual dos Trinta Ecos

Fluxo completo (`ritual.py → executar_ritual`):

1. `ariadne.historico_completo()` → marco = último sorteio registado
2. `posicao_de_chave(marco, seed)` → posição do marco na sequência Feistel
3. Para cada sorteio do período (`periodo_anos` em config): calcula posição → separa **ecos** (antes do marco) dos restantes
4. Métricas: `cobertura%`, `fracao_universo%`, `excesso%`, `espaco_medio_obs`, `espaco_teorico`
5. **Portal aberto** se `cobertura >= limiar_cobertura AND excesso >= excesso_minimo`
6. Se portal aberto:
   - `calcular_perfil(ecos)` → perfil estatístico dos ecos
   - `escolher_por_perfil(...)` → avalia `n_candidatos` chaves inéditas por score
   - Devolve a chave com maior pontuação

### Perfil dos Ecos (`perfil.py → calcular_perfil`)

Calculado a partir das chaves históricas encontradas antes do marco:

| Campo | Como se calcula |
|-------|----------------|
| `soma_media`, `desvio_soma` | média e desvio-padrão das somas dos 5 números |
| `faixa_soma_preferida` | `[media - desvio, media + desvio]` |
| `paridades_preferidas` | top-2 combinações (nPares, nÍmpares) por frequência |
| `baixos_altos_preferidos` | top-2 combinações (n≤25, n>25) por frequência |
| `numeros_mais_frequentes` | top-10 números por ocorrências nos ecos |
| `numeros_menos_frequentes` | 10 números com menos ocorrências |
| `estrelas_mais_frequentes` | top-6 estrelas por ocorrências nos ecos |
| `gap_medio` | média dos gaps consecutivos por chave, depois média global |
| `amplitude_media` | média de (max - min) por chave |
| `distribuicao_numerica` | dict {numero: contagem} para todos os presentes |
| `distribuicao_estrelas` | dict {estrela: contagem} |

### Pontuação de chaves (`perfil.py → score_chave`) — 0 a 100 pts

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

Regra anti-previsibilidade: penaliza chaves com 4 ou 5 números do top-5 (demasiado óbvias).

### Aviso obrigatório (presente em todos os relatórios)

> "A posição de uma chave numa permutação pseudoaleatória não altera a sua probabilidade
> real. Uma taxa de cobertura ≥ 50% é esperada quando se percorre ≥ 50% do universo.
> O perfil dos Ecos reflecte regularidades do passado que não têm poder preditivo matemático."

### Parâmetros de config (`[AXIOMANTES]` em config.txt)

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `peso_conselho` | 0.75 | Peso no Conselho (só vota quando portal aberto) |
| `periodo_anos` | 1 | Anos de sorteios usados como ecos de comparação |
| `limiar_cobertura` | 0.50 | Cobertura mínima para abrir o Portal |
| `excesso_minimo` | 0.0 | Excesso mínimo sobre o esperado |
| `n_candidatos` | 50000 | Chaves inéditas avaliadas (50K ≈ 1.5s; 250K ≈ 4s) |
| `guardar_experiencia` | true | Grava JSON em `axiomantes/experiences/` |

### Estrutura de ficheiros

| Ficheiro | Conteúdo |
|---------|---------|
| `faccoes/axiomantes/labirinto.py` | rank/unrank + Feistel permutation |
| `faccoes/axiomantes/perfil.py` | Perfil dos Ecos + pontuação de chaves |
| `faccoes/axiomantes/ritual.py` | análise completa + Trinta Ecos + salva experiência |
| `faccoes/axiomantes/conselho.py` | ponto de entrada para main.py |
| `faccoes/axiomantes/config.json` | metadados e linhagens |
| `axiomantes/experiences/` | relatórios JSON por execução |

### Integração

- `faccoes/axiomantes/conselho.py` → `axiomantes(ariadne, seed, cfg)` chamado em `main.py`
- Recebe o mesmo `seed` da simulação → ritual reproduzível
- Só vota quando portal aberto (caso contrário devolve `[]`)
- Peso configurável em `[AXIOMANTES] peso_conselho` em config.txt

------------------------------------------------------------------------

# Arquitetura futura (V9)

O directório `faccoes/` já existe com `kors/` e `cartografos_caos/`.
O próximo passo é migrar as facções antigas para o mesmo padrão:

    faccoes/
        kors/                  ✅ V7.2
        cartografos_caos/      ✅ V8
        axiomantes/            ✅ V8.1
        vampiros/              🔲 migrar de vampiros/
        gargulas/              🔲 migrar de gargulas/
        treefolks/             🔲 migrar de treefolks/
        clerigos/              🔲 migrar de racas/ + evolucao/
        esquadrao_negro/       🔲 migrar de esquadrao_negro/

Cada facção seguirá o padrão:

-   `config.json` — metadados, peso, descrição
-   `conselho.py` — ponto de entrada único
-   ficheiros de estratégia individuais

Ariadne carregará automaticamente `faccoes/*/config.json` para descobrir facções.

## Candidatos para V9

-   Entropia — medir o "caos" dos sorteios por ano
-   Heatmaps — matriz visual de pares/triplas (output CSV/JSON para visualização)
-   Treefolks consultando os livros dos Cartógrafos directamente
-   Ranking em ascensão por janela temporal

------------------------------------------------------------------------

# Princípios

-   As fontes originais são imutáveis.
-   Pergaminhos são vistas.
-   Livros são reconstruíveis.
-   Consultas funcionam como cache.
-   Todo o conhecimento passa por Ariadne.
-   O projeto é um simulador estatístico e narrativo; os padrões
    históricos não aumentam a probabilidade matemática de prever um
    sorteio futuro.
