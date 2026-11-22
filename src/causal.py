"""Analyse causale : le tutorat fait-il baisser le décrochage ? Phase de conception.

Rôle du module : préparer l'estimation de l'effet du tutorat sans jamais regarder le
décrochage par équipe (D-59) : moment d'entrée en tutorat, « photo » de la semaine 8
contre le temps immortel (D-53, D-54), covariables et score de propension (D-55, D-56),
poids stabilisés, support commun et équilibre des deux équipes, figure du DAG.
Les fonctions de ce module ne calculent rien sur T, E ou la survie selon le tutorat.

Tâches couvertes : CA-01, CA-02, CA-03 (CA-04 et CA-05 viendront s'y ajouter).
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from scipy.stats import rankdata

from src import config, survie


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


def covariables_du_score(population, periode, fenetre, duree="T", evenement="E"):
    """Covariables du score : profil codé comme le Cox + activité moyenne (D-55).

    Profil : survie.preparer_donnees_cox (mêmes références, même règle des manquants,
    médianes calculées sur la population reçue), sans T ni E. Activité : moyenne des 4
    variables sur la fenêtre (première, dernière) ; manquante -> médiane de la
    population reçue.
    Sortie : (X, médianes utilisées pour toutes les variables numériques).
    """
    donnees, medianes = survie.preparer_donnees_cox(population, duree=duree, evenement=evenement)
    X = donnees.drop(columns=["T", "E"]).astype(float)
    activite = activite_moyenne(periode, population[config.COLONNE_ID], fenetre[0], fenetre[1])
    medianes = dict(medianes)
    for variable in config.VARIABLES_ACTIVITE_PROPENSION:
        colonne = f"{variable}{SUFFIXE_MOYENNE}"
        medianes[colonne] = float(activite[colonne].median())
        X[colonne] = activite[colonne].fillna(medianes[colonne]).to_numpy()
    verifier_colonnes_autorisees(X.columns)
    return X, medianes


def colonnes_numeriques_du_score():
    """Variables numériques du score : âge, note du bac, log2 distance, 4 moyennes d'activité."""
    return list(config.VARIABLES_COX_NUMERIQUES) + [
        f"{v}{SUFFIXE_MOYENNE}" for v in config.VARIABLES_ACTIVITE_PROPENSION]


def ajouter_carres(X):
    """Retouche fixée d'avance (D-56) : ajoute le carré de chaque variable numérique."""
    avec_carres = X.copy()
    for colonne in colonnes_numeriques_du_score():
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

def matrice_equilibre(population, X):
    """Variables dont on vérifie l'équilibre.

    Numériques : âge, note du bac, log2 distance, 4 moyennes d'activité (valeurs du
    score, manquants remplacés). Qualitatives : une colonne 0/1 par modalité, références
    et « (manquant) » comprises (une référence peut être déséquilibrée elle aussi).
    """
    matrice = X[colonnes_numeriques_du_score()].copy()
    variables = survie.variables_du_cox(population.reset_index(drop=True))
    for variable in config.VARIABLES_COX_QUALITATIVES:
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


def chaine_de_conception(population, periode, fenetre, duree="T", evenement="E"):
    """Enchaîne covariables, score, support, poids et équilibre pour une population.

    Entrées : population d'une photo (population_photo, ou un tirage bootstrap de
    celle-ci) ; base_periode_personne ; fenêtre d'activité (première, dernière) ;
    colonnes de durée et d'événement (variantes de seuil). Si une ligne reste à
    |SMD| >= SEUIL_SMD après pondération, une seule retouche fixée d'avance (D-56) :
    carrés des variables numériques ajoutés au score ; le résultat final est rapporté
    tel quel. Sortie : dictionnaire (voir score_poids_equilibre) + X, médianes,
    tableau d'équilibre de la première tentative, retouche (booléen).
    """
    traite = population["tutore_photo"].to_numpy()
    X, medianes = covariables_du_score(population, periode, fenetre, duree=duree, evenement=evenement)
    matrice = matrice_equilibre(population, X)
    resultat = score_poids_equilibre(X, traite, matrice)
    equilibre_initial = resultat["equilibre"]
    retouche = not equilibre_initial["equilibre"].all()
    if retouche:
        X = ajouter_carres(X)
        resultat = score_poids_equilibre(X, traite, matrice)
    resultat.update({
        "X": X,
        "medianes": medianes,
        "traite": traite,
        "equilibre_initial": equilibre_initial,
        "retouche": retouche,
        "critere_atteint": bool(resultat["equilibre"]["equilibre"].all()),
    })
    return resultat


# ===========================================================================
# 10. Figure du DAG (CA-01, D-55)
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
    axe.set_xlim(0, 1)
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
