"""Analyse causale : le tutorat fait-il baisser le décrochage ?

Rôle du module :
- conception (sections 1 à 11), sans regarder le décrochage par équipe (D-59) : moment
  d'entrée en tutorat, « photo » de la semaine 8 contre le temps immortel (D-53, D-54),
  covariables et score de propension (D-55, D-56), poids stabilisés, support commun,
  équilibre des deux équipes, diagnostic hors critère, figure du DAG ;
- effet (section 12), une fois la conception relue (R02) et figée (D-57, D-61) :
  courbes de Kaplan-Meier pondérées, risque à 30 semaines, RMST, HR, bootstrap, E-value.

Tâches couvertes : CA-01 à CA-04 (CA-05 viendra s'y ajouter).
"""

import time
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.path import Path
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.exceptions import ConvergenceError, StatisticalWarning
from lifelines.statistics import proportional_hazard_test
from lifelines.utils import restricted_mean_survival_time
from scipy.stats import rankdata

from src import config, eda, survie


class ErreurCausal(Exception):
    """Cas non prévu par la spécification causale (D-53 à D-59) : on s'arrête."""


# Morceaux de noms de colonnes qui ne doivent jamais entrer dans le score (D-55) :
# colonnes de tutorat, variables de sensibilité, durée et événement.
MOTS_INTERDITS = ["tutor", "tuteur", "seance", "motif", "statut", "seuil"]
NOMS_INTERDITS = ["T", "E", "evenement"]

SUFFIXE_MOYENNE = "_moy"
PREFIXE_CARRE = "carre_"


# ===========================================================================
# 1. Moment d'entrée en tutorat (CA-01)
# ===========================================================================

def semaine_debut_inconnue(base):
    """Masque des étudiants tutorés dont la semaine de début est inconnue (D-26)."""
    return base["statut_tutorat"] == config.STATUT_TUTORAT_SEMAINE_INCONNUE


def debuts_pendant_le_suivi(base):
    """Semaines de début connues comprises entre 1 et N_SEMAINES (tous les tutorats).

    Les débuts hors suivi (ex. semaine 45, D-25) et les semaines inconnues sont écartés.
    """
    tutorats = base[base["statut_tutorat"] != config.STATUT_NON_TUTORE]
    semaines = tutorats["semaine_debut_tutorat"].dropna().astype(int)
    return semaines[(semaines >= 1) & (semaines <= config.N_SEMAINES)]


def entree_en_tutorat(base, semaine=config.SEMAINE_LANDMARK):
    """Répartition des semaines de début (sans T ni E par équipe).

    Sortie : dictionnaire : tableau (semaine, effectif, % cumulé), nombre de débuts
    connus pendant le suivi, première et dernière semaine, nombre et part (%) au plus
    tard à `semaine`, motifs d'orientation (sur tous les tutorats).
    """
    semaines = debuts_pendant_le_suivi(base)
    effectifs = semaines.value_counts().sort_index()
    tableau = pd.DataFrame({"semaine": effectifs.index, "effectif": effectifs.values})
    tableau["pct_cumule"] = 100 * tableau["effectif"].cumsum() / len(semaines)
    au_plus_tard = int((semaines <= semaine).sum())
    tutorats = base[base["statut_tutorat"] != config.STATUT_NON_TUTORE]
    return {
        "tableau": tableau,
        "nb_debuts": len(semaines),
        "premiere": int(semaines.min()),
        "derniere": int(semaines.max()),
        "nb_au_plus_tard": au_plus_tard,
        "part_au_plus_tard": 100 * au_plus_tard / len(semaines),
        "motifs": tutorats["motif_orientation"].value_counts(),
    }


# ===========================================================================
# 2. Différence standardisée (utilisée partout dans la conception)
# ===========================================================================

def difference_standardisee(valeurs, traite, poids=None):
    """Différence standardisée (SMD) entre tutorés (traite = 1) et autres (traite = 0).

    Numérateur : moyenne (pondérée si `poids` est donné) des tutorés moins celle des
    autres. Dénominateur : racine((variance tutorés + variance autres) / 2), variances
    NON pondérées (D-56) : il ne bouge pas quand les poids changent, ce qui permet de
    comparer avant et après pondération sur la même échelle.
    """
    valeurs = np.asarray(valeurs, dtype=float)
    traite = np.asarray(traite, dtype=int)
    if poids is None:
        poids = np.ones(len(valeurs))
    poids = np.asarray(poids, dtype=float)
    tutores = traite == 1
    autres = traite == 0
    ecart = (np.average(valeurs[tutores], weights=poids[tutores])
             - np.average(valeurs[autres], weights=poids[autres]))
    variance_tutores = np.var(valeurs[tutores], ddof=1)
    variance_autres = np.var(valeurs[autres], ddof=1)
    denominateur = np.sqrt((variance_tutores + variance_autres) / 2)
    if denominateur == 0:
        # Variable constante dans les deux équipes : aucun écart possible.
        if ecart == 0:
            return 0.0
        raise ErreurCausal("Différence standardisée impossible : variance nulle mais moyennes différentes")
    return float(ecart / denominateur)


# ===========================================================================
# 3. Activité moyenne sur une fenêtre de semaines
# ===========================================================================

def activite_moyenne(periode, identifiants, premiere, derniere):
    """Moyenne par étudiant des variables d'activité sur les semaines [premiere ; derniere].

    Entrées : base_periode_personne ; liste d'identifiants (doublons acceptés : un
    tirage bootstrap peut reprendre plusieurs fois le même étudiant) ; fenêtre.
    Seules les semaines renseignées comptent ; une variable sans aucune valeur sur la
    fenêtre reste manquante. Colonnes de la semaine elle-même (pas *_prec).
    Sortie : une ligne par identifiant reçu, dans le même ordre : id_etudiant et
    <variable>_moy.
    """
    dans_fenetre = periode[(periode["semaine"] >= premiere) & (periode["semaine"] <= derniere)]
    moyennes = dans_fenetre.groupby(config.COLONNE_ID)[config.VARIABLES_ACTIVITE_PROPENSION].mean()
    moyennes.columns = [f"{v}{SUFFIXE_MOYENNE}" for v in moyennes.columns]
    resultat = moyennes.reindex(list(identifiants))
    resultat.index.name = config.COLONNE_ID
    return resultat.reset_index()


def ce_qui_precede_entree(base, periode):
    """Activité des semaines qui précèdent le début du tutorat (CA-01, D-55).

    Pour chaque semaine k de config.SEMAINES_DEBUT_ANALYSEES : éligibles = étudiants
    encore suivis en k (T >= k), semaine de début connue, pas de tutorat commencé avant
    k ; « commencent » = début en semaine k. Pour chaque variable d'activité, moyenne
    par étudiant sur les semaines max(1, k - 2) à k - 1, puis SMD sans pondération
    « commencent » contre autres éligibles. Seuls T et la semaine de début servent à
    définir les éligibles ; aucun décrochage n'est comparé.
    Sortie : une ligne par k (k, commencent, eligibles, une colonne smd_<variable>).
    """
    connue = ~semaine_debut_inconnue(base)
    debut = base["semaine_debut_tutorat"]
    lignes = []
    for k in config.SEMAINES_DEBUT_ANALYSEES:
        deja_commence = (debut < k).fillna(False).astype(bool)
        eligibles = base[(base["T"] >= k) & connue & ~deja_commence]
        commence = (eligibles["semaine_debut_tutorat"] == k).fillna(False).astype(int).to_numpy()
        activite = activite_moyenne(periode, eligibles[config.COLONNE_ID],
                                    max(1, k - config.SEMAINES_AVANT_DEBUT), k - 1)
        ligne = {"k": k, "commencent": int(commence.sum()), "eligibles": len(eligibles)}
        for variable in config.VARIABLES_ACTIVITE_PROPENSION:
            valeurs = activite[f"{variable}{SUFFIXE_MOYENNE}"].to_numpy()
            renseignes = ~np.isnan(valeurs)
            ligne[f"smd_{variable}"] = difference_standardisee(valeurs[renseignes], commence[renseignes])
        lignes.append(ligne)
    return pd.DataFrame(lignes)


# ===========================================================================
# 4. La photo (landmark) : choix de la semaine et population (D-53, D-54)
# ===========================================================================

def population_photo(base, semaine, duree="T", evenement="E"):
    """Étudiants sur la photo de fin de `semaine` (D-54).

    Sur la photo : encore suivis et sans décrochage (duree > semaine), sauf semaine de
    début inconnue (D-26). tutore_photo = 1 si le tutorat a commencé au plus tard en
    `semaine`, sinon 0 (y compris un tutorat qui commencera plus tard ou hors suivi :
    ni déplacé, ni retiré, D-54). Les colonnes de durée et d'événement sont gardées
    telles quelles pour CA-04 ; aucun calcul n'est fait dessus ici.
    """
    sur_photo = (base[duree] > semaine) & ~semaine_debut_inconnue(base)
    population = base[sur_photo].copy()
    commence = (population["semaine_debut_tutorat"] <= semaine).fillna(False).astype(bool)
    population["tutore_photo"] = commence.astype(int)
    return population.reset_index(drop=True)


def ligne_photo(base, semaine, debuts):
    """Une ligne du tableau des photos pour la semaine `semaine` (voir tableau_des_photos)."""
    inconnue = semaine_debut_inconnue(base)
    debut = base["semaine_debut_tutorat"]
    sortis = base[base["T"] <= semaine]
    population = population_photo(base, semaine)
    tutores = int(population["tutore_photo"].sum())
    non_tutores = population[population["tutore_photo"] == 0]
    debut_non_tutores = non_tutores["semaine_debut_tutorat"]
    futurs = int(((debut_non_tutores > semaine) & (debut_non_tutores <= config.N_SEMAINES)).fillna(False).sum())
    partis = ((debut <= semaine) & (debut < base["T"]) & (base["T"] <= semaine)).fillna(False)
    return {
        "photo": semaine,
        "sur_la_photo": len(population),
        "sortis_avant": len(sortis),
        # Seule exception à D-59 : on compte les sorties avant la photo, toutes équipes confondues.
        "dont_decrochages": int(sortis["E"].sum()),
        "tutores": tutores,
        "pct_tutores": 100 * tutores / len(population),
        "non_tutores": len(non_tutores),
        "futurs_tutores": futurs,
        "pct_futurs_tutores": 100 * futurs / len(non_tutores),
        "pct_debuts_couverts": 100 * (debuts <= semaine).sum() / len(debuts),
        "tutores_partis_avant": int(partis.sum()),
        "semaines_apres_photo": config.N_SEMAINES - semaine,
        "inconnus_retires": int((inconnue & (base["T"] > semaine)).sum()),
    }


def tableau_des_photos(base, photos=config.PHOTOS_COMPAREES):
    """Tableau de choix de la photo (D-53) : une ligne par semaine L de `photos`.

    Colonnes : sur la photo ; sortis avant (toutes équipes) et dont décrochages ;
    tutorés (effectif, %) ; non tutorés ; futurs tutorés parmi eux (début entre L + 1
    et 30) ; part des débuts connus couverts ; tutorés partis avant la photo ; semaines
    de suivi après la photo ; étudiants à semaine de début inconnue retirés.
    """
    debuts = debuts_pendant_le_suivi(base)
    return pd.DataFrame([ligne_photo(base, semaine, debuts) for semaine in photos])


# ===========================================================================
# 5. Covariables du score de propension (D-55)
# ===========================================================================

def verifier_colonnes_autorisees(colonnes):
    """Garde-fou : ErreurCausal si une colonne interdite entre dans le score (D-55)."""
    for colonne in colonnes:
        nom = colonne.lower()
        if colonne in NOMS_INTERDITS or any(mot in nom for mot in MOTS_INTERDITS):
            raise ErreurCausal(f"Colonne interdite dans le score de propension : {colonne}")


def verifier_liste_positive(colonnes, variables_exclues=()):
    """Liste positive (D-61, principe de D-43) : ErreurCausal pour toute colonne qui
    n'est ni une variable numérique du score, ni une indicatrice d'une variable
    qualitative du Cox (moins les variables exclues)."""
    numeriques = colonnes_numeriques_du_score(variables_exclues)
    qualitatives = [v for v in config.VARIABLES_COX_QUALITATIVES if v not in variables_exclues]
    for colonne in colonnes:
        indicatrice = (config.SEPARATEUR_INDICATRICE in colonne
                       and survie.variable_d_origine(colonne) in qualitatives)
        if colonne not in numeriques and not indicatrice:
            raise ErreurCausal(f"Colonne hors de la liste positive du score : {colonne}")


def covariables_du_score(population, periode, fenetre, duree="T", evenement="E", variables_exclues=()):
    """Covariables du score : profil codé comme le Cox + activité moyenne (D-55).

    Profil : survie.preparer_donnees_cox (mêmes références, même règle des manquants,
    médianes calculées sur la population reçue), sans T ni E, ni les variables exclues
    (bonus F8). Activité : moyenne des 4 variables sur la fenêtre (première, dernière) ;
    manquante -> médiane de la population reçue. L'index est remis à zéro d'abord : un
    tirage bootstrap contient des étudiants en double (RV02-03).
    Sortie : (X, médianes utilisées pour toutes les variables numériques).
    """
    population = population.reset_index(drop=True)
    donnees, medianes = survie.preparer_donnees_cox(population, duree=duree, evenement=evenement,
                                                    variables_exclues=variables_exclues)
    X = donnees.drop(columns=["T", "E"]).astype(float)
    activite = activite_moyenne(periode, population[config.COLONNE_ID], fenetre[0], fenetre[1])
    medianes = dict(medianes)
    for variable in config.VARIABLES_ACTIVITE_PROPENSION:
        colonne = f"{variable}{SUFFIXE_MOYENNE}"
        medianes[colonne] = float(activite[colonne].median())
        X[colonne] = activite[colonne].fillna(medianes[colonne]).to_numpy()
    verifier_liste_positive(X.columns, variables_exclues)
    verifier_colonnes_autorisees(X.columns)
    return X, medianes


def colonnes_numeriques_du_score(variables_exclues=()):
    """Variables numériques du score : âge, note du bac, log2 distance, 4 moyennes d'activité."""
    numeriques = [v for v in config.VARIABLES_COX_NUMERIQUES if v not in variables_exclues]
    return numeriques + [f"{v}{SUFFIXE_MOYENNE}" for v in config.VARIABLES_ACTIVITE_PROPENSION]


def ajouter_carres(X):
    """Retouche fixée d'avance (D-56) : ajoute le carré de chaque variable numérique."""
    avec_carres = X.copy()
    for colonne in colonnes_numeriques_du_score():
        if colonne in X.columns:
            avec_carres[f"{PREFIXE_CARRE}{colonne}"] = X[colonne] ** 2
    return avec_carres


# ===========================================================================
# 6. Score de propension et support commun (CA-02, D-56)
# ===========================================================================

def ajuster_score(X, traite):
    """Régression logistique sans pénalité (GLM binomial avec constante, statsmodels).

    Sortie : (modèle ajusté, score = probabilité prédite d'être tutoré à la photo).
    """
    exogenes = sm.add_constant(X, has_constant="add")
    modele = sm.GLM(np.asarray(traite, dtype=float), exogenes, family=sm.families.Binomial()).fit()
    if not modele.converged:
        # Un score mal estimé donnerait des poids faux sans le dire (RV02-03).
        raise ErreurCausal("La régression logistique du score de propension n'a pas convergé")
    return modele, np.asarray(modele.predict(exogenes), dtype=float)


def auc_par_les_rangs(score, traite):
    """AUC = (somme des rangs des tutorés − n1(n1 + 1)/2) / (n1 × n0).

    C'est la probabilité qu'un tutoré pris au hasard ait un score plus élevé qu'un
    non-tutoré pris au hasard (ex aequo comptés pour moitié).
    """
    traite = np.asarray(traite, dtype=int)
    rangs = rankdata(score)
    n1 = int(traite.sum())
    n0 = len(traite) - n1
    return float((rangs[traite == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def rapports_de_cotes(modele):
    """Rapports de cotes du score : exp(coef), IC à 95 %, p (sans la constante)."""
    intervalles = modele.conf_int(alpha=config.ALPHA)
    tableau = pd.DataFrame({
        "rapport_de_cotes": np.exp(modele.params),
        "ic_bas": np.exp(intervalles[0]),
        "ic_haut": np.exp(intervalles[1]),
        "p": modele.pvalues,
    })
    return tableau.drop(index="const")


def support_commun(score, traite):
    """Support commun : [plus grand des minimums ; plus petit des maximums] des deux équipes.

    Sortie : dictionnaire : bornes, min et max par équipe, masque « dans le support »,
    effectifs hors support par équipe.
    """
    score = np.asarray(score, dtype=float)
    traite = np.asarray(traite, dtype=int)
    tutores = score[traite == 1]
    autres = score[traite == 0]
    bas = max(tutores.min(), autres.min())
    haut = min(tutores.max(), autres.max())
    dans_support = (score >= bas) & (score <= haut)
    return {
        "bornes": (float(bas), float(haut)),
        "tutores_min_max": (float(tutores.min()), float(tutores.max())),
        "autres_min_max": (float(autres.min()), float(autres.max())),
        "dans_support": dans_support,
        "hors_support_tutores": int((~dans_support & (traite == 1)).sum()),
        "hors_support_autres": int((~dans_support & (traite == 0)).sum()),
    }


# ===========================================================================
# 7. Poids stabilisés et troncature (CA-03, D-56)
# ===========================================================================

def poids_stabilises(score, traite):
    """Poids stabilisés (effet moyen sur toute la photo, ATE).

    Tutorés : P(tutoré) / score ; autres : (1 − P(tutoré)) / (1 − score). Le
    numérateur garde une moyenne des poids proche de 1 (taille de la photo conservée).
    """
    score = np.asarray(score, dtype=float)
    traite = np.asarray(traite, dtype=int)
    if ((score <= 0) | (score >= 1)).any():
        # Un score de 0 ou 1 donnerait un poids infini.
        raise ErreurCausal("Score de propension égal à 0 ou 1 : poids infini")
    part_tutores = traite.mean()
    return np.where(traite == 1, part_tutores / score, (1 - part_tutores) / (1 - score))


def tronquer_poids(poids):
    """Troncature aux percentiles 1 et 99 de l'ensemble des poids (numpy, méthode par défaut).

    Sortie : (poids tronqués, (borne basse, borne haute), nombre de poids modifiés).
    """
    poids = np.asarray(poids, dtype=float)
    bas, haut = np.percentile(poids, config.PERCENTILES_TRONCATURE)
    tronques = np.clip(poids, bas, haut)
    return tronques, (float(bas), float(haut)), int((tronques != poids).sum())


def taille_effective(poids):
    """Taille effective (Σw)² / Σw² : nombre d'étudiants « équivalents » après pondération."""
    poids = np.asarray(poids, dtype=float)
    return float(poids.sum() ** 2 / (poids ** 2).sum())


# ===========================================================================
# 8. Équilibre des deux équipes (CA-03, D-56)
# ===========================================================================

def matrice_equilibre(population, X, variables_exclues=()):
    """Variables dont on vérifie l'équilibre.

    Numériques : âge, note du bac, log2 distance, 4 moyennes d'activité (valeurs du
    score, manquants remplacés). Qualitatives : une colonne 0/1 par modalité, références
    et « (manquant) » comprises (une référence peut être déséquilibrée elle aussi).
    Les variables exclues du score (bonus F8) n'y figurent pas.
    """
    matrice = X[colonnes_numeriques_du_score(variables_exclues)].copy()
    variables = survie.variables_du_cox(population.reset_index(drop=True))
    for variable in [v for v in config.VARIABLES_COX_QUALITATIVES if v not in variables_exclues]:
        valeurs = variables[variable].fillna(config.MODALITE_MANQUANTE).astype(str)
        presentes = list(valeurs.unique())
        ordre = survie.modalites_ordonnees(variable, [m for m in presentes if m != config.MODALITE_MANQUANTE])
        if config.MODALITE_MANQUANTE in presentes:
            ordre.append(config.MODALITE_MANQUANTE)
        for modalite in ordre:
            colonne = f"{variable}{config.SEPARATEUR_INDICATRICE}{modalite}"
            matrice[colonne] = (valeurs == modalite).astype(int).to_numpy()
    return matrice


def tableau_equilibre(matrice, traite, poids):
    """SMD avant et après pondération pour chaque ligne, et le critère |SMD| < SEUIL_SMD."""
    lignes = []
    for colonne in matrice.columns:
        avant = difference_standardisee(matrice[colonne], traite)
        apres = difference_standardisee(matrice[colonne], traite, poids)
        lignes.append({"variable": colonne, "smd_avant": avant, "smd_apres": apres,
                       "equilibre": abs(apres) < config.SEUIL_SMD})
    return pd.DataFrame(lignes)


# ===========================================================================
# 9. Chaîne de conception complète (relancée telle quelle en C11)
# ===========================================================================

def score_poids_equilibre(X, traite, matrice):
    """Score -> support commun -> poids bruts et tronqués -> tableau d'équilibre."""
    modele, score = ajuster_score(X, traite)
    poids = poids_stabilises(score, traite)
    tronques, bornes, nb_modifies = tronquer_poids(poids)
    traite = np.asarray(traite, dtype=int)
    return {
        "modele": modele,
        "score": score,
        "support": support_commun(score, traite),
        "poids_bruts": poids,
        "poids": tronques,
        "bornes_troncature": bornes,
        "nb_poids_modifies": nb_modifies,
        "tailles_effectives": {
            "tutores": taille_effective(tronques[traite == 1]),
            "autres": taille_effective(tronques[traite == 0]),
        },
        "equilibre": tableau_equilibre(matrice, traite, tronques),
    }


def chaine_de_conception(population, periode, fenetre, semaine, duree="T", evenement="E", variables_exclues=()):
    """Enchaîne covariables, score, support, poids et équilibre pour une population.

    Entrées : population d'une photo (population_photo, ou un tirage bootstrap de
    celle-ci) ; base_periode_personne ; fenêtre d'activité (première, dernière) ;
    semaine de la photo (la fenêtre ne doit pas la dépasser, D-55) ; colonnes de durée
    et d'événement (variantes de seuil) ; variables exclues du score (bonus F8).
    Si une ligne reste à |SMD| >= SEUIL_SMD après pondération, une seule retouche fixée
    d'avance (D-56) : carrés des variables numériques ajoutés au score ; le résultat
    final est rapporté tel quel. Sortie : dictionnaire (voir score_poids_equilibre)
    + X, matrice d'équilibre, médianes, tableau d'équilibre de la première tentative,
    retouche (booléen).
    """
    if fenetre[1] > semaine:
        # L'activité après la photo est postérieure au traitement (avenir, médiateur).
        raise ErreurCausal(f"Fenêtre d'activité {fenetre} postérieure à la photo de la semaine {semaine}")
    population = population.reset_index(drop=True)
    traite = population["tutore_photo"].to_numpy()
    X, medianes = covariables_du_score(population, periode, fenetre, duree=duree, evenement=evenement,
                                       variables_exclues=variables_exclues)
    matrice = matrice_equilibre(population, X, variables_exclues)
    resultat = score_poids_equilibre(X, traite, matrice)
    equilibre_initial = resultat["equilibre"]
    retouche = not equilibre_initial["equilibre"].all()
    if retouche:
        X = ajouter_carres(X)
        resultat = score_poids_equilibre(X, traite, matrice)
    resultat.update({
        "X": X,
        "matrice": matrice,
        "medianes": medianes,
        "traite": traite,
        "equilibre_initial": equilibre_initial,
        "retouche": retouche,
        "critere_atteint": bool(resultat["equilibre"]["equilibre"].all()),
    })
    return resultat


# ===========================================================================
# 10. Diagnostic hors critère et ce qu'on estime exactement (RV02-06, RV02-07, D-61)
# ===========================================================================

def ligne_diagnostic(nom, valeurs, traite, poids):
    """SMD avant et après pondération d'une variable hors score (valeurs vides ignorées)."""
    valeurs = np.asarray(valeurs, dtype=float)
    renseignes = ~np.isnan(valeurs)
    traite = np.asarray(traite)[renseignes]
    poids = np.asarray(poids)[renseignes]
    return {"variable": nom,
            "smd_avant": difference_standardisee(valeurs[renseignes], traite),
            "smd_apres": difference_standardisee(valeurs[renseignes], traite, poids)}


def diagnostic_hors_critere(population, periode, traite, poids, semaine=config.SEMAINE_LANDMARK):
    """Équilibre de variables mesurées avant la photo mais absentes du score (RV02-06).

    Notes et connexions des 2 dernières semaines avant la photo, chaque mention du bac,
    chaque région d'origine détaillée, nombre de semaines inactives sur les semaines 1 à
    `semaine`. Simple diagnostic : le score n'est pas modifié (l'activité récente est en
    partie un médiateur ; la mention découle de la note du bac).
    Sortie : variable, smd_avant, smd_apres.
    """
    population = population.reset_index(drop=True)
    identifiants = population[config.COLONNE_ID]
    debut_recent = semaine - config.SEMAINES_RECENTES_DIAGNOSTIC + 1
    recente = activite_moyenne(periode, identifiants, debut_recent, semaine)
    lignes = [
        ligne_diagnostic(f"note_moyenne semaines {debut_recent}-{semaine}", recente[f"note_moyenne{SUFFIXE_MOYENNE}"],
                         traite, poids),
        ligne_diagnostic(f"nb_connexions_lms semaines {debut_recent}-{semaine}",
                         recente[f"nb_connexions_lms{SUFFIXE_MOYENNE}"], traite, poids),
    ]
    for variable in ["mention_bac", "region_origine"]:
        valeurs = population[variable].fillna(config.MODALITE_MANQUANTE).astype(str)
        presentes = [m for m in valeurs.unique() if m != config.MODALITE_MANQUANTE]
        ordre = survie.modalites_ordonnees(variable, presentes)
        if (valeurs == config.MODALITE_MANQUANTE).any():
            ordre.append(config.MODALITE_MANQUANTE)
        for modalite in ordre:
            lignes.append(ligne_diagnostic(f"{variable}{config.SEPARATEUR_INDICATRICE}{modalite}",
                                           (valeurs == modalite).astype(int), traite, poids))
    fenetre = periode[(periode["semaine"] >= 1) & (periode["semaine"] <= semaine)]
    inactives = (fenetre["etat_activite"] == config.ETAT_INACTIF).groupby(fenetre[config.COLONNE_ID]).sum()
    lignes.append(ligne_diagnostic(f"semaines inactives 1-{semaine}",
                                   inactives.reindex(identifiants).fillna(0).to_numpy(), traite, poids))
    return pd.DataFrame(lignes)


def ce_qu_on_estime(base, periode, population, semaine=config.SEMAINE_LANDMARK):
    """Chiffres des biais écrits d'avance (D-59, D-61 point 11), sans décrochage par équipe.

    - recouvrement : chez les tutorés de la photo, nombre moyen de semaines de la fenêtre
      1 à `semaine` qui vont de la semaine du début à la photo (début compris) ;
    - décrochages silencieux (toutes équipes) dont la série de semaines inactives déborde
      après la photo : T entre semaine − SEUIL_INACTIVITE + 2 et semaine ;
    - étudiants de la photo inactifs la semaine de la photo, et inactifs depuis la semaine
      précédente ;
    - tutorés partis avant la photo (début <= semaine, début < T, T <= semaine).
    """
    tutores = population[population["tutore_photo"] == 1]
    recouvrement = (semaine - tutores["semaine_debut_tutorat"].astype(float) + 1).mean()
    premiere = semaine - config.SEUIL_INACTIVITE + 2
    silencieux = base[(base["type_evenement"] == config.EVENEMENT_DECROCHAGE_SILENCIEUX)
                      & (base["T"] >= premiere) & (base["T"] <= semaine)]
    sur_photo = periode[periode[config.COLONNE_ID].isin(population[config.COLONNE_ID])]
    inactifs = set(sur_photo.loc[(sur_photo["semaine"] == semaine)
                                 & (sur_photo["etat_activite"] == config.ETAT_INACTIF), config.COLONNE_ID])
    inactifs_avant = set(sur_photo.loc[(sur_photo["semaine"] == semaine - 1)
                                       & (sur_photo["etat_activite"] == config.ETAT_INACTIF), config.COLONNE_ID])
    debut = base["semaine_debut_tutorat"]
    partis = ((debut <= semaine) & (debut < base["T"]) & (base["T"] <= semaine)).fillna(False)
    return {
        "recouvrement_moyen": float(recouvrement),
        "silencieux_par_semaine": silencieux["T"].value_counts().sort_index(),
        "nb_silencieux": len(silencieux),
        "inactifs_semaine_photo": len(inactifs),
        "inactifs_depuis_semaine_precedente": len(inactifs & inactifs_avant),
        "tutores_partis_avant": int(partis.sum()),
    }


# ===========================================================================
# 11. Figure du DAG (CA-01, D-55)
# ===========================================================================

COULEURS_DAG = {
    "a_prendre_en_compte": ("#d8eef0", "#2b7a85"),
    "tutorat_et_resultat": ("#e9e0f5", "#6a3d9a"),
    "ne_pas_prendre_en_compte": ("#ececec", "#6b6b6b"),
    "non_mesure": ("#f5f5f5", "#8a8a8a"),
}

# Boîtes du DAG : (x du centre, y du centre, titre, sous-titre, famille de couleur).
BOITES_DAG = {
    "profil": (0.22, 0.84, "Profil à la rentrée", "âge, note du bac, bourse, emploi…", "a_prendre_en_compte"),
    "activite": (0.78, 0.84, "Activité des semaines 1 à 8", "notes, absences, connexions, devoirs",
                 "a_prendre_en_compte"),
    "tutorat": (0.22, 0.52, "Tutorat commencé", "au plus tard en semaine 8", "tutorat_et_resultat"),
    "decrochage": (0.78, 0.52, "Décrochage", "semaines 9 à 30", "tutorat_et_resultat"),
    "mediateur": (0.50, 0.28, "Activité après le début du tutorat", "médiateur : ne pas prendre en compte",
                  "ne_pas_prendre_en_compte"),
    "non_mesures": (0.50, 0.07, "Facteurs non mesurés", "motivation, famille, santé (E-value)", "non_mesure"),
}
LARGEUR_BOITE = 0.34
HAUTEUR_BOITE = 0.11
# Couloir à droite des boîtes pour la flèche « facteurs non mesurés -> activité » (RV02-07).
COULOIR_DROIT_DAG = 1.01
MARGE_DROITE_DAG = 1.04


def bord_de_boite(nom, cote):
    """Point du bord d'une boîte (cote : haut, bas, gauche, droite, ou coin bas-gauche…)."""
    x, y = BOITES_DAG[nom][0], BOITES_DAG[nom][1]
    demi_l, demi_h = LARGEUR_BOITE / 2, HAUTEUR_BOITE / 2
    decalages = {
        "haut": (0, demi_h), "bas": (0, -demi_h), "gauche": (-demi_l, 0), "droite": (demi_l, 0),
        "bas_droite": (demi_l * 0.6, -demi_h), "bas_gauche": (-demi_l * 0.6, -demi_h),
        "haut_droite": (demi_l * 0.6, demi_h), "haut_gauche": (-demi_l * 0.6, demi_h),
    }
    dx, dy = decalages[cote]
    return x + dx, y + dy


def dessiner_boite(axe, nom):
    """Boîte arrondie avec titre (gras) et sous-titre."""
    x, y, titre, sous_titre, famille = BOITES_DAG[nom]
    fond, bord = COULEURS_DAG[famille]
    style_bord = "--" if famille == "non_mesure" else "-"
    axe.add_patch(FancyBboxPatch((x - LARGEUR_BOITE / 2, y - HAUTEUR_BOITE / 2), LARGEUR_BOITE, HAUTEUR_BOITE,
                                 boxstyle="round,pad=0,rounding_size=0.025", facecolor=fond,
                                 edgecolor=bord, linewidth=1.6, linestyle=style_bord, zorder=2))
    axe.text(x, y + 0.018, titre, ha="center", va="center", fontsize=12, fontweight="bold", zorder=3)
    axe.text(x, y - 0.025, sous_titre, ha="center", va="center", fontsize=10, color="#333333", zorder=3)


def dessiner_fleche(axe, depart, arrivee, couleur="#444444", epaisseur=1.4, pointilles=False, courbure=0.0):
    """Flèche entre deux points (bords de boîtes)."""
    axe.add_patch(FancyArrowPatch(depart, arrivee, arrowstyle="-|>", mutation_scale=16, color=couleur,
                                  linewidth=epaisseur, linestyle="--" if pointilles else "-",
                                  connectionstyle=f"arc3,rad={courbure}", zorder=4))


def dessiner_dag(chemin):
    """Dessine le DAG de D-55 et l'enregistre en PNG à `chemin`."""
    figure, axe = plt.subplots(figsize=(11, 8.5))
    axe.set_xlim(0, MARGE_DROITE_DAG)
    axe.set_ylim(-0.08, 1.0)
    axe.axis("off")
    for nom in BOITES_DAG:
        dessiner_boite(axe, nom)
    gris = COULEURS_DAG["ne_pas_prendre_en_compte"][1]
    violet = COULEURS_DAG["tutorat_et_resultat"][1]
    # Profil -> activité, tutorat, décrochage ; activité -> tutorat, décrochage.
    dessiner_fleche(axe, bord_de_boite("profil", "droite"), bord_de_boite("activite", "gauche"))
    dessiner_fleche(axe, bord_de_boite("profil", "bas_gauche"), bord_de_boite("tutorat", "haut_gauche"))
    dessiner_fleche(axe, bord_de_boite("profil", "bas_droite"), bord_de_boite("decrochage", "haut_gauche"))
    dessiner_fleche(axe, bord_de_boite("activite", "bas_gauche"), bord_de_boite("tutorat", "haut_droite"))
    dessiner_fleche(axe, bord_de_boite("activite", "bas_droite"), bord_de_boite("decrochage", "haut_droite"))
    # Effet cherché.
    dessiner_fleche(axe, bord_de_boite("tutorat", "droite"), bord_de_boite("decrochage", "gauche"),
                    couleur=violet, epaisseur=3.5)
    axe.text(0.50, 0.545, "effet cherché", ha="center", va="bottom", fontsize=11, color=violet,
             fontweight="bold")
    # Chemin par le médiateur.
    dessiner_fleche(axe, bord_de_boite("tutorat", "bas"), bord_de_boite("mediateur", "gauche"),
                    couleur=gris, courbure=0.25)
    dessiner_fleche(axe, bord_de_boite("mediateur", "droite"), bord_de_boite("decrochage", "bas"),
                    couleur=gris, courbure=0.25)
    # Facteurs non mesurés -> tutorat et décrochage (contournent le médiateur par les côtés).
    dessiner_fleche(axe, bord_de_boite("non_mesures", "gauche"), bord_de_boite("tutorat", "bas_gauche"),
                    couleur=gris, pointilles=True, courbure=-0.35)
    dessiner_fleche(axe, bord_de_boite("non_mesures", "droite"), bord_de_boite("decrochage", "bas_droite"),
                    couleur=gris, pointilles=True, courbure=0.35)
    # Facteurs non mesurés -> activité des semaines 1 à 8 (D-55, RV02-07) : la flèche passe
    # par un couloir à droite de toutes les boîtes pour n'en traverser aucune.
    depart_x, depart_y = bord_de_boite("non_mesures", "droite")
    arrivee_x, arrivee_y = bord_de_boite("activite", "droite")
    depart_y -= HAUTEUR_BOITE / 4
    trajet = Path([(depart_x, depart_y), (COULOIR_DROIT_DAG, depart_y), (COULOIR_DROIT_DAG, arrivee_y),
                   (arrivee_x, arrivee_y)])
    axe.add_patch(FancyArrowPatch(path=trajet, arrowstyle="-|>", mutation_scale=16, color=gris, linewidth=1.4,
                                  linestyle="--", zorder=4))
    legende = [
        Patch(facecolor=COULEURS_DAG["a_prendre_en_compte"][0], edgecolor=COULEURS_DAG["a_prendre_en_compte"][1],
              label="à prendre en compte (dans le score)"),
        Patch(facecolor=COULEURS_DAG["tutorat_et_resultat"][0], edgecolor=COULEURS_DAG["tutorat_et_resultat"][1],
              label="tutorat et résultat"),
        Patch(facecolor=COULEURS_DAG["ne_pas_prendre_en_compte"][0], edgecolor=gris,
              label="ne pas prendre en compte (médiateur)"),
        Patch(facecolor=COULEURS_DAG["non_mesure"][0], edgecolor=COULEURS_DAG["non_mesure"][1], linestyle="--",
              label="non mesuré (sensibilité : E-value)"),
    ]
    axe.legend(handles=legende, loc="lower center", bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=10,
               frameon=False)
    axe.set_title("Graphe causal (DAG) : tutorat et décrochage, photo de la semaine 8", fontsize=13)
    figure.tight_layout()
    figure.savefig(chemin, dpi=150, bbox_inches="tight")
    plt.close(figure)


# ===========================================================================
# 12. Effet du tutorat : courbes pondérées, RMST, HR, bootstrap (CA-04, D-57, D-61)
# ===========================================================================

# Mesures de l'effet, dans l'ordre du tableau de résultats.
MESURES_EFFET = ["risque_tutores", "risque_non_tutores", "difference_risque", "rapport_risques",
                 "rmst_tutores", "rmst_non_tutores", "difference_rmst", "hr"]
# Erreurs qui font échouer un tirage bootstrap : il est alors remplacé et compté (D-61).
ERREURS_TIRAGE = (ErreurCausal, ConvergenceError, np.linalg.LinAlgError, ValueError, ZeroDivisionError)


def kaplan_meier_pondere(duree, evenement, poids, nom):
    """Kaplan-Meier pondéré d'une équipe (lifelines, poids des étudiants)."""
    kmf = KaplanMeierFitter(label=nom)
    kmf.fit(np.asarray(duree), event_observed=np.asarray(evenement), weights=np.asarray(poids, dtype=float))
    return kmf


def survie_au_temps(kmf, temps):
    """Valeur de la courbe de survie à un temps donné (courbe en escalier)."""
    return float(kmf.survival_function_at_times([temps]).iloc[0])


def ajuster_cox_pondere(duree, evenement, traite, poids, robuste=False):
    """Cox à une seule variable (tutoré à la photo), pondéré, liens d'Efron (D-61, point 3).

    robuste=True donne l'erreur standard « sandwich » (analyse principale, pour
    information). lifelines prévient que des poids non entiers appellent robust=True :
    l'avertissement est masqué, car l'IC officiel vient du bootstrap.
    """
    table = pd.DataFrame({"duree": np.asarray(duree), "evenement": np.asarray(evenement),
                          "tutore_photo": np.asarray(traite), "poids": np.asarray(poids, dtype=float)})
    cph = CoxPHFitter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", StatisticalWarning)
        cph.fit(table, duration_col="duree", event_col="evenement", weights_col="poids", robust=robuste)
    return cph, table


def effet_pondere(duree, evenement, traite, poids, horizon, robuste=False):
    """Effet du tutorat sur une population pondérée (D-57, D-61 point 4).

    Entrées : durée depuis la photo (T − L), événement, équipe (1 = tutoré), poids
    tronqués, horizon H = 30 − L. Pour chaque équipe : Kaplan-Meier pondéré, risque de
    décrochage à 30 semaines = 1 − S(H), RMST = aire sous la courbe jusqu'à H (semaines
    sans décrochage gagnées sur la période). HR : Cox pondéré à une variable.
    Sortie : dictionnaire des mesures de MESURES_EFFET + courbes et modèle.
    """
    duree = np.asarray(duree)
    evenement = np.asarray(evenement)
    traite = np.asarray(traite, dtype=int)
    poids = np.asarray(poids, dtype=float)
    courbes = {}
    for equipe, nom in [(1, "tutores"), (0, "non_tutores")]:
        dans = traite == equipe
        courbes[nom] = kaplan_meier_pondere(duree[dans], evenement[dans], poids[dans], nom)
    risque_t = 1 - survie_au_temps(courbes["tutores"], horizon)
    risque_n = 1 - survie_au_temps(courbes["non_tutores"], horizon)
    rmst_t = float(restricted_mean_survival_time(courbes["tutores"], t=horizon))
    rmst_n = float(restricted_mean_survival_time(courbes["non_tutores"], t=horizon))
    cph, table = ajuster_cox_pondere(duree, evenement, traite, poids, robuste=robuste)
    return {
        "risque_tutores": risque_t,
        "risque_non_tutores": risque_n,
        "difference_risque": risque_t - risque_n,
        "rapport_risques": risque_t / risque_n,
        "rmst_tutores": rmst_t,
        "rmst_non_tutores": rmst_n,
        "difference_rmst": rmst_t - rmst_n,
        "hr": float(np.exp(cph.params_["tutore_photo"])),
        "courbes": courbes,
        "cox": cph,
        "table_cox": table,
    }


def e_value(rapport):
    """E-value d'un rapport de risques (D-61, point 5) : RR < 1 -> 1 / RR ; E = RR + √(RR(RR − 1)).

    C'est la force minimale (en rapport de risques) qu'un facteur caché devrait avoir avec
    le tutorat ET avec le décrochage pour expliquer entièrement l'association observée.
    """
    if rapport < 1:
        rapport = 1 / rapport
    return float(rapport + np.sqrt(rapport * (rapport - 1)))


def e_value_intervalle(borne_basse, borne_haute):
    """E-value de la borne de l'IC la plus proche de 1 ; 1 si l'IC contient 1."""
    if borne_basse <= 1 <= borne_haute:
        return 1.0
    plus_proche = borne_haute if borne_haute < 1 else borne_basse
    return e_value(plus_proche)


def tirage_bootstrap(conception, duree, evenement, indices, horizon):
    """Un tirage (D-61, point 1) : X, matrice d'équilibre, équipe, durée et E pris aux indices.

    Le score est ré-estimé avec la spécification de l'analyse (les carrés restent si la
    retouche a été appliquée ; on ne redécide jamais dans un tirage), puis poids
    stabilisés, troncature, plus grand |SMD| du tirage et effet pondéré (estimations seules).
    """
    X = conception["X"].iloc[indices].reset_index(drop=True)
    matrice = conception["matrice"].iloc[indices].reset_index(drop=True)
    traite = np.asarray(conception["traite"])[indices]
    resultat = score_poids_equilibre(X, traite, matrice)
    effet = effet_pondere(np.asarray(duree)[indices], np.asarray(evenement)[indices], traite, resultat["poids"],
                          horizon)
    ligne = {mesure: effet[mesure] for mesure in MESURES_EFFET}
    ligne["smd_max"] = float(resultat["equilibre"]["smd_apres"].abs().max())
    return ligne


def bootstrap(conception, duree, evenement, horizon, nb_tirages, graine=config.SEED, fonction_tirage=tirage_bootstrap):
    """Bootstrap de l'effet : nb_tirages tirages avec remise des étudiants de la population.

    Un générateur neuf par analyse (graine SEED) ; indices = rng.integers(0, n, size=n).
    Un tirage qui échoue (erreur, score non convergé) est remplacé par le suivant et compté.
    Sortie : (tableau des tirages, nombre d'échecs).
    """
    generateur = np.random.default_rng(graine)
    n = len(duree)
    lignes = []
    echecs = 0
    while len(lignes) < nb_tirages:
        indices = generateur.integers(0, n, size=n)
        try:
            lignes.append(fonction_tirage(conception, duree, evenement, indices, horizon))
        except ERREURS_TIRAGE:
            echecs += 1
            if echecs > nb_tirages:
                raise ErreurCausal(f"Bootstrap : plus de {nb_tirages} tirages en échec")
    tirages = pd.DataFrame(lignes)
    tirages.insert(0, "tirage", np.arange(1, len(tirages) + 1))
    return tirages, echecs


def intervalle(valeurs):
    """IC à 95 % par les percentiles 2,5 et 97,5 (numpy, méthode par défaut)."""
    bas, haut = np.percentile(np.asarray(valeurs, dtype=float), config.QUANTILES_IC)
    return float(bas), float(haut)


def tableau_effet(effet, tirages):
    """Tableau mesure, estimation, borne basse, borne haute (IC bootstrap)."""
    lignes = []
    for mesure in MESURES_EFFET:
        bas, haut = intervalle(tirages[mesure])
        lignes.append({"mesure": mesure, "estimation": effet[mesure], "ic_bas": bas, "ic_haut": haut})
    return pd.DataFrame(lignes)


def analyse_effet(population, periode, semaine, fenetre, duree="T", evenement="E", nb_tirages=None,
                  robuste=False):
    """Conception (chaîne de C10) puis effet pondéré et bootstrap pour une population.

    Durée depuis la photo = duree − semaine ; horizon = N_SEMAINES − semaine.
    Sortie : dictionnaire : conception, effet, tirages, échecs, tableau, horizon.
    """
    population = population.reset_index(drop=True)
    conception = chaine_de_conception(population, periode, fenetre, semaine, duree=duree, evenement=evenement)
    horizon = config.N_SEMAINES - semaine
    durees = (population[duree] - semaine).to_numpy()
    evenements = population[evenement].to_numpy()
    effet = effet_pondere(durees, evenements, conception["traite"], conception["poids"], horizon, robuste=robuste)
    tirages, echecs = bootstrap(conception, durees, evenements, horizon, nb_tirages)
    return {
        "population": population,
        "conception": conception,
        "effet": effet,
        "tirages": tirages,
        "echecs": echecs,
        "tableau": tableau_effet(effet, tirages),
        "horizon": horizon,
        "semaine": semaine,
    }


def courbes_ponderees(effet, semaine, horizon):
    """Survie pondérée des deux équipes, de la semaine de la photo à la semaine 30."""
    durees = np.arange(0, horizon + 1)
    return pd.DataFrame({
        "semaine": semaine + durees,
        "survie_tutores": effet["courbes"]["tutores"].survival_function_at_times(durees).to_numpy(),
        "survie_non_tutores": effet["courbes"]["non_tutores"].survival_function_at_times(durees).to_numpy(),
    })


def schoenfeld_pondere(effet):
    """Test de Schoenfeld (« rank ») du Cox pondéré : indicatif sur un modèle pondéré (D-61)."""
    test = proportional_hazard_test(effet["cox"], effet["table_cox"],
                                    time_transform=config.TRANSFORMATION_SCHOENFELD)
    resume = test.summary
    return pd.DataFrame({"variable": ["tutore_photo"], "statistique": [float(resume["test_statistic"].iloc[0])],
                         "p": [float(resume["p"].iloc[0])]})


def tableau_effet_principal(analyse):
    """Tableau de l'effet principal + IC « sandwich » du HR (pour information) + E-value."""
    tableau = analyse["tableau"].copy()
    resume = analyse["effet"]["cox"].summary.loc["tutore_photo"]
    niveau = f"{100 * (1 - config.ALPHA):.0f}%"
    rr = tableau.set_index("mesure").loc["rapport_risques"]
    lignes_en_plus = pd.DataFrame([
        {"mesure": "hr_ic_sandwich", "estimation": float(resume["exp(coef)"]),
         "ic_bas": float(resume[f"exp(coef) lower {niveau}"]), "ic_haut": float(resume[f"exp(coef) upper {niveau}"])},
        {"mesure": "e_value", "estimation": e_value(rr["estimation"]), "ic_bas": np.nan, "ic_haut": np.nan},
        {"mesure": "e_value_borne_ic", "estimation": e_value_intervalle(rr["ic_bas"], rr["ic_haut"]),
         "ic_bas": np.nan, "ic_haut": np.nan},
    ])
    return pd.concat([tableau, lignes_en_plus], ignore_index=True)


def diagnostic_bootstrap(nom, analyse):
    """Tirages hors critère (|SMD| >= SEUIL_SMD dans le tirage) et tirages en échec."""
    tirages = analyse["tirages"]
    hors = int((tirages["smd_max"] >= config.SEUIL_SMD).sum())
    return {"analyse": nom, "tirages": len(tirages), "echecs": analyse["echecs"], "hors_critere": hors,
            "part_hors_critere": hors / len(tirages)}


def ecrire_resultat(df, nom_fichier):
    """Écrit un résultat en CSV dans DOSSIER_RESULTATS (UTF-8, LF, 8 chiffres significatifs)."""
    config.DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = config.DOSSIER_RESULTATS / nom_fichier
    df.to_csv(chemin, sep=config.SEPARATEUR_PROCESSED, index=False, encoding=config.ENCODAGE,
              lineterminator="\n", float_format=config.FORMAT_NOMBRES_RESULTATS)
    return chemin


def resultats_principaux(base, periode):
    """Analyse principale (photo de la semaine 8, fenêtre 1 à 8, 500 tirages) -> tables à écrire."""
    semaine = config.SEMAINE_LANDMARK
    population = population_photo(base, semaine)
    analyse = analyse_effet(population, periode, semaine, (1, semaine), nb_tirages=config.NB_TIRAGES_PRINCIPAL,
                            robuste=True)
    return analyse, {
        "ca_effet_principal.csv": tableau_effet_principal(analyse),
        "ca_tirages_principal.csv": analyse["tirages"],
        "ca_courbes_ponderees.csv": courbes_ponderees(analyse["effet"], semaine, analyse["horizon"]),
        "ca_schoenfeld_principal.csv": schoenfeld_pondere(analyse["effet"]),
    }


def lancer():
    """Étape causale de run_all.py : effet du tutorat et sensibilité, résultats enregistrés."""
    debut = time.perf_counter()
    base, periode = eda.lire_bases()
    analyse, fichiers = resultats_principaux(base, periode)
    fichiers["ca_diagnostic_bootstrap.csv"] = pd.DataFrame([diagnostic_bootstrap("principale", analyse)])
    for nom_fichier, table in fichiers.items():
        ecrire_resultat(table, nom_fichier)
    duree = time.perf_counter() - debut
    print(f"Analyse causale (CA-04) : {len(fichiers)} fichiers écrits dans "
          f"{config.DOSSIER_RESULTATS.relative_to(config.RACINE)} en {duree:.0f} s.")
    return fichiers
