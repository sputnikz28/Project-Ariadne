# Timeline — Project Ariadne

The official chronology. Every race's `lore.md` should reference an Era id from this document rather than inventing its own dates or sequence. Source: `HISTORIA_DO_PROJECTO.md` (V1–V7) reconciled with `CLAUDE.md` (V7.2–V10.5).

---

## Era I — `era:v1` — Os Primeiros Oráculos

*(Also known in-universe as the "Era dos Primeiros Oráculos" — the origin era named in `docs/lore/legends/ecos_ancestrais.json` for `character:iria_da_nevoa_azul`.)*

Bruxas, Videntes, Chefes Tribais, Elfos, Goblins e Shamans começam a gerar chaves com estratégias diferentes — o Conselho ainda não existe como instituição; são só personagens dispersas a tentar dar sentido ao acaso. Estas seis linhagens tornam-se mais tarde a base racial dos Clérigos (`races/legacy.py: RACAS`).

## Era II — `era:v2` — A Evolução Genética

As personagens passam a nascer, cruzar genes, competir, sobreviver e deixar linhagens — nasce o algoritmo genético que ainda hoje gera os Clérigos.

## Era III — `era:v3` — O Mundo Vivo

Entram as fases da Lua, as estações, o jackpot. Chegam os Anões (`race:dwarves`), as Fadas (`race:faeries`), os Lobisomens (`race:werewolves`), os Treefolks (`race:treefolks`), os Melforks (`race:melforks`), e conceitos entretanto retirados do universo activo — Zombies, Aracnomantes — e o Caminho das 1000 Almas (`concept:caminho_das_1000_almas`).

## Era IV — `era:v4` — O Conselho e Malphas

O Conselho passa a escolher uma chave final, e **Malphas, o Quebra-Conselhos** (`entity:malphas`) ganha o poder de a corromper — nasce o antagonista central do universo.

- **IV.1 — Crónicas do Destino:** todas as personagens e todas as chaves passam a ser guardadas.
- **IV.2 — Cronomantes:** o instante simulado da extração torna-se uma variável narrativa; nascem os Cronomantes (`race:chronomancers`).
- **IV.3 — Convergência Celeste:** as almas passam a doar energia proporcional ao score, título, estado e amuletos — nasce o Ritual Celeste.
- **IV.4 — Guerra dos Artefactos:** amuletos vivos, vírus de Malphas e conflitos internos do Conselho.
- **IV.5 — Biblioteca Oculta e Arca Persistente:** livros estatísticos, Monges, Escribas (`order:scribes`) e relíquias que sobrevivem entre universos.

## Era V — `era:v5` — Guerra das Sombras (`event:guerra_das_sombras`)

Nasce uma guerra persistente pelo conhecimento, ainda activa hoje:

- o Esquadrão Negro (`order:black_squad`) cria cópias corrompidas dos livros ("Reflexos Sombrios");
- as relíquias podem ser roubadas;
- o Grimório Negro (`artifact:grimorio_negro`) aprende entre execuções;
- os Ninjas Élficos da Ordem Élfica (`order:elven_order`) recuperam e purificam;
- personagens com 3 números + 2 estrelas entram no Livro das Lendas;
- ecos antigos, como **Íria da Névoa Azul** (`character:iria_da_nevoa_azul`, da Era I), podem ser ressuscitados pelo Esquadrão Negro — não recriados, mas trazidos de volta corrompidos (ex.: "Íria da Névoa Azul Eclipse").

## Era VI — `era:v6` — Crónicas das Eras

A simulação deixa de representar apenas uma linha temporal — uma campanha pode atravessar cinco eras consecutivas. Os Escribas passam a manter inventários, crónicas, biografias, o Museu do Mosteiro e o Atlas do Universo. Os Esqueletos chegam das Catacumbas Numéricas (`race:skeletons`) com a estratégia das janelas móveis, e Malphas passa a executar o Ritual da Convicção Sombria depois de cada Conselho. Ao fim da campanha, as cinco chaves originais formam o Conselho dos Conselhos.

### VI.1 — Painel dos Deuses (`concept:painel_dos_deuses`)

O número de eras passa para `config.txt`. As regras do universo são separadas em perfis, permitindo trocar de realidade sem alterar o código.

## Era VII — `era:v7` — Biblioteca Eterna

A Biblioteca torna-se o centro do universo — Ariadne (`entity:ariadne`) passa a conhecer a localização e integridade de todos os pergaminhos. Os Bibliotecários (`order:librarians`) convertem o dataset real em conhecimento persistente. Chegam os Vampiros (`race:vampires`, Linhagens Sanguínea e Sombria) e as Gárgulas (`race:gargoyles`, Linhagens de Pedra e do Espelho). Os Treefolks passam a consultar Ariadne e a testar hipóteses em vez de declarar previsões.

### VII.2 — Kors de Elarion

Chegam os quatro Kors (`race:kors`) — Branco, Vermelho, Verde e Preto — observadores que nunca leem os datasets directamente, apenas através de Ariadne.

## Era VIII — `era:v8` — Cartógrafos do Caos

Chegam os cinco Cartógrafos do Caos (`race:chaos_cartographers`) — facção puramente analítica, que produz livros mas nunca vota no Conselho.

### VIII.1 — Axiomantes de Nemerion

Chega a ordem mais matematicamente densa do universo: os Axiomantes (`race:axiomantes`), guardiões do Labirinto Combinatório de 139.838.160 câmaras — só falam quando o portal se abre.

## Era IX — `era:v9` — Arquitetura de Plugins

Não é uma era narrativa, mas uma era de fundação: todas as facções migram para o sistema de plugins (`core/registry.py`, `core/plugin_loader.py`). Nenhuma alteração a `main.py` volta a ser necessária para adicionar uma facção nova.

## Era X — `era:v10` — Mystics

Regressa o espírito da Era I — chegam os Mystics (`race:mystics`): Nature Mystics (Druids, Moon Priests, Star Gazers) e Prophecy Mystics (Shamans, Witches, Seers, Oracles, Bone Readers). Ainda placeholders sem algoritmo, mas com assento pleno no Conselho desde o primeiro dia.

## Era X.5 — `era:v10_5` — Architecture Complete

Era de consolidação, não de expansão narrativa: `races/` torna-se documentação pura (com a única excepção deliberada de `races/legacy.py`, aguardando a migração dos Clérigos). O Panteão (`order:pantheon`) é reorganizado numa única estrutura coerente em vez de disperso por vários plugins. Esta era culmina no presente documento e nos restantes ficheiros de `docs/lore/`.

---

## What comes next (not yet canon — see CLAUDE.md Roadmap)

**Era XI — V11 (planned):** migração dos Clérigos para `factions/clerics/` + `races/clerics/`; remoção definitiva de `races/legacy.py`; três novas facções (Juízes do Conselho, Geómetras do Véu, Estatísticos Imperiais); `dashboard/`.
