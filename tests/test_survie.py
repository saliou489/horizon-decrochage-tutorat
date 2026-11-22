"""Tests de l'analyse de survie (Kaplan-Meier, semaines critiques, Cox).

Rôle du module : tester src/survie.py sur de petits jeux d'étudiants inventés.

Tâches couvertes : SV-01, SV-02.
"""

import numpy as np
import pandas as pd
import pytest

from src import config, survie


# ---------------------------------------------------------------------------
# Kaplan-Meier et semaines critiques (SV-01)
# ---------------------------------------------------------------------------

def dix_etudiants():
    """1 décrochage en semaine 1, 1 censuré en semaine 2, 2 décrochages en semaine 3,
    6 censurés en semaine 4."""
    return pd.DataFrame({"T": [1, 2, 3, 3] + [4] * 6, "E": [1, 0, 1, 1] + [0] * 6})


def test_kaplan_meier_exemple_de_dix_etudiants():
    kmf = survie.ajuster_kaplan_meier(dix_etudiants()["T"], dix_etudiants()["E"])
    survies = survie.survie_aux_semaines(kmf, semaines=(1, 2, 3, 4)).set_index("semaine")["survie"]
    assert survies[1] == pytest.approx(0.90)
    assert survies[2] == pytest.approx(0.90)  # le censuré de la semaine 2 ne fait pas baisser la courbe
    assert survies[3] == pytest.approx(0.675)  # 0,90 × (1 − 2/8)
    assert survie.mediane_de_survie(kmf) is None  # la courbe ne passe pas sous 50 %


def test_semaines_critiques():
    table = pd.DataFrame({"semaine": [1, 2, 3, 4, 5], "taux": [0.010, 0.030, 0.015, 0.014, 0.020]})
    marquee = survie.marquer_semaines_critiques(table, risque_moyen=0.010)
    # Seuil = 1,5 × 1 % = 1,5 % : la semaine 3 (exactement 1,5 %) est critique, la semaine 4 non.
    assert list(marquee.loc[marquee["critique"], "semaine"]) == [2, 3, 5]


def test_risque_hebdomadaire_moyen():
    table, risque_moyen = survie.risque_hebdomadaire(dix_etudiants())
    # 3 décrochages pour 1 + 2 + 3 + 3 + 6 × 4 = 33 semaines-étudiant à risque.
    assert risque_moyen == pytest.approx(3 / 33)
    suivies = table[table["suivis"] > 0]
    assert (suivies["ic_bas"] >= 0).all() and (suivies["ic_bas"] <= suivies["taux"]).all()
    # Après la semaine 4, plus personne n'est suivi : taux et IC vides, jamais de division par 0.
    assert table.loc[table["suivis"] == 0, ["taux", "ic_bas", "ic_haut"]].isna().all().all()


def test_log_rank_exclut_les_manquants():
    base = pd.DataFrame({"T": [2, 5, 3, 8, 4, 6, 7], "E": [1, 0, 1, 0, 1, 1, 0],
                         "emploi_parallele": ["Oui", "Non", "Oui", "Non", None, "Oui", "Non"]})
    resultat = survie.kaplan_meier_sous_groupe(base, "emploi_parallele")
    assert resultat["manquants"] == 1
    assert resultat["tableau"]["effectif"].sum() == 6
    assert 0 <= resultat["p"] <= 1


# ---------------------------------------------------------------------------
# Préparation des données et modèle de Cox (SV-02)
# ---------------------------------------------------------------------------

def base_inventee(n=80):
    """n étudiants inventés (graine fixe), avec les colonnes de base_survie.csv."""
    generateur = np.random.default_rng(config.SEED)
    filieres = config.MODALITES[("etudiants", "filiere")]
    base = pd.DataFrame({
        "id_etudiant": [f"HZ{i:05d}" for i in range(n)],
        "cohorte": ["2024", "2025"] * (n // 2),
        "genre": generateur.choice(["F", "M"], n),
        "age": pd.array(generateur.integers(18, 25, n), dtype="Int64"),
        "boursier": generateur.choice(["Oui", "Non"], n),
        "filiere": [filieres[i % len(filieres)] for i in range(n)],
        "mention_bac": generateur.choice(["Passable", "Bien"], n),
        "note_bac": generateur.uniform(10, 18, n).round(2),
        "region_origine": generateur.choice(["Dakar", "Thiès", "Kolda"], n).astype(object),
        "distance_campus_km": generateur.uniform(1, 100, n).round(1),
        "emploi_parallele": generateur.choice(["Oui", "Non"], n).astype(object),
        "T": generateur.integers(1, 31, n),
        "E": generateur.integers(0, 2, n),
    })
    for colonne in ["T_seuil3", "T_seuil5"]:
        base[colonne] = base["T"]
    for colonne in ["E_seuil3", "E_seuil5"]:
        base[colonne] = base["E"]
    base["tutore"] = 0
    base["nb_seances"] = 0
    # Quelques valeurs manquantes.
    base.loc[0, "age"] = pd.NA
    base.loc[1, "note_bac"] = np.nan
    base.loc[2, "region_origine"] = np.nan
    base.loc[3, "emploi_parallele"] = np.nan
    return base


def test_preparation_cox_variables():
    donnees, _ = survie.preparer_donnees_cox(base_inventee())
    covariables = [c for c in donnees.columns if c not in ("T", "E")]
    origines = {survie.variable_d_origine(c) for c in covariables}
    assert "mention_bac" not in origines  # D-49 : redondante avec la note du bac
    interdites = {"tutore", "statut_tutorat", "semaine_debut_tutorat", "type_tuteur", "motif_orientation",
                  "nb_seances"}
    assert not origines & interdites
    assert not any("_seuil" in c for c in covariables)
    # Les modalités de référence n'ont pas d'indicatrice.
    for variable, reference in config.REFERENCES_COX.items():
        assert f"{variable}{config.SEPARATEUR_INDICATRICE}{reference}" not in covariables
    # Modalité « (manquant) » créée pour les qualitatives, aucun manquant restant.
    assert f"emploi_parallele={config.MODALITE_MANQUANTE}" in covariables
    assert f"region_dakar={config.MODALITE_MANQUANTE}" in covariables
    assert donnees.notna().all().all()
    assert set(origines) <= set(config.VARIABLES_COX_NUMERIQUES + config.VARIABLES_COX_QUALITATIVES)


def test_preparation_cox_utilise_les_medianes_fournies():
    base = base_inventee()
    medianes = {"age": 99.0, "note_bac": 5.5, "log2_distance": 7.0}
    donnees, utilisees = survie.preparer_donnees_cox(base, medianes=medianes)
    assert utilisees == medianes
    assert donnees.loc[0, "age"] == 99.0  # âge manquant de l'étudiant 0
    assert donnees.loc[1, "note_bac"] == 5.5  # note manquante de l'étudiant 1
    _, calculees = survie.preparer_donnees_cox(base)
    assert calculees["age"] == pytest.approx(base["age"].dropna().astype(float).median())


def test_cox_stratifie_s_ajuste():
    donnees, _ = survie.preparer_donnees_cox(base_inventee())
    cph = survie.ajuster_cox(donnees, strates=[config.VARIABLE_COHORTE])
    hr = survie.hazard_ratios(cph)
    assert "cohorte=2025" not in hr.index  # variable de strate : pas de hazard ratio
    assert "age" in hr.index and (hr["HR"] > 0).all()
    assert 0 <= cph.concordance_index_ <= 1
