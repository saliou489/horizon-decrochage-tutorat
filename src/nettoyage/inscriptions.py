"""Nettoyage de la table « inscriptions » et cohérence avec « etudiants ».

Rôle du module : appliquer, dans l'ordre imposé par la consigne C03, les règles
validées par Saliou (décisions D-12 à D-17) à data/raw/inscriptions.csv, puis
construire les colonnes dérivées sortie_suivi et drapeau_inscription.
Chaque règle est une fonction : DataFrame en entrée -> (DataFrame corrigé, nombre de
lignes touchées, lignes de journal). Aucun numéro de semaine n'est calculé ici :
la conversion date -> semaine est un point ouvert de DA-07.

Tâche couverte : DA-03.
"""

import re
from datetime import datetime

import pandas as pd

from src import config
from src.nettoyage.commun import (
    ErreurNettoyage,
    entree_journal,
    est_vide,
    forme_simplifiee,
    harmoniser_modalites,
)

TABLE = "inscriptions"
COLONNES_SORTIE = ["id_etudiant", "annee_universitaire", "date_debut", "date_fin",
                   "statut_final", "sortie_suivi", "drapeau_inscription"]


# ---------------------------------------------------------------------------
# Lecture des dates
# ---------------------------------------------------------------------------

def lire_date(valeur):
    """Lit une date brute dans l'un des 4 formats observés (D-12).

    Formats : AAAA-MM-JJ, JJ/MM/AAAA, AAAA/MM/JJ et « J mois AAAA » en français
    (mois abrégé ou complet, avec ou sans point, avec ou sans accent).
    Sortie : la date (datetime), ou None si la case est vide.
    Une date illisible ou impossible arrête le nettoyage.
    """
    texte = valeur.strip()
    if texte == "":
        return None
    formats_numeriques = {
        r"\d{4}-\d{1,2}-\d{1,2}": "%Y-%m-%d",
        r"\d{1,2}/\d{1,2}/\d{4}": "%d/%m/%Y",
        r"\d{4}/\d{1,2}/\d{1,2}": "%Y/%m/%d",
    }
    try:
        for motif, format_date in formats_numeriques.items():
            if re.fullmatch(motif, texte):
                return datetime.strptime(texte, format_date)
        morceaux = re.fullmatch(r"(\d{1,2})\s+(\S+)\s+(\d{4})", texte)
        if morceaux:
            mois = forme_simplifiee(morceaux.group(2)).rstrip(".")
            if mois in config.MOIS_FR_SIMPLIFIES:
                return datetime(int(morceaux.group(3)), config.MOIS_FR_SIMPLIFIES[mois],
                                int(morceaux.group(1)))
    except ValueError:
        pass  # date au bon format mais impossible (ex. 31/02) : signalée ci-dessous
    raise ErreurNettoyage(f"Date illisible ou impossible : «{valeur}»")


def ecrire_date(date):
    """Date -> texte AAAA-MM-JJ ; manquant si la date l'est."""
    if date is None or pd.isna(date):
        return pd.NA
    return date.strftime(config.FORMAT_DATE_PROCESSED)


# ---------------------------------------------------------------------------
# Règle 1 : identifiants
# ---------------------------------------------------------------------------

def regle_identifiants(df):
    """Majuscules, espaces retirés ; format HZ + 5 chiffres, sinon arrêt."""
    resultat = df.copy()
    avant = df[config.COLONNE_ID]
    apres = avant.str.replace(r"\s+", "", regex=True).str.upper()
    mal_formes = sorted(set(apres[~apres.str.fullmatch(config.FORMAT_ID_ETUDIANT)]))
    if mal_formes:
        raise ErreurNettoyage(f"Identifiant(s) mal formé(s) après correction : {mal_formes}")
    resultat[config.COLONNE_ID] = apres
    nb = int((apres != avant).sum())
    entrees = [entree_journal(TABLE, "Identifiant en minuscules ou entouré d'espaces", nb,
                              "Mis en majuscules, espaces retirés", "D-12")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 2 : statuts
# ---------------------------------------------------------------------------

def regle_statuts(df):
    """Ramène statut_final à inscrit / abandon / transfert (D-12).

    Forme simplifiée (minuscules, sans accents ni espaces superflus) ;
    « abandonné » -> abandon, « transféré » -> transfert. Une valeur imprévue arrête
    le nettoyage ; un statut vide reste vide (D-15).
    """
    resultat = df.copy()
    harmonise, nb = harmoniser_modalites(
        df["statut_final"], config.MODALITES[(TABLE, "statut_final")],
        config.ABREVIATIONS[(TABLE, "statut_final")], "statut_final")
    resultat["statut_final"] = harmonise
    entrees = [entree_journal(TABLE, "statut_final écrit de plusieurs façons (casse, espaces, accents, INS-04)",
                              nb, "Recodage vers inscrit / abandon / transfert", "D-12")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 3 : dates
# ---------------------------------------------------------------------------

def regle_dates(df):
    """Lit les 4 formats de date et les écrit en AAAA-MM-JJ (D-12).

    Les cases vides de date_fin restent vides (toujours inscrit ou date inconnue).
    """
    resultat = df.copy()
    touchees = pd.Series(False, index=df.index)
    entrees = []
    for colonne in ["date_debut", "date_fin"]:
        lues = df[colonne].map(lire_date)
        ecrites = lues.map(ecrire_date)
        changees = ecrites.notna() & (ecrites != df[colonne].str.strip())
        touchees = touchees | changees
        resultat[colonne] = ecrites
        code = "INS-05" if colonne == "date_debut" else "INS-06"
        entrees.append(entree_journal(TABLE, f"{colonne} dans un autre format que AAAA-MM-JJ "
                                      f"(JJ/MM/AAAA, AAAA/MM/JJ, « 7 oct. 2024 » ; {code})", int(changees.sum()),
                                      "Date convertie en AAAA-MM-JJ", "D-12"))
    return resultat, int(touchees.sum()), entrees


# ---------------------------------------------------------------------------
# Règle 4 : doublons exacts
# ---------------------------------------------------------------------------

def regle_doublons(df):
    """Supprime les lignes identiques (après les règles 1 à 3) : une ligne par étudiant.

    Si un étudiant a encore deux lignes différentes, le nettoyage s'arrête (D-12 ne
    couvre que les doublons exacts).
    """
    identiques = df.duplicated(keep="first")
    resultat = df[~identiques].reset_index(drop=True)
    encore_doubles = sorted(set(resultat.loc[resultat.duplicated(config.COLONNE_ID), config.COLONNE_ID]))
    if encore_doubles:
        raise ErreurNettoyage(f"Étudiant(s) avec deux inscriptions différentes : {encore_doubles}")
    nb = int(identiques.sum())
    entrees = [entree_journal(TABLE, "Inscription strictement identique à une ligne précédente (INS-01, INS-02)",
                              nb, "Ligne supprimée", "D-12")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 5 : dates inversées
# ---------------------------------------------------------------------------

def rentrees_de_reference(df):
    """Rentrée de référence de chaque année universitaire : la date_debut la plus fréquente.

    Sortie : dictionnaire {annee_universitaire: date AAAA-MM-JJ}.
    """
    return {annee: groupe["date_debut"].mode().iloc[0]
            for annee, groupe in df.groupby("annee_universitaire")}


def regle_dates_inversees(df):
    """Échange date_debut et date_fin quand elles ont été saisies à l'envers (D-13).

    Règle : date_fin < date_debut ET date_fin = rentrée de référence de l'année.
    Tout autre cas date_fin < date_debut arrête le nettoyage.
    Les dates sont en AAAA-MM-JJ : la comparaison de textes suit l'ordre des dates.
    Sortie : (table, nb lignes, journal, masque des lignes échangées pour le drapeau).
    """
    resultat = df.copy()
    reference = df["annee_universitaire"].map(rentrees_de_reference(df))
    # Une date_fin manquante est remplacée par "" le temps de la comparaison (jamais échangée).
    date_fin = df["date_fin"].fillna("")
    fin_avant_debut = (date_fin != "") & (date_fin < df["date_debut"])
    echangeables = fin_avant_debut & (date_fin == reference)
    autres = fin_avant_debut & ~echangeables
    if autres.any():
        raise ErreurNettoyage("date_fin < date_debut sans correspondre à la rentrée : "
                              f"{list(df.loc[autres, config.COLONNE_ID])}")
    resultat.loc[echangeables, "date_debut"] = df.loc[echangeables, "date_fin"]
    resultat.loc[echangeables, "date_fin"] = df.loc[echangeables, "date_debut"]
    nb = int(echangeables.sum())
    entrees = [entree_journal(TABLE, "date_fin antérieure à date_debut, date_fin égale à la rentrée de la "
                              "cohorte (INS-07, INS-08, INS-09, INS-10)", nb, "date_debut et date_fin échangées",
                              "D-13")]
    return resultat, nb, entrees, echangeables


# ---------------------------------------------------------------------------
# Règle 6 : orphelins
# ---------------------------------------------------------------------------

def regle_orphelins(df, etudiants):
    """Retire les inscriptions dont l'étudiant est absent de etudiants (D-17).

    Sortie : (table sans orphelins, nb lignes, journal, table des rejets). Les rejets
    sont écrits à part par l'appelant (data/processed/rejets/).
    """
    connus = set(etudiants[config.COLONNE_ID])
    orphelins = ~df[config.COLONNE_ID].isin(connus)
    rejets = df[orphelins].reset_index(drop=True)
    resultat = df[~orphelins].reset_index(drop=True)
    nb = int(orphelins.sum())
    entrees = [entree_journal(TABLE, "Inscription d'un identifiant absent de etudiants (X-01)", nb,
                              "Ligne retirée et conservée dans data/processed/rejets/"
                              "inscriptions_sans_etudiant.csv", "D-17")]
    return resultat, nb, entrees, rejets


# ---------------------------------------------------------------------------
# Règle 7 : contrôle de la rentrée
# ---------------------------------------------------------------------------

def annee_vers_cohorte(annee_universitaire):
    """« 2024-2025 » -> 2024 (année de rentrée)."""
    return int(annee_universitaire.split("-")[0])


def regle_controle_rentree(df, etudiants):
    """Vérifie date_debut = rentrée de référence et année universitaire = cohorte.

    Contrôle seulement : aucun changement. Un écart arrête le nettoyage.
    """
    reference = df["annee_universitaire"].map(rentrees_de_reference(df))
    autre_rentree = df["date_debut"] != reference
    cohorte = df[config.COLONNE_ID].map(etudiants.set_index(config.COLONNE_ID)["cohorte"])
    autre_cohorte = df["annee_universitaire"].map(annee_vers_cohorte) != cohorte
    ecarts = autre_rentree | autre_cohorte
    if ecarts.any():
        raise ErreurNettoyage("Rentrée ou année universitaire incohérente pour : "
                              f"{list(df.loc[ecarts, config.COLONNE_ID])}")
    entrees = [entree_journal(TABLE, "Contrôle : date_debut différente de la rentrée de référence, ou "
                              "année universitaire différente de la cohorte", 0,
                              "Aucun écart après échange des dates inversées : rien à corriger",
                              "D-13, D-17")]
    return df, 0, entrees


# ---------------------------------------------------------------------------
# Règle 8 : étudiants sans inscription
# ---------------------------------------------------------------------------

def regle_inscriptions_reconstituees(df, etudiants):
    """Ajoute une inscription aux étudiants qui n'en ont pas (D-17).

    Année universitaire de leur cohorte (2024 -> 2024-2025), date_debut = rentrée de
    référence de cette année, statut et date_fin vides.
    Sortie : (table, nb lignes ajoutées, journal, identifiants ajoutés).
    """
    reference = rentrees_de_reference(df)
    cohorte_vers_annee = {int(c): a for a, c in config.ANNEE_VERS_COHORTE.items()}
    manquants = etudiants[~etudiants[config.COLONNE_ID].isin(set(df[config.COLONNE_ID]))]
    nouvelles = pd.DataFrame({
        config.COLONNE_ID: manquants[config.COLONNE_ID].values,
        "annee_universitaire": [cohorte_vers_annee[int(c)] for c in manquants["cohorte"]],
    })
    nouvelles["date_debut"] = nouvelles["annee_universitaire"].map(reference)
    nouvelles["date_fin"] = pd.NA
    nouvelles["statut_final"] = ""
    resultat = pd.concat([df, nouvelles], ignore_index=True)
    nb = len(nouvelles)
    entrees = [entree_journal(TABLE, "Étudiant sans aucune inscription (X-03)", nb,
                              "Inscription ajoutée : année et rentrée de sa cohorte, statut et date_fin vides",
                              "D-17")]
    return resultat, nb, entrees, set(nouvelles[config.COLONNE_ID])


# ---------------------------------------------------------------------------
# Règles 9 et 10 : sortie_suivi et drapeau_inscription
# ---------------------------------------------------------------------------

def fin_du_suivi(date_debut):
    """Date de fin du suivi : date_debut + N_SEMAINES semaines (texte AAAA-MM-JJ)."""
    debut = datetime.strptime(date_debut, config.FORMAT_DATE_PROCESSED)
    return ecrire_date(debut + pd.Timedelta(weeks=config.N_SEMAINES))


def sortie_et_drapeaux(ligne, reconstituee, inversee):
    """Calcule (sortie_suivi, liste de drapeaux) pour une inscription.

    D-14 : abandon daté après le suivi -> aucune sortie déclarée.
    D-15 : statut vide -> aucune sortie déclarée.
    D-16 : abandon sans date -> abandon, semaine déterminée en DA-07.
    Un transfert sans date ou daté après le suivi n'est couvert par aucune décision :
    arrêt.
    """
    drapeaux = [config.DRAPEAU_DATES_INVERSEES] if inversee else []
    statut = ligne["statut_final"]
    date_fin = ligne["date_fin"]
    if reconstituee:
        return config.SORTIE_AUCUNE, drapeaux + [config.DRAPEAU_INSCRIPTION_RECONSTITUEE]
    if statut == "":
        return config.SORTIE_AUCUNE, drapeaux + [config.DRAPEAU_STATUT_VIDE]
    if statut == "inscrit":
        return config.SORTIE_AUCUNE, drapeaux
    sans_date = pd.isna(date_fin)
    dans_suivi = (not sans_date) and date_fin < fin_du_suivi(ligne["date_debut"])
    if statut == "abandon":
        if sans_date:
            return config.SORTIE_ABANDON, drapeaux + [config.DRAPEAU_ABANDON_SANS_DATE]
        if dans_suivi:
            return config.SORTIE_ABANDON, drapeaux
        return config.SORTIE_AUCUNE, drapeaux + [config.DRAPEAU_ABANDON_HORS_SUIVI]
    if dans_suivi:  # transfert daté pendant le suivi
        return config.SORTIE_TRANSFERT, drapeaux
    raise ErreurNettoyage(f"Transfert sans date_fin ou daté après le suivi : {ligne[config.COLONNE_ID]}")


def regle_sortie_et_drapeaux(df, reconstituees, inversees):
    """Ajoute sortie_suivi et drapeau_inscription ; statut_final et date_fin sont conservés.

    Entrées : la table, les identifiants des inscriptions reconstituées (règle 8),
    les identifiants dont les dates ont été échangées (règle 5).
    """
    resultat = df.copy()
    calculs = [sortie_et_drapeaux(ligne, ligne[config.COLONNE_ID] in reconstituees,
                                  ligne[config.COLONNE_ID] in inversees)
               for _, ligne in df.iterrows()]
    resultat["sortie_suivi"] = [sortie for sortie, _ in calculs]
    resultat["drapeau_inscription"] = [config.SEPARATEUR_DRAPEAUX.join(d) if d else pd.NA
                                       for _, d in calculs]
    abandons_hors_suivi = resultat["drapeau_inscription"].fillna("").str.contains(
        config.DRAPEAU_ABANDON_HORS_SUIVI)
    statuts_vides = resultat["drapeau_inscription"].fillna("").str.contains(config.DRAPEAU_STATUT_VIDE)
    abandons_sans_date = resultat["drapeau_inscription"].fillna("").str.contains(
        config.DRAPEAU_ABANDON_SANS_DATE)
    entrees = [
        entree_journal(TABLE, "Abandon daté après la fin du suivi (date_fin ≥ date_debut + 30 semaines, INS-11)",
                       int(abandons_hors_suivi.sum()), "sortie_suivi = aucune_sortie_declaree, ligne gardée, "
                       "drapeau abandon_hors_suivi", "D-14"),
        entree_journal(TABLE, "statut_final vide (INS-03)", int(statuts_vides.sum()),
                       "sortie_suivi = aucune_sortie_declaree, statut laissé vide, drapeau statut_vide", "D-15"),
        entree_journal(TABLE, "Abandon sans date_fin (INS-12)", int(abandons_sans_date.sum()),
                       "sortie_suivi = abandon, date_fin laissée vide (semaine à déterminer en DA-07), "
                       "drapeau abandon_sans_date", "D-16"),
    ]
    nb = int((abandons_hors_suivi | statuts_vides | abandons_sans_date).sum())
    return resultat[COLONNES_SORTIE], nb, entrees


# ---------------------------------------------------------------------------
# Enchaînement
# ---------------------------------------------------------------------------

def nettoyer(df_brut, etudiants):
    """Applique les 10 règles dans l'ordre.

    Entrées : table brute (texte), table etudiants nettoyée (data/processed/etudiants.csv).
    Sortie : (table nettoyée, rejets, lignes de journal, {règle: lignes touchées}).
    """
    entrees = []
    touchees = {}

    df = df_brut
    for regle in [regle_identifiants, regle_statuts, regle_dates, regle_doublons]:
        df, nb, journal = regle(df)
        touchees[regle.__name__] = nb
        entrees += journal

    df, nb, journal, masque_inversees = regle_dates_inversees(df)
    inversees = set(df.loc[masque_inversees, config.COLONNE_ID])
    touchees["regle_dates_inversees"] = nb
    entrees += journal

    df, nb, journal, rejets = regle_orphelins(df, etudiants)
    touchees["regle_orphelins"] = nb
    entrees += journal

    df, nb, journal = regle_controle_rentree(df, etudiants)
    touchees["regle_controle_rentree"] = nb
    entrees += journal

    df, nb, journal, reconstituees = regle_inscriptions_reconstituees(df, etudiants)
    touchees["regle_inscriptions_reconstituees"] = nb
    entrees += journal

    df, nb, journal = regle_sortie_et_drapeaux(df, reconstituees, inversees)
    touchees["regle_sortie_et_drapeaux"] = nb
    entrees += journal

    df["statut_final"] = df["statut_final"].where(~est_vide(df["statut_final"].fillna("")), pd.NA)
    return df, rejets, entrees, touchees


def effectifs(df):
    """Effectifs de sortie_suivi et de chaque drapeau, pour le journal."""
    sorties = df["sortie_suivi"].value_counts().reindex(config.VALEURS_SORTIE_SUIVI, fill_value=0)
    drapeaux = df["drapeau_inscription"].dropna().str.split(config.SEPARATEUR_DRAPEAUX).explode()
    liste_drapeaux = [config.DRAPEAU_DATES_INVERSEES, config.DRAPEAU_ABANDON_HORS_SUIVI,
                      config.DRAPEAU_STATUT_VIDE, config.DRAPEAU_ABANDON_SANS_DATE,
                      config.DRAPEAU_INSCRIPTION_RECONSTITUEE]
    comptes_drapeaux = drapeaux.value_counts().reindex(liste_drapeaux, fill_value=0)
    return [
        ("sortie_suivi", {k: int(v) for k, v in sorties.items()}),
        ("drapeau_inscription", {k: int(v) for k, v in comptes_drapeaux.items()}),
    ]
