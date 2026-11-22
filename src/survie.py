"""Analyse de survie : Kaplan-Meier, log-rank, semaines critiques et modèle de Cox.

Rôle du module : décrire le temps jusqu'au décrochage à partir de base_survie.csv
(T, E et covariables de la rentrée uniquement, D-43 ; aucune variable de tutorat, qui
relève de la partie causale) :
- courbe de Kaplan-Meier globale et par sous-groupe, tests du log-rank (D-46) ;
- risque hebdomadaire et semaines critiques (D-47) ;
- modèle de Cox explicatif sur les 5 000 étudiants (D-48), variables de D-49, valeurs
  manquantes traitées selon D-50, proportionnalité des risques vérifiée selon D-51.
Les résultats sont des associations, pas des effets causaux.

Tâches couvertes : SV-01, SV-02.
"""

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test, proportional_hazard_test
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


# ===========================================================================
# 4. Préparation des données du Cox (D-49, D-50)
# ===========================================================================

def regrouper_region(region):
    """Dakar / Hors Dakar ; une région manquante reste manquante (traitée ensuite)."""
    if pd.isna(region):
        return pd.NA
    return config.REGION_DAKAR if region == config.REGION_DAKAR else config.REGION_HORS_DAKAR


def variables_du_cox(base):
    """Variables du Cox avant codage : numériques et qualitatives de D-49.

    Toutes viennent de config.COVARIABLES_RENTREE ; la mention n'est pas retenue.
    """
    variables = pd.DataFrame(index=base.index)
    variables["age"] = pd.to_numeric(base["age"], errors="raise").astype(float)
    variables["note_bac"] = base["note_bac"].astype(float)
    variables[config.COLONNE_DISTANCE_COX] = np.log2(base["distance_campus_km"].astype(float))
    for variable in [config.VARIABLE_COHORTE, "genre", "boursier", "filiere", "emploi_parallele"]:
        variables[variable] = base[variable].astype("string")
    variables[config.COLONNE_REGION_COX] = base["region_origine"].map(regrouper_region).astype("string")
    return variables


def indicatrices(valeurs, variable):
    """Une colonne 0/1 par modalité présente, sauf la référence de D-49."""
    reference = config.REFERENCES_COX[variable]
    presentes = list(valeurs.unique())
    if reference not in presentes:
        raise ErreurSurvie(f"Modalité de référence « {reference} » absente pour {variable}")
    ordre = modalites_ordonnees(variable, [m for m in presentes if m != config.MODALITE_MANQUANTE])
    if config.MODALITE_MANQUANTE in presentes:
        ordre.append(config.MODALITE_MANQUANTE)
    colonnes = {}
    for modalite in ordre:
        if modalite != reference:
            colonnes[f"{variable}{config.SEPARATEUR_INDICATRICE}{modalite}"] = (valeurs == modalite).astype(int)
    return pd.DataFrame(colonnes, index=valeurs.index)


def preparer_donnees_cox(base, medianes=None, duree="T", evenement="E"):
    """Table d'ajustement du Cox : T, E, variables numériques et indicatrices (D-49, D-50).

    Entrées : base_survie ; medianes = dictionnaire {variable numérique: médiane} à utiliser
    pour remplacer les manquants (ex. médianes de la cohorte 2024 appliquées à 2025, SV-03) ;
    si None, elles sont calculées sur les données reçues ; colonnes de durée et
    d'événement (T et E, ou une variante de sensibilité).
    Variables qualitatives manquantes -> modalité config.MODALITE_MANQUANTE.
    Sortie : (donnees, medianes utilisées). Les colonnes de durée et d'événement sont
    renommées T et E.
    """
    variables = variables_du_cox(base)
    if medianes is None:
        medianes = {v: float(variables[v].median()) for v in config.VARIABLES_COX_NUMERIQUES}
    donnees = pd.DataFrame({"T": base[duree].astype(int), "E": base[evenement].astype(int)}, index=base.index)
    for variable in config.VARIABLES_COX_NUMERIQUES:
        donnees[variable] = variables[variable].fillna(medianes[variable])
    for variable in config.VARIABLES_COX_QUALITATIVES:
        valeurs = variables[variable].fillna(config.MODALITE_MANQUANTE).astype(str)
        donnees = donnees.join(indicatrices(valeurs, variable))
    return donnees.reset_index(drop=True), medianes


def variable_d_origine(colonne):
    """Variable d'origine d'une colonne du Cox (ex. « filiere=Droit » -> « filiere »)."""
    return colonne.split(config.SEPARATEUR_INDICATRICE)[0]


def colonnes_de(donnees, variable):
    """Colonnes (indicatrices ou variable numérique) issues d'une variable d'origine."""
    return [c for c in donnees.columns if c not in ("T", "E") and variable_d_origine(c) == variable]


# ===========================================================================
# 5. Modèle de Cox (D-48, D-51)
# ===========================================================================

def ajuster_cox(donnees, strates=()):
    """Ajuste un Cox sur une table de preparer_donnees_cox.

    strates : variables d'origine selon lesquelles le modèle est stratifié (un risque de
    base propre à chaque modalité, sans hazard ratio pour cette variable).
    """
    colonnes_strates = [c for variable in strates for c in colonnes_de(donnees, variable)]
    cph = CoxPHFitter(alpha=config.ALPHA)
    cph.fit(donnees, duration_col="T", event_col="E", strata=colonnes_strates or None)
    return cph


def test_schoenfeld(cph, donnees):
    """Test des résidus de Schoenfeld par colonne (lifelines, transformation « rank »).

    Sortie : DataFrame colonne, variable, statistique, p.
    """
    test = proportional_hazard_test(cph, donnees, time_transform=config.TRANSFORMATION_SCHOENFELD)
    resultat = test.summary[["test_statistic", "p"]].rename(columns={"test_statistic": "statistique"})
    resultat.index = [i if isinstance(i, str) else i[0] for i in resultat.index]
    resultat.index.name = "colonne"
    resultat = resultat.reset_index()
    resultat.insert(1, "variable", resultat["colonne"].map(variable_d_origine))
    return resultat


def regle_proportionnalite(test):
    """Règle de D-51 appliquée aux variables dont une colonne a p < ALPHA.

    Variable qualitative -> stratification. Variable numérique -> interaction avec la
    période (semaines 1 à FIN_PREMIERE_PERIODE, puis suivantes).
    Sortie : (variables à stratifier, variables numériques à mettre en interaction).
    """
    en_defaut = list(dict.fromkeys(test.loc[test["p"] < config.ALPHA, "variable"]))
    strates = [v for v in en_defaut if v in config.VARIABLES_COX_QUALITATIVES]
    interactions = [v for v in en_defaut if v in config.VARIABLES_COX_NUMERIQUES]
    return strates, interactions


def cox_avec_regle(donnees):
    """Modèle 1 (cohorte en covariable), règle de D-51, puis modèle final.

    Sortie : dictionnaire modele_1, schoenfeld_1, strates, modele_final, schoenfeld_final.
    L'interaction avec la période n'est pas programmée : si une variable numérique viole
    l'hypothèse, l'analyse s'arrête pour que la décision soit revue (D-18).
    """
    modele_1 = ajuster_cox(donnees)
    schoenfeld_1 = test_schoenfeld(modele_1, donnees)
    strates, interactions = regle_proportionnalite(schoenfeld_1)
    if interactions:
        raise ErreurSurvie(f"Variables numériques non proportionnelles (D-51, interaction avec la période "
                           f"à mettre en place) : {interactions}")
    modele_final = ajuster_cox(donnees, strates)
    return {"modele_1": modele_1, "schoenfeld_1": schoenfeld_1, "strates": strates,
            "modele_final": modele_final, "schoenfeld_final": test_schoenfeld(modele_final, donnees)}


def hazard_ratios(cph):
    """Tableau des hazard ratios : HR, IC à 95 % et p de chaque colonne."""
    resume = cph.summary
    return pd.DataFrame({
        "HR": resume["exp(coef)"],
        "IC bas": resume[f"exp(coef) lower {100 * (1 - config.ALPHA):.0f}%"],
        "IC haut": resume[f"exp(coef) upper {100 * (1 - config.ALPHA):.0f}%"],
        "p": resume["p"],
    }).rename_axis("variable")


# ===========================================================================
# 6. Sensibilité
# ===========================================================================

COLONNES_BRUTES_DU_COX = ["cohorte", "genre", "age", "boursier", "filiere", "note_bac", "region_origine",
                          "distance_campus_km", "emploi_parallele"]


def sensibilite_dossiers_complets(base, strates, hr_reference):
    """Modèle final sur les étudiants sans aucune covariable manquante (D-50).

    Sortie : dictionnaire n, evenements, hr (tableau), ecart_max (plus grand écart absolu
    des HR avec le modèle de référence, sur les colonnes communes).
    """
    complets = base.dropna(subset=COLONNES_BRUTES_DU_COX)
    donnees, _ = preparer_donnees_cox(complets)
    hr = hazard_ratios(ajuster_cox(donnees, strates))
    communes = hr.index.intersection(hr_reference.index)
    ecart = (hr.loc[communes, "HR"] - hr_reference.loc[communes, "HR"]).abs()
    return {"n": len(complets), "evenements": int(complets["E"].sum()), "hr": hr, "ecart_max": float(ecart.max())}


def sensibilite_seuils(base, strates, seuils=config.SEUILS_SENSIBILITE):
    """Survie globale et HR du modèle final avec T et E calculés aux seuils 3 et 5 semaines.

    Sortie : (survies, hr) : survies = S à 10, 20, 30 semaines par seuil ; hr = HR par
    seuil (colonnes), y compris le seuil de référence.
    """
    variantes = {f"{config.SEUIL_INACTIVITE} semaines (référence)": ("T", "E")}
    for seuil in seuils:
        variantes[f"{seuil} semaines"] = (f"T_seuil{seuil}", f"E_seuil{seuil}")
    survies, hr = [], {}
    for nom, (duree, evenement) in variantes.items():
        global_ = kaplan_meier_global(base, duree, evenement)["survies"]
        survies.append(global_.assign(seuil=nom, decrochages=int(base[evenement].sum())))
        donnees, _ = preparer_donnees_cox(base, duree=duree, evenement=evenement)
        hr[nom] = hazard_ratios(ajuster_cox(donnees, strates))["HR"]
    return pd.concat(survies, ignore_index=True), pd.DataFrame(hr)
