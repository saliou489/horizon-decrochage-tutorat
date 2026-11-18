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
# Nom propre introduit par une formule de présentation (« Je suis Awa Fall »,
# « c'est Moussa Ndiaye », « je m'appelle … », « mon nom est … »).
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
