"""Configuration centrale du projet Horizon.

Rôle du module : regrouper en un seul endroit les chemins du dépôt, les paramètres
généraux (graine, durée du suivi, seuil d'inactivité) et les valeurs attendues des
fichiers bruts telles que décrites dans data/raw/LISEZMOI.md.
Aucun autre module ne doit contenir de chemin absolu ni de « nombre magique ».

Tâches couvertes : GP-01 (configuration), DA-01 (valeurs attendues pour l'audit).
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins : tous construits à partir de l'emplacement de ce fichier (src/config.py),
# pour que le code fonctionne quel que soit le dossier où le dépôt est cloné
# (Windows chez Saliou, Linux / macOS chez l'enseignant).
# ---------------------------------------------------------------------------
RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_RAW = DOSSIER_DATA / "raw"
DOSSIER_PROCESSED = DOSSIER_DATA / "processed"
FICHIER_SHA256 = DOSSIER_DATA / "raw_sha256.txt"
DOSSIER_DOCS = RACINE / "docs"
DOSSIER_FIGURES = DOSSIER_DOCS / "figures"
FICHIER_AUDIT = DOSSIER_DOCS / "audit_qualite.md"
FICHIER_JOURNAL = DOSSIER_DOCS / "journal_nettoyage.md"

# ---------------------------------------------------------------------------
# Paramètres généraux (CLAUDE.md §5 et §6)
# ---------------------------------------------------------------------------
SEED = 42
N_SEMAINES = 30  # durée du suivi : semaines 1 à 30 depuis la rentrée
SEUIL_INACTIVITE = 4  # semaines consécutives sans connexion ni devoir = décrochage

# Encodage imposé pour lire et écrire tout fichier texte (sinon cp1252 sous Windows).
ENCODAGE = "utf-8"

# ---------------------------------------------------------------------------
# Description des fichiers bruts (LISEZMOI.md, section « Fichiers »)
# ---------------------------------------------------------------------------
# Pour chaque table : nom du fichier, séparateur attendu, nombre de lignes annoncé
# (approximatif, signe « ≈ » dans le LISEZMOI) et colonnes attendues, dans l'ordre
# du dictionnaire des variables.
FICHIERS_BRUTS = {
    "etudiants": {
        "fichier": "etudiants.csv",
        "separateur": ",",
        "lignes_annoncees": 5000,
        "colonnes": [
            "id_etudiant", "cohorte", "genre", "age", "boursier", "filiere",
            "mention_bac", "note_bac", "region_origine", "distance_campus_km",
            "emploi_parallele",
        ],
    },
    "inscriptions": {
        "fichier": "inscriptions.csv",
        "separateur": ";",
        "lignes_annoncees": 5000,
        "colonnes": [
            "id_etudiant", "annee_universitaire", "date_debut", "date_fin", "statut_final",
        ],
    },
    "activite_hebdo": {
        "fichier": "activite_hebdo.csv",
        "separateur": ",",
        "lignes_annoncees": 130000,
        "colonnes": [
            "id_etudiant", "semaine", "nb_connexions_lms", "devoirs_rendus",
            "note_moyenne", "absences",
        ],
    },
    "tutorat": {
        "fichier": "tutorat.csv",
        "separateur": ",",
        "lignes_annoncees": 1300,
        "colonnes": [
            "id_etudiant", "semaine_debut", "nb_seances", "type_tuteur", "motif_orientation",
        ],
    },
    "messages": {
        "fichier": "messages.csv",
        "separateur": ",",
        "lignes_annoncees": 3200,
        "colonnes": ["id_message", "id_etudiant", "semaine", "canal", "texte"],
    },
}

# Séparateurs candidats testés par l'audit pour détecter le séparateur réel.
SEPARATEURS_CANDIDATS = [",", ";", "\t", "|"]

# ---------------------------------------------------------------------------
# Identifiants
# ---------------------------------------------------------------------------
# Format attendu : « HZ » suivi de 5 chiffres (ex. HZ38160).
FORMAT_ID_ETUDIANT = r"HZ\d{5}"
COLONNE_ID = "id_etudiant"

# ---------------------------------------------------------------------------
# Bornes numériques (LISEZMOI, dictionnaire des variables).
# None = pas de borne de ce côté. « strict » = la borne elle-même est interdite
# (distance « > 0 »).
# ---------------------------------------------------------------------------
BORNES = {
    ("etudiants", "age"): {"min": 17, "max": 35, "strict": False},
    ("etudiants", "note_bac"): {"min": 10, "max": 20, "strict": False},
    ("etudiants", "distance_campus_km"): {"min": 0, "max": None, "strict": True},
    ("activite_hebdo", "semaine"): {"min": 1, "max": N_SEMAINES, "strict": False},
    ("activite_hebdo", "devoirs_rendus"): {"min": 0, "max": 2, "strict": False},
    ("activite_hebdo", "note_moyenne"): {"min": 0, "max": 20, "strict": False},
    ("activite_hebdo", "absences"): {"min": 0, "max": 20, "strict": False},
    # Pas de borne haute donnée pour les connexions : seulement « pas de négatif ».
    ("activite_hebdo", "nb_connexions_lms"): {"min": 0, "max": None, "strict": False},
    ("tutorat", "semaine_debut"): {"min": 1, "max": N_SEMAINES, "strict": False},
    # Un étudiant présent dans la table tutorat a suivi au moins une séance.
    ("tutorat", "nb_seances"): {"min": 1, "max": None, "strict": False},
    ("messages", "semaine"): {"min": 1, "max": N_SEMAINES, "strict": False},
}

# Colonnes censées être des nombres entiers (un « 5.0 » ou « 19 ans » est un format à signaler).
COLONNES_ENTIERES = {
    ("etudiants", "cohorte"), ("etudiants", "age"),
    ("activite_hebdo", "semaine"), ("activite_hebdo", "nb_connexions_lms"),
    ("activite_hebdo", "devoirs_rendus"), ("activite_hebdo", "absences"),
    ("tutorat", "semaine_debut"), ("tutorat", "nb_seances"),
    ("messages", "semaine"),
}

# Colonnes qui peuvent être vides sans anomalie (LISEZMOI) : date_fin vide = toujours
# inscrit ; note_moyenne vide = semaine sans évaluation.
VIDES_AUTORISES = {("inscriptions", "date_fin"), ("activite_hebdo", "note_moyenne")}

# Colonnes de dates de la table inscriptions.
COLONNES_DATE = {("inscriptions", "date_debut"), ("inscriptions", "date_fin")}

# Unités parfois écrites dans les champs numériques (ex. « 19 ans », « 9.1 km »).
UNITES_TEXTE = ["ans", "km"]

# Codes souvent utilisés à la place d'une valeur manquante dans les systèmes sources.
VALEURS_SENTINELLES = [-1, 99, 999, 9999]

# Valeurs extrêmes : au-delà de Q3 + COEF_IQR_EXTREMES × IQR (règle de Tukey « très
# éloignée »), une valeur est signalée « à examiner » quand aucune borne haute n'existe.
COEF_IQR_EXTREMES = 3

# ---------------------------------------------------------------------------
# Modalités attendues des variables catégorielles (LISEZMOI).
# Le texte entre parenthèses du LISEZMOI est une explication, pas une modalité.
# ---------------------------------------------------------------------------
REGIONS_SENEGAL = [
    "Dakar", "Diourbel", "Fatick", "Kaffrine", "Kaolack", "Kédougou", "Kolda",
    "Louga", "Matam", "Saint-Louis", "Sédhiou", "Tambacounda", "Thiès", "Ziguinchor",
]

MODALITES = {
    ("etudiants", "cohorte"): ["2024", "2025"],
    ("etudiants", "genre"): ["F", "M"],
    ("etudiants", "boursier"): ["Oui", "Non"],
    ("etudiants", "filiere"): ["Informatique", "Gestion", "Droit", "Génie civil", "Communication"],
    ("etudiants", "mention_bac"): ["Passable", "Assez bien", "Bien", "Très bien"],
    ("etudiants", "region_origine"): REGIONS_SENEGAL,
    ("etudiants", "emploi_parallele"): ["Oui", "Non"],
    ("inscriptions", "annee_universitaire"): ["2024-2025", "2025-2026"],
    ("inscriptions", "statut_final"): ["abandon", "transfert", "inscrit"],
    ("tutorat", "type_tuteur"): ["pair", "enseignant"],
    ("tutorat", "motif_orientation"): [
        "notes faibles", "absences répétées", "signalement enseignant", "demande personnelle",
    ],
    ("messages", "canal"): ["forum", "formulaire de suivi"],
}

# Intervalle de note_bac correspondant à chaque mention (LISEZMOI : Passable 10–12,
# AB 12–14, B 14–16, TB ≥ 16). Les bornes communes (12, 14, 16) sont ambiguës :
# l'audit tolère les deux mentions voisines sur une borne et ne signale que les
# écarts francs.
INTERVALLES_MENTION = {
    "Passable": (10, 12),
    "Assez bien": (12, 14),
    "Bien": (14, 16),
    "Très bien": (16, 20),
}

# ---------------------------------------------------------------------------
# Dates (table inscriptions)
# ---------------------------------------------------------------------------
# Formats numériques reconnus par l'audit (constat de l'hétérogénéité, pas de correction).
FORMATS_DATE = {
    "AAAA-MM-JJ": "%Y-%m-%d",
    "JJ/MM/AAAA": "%d/%m/%Y",
    "AAAA/MM/JJ": "%Y/%m/%d",
}
# Mois abrégés en français (format du type « 6 oct. 2025 »).
MOIS_FR = {
    "janv.": 1, "févr.": 2, "mars": 3, "avr.": 4, "mai": 5, "juin": 6,
    "juil.": 7, "août": 8, "sept.": 9, "oct.": 10, "nov.": 11, "déc.": 12,
}
MOIS_RENTREE = 10  # les rentrées ont lieu en octobre (cahier des charges §4.1)
# Correspondance année universitaire -> cohorte (année de rentrée).
ANNEE_VERS_COHORTE = {"2024-2025": "2024", "2025-2026": "2025"}
JOURS_PAR_SEMAINE = 7

# ---------------------------------------------------------------------------
# Données personnelles dans messages.texte (détection pour l'audit uniquement)
# ---------------------------------------------------------------------------
# Téléphone sénégalais : indicatif +221 / 00221 facultatif, puis 9 chiffres
# commençant par 70, 75, 76, 77 ou 78, avec ou sans séparateurs.
MOTIF_TELEPHONE = r"(?:(?:\+|00)221[\s.-]?)?7[05678](?:[\s.-]?\d){7}"
MOTIF_EMAIL = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
# Nom propre introduit par une formule de présentation (« Je suis Prénom Testnom »,
# « c'est Fatou Exemple », « je m'appelle … », « mon nom est … »).
MOTIF_NOM = (
    r"(?:[Jj]e suis|[Cc]'est|[Jj]e m'appelle|[Mm]on nom est|[Mm]oi c'est)\s+"
    r"(?P<nom>[A-ZÀ-Þ][^\s,.;:!?]*(?:\s+[A-ZÀ-Þ][^\s,.;:!?]*)+)"
)
# Mots qui signalent une adresse postale (le groupe « lieu » est la partie à masquer).
MOTIF_ADRESSE = (
    r"\b(?i:rue|avenue|boulevard|bd|quartier|cité|villa|lot|parcelles|"
    r"résidence|immeuble|appartement)\b\s+(?P<lieu>\S+)"
)
# Mojibake : UTF-8 relu comme Latin-1 (ex. « Ã© » à la place de « é »).
MOTIF_MOJIBAKE = r"Ã[\u0080-¿]|Â[\u0080-¿]"

# Nombre d'exemples affichés par anomalie dans l'audit.
NB_EXEMPLES = 3

# ---------------------------------------------------------------------------
# Nettoyage (DA-02 et suivantes) — règles validées dans docs/decisions.md
# ---------------------------------------------------------------------------
# Séparateur des tables nettoyées écrites dans data/processed/.
SEPARATEUR_PROCESSED = ","

# En-têtes à renommer (après retrait des espaces) pour retrouver le nom du LISEZMOI.
RENOMMAGE_COLONNES = {
    "etudiants": {"Distance campus (km)": "distance_campus_km"},
    "tutorat": {"ID Etudiant": "id_etudiant"},
}

# Abréviations et synonymes reconnus, écrits en FORME SIMPLIFIÉE (minuscules, sans
# accents, tirets remplacés par des espaces). Les modalités officielles elles-mêmes
# (config.MODALITES) sont toujours reconnues sous leur forme simplifiée. (D-06, D-11)
ABREVIATIONS = {
    ("etudiants", "genre"): {
        "femme": "F", "feminin": "F",
        "h": "M", "homme": "M", "masculin": "M",
    },
    ("etudiants", "boursier"): {
        "o": "Oui", "yes": "Oui", "1": "Oui",
        "n": "Non", "no": "Non", "0": "Non",
    },
    ("etudiants", "filiere"): {
        "info": "Informatique", "gc": "Génie civil", "com": "Communication",
    },
    ("etudiants", "mention_bac"): {
        "p": "Passable", "ab": "Assez bien", "b": "Bien", "tb": "Très bien",
    },
    ("etudiants", "region_origine"): {
        "st louis": "Saint-Louis", "zig": "Ziguinchor",
    },
    ("etudiants", "emploi_parallele"): {},
}

# Colonnes numériques de la table etudiants : entières (type entier acceptant les
# manquants) ou décimales.
COLONNES_ENTIERES_ETUDIANTS = ["cohorte", "age"]
COLONNES_DECIMALES_ETUDIANTS = ["note_bac", "distance_campus_km"]

# Seule sentinelle de distance présente dans les données (D-09). 99 et 999 ne sont
# PAS des sentinelles pour la distance : ce seraient des distances plausibles.
SENTINELLE_DISTANCE = 9999

# Colonne sur laquelle deux lignes d'un même étudiant peuvent différer (D-07).
COLONNE_DIFFERENCE_TOLEREE = "distance_campus_km"

# Seuils des mentions du bac (D-10) : note >= seuil -> mention, du plus haut au plus
# bas. Une note de 12 exactement est donc « Assez bien ».
SEUILS_MENTION = [
    (16, "Très bien"),
    (14, "Bien"),
    (12, "Assez bien"),
    (10, "Passable"),
]

# Exemple d'écriture avec unité observé dans chaque colonne (affiché dans le journal).
EXEMPLES_UNITE = {"age": "19 ans", "distance_campus_km": "11.8 km"}

# ---------------------------------------------------------------------------
# Nettoyage de la table inscriptions (DA-03, décisions D-12 à D-17)
# ---------------------------------------------------------------------------
# Écritures du statut reconnues en plus des modalités officielles (forme simplifiée).
ABREVIATIONS[("inscriptions", "statut_final")] = {
    "abandonne": "abandon",
    "transfere": "transfert",
}

# Mois en français, en forme simplifiée (minuscules, sans accents, sans point final),
# abrégés ou complets. Observés : oct., nov., déc., janv., févr., mars, avr.
MOIS_FR_SIMPLIFIES = {
    "janv": 1, "janvier": 1,
    "fev": 2, "fevr": 2, "fevrier": 2,
    "mars": 3,
    "avr": 4, "avril": 4,
    "mai": 5,
    "juin": 6,
    "juil": 7, "juillet": 7,
    "aout": 8,
    "sept": 9, "septembre": 9,
    "oct": 10, "octobre": 10,
    "nov": 11, "novembre": 11,
    "dec": 12, "decembre": 12,
}

# Format d'écriture des dates dans les tables nettoyées.
FORMAT_DATE_PROCESSED = "%Y-%m-%d"

# Valeurs de la colonne dérivée sortie_suivi.
SORTIE_ABANDON = "abandon"
SORTIE_TRANSFERT = "transfert"
SORTIE_AUCUNE = "aucune_sortie_declaree"
VALEURS_SORTIE_SUIVI = [SORTIE_ABANDON, SORTIE_TRANSFERT, SORTIE_AUCUNE]

# Drapeaux de la colonne drapeau_inscription (plusieurs séparés par SEPARATEUR_DRAPEAUX).
DRAPEAU_DATES_INVERSEES = "dates_inversees"
DRAPEAU_ABANDON_HORS_SUIVI = "abandon_hors_suivi"
DRAPEAU_STATUT_VIDE = "statut_vide"
DRAPEAU_ABANDON_SANS_DATE = "abandon_sans_date"
DRAPEAU_INSCRIPTION_RECONSTITUEE = "inscription_reconstituee"
SEPARATEUR_DRAPEAUX = ";"

# Inscriptions sans étudiant correspondant, exclues de l'analyse mais conservées (D-17).
DOSSIER_REJETS = DOSSIER_PROCESSED / "rejets"
FICHIER_REJETS_INSCRIPTIONS = DOSSIER_REJETS / "inscriptions_sans_etudiant.csv"

# ---------------------------------------------------------------------------
# Nettoyage des tables activite_hebdo et tutorat (DA-04, décisions D-19 à D-27)
# ---------------------------------------------------------------------------
# activite_hebdo : colonnes entières (type Int64) et décimale.
COLONNES_ENTIERES_ACTIVITE = ["semaine", "nb_connexions_lms", "devoirs_rendus", "absences"]
COLONNES_DECIMALES_ACTIVITE = ["note_moyenne"]

# Connexions plausibles par semaine : jusqu'à 26 observées, puis rien avant 3 604 (D-19).
CONNEXIONS_MAX_PLAUSIBLE = 100
# Note hebdomadaire codée -1 = sentinelle, mise à manquant (D-19).
SENTINELLE_NOTE = -1
# Note > 20 = virgule décalée (12,2 saisi 122) : divisée par ce facteur (D-21).
FACTEUR_NOTE_DECALEE = 10

# tutorat : écritures de type_tuteur reconnues, en forme simplifiée (D-24).
ABREVIATIONS[("tutorat", "type_tuteur")] = {
    "pair (etudiant avance)": "pair",
    "etudiant": "pair",
    "prof": "enseignant",
}
ABREVIATIONS[("tutorat", "motif_orientation")] = {}
COLONNES_ENTIERES_TUTORAT = ["semaine_debut", "nb_seances"]

# Drapeaux de la colonne drapeau_tutorat (séparés par SEPARATEUR_DRAPEAUX).
DRAPEAU_NB_SEANCES_INVALIDE = "nb_seances_invalide"
DRAPEAU_DEBUT_HORS_SUIVI = "debut_hors_suivi"
DRAPEAU_DEBUT_SEMAINE_INVALIDE = "debut_semaine_invalide"
DRAPEAU_DEBUT_APRES_SORTIE = "debut_apres_sortie"

# Fichiers de rejets (lignes retirées mais conservées pour la traçabilité).
FICHIER_REJETS_ACTIVITE_SEMAINE = DOSSIER_REJETS / "activite_semaine_invalide.csv"
FICHIER_REJETS_ACTIVITE_SORTIE = DOSSIER_REJETS / "activite_apres_sortie.csv"
FICHIER_REJETS_TUTORAT = DOSSIER_REJETS / "tutorat_sans_etudiant.csv"

# ---------------------------------------------------------------------------
# Nettoyage et pseudonymisation de la table messages (DA-05, décisions D-28, D-29)
# ---------------------------------------------------------------------------
CANAUX_MESSAGES = ["forum", "formulaire de suivi"]

# Signes d'un texte UTF-8 relu comme cp1252 (« trouvÃ© » pour « trouvé », « â€™ »
# pour une apostrophe typographique). Réparation : texte.encode("cp1252").decode("utf-8").
MOTIF_ENCODAGE_CASSE = r"Ã|Â|â€"
ENCODAGE_DE_LA_CASSE = "cp1252"

# Un message « vide » ne contient aucun caractère alphanumérique (lettre ou chiffre) (D-29).
MOTIF_ALPHANUMERIQUE = r"[^\W_]"

# Pseudonymisation (D-28) : chaque motif reconnu est remplacé par sa balise.
# E-mail : une ou plusieurs lettres, chiffres, points, « + » ou « - », puis « @ »,
# puis un domaine d'au moins deux parties séparées par des points (ex. « exemple.sn »).
MOTIF_PSEUDO_EMAIL = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
BALISE_EMAIL = "[EMAIL]"

# Téléphone sénégalais : indicatif « +221 » facultatif, puis 9 chiffres commençant par
# 70, 75, 76, 77 ou 78, groupés ou non par des espaces ou des points
# (ex. « 77 000 00 00 », « +221 77.000.00.00 »). Les \b évitent de couper un nombre plus long.
MOTIF_PSEUDO_TELEPHONE = r"(?:\+221[\s.]?)?\b7[05678](?:[\s.]?\d){7}\b"
BALISE_TELEPHONE = "[TEL]"

# Nom : « c'est » ou « je suis » (majuscule ou non, apostrophe droite ou typographique),
# puis au moins deux mots qui commencent par une majuscule (lettres et tirets autorisés,
# ex. « Prénom Testnom », « Marie-Claire Exemple »). Le groupe « intro » est gardé, seul le nom
# est remplacé : « c'est Prénom Testnom » -> « c'est [NOM] ». « je suis découragé » ne change
# pas (minuscule).
MOTIF_PSEUDO_NOM = (
    r"(?P<intro>\b[Cc][’']est|\b[Jj]e suis)\s+"
    r"[A-ZÀ-Þ][A-Za-zÀ-ÖØ-öø-ÿ-]*(?:\s+[A-ZÀ-Þ][A-Za-zÀ-ÖØ-öø-ÿ-]*)+"
)
BALISE_NOM = "[NOM]"

# Contrôle résiduel après remplacement : une suite de 8 chiffres ou plus, en ignorant
# les espaces et les points qui les séparent, signale un numéro oublié.
MOTIF_RESIDU_CHIFFRES = r"\d(?:[\s.]?\d){7,}"

FICHIER_REJETS_MESSAGES = DOSSIER_REJETS / "messages_vides.csv"

# ---------------------------------------------------------------------------
# Journal de nettoyage complet (DA-06)
# ---------------------------------------------------------------------------
# Code d'anomalie de docs/audit_qualite.md (ex. « ETU-12 », « X-04 »).
CODE_AUDIT = r"(?:ETU|INS|ACT|TUT|MSG|X)-\d{2}"
# Le même code, comme mot entier, pour le retrouver au milieu d'un texte.
MOTIF_CODE_AUDIT = r"\b" + CODE_AUDIT + r"\b"

# Anomalies constatées par l'audit et volontairement laissées sans traitement, avec la
# raison (textes imposés par la consigne C05). ETU-09 (mentions vides) n'y figure pas :
# ces mentions sont complétées à partir de la note par D-10.
RAISON_MANQUANTS = ("valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : "
                    "pas d'imputation dans les tables nettoyées)")
ANOMALIES_SANS_TRAITEMENT = {
    "ETU-08": RAISON_MANQUANTS,
    "ETU-10": RAISON_MANQUANTS,
    "ETU-11": RAISON_MANQUANTS,
    "ACT-05": RAISON_MANQUANTS,
    "TUT-04": RAISON_MANQUANTS,
    "ETU-26": "distances > 51,7 km conservées, toutes hors Dakar et plausibles (D-09)",
    "X-04": ("étudiants sans sortie déclarée dont l'activité s'arrête avant la semaine 30 — "
             "lecture renvoyée à DA-07"),
    "X-05": "arrêt de l'activité après une sortie déclarée — situation normale, pas une anomalie",
    "X-09": ("messages après la sortie — disparus après la correction des dates inversées (D-13), "
             "0 restant"),
    "MSG-07": "synthèse de MSG-04 à MSG-06 (un message peut contenir plusieurs données personnelles)",
}

# ---------------------------------------------------------------------------
# Construction de T et E, base_survie et format période-personne (DA-07, D-30 à D-39)
# ---------------------------------------------------------------------------
# Seuils d'inactivité étudiés en sensibilité (la référence est SEUIL_INACTIVITE = 4).
SEUILS_SENSIBILITE = (3, 5)

# État d'une semaine d'activité (D-31).
ETAT_ACTIF = "actif"
ETAT_INACTIF = "inactif"
ETAT_INCONNU = "inconnu"

# Lecture d'une semaine « inconnue » : « active » = référence (elle coupe une série
# d'inactivité, D-31) ; « inactive » = sensibilité (elle compte comme inactive).
LECTURE_INCONNU_REFERENCE = "active"
LECTURE_INCONNU_SENSIBILITE = "inactive"

# Types d'événement de base_survie (D-30, D-32 à D-35) ; les 4 premiers ont E = 1.
EVENEMENT_ABANDON_DECLARE = "abandon_declare"
EVENEMENT_ABANDON_SANS_DATE = "abandon_sans_date"
EVENEMENT_ABANDON_DATE_INVALIDE = "abandon_date_invalide"
EVENEMENT_DECROCHAGE_SILENCIEUX = "decrochage_silencieux"
EVENEMENT_TRANSFERT = "transfert"
EVENEMENT_PERDU_DE_VUE = "perdu_de_vue"
EVENEMENT_FIN_DE_SUIVI = "fin_de_suivi"
TYPES_AVEC_EVENEMENT = [EVENEMENT_ABANDON_DECLARE, EVENEMENT_ABANDON_SANS_DATE,
                        EVENEMENT_ABANDON_DATE_INVALIDE, EVENEMENT_DECROCHAGE_SILENCIEUX]
TYPES_CENSURES = [EVENEMENT_TRANSFERT, EVENEMENT_PERDU_DE_VUE, EVENEMENT_FIN_DE_SUIVI]

# Statut de tutorat par rapport au T de référence (D-37).
STATUT_NON_TUTORE = "non_tutore"
STATUT_TUTORE = "tutore"
STATUT_TUTORAT_MEME_SEMAINE = "tutorat_meme_semaine_que_T"
STATUT_TUTORAT_APRES_T = "tutorat_apres_T"
STATUT_TUTORAT_SEMAINE_INCONNUE = "tutorat_semaine_inconnue"
# Statuts comptés comme « tutoré » (tutore = 1) ; la semaine inconnue sera traitée en CA-01.
STATUTS_TUTORE = [STATUT_TUTORE, STATUT_TUTORAT_SEMAINE_INCONNUE]

FICHIER_BASE_SURVIE = DOSSIER_PROCESSED / "base_survie.csv"
FICHIER_PERIODE_PERSONNE = DOSSIER_PROCESSED / "base_periode_personne.csv"

# Colonnes de base_survie, dans l'ordre imposé (D-36 : seules les covariables de
# etudiants, connues à la rentrée ; aucune variable calculée sur tout le suivi).
COLONNES_BASE_SURVIE = [
    "id_etudiant", "cohorte", "genre", "age", "boursier", "filiere", "mention_bac", "note_bac",
    "region_origine", "distance_campus_km", "emploi_parallele",
    "T", "E", "type_evenement", "T_seuil3", "E_seuil3", "T_seuil5", "E_seuil5",
    "tutore", "statut_tutorat", "semaine_debut_tutorat", "type_tuteur", "motif_orientation", "nb_seances",
]
# Variables connues le jour de la rentrée (D-43) : les modèles prennent leurs covariables
# fixes dans cette liste, jamais « toutes les colonnes sauf T et E ». Les colonnes de
# tutorat (nb_seances, tutore, statut_tutorat…) sont connues plus tard : elles n'y sont pas.
COVARIABLES_RENTREE = [
    "cohorte", "genre", "age", "boursier", "filiere", "mention_bac", "note_bac",
    "region_origine", "distance_campus_km", "emploi_parallele",
]

# Activité d'une semaine, telle qu'elle figure dans activite_hebdo (avec etat_activite).
COLONNES_ACTIVITE_SEMAINE = ["nb_connexions_lms", "devoirs_rendus", "note_moyenne", "absences", "etat_activite"]
# Mêmes colonnes pour la semaine précédente du même étudiant (vides en semaine 1).
# D-42 : ce sont les SEULES colonnes d'activité utilisables dans un modèle semaine par
# semaine ; l'activité de la semaine en cours fait partie de la définition de l'événement.
SUFFIXE_PREC = "_prec"
COLONNES_ACTIVITE_PREC = [colonne + SUFFIXE_PREC for colonne in COLONNES_ACTIVITE_SEMAINE]

COLONNES_PERIODE_PERSONNE = [
    "id_etudiant", "semaine", "evenement", "nb_connexions_lms", "devoirs_rendus", "note_moyenne",
    "absences", "etat_activite", "tutorat_commence",
] + COLONNES_ACTIVITE_PREC

# ---------------------------------------------------------------------------
# Analyse exploratoire (DA-08)
# ---------------------------------------------------------------------------

# Semaine repère pour décrire l'entrée en tutorat (part des tutorats commencés au plus
# tard cette semaine-là, consigne C08). Simple description : la semaine landmark de
# l'analyse causale sera choisie et validée en CA-01.
SEMAINE_REPERE_TUTORAT = 8

# Libellé de la ligne des valeurs manquantes dans le profil d'une variable qualitative.
MODALITE_MANQUANTE = "(manquant)"

# ---------------------------------------------------------------------------
# Analyse de survie : Kaplan-Meier et Cox (SV-01, SV-02)
# ---------------------------------------------------------------------------

# Semaines auxquelles la survie (part des étudiants sans décrochage) est rapportée.
SEMAINES_SURVIE = (10, 20, 30)
# Niveau des tests et des intervalles de confiance (IC à 95 %).
ALPHA = 0.05

# Sous-groupes comparés par Kaplan-Meier et le log-rank (D-46, sous-groupes du cahier).
# Avec 4 tests, le seuil de Bonferroni est ALPHA / 4 = 0,0125.
VARIABLES_KAPLAN_MEIER = ["boursier", "filiere", "mention_bac", "emploi_parallele"]

# Semaine critique (D-47) : risque de la semaine >= 1,5 fois le risque hebdomadaire moyen.
FACTEUR_SEMAINE_CRITIQUE = 1.5
