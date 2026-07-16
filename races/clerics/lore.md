# Clérigos — Lore

> Este documento expande a história da raça dos Clérigos dentro do universo de Project Ariadne. Como em todo o projecto: **os padrões narrados aqui não aumentam a probabilidade matemática de prever um sorteio futuro.**

## História

Os Clérigos são a mais antiga metodologia do Grande Conselho — a única que remonta à Era I, quando Bruxas, Videntes, Chefes Tribais, Elfos, Goblins e Shamans começaram a gerar chaves com estratégias diferentes, antes de o Conselho sequer existir como instituição formal. Essas seis linhagens tornaram-se, na Era II — A Evolução Genética, a base racial de um único povo: os Clérigos, cuja população passou a nascer, cruzar genes, competir, sobreviver e deixar descendência.

Não são uma raça no sentido convencional — são uma população evolutiva. Cada Clérigo nasce com uma das oito linhagens ancestrais, e a cada geração do Conselho, os melhores cruzam-se, os piores são eliminados ou seguem o Caminho das 1000 Almas, e uma nova geração nasce das cinzas da anterior.

## Homeland

O **Templo dos Clérigos** não é apenas uma morada — é onde a Ritual Celeste acontece, onde as almas dos Clérigos eliminados ou ressuscitados doam energia proporcional ao seu score, título e amuletos, produzindo a "Escolha Humana Consagrada pelos Clérigos" que o Conselho também considera.

## Filosofia Evolutiva

Um Clérigo não escolhe uma chave — herda-a, de uma entre oito linhagens ancestrais, e refina-a através de gerações. "Não há uma verdade única," dizem no Templo, "há apenas sobrevivência: quem pontua bem cruza-se, quem pontua mal cai — e mesmo os que caem podem regressar pelo Caminho das 1000 Almas." Nenhuma outra raça do universo de Ariadne combina tantas estratégias distintas dentro de uma única população evolutiva.

## As Oito Linhagens Ancestrais

Cada Clérigo nasce com uma raça interna (ver `lineages.json`), herdada dos seus pais ou sorteada na criação:

- **Bruxa** — mistura números quentes e frios com um toque de acaso, como quem mistura estratégias alheias num caldeirão pessoal.
- **Vidente** — confia nos números quentes, mas deixa-se influenciar pelo último sorteio quando a "clareza" do seu genoma é alta.
- **Chefe Tribal** — lança símbolos rituais (sol, lua, lobo, fogo, água, montanha, corvo) e deixa-os deslocar um número inicial.
- **Elfo** — procura, por rejeição sistemática, uma combinação que respeite paridade, soma e distribuição de gaps — o mais disciplinado dos oito.
- **Goblin** — aposta em números altos quando o jackpot é generoso, e em qualquer coisa quando não é.
- **Shaman** — segue o deslocamento da fase lunar sobre o último sorteio, um eco direto da filosofia dos Nature Mystics.
- **Cronomante** — reutiliza directamente o algoritmo dos Cronomantes da Ordem do Tempo (`factions/chronomancers/algorithm.py`) para essa instância.
- **Esqueleto** — reutiliza directamente o algoritmo dos Esqueletos das Catacumbas Numéricas (`factions/skeletons/algorithm.py`) para essa instância.

As duas últimas linhagens não têm lógica própria — são um empréstimo directo de outras raças, prova de que mesmo a mais antiga metodologia do Conselho continua a aprender com as mais novas.

## Hierarquia — as Seis Casas

Para além da linhagem ancestral, cada Clérigo pertence a uma de seis Casas: Casa Lunar, Casa dos Ossos, Casa do Caos, Casa das Estrelas, Casa Tribal, Casa do Bosque — herdada de um dos pais, sem relação fixa com a linhagem ancestral. Um Clérigo pode ser, por exemplo, um Vidente da Casa dos Ossos, ou um Elfo da Casa Lunar.

## Personagens Notáveis

Os Clérigos não têm figuras fixas — cada geração recria a população inteira a partir de um conjunto de nomes (Lyra, Morgana, Kael, Gruk, Aruk, Elarion, Selene, Thara, Aion, Velka) e títulos (da Névoa, dos Ossos, da Lua Fria, Pedra-Partida, dos Astros, do Bosque). Ver `characters.json` para os oito arquétipos de linhagem.

## Artefactos

Ver `artifacts.json`. Os Clérigos são a única raça cujos indivíduos de elite podem forjar Amuletos Vivos (`artifacts/living.py`) e cujos eliminados alimentam o Ritual Celeste com energia.

## Relação com o Conselho

Os Clérigos contribuem ao Conselho de duas formas distintas: os finalistas da população (cada um com peso 1.0) e, separadamente, a "Escolha Humana Consagrada pelos Clérigos" produzida pelo Ritual Celeste — uma chave adicional, com peso próprio (`peso_no_conselho`), gerada a partir da energia das almas do Caminho das 1000 Almas.

## Relação com Ariadne e a Biblioteca Eterna

Os Clérigos são a única raça cuja população inteira é arquivada individualmente — `datasets/generated/world_state/populacao_final.json` regista cada indivíduo, a sua linhagem, casa, pontuação e chaves geradas. Ariadne não distingue entre um Clérigo e qualquer outra fonte de conhecimento: regista, sem julgar o método.

## Relação com outras raças

Com os **Melforks**, a relação é de descendência directa — os Melforks são geneticamente cultivados a partir da mesma linhagem clerical, isolados num laboratório para ciclos evolutivos mais rápidos. Os seus representantes chamam-se, não por coincidência, "Clérigo-N".

Com os **Lobisomens de Fenrir**, mantêm a aliança mais concreta do universo: juntos, são as duas únicas forças capazes de purificar uma chave corrompida por Malphas na Guerra do Conselho.

Com os **Cronomantes** e os **Esqueletos**, existe uma relação de empréstimo directo — duas das oito linhagens ancestrais reutilizam os seus algoritmos, sem duplicação de código.

---

**Aviso obrigatório:** como em qualquer facção de Project Ariadne, a metodologia dos Clérigos não aumenta a probabilidade real de prever um sorteio futuro. Esta raça existe para explorar a narrativa e a estatística histórica do Euromilhões — nunca para prever.
