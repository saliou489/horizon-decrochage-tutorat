"""Nettoyage de la table « activite_hebdo ».

Rôle du module : appliquer, dans l'ordre imposé par la consigne C04, les règles
validées par Saliou (décisions D-19 à D-23) à data/raw/activite_hebdo.csv.
Chaque règle est une fonction : DataFrame en entrée -> (DataFrame corrigé, nombre de
lignes touchées, lignes de journal) ; les règles qui retirent des lignes renvoient
aussi les lignes retirées (rejets).
Les semaines absentes et les valeurs manquantes ne sont PAS comblées : savoir si une
semaine absente veut dire « inactif » ou « donnée manquante » est un point de DA-07.

Tâche couverte : DA-04.
"""

import pandas as pd

from src import config
from src.nettoyage.commun import (
    ErreurNettoyage,
    convertir_nombres,
    entree_journal,
    remplacer_virgule,
)

TABLE = "activite_hebdo"
CLE = [config.COLONNE_ID, "semaine"]


# ---------------------------------------------------------------------------
# Règle 1 : identifiants
# ---------------------------------------------------------------------------

def regle_identifiants(df, etudiants):
    """Majuscules, espaces retirés ; format HZ + 5 chiffres ; étudiant connu, sinon arrêt.

    Audit ACT-01 ; décision D-19.
    """
    resultat = df.copy()
    avant = df[config.COLONNE_ID]
    apres = avant.str.replace(r"\s+", "", regex=True).str.upper()
    mal_formes = sorted(set(apres[~apres.str.fullmatch(config.FORMAT_ID_ETUDIANT)]))
    if mal_formes:
        raise ErreurNettoyage(f"Identifiant(s) mal formé(s) après correction : {mal_formes[:10]}")
    inconnus = sorted(set(apres) - set(etudiants[config.COLONNE_ID]))
    if inconnus:
        raise ErreurNettoyage(f"Identifiant(s) d'activité absent(s) de etudiants : {inconnus[:10]}")
    resultat[config.COLONNE_ID] = apres
    nb = int((apres != avant).sum())
    entrees = [entree_journal(TABLE, "Identifiant en minuscules (ACT-01)", nb, "Mis en majuscules", "D-19")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 2 : nombres
# ---------------------------------------------------------------------------

def regle_nombres(df):
    """Virgule -> point, conversion numérique ; semaine, connexions, devoirs, absences en entiers.

    Audit ACT-09 (virgule), ACT-12 (« 10.0 ») ; décision D-19. Un entier avec une
    vraie partie décimale (ex. 3.5 connexions) arrête le nettoyage.
    """
    resultat = df.copy()
    entrees = []
    touchees = pd.Series(False, index=df.index)
    for colonne in config.COLONNES_ENTIERES_ACTIVITE + config.COLONNES_DECIMALES_ACTIVITE:
        texte, nb_virgules = remplacer_virgule(df[colonne])
        entier = colonne in config.COLONNES_ENTIERES_ACTIVITE
        resultat[colonne] = convertir_nombres(texte, colonne, entier)
        if nb_virgules:
            touchees = touchees | (texte != df[colonne])
            entrees.append(entree_journal(TABLE, f"{colonne} écrit avec une virgule décimale (ACT-09)",
                                          nb_virgules, "Virgule remplacée par un point", "D-19"))
        if entier:
            decimales = df[colonne].str.contains(".", regex=False)
            touchees = touchees | decimales
            if decimales.any():
                entrees.append(entree_journal(TABLE, f"{colonne} entier écrit « 10.0 » (ACT-12)",
                                              int(decimales.sum()), "Converti en entier", "D-19"))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 3 : semaines invalides
# ---------------------------------------------------------------------------

def semaines_attendues(identifiant, sorties):
    """Semaines où l'étudiant devrait avoir une ligne : 1 à sa semaine de sortie, ou 1 à 30."""
    derniere = min(int(sorties.get(identifiant, config.N_SEMAINES)), config.N_SEMAINES)
    return set(range(1, derniere + 1))


def regle_semaines_invalides(df, sorties):
    """Retire les lignes dont la semaine sort de [1 ; 30] (D-19, audit ACT-06, ACT-07).

    Contrôle : si l'étudiant concerné a une semaine manquante entre 1 et sa semaine de
    sortie (ou 30), la ligne retirée aurait pu la combler : arrêt.
    Sortie : (table, nb lignes retirées, journal, rejets).
    """
    invalides = df["semaine"].isna() | ~df["semaine"].between(1, config.N_SEMAINES).fillna(False)
    rejets = df[invalides].reset_index(drop=True)
    resultat = df[~invalides].reset_index(drop=True)
    presentes = resultat.groupby(config.COLONNE_ID)["semaine"].agg(set)
    a_combler = [i for i in sorted(set(rejets[config.COLONNE_ID]))
                 if semaines_attendues(i, sorties) - presentes.get(i, set())]
    if a_combler:
        raise ErreurNettoyage("Ligne à semaine invalide pour un étudiant à qui il manque une semaine : "
                              f"{a_combler[:10]}")
    nb = len(rejets)
    entrees = [entree_journal(TABLE, "semaine hors [1 ; 30] (valeurs −1, 0, 31, 32, 99 ; ACT-06, ACT-07)", nb,
                              "Ligne retirée, conservée dans rejets/activite_semaine_invalide.csv "
                              "(aucune semaine à combler chez ces étudiants)", "D-19")]
    return resultat, nb, entrees, rejets


# ---------------------------------------------------------------------------
# Règle 4 : valeurs impossibles -> manquant
# ---------------------------------------------------------------------------

def regle_valeurs_impossibles(df):
    """Connexions < 0 ou > 100, devoirs hors [0 ; 2], note = −1 -> manquant (D-19).

    Audit ACT-08, ACT-10, ACT-13, ACT-14. Les connexions de 21 à 26 restent.
    """
    resultat = df.copy()
    bornes_devoirs = config.BORNES[(TABLE, "devoirs_rendus")]
    masques = {
        "nb_connexions_lms": df["nb_connexions_lms"].notna()
        & ((df["nb_connexions_lms"] < 0) | (df["nb_connexions_lms"] > config.CONNEXIONS_MAX_PLAUSIBLE)),
        "devoirs_rendus": df["devoirs_rendus"].notna()
        & ~df["devoirs_rendus"].between(bornes_devoirs["min"], bornes_devoirs["max"]),
        "note_moyenne": df["note_moyenne"].notna() & (df["note_moyenne"] == config.SENTINELLE_NOTE),
    }
    descriptions = {
        "nb_connexions_lms": "nb_connexions_lms négatif ou > 100 (ACT-13, ACT-14)",
        "devoirs_rendus": "devoirs_rendus hors [0 ; 2] (ACT-08)",
        "note_moyenne": "note_moyenne = −1, valeur sentinelle (ACT-10)",
    }
    entrees = []
    touchees = pd.Series(False, index=df.index)
    for colonne, masque in masques.items():
        resultat.loc[masque, colonne] = pd.NA
        touchees = touchees | masque
        entrees.append(entree_journal(TABLE, descriptions[colonne], int(masque.sum()),
                                      f"{colonne} mis à manquant, ligne conservée", "D-19"))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 5 : notes décalées
# ---------------------------------------------------------------------------

def regle_notes_decalees(df):
    """note_moyenne > 20 -> divisée par 10 (virgule décalée, D-21, audit ACT-11).

    La justification compare la distribution des notes divisées à celle des notes
    valides (moyenne et écart-type calculés ici). Ensuite, toute note hors [0 ; 20]
    arrête le nettoyage.
    """
    resultat = df.copy()
    notes = df["note_moyenne"]
    bornes = config.BORNES[(TABLE, "note_moyenne")]
    decalees = notes.notna() & (notes > bornes["max"])
    divisees = notes[decalees] / config.FACTEUR_NOTE_DECALEE
    valides = notes[notes.notna() & notes.between(bornes["min"], bornes["max"])]
    resultat.loc[decalees, "note_moyenne"] = divisees
    hors_bornes = resultat["note_moyenne"].notna() & ~resultat["note_moyenne"].between(bornes["min"], bornes["max"])
    if hors_bornes.any():
        raise ErreurNettoyage(f"note_moyenne encore hors [0 ; 20] : {sorted(resultat.loc[hors_bornes, 'note_moyenne'])[:10]}")
    justification = (f"D-21 : après division, moyenne {divisees.mean():.2f} et écart-type {divisees.std():.2f}, "
                     f"comme les notes valides ({valides.mean():.2f} et {valides.std():.2f})")
    nb = int(decalees.sum())
    entrees = [entree_journal(TABLE, "note_moyenne > 20 (entre 34,4 et 163,6 ; virgule décalée, ACT-11)", nb,
                              "Note divisée par 10", justification)]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 6 : doublons
# ---------------------------------------------------------------------------

def premiere_valeur(serie):
    """Valeur de la première ligne du fichier, même si elle est manquante."""
    return serie.iloc[0]


def regle_doublons(df):
    """Une ligne par (étudiant, semaine) (D-19, D-20 ; audit ACT-02 à ACT-04).

    1. Lignes strictement identiques -> une seule gardée.
    2. Même (étudiant, semaine) avec des valeurs différentes -> une ligne :
       connexions et devoirs = la plus grande valeur renseignée (si une source a vu de
       l'activité, l'étudiant n'était pas inactif) ; note et absences = celles de la
       première ligne du fichier. Des absences différentes arrêtent le nettoyage.
    """
    identiques = df.duplicated(keep="first")
    sans_identiques = df[~identiques]
    en_double = sans_identiques.duplicated(CLE, keep=False)
    copies = sans_identiques[en_double]
    absences_differentes = copies.groupby(CLE)["absences"].nunique(dropna=False) > 1
    if absences_differentes.any():
        raise ErreurNettoyage("Semaines en double avec des absences différentes : "
                              f"{list(absences_differentes[absences_differentes].index[:10])}")

    groupes = copies.groupby(CLE, sort=False)
    fusion = groupes.agg(nb_connexions_lms=("nb_connexions_lms", "max"),
                         devoirs_rendus=("devoirs_rendus", "max"),
                         note_moyenne=("note_moyenne", premiere_valeur),
                         absences=("absences", premiere_valeur)).reset_index()
    # Position de la première copie de chaque couple, pour garder l'ordre du fichier
    # (avec sort=False, les groupes suivent l'ordre de première apparition, comme head(1)).
    fusion["_ordre"] = groupes.head(1).index.values
    zero_contre_activite = int(((groupes["nb_connexions_lms"].min() == 0)
                                & (groupes["nb_connexions_lms"].max() > 0)).sum())

    restantes = sans_identiques[~en_double].copy()
    restantes["_ordre"] = restantes.index
    resultat = (pd.concat([restantes, fusion[restantes.columns]], ignore_index=True)
                .sort_values("_ordre").drop(columns="_ordre").reset_index(drop=True))
    for colonne in config.COLONNES_ENTIERES_ACTIVITE:
        resultat[colonne] = resultat[colonne].astype("Int64")

    nb_couples = len(fusion)
    entrees = [
        entree_journal(TABLE, "Ligne strictement identique à une ligne précédente (ACT-02, ACT-03 ; plus "
                       "nombreuses qu'à l'audit car certaines copies deviennent identiques après les règles 3 à 5)",
                       int(identiques.sum()), "Ligne supprimée", "D-19"),
        entree_journal(TABLE, f"Même (étudiant, semaine) avec des valeurs différentes (ACT-04) : {len(copies)} "
                       f"lignes pour {nb_couples} couples", len(copies) - nb_couples,
                       "Fusion en une ligne : connexions et devoirs = maximum, note et absences = première ligne",
                       "D-20"),
        entree_journal(TABLE, "dont couples où une copie indique 0 connexion et l'autre une activité",
                       zero_contre_activite, "Activité gardée (maximum) : évite un faux jour d'inactivité",
                       "D-20"),
    ]
    return resultat, int(identiques.sum()) + len(copies), entrees


# ---------------------------------------------------------------------------
# Règle 7 : activité après la sortie
# ---------------------------------------------------------------------------

def regle_apres_sortie(df, sorties):
    """Retire les lignes dont la semaine dépasse la semaine de sortie déclarée (D-22, D-23).

    Audit X-06, X-07. Sortie : (table, nb lignes retirées, journal, rejets).
    """
    semaine_sortie = df[config.COLONNE_ID].map(sorties)
    apres = semaine_sortie.notna() & (df["semaine"] > semaine_sortie)
    rejets = df[apres].reset_index(drop=True)
    resultat = df[~apres].reset_index(drop=True)
    nb = len(rejets)
    nb_etudiants = rejets[config.COLONNE_ID].nunique()
    entrees = [entree_journal(TABLE, f"Activité après la semaine de sortie déclarée ({nb_etudiants} étudiants ; "
                              "X-06, X-07)", nb, "Ligne retirée, conservée dans rejets/activite_apres_sortie.csv",
                              "D-22, D-23")]
    return resultat, nb, entrees, rejets


# ---------------------------------------------------------------------------
# Enchaînement
# ---------------------------------------------------------------------------

def nettoyer(df_brut, etudiants, sorties):
    """Applique les 7 règles dans l'ordre.

    Entrées : table brute (texte), etudiants nettoyée, semaines de sortie
    (commun.semaines_de_sortie).
    Sortie : (table nettoyée, {nom: rejets}, lignes de journal, {règle: lignes touchées}).
    """
    entrees, touchees, rejets = [], {}, {}

    df, nb, journal = regle_identifiants(df_brut, etudiants)
    touchees["regle_identifiants"], entrees = nb, entrees + journal
    df, nb, journal = regle_nombres(df)
    touchees["regle_nombres"], entrees = nb, entrees + journal
    df, nb, journal, rejets["semaine_invalide"] = regle_semaines_invalides(df, sorties)
    touchees["regle_semaines_invalides"], entrees = nb, entrees + journal
    df, nb, journal = regle_valeurs_impossibles(df)
    touchees["regle_valeurs_impossibles"], entrees = nb, entrees + journal
    df, nb, journal = regle_notes_decalees(df)
    touchees["regle_notes_decalees"], entrees = nb, entrees + journal
    df, nb, journal = regle_doublons(df)
    touchees["regle_doublons"], entrees = nb, entrees + journal
    df, nb, journal, rejets["apres_sortie"] = regle_apres_sortie(df, sorties)
    touchees["regle_apres_sortie"], entrees = nb, entrees + journal
    return df, rejets, entrees, touchees
