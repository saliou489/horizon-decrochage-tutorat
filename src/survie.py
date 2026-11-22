"""Analyse de survie : Kaplan-Meier, log-rank et semaines critiques.

Rôle du module : décrire le temps jusqu'au décrochage à partir de base_survie.csv
(T, E et covariables de la rentrée uniquement, D-43 ; aucune variable de tutorat, qui
relève de la partie causale) :
- courbe de Kaplan-Meier globale et par sous-groupe, tests du log-rank (D-46) ;
- risque hebdomadaire et semaines critiques (D-47).
Les résultats sont des associations, pas des effets causaux.

Tâche couverte : SV-01.
"""

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test
from scipy.stats import norm

from src import config, eda


class ErreurSurvie(Exception):
    """Cas non prévu par les décisions : l'analyse s'arrête (même principe que D-18)."""


# ===========================================================================
# 1. Lecture
# ===========================================================================

def lire_base():
    """Lit base_survie.csv (produit par le pipeline ; il n'est pas relancé ici)."""
    return pd.read_csv(config.FICHIER_BASE_SURVIE, sep=config.SEPARATEUR_PROCESSED,
                       dtype={"cohorte": str, "age": "Int64", "semaine_debut_tutorat": "Int64"},
                       encoding=config.ENCODAGE)


# ===========================================================================
# 2. Kaplan-Meier
# ===========================================================================

def ajuster_kaplan_meier(durees, evenements, nom="tous les étudiants"):
    """Ajuste un estimateur de Kaplan-Meier (IC à 95 %)."""
    kmf = KaplanMeierFitter(alpha=config.ALPHA)
    kmf.fit(durees, event_observed=evenements, label=nom)
    return kmf


def valeur_a_la_semaine(table, semaine):
    """Valeur d'une fonction en escalier (indexée par le temps) à la semaine donnée."""
    return table.loc[:semaine].iloc[-1]


def survie_aux_semaines(kmf, semaines=config.SEMAINES_SURVIE):
    """Survie S(t) et son IC à 95 % aux semaines demandées.

    Sortie : DataFrame semaine, survie, ic_bas, ic_haut.
    """
    survie = kmf.survival_function_.iloc[:, 0]
    intervalle = kmf.confidence_interval_survival_function_
    lignes = []
    for semaine in semaines:
        bornes = valeur_a_la_semaine(intervalle, semaine)
        lignes.append({"semaine": semaine, "survie": float(valeur_a_la_semaine(survie, semaine)),
                       "ic_bas": float(bornes.iloc[0]), "ic_haut": float(bornes.iloc[1])})
    return pd.DataFrame(lignes)


def mediane_de_survie(kmf):
    """Semaine où la survie passe sous 50 %, ou None si elle n'est pas atteinte."""
    mediane = kmf.median_survival_time_
    return None if np.isinf(mediane) else float(mediane)


def kaplan_meier_global(base, duree="T", evenement="E"):
    """Kaplan-Meier sur tous les étudiants.

    Sortie : dictionnaire kmf, survies (S à 10, 20, 30 semaines avec IC), mediane.
    """
    kmf = ajuster_kaplan_meier(base[duree], base[evenement])
    return {"kmf": kmf, "survies": survie_aux_semaines(kmf), "mediane": mediane_de_survie(kmf)}


def modalites_ordonnees(variable, valeurs):
    """Modalités présentes, dans l'ordre de config.MODALITES (sinon ordre alphabétique)."""
    presentes = set(valeurs)
    ordre = config.MODALITES.get(("etudiants", variable), sorted(presentes))
    return [m for m in ordre if m in presentes] + sorted(presentes - set(ordre))


def kaplan_meier_sous_groupe(base, variable, duree="T", evenement="E"):
    """Kaplan-Meier par modalité d'une variable et test du log-rank (D-46).

    Les étudiants dont la variable manque sont exclus de cette comparaison ; leur nombre
    est rapporté. Le log-rank est à k groupes quand la variable a plus de 2 modalités.
    Sortie : dictionnaire tableau (une ligne par modalité : effectif, décrochages,
    survie à 10, 20, 30 semaines), kmfs, manquants, statistique, p.
    """
    connus = base[base[variable].notna()]
    lignes, kmfs = [], {}
    for modalite in modalites_ordonnees(variable, connus[variable]):
        groupe = connus[connus[variable] == modalite]
        kmf = ajuster_kaplan_meier(groupe[duree], groupe[evenement], nom=str(modalite))
        kmfs[modalite] = kmf
        ligne = {"variable": variable, "modalite": modalite, "effectif": len(groupe),
                 "decrochages": int(groupe[evenement].sum())}
        for _, survie in survie_aux_semaines(kmf).iterrows():
            ligne[f"S({int(survie['semaine'])})"] = survie["survie"]
        lignes.append(ligne)
    test = multivariate_logrank_test(connus[duree], connus[variable], connus[evenement])
    return {"tableau": pd.DataFrame(lignes), "kmfs": kmfs, "manquants": len(base) - len(connus),
            "statistique": float(test.test_statistic), "p": float(test.p_value)}


def tableau_log_rank(resultats):
    """Tableau des tests du log-rank avec le seuil de Bonferroni (D-46).

    Entrée : dictionnaire {variable: résultat de kaplan_meier_sous_groupe}.
    """
    seuil = config.ALPHA / len(resultats)
    lignes = []
    for variable, resultat in resultats.items():
        lignes.append({"variable": variable, "groupes": len(resultat["tableau"]),
                       "manquants exclus": resultat["manquants"], "statistique": resultat["statistique"],
                       "p brute": resultat["p"], "seuil de Bonferroni": seuil,
                       "différence significative": resultat["p"] < seuil})
    return pd.DataFrame(lignes)


# ===========================================================================
# 3. Risque hebdomadaire et semaines critiques
# ===========================================================================

def risque_hebdomadaire(base):
    """Risque de décrochage de chaque semaine avec son IC à 95 % (D-47).

    Réutilise eda.taux_hebdomadaire (décrochages / étudiants encore suivis). IC par
    l'approximation normale : taux ± 1,96 × racine(taux × (1 − taux) / suivis), borné à 0.
    Risque moyen = total des décrochages / total des semaines-étudiant à risque.
    Sortie : (table, risque_moyen).
    """
    table = eda.taux_hebdomadaire(base)
    # Une semaine sans étudiant suivi a un taux vide (pd.NA) : on le passe en NaN pour le calcul.
    table["taux"] = pd.to_numeric(table["taux"], errors="coerce").astype(float)
    z = norm.ppf(1 - config.ALPHA / 2)
    erreur = z * np.sqrt(table["taux"] * (1 - table["taux"]) / table["suivis"])
    table["ic_bas"] = (table["taux"] - erreur).clip(lower=0)
    table["ic_haut"] = table["taux"] + erreur
    risque_moyen = table["decrochages"].sum() / table["suivis"].sum()
    return table, float(risque_moyen)


def marquer_semaines_critiques(table, risque_moyen, facteur=config.FACTEUR_SEMAINE_CRITIQUE):
    """Ajoute seuil et critique : semaine critique si taux >= facteur × risque moyen (D-47)."""
    resultat = table.copy()
    resultat["seuil"] = facteur * risque_moyen
    resultat["critique"] = resultat["taux"] >= resultat["seuil"]
    return resultat
