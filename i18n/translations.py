"""
Traduções do simulador — suporta os 9 países participantes do Euromilhões.

Códigos suportados:
  pt  — Português   (Portugal 🇵🇹)
  es  — Español     (España 🇪🇸)
  fr  — Français    (France 🇫🇷 · Belgique 🇧🇪 · Luxembourg 🇱🇺 · Suisse 🇨🇭)
  nl  — Nederlands  (België 🇧🇪)
  de  — Deutsch     (Österreich 🇦🇹 · Schweiz 🇨🇭 · Luxemburg 🇱🇺)
  en  — English     (UK 🇬🇧 · Ireland 🇮🇪)
  gb  — alias de en

Nomes do universo narrativo (facções, personagens, lugares) não são traduzidos —
são nomes próprios ficcionais.
"""

_T = {
    # ------------------------------------------------------------------ pt
    'pt': {
        # Axiomantes — veredictos
        'veredicto_acaso':   'COMPATÍVEL COM O ACASO',
        'veredicto_ligeiro': 'LIGEIRAMENTE ACIMA DO ESPERADO',
        'veredicto_desvio':  'DESVIO POSITIVO SIGNIFICATIVO',
        'veredicto_abaixo':  'ABAIXO DO ESPERADO',

        # Axiomantes — portal
        'portal_aberto':          'ABERTO',
        'portal_fechado':         'FECHADO',
        'portal_aberto_msg':      'Portal ABERTO',
        'portal_fechado_msg':     'Portal fechado (abstêm-se)',

        # Axiomantes — aviso obrigatório
        'aviso': (
            "A posição de uma chave numa permutação pseudoaleatória não altera "
            "a sua probabilidade real. Uma taxa de cobertura >= 50% é esperada "
            "quando se percorre >= 50% do universo. O perfil dos Ecos reflecte "
            "regularidades do passado que não têm poder preditivo matemático."
        ),

        # main.py
        'simulacao_concluida': 'Simulação concluída.',
        'semente':             'Semente do universo',
        'chave_original':      'Chave original',
        'chave_corrompida':    'Chave corrompida',
        'relatorio':           'Relatório',
        'individuos_unicos':   'Indivíduos únicos',
        'registos_externos':   'Registos externos',
        'livros_proibidos':    'Livros proibidos',
        'reliquias':           'Relíquias persistentes',
        'magos_negros':        'Magos Negros',
        'missoes_elficas':     'Missões Élficas',
        'esqueletos':          'Esqueletos',
        'invocacoes':          'Invocações sombrias',
        'kors':                'Kors de Elarion',
        'cartografos':         'Cartógrafos do Caos',
        'livros_label':        'Livros',
    },

    # ------------------------------------------------------------------ es
    'es': {
        'veredicto_acaso':   'COMPATIBLE CON EL AZAR',
        'veredicto_ligeiro': 'LIGERAMENTE POR ENCIMA DE LO ESPERADO',
        'veredicto_desvio':  'DESVIACIÓN POSITIVA SIGNIFICATIVA',
        'veredicto_abaixo':  'POR DEBAJO DE LO ESPERADO',

        'portal_aberto':      'ABIERTO',
        'portal_fechado':     'CERRADO',
        'portal_aberto_msg':  'Portal ABIERTO',
        'portal_fechado_msg': 'Portal cerrado (se abstienen)',

        'aviso': (
            "La posición de una combinación en una permutación pseudoaleatoria no altera "
            "su probabilidad real. Una tasa de cobertura >= 50% es esperada cuando se "
            "recorre >= 50% del universo. El perfil de los Ecos refleja regularidades "
            "del pasado sin poder predictivo matemático."
        ),

        'simulacao_concluida': 'Simulación completada.',
        'semente':             'Semilla del universo',
        'chave_original':      'Combinación original',
        'chave_corrompida':    'Combinación corrompida',
        'relatorio':           'Informe',
        'individuos_unicos':   'Individuos únicos',
        'registos_externos':   'Registros externos',
        'livros_proibidos':    'Libros prohibidos',
        'reliquias':           'Reliquias persistentes',
        'magos_negros':        'Magos Negros',
        'missoes_elficas':     'Misiones Élficas',
        'esqueletos':          'Esqueletos',
        'invocacoes':          'Invocaciones oscuras',
        'kors':                'Kors de Elarion',
        'cartografos':         'Cartógrafos del Caos',
        'livros_label':        'Libros',
    },

    # ------------------------------------------------------------------ fr
    'fr': {
        'veredicto_acaso':   "COMPATIBLE AVEC LE HASARD",
        'veredicto_ligeiro': "LÉGÈREMENT AU-DESSUS DE L'ATTENDU",
        'veredicto_desvio':  'ÉCART POSITIF SIGNIFICATIF',
        'veredicto_abaixo':  "EN DESSOUS DE L'ATTENDU",

        'portal_aberto':      'OUVERT',
        'portal_fechado':     'FERMÉ',
        'portal_aberto_msg':  'Portail OUVERT',
        'portal_fechado_msg': "Portail fermé (s'abstiennent)",

        'aviso': (
            "La position d'une combinaison dans une permutation pseudoaléatoire n'altère pas "
            "sa probabilité réelle. Un taux de couverture >= 50% est attendu lorsqu'on "
            "parcourt >= 50% de l'univers. Le profil des Échos reflète des régularités "
            "du passé sans pouvoir prédictif mathématique."
        ),

        'simulacao_concluida': 'Simulation terminée.',
        'semente':             "Graine de l'univers",
        'chave_original':      'Combinaison originale',
        'chave_corrompida':    'Combinaison corrompue',
        'relatorio':           'Rapport',
        'individuos_unicos':   'Individus uniques',
        'registos_externos':   'Enregistrements externes',
        'livros_proibidos':    'Livres interdits',
        'reliquias':           'Reliques persistantes',
        'magos_negros':        'Mages Noirs',
        'missoes_elficas':     'Missions Elfiques',
        'esqueletos':          'Squelettes',
        'invocacoes':          'Invocations sombres',
        'kors':                'Kors de Elarion',
        'cartografos':         'Cartographes du Chaos',
        'livros_label':        'Livres',
    },

    # ------------------------------------------------------------------ nl
    'nl': {
        'veredicto_acaso':   'VERENIGBAAR MET TOEVAL',
        'veredicto_ligeiro': 'IETS BOVEN HET VERWACHTE',
        'veredicto_desvio':  'SIGNIFICANTE POSITIEVE AFWIJKING',
        'veredicto_abaixo':  'ONDER HET VERWACHTE',

        'portal_aberto':      'OPEN',
        'portal_fechado':     'GESLOTEN',
        'portal_aberto_msg':  'Portaal OPEN',
        'portal_fechado_msg': 'Portaal gesloten (onthouden zich)',

        'aviso': (
            "De positie van een combinatie in een pseudo-willekeurige permutatie verandert "
            "de werkelijke kans niet. Een dekkingsgraad >= 50% is te verwachten wanneer "
            ">= 50% van het universum is doorkruist. Het profiel van de Echo's weerspiegelt "
            "verleden patronen zonder wiskundig voorspellend vermogen."
        ),

        'simulacao_concluida': 'Simulatie voltooid.',
        'semente':             'Universum zaad',
        'chave_original':      'Originele combinatie',
        'chave_corrompida':    'Gecorrumpeerde combinatie',
        'relatorio':           'Rapport',
        'individuos_unicos':   'Unieke individuen',
        'registos_externos':   'Externe records',
        'livros_proibidos':    'Verboden boeken',
        'reliquias':           'Persistente relikwieën',
        'magos_negros':        'Zwarte Magiërs',
        'missoes_elficas':     'Elfenmissies',
        'esqueletos':          'Skeletten',
        'invocacoes':          'Duistere aanroepingen',
        'kors':                'Kors van Elarion',
        'cartografos':         'Cartografen van de Chaos',
        'livros_label':        'Boeken',
    },

    # ------------------------------------------------------------------ de
    'de': {
        'veredicto_acaso':   'VEREINBAR MIT DEM ZUFALL',
        'veredicto_ligeiro': 'LEICHT ÜBER DEM ERWARTETEN',
        'veredicto_desvio':  'SIGNIFIKANTE POSITIVE ABWEICHUNG',
        'veredicto_abaixo':  'UNTER DEM ERWARTETEN',

        'portal_aberto':      'GEÖFFNET',
        'portal_fechado':     'GESCHLOSSEN',
        'portal_aberto_msg':  'Portal GEÖFFNET',
        'portal_fechado_msg': 'Portal geschlossen (enthalten sich)',

        'aviso': (
            "Die Position einer Kombination in einer pseudozufälligen Permutation ändert "
            "ihre tatsächliche Wahrscheinlichkeit nicht. Eine Abdeckungsrate >= 50% ist "
            "zu erwarten, wenn >= 50% des Universums durchquert wurde. Das Echo-Profil "
            "spiegelt vergangene Muster ohne mathematische Vorhersagekraft wider."
        ),

        'simulacao_concluida': 'Simulation abgeschlossen.',
        'semente':             'Universum-Samen',
        'chave_original':      'Originale Kombination',
        'chave_corrompida':    'Korrumpierte Kombination',
        'relatorio':           'Bericht',
        'individuos_unicos':   'Einzigartige Individuen',
        'registos_externos':   'Externe Datensätze',
        'livros_proibidos':    'Verbotene Bücher',
        'reliquias':           'Persistente Reliquien',
        'magos_negros':        'Schwarze Magier',
        'missoes_elficas':     'Elfenmissionen',
        'esqueletos':          'Skelette',
        'invocacoes':          'Dunkle Beschwörungen',
        'kors':                'Kors von Elarion',
        'cartografos':         'Kartographen des Chaos',
        'livros_label':        'Bücher',
    },

    # ------------------------------------------------------------------ en  (also: gb)
    'en': {
        'veredicto_acaso':   'COMPATIBLE WITH CHANCE',
        'veredicto_ligeiro': 'SLIGHTLY ABOVE EXPECTED',
        'veredicto_desvio':  'SIGNIFICANT POSITIVE DEVIATION',
        'veredicto_abaixo':  'BELOW EXPECTED',

        'portal_aberto':      'OPEN',
        'portal_fechado':     'CLOSED',
        'portal_aberto_msg':  'Portal OPEN',
        'portal_fechado_msg': 'Portal closed (abstain)',

        'aviso': (
            "The position of a combination in a pseudorandom permutation does not alter "
            "its real probability. A coverage rate >= 50% is expected when >= 50% of the "
            "universe has been traversed. The Echo Profile reflects past regularities "
            "with no mathematical predictive power."
        ),

        'simulacao_concluida': 'Simulation complete.',
        'semente':             'Universe seed',
        'chave_original':      'Original key',
        'chave_corrompida':    'Corrupted key',
        'relatorio':           'Report',
        'individuos_unicos':   'Unique individuals',
        'registos_externos':   'External records',
        'livros_proibidos':    'Forbidden books',
        'reliquias':           'Persistent relics',
        'magos_negros':        'Black Mages',
        'missoes_elficas':     'Elven missions',
        'esqueletos':          'Skeletons',
        'invocacoes':          'Dark invocations',
        'kors':                'Kors of Elarion',
        'cartografos':         'Cartographers of Chaos',
        'livros_label':        'Books',
    },
}

# gb é alias de en
_T['gb'] = _T['en']

CODIGOS_VALIDOS = frozenset(_T)


def t(key, lang='pt'):
    """
    Devolve a string traduzida para lang.
    Fallback: tenta 'pt'; se a chave não existir em lado nenhum, devolve a própria chave.
    """
    idioma = _T.get(lang) or _T['pt']
    return idioma.get(key) or _T['pt'].get(key, key)


def lang_de_cfg(cfg):
    """Lê o lang do ConfigParser; normaliza para minúsculas; fallback 'pt'."""
    if cfg is None:
        return 'pt'
    raw = cfg.get('MUNDO', 'lang', fallback='pt').strip().lower()
    return raw if raw in CODIGOS_VALIDOS else 'pt'
