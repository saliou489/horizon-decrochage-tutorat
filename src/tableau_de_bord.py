"""Logique du tableau de bord (app/app.py), sans Streamlit : testable avec pytest.

Rôle du module : relire les résultats de run_all.py et le cache des fiches, puis préparer
ce que le tableau de bord affiche : la table des étudiants à risque d'une semaine L, la
courbe de survie d'un étudiant, son profil (sans genre ni région), son activité récente,
sa fiche LLM et le résumé de l'effet du tutorat. Aucun modèle n'est recalculé et l'API du
LLM n'est jamais appelée (D-68) : les fonctions de src/llm.py sont seulement réutilisées,
pour que les facteurs soient calculés exactement comme dans les fiches (D-66).

Tâches couvertes : DB-01.
"""

import pandas as pd

from src import config, eda, llm

# Fichiers de data/processed/resultats/ relus par le tableau de bord (clé -> nom du fichier).
FICHIERS_RESULTATS = {
    "predictions": "ml_predictions_2025.csv",
    "scores_hebdomadaires": "ml_scores_hebdomadaires_2025.csv",
    "hr": "ml_hr_cox_2024.csv",
    "mesures": "ml_mesures_rentree.csv",
    "effet": "ca_effet_principal.csv",
    "courbes_ponderees": "ca_courbes_ponderees.csv",
    "sensibilite": "ca_sensibilite.csv",
}
COLONNES_TABLE = ["id_etudiant", "risque_cox_pct", "risque_semaine_suivante_pct", "facteurs", "tutorat", "fiche"]
# Colonnes de la table des variantes (CA-05) gardées pour l'affichage.
COLONNES_VARIANTES = ["analyse", "etudiants", "tutores", "smd_max", "critere_atteint", "tirages",
                      "difference_risque", "difference_risque_ic_bas", "difference_risque_ic_haut",
                      "hr", "hr_ic_bas", "hr_ic_haut"]


# ===========================================================================
# 1. Chargement
# ===========================================================================

def charger_donnees():
    """Toutes les tables utiles au tableau de bord, lues une fois.

    Sortie : dictionnaire avec "base" (base_survie), "periode" (table période-personne),
    une clé par fichier de FICHIERS_RESULTATS, et "fiches" (liste vide sans cache).
    """
    base, periode = eda.lire_bases()
    donnees = {"base": base, "periode": periode}
    for cle, nom in FICHIERS_RESULTATS.items():
        donnees[cle] = llm.lire_resultat(nom)
    fiches = llm.lire_json(config.FICHIER_FICHES_LLM) if config.FICHIER_FICHES_LLM.exists() else []
    donnees["fiches"] = fiches
    return donnees


# ===========================================================================
# 2. Table des étudiants à risque
# ===========================================================================

def texte_facteurs(facteurs):
    """Texte court des facteurs d'une fiche : « âge ×2,1 ; emploi ×1,6 »."""
    morceaux = []
    for facteur in facteurs:
        variable = llm.VARIABLE_DU_LIBELLE[facteur["facteur"]]
        libelle = config.LIBELLES_COURTS_FACTEURS[variable]
        morceaux.append(f"{libelle} ×{llm.nombre_fr(facteur['multiplicateur'])}")
    return " ; ".join(morceaux)


def texte_tutorat(statut):
    """Statut de tutorat lisible (« en cours depuis la semaine 5 », « aucun »…)."""
    if statut["statut"] == "en cours":
        return f"en cours depuis la semaine {statut['semaine_debut']}"
    return statut["statut"]


def texte_tutorat_court(statut):
    """Statut de tutorat en un ou deux mots (« en cours », « aucun », « signalé ») : une
    métrique Streamlit coupe une valeur longue ; le texte complet va dans une légende."""
    if statut["statut"] == "signalé, semaine de début inconnue":
        return "signalé"
    return statut["statut"]


def statut_tutorat_etudiant(donnees, id_etudiant, semaine):
    """Statut de tutorat de l'étudiant connu à la semaine `semaine` (llm.statut_tutorat)."""
    base = donnees["base"]
    return llm.statut_tutorat(base[base[config.COLONNE_ID] == id_etudiant].iloc[0], semaine)


def facteurs_de_la_semaine(base, population, hr):
    """Facteurs de chaque étudiant de `population`, calculés comme les fiches (contributions
    du Cox, références de cette population, D-66), dans l'ordre des lignes.

    Sortie : une liste par étudiant, de dictionnaires (facteur, valeur_etudiant,
    reference_promotion, multiplicateur), comme dans les entrées des fiches.
    """
    apports = llm.contributions(llm.table_codee_population(base, population), hr)
    references = llm.references_promotion(population)
    return [llm.facteurs_principaux(apports.iloc[i], population.iloc[i], references)
            for i in range(len(population))]


def facteurs_par_etudiant(donnees, semaine):
    """Dictionnaire id_etudiant -> facteurs détaillés, pour la population de `semaine`."""
    population = llm.population_suivie(donnees["base"], semaine)
    facteurs = facteurs_de_la_semaine(donnees["base"], population, donnees["hr"])
    return dict(zip(population[config.COLONNE_ID], facteurs))


def risques_semaine_suivante(scores, ids, semaine):
    """Risque hebdomadaire du gradient boosting à la semaine `semaine + 1` (activité connue
    jusqu'à la semaine choisie), dans l'ordre de `ids` ; NaN si absent."""
    lignes = scores[scores["semaine"] == semaine + 1].set_index(config.COLONNE_ID)["risque_hebdomadaire"]
    return lignes.reindex(list(ids)).to_numpy()


def statuts_fiches(fiches, semaine):
    """Statut de la fiche de chaque étudiant (dictionnaire id -> statut), seulement pour la
    semaine des fiches ; dictionnaire vide sinon."""
    if semaine != config.SEMAINE_FICHES:
        return {}
    return {fiche["id_etudiant"]: fiche["statut"] for fiche in fiches}


def table_a_risque(donnees, semaine):
    """Une ligne par étudiant de 2025 encore suivi après `semaine` (T > semaine).

    Colonnes : id_etudiant, risque_cox_pct (1 − S(30) / S(semaine), en %),
    risque_semaine_suivante_pct (gradient boosting, en %), facteurs (texte), tutorat
    (texte), fiche (statut de la fiche LLM à la semaine des fiches, sinon vide).
    Tri : risque Cox décroissant, puis identifiant. Les nombres restent numériques.
    """
    base = donnees["base"]
    population = llm.population_suivie(base, semaine)
    ids = population[config.COLONNE_ID].tolist()
    fiches = statuts_fiches(donnees["fiches"], semaine)
    table = pd.DataFrame({
        "id_etudiant": ids,
        "risque_cox_pct": 100 * llm.risques_conditionnels(donnees["predictions"], ids, semaine),
        "risque_semaine_suivante_pct": 100 * risques_semaine_suivante(donnees["scores_hebdomadaires"], ids, semaine),
        "facteurs": [texte_facteurs(f) for f in facteurs_de_la_semaine(base, population, donnees["hr"])],
        "tutorat": [texte_tutorat(llm.statut_tutorat(ligne, semaine)) for _, ligne in population.iterrows()],
        "fiche": [fiches.get(i, "") for i in ids],
    })
    table = table.sort_values(["risque_cox_pct", "id_etudiant"], ascending=[False, True])
    return table.reset_index(drop=True)[COLONNES_TABLE]


# ===========================================================================
# 3. Un étudiant
# ===========================================================================

def courbe_individuelle(donnees, id_etudiant):
    """Semaines 1 à 30 : survie Cox de l'étudiant et moyenne des courbes Cox de la cohorte 2025.

    Sortie : DataFrame (semaine, survie_etudiant, survie_moyenne_cohorte).
    """
    predictions = donnees["predictions"]
    moyenne = predictions.groupby("semaine")["survie_cox"].mean()
    etudiant = predictions[predictions[config.COLONNE_ID] == id_etudiant].set_index("semaine")["survie_cox"]
    semaines = list(range(1, config.N_SEMAINES + 1))
    return pd.DataFrame({"semaine": semaines, "survie_etudiant": etudiant.reindex(semaines).to_numpy(),
                         "survie_moyenne_cohorte": moyenne.reindex(semaines).to_numpy()})


def profil(donnees, id_etudiant):
    """Profil de rentrée de l'étudiant (COLONNES_PROFIL_TABLEAU) : ni genre ni région (D-68)."""
    base = donnees["base"]
    ligne = base[base[config.COLONNE_ID] == id_etudiant].iloc[0]
    return {colonne: ligne[colonne] for colonne in config.COLONNES_PROFIL_TABLEAU}


def semaines_recentes(semaine):
    """Les deux dernières semaines connues à la semaine `semaine` (la semaine 1 seule au début)."""
    return [1] if semaine == 1 else [semaine - 1, semaine]


def activite_semaines(donnees, id_etudiant, semaine):
    """Activité moyenne de l'étudiant et de la population de la semaine, sur semaines_recentes.

    Sortie : (semaines, activité de l'étudiant, activité de la population) ; chaque activité
    est un dictionnaire des champs de llm.CHAMPS_ACTIVITE (None si non renseigné).
    """
    semaines = semaines_recentes(semaine)
    ids = llm.population_suivie(donnees["base"], semaine)[config.COLONNE_ID].tolist()
    par_etudiant, promotion = llm.activite_recente(donnees["periode"], ids, semaines)
    return semaines, par_etudiant.loc[id_etudiant].to_dict(), promotion


def fiche_llm(donnees, id_etudiant):
    """La fiche LLM de l'étudiant dans le cache, ou None s'il n'en a pas."""
    for fiche in donnees["fiches"]:
        if fiche["id_etudiant"] == id_etudiant:
            return fiche
    return None


# ===========================================================================
# 4. Effet du tutorat
# ===========================================================================

def resume_effet(donnees):
    """Mesures de l'effet principal et table des variantes, prêtes à afficher.

    Sortie : dictionnaire avec "mesures" (mesure -> (estimation, ic_bas, ic_haut)),
    "variantes" (DataFrame de COLONNES_VARIANTES, sans la ligne principale) et
    "meme_sens" (vrai si chaque variante a une différence de risque du même signe que
    l'analyse principale).
    """
    effet = donnees["effet"].set_index("mesure")
    mesures = {mesure: (effet.loc[mesure, "estimation"], effet.loc[mesure, "ic_bas"], effet.loc[mesure, "ic_haut"])
               for mesure in effet.index}
    sensibilite = donnees["sensibilite"]
    variantes = sensibilite[sensibilite["analyse"] != "analyse principale"][COLONNES_VARIANTES].reset_index(drop=True)
    signe_principal = mesures["difference_risque"][0] < 0
    meme_sens = bool(((variantes["difference_risque"] < 0) == signe_principal).all())
    return {"mesures": mesures, "variantes": variantes, "meme_sens": meme_sens}
