"""Construction de T et E, de base_survie.csv et du format période-personne.

Rôle du module : à partir des tables nettoyées (data/processed/), calculer pour chaque
étudiant la durée T (en semaines) et l'indicateur d'événement E selon les définitions
imposées (cahier §4.3, CLAUDE.md §5) et les décisions D-22, D-25 à D-27, D-30 à D-39,
puis écrire base_survie.csv (une ligne par étudiant) et base_periode_personne.csv
(une ligne par étudiant et par semaine, de 1 à T).
Un cas non couvert par une décision arrête le calcul (principe D-18).
Lancement depuis la racine du dépôt : python -m src.base_survie

Tâche couverte : DA-07.
"""

import pandas as pd

from src import config
from src.nettoyage.commun import ErreurNettoyage, semaine_depuis_date


# ===========================================================================
# 1. Lecture des tables nettoyées
# ===========================================================================

def lire_tables():
    """Lit les tables nettoyées utiles. Sortie : dictionnaire {nom: DataFrame}."""
    def lire(nom, types=None):
        return pd.read_csv(config.DOSSIER_PROCESSED / f"{nom}.csv", sep=config.SEPARATEUR_PROCESSED,
                           dtype=types, encoding=config.ENCODAGE)

    entiers_activite = {c: "Int64" for c in config.COLONNES_ENTIERES_ACTIVITE}
    return {
        "etudiants": lire("etudiants", {"cohorte": "Int64", "age": "Int64"}),
        "inscriptions": lire("inscriptions", str),
        "activite_hebdo": lire("activite_hebdo", entiers_activite),
        "tutorat": lire("tutorat", {"semaine_debut": "Int64", "nb_seances": "Int64"}),
    }


# ===========================================================================
# 2. État d'une semaine et séries d'inactivité
# ===========================================================================

def etat_semaine(connexions, devoirs):
    """État d'une semaine (D-31).

    actif : au moins une connexion ou un devoir rendu ;
    inactif : 0 connexion ET 0 devoir (les deux connus) ;
    inconnu : une valeur manque et l'autre ne montre aucune activité.
    """
    connexions_connues = not pd.isna(connexions)
    devoirs_connus = not pd.isna(devoirs)
    if (connexions_connues and connexions > 0) or (devoirs_connus and devoirs > 0):
        return config.ETAT_ACTIF
    if connexions_connues and devoirs_connus:
        return config.ETAT_INACTIF
    return config.ETAT_INCONNU


def ajouter_etats(activite):
    """Ajoute la colonne etat_activite à la table d'activité (une valeur par semaine)."""
    resultat = activite.copy()
    resultat["etat_activite"] = [etat_semaine(c, d) for c, d in
                                 zip(activite["nb_connexions_lms"], activite["devoirs_rendus"])]
    return resultat


def premiere_serie(etats, seuil, lecture_inconnu=config.LECTURE_INCONNU_REFERENCE):
    """Première semaine d'une suite de `seuil` semaines consécutives inactives.

    Entrées : liste des états des semaines 1, 2, 3… (dans l'ordre, sans trou) ; seuil ;
    lecture des semaines inconnues : « active » (référence, elles coupent une série) ou
    « inactive » (sensibilité, elles comptent comme inactives).
    Sortie : numéro de la première semaine de la série, ou None s'il n'y en a pas.
    Une série coupée par la fin des données (moins de `seuil` semaines) ne compte pas.
    """
    comptees_inactives = {config.ETAT_INACTIF}
    if lecture_inconnu == config.LECTURE_INCONNU_SENSIBILITE:
        comptees_inactives.add(config.ETAT_INCONNU)
    longueur = 0
    for position, etat in enumerate(etats):
        longueur = longueur + 1 if etat in comptees_inactives else 0
        if longueur == seuil:
            return position - seuil + 2  # semaine (numérotée à partir de 1) du début de la série
    return None


# ===========================================================================
# 3. T et E d'un étudiant
# ===========================================================================

def situation_de_sortie(inscription):
    """Situation de sortie d'un étudiant lue dans inscriptions nettoyée.

    Sortie : (type, semaine de sortie ou None) avec type parmi abandon_declare,
    abandon_sans_date, abandon_date_invalide, transfert, aucune.
    """
    drapeaux = str(inscription["drapeau_inscription"]) if pd.notna(inscription["drapeau_inscription"]) else ""
    sortie = inscription["sortie_suivi"]
    date_fin = inscription["date_fin"]
    if config.DRAPEAU_ABANDON_HORS_SUIVI in drapeaux.split(config.SEPARATEUR_DRAPEAUX):
        return config.EVENEMENT_ABANDON_DATE_INVALIDE, None  # D-33
    if sortie == config.SORTIE_ABANDON and pd.isna(date_fin):
        return config.EVENEMENT_ABANDON_SANS_DATE, None  # D-16, D-32
    semaine_sortie = None if pd.isna(date_fin) else semaine_depuis_date(date_fin, inscription["date_debut"])
    if sortie == config.SORTIE_ABANDON:
        return config.EVENEMENT_ABANDON_DECLARE, semaine_sortie
    if sortie == config.SORTIE_TRANSFERT:
        if semaine_sortie is None:
            raise ErreurNettoyage(f"Transfert sans date pour {inscription[config.COLONNE_ID]}")
        return config.EVENEMENT_TRANSFERT, semaine_sortie
    return "aucune", None


def t_et_e(identifiant, semaines, etats, situation, seuil, lecture_inconnu):
    """Calcule (T, E, type_evenement) pour un étudiant (tableau de la consigne C06).

    Entrées : identifiant ; semaines et états d'activité triés ; situation de sortie
    (situation_de_sortie) ; seuil d'inactivité ; lecture des semaines inconnues.
    Arrête le calcul sur les cas absents des données (D-18) : série d'inactivité avant
    une sortie déclarée (D-30), abandon à date invalide avec série ou activité jusqu'à 30
    (D-33), semaine manquante entre 1 et la dernière semaine (RV01-07).
    """
    type_sortie, semaine_sortie = situation
    derniere = semaines[-1]
    # premiere_serie compte des positions dans la liste : elle n'a de sens que si la liste
    # est exactement 1, 2, …, dernière. Un trou (même après le début d'une série) arrête tout.
    if semaines != list(range(1, derniere + 1)):
        raise ErreurNettoyage(f"Semaine d'activité manquante entre 1 et {derniere} : {identifiant}")
    serie = premiere_serie(etats, seuil, lecture_inconnu)

    if type_sortie == config.EVENEMENT_ABANDON_DATE_INVALIDE:
        if serie is not None or derniere == config.N_SEMAINES:
            raise ErreurNettoyage(f"Abandon à date invalide avec série ou activité jusqu'à 30 : {identifiant}")
        resultat = (derniere, 1, type_sortie)
    elif type_sortie == config.EVENEMENT_ABANDON_SANS_DATE:
        resultat = (derniere, 1, type_sortie)
    elif type_sortie == config.EVENEMENT_ABANDON_DECLARE:
        resultat = (semaine_sortie, 1, type_sortie)
    elif type_sortie == config.EVENEMENT_TRANSFERT:
        resultat = (semaine_sortie, 0, type_sortie)
    elif serie is not None:
        resultat = (serie, 1, config.EVENEMENT_DECROCHAGE_SILENCIEUX)
    elif derniere < config.N_SEMAINES:
        resultat = (derniere, 0, config.EVENEMENT_PERDU_DE_VUE)  # D-34
    else:
        resultat = (config.N_SEMAINES, 0, config.EVENEMENT_FIN_DE_SUIVI)

    sortie_declaree = type_sortie in (config.EVENEMENT_ABANDON_DECLARE, config.EVENEMENT_ABANDON_SANS_DATE,
                                      config.EVENEMENT_TRANSFERT)
    if sortie_declaree and serie is not None and serie <= resultat[0]:
        raise ErreurNettoyage(f"Série d'inactivité avant une sortie déclarée : {identifiant}")
    if resultat[0] is None or resultat[0] > derniere:
        raise ErreurNettoyage(f"Semaine d'activité manquante entre 1 et T = {resultat[0]} : {identifiant}")
    return resultat


def construire_t_e(activite_etats, inscriptions, seuil=config.SEUIL_INACTIVITE,
                   lecture_inconnu=config.LECTURE_INCONNU_REFERENCE):
    """T, E et type_evenement de chaque étudiant.

    Entrées : activité avec etat_activite (ajouter_etats), inscriptions nettoyée,
    seuil d'inactivité, lecture des semaines inconnues.
    Sortie : DataFrame id_etudiant, T, E, type_evenement.
    """
    situations = {ligne[config.COLONNE_ID]: situation_de_sortie(ligne) for _, ligne in inscriptions.iterrows()}
    triee = activite_etats.sort_values([config.COLONNE_ID, "semaine"])
    lignes = []
    for identifiant, groupe in triee.groupby(config.COLONNE_ID, sort=False):
        T, E, type_evenement = t_et_e(identifiant, [int(s) for s in groupe["semaine"]],
                                      list(groupe["etat_activite"]), situations[identifiant],
                                      seuil, lecture_inconnu)
        lignes.append({config.COLONNE_ID: identifiant, "T": T, "E": E, "type_evenement": type_evenement})
    return pd.DataFrame(lignes)


# ===========================================================================
# 4. Tutorat
# ===========================================================================

def statut_tutorat(semaine_debut, a_un_tutorat, T):
    """Statut de tutorat d'un étudiant par rapport à son T de référence (D-37)."""
    if not a_un_tutorat:
        return config.STATUT_NON_TUTORE
    if pd.isna(semaine_debut):
        return config.STATUT_TUTORAT_SEMAINE_INCONNUE
    if semaine_debut < T:
        return config.STATUT_TUTORE
    if semaine_debut == T:
        return config.STATUT_TUTORAT_MEME_SEMAINE
    return config.STATUT_TUTORAT_APRES_T


def ajouter_tutorat(base, tutorat):
    """Ajoute à base (qui contient T) les colonnes de tutorat (D-36, D-37).

    tutore = 1 si tutorat commencé strictement avant T, ou à une semaine inconnue.
    semaine_debut_tutorat = valeur de la table tutorat (vide sans tutorat ou si inconnue).
    """
    colonnes = tutorat[[config.COLONNE_ID, "semaine_debut", "type_tuteur", "motif_orientation", "nb_seances"]]
    resultat = base.merge(colonnes, on=config.COLONNE_ID, how="left", validate="one_to_one")
    a_un_tutorat = resultat[config.COLONNE_ID].isin(set(tutorat[config.COLONNE_ID]))
    resultat["statut_tutorat"] = [statut_tutorat(s, a, T) for s, a, T in
                                  zip(resultat["semaine_debut"], a_un_tutorat, resultat["T"])]
    resultat["tutore"] = resultat["statut_tutorat"].isin(config.STATUTS_TUTORE).astype(int)
    return resultat.rename(columns={"semaine_debut": "semaine_debut_tutorat"})


# ===========================================================================
# 5. Tables finales
# ===========================================================================

def construire_base_survie(tables):
    """base_survie : une ligne par étudiant de etudiants.csv (D-36, D-38).

    Sortie : (base_survie, activité avec états). T et E de référence (seuil 4,
    semaines inconnues lues « actives »), plus T et E aux seuils 3 et 5.
    """
    activite = ajouter_etats(tables["activite_hebdo"])
    reference = construire_t_e(activite, tables["inscriptions"])
    base = tables["etudiants"].merge(reference, on=config.COLONNE_ID, how="left", validate="one_to_one")
    for seuil in config.SEUILS_SENSIBILITE:
        variante = construire_t_e(activite, tables["inscriptions"], seuil=seuil)
        variante = variante.rename(columns={"T": f"T_seuil{seuil}", "E": f"E_seuil{seuil}"})
        base = base.merge(variante.drop(columns="type_evenement"), on=config.COLONNE_ID, how="left",
                          validate="one_to_one")
    if base["T"].isna().any() or len(base) != len(tables["etudiants"]):
        raise ErreurNettoyage("Étudiant sans T ou ligne perdue dans base_survie")
    base = ajouter_tutorat(base, tables["tutorat"])
    return base[config.COLONNES_BASE_SURVIE], activite


def ajouter_activite_prec(activite):
    """Ajoute les colonnes *_prec : activité de la semaine précédente du même étudiant (D-42).

    Entrée : activité avec etat_activite (semaines 1, 2, … sans trou, vérifié dans t_et_e).
    Sortie : copie triée par étudiant et semaine, avec 5 colonnes de plus, vides en semaine 1.
    """
    resultat = activite.sort_values([config.COLONNE_ID, "semaine"]).copy()
    # shift(1) par étudiant : la ligne de la semaine s reçoit les valeurs de la semaine s − 1 ;
    # la première semaine de chaque étudiant n'a pas de semaine précédente (vide).
    precedent = resultat.groupby(config.COLONNE_ID, sort=False)[config.COLONNES_ACTIVITE_SEMAINE].shift(1)
    for colonne in config.COLONNES_ACTIVITE_SEMAINE:
        resultat[colonne + config.SUFFIXE_PREC] = precedent[colonne]
    return resultat


def construire_periode_personne(base, activite):
    """Format période-personne : une ligne par étudiant et par semaine 1 … T (D-39).

    evenement = 1 seulement à la semaine T si E = 1 ;
    tutorat_commence = 1 si semaine > semaine_debut_tutorat pour les « tutore »,
    0 pour les autres, vide pour les tutorats à semaine inconnue.
    Colonnes *_prec (D-42) : activité de la semaine précédente du même étudiant
    (nb_connexions_lms_prec, devoirs_rendus_prec, note_moyenne_prec, absences_prec,
    etat_activite_prec), vides en semaine 1. Ce sont les seules colonnes d'activité qu'un
    modèle semaine par semaine peut utiliser : l'activité de la semaine en cours sert à
    définir l'événement (une série d'inactivité commence à la semaine T).
    """
    colonnes_base = [config.COLONNE_ID, "T", "E", "statut_tutorat", "semaine_debut_tutorat"]
    activite = ajouter_activite_prec(activite)
    periode = activite.merge(base[colonnes_base], on=config.COLONNE_ID, how="inner")
    periode = periode[periode["semaine"] <= periode["T"]].sort_values([config.COLONNE_ID, "semaine"])
    periode["evenement"] = ((periode["semaine"] == periode["T"]) & (periode["E"] == 1)).astype(int)
    tutore_connu = periode["statut_tutorat"] == config.STATUT_TUTORE
    commence = (tutore_connu & (periode["semaine"] > periode["semaine_debut_tutorat"])).fillna(False)
    periode["tutorat_commence"] = pd.array(commence.astype(int), dtype="Int64")
    inconnu = periode["statut_tutorat"] == config.STATUT_TUTORAT_SEMAINE_INCONNUE
    periode.loc[inconnu, "tutorat_commence"] = pd.NA
    return periode[config.COLONNES_PERIODE_PERSONNE].reset_index(drop=True)


def ecrire(df, chemin):
    """Écrit une table finale en CSV (UTF-8, séparateur « , », sans index)."""
    df.to_csv(chemin, sep=config.SEPARATEUR_PROCESSED, index=False, encoding=config.ENCODAGE)
    return chemin


def lancer():
    """Point d'entrée : construit et écrit base_survie.csv et base_periode_personne.csv."""
    tables = lire_tables()
    base, activite = construire_base_survie(tables)
    periode = construire_periode_personne(base, activite)
    ecrire(base, config.FICHIER_BASE_SURVIE)
    ecrire(periode, config.FICHIER_PERIODE_PERSONNE)
    print(f"base_survie : {len(base)} étudiants, E = 1 pour {int(base['E'].sum())}")
    print(f"période-personne : {len(periode)} lignes")
    return base, periode


if __name__ == "__main__":
    lancer()
