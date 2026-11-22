"""Tests des modèles prédictifs de survie (Cox, gradient boosting à temps discret).

Rôle du module : tester src/ml_survie.py (survie à partir des risques, censure, Brier,
calibration, alignement des colonnes, validation temporelle, liste positive,
permutation) sur de petits exemples calculés à la main ou inventés.

Tâches couvertes : SV-03, SV-04.
"""

import numpy as np
import pandas as pd
import pytest

from src import config, ml_survie, survie


# ---------------------------------------------------------------------------
# Courbes de survie, censure, Brier, calibration
# ---------------------------------------------------------------------------

def test_survie_depuis_risques():
    survies = ml_survie.survie_depuis_risques([[0.1, 0.2]])
    assert survies[0] == pytest.approx([0.9, 0.72])


def test_survie_de_la_censure_avec_egalites():
    # Semaine 1 : 1 décrochage passe avant la censure -> 3 à risque, 1 censure -> 2/3.
    censure = ml_survie.survie_de_la_censure([1, 1, 2, 3], [1, 0, 0, 1], 3)
    assert censure[1] == pytest.approx(2 / 3)
    assert censure[2] == pytest.approx(1 / 3)
    assert censure[3] == pytest.approx(1 / 3)  # personne à risque après le décrochage : G inchangé


def test_brier_exemple_calcule_a_la_main():
    censure = ml_survie.survie_de_la_censure([1, 2, 2, 3, 4], [1, 0, 1, 0, 1], 4)
    survies = np.array([[0.8, 0.6], [0.9, 0.8], [0.95, 0.85], [0.7, 0.5]])
    brier = ml_survie.brier_par_semaine([1, 2, 3, 3], [1, 0, 1, 0], survies, censure, [1, 2])
    assert brier[1] == pytest.approx(0.185625)
    assert brier[2] == pytest.approx(0.1921875)
    assert ml_survie.brier_integre(brier) == pytest.approx(0.18890625)


def test_calibration_groupes_de_meme_taille():
    generateur = np.random.default_rng(config.SEED)
    risques = generateur.uniform(0, 1, 25)
    table, _ = ml_survie.calibration(risques, np.full(25, 30), np.zeros(25, dtype=int))
    assert len(table) == config.NB_GROUPES_CALIBRATION
    assert set(table["effectif"]) == {2, 3} and table["effectif"].sum() == 25
    assert table["risque_predit"].is_monotonic_increasing


def test_calibration_risque_observe_par_kaplan_meier():
    # Groupe 1 (risques 0,1 et 0,2) : aucun décrochage avant 4 -> observé 0.
    # Groupe 2 (0,8 et 0,9) : un décrochage en semaine 3 sur 2 étudiants -> observé 0,5.
    table, ecart = ml_survie.calibration([0.1, 0.2, 0.8, 0.9], [5, 5, 3, 10], [0, 0, 1, 0],
                                         semaine=4, nb_groupes=2)
    assert list(table["risque_observe"]) == pytest.approx([0.0, 0.5])
    assert list(table["risque_predit"]) == pytest.approx([0.15, 0.85])
    assert ecart == pytest.approx((0.15 + 0.35) / 2)


# ---------------------------------------------------------------------------
# Colonnes : alignement, liste positive
# ---------------------------------------------------------------------------

def test_alignement_des_colonnes():
    colonnes = ["age", "filiere=Droit", "filiere=Gestion"]
    test = pd.DataFrame({"age": [20.0], "filiere=Droit": [1]})
    aligne = ml_survie.aligner_colonnes(test, colonnes)
    assert list(aligne.columns) == colonnes
    assert aligne.loc[0, "filiere=Gestion"] == 0  # modalité absente du test -> 0
    with pytest.raises(ml_survie.ErreurMLSurvie):
        ml_survie.aligner_colonnes(test.assign(**{"filiere=Médecine": [0]}), colonnes)


def test_liste_positive():
    for colonne in ["tutore", "nb_seances", "T", "E", "nb_connexions_lms", "etat_activite", "cohorte=2025",
                    "semaine_debut_tutorat", "mention_bac"]:
        with pytest.raises(ml_survie.ErreurMLSurvie):
            ml_survie.verifier_colonnes(["age", colonne], hebdomadaire=True)
    # Activité de la semaine précédente : seulement pour le modèle hebdomadaire.
    ml_survie.verifier_colonnes(["semaine", "age", "absences_prec"], hebdomadaire=True)
    with pytest.raises(ml_survie.ErreurMLSurvie):
        ml_survie.verifier_colonnes(["semaine", "age", "absences_prec"])


# ---------------------------------------------------------------------------
# Données inventées : deux cohortes, activité semaine par semaine
# ---------------------------------------------------------------------------

def donnees_inventees(n=400):
    """n étudiants inventés (moitié 2024, moitié 2025) et leurs lignes semaine par semaine."""
    generateur = np.random.default_rng(config.SEED)
    filieres = config.MODALITES[("etudiants", "filiere")]
    T = generateur.integers(1, config.N_SEMAINES + 1, n)
    base = pd.DataFrame({
        "id_etudiant": [f"HZ{i:05d}" for i in range(n)],
        "cohorte": [config.COHORTE_ENTRAINEMENT] * (n // 2) + [config.COHORTE_TEST] * (n // 2),
        "genre": generateur.choice(["F", "M"], n),
        "age": pd.array(generateur.integers(18, 25, n), dtype="Int64"),
        "boursier": generateur.choice(["Oui", "Non"], n),
        "filiere": [filieres[i % len(filieres)] for i in range(n)],
        "note_bac": generateur.uniform(10, 18, n).round(2),
        "region_origine": generateur.choice(["Dakar", "Thiès"], n).astype(object),
        "distance_campus_km": generateur.uniform(1, 100, n).round(1),
        "emploi_parallele": generateur.choice(["Oui", "Non"], n).astype(object),
        "T": T,
        "E": np.where(T < config.N_SEMAINES, generateur.integers(0, 2, n), 0),
    })
    # Âges différents selon la cohorte : les médianes de 2024 et de 2025 diffèrent.
    base.loc[base["cohorte"] == config.COHORTE_TEST, "age"] += 3
    base.loc[[0, n // 2], "age"] = pd.NA
    lignes = []
    for _, etudiant in base.iterrows():
        etat_prec = None
        for semaine in range(1, etudiant["T"] + 1):
            etat = generateur.choice(list(config.ETATS_ACTIVITE))
            lignes.append({
                "id_etudiant": etudiant["id_etudiant"], "semaine": semaine,
                "evenement": int(semaine == etudiant["T"] and etudiant["E"] == 1),
                "nb_connexions_lms": float(generateur.integers(0, 10)), "etat_activite": etat,
                "nb_connexions_lms_prec": np.nan if semaine == 1 else float(generateur.integers(0, 10)),
                "devoirs_rendus_prec": np.nan if semaine == 1 else float(generateur.integers(0, 3)),
                "note_moyenne_prec": np.nan if semaine == 1 else float(generateur.uniform(5, 18)),
                "absences_prec": np.nan if semaine == 1 else float(generateur.integers(0, 4)),
                "etat_activite_prec": etat_prec,
                "tutorat_commence": 0,
            })
            etat_prec = etat
    return base, pd.DataFrame(lignes)


@pytest.fixture(scope="module")
def inventees():
    return donnees_inventees()


def test_separation_temporelle(inventees):
    base, periode = inventees
    entrainement, test = ml_survie.separer_cohortes(base)
    assert (entrainement["cohorte"] == config.COHORTE_ENTRAINEMENT).all()
    assert (test["cohorte"] == config.COHORTE_TEST).all()
    rentree = ml_survie.variables_rentree(entrainement, test)
    # Aucune ligne d'entraînement de 2025.
    assert set(rentree["entrainement"]["id_etudiant"]) == set(entrainement["id_etudiant"])
    lignes, _ = ml_survie.lignes_semaines(periode, rentree["entrainement"], rentree["colonnes"], hebdomadaire=True)
    assert set(lignes["id_etudiant"]) <= set(entrainement["id_etudiant"])
    # Les médianes de 2024 servent à remplacer l'âge manquant de l'étudiant de 2025.
    mediane_2024 = entrainement["age"].dropna().astype(float).median()
    assert rentree["medianes"]["age"] == pytest.approx(mediane_2024)
    assert mediane_2024 != pytest.approx(test["age"].dropna().astype(float).median())
    assert rentree["test"].loc[0, "age"] == pytest.approx(mediane_2024)


def test_preparer_donnees_cox_variables_exclues(inventees):
    base, _ = inventees
    _, test = ml_survie.separer_cohortes(base)
    # Une seule cohorte (2025) : sans exclusion, la référence « 2024 » manque.
    with pytest.raises(survie.ErreurSurvie):
        survie.preparer_donnees_cox(test)
    donnees, _ = survie.preparer_donnees_cox(test, variables_exclues=(config.VARIABLE_COHORTE,))
    assert not any(c.startswith(config.VARIABLE_COHORTE) for c in donnees.columns)
    # Sans exclusion (deux cohortes), le résultat est le même qu'avant le nouveau paramètre.
    defaut, medianes_defaut = survie.preparer_donnees_cox(base)
    explicite, medianes_explicite = survie.preparer_donnees_cox(base, variables_exclues=())
    assert defaut.equals(explicite) and medianes_defaut == medianes_explicite
    assert f"{config.VARIABLE_COHORTE}={config.COHORTE_TEST}" in defaut.columns


def test_lignes_semaines_liste_positive(inventees):
    base, periode = inventees
    entrainement, test = ml_survie.separer_cohortes(base)
    rentree = ml_survie.variables_rentree(entrainement, test)
    for hebdomadaire in (False, True):
        _, colonnes = ml_survie.lignes_semaines(periode, rentree["entrainement"], rentree["colonnes"],
                                                hebdomadaire=hebdomadaire)
        for colonne in colonnes:
            assert colonne not in ("T", "E", "evenement", "nb_connexions_lms", "etat_activite", "tutorat_commence")
            assert "tutor" not in colonne and "cohorte" not in colonne


def test_importance_meme_graine_memes_resultats(inventees):
    base, periode = inventees
    entrainement, test = ml_survie.separer_cohortes(base)
    rentree = ml_survie.variables_rentree(entrainement, test)
    lignes_2024, colonnes = ml_survie.lignes_semaines(periode, rentree["entrainement"], rentree["colonnes"],
                                                      hebdomadaire=True)
    lignes_2025, _ = ml_survie.lignes_semaines(periode, rentree["test"], rentree["colonnes"], hebdomadaire=True)
    modele = ml_survie.entrainer_gradient_boosting(lignes_2024, colonnes)
    premiere = ml_survie.importance_hebdomadaire(modele, lignes_2025, colonnes)
    seconde = ml_survie.importance_hebdomadaire(modele, lignes_2025, colonnes)
    pd.testing.assert_frame_equal(premiere, seconde)
    assert len(premiere) == len(ml_survie.VARIABLES_HEBDOMADAIRES_PERMUTATION)
