"""Nettoyage de la table « tutorat ».

Rôle du module : appliquer, dans l'ordre imposé par la consigne C04, les règles
validées par Saliou (décisions D-24 à D-27) à data/raw/tutorat.csv, et construire
la colonne drapeau_tutorat.
Chaque règle est une fonction : DataFrame en entrée -> (DataFrame corrigé, nombre de
lignes touchées, lignes de journal). La colonne de travail « _drapeaux » (une liste
par ligne) se remplit au fil des règles, puis devient drapeau_tutorat.
Aucune colonne « tutoré pendant le suivi » n'est créée ici : le traitement sera
construit en DA-07, à partir de T.

Tâche couverte : DA-04.
"""

import pandas as pd

from src import config
from src.nettoyage.commun import (
    ErreurNettoyage,
    ajouter_drapeau,
    convertir_nombres,
    drapeaux_en_texte,
    entree_journal,
    harmoniser_modalites,
)

TABLE = "tutorat"
COLONNES_SORTIE = ["id_etudiant", "semaine_debut", "nb_seances", "type_tuteur", "motif_orientation",
                   "drapeau_tutorat"]
DRAPEAUX = [config.DRAPEAU_NB_SEANCES_INVALIDE, config.DRAPEAU_DEBUT_HORS_SUIVI,
            config.DRAPEAU_DEBUT_SEMAINE_INVALIDE, config.DRAPEAU_DEBUT_APRES_SORTIE]


# ---------------------------------------------------------------------------
# Règle 1 : en-tête et identifiants
# ---------------------------------------------------------------------------

def regle_entete_identifiants(df):
    """« ID Etudiant » -> id_etudiant ; majuscules, sans espaces ; format HZ + 5 chiffres.

    Audit TUT-01 ; décision D-24. Un en-tête ou un identifiant inattendu arrête le nettoyage.
    """
    renommage = config.RENOMMAGE_COLONNES[TABLE]
    colonnes = [renommage.get(c.strip(), c.strip()) for c in df.columns]
    if colonnes != config.FICHIERS_BRUTS[TABLE]["colonnes"]:
        raise ErreurNettoyage(f"En-têtes inattendus après correction : {colonnes}")
    resultat = df.copy()
    resultat.columns = colonnes
    avant = resultat[config.COLONNE_ID]
    apres = avant.str.replace(r"\s+", "", regex=True).str.upper()
    mal_formes = sorted(set(apres[~apres.str.fullmatch(config.FORMAT_ID_ETUDIANT)]))
    if mal_formes:
        raise ErreurNettoyage(f"Identifiant(s) mal formé(s) après correction : {mal_formes}")
    resultat[config.COLONNE_ID] = apres
    resultat["_drapeaux"] = [[] for _ in range(len(resultat))]
    nb = int((apres != avant).sum())
    nb_entetes = sum(a != n for a, n in zip(df.columns, colonnes))
    entrees = [
        entree_journal(TABLE, "En-tête « ID Etudiant » au lieu de id_etudiant (TUT-01)", nb_entetes,
                       "Renommé en id_etudiant", "D-24"),
        entree_journal(TABLE, "Identifiant en minuscules ou entouré d'espaces", nb,
                       "Mis en majuscules, espaces retirés", "D-24"),
    ]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 2 : modalités
# ---------------------------------------------------------------------------

def regle_modalites(df):
    """type_tuteur -> pair / enseignant ; motif_orientation parmi les 4 valeurs (D-24, TUT-05).

    Forme simplifiée comme pour etudiants. Une valeur imprévue arrête le nettoyage.
    """
    resultat = df.copy()
    entrees = []
    touchees = pd.Series(False, index=df.index)
    for colonne in ["type_tuteur", "motif_orientation"]:
        officielles = config.MODALITES[(TABLE, colonne)]
        harmonisee, nb = harmoniser_modalites(df[colonne], officielles,
                                              config.ABREVIATIONS[(TABLE, colonne)], colonne)
        resultat[colonne] = harmonisee
        touchees = touchees | (harmonisee != df[colonne])
        anomalie = (f"{colonne} écrit de plusieurs façons (« pair (étudiant avancé) », « PAIR », « Prof »…, TUT-05)"
                    if colonne == "type_tuteur" else f"{colonne} hors des 4 valeurs du LISEZMOI")
        entrees.append(entree_journal(TABLE, anomalie, nb, f"Recodage vers {' / '.join(officielles)}", "D-24"))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 3 : nombres
# ---------------------------------------------------------------------------

def regle_nombres(df):
    """semaine_debut et nb_seances en entiers (« -2.0 » -> −2) ; vide -> manquant (TUT-07)."""
    resultat = df.copy()
    touchees = pd.Series(False, index=df.index)
    for colonne in config.COLONNES_ENTIERES_TUTORAT:
        resultat[colonne] = convertir_nombres(df[colonne], colonne, entier=True)
        touchees = touchees | df[colonne].str.contains(".", regex=False)
    nb = int(touchees.sum())
    entrees = [entree_journal(TABLE, "nb_seances entier écrit « -2.0 » ou « 0.0 » (TUT-07)", nb,
                              "Converti en entier", "D-24")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 4 : séances
# ---------------------------------------------------------------------------

def regle_seances(df):
    """nb_seances <= 0 -> manquant, drapeau nb_seances_invalide (D-24, TUT-08).

    semaine_debut est la semaine de la première séance : au moins une séance a eu lieu,
    l'étudiant reste tutoré.
    """
    resultat = df.copy()
    invalides = df["nb_seances"].notna() & (df["nb_seances"] <= 0)
    resultat.loc[invalides, "nb_seances"] = pd.NA
    resultat["_drapeaux"] = ajouter_drapeau(df["_drapeaux"], invalides, config.DRAPEAU_NB_SEANCES_INVALIDE)
    nb = int(invalides.sum())
    entrees = [entree_journal(TABLE, "nb_seances nul ou négatif (0, −2 ; TUT-08)", nb,
                              "nb_seances mis à manquant, drapeau nb_seances_invalide, étudiant gardé tutoré",
                              "D-24")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 5 : doublons exacts
# ---------------------------------------------------------------------------

def regle_doublons(df):
    """Supprime les lignes identiques : une ligne par étudiant (D-24, TUT-02, TUT-03, X-10).

    S'il reste deux lignes différentes pour un étudiant, le nettoyage s'arrête.
    """
    contenu = df.drop(columns="_drapeaux")
    identiques = contenu.duplicated(keep="first")
    resultat = df[~identiques].reset_index(drop=True)
    encore = sorted(set(resultat.loc[resultat.duplicated(config.COLONNE_ID), config.COLONNE_ID]))
    if encore:
        raise ErreurNettoyage(f"Étudiant(s) avec deux lignes de tutorat différentes : {encore}")
    nb = int(identiques.sum())
    entrees = [entree_journal(TABLE, "Ligne de tutorat strictement identique à une ligne précédente "
                              "(TUT-02, TUT-03, X-10)", nb, "Ligne supprimée", "D-24")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 6 : orphelins
# ---------------------------------------------------------------------------

def regle_orphelins(df, etudiants):
    """Retire les tutorats d'identifiants absents de etudiants (D-24, X-02).

    Sortie : (table, nb lignes retirées, journal, rejets).
    """
    orphelins = ~df[config.COLONNE_ID].isin(set(etudiants[config.COLONNE_ID]))
    rejets = df[orphelins].drop(columns="_drapeaux").reset_index(drop=True)
    resultat = df[~orphelins].reset_index(drop=True)
    nb = int(orphelins.sum())
    entrees = [entree_journal(TABLE, "Tutorat d'un identifiant absent de etudiants (X-02)", nb,
                              "Ligne retirée, conservée dans rejets/tutorat_sans_etudiant.csv", "D-24")]
    return resultat, nb, entrees, rejets


# ---------------------------------------------------------------------------
# Règle 7 : semaine de début
# ---------------------------------------------------------------------------

def regle_semaine_debut(df):
    """semaine_debut > 30 -> gardée, drapeau debut_hors_suivi (D-25) ;
    semaine_debut <= 0 -> manquant, drapeau debut_semaine_invalide (D-26). Audit TUT-06, TUT-09.
    """
    resultat = df.copy()
    semaine = df["semaine_debut"]
    hors_suivi = semaine.notna() & (semaine > config.N_SEMAINES)
    invalide = semaine.notna() & (semaine <= 0)
    resultat.loc[invalide, "semaine_debut"] = pd.NA
    drapeaux = ajouter_drapeau(df["_drapeaux"], hors_suivi, config.DRAPEAU_DEBUT_HORS_SUIVI)
    resultat["_drapeaux"] = ajouter_drapeau(drapeaux, invalide, config.DRAPEAU_DEBUT_SEMAINE_INVALIDE)
    entrees = [
        entree_journal(TABLE, "Tutorat commencé après la semaine 30 (45, 52 ; TUT-09)", int(hors_suivi.sum()),
                       "Valeur gardée, drapeau debut_hors_suivi (non tutoré pendant le suivi)", "D-25"),
        entree_journal(TABLE, "Tutorat commencé en « semaine 0 » (TUT-06)", int(invalide.sum()),
                       "semaine_debut mise à manquant, drapeau debut_semaine_invalide, étudiant gardé tutoré",
                       "D-26"),
    ]
    return resultat, int((hors_suivi | invalide).sum()), entrees


# ---------------------------------------------------------------------------
# Règle 8 : après la sortie
# ---------------------------------------------------------------------------

def regle_apres_sortie(df, sorties):
    """semaine_debut > semaine de sortie -> gardée, drapeau debut_apres_sortie (D-27, X-08)."""
    resultat = df.copy()
    semaine_sortie = df[config.COLONNE_ID].map(sorties)
    apres = (df["semaine_debut"].notna() & semaine_sortie.notna()
             & (df["semaine_debut"] > semaine_sortie)).fillna(False)
    resultat["_drapeaux"] = ajouter_drapeau(df["_drapeaux"], apres, config.DRAPEAU_DEBUT_APRES_SORTIE)
    nb = int(apres.sum())
    entrees = [entree_journal(TABLE, "Tutorat commencé après la semaine de sortie déclarée (X-08)", nb,
                              "Valeur gardée, drapeau debut_apres_sortie (non tutoré pendant son suivi)",
                              "D-22, D-27")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Enchaînement
# ---------------------------------------------------------------------------

def nettoyer(df_brut, etudiants, sorties):
    """Applique les 8 règles dans l'ordre.

    Entrées : table brute (texte), etudiants nettoyée, semaines de sortie.
    Sortie : (table nettoyée, rejets, lignes de journal, {règle: lignes touchées}).
    """
    entrees, touchees = [], {}
    df = df_brut
    for regle in [regle_entete_identifiants, regle_modalites, regle_nombres, regle_seances, regle_doublons]:
        df, nb, journal = regle(df)
        touchees[regle.__name__], entrees = nb, entrees + journal
    df, nb, journal, rejets = regle_orphelins(df, etudiants)
    touchees["regle_orphelins"], entrees = nb, entrees + journal
    df, nb, journal = regle_semaine_debut(df)
    touchees["regle_semaine_debut"], entrees = nb, entrees + journal
    df, nb, journal = regle_apres_sortie(df, sorties)
    touchees["regle_apres_sortie"], entrees = nb, entrees + journal
    df["drapeau_tutorat"] = drapeaux_en_texte(df["_drapeaux"])
    return df[COLONNES_SORTIE], rejets, entrees, touchees


def effectifs(df):
    """Effectifs de type_tuteur, de chaque drapeau et de chaque valeur de drapeau_tutorat."""
    par_drapeau = df["drapeau_tutorat"].dropna().str.split(config.SEPARATEUR_DRAPEAUX).explode()
    return [
        ("type_tuteur", {k: int(v) for k, v in df["type_tuteur"].value_counts().items()}),
        ("drapeau_tutorat (par drapeau)",
         {k: int(v) for k, v in par_drapeau.value_counts().reindex(DRAPEAUX, fill_value=0).items()}),
        ("drapeau_tutorat (par valeur de la colonne)",
         {k: int(v) for k, v in df["drapeau_tutorat"].value_counts().items()}),
    ]
