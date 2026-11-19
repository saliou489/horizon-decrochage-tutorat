"""Nettoyage de la table « etudiants ».

Rôle du module : appliquer, dans l'ordre imposé par la consigne C02, les règles
validées par Saliou (décisions D-06 à D-11) à data/raw/etudiants.csv.
Chaque règle est une fonction : DataFrame en entrée -> (DataFrame corrigé, nombre de
lignes touchées, lignes de journal). L'ordre compte : on harmonise avant de
dédoublonner, sinon deux écritures d'un même étudiant ne seraient pas reconnues.

Tâche couverte : DA-02.
"""

import pandas as pd

from src import config
from src.nettoyage.commun import (
    ErreurNettoyage,
    convertir_nombres,
    entree_journal,
    est_vide,
    harmoniser_modalites,
    remplacer_virgule,
    retirer_unites,
)

TABLE = "etudiants"
COLONNES_CATEGORIELLES = ["genre", "boursier", "filiere", "mention_bac",
                          "region_origine", "emploi_parallele"]

# Codes d'anomalie de docs/audit_qualite.md traités par chaque ligne du journal (DA-06).
CODES_MODALITES = {"genre": "ETU-12", "boursier": "ETU-13", "filiere": "ETU-14",
                   "mention_bac": "ETU-15", "region_origine": "ETU-16",
                   "emploi_parallele": "aucune anomalie à l'audit"}
CODES_VIRGULE = {"note_bac": "ETU-20", "distance_campus_km": "ETU-22"}
CODES_UNITE = {"age": "ETU-17", "distance_campus_km": "ETU-23"}


# ---------------------------------------------------------------------------
# Règle 1 : en-têtes
# ---------------------------------------------------------------------------

def regle_entetes(df):
    """Retire les espaces des en-têtes et renomme les colonnes comme le LISEZMOI.

    Audit ETU-01, ETU-02 ; décision D-06. S'arrête si, après correction, les colonnes
    ne sont pas exactement celles attendues.
    """
    anciennes = list(df.columns)
    sans_espaces = [c.strip() for c in anciennes]
    renommage = config.RENOMMAGE_COLONNES[TABLE]
    nouvelles = [renommage.get(c, c) for c in sans_espaces]
    attendues = config.FICHIERS_BRUTS[TABLE]["colonnes"]
    if nouvelles != attendues:
        raise ErreurNettoyage(f"En-têtes inattendus après correction : {nouvelles}")
    resultat = df.copy()
    resultat.columns = nouvelles
    nb_espaces = sum(a != s for a, s in zip(anciennes, sans_espaces))
    nb_renommees = sum(s != n for s, n in zip(sans_espaces, nouvelles))
    entrees = [
        entree_journal(TABLE, "En-tête entouré d'espaces (« id_etudiant  », ETU-01)", nb_espaces,
                       "Espaces retirés", "D-06"),
        entree_journal(TABLE, "En-tête nommé autrement que dans le LISEZMOI (« Distance campus (km) », ETU-02)",
                       nb_renommees, "Renommé en distance_campus_km", "D-06"),
    ]
    # Lignes touchées : 0, une correction d'en-tête ne modifie aucune ligne de données.
    return resultat, 0, entrees


# ---------------------------------------------------------------------------
# Règle 2 : identifiants
# ---------------------------------------------------------------------------

def regle_identifiants(df):
    """Met les identifiants en majuscules et retire les espaces.

    Audit ETU-03, ETU-04 ; décision D-06. Un identifiant qui ne respecte toujours pas
    « HZ » + 5 chiffres arrête le nettoyage (aucun n'a été trouvé par l'audit).
    """
    resultat = df.copy()
    avant = resultat[config.COLONNE_ID]
    apres = avant.str.replace(r"\s+", "", regex=True).str.upper()
    mal_formes = sorted(set(apres[~apres.str.fullmatch(config.FORMAT_ID_ETUDIANT)]))
    if mal_formes:
        raise ErreurNettoyage(f"Identifiant(s) mal formé(s) après correction : {mal_formes}")
    resultat[config.COLONNE_ID] = apres
    nb_espaces = int((avant != avant.str.strip()).sum())
    nb_casse = int((avant.str.strip() != avant.str.strip().str.upper()).sum())
    entrees = [
        entree_journal(TABLE, "Identifiant entouré d'espaces (ETU-03)", nb_espaces,
                       "Espaces retirés", "D-06"),
        entree_journal(TABLE, "Identifiant en minuscules (ETU-04)", nb_casse,
                       "Mis en majuscules", "D-06"),
    ]
    return resultat, int((apres != avant).sum()), entrees


# ---------------------------------------------------------------------------
# Règle 3 : modalités
# ---------------------------------------------------------------------------

def regle_modalites(df):
    """Ramène les colonnes catégorielles aux modalités officielles du LISEZMOI.

    Audit ETU-12 à ETU-16 ; décisions D-06 et D-11 (0 -> Non, 1 -> Oui).
    Comparaison sur la forme simplifiée (minuscules, sans accents, tirets -> espaces).
    Une valeur inconnue arrête le nettoyage ; les cases vides restent vides.
    """
    resultat = df.copy()
    entrees = []
    touchees = pd.Series(False, index=df.index)
    for colonne in COLONNES_CATEGORIELLES:
        officielles = config.MODALITES[(TABLE, colonne)]
        abreviations = config.ABREVIATIONS[(TABLE, colonne)]
        harmonisee, nb = harmoniser_modalites(df[colonne], officielles, abreviations, colonne)
        touchees = touchees | (harmonisee != df[colonne])
        resultat[colonne] = harmonisee
        justification = "D-06, D-11" if colonne == "boursier" else "D-06"
        entrees.append(entree_journal(
            TABLE, f"Modalités de {colonne} non harmonisées (casse, espaces, accents, abréviations ; "
            f"{CODES_MODALITES[colonne]})", nb,
            f"Recodage vers {' / '.join(officielles) if len(officielles) <= 5 else 'les 14 régions officielles'}",
            justification))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 4 : nombres
# ---------------------------------------------------------------------------

def regle_nombres(df):
    """Virgule -> point, unités « ans » / « km » retirées, conversion numérique.

    Audit ETU-17, ETU-20, ETU-22, ETU-23 ; décision D-06. age et cohorte en entiers
    (type Int64, qui accepte les manquants), note_bac et distance en décimaux.
    """
    resultat = df.copy()
    entrees = []
    touchees = pd.Series(False, index=df.index)
    colonnes = config.COLONNES_ENTIERES_ETUDIANTS + config.COLONNES_DECIMALES_ETUDIANTS
    for colonne in colonnes:
        texte, nb_unites = retirer_unites(df[colonne], config.UNITES_TEXTE)
        texte, nb_virgules = remplacer_virgule(texte)
        touchees = touchees | (texte != df[colonne])
        entier = colonne in config.COLONNES_ENTIERES_ETUDIANTS
        resultat[colonne] = convertir_nombres(texte, colonne, entier)
        if nb_virgules:
            entrees.append(entree_journal(TABLE, f"{colonne} écrit avec une virgule décimale ({CODES_VIRGULE[colonne]})",
                                          nb_virgules, "Virgule remplacée par un point", "D-06"))
        if nb_unites:
            exemple = config.EXEMPLES_UNITE[colonne]
            entrees.append(entree_journal(TABLE, f"{colonne} écrit avec son unité (ex. « {exemple} », {CODES_UNITE[colonne]})",
                                          nb_unites, "Unité retirée", "D-06"))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 5 : valeurs impossibles -> manquant
# ---------------------------------------------------------------------------

def masque_impossibles(df):
    """Masques des valeurs impossibles par colonne (D-08, D-09).

    Les bornes viennent de config.BORNES (LISEZMOI). Pour la distance : <= 0 ou égale
    à la seule sentinelle présente (9999). Les grandes distances (> 51,7 km) restent.
    """
    masques = {}
    for colonne in ["age", "note_bac"]:
        bornes = config.BORNES[(TABLE, colonne)]
        valeurs = df[colonne]
        masques[colonne] = valeurs.notna() & ((valeurs < bornes["min"]) | (valeurs > bornes["max"]))
    distance = df["distance_campus_km"]
    masques["distance_campus_km"] = distance.notna() & (
        (distance <= config.BORNES[(TABLE, "distance_campus_km")]["min"])
        | (distance == config.SENTINELLE_DISTANCE))
    return masques


def regle_valeurs_impossibles(df):
    """Met à manquant les valeurs impossibles ; la ligne est gardée.

    Audit ETU-18, ETU-19, ETU-21, ETU-24, ETU-25 ; décisions D-08 (age, note_bac,
    sentinelles comprises ; mention conservée) et D-09 (distances).
    """
    resultat = df.copy()
    masques = masque_impossibles(df)
    descriptions = {
        "age": ("age hors [17 ; 35] (sentinelle 99 comprise ; ETU-18, ETU-19)", "D-08"),
        "note_bac": ("note_bac hors [10 ; 20] (ETU-21)", "D-08"),
        "distance_campus_km": ("distance_campus_km négative ou nulle, ou sentinelle 9999 (ETU-24, ETU-25)", "D-09"),
    }
    entrees = []
    touchees = pd.Series(False, index=df.index)
    for colonne, masque in masques.items():
        resultat.loc[masque, colonne] = pd.NA
        touchees = touchees | masque
        anomalie, decision = descriptions[colonne]
        entrees.append(entree_journal(TABLE, anomalie, int(masque.sum()),
                                      f"{colonne} mis à manquant, ligne conservée", decision))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 6 : doublons
# ---------------------------------------------------------------------------

def regle_doublons(df):
    """Une seule ligne par étudiant : la première du fichier.

    Audit ETU-05 à ETU-07 ; décisions D-06 (doublons exacts) et D-07 (quasi-doublons :
    première ligne gardée). Deux lignes d'un même étudiant qui diffèrent sur une autre
    colonne que la distance arrêtent le nettoyage.
    """
    colonnes_controlees = [c for c in df.columns
                           if c not in (config.COLONNE_ID, config.COLONNE_DIFFERENCE_TOLEREE)]
    en_double = df[df.duplicated(config.COLONNE_ID, keep=False)]
    versions = en_double.groupby(config.COLONNE_ID)[colonnes_controlees].nunique(dropna=False)
    conflits = versions[(versions > 1).any(axis=1)]
    if len(conflits) > 0:
        raise ErreurNettoyage(
            "Étudiant(s) en double avec des valeurs différentes hors distance : "
            f"{list(conflits.index)}")

    # Une ligne strictement identique à une ligne précédente (après harmonisation).
    identiques = df.duplicated(keep="first")
    # Toute autre répétition d'un identifiant déjà vu : même étudiant, distance différente.
    repetees = df.duplicated(config.COLONNE_ID, keep="first")
    differentes = repetees & ~identiques
    resultat = df[~repetees].reset_index(drop=True)
    entrees = [
        entree_journal(TABLE, "Ligne strictement identique à une ligne précédente (après harmonisation, ETU-05, ETU-06)",
                       int(identiques.sum()), "Ligne supprimée", "D-06"),
        entree_journal(TABLE, "Même étudiant présent deux fois avec une distance différente (ETU-07)",
                       int(differentes.sum()), "Première ligne du fichier gardée, l'autre supprimée", "D-07"),
    ]
    return resultat, int(repetees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 7 : mention / note
# ---------------------------------------------------------------------------

def mention_depuis_note(note):
    """Mention du bac correspondant à une note (D-10) ; manquant si la note l'est."""
    if pd.isna(note):
        return pd.NA
    for seuil, mention in config.SEUILS_MENTION:
        if note >= seuil:
            return mention
    return pd.NA


def regle_mention_note(df):
    """Recalcule mention_bac à partir de note_bac quand la note est connue.

    Audit ETU-27 ; décision D-10 : la note fait foi. Compte à part les mentions
    corrigées (contradiction) et complétées (vides). Note manquante : mention gardée.
    """
    resultat = df.copy()
    calculee = df["note_bac"].map(mention_depuis_note)
    note_connue = calculee.notna()
    mention_vide = est_vide(df["mention_bac"])
    corrigees = note_connue & ~mention_vide & (calculee != df["mention_bac"])
    completees = note_connue & mention_vide
    resultat.loc[note_connue, "mention_bac"] = calculee[note_connue]
    entrees = [
        entree_journal(TABLE, "mention_bac en contradiction avec note_bac (ETU-27 ; une note de 12, 14 ou 16 "
                       "tout rond est tranchée par D-10)", int(corrigees.sum()),
                       "Mention recalculée à partir de la note", "D-10"),
        entree_journal(TABLE, "mention_bac vide alors que note_bac est connue (ETU-09)", int(completees.sum()),
                       "Mention calculée à partir de la note", "D-10"),
    ]
    return resultat, int((corrigees | completees).sum()), entrees


# ---------------------------------------------------------------------------
# Finitions et enchaînement
# ---------------------------------------------------------------------------

def vides_en_manquants(df):
    """Les cases vides des colonnes texte deviennent des NA (manquant explicite).

    Ce n'est pas une règle de nettoyage : une case vide et un NA s'écrivent tous les
    deux comme une case vide dans le CSV ; cela rend seulement le comptage homogène.
    """
    resultat = df.copy()
    for colonne in COLONNES_CATEGORIELLES:
        resultat[colonne] = resultat[colonne].where(resultat[colonne] != "", pd.NA)
    return resultat


REGLES = [
    regle_entetes,
    regle_identifiants,
    regle_modalites,
    regle_nombres,
    regle_valeurs_impossibles,
    regle_doublons,
    regle_mention_note,
]


def nettoyer(df_brut):
    """Applique les 7 règles dans l'ordre.

    Entrée : table brute (toutes valeurs en texte).
    Sortie : (table nettoyée, liste des lignes de journal, {règle: lignes touchées}).
    """
    df = df_brut
    entrees = []
    lignes_touchees = {}
    for regle in REGLES:
        df, nb, entrees_regle = regle(df)
        lignes_touchees[regle.__name__] = nb
        entrees += entrees_regle
    return vides_en_manquants(df), entrees, lignes_touchees


def profil_brut_comparable(df_brut):
    """Table brute avec les en-têtes attendus (par position), pour le tableau avant / après."""
    comparable = df_brut.copy()
    comparable.columns = config.FICHIERS_BRUTS[TABLE]["colonnes"]
    return comparable
