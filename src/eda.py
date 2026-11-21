"""Analyse exploratoire : description des étudiants, de la censure, des durées et de l'activité.

Rôle du module : calculer les tableaux descriptifs du notebook 02_eda à partir de
base_survie.csv et base_periode_personne.csv. Description seulement : aucun modèle,
aucun test statistique, et aucune comparaison du décrochage entre groupes (avec la
censure, un taux brut par groupe serait biaisé ; ces comparaisons viendront en SV-01
avec Kaplan-Meier). La seule mesure de décrochage est le taux hebdomadaire global,
qui tient compte de la censure.

Tâche couverte : DA-08.
"""

import pandas as pd

from src import config


# ===========================================================================
# 1. Lecture
# ===========================================================================

def lire_bases():
    """Lit base_survie.csv et base_periode_personne.csv (produits par le pipeline).

    Sortie : (base, periode). Le notebook ne relance pas le pipeline.
    """
    base = pd.read_csv(config.FICHIER_BASE_SURVIE, sep=config.SEPARATEUR_PROCESSED,
                       dtype={"semaine_debut_tutorat": "Int64", "nb_seances": "Int64", "age": "Int64"},
                       encoding=config.ENCODAGE)
    periode = pd.read_csv(config.FICHIER_PERIODE_PERSONNE, sep=config.SEPARATEUR_PROCESSED,
                          dtype={"tutorat_commence": "Int64"}, encoding=config.ENCODAGE)
    return base, periode


# ===========================================================================
# 2. Profil des étudiants
# ===========================================================================

def est_numerique(serie):
    """Vrai si la colonne est numérique (résumée par moyenne et écart-type)."""
    return pd.api.types.is_numeric_dtype(serie)


def profil_variable(valeurs, variable, cohorte):
    """Lignes du profil d'une variable pour une cohorte.

    Variable numérique : une ligne (effectif renseigné, moyenne et écart-type des valeurs
    renseignées).
    Variable qualitative : une ligne par modalité, plus une ligne config.MODALITE_MANQUANTE s'il
    manque des valeurs ; les % sont calculés sur tous les étudiants de la cohorte, pour
    que les effectifs d'une variable fassent exactement la taille de la cohorte.
    Le nombre de manquants est répété sur chaque ligne.
    """
    manquants = int(valeurs.isna().sum())
    connues = valeurs.dropna()
    if est_numerique(valeurs):
        return [{"variable": variable, "cohorte": cohorte, "modalite": "moyenne (écart-type)",
                 "effectif": len(connues), "pourcentage": pd.NA,
                 "moyenne": float(connues.mean()), "ecart_type": float(connues.std()),
                 "manquants": manquants}]
    effectifs = connues.value_counts().sort_index()
    if manquants > 0:
        effectifs[config.MODALITE_MANQUANTE] = manquants
    lignes = []
    for modalite, effectif in effectifs.items():
        lignes.append({"variable": variable, "cohorte": cohorte, "modalite": modalite,
                       "effectif": int(effectif), "pourcentage": 100 * effectif / len(valeurs),
                       "moyenne": pd.NA, "ecart_type": pd.NA, "manquants": manquants})
    return lignes


def profil_par_cohorte(base):
    """Profil des covariables de la rentrée (D-43, sauf cohorte), cohorte par cohorte.

    Entrée : base_survie (ou toute table avec cohorte et les COVARIABLES_RENTREE).
    Sortie : DataFrame long : variable, cohorte, modalite, effectif, pourcentage,
    moyenne, ecart_type, manquants.
    """
    variables = [v for v in config.COVARIABLES_RENTREE if v != "cohorte"]
    lignes = []
    for cohorte, groupe in base.groupby("cohorte"):
        for variable in variables:
            lignes.extend(profil_variable(groupe[variable], variable, cohorte))
    return pd.DataFrame(lignes)


def manquants_covariables(base):
    """Nombre et % de valeurs manquantes de chaque covariable de la rentrée."""
    manquants = base[config.COVARIABLES_RENTREE].isna().sum()
    return pd.DataFrame({"manquants": manquants, "pourcentage": 100 * manquants / len(base)})


# ===========================================================================
# 3. Décrochage et censure
# ===========================================================================

def repartition_evenements(base):
    """Répartition des types d'événement, de E et de la censure.

    Sortie : (par_type, synthese) ; par_type : effectif, %, E de chaque type_evenement ;
    synthese : effectif et % de E = 1 (décrochage) et E = 0 (censure).
    """
    par_type = base["type_evenement"].value_counts().rename("effectif").to_frame()
    par_type["pourcentage"] = 100 * par_type["effectif"] / len(base)
    par_type["E"] = [1 if t in config.TYPES_AVEC_EVENEMENT else 0 for t in par_type.index]
    nb_decrochages = int((base["E"] == 1).sum())
    nb_censures = int((base["E"] == 0).sum())
    synthese = pd.DataFrame({"effectif": [nb_decrochages, nb_censures]},
                            index=["E = 1 (décrochage)", "E = 0 (censure)"])
    synthese["pourcentage"] = 100 * synthese["effectif"] / len(base)
    return par_type, synthese


def taux_hebdomadaire(base):
    """Taux de décrochage de chaque semaine parmi les étudiants encore suivis.

    Pour la semaine s : suivis = étudiants encore suivis au début de la semaine (T >= s) ;
    decrochages = étudiants dont le décrochage tombe en semaine s (T = s et E = 1) ;
    taux = decrochages / suivis. Un étudiant censuré compte parmi les suivis jusqu'à sa
    semaine T, puis sort du calcul : la censure est ainsi prise en compte.
    """
    lignes = []
    for semaine in range(1, config.N_SEMAINES + 1):
        suivis = int((base["T"] >= semaine).sum())
        decrochages = int(((base["T"] == semaine) & (base["E"] == 1)).sum())
        taux = decrochages / suivis if suivis > 0 else pd.NA
        lignes.append({"semaine": semaine, "suivis": suivis, "decrochages": decrochages, "taux": taux})
    return pd.DataFrame(lignes)


# ===========================================================================
# 4. Activité
# ===========================================================================

def activite_par_semaine(periode):
    """Activité moyenne des étudiants encore suivis, semaine par semaine.

    Entrée : base_periode_personne (une ligne par étudiant et par semaine 1 … T).
    Sortie : semaine, suivis (lignes de la semaine), connexions_moyennes (valeurs
    renseignées), pct_inactives (% des lignes de la semaine à l'état « inactif »).
    """
    groupes = periode.groupby("semaine")
    resultat = pd.DataFrame({
        "suivis": groupes.size(),
        "connexions_moyennes": groupes["nb_connexions_lms"].mean(),
        "pct_inactives": 100 * groupes["etat_activite"].apply(lambda etats: (etats == config.ETAT_INACTIF).mean()),
    })
    return resultat.reset_index()


# ===========================================================================
# 5. Tutorat
# ===========================================================================

def debut_tutorat(base):
    """Moment d'entrée en tutorat, motifs et types de tuteur, SANS donnée de décrochage.

    Entrée : base avec statut_tutorat, semaine_debut_tutorat, motif_orientation,
    type_tuteur (T et E ne sont pas utilisés).
    Sortie : dictionnaire : distribution (effectif par semaine de début connue),
    quartiles, nb_connues, nb_au_plus_tard_landmark et part (%) des tutorats commencés au
    plus tard à la semaine config.SEMAINE_REPERE_TUTORAT, motifs, types_tuteur.
    """
    tutorats = base[base["statut_tutorat"] != config.STATUT_NON_TUTORE]
    semaines = tutorats["semaine_debut_tutorat"].dropna().astype(int)
    au_plus_tard = int((semaines <= config.SEMAINE_REPERE_TUTORAT).sum())
    return {
        "nb_tutorats": len(tutorats),
        "nb_connues": len(semaines),
        "distribution": semaines.value_counts().sort_index().rename("effectif"),
        "quartiles": semaines.quantile([0.25, 0.5, 0.75]),
        "nb_au_plus_tard_repere": au_plus_tard,
        "part_au_plus_tard_repere": 100 * au_plus_tard / len(semaines) if len(semaines) else pd.NA,
        "motifs": tutorats["motif_orientation"].value_counts(),
        "types_tuteur": tutorats["type_tuteur"].value_counts(),
    }
