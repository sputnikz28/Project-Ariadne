# Bestiário Algorítmico Recuperado — Reconstrução a partir do Código e do Git

> **Nota de âmbito (importante, ler antes do resto)**: esta versão do
> Bestiário representa principalmente a **arqueologia V8 → atual**. Foi
> construída antes de recuperarmos os ficheiros Python das versões
> primordiais do projeto (V1/V2/V3) — o commit mais antigo disponível em
> qualquer branch deste repositório Git é `756c63e6` ("V8 - Claude"), e é
> esse o limite real de tudo o que está confirmado abaixo como
> "CONFIRMADO NO HISTÓRICO GIT". As descobertas pré-Git (ficheiros
> primordiais recuperados por outra via, fora deste repositório) **não
> foram ainda incorporadas aqui por memória, deliberadamente** — ficam
> reservadas para uma segunda passagem, baseada diretamente nesses
> ficheiros, que acrescentará uma secção própria **ARQUEOLOGIA PRÉ-GIT —
> V1/V2/V3** e uma árvore evolutiva das estratégias. Tudo o que se segue
> é o conteúdo integral e os níveis de evidência exatamente como
> produzidos nessa auditoria.

**Nota de método, antes de tudo**: como já estabelecido no audit anterior, `main` só tem história Git a partir de "V8.1 - Open Source Edition" (`f3965931`); a linhagem paralela em português (`master`/`claude`/`open`) tem só 3 commits, o mais antigo sendo `756c63e6` ("V8 - Claude"). **Esse é o limite absoluto da arqueologia possível** — não existe V1-V7 em Git em lado nenhum. Tudo o que se segue está ancorado nesse commit mais antigo disponível e no código atual; nada foi inventado a partir de memória ou de lore.

---

## CAMADA A — Facções / Povos / Organizações

| # | Entidade | Estado | Nasceu em (evidência) | Gera chaves | Entrypoint |
|---|---|---|---|---|---|
| 1 | **Clérigos** | ACTIVE | V8 (`racas/antigas.py`) | Sim (10 raças internas) | `main.py` explícito + loop |
| 2 | **Melforks** | ACTIVE | V8 (`racas/extras.py:melforks()`) | Sim (GA) | loop genérico |
| 3 | **Vampiros** | ACTIVE | V8 (`vampiros/linhagens.py`) | Sim (2 linhagens) | loop genérico |
| 4 | **Gárgulas** | ACTIVE | V8 (`gargulas/linhagens.py`) | Sim (2 linhagens) | loop genérico |
| 5 | **Treefolks** | ACTIVE | V8 (`treefolks/investigador.py`; `algorithm.py` com "modelo" narrativo já presente em V8 texto, embora não neste ficheiro específico) | Sim | loop genérico |
| 6 | **Kors de Elarion** | ACTIVE | V8 (`faccoes/kors/`) | Sim (4 sub-entidades) | loop genérico (era explícito antes do V9) |
| 7 | **Cartógrafos do Caos** | ACTIVE, analítico (não vota) | V8 (`faccoes/cartografos_caos/`) | Não | `main.py` explícito |
| 8 | **Axiomantes de Nemerion** | ACTIVE | V8.1 (`f79d907a` "v8.1 Axiomantes") | Sim | loop genérico |
| 9 | **Esqueletos** | ACTIVE | não confirmado em V8; presente em `racas/antigas.py:gerar()` como raça de Clérigo já em V8 (`from racas.esqueletos import gerar`) | Sim | loop genérico + interno a Clérigos |
| 10 | **Cronomantes** | ACTIVE | idem — já referenciado em V8 (`racas.cronomantes`) | Sim | loop genérico + interno a Clérigos |
| 11 | **Anões** | ACTIVE | V8 (`racas/extras.py:anoes()`) | Sim (3 clãs, mesma estratégia) | loop genérico |
| 12 | **Fadas** | ACTIVE | V8 (`racas/extras.py:fadas()`) | Sim | loop genérico |
| 13 | **Lobisomens** | ACTIVE, mas **nunca disparou num run real** (achado do audit anterior) | V8 (`racas/extras.py:lobisomens()`) | Sim | loop genérico (condicional lua cheia) |
| 14 | **Esquadrão Negro** | ACTIVE, fora do `FactionRegistry` | V8 (`esquadrao_negro/`) | Sim | `main.py` explícito |
| 15 | **Ordem Élfica** | ACTIVE, fora do `FactionRegistry`, não vota | V8 (`ordem_elfica/`) | Não | `main.py` explícito |
| 16 | **Guardiões do Tempo** | **Inexistente** — confirmado no audit anterior (0 resultados, todas as branches) | — | — | — |
| 17 | 8 Mystics (incl. Bone Readers) | LORE_ONLY/PLACEHOLDER | V10 (`28947bae`) | Não | loop genérico, sempre `[]` |
| 18 | Panteão (Magos/Druidas/Djinns/Aion) | ACTIVE, fora do `FactionRegistry` | V8 (`racas/extras.py:superiores()`) | Sim | `main.py` explícito |

---

## CAMADA B — Bestiário por raça/linhagem/arquétipo

### 🕯️ CLÉRIGOS — `factions/clerics/archetypes.py`

**Todas as 10 raças confirmadas no código atual.** As 8 originais (Bruxa, Vidente, Chefe Tribal, Elfo, Goblin, Shaman, Cronomante, Esqueleto) já existiam, **byte-a-byte com a mesma lógica**, em `racas/antigas.py` no commit mais antigo disponível (`756c63e6`, V8) — só mudaram nomes de variáveis (PT→EN) e a chamada RNG (`random`→`normalize_candidate(...,random)`). Minotauro entrou depois (Commit 19, `77b69b9`), Zombie por último (Commit 26, `71be259`). **Nenhuma raça de Clérigos foi alguma vez removida** — confirmado por `git log -p` sobre `RACAS =`: a lista só cresce, 8→9→10, nunca encolhe.

---
**Nome:** Bruxa
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL (`archetypes.py:149-160`) e CONFIRMADO NO HISTÓRICO GIT (idêntico desde V8)
**Estratégia:** frequências recentes — mistura 2 números "quentes" + 2 "frios" + 1 aleatório puro
**Como gera a chave:** `random.sample(quentes,2) + random.sample(frios,2) + [randint(1,50)]`; estrelas: 1 quente + 1 fria
**O que a distingue:** é a única raça que combina deliberadamente quente+frio na mesma chave (equilíbrio, não extremo)
**Hipótese que testa:** *"misturar extremos de frequência (quente+frio) produz um comportamento diferente de escolher só um dos dois?"*
**Evidência:** `factions/clerics/archetypes.py:149`; `racas/antigas.py` (commit `756c63e6`)

---
**Nome:** Vidente
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** frequências quentes + "visão" probabilística do sorteio mais antigo da janela (`hist[0]`), com "confusão" (ruído genómico) a distorcer o número visto
**Como gera a chave:** base = 2 quentes; com prob. `0.08 + clareza*0.25` adiciona 1-2 números de `hist[0]["numeros"]`, cada um distorcido em ±1/±2 se `random() < confusao`
**O que a distingue:** único que lê explicitamente o **genoma individual** (`clareza`/`confusao`) para modular a própria estratégia — não é global, é por indivíduo
**Hipótese que testa:** *"dar 'visão' ruidosa e individualizada de um sorteio antigo melhora ou piora vs. quentes puros?"*
**Evidência:** `archetypes.py:162-172`

---
**Nome:** Chefe Tribal
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** passeio simbólico determinístico-por-sorteio — "lançar ossos" com símbolos (sol/lua/lobo/fogo/água/montanha/corvo) cada um com deslocamento fixo, aplicados sequencialmente a partir de um ponto aleatório
**Como gera a chave:** `atual = randint(1,12)`; para cada um dos 5 "ossos" sorteados, `atual += simbolos[osso]` (clamp 1-50); regista os ossos usados em `h.genoma["ossos"]`
**O que a distingue:** é um **passeio aditivo** (random walk com passos fixos e nomeados), não amostragem direta — nenhuma outra raça faz isto
**Hipótese que testa:** *"um passeio aditivo com passos narrativamente motivados produz uma distribuição diferente de amostragem uniforme?"*
**Evidência:** `archetypes.py:174-192`

---
**Nome:** Elfo
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** **rejection sampling / filtragem combinatória** — gera até 1000 chaves aleatórias e só aceita a primeira que respeita soma∈[100,170], paridade∈{2,3}, baixos∈{2,3}, maior gap≤20
**Como gera a chave:** `for _ in range(1000): amostra; testa 4 critérios; aceita a primeira válida`
**O que a distingue:** é o único com um **orçamento de tentativas explícito e critérios múltiplos simultâneos** — mais próximo de "constraint satisfaction" do que qualquer outra raça
**Hipótese que testa:** *"impor múltiplas restrições estatísticas simultâneas (soma+paridade+baixos/altos+gaps) produz chaves com comportamento diferente de amostragem livre?"*
**Evidência:** `archetypes.py:194-206`

---
**Nome:** Goblin
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** condicional ao jackpot — se `jackpot≥100M`, injeta 3 números altos (35-50) além dos 5 aleatórios
**Como gera a chave:** amostragem uniforme pura, exceto o bónus de "números altos" quando o jackpot é grande
**O que a distingue:** único cuja estratégia depende de um **valor de mundo externo** (`mundo['jackpot']`), não de estatística histórica nem de genoma
**Hipótese que testa:** *"jackpots grandes (mais jogadores, mais 'ganância' narrativa) devem favorecer números altos?"*
**Evidência:** `archetypes.py:208-215`

---
**Nome:** Shaman
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL — **achado novo, não documentado antes em CLAUDE.md nem em nenhum audit anterior**
**Estratégia:** **nenhuma estratégia própria** — cai no ramo `else` final (deslocamento por fase lunar do último sorteio), exatamente como qualquer raça sem `if raca == "Shaman":` dedicado
**Como gera a chave:** `deslocamento = tabela_fase_lua[mundo['fase_lua']]`; `nums = [n+deslocamento for n in hist[-1]['numeros']]` (clamp 1-50); estrelas: ±1 conforme sinal do deslocamento
**O que a distingue:** **é quase totalmente determinístico por run** — para uma fase lunar e um último sorteio fixos (que não mudam durante um run), TODOS os Shamans produzem a mesma chave. Isto explica exatamente o achado da Baseline dos Clérigos (Shaman: 144.077 candidatas, só **5** chaves únicas — correspondendo às ≤5 fases lunares distintas observadas nos 5 targets da campanha)
**Hipótese que testa:** ⚠️ **INFERÊNCIA, não facto de código** — é plausível que Shaman funcione deliberadamente como "grupo de controlo" (a única raça sem inteligência própria, para comparar as outras contra o acaso estrutural), mas **não há nenhum comentário ou commit que confirme esta intenção**. Confirmado apenas que, faticamente, não tem branch — o resto é inferência.
**Evidência:** `archetypes.py:217-237` (ausência do branch); `racas/antigas.py` (commit `756c63e6`) já tinha `RACAS` incluindo "Shaman" sem `if raca=="Shaman"` correspondente — **este comportamento existe desde o commit mais antigo disponível, nunca foi diferente**

---
**Nome:** Esqueleto
**Facção:** Clérigos (delega para a facção standalone)
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** janela móvel — escolhe um sub-intervalo aleatório de largura configurável (25 números, 6 estrelas por omissão) dentro do universo total, amostra 5/2 desse sub-intervalo
**Como gera a chave:** `start = rng.randint(1, 50-largura+1)`; `sample(range(start,start+largura), 5)`
**O que a distingue:** único com o conceito explícito de "janela deslizante sobre o universo" como restrição de amostragem
**Hipótese que testa:** *"restringir o espaço de amostragem a uma janela contígua aleatória produz comportamento diferente de amostrar o universo inteiro?"*
**Evidência:** `factions/skeletons/algorithm.py:1-27`; referenciado como `racas.esqueletos` já em `racas/antigas.py` (V8)

---
**Nome:** Cronomante
**Facção:** Clérigos (delega) + facção standalone
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** **energia temporal determinística** — deriva números de `segundo + (milissegundo%100) + idade_lua + índice*3` de cada evento real de extração de bola
**Como gera a chave:** sem eventos → fallback aleatório puro; com eventos → `int(energia % 50) + 1` por número
**O que a distingue:** único totalmente ancorado em **timestamps físicos simulados da extração**, não em estatística histórica nem em genoma
**Hipótese que testa:** *"a microestrutura temporal do próprio sorteio (quando cada bola saiu, ao segundo/milissegundo) contém sinal recuperável?"*
**Evidência:** `factions/chronomancers/algorithm.py`; `racas/cronomantes` já referenciado em `racas/antigas.py` (V8)

---
**Nome:** Minotauro
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT (Commit 19, `77b69b9`)
**Estratégia:** **persistência/herança de chave** — sobreviventes repetem exatamente a última chave; fundadores herdam a chave de um progenitor Minotauro elegível (p1 tem precedência) ou geram uma nova aleatória
**Como gera a chave:** `if h.keys: return h.keys[-1]` — nunca recalcula
**O que a distingue:** é a **única raça sem geração ativa** — a "estratégia" é não gerar, apenas reter. Nunca passa por `aplicar_conhecimento()`.
**Hipótese que testa:** *"manter uma chave estável ao longo de gerações (em vez de reamostrar sempre) produz comportamento mensuravelmente diferente das raças exploratórias?"* — confirmado empiricamente na Baseline: `repeat_rate≈0.999` em todas as gerações testadas (G20/G100/G520)
**Evidência:** `archetypes.py:111-120`; `tests/test_minotauros.py`

---
**Nome:** Zombie
**Facção:** Clérigos
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT (Commit 26, `71be259`)
**Estratégia:** **território local + Monte Carlo** — nasce com um "território" (pool fixo de 12 números + 5 estrelas), herdável e mutável (deriva mínima, 10%), e explora exaustivamente esse território via Monte Carlo (300 simulações, argmax de `fitness()`)
**Como gera a chave:** amostra 300× dentro do território próprio, guarda o melhor por `fitness()` (a mesma função dos Lobisomens)
**O que a distingue:** único que combina **restrição espacial local herdável** com otimização Monte Carlo — nem os Lobisomens (Monte Carlo sobre o universo inteiro) nem o Minotauro (persistência sem otimização) fazem as duas coisas
**Hipótese que testa:** *"restringir a busca Monte Carlo a um território pequeno e hereditário converge para melhores resultados locais, à custa de diversidade global?"* — confirmado na Baseline: `repeat_rate` sobe com gerações (0.28→0.47→0.62, G20→G100→G520), exatamente o comportamento esperado de convergência territorial
**Evidência:** `archetypes.py:16-131`; `tests/test_minotauros.py`/testes Zombie dedicados (Commit 26)

---

### 🧬 MELFORKS — `factions/melforks/algorithm.py`

**Nome:** Melforks (raça única, sem sub-linhagens)
**Facção:** Melforks
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT (idêntico desde V8, `racas/extras.py:melforks()`)
**Estratégia:** **algoritmo genético completo e independente** — população→fitness→elite→crossover (união de genes dos pais)→N gerações
**Como gera a chave:** `pop=[amostra aleatória]*tam`; a cada geração: `elite=top-k por fitness`; `filho = amostra(pai1∪pai2)`
**O que a distingue:** **segundo e único outro GA do projeto** além dos Clérigos — mas muito mais simples (sem raças, sem persistência, sem mutação explícita, crossover por união em vez de cruzamento posicional)
**Hipótese que testa:** *"um GA genérico e minimalista (sem lore/raças) converge de forma diferente do GA elaborado dos Clérigos?"*
**Curiosidade não corrigida**: os representantes finais são rotulados internamente `f'Clérigo-{i+1}'` (não `'Melfork-{i+1}'`) — resíduo de copy-paste presente desde V8, `tipo` continua correto (`'Melfork'`), só o `nome` está errado
**Evidência:** `factions/melforks/algorithm.py:6-23`; `racas/extras.py:melforks()` (`756c63e6`)

---

### 🩸 VAMPIROS — `factions/vampires/algorithm.py`

**Nome:** Linhagem Sanguínea (Conde Vaelor)
**Facção:** Vampiros
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT (idêntico byte-a-byte desde V8, só PT→EN)
**Estratégia:** **procura triplas frequentes** — lê `triplas_mais_comuns` de `library/indexes/triplas.json` diretamente (bypassa Ariadne), escolhe uma tripla e completa até 5 números
**Hipótese que testa:** *"ancorar a chave numa tripla historicamente frequente produz resultado diferente de não ancorar?"*
**Evidência:** `factions/vampires/algorithm.py:19-31`; `vampiros/linhagens.py:linhagem_sanguinea()` (`756c63e6`)

**Nome:** Linhagem Sombria (Lady Nyx)
**Facção:** Vampiros
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT (idêntico desde V8)
**Estratégia:** **procura triplas consecutivas** (`triplas_consecutivas`, fallback para as mais comuns)
**O que distingue as 2 linhagens:** comum-vs-consecutiva — mesma fonte de dados, filtro diferente
**Hipótese que testa:** *"triplas de números consecutivos (16-17-18) comportam-se de forma diferente de triplas frequentes não-consecutivas?"*
**Evidência:** `factions/vampires/algorithm.py:34-46`

---

### 🗿 GÁRGULAS — `factions/gargoyles/algorithm.py`

**Nome:** Linhagem de Pedra (Gorath)
**Facção:** Gárgulas
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT (idêntico desde V8)
**Estratégia:** **procura duplas frequentes** (`duplas_mais_comuns` de `duplas.json`, ficheiro direto)
**Hipótese que testa:** análogo às triplas dos Vampiros, mas com pares — *"o efeito de ancorar numa dupla é mais fraco/mais forte que ancorar numa tripla?"*
**Evidência:** `factions/gargoyles/algorithm.py:19-30`

**Nome:** Linhagem do Espelho (Seraphine)
**Facção:** Gárgulas
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** **duplas consecutivas** (`duplas_consecutivas`, fallback comuns) — "relações simétricas"
**Evidência:** `factions/gargoyles/algorithm.py:33-44`

---

### 🌳 TREEFOLKS — `factions/treefolks/algorithm.py`

**Nome:** Raiz-N (só um arquétipo, instanciado N vezes)
**Facção:** Treefolks
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** heurística de pontuação ponderada — `.45*freq_norm + .35*atraso_norm + .2*random()` por número; **"modelo" ML é só um rótulo narrativo sorteado**
**⚠️ Achado explicitamente pedido — redes neuronais**: `'modelo': random.choice(['Random Forest','Rede Neural','LSTM','Bayesiano'])` **nunca corresponde a um modelo real**. Nenhuma dependência de ML (numpy/sklearn/tensorflow) existe em código nem em qualquer commit de qualquer branch — busca exaustiva confirmou isto. A string "Rede Neural" já existia no commit mais antigo disponível (`756c63e6`). **CONFIRMADO NO HISTÓRICO GIT que nunca houve implementação real — a memória do utilizador está correta sobre a existência do rótulo, mas o rótulo nunca foi acompanhado de código de ML.**
**Hipótese que testa (a genuína, por trás do teatro do "modelo")**: *"uma pontuação combinando frequência+atraso+ruído aleatório produz melhor cobertura que qualquer um dos três sozinho?"*
**Evidência:** `factions/treefolks/algorithm.py:1-24`; `racas/extras.py:treefolks()` (`756c63e6`)

---

### 🔮 KORS DE ELARION — `factions/kors/{white,red,green,black}.py`

**Nome:** Aelyra dos Silêncios (Kor Branco)
**Estratégia:** **seleciona números atrasados** — `ariadne.overdue_numbers(15)`, amostragem ponderada pelo atraso
**Hipótese:** *"números atrasados há mais tempo têm maior probabilidade de 'despertar'"*

**Nome:** Kael da Chama Fria (Kor Vermelho)
**Estratégia:** **frequências raras** — `ariadne.least_frequent_numbers(20)`, ponderação inversa à frequência
**Hipótese:** *"o raramente convocado guarda tensão de reaparecer"*
**Nota de VERIFIED**: este é o único dos 4 Kors comprovadamente **impossível de certificar temporalmente** (Commit 23: `least_frequent_numbers()` levanta `RuntimeError` em modo temporal)

**Nome:** Sylvara das Passagens (Kor Verde)
**Estratégia:** **padrão de transição** entre os 2 últimos sorteios — números "chegados" (novos) + 1-2 "persistentes" + vizinhos adjacentes (±1) dos chegados
**Hipótese:** *"o que mudou entre o penúltimo e o último sorteio prediz o próximo?"*

**Nome:** Nyxara das Sombras Semanais (Kor Preto)
**Estratégia:** **ecos semanais** — `ariadne.weekly_echoes(semana_iso)`, frequência ponderada sobre todos os sorteios históricos da mesma semana ISO em todos os anos; **grava papiro em disco** (única persistência real entre os Kors)
**Hipótese:** *"a mesma semana do calendário, através dos anos, ressoa um padrão?"*

**Estado (4/4):** ✅ CONFIRMADO NO CÓDIGO ATUAL, idênticos desde V8 (`faccoes/kors/{branco,vermelho,verde,preto}.py`).

---

### 🗺️ CARTÓGRAFOS DO CAOS — `factions/chaos_cartographers/*.py` (analítico, não gera chave)

| Cartógrafo | Estratégia concreta |
|---|---|
| Eldran das Constelações | **rede de coocorrência + centralidade de grau** entre números (par a par, em cada sorteio) — o mais próximo de "clustering"/análise de grafo no projeto inteiro |
| Vesara dos Intervalos | atraso médio/máx/mín/variância por número (estatística de ciclos) |
| Lirien das Correntes | tendência por **janelas** de 50/100/200 sorteios vs. média histórica |
| Thalvos do Acaso Esperado | **Monte Carlo genuíno, 100.000 simulações** — compara distribuição real vs. esperada sob aleatoriedade pura |
| Oryn dos Ecos Sequenciais | **cadeia de Markov real** (transições sorteio→sorteio seguinte) + vizinhança intra-sorteio + sequências consecutivas |

**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL, idênticos desde V8. **Nenhum gera `CandidateKey`** (`votes:false`).

---

### 🧮 AXIOMANTES DE NEMERION

**Nome:** Axiomantes (raça única)
**Estratégia:** **Feistel determinístico** — rank/unrank combinatório + permutação de 4 rondas sobre 139.838.160 posições; caminha sequencialmente a partir de um ponto-âncora, sem amostragem probabilística nenhuma
**RNG:** **nenhum** — `seed` é parâmetro estrutural do Feistel, não entropia
**Hipótese:** *"uma bijeção determinística sobre o espaço combinatório completo, ancorada no último sorteio real, revela candidatos com perfil estatístico diferente de amostragem aleatória?"*
**Evidência:** `factions/axiomantes/{labyrinth,profile,ritual}.py`; nasceu em V8.1 (`f79d907a`)

---

### 🪨 ANÕES — `factions/dwarves/algorithm.py`

**Nome:** Barbas de Ferro / Cristal Azul / Forja Negra (3 "clãs")
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** **enumeração combinatória filtrada** — pool reduzido de 20 números (quentes+frios+último sorteio), gera todas as combinações C(20,5), embaralha, aceita as que têm soma∈[85,190]
**⚠️ Nota importante**: os 3 "clãs" **não são 3 estratégias diferentes** — é a mesma função `dwarves()` instanciada 3× com nomes diferentes. Não confundir com Vampiros/Gárgulas, cujas linhagens genuinamente diferem no filtro.
**Hipótese:** *"enumerar exaustivamente (dentro de um pool pequeno) em vez de amostrar diretamente cobre melhor o espaço válido?"*
**Evidência:** `factions/dwarves/algorithm.py`; `racas/extras.py:anoes()` (`756c63e6`)

---

### 🧚 FADAS — `factions/faeries/algorithm.py`

**Nome:** Lunélia-N
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT
**Estratégia:** **amostragem ponderada** (`random.choices` com pesos combinando proximidade ao centro 25.5, atraso, frequência e "números do quotidiano" configuráveis pelo utilizador), até 2000 tentativas para satisfazer critérios narrativos (paridade, baixo+alto, sobreposição com quentes/frios)
**Hipótese:** *"pesos combinando 4 sinais diferentes + números pessoais do utilizador produzem melhor cobertura que 1 sinal só?"*
**Evidência:** `factions/faeries/algorithm.py`; `racas/extras.py:fadas()`

---

### 🐺 LOBISOMENS — `factions/werewolves/algorithm.py`

**Nome:** Fenrir-N
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL / HISTÓRICO GIT, **mas nunca executado num run real** (achado do audit anterior — `origem="lobisomem"` tem 0 ocorrências em 42.527 registos reais)
**Estratégia:** **Monte Carlo puro** — 30.000 simulações (config real), heap top-100 por `fitness()`, só ativo em semana de lua cheia
**Hipótese:** *"Monte Carlo sem restrição nenhuma (universo inteiro) e sem território, só otimizando por fitness, produz melhores candidatos que amostragem única?"*
**Evidência:** `factions/werewolves/algorithm.py`; `racas/extras.py:lobisomens()`

---

### 🖤 ESQUADRÃO NEGRO — `orders/black_squad/`

**Nome:** Magos Negros (sem nomes individuais fixos no código lido)
**Estado:** ✅ CONFIRMADO NO CÓDIGO ATUAL
**Estratégia:** **anti-popularidade + memória persistente (grimório roubado)** + **diversificação gulosa por distância de conjunto simétrico** (`|A△B|`, greedy max-min, primeira vez documentada com este nome)
**Persistência:** Grimório sem timestamp — "irremediavelmente legado" (Commit 21/24), nunca poderá ser VERIFIED
**Hipótese:** *"penalizar explicitamente números populares (evitar partilhar prémio) produz um perfil de chave mensuravelmente diferente?"*
**Evidência:** `orders/black_squad/strategies.py`

---

### 🧝 ORDEM ÉLFICA — `orders/elven_order/`

**Estado:** ACTIVE, **não gera chave própria** — recuperação/purificação de missões, não uma estratégia de geração
**Evidência:** `orders/elven_order/ninjas.py`

---

### 👑 PANTHEON (Magos / Druidas-Panteão / Djinns / Aion)

Ver auditoria anterior desta mesma conversa para o detalhe completo — resumo aqui:
- **Magos, Druidas (Panteão, distintos dos Mystics), Djinns**: ✅ CONFIRMADO, idênticos desde V8 (`racas/extras.py:superiores()`), só RNG retrofit em V10.5. Estratégias: atrasados+quentes (Magos), quentes puro (Druidas), perturbação do último sorteio (Djinns). **Indistinguíveis no `CandidateKey`** — todos registados sob `origem="ser_superior"`.
- **Aion**: agregador determinístico (Counter sobre as chaves dos 3 anteriores), `origem="deus"`, distinguível.

---

### 🦴 BONE READERS

**Estado:** DOCUMENTADO/LORE, MAS IMPLEMENTAÇÃO NÃO ENCONTRADA — **nunca existiu, em nenhum commit de nenhuma branch**, uma versão com algoritmo real. Nasceu já placeholder em V10.
**Estratégia:** nenhuma — `return []` sempre
**Hipótese planeada (nunca implementada)**: gerador ritual pseudo-aleatório, "ritual seeds", combinações simbólicas (texto do próprio `council.py`)

---

## Resumo dos 4 rótulos de evidência aplicados

- **CONFIRMADO NO CÓDIGO ATUAL**: 10 raças de Clérigos, 2+2 linhagens Vampiros/Gárgulas, Melforks, Treefolks, 4 Kors, 5 Cartógrafos, Axiomantes, Anões, Fadas, Lobisomens, Esquadrão Negro, Magos/Druidas/Djinns/Aion.
- **CONFIRMADO NO HISTÓRICO GIT** (idêntico ou quase-idêntico desde V8, o commit mais antigo disponível): todos os acima, exceto Minotauro (V11) e Zombie (V26), que só existem no `main`.
- **DOCUMENTADO/LORE, SEM IMPLEMENTAÇÃO**: Bone Readers e os restantes 7 Mystics placeholders (Druids-Mystics, Moon Priests, Star Gazers, Oracles, Seers, Shamans-Mystics, Witches).
- **INFERÊNCIA (nunca facto)**: a única usada foi sobre Shaman-Clérigo poder ser um "grupo de controlo" deliberado — sinalizada explicitamente como tal, não como conclusão.

## Raças que desapareceram completamente

**Nenhuma foi encontrada.** Verificado especificamente: (a) `RACAS` dos Clérigos só cresceu, nunca encolheu, em toda a história `main`; (b) as 2 linhagens de Vampiros e as 2 de Gárgulas são idênticas, nome a nome, desde V8; (c) nenhum diretório de facção existente em V8 (`gargulas/`, `vampiros/`, `treefolks/`, `faccoes/kors/`, `faccoes/cartografos_caos/`, `racas/extras.py`) foi apagado sem sucessor — todos migraram, nunca desapareceram. Isto cobre tudo o que a arqueologia Git disponível (V8→hoje) consegue provar; **não é prova sobre V1-V7**, que não existem em Git nem em lado nenhum verificável.
