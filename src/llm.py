"""Fiches d'alerte rédigées par un LLM (Gemini) pour les conseillers pédagogiques.

Rôle du module :
- construire, sans réseau, l'entrée de chaque fiche : une liste fermée de champs (risque
  du Cox, facteurs, activité récente, tutorat), sans identifiant ni donnée personnelle
  (D-65, D-66) ;
- construire le prompt à partir du gabarit versionné (src/prompts/), appeler l'API
  Gemini (commande séparée, jamais par run_all.py), contrôler chaque fiche (chiffres
  présents dans l'entrée, mots interdits, actions de la liste) et la redemander si besoin ;
- tirer l'échantillon d'évaluation (LL-02) et écrire la grille à remplir par Saliou.
Le LLM rédige ; il ne décide de rien : chaque fiche porte un avertissement et reste à
vérifier par le conseiller.

Tâches couvertes : LL-01, LL-02.

Commandes : python -m src.llm --entrees | --tester | --generer [--forcer | --revoir] [--limite N] | --verifier | --grille
"""

import argparse
import json
import math
import os
import re
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
from dotenv import dotenv_values

from src import config, eda, ml_survie, survie


class ErreurLLM(Exception):
    """Cas non prévu, entrée non conforme ou erreur de l'API : on s'arrête sans rien envoyer."""


class ErreurQuotaLLM(ErreurLLM):
    """Quota de l'API atteint (erreur 429) ou service surchargé (503)."""


# Colonne de la valeur brute de chaque facteur affichable (la distance du Cox est en log2).
COLONNE_BRUTE = {"age": "age", "note_bac": "note_bac", config.COLONNE_DISTANCE_COX: "distance_campus_km",
                 "boursier": "boursier", "emploi_parallele": "emploi_parallele", "filiere": "filiere"}
VARIABLES_QUALITATIVES_FICHE = ["boursier", "emploi_parallele", "filiere"]
# Noms des champs d'activité vus par le LLM (mots simples) -> colonnes de base_periode_personne.
CHAMPS_ACTIVITE = {"connexions_plateforme": "nb_connexions_lms", "devoirs_rendus": "devoirs_rendus",
                   "seances_manquees": "absences", "note_moyenne": "note_moyenne"}
NOTE_MAXIMUM = config.BORNES[("activite_hebdo", "note_moyenne")]["max"]
NOTE_MAXIMUM_BAC = config.BORNES[("etudiants", "note_bac")]["max"]
# Clés autorisées de l'entrée, à chaque niveau, dans l'ordre (D-65, point 3).
CLES_ENTREE = ["semaine_observation", "horizon_semaines", "risque_decrochage_pct", "risque_moyen_promotion_pct",
               "facteurs", "activite", "activite_promotion", "tutorat"]
CLES_FACTEUR = ["facteur", "valeur_etudiant", "reference_promotion", "multiplicateur"]
CLES_ACTIVITE = ["semaines", "note_maximum"] + list(CHAMPS_ACTIVITE)
CLES_ACTIVITE_PROMOTION = list(CHAMPS_ACTIVITE)
CLES_FICHE = ["situation", "points_attention", "actions"]
TITRE_INSTRUCTIONS = "## Instructions système"
TITRE_MESSAGE = "## Message"
MESSAGE_TEST = "Réponds uniquement par le mot OK."
LONGUEUR_MAX_REPONSE_BRUTE = 2000
CODES_QUOTA = (429, 503)
# Formats exacts des textes de l'entrée, tels que le code les écrit (D-67, point 2), par facteur.
# Un texte qui ne suit pas son format (nom propre, instruction, texte libre) bloque l'envoi.
FORMATS_VALEUR_FACTEUR = {
    "age": r"\d{1,2} ans",
    "note_bac": r"\d{1,2},\d / " + str(NOTE_MAXIMUM_BAC),
    config.COLONNE_DISTANCE_COX: r"\d{1,4} km",
    "boursier": r"boursier|non boursier",
    "emploi_parallele": r"oui|non",
    "filiere": "|".join(re.escape(filiere) for filiere in config.MODALITES[("etudiants", "filiere")]),
}
FORMAT_REFERENCE_MODALITE = r"\d{1,3} % de la promotion dans ce cas"
FORMATS_REFERENCE_FACTEUR = {
    "age": r"\d{1,2},\d ans en moyenne dans la promotion",
    "note_bac": r"\d{1,2},\d / " + str(NOTE_MAXIMUM_BAC) + r" en moyenne dans la promotion",
    config.COLONNE_DISTANCE_COX: r"\d{1,4} km pour un étudiant typique de la promotion",
    "boursier": FORMAT_REFERENCE_MODALITE,
    "emploi_parallele": FORMAT_REFERENCE_MODALITE,
    "filiere": FORMAT_REFERENCE_MODALITE,
}
VARIABLE_DU_LIBELLE = {libelle: variable for variable, libelle in config.LIBELLES_FACTEURS_FICHE.items()}
TABLE_ACTIVITE = "activite_hebdo"
MULTIPLICATEUR_MAX = 100
MOTIF_NOMBRE = r"\d+(?:[.,]\d+)?"
DECIMALES_COMPARAISON = 6
# Grille d'évaluation LL-02 (D-66, point 5) : colonnes dans l'ordre, et valeurs permises de
# chaque critère noté par Saliou (une case vide veut dire « pas encore notée »).
COLONNES_GRILLE = ["id_etudiant", "statut_automatique", "motifs_rejet", "exactitude_humaine", "ton",
                   "stigmatisation", "actions_pertinentes", "commentaire"]
VALEURS_GRILLE = {
    "exactitude_humaine": ("oui", "non"),
    "ton": ("1", "2", "3"),
    "stigmatisation": ("oui", "non"),
    "actions_pertinentes": ("1", "2", "3"),
}
# Indicateurs de qualité LL-02 (D-69), jamais bloquants : motifs relevés dans les fiches v1.
MOTIF_DECIMALE_POINT = r"\d\.\d"
MOTIF_TUTORAT_AUCUN = r"\b(?:est|statut|étant)\s+(?:actuellement\s+)?aucun\b"
NOM_DE_CHAMP_FICHE = "semaine d'observation"
COMPARAISON_MULTIPLICATEUR = "étudiant moyen"
ACTION_ENTRETIEN = "entretien individuel"
ACTIONS_SUIVIES_INDICATEURS = ["aménager l'emploi du temps", "informer sur les aides", "relancer sur les devoirs",
                               "suivre l'assiduité"]


# ===========================================================================
# 1. Outils de format et de lecture
# ===========================================================================

def nombre_fr(valeur, decimales=1):
    """Nombre au format français : 20,1."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def arrondi(valeur, decimales=1):
    """Arrondi d'un nombre ; None si la valeur manque."""
    if valeur is None or pd.isna(valeur):
        return None
    return round(float(valeur), decimales)


def lire_resultat(nom_fichier):
    """Lit un résultat CSV de data/processed/resultats/ (produit par run_all.py)."""
    return pd.read_csv(config.DOSSIER_RESULTATS / nom_fichier, sep=config.SEPARATEUR_PROCESSED,
                       encoding=config.ENCODAGE)


def ecrire_json(objet, chemin):
    """Écrit un JSON lisible (UTF-8, accents gardés, fins de ligne LF), de façon atomique.

    On écrit d'abord un fichier temporaire du même dossier, puis os.replace le met à la
    place de l'ancien d'un seul coup : un arrêt pendant l'écriture (Ctrl+C) laisse
    l'ancien fichier intact et lisible (D-67, point 5).
    """
    chemin.parent.mkdir(parents=True, exist_ok=True)
    temporaire = chemin.with_name(chemin.name + ".tmp")
    try:
        with open(temporaire, "w", encoding=config.ENCODAGE, newline="\n") as fichier:
            json.dump(objet, fichier, ensure_ascii=False, indent=2)
            fichier.write("\n")
        os.replace(temporaire, chemin)
    except BaseException:
        # BaseException : le fichier temporaire est aussi supprimé après un Ctrl+C.
        temporaire.unlink(missing_ok=True)
        raise


def lire_json(chemin):
    """Lit un fichier JSON (UTF-8)."""
    with open(chemin, encoding=config.ENCODAGE) as fichier:
        return json.load(fichier)


# ===========================================================================
# 2. Entrées des fiches (sans réseau)
# ===========================================================================

def population_suivie(base, semaine):
    """Étudiants de la cohorte de test encore suivis après `semaine` (T > semaine), D-66."""
    cohorte = base[config.VARIABLE_COHORTE].astype(int)
    return base[(cohorte == config.COHORTE_TEST) & (base["T"] > semaine)].reset_index(drop=True)


def risques_conditionnels(predictions, ids, semaine):
    """Risque de décrocher d'ici la semaine 30 sachant qu'on est inscrit en `semaine` :
    1 − S(30) / S(semaine), survie du Cox (colonne survie_cox), dans l'ordre de `ids`."""
    survies = predictions.pivot(index=config.COLONNE_ID, columns="semaine", values="survie_cox")
    manquants = [i for i in ids if i not in survies.index]
    if manquants:
        raise ErreurLLM(f"{len(manquants)} étudiant(s) sans prédiction du Cox")
    lignes = survies.loc[list(ids)]
    return (1 - lignes[config.N_SEMAINES] / lignes[semaine]).to_numpy()


def contributions(table_codee, hr):
    """Contribution de chaque variable du Cox au risque d'un étudiant (D-66, point 3).

    Pour chaque colonne codée : β × (x − moyenne des lignes reçues), avec β = log(HR) ;
    les indicatrices d'une variable qualitative sont additionnées. La somme des
    contributions d'un étudiant = son prédicteur linéaire moins celui de la moyenne.
    Sortie : une ligne par étudiant, une colonne par variable d'origine.
    """
    hazard_ratios = hr.set_index("variable")["HR"]
    colonnes = [c for c in table_codee.columns if c not in (config.COLONNE_ID, "T", "E")]
    sans_hr = [c for c in colonnes if c not in hazard_ratios.index]
    if sans_hr:
        raise ErreurLLM(f"Colonnes sans hazard ratio : {sans_hr}")
    resultat = pd.DataFrame(index=table_codee.index)
    for colonne in colonnes:
        beta = math.log(hazard_ratios[colonne])
        valeurs = table_codee[colonne].astype(float)
        part = beta * (valeurs - valeurs.mean())
        variable = survie.variable_d_origine(colonne)
        resultat[variable] = resultat[variable] + part if variable in resultat.columns else part
    return resultat


def references_promotion(population):
    """Textes de référence de la promotion (valeurs connues seulement, format français).

    Distance : 2^(moyenne de log2 de la distance), la distance « typique » qui correspond
    au centrage du Cox. Modalité : part de la promotion dans le même cas.
    """
    distance_typique = 2 ** np.log2(population["distance_campus_km"].dropna().astype(float)).mean()
    references = {
        "age": f"{nombre_fr(population['age'].dropna().astype(float).mean())} ans en moyenne dans la promotion",
        "note_bac": (f"{nombre_fr(population['note_bac'].dropna().astype(float).mean())} / "
                     f"{NOTE_MAXIMUM_BAC} en moyenne dans la promotion"),
        config.COLONNE_DISTANCE_COX: f"{round(distance_typique)} km pour un étudiant typique de la promotion",
    }
    for variable in VARIABLES_QUALITATIVES_FICHE:
        parts = population[variable].dropna().value_counts(normalize=True)
        references[variable] = {modalite: f"{round(100 * part)} % de la promotion dans ce cas"
                                for modalite, part in parts.items()}
    return references


def valeur_affichee(variable, valeur):
    """Valeur de l'étudiant telle que la fiche la montre (« 28 ans », « 10,6 / 20 »…)."""
    if variable == "age":
        return f"{int(round(float(valeur)))} ans"
    if variable == "note_bac":
        return f"{nombre_fr(float(valeur))} / {NOTE_MAXIMUM_BAC}"
    if variable == config.COLONNE_DISTANCE_COX:
        return f"{int(round(float(valeur)))} km"
    if variable == "boursier":
        return "boursier" if valeur == "Oui" else "non boursier"
    if variable == "emploi_parallele":
        return "oui" if valeur == "Oui" else "non"
    return str(valeur)


def facteurs_principaux(contributions_etudiant, ligne_brute, references):
    """Au plus NB_FACTEURS_FICHE facteurs affichables qui augmentent le risque (D-66).

    Candidats : VARIABLES_FACTEURS_FICHE seulement (jamais le genre ni la région) ;
    valeur brute manquante -> jamais un facteur ; multiplicateur = exp(contribution)
    arrondi à 0,1, gardé s'il vaut au moins MULTIPLICATEUR_MIN_FACTEUR ; ordre
    décroissant des contributions (à égalité : ordre de la liste).
    """
    candidats = []
    for rang, variable in enumerate(config.VARIABLES_FACTEURS_FICHE):
        valeur = ligne_brute[COLONNE_BRUTE[variable]]
        if pd.isna(valeur) or variable not in contributions_etudiant.index:
            continue
        contribution = float(contributions_etudiant[variable])
        multiplicateur = round(math.exp(contribution), 1)
        if multiplicateur >= config.MULTIPLICATEUR_MIN_FACTEUR:
            candidats.append((-contribution, rang, variable, multiplicateur, valeur))
    facteurs = []
    for _, _, variable, multiplicateur, valeur in sorted(candidats)[:config.NB_FACTEURS_FICHE]:
        reference = references[variable]
        if isinstance(reference, dict):
            reference = reference[valeur]
        facteurs.append({"facteur": config.LIBELLES_FACTEURS_FICHE[variable],
                         "valeur_etudiant": valeur_affichee(variable, valeur),
                         "reference_promotion": reference, "multiplicateur": multiplicateur})
    return facteurs


def activite_recente(periode, ids, semaines):
    """Activité moyenne par semaine sur `semaines` (valeurs renseignées seulement).

    Sortie : (table par étudiant, dans l'ordre de `ids`, avec les champs de
    CHAMPS_ACTIVITE arrondis à 0,1, None si aucune valeur ; dictionnaire de la
    promotion = moyenne des moyennes des étudiants qui en ont une, arrondie à 0,1).
    """
    lignes = periode[periode["semaine"].isin(semaines) & periode[config.COLONNE_ID].isin(ids)]
    moyennes = lignes.groupby(config.COLONNE_ID)[list(CHAMPS_ACTIVITE.values())].mean().reindex(list(ids))
    moyennes.columns = list(CHAMPS_ACTIVITE)
    promotion = {champ: arrondi(moyennes[champ].mean()) for champ in CHAMPS_ACTIVITE}
    par_etudiant = moyennes.apply(lambda colonne: colonne.map(arrondi)).astype(object)
    return par_etudiant, promotion


def statut_tutorat(ligne, semaine):
    """Tutorat connu à la semaine `semaine` (un tutorat commencé plus tard n'est pas encore connu)."""
    debut = ligne["semaine_debut_tutorat"]
    if not pd.isna(debut) and int(debut) <= semaine:
        return {"statut": "en cours", "semaine_debut": int(debut)}
    if ligne["statut_tutorat"] == config.STATUT_TUTORAT_SEMAINE_INCONNUE:
        return {"statut": "signalé, semaine de début inconnue"}
    return {"statut": "aucun"}


def table_codee_population(base, population):
    """Variables de la rentrée de la population, codées avec les médianes de 2024 (D-63)."""
    entrainement, test = ml_survie.separer_cohortes(base)
    codee = ml_survie.variables_rentree(entrainement, test)["test"].set_index(config.COLONNE_ID)
    return codee.loc[population[config.COLONNE_ID]].reset_index()


def construire_entrees(base, periode, predictions, hr, semaine=config.SEMAINE_FICHES):
    """Entrées des fiches : étudiants dont le risque atteint SEUIL_RISQUE_FICHE.

    Sortie : liste de {"id_etudiant": ..., "entree": {...}}, triée par risque décroissant
    puis identifiant. L'identifiant reste HORS de `entree` : seul `entree` part vers le LLM.
    """
    population = population_suivie(base, semaine)
    ids = population[config.COLONNE_ID].tolist()
    risques = risques_conditionnels(predictions, ids, semaine)
    apports = contributions(table_codee_population(base, population), hr)
    references = references_promotion(population)
    activite, activite_promotion = activite_recente(periode, ids, config.SEMAINES_ACTIVITE_FICHE)
    risque_moyen = round(100 * float(np.mean(risques)))
    retenus = [i for i in range(len(population)) if risques[i] >= config.SEUIL_RISQUE_FICHE]
    retenus.sort(key=lambda i: (-risques[i], ids[i]))
    entrees = []
    for i in retenus:
        ligne = population.iloc[i]
        entree = {
            "semaine_observation": semaine,
            "horizon_semaines": config.N_SEMAINES,
            "risque_decrochage_pct": round(100 * float(risques[i])),
            "risque_moyen_promotion_pct": risque_moyen,
            "facteurs": facteurs_principaux(apports.iloc[i], ligne, references),
            "activite": {"semaines": list(config.SEMAINES_ACTIVITE_FICHE), "note_maximum": NOTE_MAXIMUM,
                         **activite.iloc[i].to_dict()},
            "activite_promotion": dict(activite_promotion),
            "tutorat": statut_tutorat(ligne, semaine),
        }
        verifier_entree_sans_donnee_personnelle(entree)
        entrees.append({"id_etudiant": ids[i], "entree": entree})
    return entrees


def textes_de(objet):
    """Tous les textes d'un objet JSON (clés comprises)."""
    if isinstance(objet, str):
        return [objet]
    if isinstance(objet, dict):
        return [t for cle, valeur in objet.items() for t in [cle] + textes_de(valeur)]
    if isinstance(objet, list):
        return [t for valeur in objet for t in textes_de(valeur)]
    return []


def donnees_personnelles_dans(texte):
    """Motifs d'identifiant étudiant, d'e-mail ou de téléphone trouvés dans un texte."""
    trouves = []
    for nom, motif in [("identifiant", config.FORMAT_ID_ETUDIANT), ("e-mail", config.MOTIF_EMAIL),
                       ("téléphone", config.MOTIF_TELEPHONE)]:
        if re.search(motif, texte):
            trouves.append(nom)
    return trouves


def verifier_cles(objet, attendues, niveau):
    """ErreurLLM si un objet n'a pas exactement les clés attendues, dans cet ordre."""
    if not isinstance(objet, dict) or list(objet) != list(attendues):
        recues = list(objet) if isinstance(objet, dict) else type(objet).__name__
        raise ErreurLLM(f"Entrée non conforme ({niveau}) : clés attendues {attendues}, reçues {recues}")


def est_entier(valeur):
    """Vrai pour un entier Python (un booléen n'est pas un nombre ici)."""
    return isinstance(valeur, int) and not isinstance(valeur, bool)


def est_nombre(valeur):
    """Vrai pour un entier ou un réel fini (ni booléen, ni texte, ni None)."""
    return (isinstance(valeur, (int, float)) and not isinstance(valeur, bool)
            and math.isfinite(float(valeur)))


def verifier_entier(valeur, minimum, maximum, champ):
    """ErreurLLM si `valeur` n'est pas un entier de minimum à maximum."""
    if not est_entier(valeur) or not minimum <= valeur <= maximum:
        raise ErreurLLM(f"Entrée non conforme : {champ} doit être un entier de {minimum} à {maximum}")


def verifier_nombre(valeur, minimum, maximum, champ):
    """ErreurLLM si `valeur` n'est pas un nombre de minimum à maximum."""
    if not est_nombre(valeur) or not minimum <= valeur <= maximum:
        raise ErreurLLM(f"Entrée non conforme : {champ} doit être un nombre de {minimum} à {maximum}")


def verifier_format(texte, motif, champ):
    """ErreurLLM si `texte` n'est pas un texte qui suit exactement `motif` (re.fullmatch).

    Le texte lui-même n'est jamais repris dans le message d'erreur.
    """
    if not isinstance(texte, str) or re.fullmatch(motif, texte) is None:
        raise ErreurLLM(f"Entrée non conforme : {champ} ne suit pas le format écrit par le code")


def bornes_activite(champ):
    """(minimum, maximum) d'un champ d'activité, pris dans les bornes du nettoyage ; sans
    borne haute (connexions), BORNE_HAUTE_PAR_DEFAUT_ENTREE."""
    bornes = config.BORNES[(TABLE_ACTIVITE, CHAMPS_ACTIVITE[champ])]
    maximum = bornes["max"] if bornes["max"] is not None else config.BORNE_HAUTE_PAR_DEFAUT_ENTREE
    return bornes["min"], maximum


def verifier_facteur(facteur):
    """Clés, libellé de la liste, valeur et référence au format de ce facteur, multiplicateur."""
    verifier_cles(facteur, CLES_FACTEUR, "facteur")
    libelle = facteur["facteur"]
    variable = VARIABLE_DU_LIBELLE.get(libelle) if isinstance(libelle, str) else None
    if variable is None:
        raise ErreurLLM("Entrée non conforme : libellé de facteur hors de la liste")
    verifier_format(facteur["valeur_etudiant"], FORMATS_VALEUR_FACTEUR[variable], "valeur_etudiant")
    verifier_format(facteur["reference_promotion"], FORMATS_REFERENCE_FACTEUR[variable], "reference_promotion")
    verifier_nombre(facteur["multiplicateur"], config.MULTIPLICATEUR_MIN_FACTEUR, MULTIPLICATEUR_MAX,
                    "multiplicateur")


def verifier_activite(activite, activite_promotion, semaine):
    """Activité de l'étudiant (None permis) et de la promotion (sans None), dans les bornes."""
    verifier_cles(activite, CLES_ACTIVITE, "activité")
    verifier_cles(activite_promotion, CLES_ACTIVITE_PROMOTION, "activité de la promotion")
    if not isinstance(activite["semaines"], list) or not activite["semaines"]:
        raise ErreurLLM("Entrée non conforme : semaines doit être une liste d'entiers")
    for numero in activite["semaines"]:
        verifier_entier(numero, 1, semaine, "semaines")
    if not est_entier(activite["note_maximum"]) or activite["note_maximum"] != NOTE_MAXIMUM:
        raise ErreurLLM(f"Entrée non conforme : note_maximum doit valoir {NOTE_MAXIMUM}")
    for champ in CHAMPS_ACTIVITE:
        minimum, maximum = bornes_activite(champ)
        if activite[champ] is not None:
            verifier_nombre(activite[champ], minimum, maximum, champ)
        verifier_nombre(activite_promotion[champ], minimum, maximum, f"{champ} de la promotion")


def verifier_tutorat(tutorat, semaine):
    """Statut de la liste fermée ; semaine de début (entier) seulement si « en cours »."""
    statut = tutorat.get("statut") if isinstance(tutorat, dict) else None
    if not isinstance(statut, str) or statut not in config.STATUTS_TUTORAT_FICHE:
        raise ErreurLLM("Entrée non conforme : statut de tutorat hors de la liste")
    verifier_cles(tutorat, ["statut", "semaine_debut"] if statut == "en cours" else ["statut"], "tutorat")
    if statut == "en cours":
        verifier_entier(tutorat["semaine_debut"], 1, semaine, "semaine_debut")


def verifier_entree_sans_donnee_personnelle(entree):
    """Contrôle avant tout envoi (D-65, point 3 ; D-67, point 2) : rien n'est envoyé si une
    règle échoue.

    Clés exactes (ordre compris) à chaque niveau ; chaque valeur vérifiée par son type et
    son format (formats écrits par le code, listes fermées, bornes du nettoyage) ; textes
    courts ; aucun identifiant, e-mail ni téléphone.
    """
    verifier_cles(entree, CLES_ENTREE, "entrée")
    verifier_entier(entree["semaine_observation"], 1, config.N_SEMAINES, "semaine_observation")
    semaine = entree["semaine_observation"]
    verifier_entier(entree["horizon_semaines"], config.N_SEMAINES, config.N_SEMAINES, "horizon_semaines")
    verifier_entier(entree["risque_decrochage_pct"], 0, 100, "risque_decrochage_pct")
    verifier_entier(entree["risque_moyen_promotion_pct"], 0, 100, "risque_moyen_promotion_pct")
    if not isinstance(entree["facteurs"], list):
        raise ErreurLLM("Entrée non conforme : facteurs doit être une liste")
    for facteur in entree["facteurs"]:
        verifier_facteur(facteur)
    verifier_activite(entree["activite"], entree["activite_promotion"], semaine)
    verifier_tutorat(entree["tutorat"], semaine)
    for texte in textes_de(entree):
        if len(texte) > config.LONGUEUR_MAX_TEXTE_ENTREE:
            raise ErreurLLM("Entrée non conforme : texte trop long")
        trouves = donnees_personnelles_dans(texte)
        if trouves:
            # Le texte lui-même n'est jamais repris dans le message d'erreur.
            raise ErreurLLM(f"Entrée non conforme : motif de donnée personnelle ({', '.join(trouves)})")


def etat_du_cache():
    """Phrase qui décrit le cache des fiches (aucun appel à l'API)."""
    if not config.FICHIER_FICHES_LLM.exists():
        return "aucune fiche : lancer python -m src.llm --generer après la relecture R03"
    fiches = lire_json(config.FICHIER_FICHES_LLM)
    if not fiches:
        return "aucune fiche dans le cache"
    derniere = max(f["date_generation"] for f in fiches)
    modeles = ", ".join(sorted({f["modele"] for f in fiches}))
    versions = ", ".join(sorted({f["version_prompt"] for f in fiches}))
    return f"{len(fiches)} fiches en cache ({modeles}, {versions}, {derniere})"


def lancer_entrees():
    """Écrit FICHIER_ENTREES_LLM à partir des résultats de run_all.py. N'appelle jamais l'API."""
    base, periode = eda.lire_bases()
    entrees = construire_entrees(base, periode, lire_resultat("ml_predictions_2025.csv"),
                                 lire_resultat("ml_hr_cox_2024.csv"))
    ecrire_json(entrees, config.FICHIER_ENTREES_LLM)
    print(f"Fiches d'alerte (LL-01) : {len(entrees)} étudiants à risque d'au moins "
          f"{round(100 * config.SEUIL_RISQUE_FICHE)} % "
          f"en semaine {config.SEMAINE_FICHES} ; {etat_du_cache()}.")
    return entrees


# ===========================================================================
# 3. Prompt et appel à l'API
# ===========================================================================

def lire_gabarit(version):
    """Gabarit src/prompts/fiche_<version>.md -> (instructions système, message)."""
    texte = (config.DOSSIER_PROMPTS / f"fiche_{version}.md").read_text(encoding=config.ENCODAGE)
    if TITRE_INSTRUCTIONS not in texte or TITRE_MESSAGE not in texte:
        raise ErreurLLM(f"Gabarit {version} : titres « {TITRE_INSTRUCTIONS} » et « {TITRE_MESSAGE} » attendus")
    avant, message = texte.split(TITRE_MESSAGE, 1)
    instructions = avant.split(TITRE_INSTRUCTIONS, 1)[1]
    return instructions.strip(), message.strip()


def construire_prompt(entree, version=config.VERSION_PROMPT):
    """(instructions, message) prêts à envoyer : actions et entrée insérées dans le gabarit."""
    instructions, message = lire_gabarit(version)
    actions = "\n".join(f"- {action}" for action in config.ACTIONS_FICHE)
    return (instructions.replace("{actions}", actions),
            message.replace("{entree}", json.dumps(entree, ensure_ascii=False, indent=2)))


def schema_fiche():
    """Schéma JSON imposé à la réponse du LLM (trois clés, actions de la liste fermée)."""
    return {
        "type": "object",
        "properties": {
            "situation": {"type": "string"},
            "points_attention": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
            "actions": {"type": "array", "items": {"type": "string", "enum": list(config.ACTIONS_FICHE)},
                        "minItems": 2, "maxItems": 3},
        },
        "required": list(CLES_FICHE),
        "additionalProperties": False,
    }


def lire_cle_api(chemin=config.FICHIER_ENV):
    """Clé GEMINI_API_KEY lue dans .env seulement (pas dans os.environ, D-65 point 1).

    Le message d'erreur ne reprend jamais le contenu du fichier.
    """
    cle = dotenv_values(chemin).get(config.NOM_CLE_API) if chemin.exists() else None
    if not cle:
        raise ErreurLLM(f"Clé d'API absente : copier .env.example en .env (à la racine du dépôt), puis coller la "
                        f"clé après {config.NOM_CLE_API}=")
    return cle


def creer_appel_gemini(cle, modele, schema=None):
    """Fonction appeler(instructions, message) -> texte de la réponse de Gemini.

    google.genai est importé ici seulement : ni les tests ni run_all.py ne le chargent.
    Pas de température : la valeur par défaut est celle recommandée pour Gemini 3.
    Erreur 429 ou 503 -> ErreurQuotaLLM ; autre erreur -> ErreurLLM avec son seul code.
    """
    from google import genai
    from google.genai import errors, types

    # L'adresse fixée dans le code l'emporte sur GOOGLE_GEMINI_BASE_URL, et vertexai=False
    # neutralise GOOGLE_GENAI_USE_VERTEXAI : aucune variable d'environnement de la machine
    # ne peut envoyer la clé ailleurs (D-67, point 4).
    client = genai.Client(api_key=cle, vertexai=False,
                          http_options=types.HttpOptions(base_url=config.URL_API_GEMINI,
                                                         timeout=config.DELAI_MAX_APPEL_LLM_MS))

    def appeler(instructions, message):
        reglages = types.GenerateContentConfig(
            system_instruction=instructions or None,
            response_mime_type="application/json" if schema else None,
            response_json_schema=schema,
        )
        try:
            reponse = client.models.generate_content(model=modele, contents=message, config=reglages)
        except errors.APIError as erreur:
            if erreur.code in CODES_QUOTA:
                raise ErreurQuotaLLM(f"Quota ou surcharge de l'API Gemini (code {erreur.code})") from None
            raise ErreurLLM(f"Erreur de l'API Gemini (code {erreur.code})") from None
        except Exception as erreur:
            # Réseau, délai dépassé… : seul le type est cité, car le texte pourrait contenir
            # l'adresse ou des en-têtes.
            raise ErreurLLM(f"Échec de l'appel à l'API Gemini ({type(erreur).__name__})") from None
        return reponse.text or ""

    return appeler


# ===========================================================================
# 4. Contrôles automatiques des fiches (D-65, point 4)
# ===========================================================================

def nombres_de(objet):
    """Ensemble des nombres d'un objet JSON, y compris ceux écrits dans les textes.

    « 6,1 » est lu comme 6.1 ; 3 et 3.0 sont le même nombre ; booléens et None ignorés.
    """
    if isinstance(objet, bool) or objet is None:
        return set()
    if isinstance(objet, (int, float)):
        return {round(float(objet), DECIMALES_COMPARAISON)}
    if isinstance(objet, str):
        return {round(float(n.replace(",", ".")), DECIMALES_COMPARAISON) for n in re.findall(MOTIF_NOMBRE, objet)}
    if isinstance(objet, dict):
        return set().union(*(nombres_de(v) for v in objet.values())) if objet else set()
    if isinstance(objet, list):
        return set().union(*(nombres_de(v) for v in objet)) if objet else set()
    return set()


def mots_interdits_presents(texte):
    """Expressions de MOTS_INTERDITS_FICHE présentes comme mots entiers (« filière » ne
    déclenche pas « fille », « entraînement » ne déclenche pas « entraîne »)."""
    minuscules = texte.lower()
    return [expression for expression in config.MOTS_INTERDITS_FICHE
            if re.search(r"(?<!\w)" + re.escape(expression) + r"(?!\w)", minuscules)]


def ecrire_nombre(nombre):
    """Nombre lisible dans un motif de rejet (3 plutôt que 3.0)."""
    return nombre_fr(nombre, 0) if float(nombre).is_integer() else str(nombre).replace(".", ",")


def lire_reponse(texte):
    """(fiche, motif) : la réponse lue comme objet JSON, ou None et le motif de rejet."""
    if not texte or not texte.strip():
        return None, "réponse vide"
    try:
        fiche = json.loads(texte)
    except json.JSONDecodeError:
        return None, "réponse non JSON"
    if not isinstance(fiche, dict):
        return None, "réponse qui n'est pas un objet JSON"
    return fiche, None


def motifs_de_forme(fiche):
    """Motifs liés aux clés, aux types et aux longueurs."""
    motifs = []
    if set(fiche) != set(CLES_FICHE):
        motifs.append(f"clés attendues {CLES_FICHE}, reçues {list(fiche)}")
    situation = fiche.get("situation")
    if not isinstance(situation, str) or not situation.strip():
        motifs.append("situation vide ou absente")
    elif len(situation) > config.LONGUEUR_MAX_SITUATION:
        motifs.append(f"situation de plus de {config.LONGUEUR_MAX_SITUATION} caractères")
    points = fiche.get("points_attention")
    if not isinstance(points, list) or not all(isinstance(p, str) for p in points):
        motifs.append("points_attention doit être une liste de textes")
    else:
        if not 2 <= len(points) <= 4:
            motifs.append(f"{len(points)} point(s) d'attention au lieu de 2 à 4")
        if any(not p.strip() or len(p) > config.LONGUEUR_MAX_POINT for p in points):
            motifs.append(f"point d'attention vide ou de plus de {config.LONGUEUR_MAX_POINT} caractères")
    return motifs


def motifs_des_actions(actions, entree):
    """Motifs liés aux actions : nombre, liste fermée, doublons, cohérence avec le tutorat."""
    if not isinstance(actions, list) or not all(isinstance(a, str) for a in actions):
        return ["actions doit être une liste de textes"]
    motifs = []
    if not 2 <= len(actions) <= 3:
        motifs.append(f"{len(actions)} action(s) au lieu de 2 ou 3")
    hors_liste = [a for a in actions if a not in config.ACTIONS_FICHE]
    if hors_liste:
        motifs.append(f"action(s) hors de la liste : {hors_liste}")
    if len(set(actions)) != len(actions):
        motifs.append("action en double")
    statut = entree["tutorat"]["statut"]
    if statut == "en cours" and "proposer un tutorat" in actions:
        motifs.append("« proposer un tutorat » alors qu'un tutorat est en cours")
    if statut == "aucun" and "faire le point sur le tutorat en cours" in actions:
        motifs.append("« faire le point sur le tutorat en cours » alors qu'il n'y a pas de tutorat")
    return motifs


def verifier_fiche(texte, entree):
    """Contrôle automatique d'une réponse -> (fiche ou None, motifs ; vide = conforme)."""
    fiche, motif = lire_reponse(texte)
    if fiche is None:
        return None, [motif]
    motifs = motifs_de_forme(fiche) + motifs_des_actions(fiche.get("actions"), entree)
    textes = [t for cle in ("situation", "points_attention") for t in textes_de(fiche.get(cle))]
    absents = sorted(nombres_de(textes) - nombres_de(entree))
    if absents:
        motifs.append("nombre(s) absent(s) de l'entrée : " + ", ".join(ecrire_nombre(n) for n in absents))
    tous_les_textes = textes_de(fiche)
    interdits = sorted({mot for t in tous_les_textes for mot in mots_interdits_presents(t)})
    if interdits:
        motifs.append(f"mot(s) interdit(s) : {', '.join(interdits)}")
    personnels = sorted({m for t in tous_les_textes for m in donnees_personnelles_dans(t)})
    if personnels:
        motifs.append(f"motif de donnée personnelle : {', '.join(personnels)}")
    return fiche, motifs


# ===========================================================================
# 5. Génération des fiches (commande séparée, après la relecture R03)
# ===========================================================================

def appeler_avec_quota(appeler, instructions, message, attendre):
    """Un appel ; après une erreur de quota, attendre chaque durée de ATTENTES_QUOTA_LLM et
    réessayer ; si le quota n'est toujours pas rétabli, arrêter toute la génération."""
    for attente in (None,) + tuple(config.ATTENTES_QUOTA_LLM):
        if attente is not None:
            attendre(attente)
        try:
            return appeler(instructions, message)
        except ErreurQuotaLLM:
            continue
    raise ErreurQuotaLLM("quota atteint : relancer plus tard ; les fiches déjà faites sont gardées")


def fiche_reutilisable(existante, element, modele):
    """Une fiche du cache est reprise si rien n'a changé (étudiant, entrée, modèle, prompt)."""
    return (existante is not None and existante["id_etudiant"] == element["id_etudiant"]
            and existante["version_prompt"] == config.VERSION_PROMPT and existante["modele"] == modele
            and existante["entree"] == element["entree"])


def texte_de_fiche(fiche):
    """Texte JSON reconstruit à partir des trois champs rédigés d'une fiche du cache."""
    return json.dumps({cle: fiche.get(cle) for cle in CLES_FICHE}, ensure_ascii=False)


def reverifier_fiches(fiches):
    """Repasse les contrôles actuels sur chaque fiche « validée » du cache, sans appel.

    Les contrôles peuvent avoir été complétés après la génération (D-67, point 3) : une
    fiche qui ne les passe plus devient « à revoir », avec ses nouveaux motifs.
    Sortie : (liste des fiches, nombre de fiches rétrogradées).
    """
    resultat = []
    retrogradees = 0
    for fiche in fiches:
        if fiche["statut"] == config.STATUT_FICHE_VALIDEE:
            _, motifs = verifier_fiche(texte_de_fiche(fiche), fiche["entree"])
            if motifs:
                fiche = {**fiche, "statut": config.STATUT_FICHE_A_REVOIR, "motifs_rejet": motifs}
                retrogradees += 1
        resultat.append(fiche)
    return resultat, retrogradees


def enregistrement_fiche(element, fiche, motifs, nb_essais, texte, modele):
    """Fiche enregistrée : contenu du dernier essai, statut, motifs, avertissement, traçabilité."""
    entree = element["entree"]
    lisible = fiche if isinstance(fiche, dict) else {}
    resultat = {
        "id_etudiant": element["id_etudiant"],
        "semaine": entree["semaine_observation"],
        "risque_decrochage_pct": entree["risque_decrochage_pct"],
        "statut": config.STATUT_FICHE_VALIDEE if not motifs else config.STATUT_FICHE_A_REVOIR,
        "situation": lisible.get("situation"),
        "points_attention": lisible.get("points_attention"),
        "actions": lisible.get("actions"),
        "motifs_rejet": motifs,
        "nb_essais": nb_essais,
        "avertissement": config.AVERTISSEMENT_FICHE,
        "modele": modele,
        "version_prompt": config.VERSION_PROMPT,
        "date_generation": datetime.now().isoformat(timespec="seconds"),
        "entree": entree,
    }
    if motifs and fiche is None:
        resultat["reponse_brute"] = (texte or "")[:LONGUEUR_MAX_REPONSE_BRUTE]
    return resultat


def generer_fiches(entrees, appeler, fiches_existantes, modele, forcer=False, attendre=time.sleep, enregistrer=None,
                   revoir=False):
    """Génère les fiches manquantes ; réutilise le cache ; enregistre après chaque fiche.

    forcer : tout régénérer ; revoir : régénérer aussi les fiches « à revoir » du cache,
    en gardant les fiches validées.

    Pour chaque entrée : contrôle sans donnée personnelle, prompt, jusqu'à NB_ESSAIS_FICHE
    essais (appel puis verifier_fiche), PAUSE_ENTRE_APPELS_LLM secondes entre deux appels.
    L'identifiant n'est jamais dans le message : il est ajouté localement à la fiche.
    Sortie : la liste des fiches, dans l'ordre des entrées.
    """
    ordre = [element["id_etudiant"] for element in entrees]
    courantes = {fiche["id_etudiant"]: fiche for fiche in (fiches_existantes or [])}
    resultat = []
    premier_appel = True
    for element in entrees:
        existante = courantes.get(element["id_etudiant"])
        a_revoir = revoir and existante is not None and existante["statut"] == config.STATUT_FICHE_A_REVOIR
        if not forcer and not a_revoir and fiche_reutilisable(existante, element, modele):
            resultat.append(existante)
            continue
        verifier_entree_sans_donnee_personnelle(element["entree"])
        instructions, message = construire_prompt(element["entree"])
        for essai in range(1, config.NB_ESSAIS_FICHE + 1):
            if not premier_appel:
                attendre(config.PAUSE_ENTRE_APPELS_LLM)
            premier_appel = False
            texte = appeler_avec_quota(appeler, instructions, message, attendre)
            fiche, motifs = verifier_fiche(texte, element["entree"])
            if not motifs:
                break
        nouvelle = enregistrement_fiche(element, fiche, motifs, essai, texte, modele)
        courantes[element["id_etudiant"]] = nouvelle
        resultat.append(nouvelle)
        if enregistrer is not None:
            # Le cache garde aussi les fiches des étudiants pas encore traités.
            enregistrer([courantes[i] for i in ordre if i in courantes])
    return resultat


# ===========================================================================
# 6. Évaluation (LL-02)
# ===========================================================================

def echantillon_evaluation(fiches, n=config.NB_FICHES_EVALUATION, graine=config.SEED):
    """n fiches tirées au hasard (graine fixe) parmi les identifiants triés, dans l'ordre des fiches."""
    identifiants = sorted(f["id_etudiant"] for f in fiches)
    tires = set(np.random.default_rng(graine).choice(identifiants, size=min(n, len(identifiants)), replace=False))
    return [f for f in fiches if f["id_etudiant"] in tires]


def ecrire_grille_evaluation(fiches, chemin=config.FICHIER_GRILLE_EVALUATION):
    """Grille d'évaluation à remplir par Saliou ; refuse d'écraser une grille existante.

    Séparateur « ; » et encodage utf-8-sig : Excel en français ouvre alors le fichier en
    colonnes, avec les accents.
    """
    if chemin.exists():
        raise ErreurLLM(f"La grille {chemin.name} existe déjà : elle n'est pas écrasée")
    lignes = []
    for fiche in echantillon_evaluation(fiches):
        ligne = {colonne: "" for colonne in COLONNES_GRILLE}
        ligne["id_etudiant"] = fiche["id_etudiant"]
        ligne["statut_automatique"] = fiche["statut"]
        ligne["motifs_rejet"] = " ; ".join(fiche["motifs_rejet"])
        lignes.append(ligne)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(lignes, columns=COLONNES_GRILLE).to_csv(chemin, sep=";", index=False, encoding="utf-8-sig",
                                                         lineterminator="\n")
    return chemin


def lire_grille_evaluation(chemin):
    """Grille remplie par Saliou, lue en texte et contrôlée.

    Tout est lu comme du texte (une case vide reste "") : on contrôle ce que Saliou a écrit,
    sans conversion. ErreurLLM si les colonnes ne sont pas exactement COLONNES_GRILLE (par
    exemple une ligne entière entre guillemets, lue comme une seule colonne), si un
    identifiant est en double, ou si une valeur sort de VALEURS_GRILLE.
    Sortie : DataFrame de texte, colonnes COLONNES_GRILLE.
    """
    grille = pd.read_csv(chemin, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    if list(grille.columns) != COLONNES_GRILLE:
        raise ErreurLLM(f"Grille {chemin.name} : colonnes attendues {COLONNES_GRILLE}, lues {list(grille.columns)}")
    doublons = grille.loc[grille["id_etudiant"].duplicated(), "id_etudiant"].tolist()
    if doublons:
        raise ErreurLLM(f"Grille {chemin.name} : identifiant(s) en double {doublons}")
    for colonne, valeurs in VALEURS_GRILLE.items():
        # Une case vide veut dire « pas encore notée » : elle est permise.
        hors_liste = sorted(set(grille[colonne]) - set(valeurs) - {""})
        if hors_liste:
            raise ErreurLLM(f"Grille {chemin.name} : colonne {colonne}, valeur(s) hors liste {hors_liste} "
                            f"(attendu : {', '.join(valeurs)} ou vide)")
    return grille


def resume_grille(grille):
    """Résumé des notes humaines, sur les fiches entièrement notées (les 4 critères remplis).

    Sortie : dictionnaire (fiches_notees, exactitude_oui, ton_moyen, stigmatisation_oui,
    actions_pertinentes_moyennes, commentaires) ; les moyennes valent None si aucune fiche
    n'est notée.
    """
    notees = grille[(grille[list(VALEURS_GRILLE)] != "").all(axis=1)]
    aucune = len(notees) == 0
    return {
        "fiches_notees": len(notees),
        "exactitude_oui": int((notees["exactitude_humaine"] == "oui").sum()),
        "ton_moyen": None if aucune else float(notees["ton"].astype(int).mean()),
        "stigmatisation_oui": int((notees["stigmatisation"] == "oui").sum()),
        "actions_pertinentes_moyennes": None if aucune else float(notees["actions_pertinentes"].astype(int).mean()),
        "commentaires": int((notees["commentaire"].str.strip() != "").sum()),
    }


# ===========================================================================
# 7. Indicateurs de qualité (LL-02, D-69)
# ===========================================================================
# Ces indicateurs servent à évaluer et comparer les versions du prompt : ils ne changent
# jamais le statut d'une fiche (les contrôles bloquants restent ceux de la section 4).

def facteur_vaut(entree, variable, valeur):
    """Vrai si l'entrée contient le facteur de `variable` avec cette valeur pour l'étudiant."""
    libelle = config.LIBELLES_FACTEURS_FICHE[variable]
    return any(f["facteur"] == libelle and f["valeur_etudiant"] == valeur for f in entree["facteurs"])


def compare_activite(entree, champ):
    """(valeur de l'étudiant, valeur de la promotion) du champ d'activité, ou None si l'une
    des deux n'est pas renseignée (on ne compare pas une valeur inconnue)."""
    etudiant = entree["activite"][champ]
    promotion = entree["activite_promotion"][champ]
    if etudiant is None or promotion is None:
        return None
    return etudiant, promotion


def actions_appuyees(entree):
    """Actions qu'un fait de l'entrée appuie (règles du gabarit v2, D-69).

    « entretien individuel » n'en fait jamais partie : la fiche prépare déjà un entretien.
    """
    appuyees = set()
    if entree["tutorat"]["statut"] == "aucun":
        appuyees.add("proposer un tutorat")
    else:
        appuyees.add("faire le point sur le tutorat en cours")
    if facteur_vaut(entree, "emploi_parallele", "oui"):
        appuyees.add("aménager l'emploi du temps")
    if facteur_vaut(entree, "boursier", "non boursier"):
        appuyees.add("informer sur les aides")
    devoirs = compare_activite(entree, "devoirs_rendus")
    if devoirs is not None and devoirs[0] < devoirs[1]:
        appuyees.add("relancer sur les devoirs")
    seances = compare_activite(entree, "seances_manquees")
    if seances is not None and seances[0] > seances[1]:
        appuyees.add("suivre l'assiduité")
    return appuyees


def texte_redige(fiche):
    """Situation et points d'attention d'une fiche, en une liste de textes (vide si absents)."""
    return [t for cle in ("situation", "points_attention") for t in textes_de(fiche.get(cle))]


def nombres_cites(textes_entree, nombres_fiche):
    """(nombre de textes qui contiennent un nombre, nombre de ceux dont tous les nombres
    figurent dans la fiche)."""
    chiffres = [t for t in textes_entree if nombres_de(t)]
    cites = [t for t in chiffres if nombres_de(t) <= nombres_fiche]
    return len(chiffres), len(cites)


def indicateurs_fiche(fiche):
    """Indicateurs automatiques d'une fiche, calculés sur sa situation et ses points d'attention.

    Sortie : dictionnaire (motifs de forme, facteurs cités, actions appuyées ou non) ; voir
    resume_indicateurs pour leur lecture.
    """
    textes = texte_redige(fiche)
    texte = " ".join(textes)
    nombres_fiche = nombres_de(textes)
    facteurs = fiche["entree"]["facteurs"]
    facteurs_chiffres, valeurs_citees = nombres_cites([f["valeur_etudiant"] for f in facteurs], nombres_fiche)
    _, references_citees = nombres_cites([f["reference_promotion"] for f in facteurs], nombres_fiche)
    actions = fiche.get("actions") or []
    appuyees = actions_appuyees(fiche["entree"])
    # Une place restait si la fiche a moins de 3 actions ou en garde une pour l'entretien.
    place_restante = len(actions) < 3 or ACTION_ENTRETIEN in actions
    return {
        "decimale_avec_point": bool(re.search(MOTIF_DECIMALE_POINT, texte)),
        "tutorat_est_aucun": bool(re.search(MOTIF_TUTORAT_AUCUN, texte.lower())),
        "nom_de_champ": NOM_DE_CHAMP_FICHE in texte.lower(),
        "multiplicateur_compare": COMPARAISON_MULTIPLICATEUR in texte.lower(),
        "facteurs_chiffres": facteurs_chiffres,
        "valeurs_citees": valeurs_citees,
        "facteurs": len(facteurs),
        "references_citees": references_citees,
        "actions": list(actions),
        "appuyees": sorted(appuyees),
        "action_sans_appui": any(a not in appuyees and a != ACTION_ENTRETIEN for a in actions),
        "oubli_evitable": bool(appuyees - set(actions)) and place_restante,
        "entretien_individuel": ACTION_ENTRETIEN in actions,
        "combinaison": " | ".join(sorted(actions)),
    }


def ligne_indicateur(groupe, indicateur, nombre, sur):
    """Une ligne du tableau de resume_indicateurs."""
    return {"groupe": groupe, "indicateur": indicateur, "nombre": int(nombre), "sur": sur}


def resume_indicateurs(fiches):
    """Tableau des indicateurs sur un ensemble de fiches (colonnes groupe, indicateur, nombre, sur).

    Les groupes « forme », « facteurs » et « actions » portent sur les fiches rédigées (avec
    une situation). Avec 3 actions au plus, une fiche à 4 ou 5 actions appuyées ne peut pas
    toutes les proposer : les lignes « quand un fait l'appuie » n'ont pas à atteindre 100 %.
    """
    redigees = [f for f in fiches if f.get("situation")]
    indicateurs = [indicateurs_fiche(f) for f in redigees]
    n = len(redigees)

    def compter(cle):
        return sum(i[cle] for i in indicateurs)

    validees = [f for f in fiches if f["statut"] == config.STATUT_FICHE_VALIDEE]
    lignes = [
        ligne_indicateur("contrôles", "Fiches validées", len(validees), len(fiches)),
        ligne_indicateur("contrôles", "Validées dès le premier essai", sum(f["nb_essais"] == 1 for f in validees),
                         len(fiches)),
        ligne_indicateur("forme", "Nombre décimal écrit avec un point", compter("decimale_avec_point"), n),
        ligne_indicateur("forme", "Tutorat formulé « est aucun » ou « statut aucun »", compter("tutorat_est_aucun"), n),
        ligne_indicateur("forme", "Nom de champ « semaine d'observation »", compter("nom_de_champ"), n),
        ligne_indicateur("facteurs", "Multiplicateur comparé à « un étudiant moyen »", compter("multiplicateur_compare"),
                         n),
        ligne_indicateur("facteurs", "Valeur de l'étudiant citée (facteurs chiffrés)", compter("valeurs_citees"),
                         compter("facteurs_chiffres")),
        ligne_indicateur("facteurs", "Référence de la promotion citée", compter("references_citees"),
                         compter("facteurs")),
        ligne_indicateur("actions", "Au moins une action qu'aucun fait n'appuie", compter("action_sans_appui"), n),
        ligne_indicateur("actions", "Action appuyée oubliée alors qu'une place restait", compter("oubli_evitable"), n),
        ligne_indicateur("actions", f"« {ACTION_ENTRETIEN} » proposé", compter("entretien_individuel"), n),
    ]
    for action in ACTIONS_SUIVIES_INDICATEURS:
        appuyee = [i for i in indicateurs if action in i["appuyees"]]
        choisie = [i for i in appuyee if action in i["actions"]]
        lignes.append(ligne_indicateur("actions", f"« {action} » quand un fait l'appuie", len(choisie), len(appuyee)))
    combinaisons = {i["combinaison"] for i in indicateurs}
    lignes.append(ligne_indicateur("actions", "Combinaisons d'actions différentes", len(combinaisons), None))
    tableau = pd.DataFrame(lignes, columns=["groupe", "indicateur", "nombre", "sur"])
    # Entiers, avec une case vide pour la ligne des combinaisons (sans dénominateur).
    tableau["sur"] = tableau["sur"].astype("Int64")
    return tableau


# ===========================================================================
# 8. Ligne de commande
# ===========================================================================

def commande_tester(modele):
    """Un seul appel neutre, sans aucune donnée d'étudiant ni instructions système."""
    appeler = creer_appel_gemini(lire_cle_api(), modele)
    print(f"Modèle {modele} : {appeler('', MESSAGE_TEST)}")


def commande_generer(modele, forcer, revoir):
    """Génère les fiches à partir des entrées enregistrées ; cache revérifié d'abord, puis
    écrit après chaque fiche."""
    entrees = lire_json(config.FICHIER_ENTREES_LLM)
    existantes = lire_json(config.FICHIER_FICHES_LLM) if config.FICHIER_FICHES_LLM.exists() else []
    existantes, retrogradees = reverifier_fiches(existantes)
    if retrogradees:
        print(f"{retrogradees} fiche(s) du cache rétrogradée(s) « à revoir » par les contrôles actuels.")
    appeler = creer_appel_gemini(lire_cle_api(), modele, schema_fiche())
    fiches = generer_fiches(entrees, appeler, existantes, modele, forcer=forcer, revoir=revoir,
                            enregistrer=lambda f: ecrire_json(f, config.FICHIER_FICHES_LLM))
    ecrire_json(fiches, config.FICHIER_FICHES_LLM)
    validees = sum(f["statut"] == config.STATUT_FICHE_VALIDEE for f in fiches)
    print(f"{validees} fiches validées, {len(fiches) - validees} à revoir.")


def commande_verifier():
    """Repasse les contrôles actuels sur les fiches validées de chaque cache présent (une
    version du prompt par fichier, aucun appel), puis réécrit chaque cache."""
    presents = {version: chemin for version, chemin in config.FICHIERS_FICHES_LLM.items() if chemin.exists()}
    if not presents:
        raise ErreurLLM("Aucune fiche en cache : lancer d'abord python -m src.llm --generer")
    for version, chemin in presents.items():
        fiches, retrogradees = reverifier_fiches(lire_json(chemin))
        ecrire_json(fiches, chemin)
        print(f"Prompt {version} : {retrogradees} fiche(s) rétrogradée(s) « à revoir » sur {len(fiches)}.")


def commande_grille():
    """Écrit la grille d'évaluation à partir du cache des fiches."""
    if not config.FICHIER_FICHES_LLM.exists():
        raise ErreurLLM("Aucune fiche en cache : lancer d'abord python -m src.llm --generer")
    chemin = ecrire_grille_evaluation(lire_json(config.FICHIER_FICHES_LLM))
    print(f"Grille écrite : {chemin.relative_to(config.RACINE)}")


def main():
    """Point d'entrée de python -m src.llm."""
    parseur = argparse.ArgumentParser(description="Fiches d'alerte par LLM (LL-01, LL-02)")
    groupe = parseur.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--entrees", action="store_true", help="écrire les entrées (sans API)")
    groupe.add_argument("--tester", action="store_true", help="un appel neutre, sans donnée d'étudiant")
    groupe.add_argument("--generer", action="store_true", help="générer les fiches (API Gemini)")
    groupe.add_argument("--verifier", action="store_true", help="revérifier les fiches du cache (sans API)")
    groupe.add_argument("--grille", action="store_true", help="écrire la grille d'évaluation LL-02")
    parseur.add_argument("--forcer", action="store_true", help="régénérer même les fiches en cache")
    parseur.add_argument("--revoir", action="store_true", help="avec --generer : régénérer les fiches « à revoir »")
    parseur.add_argument("--modele", default=config.MODELE_LLM, help="modèle Gemini (--tester, --generer)")
    arguments = parseur.parse_args()
    if (arguments.forcer or arguments.revoir) and not arguments.generer:
        parseur.error("--forcer et --revoir s'utilisent seulement avec --generer")
    try:
        if arguments.entrees:
            lancer_entrees()
        elif arguments.tester:
            commande_tester(arguments.modele)
        elif arguments.generer:
            commande_generer(arguments.modele, arguments.forcer, arguments.revoir)
        elif arguments.verifier:
            commande_verifier()
        else:
            commande_grille()
    except ErreurLLM as erreur:
        # Arrêt sans trace Python (D-67, point 5) : le message suffit, code de sortie 1.
        print(erreur, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
