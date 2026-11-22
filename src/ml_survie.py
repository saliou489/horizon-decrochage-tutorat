"""Modèles prédictifs de survie : Cox et gradient boosting à temps discret, 2024 -> 2025.

Rôle du module : entraîner sur la cohorte 2024 et tester sur la cohorte 2025 (examen
final : rien de 2025 ne sert à l'entraînement, ni médianes, ni colonnes, ni réglages) :
- un Cox (lifelines) et un gradient boosting à temps discret (scikit-learn, D-60) sur
  les variables de la rentrée (modèle « rentrée », comparaison officielle, D-63) ;
- un gradient boosting « hebdomadaire » qui ajoute l'activité de la semaine précédente
  (colonnes *_prec, D-42) : le score actualisable chaque semaine ;
- les mesures sur 2025 (C-index, Brier score intégré, calibration à 20 semaines, AUC
  hebdomadaire) et l'importance des variables par permutation ;
- l'enregistrement des résultats dans data/processed/resultats/ (relus par le notebook
  04 et le tableau de bord). Aucune variable de tutorat (D-43).

Tâches couvertes : SV-03, SV-04.
"""

import time

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from src import config, eda, survie


class ErreurMLSurvie(Exception):
    """Cas non prévu par la méthode de SV-03 / SV-04 (D-60, D-63) : on s'arrête."""


SEMAINES = np.arange(1, config.N_SEMAINES + 1)
COLONNE_SEMAINE = "semaine"
COLONNE_EVENEMENT = "evenement"
COLONNE_ETAT_PREC = "etat_activite" + config.SUFFIXE_PREC
# Variables d'activité numériques de la semaine précédente (D-42) et indicatrices d'état.
COLONNES_ACTIVITE_NUMERIQUES_PREC = [f"{v}{config.SUFFIXE_PREC}" for v in config.VARIABLES_ACTIVITE_PROPENSION]
COLONNES_ETAT_PREC = [f"{COLONNE_ETAT_PREC}{config.SEPARATEUR_INDICATRICE}{etat}" for etat in config.ETATS_ACTIVITE]
# Variables expliquées par permutation (une variable qualitative = toutes ses indicatrices).
VARIABLES_RENTREE_PERMUTATION = ["age", "note_bac", config.COLONNE_DISTANCE_COX, "genre", "boursier", "filiere",
                                 config.COLONNE_REGION_COX, "emploi_parallele"]
VARIABLES_HEBDOMADAIRES_PERMUTATION = (VARIABLES_RENTREE_PERMUTATION + COLONNES_ACTIVITE_NUMERIQUES_PREC
                                       + [COLONNE_ETAT_PREC])


# ===========================================================================
# 1. Séparation des cohortes et variables de la rentrée
# ===========================================================================

def separer_cohortes(base):
    """(base 2024 d'entraînement, base 2025 de test), index remis à zéro."""
    cohorte = base[config.VARIABLE_COHORTE].astype(int)
    entrainement = base[cohorte == config.COHORTE_ENTRAINEMENT].reset_index(drop=True)
    test = base[cohorte == config.COHORTE_TEST].reset_index(drop=True)
    return entrainement, test


def est_colonne_rentree(colonne):
    """Liste positive (principe de D-43) : variable numérique du Cox, ou indicatrice
    d'une variable qualitative du Cox autre que la cohorte."""
    if colonne in config.VARIABLES_COX_NUMERIQUES:
        return True
    qualitatives = [v for v in config.VARIABLES_COX_QUALITATIVES if v != config.VARIABLE_COHORTE]
    return config.SEPARATEUR_INDICATRICE in colonne and survie.variable_d_origine(colonne) in qualitatives


def verifier_colonnes(colonnes, hebdomadaire=False):
    """ErreurMLSurvie si une colonne n'est pas dans la liste positive des variables.

    Autorisées : variables de la rentrée ; pour le gradient boosting, le numéro de la
    semaine ; pour le modèle hebdomadaire, l'activité de la semaine précédente (D-42).
    """
    autorisees_en_plus = {COLONNE_SEMAINE}
    if hebdomadaire:
        autorisees_en_plus |= set(COLONNES_ACTIVITE_NUMERIQUES_PREC) | set(COLONNES_ETAT_PREC)
    for colonne in colonnes:
        if not (est_colonne_rentree(colonne) or colonne in autorisees_en_plus):
            raise ErreurMLSurvie(f"Colonne hors de la liste positive des variables : {colonne}")


def aligner_colonnes(table, colonnes_entrainement):
    """Colonnes du test alignées sur celles de l'entraînement.

    Indicatrice absente du test (modalité non observée en 2025) -> 0 ; colonne du test
    inconnue à l'entraînement -> ErreurMLSurvie (le modèle ne saurait pas la lire).
    """
    inconnues = [c for c in table.columns if c not in colonnes_entrainement]
    if inconnues:
        raise ErreurMLSurvie(f"Colonnes absentes de l'entraînement : {inconnues}")
    alignee = table.copy()
    for colonne in colonnes_entrainement:
        if colonne not in alignee.columns:
            alignee[colonne] = 0
    return alignee[list(colonnes_entrainement)]


def variables_rentree(entrainement, test):
    """Variables de la rentrée codées comme le Cox, sans la cohorte (D-63).

    Les médianes et la liste de colonnes viennent de 2024 seulement ; 2025 est codé
    avec elles. Sortie : dictionnaire : tables (id_etudiant, T, E, variables) de 2024
    et 2025, liste des colonnes, médianes de 2024.
    """
    exclues = (config.VARIABLE_COHORTE,)
    donnees_entrainement, medianes = survie.preparer_donnees_cox(entrainement, variables_exclues=exclues)
    donnees_test, _ = survie.preparer_donnees_cox(test, medianes=medianes, variables_exclues=exclues)
    colonnes = [c for c in donnees_entrainement.columns if c not in ("T", "E")]
    verifier_colonnes(colonnes)
    tables = {}
    for nom, base, donnees in [("entrainement", entrainement, donnees_entrainement),
                               ("test", test, donnees_test)]:
        variables = aligner_colonnes(donnees.drop(columns=["T", "E"]), colonnes)
        table = pd.concat([donnees[["T", "E"]], variables], axis=1)
        table.insert(0, config.COLONNE_ID, base[config.COLONNE_ID].to_numpy())
        tables[nom] = table
    return {"entrainement": tables["entrainement"], "test": tables["test"], "colonnes": colonnes,
            "medianes": medianes}


# ===========================================================================
# 2. Lignes semaine-étudiant (gradient boosting à temps discret, D-60)
# ===========================================================================

def indicatrices_etat_precedent(etats):
    """Une colonne 0/1 par état de ETATS_ACTIVITE ; manquante si l'état précédent manque."""
    colonnes = {}
    for etat, colonne in zip(config.ETATS_ACTIVITE, COLONNES_ETAT_PREC):
        valeurs = (etats == etat).astype(float)
        colonnes[colonne] = valeurs.where(etats.notna())
    return pd.DataFrame(colonnes, index=etats.index)


def lignes_semaines(periode, table_rentree, colonnes_rentree, hebdomadaire=False):
    """Une ligne par semaine où l'étudiant est encore suivi ; cible = evenement.

    Variables : semaine + variables de la rentrée (jointure sur id_etudiant) ; en plus,
    pour le modèle hebdomadaire, l'activité de la semaine précédente (valeurs manquantes
    laissées au modèle) et les indicatrices de etat_activite_prec.
    Sortie : (lignes avec id_etudiant, semaine, evenement et les variables ; colonnes).
    """
    gardees = [config.COLONNE_ID, COLONNE_SEMAINE, COLONNE_EVENEMENT]
    if hebdomadaire:
        gardees += COLONNES_ACTIVITE_NUMERIQUES_PREC + [COLONNE_ETAT_PREC]
    semaines = periode.loc[periode[config.COLONNE_ID].isin(table_rentree[config.COLONNE_ID]), gardees]
    lignes = semaines.merge(table_rentree[[config.COLONNE_ID] + list(colonnes_rentree)], on=config.COLONNE_ID,
                            how="left", validate="many_to_one")
    colonnes = [COLONNE_SEMAINE] + list(colonnes_rentree)
    if hebdomadaire:
        lignes = pd.concat([lignes.drop(columns=[COLONNE_ETAT_PREC]),
                            indicatrices_etat_precedent(lignes[COLONNE_ETAT_PREC])], axis=1)
        colonnes += COLONNES_ACTIVITE_NUMERIQUES_PREC + COLONNES_ETAT_PREC
    verifier_colonnes(colonnes, hebdomadaire=hebdomadaire)
    return lignes.reset_index(drop=True), colonnes


# ===========================================================================
# 3. Entraînement (2024 uniquement)
# ===========================================================================

def entrainer_gradient_boosting(lignes, colonnes):
    """HistGradientBoostingClassifier avec les réglages fixés d'avance (D-63)."""
    modele = HistGradientBoostingClassifier(**config.REGLAGES_GRADIENT_BOOSTING)
    modele.fit(lignes[colonnes], lignes[COLONNE_EVENEMENT])
    return modele


def entrainer_cox(table, colonnes):
    """Cox de lifelines (liens d'Efron, sans pénalité) sur la table de la rentrée."""
    cph = CoxPHFitter()
    cph.fit(table[["T", "E"] + list(colonnes)], duration_col="T", event_col="E")
    return cph


# ===========================================================================
# 4. Courbes de survie prédites (semaines 1 à 30)
# ===========================================================================

def survie_depuis_risques(risques):
    """S(t) = produit des (1 − h(k)) pour k <= t, ligne par ligne (une ligne par étudiant)."""
    return np.cumprod(1 - np.asarray(risques, dtype=float), axis=1)


def grille_rentree(table, colonnes):
    """Chaque étudiant répété pour les semaines 1 à 30 (modèle « rentrée »)."""
    grille = table[list(colonnes)].loc[np.repeat(table.index, len(SEMAINES))].reset_index(drop=True)
    grille.insert(0, COLONNE_SEMAINE, np.tile(SEMAINES, len(table)))
    return grille


def risques_gradient_boosting_rentree(modele, table, colonnes):
    """Matrice (étudiants × 30 semaines) des risques hebdomadaires h(k) prédits."""
    grille = grille_rentree(table, colonnes)
    risques = modele.predict_proba(grille[[COLONNE_SEMAINE] + list(colonnes)])[:, 1]
    return risques.reshape(len(table), len(SEMAINES))


def survie_cox(cph, table, colonnes):
    """Matrice (étudiants × 30 semaines) des survies prédites par le Cox."""
    return cph.predict_survival_function(table[list(colonnes)], times=SEMAINES).T.to_numpy()


def survie_reference(entrainement, nb_etudiants):
    """Kaplan-Meier de 2024 aux semaines 1 à 30, la même courbe pour tous les étudiants."""
    kmf = survie.ajuster_kaplan_meier(entrainement["T"], entrainement["E"])
    courbe = kmf.survival_function_at_times(SEMAINES).to_numpy()
    return np.tile(courbe, (nb_etudiants, 1))


def risques_depuis_survie(survies):
    """h(t) = 1 − S(t) / S(t − 1), avec S(0) = 1 (risque de la semaine t)."""
    precedentes = np.hstack([np.ones((len(survies), 1)), survies[:, :-1]])
    return 1 - survies / precedentes


# ===========================================================================
# 5. Mesures : C-index, Brier score intégré, calibration (D-63)
# ===========================================================================

def c_index(T, E, survie_30):
    """C-index de Harrell : un étudiant qui décroche plus tôt doit avoir une survie
    prédite à 30 semaines plus faible."""
    return float(concordance_index(T, survie_30, E))


def survie_de_la_censure(T, E, derniere):
    """G(t), t = 0 à derniere : Kaplan-Meier « à l'envers » (la censure est l'événement).

    À égalité de semaine, les décrochages passent avant les censures : à risque = T >= t
    moins les décrochages de la semaine t. Si ce nombre vaut 0, G ne change pas.
    """
    T = np.asarray(T)
    E = np.asarray(E)
    valeurs = [1.0]
    for t in range(1, derniere + 1):
        a_risque = (T >= t).sum() - ((T == t) & (E == 1)).sum()
        censures = ((T == t) & (E == 0)).sum()
        precedente = valeurs[-1]
        valeurs.append(precedente * (1 - censures / a_risque) if a_risque > 0 else precedente)
    return pd.Series(valeurs, index=range(derniere + 1))


def brier_par_semaine(T, E, survies, censure, semaines):
    """BS(t) pondéré par l'inverse de la probabilité de censure (IPCW), pour chaque t.

    survies : matrice (étudiants × semaines 1 à 30) ; censure : G(t) estimée sur 2024.
    Décroché au plus tard en t : S(t)² / G(T) ; encore suivi après t : (1 − S(t))² / G(t) ;
    censuré avant t : 0 (son information est reportée sur les autres par les poids).
    """
    T = np.asarray(T)
    E = np.asarray(E)
    resultats = []
    for t in semaines:
        s = survies[:, t - 1]
        decroches = (T <= t) & (E == 1)
        encore_suivis = T > t
        termes = np.zeros(len(T))
        termes[decroches] = s[decroches] ** 2 / censure.loc[T[decroches]].to_numpy()
        termes[encore_suivis] = (1 - s[encore_suivis]) ** 2 / censure.loc[t]
        resultats.append(termes.mean())
    return pd.Series(resultats, index=list(semaines))


def brier_integre(brier):
    """Aire sous BS(t) (méthode des trapèzes) divisée par la durée (dernière − première)."""
    semaines = np.asarray(brier.index, dtype=float)
    return float(np.trapezoid(brier.to_numpy(), semaines) / (semaines[-1] - semaines[0]))


def calibration(risque_predit, T, E, semaine=config.SEMAINE_CALIBRATION, nb_groupes=config.NB_GROUPES_CALIBRATION):
    """Calibration : risque prédit moyen contre risque observé, par groupe de risque.

    Groupes de même taille (à 1 près) selon le rang du risque prédit ; risque observé =
    1 − Kaplan-Meier du groupe à `semaine` (tient compte de la censure).
    Sortie : (table groupe, effectif, risque_predit, risque_observe ; écart absolu moyen).
    """
    risque_predit = np.asarray(risque_predit, dtype=float)
    T = np.asarray(T)
    E = np.asarray(E)
    ordre = np.argsort(risque_predit, kind="stable")
    lignes = []
    for numero, indices in enumerate(np.array_split(ordre, nb_groupes), start=1):
        kmf = survie.ajuster_kaplan_meier(T[indices], E[indices])
        observe = 1 - float(kmf.survival_function_at_times([semaine]).iloc[0])
        lignes.append({"groupe": numero, "effectif": len(indices),
                       "risque_predit": float(risque_predit[indices].mean()), "risque_observe": observe})
    table = pd.DataFrame(lignes)
    ecart = float((table["risque_predit"] - table["risque_observe"]).abs().mean())
    return table, ecart


def risque_semaine_par_ligne(lignes, table, matrice_risques):
    """Risque de la semaine de chaque ligne semaine-étudiant, lu dans une matrice
    (étudiants de `table` × semaines 1 à 30)."""
    position = pd.Series(np.arange(len(table)), index=table[config.COLONNE_ID])
    rangs = position.loc[lignes[config.COLONNE_ID]].to_numpy()
    return matrice_risques[rangs, lignes[COLONNE_SEMAINE].to_numpy() - 1]


# ===========================================================================
# 6. Importance par permutation (D-63)
# ===========================================================================

def colonnes_de_la_variable(colonnes, variable):
    """Colonnes d'une variable : elle-même, ou toutes ses indicatrices « variable=… »."""
    return [c for c in colonnes if c == variable or survie.variable_d_origine(c) == variable]


def importance_rentree(modele, table, colonnes, graine=config.SEED):
    """Baisse du C-index du gradient boosting « rentrée » quand on mélange une variable.

    Le mélange se fait au niveau des étudiants (toutes les indicatrices d'une variable
    qualitative ensemble). Sortie : variable, baisse_moyenne, ecart_type.
    """
    generateur = np.random.default_rng(graine)
    reference = c_index(table["T"], table["E"],
                        survie_depuis_risques(risques_gradient_boosting_rentree(modele, table, colonnes))[:, -1])
    lignes = []
    for variable in VARIABLES_RENTREE_PERMUTATION:
        concernees = colonnes_de_la_variable(colonnes, variable)
        baisses = []
        for _ in range(config.NB_REPETITIONS_PERMUTATION):
            melangee = table.copy()
            ordre = generateur.permutation(len(table))
            melangee[concernees] = table[concernees].to_numpy()[ordre]
            survies = survie_depuis_risques(risques_gradient_boosting_rentree(modele, melangee, colonnes))
            baisses.append(reference - c_index(table["T"], table["E"], survies[:, -1]))
        lignes.append({"variable": variable, "baisse_moyenne": float(np.mean(baisses)),
                       "ecart_type": float(np.std(baisses))})
    return pd.DataFrame(lignes)


def importance_hebdomadaire(modele, lignes, colonnes, graine=config.SEED):
    """Baisse de l'AUC hebdomadaire du modèle hebdomadaire quand on mélange une variable.

    Le mélange se fait au niveau des lignes semaine-étudiant.
    Sortie : variable, baisse_moyenne, ecart_type.
    """
    generateur = np.random.default_rng(graine)
    cible = lignes[COLONNE_EVENEMENT]
    reference = roc_auc_score(cible, modele.predict_proba(lignes[colonnes])[:, 1])
    resultats = []
    for variable in VARIABLES_HEBDOMADAIRES_PERMUTATION:
        concernees = colonnes_de_la_variable(colonnes, variable)
        baisses = []
        for _ in range(config.NB_REPETITIONS_PERMUTATION):
            melangee = lignes[colonnes].copy()
            ordre = generateur.permutation(len(lignes))
            melangee[concernees] = lignes[concernees].to_numpy()[ordre]
            baisses.append(reference - roc_auc_score(cible, modele.predict_proba(melangee)[:, 1]))
        resultats.append({"variable": variable, "baisse_moyenne": float(np.mean(baisses)),
                          "ecart_type": float(np.std(baisses))})
    return pd.DataFrame(resultats)


# ===========================================================================
# 7. Chaîne complète et enregistrement
# ===========================================================================

def mesures_rentree(nom, survies, test, censure):
    """C-index, Brier intégré, Brier à 20 semaines, BS(t) et calibration d'un modèle."""
    brier = brier_par_semaine(test["T"], test["E"], survies, censure, config.SEMAINES_BRIER)
    resultat = {
        "modele": nom,
        "c_index": c_index(test["T"], test["E"], survies[:, -1]),
        "brier_integre": brier_integre(brier),
        "brier_20_semaines": float(brier.loc[config.SEMAINE_CALIBRATION]),
        "ecart_calibration": np.nan,
    }
    return resultat, brier


def ecrire_resultat(df, nom_fichier):
    """Écrit un résultat en CSV dans DOSSIER_RESULTATS (UTF-8, fins de ligne LF)."""
    config.DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = config.DOSSIER_RESULTATS / nom_fichier
    df.to_csv(chemin, sep=config.SEPARATEUR_PROCESSED, index=False, encoding=config.ENCODAGE,
              lineterminator="\n")
    return chemin


def modeles_et_mesures(base, periode):
    """Entraîne les trois modèles sur 2024, les mesure sur 2025. Sortie : dictionnaire de tables."""
    entrainement, test = separer_cohortes(base)
    rentree = variables_rentree(entrainement, test)
    colonnes = rentree["colonnes"]
    table_entrainement, table_test = rentree["entrainement"], rentree["test"]

    # Lignes semaine-étudiant.
    lignes_rentree_2024, colonnes_gb = lignes_semaines(periode, table_entrainement, colonnes)
    lignes_hebdo_2024, colonnes_hebdo = lignes_semaines(periode, table_entrainement, colonnes, hebdomadaire=True)
    lignes_hebdo_2025, _ = lignes_semaines(periode, table_test, colonnes, hebdomadaire=True)

    # Entraînement sur 2024 uniquement.
    gb_rentree = entrainer_gradient_boosting(lignes_rentree_2024, colonnes_gb)
    gb_hebdo = entrainer_gradient_boosting(lignes_hebdo_2024, colonnes_hebdo)
    cph = entrainer_cox(table_entrainement, colonnes)
    schoenfeld = survie.test_schoenfeld(cph, table_entrainement[["T", "E"] + colonnes])

    # Courbes de survie prédites pour 2025.
    risques_gb = risques_gradient_boosting_rentree(gb_rentree, table_test, colonnes)
    survies = {
        "Cox": survie_cox(cph, table_test, colonnes),
        "Gradient boosting": survie_depuis_risques(risques_gb),
        "Référence (Kaplan-Meier 2024)": survie_reference(table_entrainement, len(table_test)),
    }

    # Mesures du modèle « rentrée ».
    censure = survie_de_la_censure(table_entrainement["T"], table_entrainement["E"], config.N_SEMAINES)
    mesures, briers, calibrations = [], {}, []
    for nom, matrice in survies.items():
        resultat, brier = mesures_rentree(nom, matrice, table_test, censure)
        briers[nom] = brier
        if not nom.startswith("Référence"):
            risque_20 = 1 - matrice[:, config.SEMAINE_CALIBRATION - 1]
            table_calibration, ecart = calibration(risque_20, table_test["T"], table_test["E"])
            table_calibration.insert(0, "modele", nom)
            calibrations.append(table_calibration)
            resultat["ecart_calibration"] = ecart
        mesures.append(resultat)
    tableau_brier = pd.DataFrame(briers).rename_axis("semaine").reset_index()

    # Score hebdomadaire : AUC sur les semaines-étudiants 2025.
    cible = lignes_hebdo_2025[COLONNE_EVENEMENT]
    risque_hebdo = gb_hebdo.predict_proba(lignes_hebdo_2025[colonnes_hebdo])[:, 1]
    risque_cox = risque_semaine_par_ligne(lignes_hebdo_2025, table_test, risques_depuis_survie(survies["Cox"]))
    risque_gb_rentree = risque_semaine_par_ligne(lignes_hebdo_2025, table_test, risques_gb)
    hebdomadaire = pd.DataFrame([
        {"modele": "Cox", "auc": roc_auc_score(cible, risque_cox)},
        {"modele": "Gradient boosting « rentrée »", "auc": roc_auc_score(cible, risque_gb_rentree)},
        {"modele": "Gradient boosting hebdomadaire", "auc": roc_auc_score(cible, risque_hebdo),
         "decrochages_attendus": float(risque_hebdo.sum()), "decrochages_observes": int(cible.sum())},
    ])

    # Importance par permutation.
    importances = pd.concat([
        importance_rentree(gb_rentree, table_test, colonnes).assign(modele="rentree", mesure="baisse du C-index"),
        importance_hebdomadaire(gb_hebdo, lignes_hebdo_2025, colonnes_hebdo).assign(
            modele="hebdomadaire", mesure="baisse de l'AUC hebdomadaire"),
    ], ignore_index=True)[["modele", "mesure", "variable", "baisse_moyenne", "ecart_type"]]

    # Données décrites par cohorte (section 2 du notebook).
    donnees = pd.DataFrame([
        {"cohorte": config.COHORTE_ENTRAINEMENT, "role": "entraînement", "etudiants": len(table_entrainement),
         "decrochages": int(table_entrainement["E"].sum()), "semaines_etudiants": len(lignes_hebdo_2024),
         "decrochages_semaines": int(lignes_hebdo_2024[COLONNE_EVENEMENT].sum())},
        {"cohorte": config.COHORTE_TEST, "role": "test", "etudiants": len(table_test),
         "decrochages": int(table_test["E"].sum()), "semaines_etudiants": len(lignes_hebdo_2025),
         "decrochages_semaines": int(cible.sum())},
    ])
    medianes = pd.DataFrame({"variable": list(rentree["medianes"]), "mediane_2024": list(rentree["medianes"].values())})

    predictions = pd.DataFrame({
        config.COLONNE_ID: np.repeat(table_test[config.COLONNE_ID].to_numpy(), len(SEMAINES)),
        COLONNE_SEMAINE: np.tile(SEMAINES, len(table_test)),
        "survie_cox": survies["Cox"].ravel(),
        "survie_gradient_boosting": survies["Gradient boosting"].ravel(),
    })
    scores = pd.DataFrame({
        config.COLONNE_ID: lignes_hebdo_2025[config.COLONNE_ID],
        COLONNE_SEMAINE: lignes_hebdo_2025[COLONNE_SEMAINE],
        "risque_hebdomadaire": risque_hebdo,
        "risque_cox": risque_cox,
    })
    hr = survie.hazard_ratios(cph).reset_index()
    return {
        "ml_donnees.csv": donnees,
        "ml_medianes_2024.csv": medianes,
        "ml_mesures_rentree.csv": pd.DataFrame(mesures),
        "ml_brier_par_semaine.csv": tableau_brier,
        "ml_calibration_20_semaines.csv": pd.concat(calibrations, ignore_index=True),
        "ml_score_hebdomadaire.csv": hebdomadaire,
        "ml_importance.csv": importances,
        "ml_hr_cox_2024.csv": hr,
        "ml_schoenfeld_cox_2024.csv": schoenfeld,
        "ml_predictions_2025.csv": predictions,
        "ml_scores_hebdomadaires_2025.csv": scores,
    }


def lancer():
    """Étape ML de run_all.py : lit les bases, entraîne, mesure et enregistre les résultats."""
    debut = time.perf_counter()
    base, periode = eda.lire_bases()
    resultats = modeles_et_mesures(base, periode)
    for nom_fichier, table in resultats.items():
        ecrire_resultat(table, nom_fichier)
    duree = time.perf_counter() - debut
    print(f"ML de survie (SV-03, SV-04) : {len(resultats)} fichiers écrits dans "
          f"{config.DOSSIER_RESULTATS.relative_to(config.RACINE)} en {duree:.0f} s.")
    return resultats
