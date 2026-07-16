# Cronomantes da Ordem do Tempo — Lore

> Este documento expande a história da raça dos Cronomantes dentro do universo de Project Ariadne. Como em todo o projecto: **os padrões narrados aqui não aumentam a probabilidade matemática de prever um sorteio futuro.**

## História

Os Cronomantes nasceram na Era IV.2 — Cronomantes, quando o instante simulado da extração se tornou, pela primeira vez, uma variável narrativa por direito próprio. Antes deles, a extração era um evento instantâneo; depois, passou a ter uma cronologia interna — segundos, milissegundos, a idade da lua no momento exacto de cada bola.

## Homeland

A **Ordem do Tempo** não é um lugar no sentido comum — é uma organização que existe, narrativamente, fora da geografia normal do universo, medindo tudo pelo instante em vez do espaço.

## Filosofia

Um Cronomante não olha para o histórico de sorteios — olha para o próprio momento da extração. Cada bola sorteada gera um evento com segundo e milissegundo exactos; um Cronomante soma esses valores à idade da lua e a um índice pessoal, e extrai um número do resultado. "O sorteio não é só o quê," dizem na Ordem, "é também o quando."

## Hierarquia

Cinco Cronomantes nomeados formam o núcleo da Ordem, cada um a um índice diferente da mesma fórmula temporal:

- **Aurel dos Segundos Perdidos**
- **Chrona da Ampulheta Partida**
- **Kairon do Último Instante**
- **Selvar, Guardião do Pulso**
- **Nym do Relógio Lunar**

Nenhum lidera os outros — a Ordem do Tempo não reconhece hierarquia além da ordem de invocação a cada sessão.

## Personagens Notáveis

Ver `characters.json`. Para além dos cinco Cronomantes nomeados, a Ordem está ligada a **Aion**, a entidade agregadora do Panteão — Aion combina as propostas de Magos, Druidas e Djinns numa única chave "Deus", e a sua ligação temática à Ordem do Tempo reflecte-se no facto de o seu código residir junto ao dos Cronomantes (`orders/pantheon/aion.py`, colocado ao lado de `factions/chronomancers/`).

## Artefactos

Ver `artifacts.json`.

## Relação com o Conselho

Os Cronomantes votam com peso 1.0, através da sua própria chave de configuração (`peso_cronomantes`) — um tratamento distinto de todas as outras raças, reflectindo a sua ligação directa ao próprio evento de extração, não apenas ao histórico.

## Relação com outras raças

Com o **Panteão**, através de Aion, mantêm a ligação temática mais forte fora do sistema de votação do Conselho.

Com os **Esqueletos**, partilham um laço estrutural: a `raca` "Cronomante" existe entre os oito arquétipos genéticos dos Clérigos (`races/legacy.py: RACAS`), tal como "Esqueleto" — quando um Clérigo nasce com essa raça interna, herda literalmente o algoritmo dos Cronomantes.

Com os **Axiomantes**, existe um respeito distante — ambas as ordens lidam com precisão extrema (tempo contra combinatória), mas raramente têm motivo para se cruzar directamente.

---

**Aviso obrigatório:** como em qualquer facção de Project Ariadne, a metodologia dos Cronomantes não aumenta a probabilidade real de prever um sorteio futuro. Esta raça existe para explorar a narrativa e a estatística histórica do Euromilhões — nunca para prever.
