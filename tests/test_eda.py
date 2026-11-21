"""Tests des fonctions descriptives de l'analyse exploratoire.

Rôle du module : tester src/eda.py sur de petits jeux d'étudiants inventés.

Tâche couverte : DA-08.
"""

import pandas as pd
import pytest

from src import config, eda


def test_taux_hebdomadaire_tient_compte_de_la_censure():
    # 4 étudiants : décroche en semaine 2 ; censuré en semaine 3 ; décroche en semaine 3 ; suivi jusqu'à 30.
    base = pd.DataFrame({"T": [2, 3, 3, 30], "E": [1, 0, 1, 0]})
    taux = eda.taux_hebdomadaire(base).set_index("semaine")
    assert len(taux) == config.N_SEMAINES
    assert list(taux.loc[[1, 2, 3], "suivis"]) == [4, 4, 3]
    assert list(taux.loc[[1, 2, 3], "decrochages"]) == [0, 1, 1]
    assert taux.loc[1, "taux"] == 0
    assert taux.loc[2, "taux"] == pytest.approx(0.25)
    assert taux.loc[3, "taux"] == pytest.approx(1 / 3)
    assert taux.loc[30, "suivis"] == 1 and taux.loc[30, "decrochages"] == 0


def base_inventee():
    """6 étudiants inventés sur 2 cohortes, avec quelques valeurs manquantes."""
    return pd.DataFrame({
        "cohorte": [2024, 2024, 2024, 2025, 2025, 2025],
        "genre": ["F", "M", "F", "M", "M", "F"],
        "age": pd.array([19, pd.NA, 21, 20, 22, 18], dtype="Int64"),
        "boursier": ["Oui", "Non", "Oui", "Non", "Non", "Oui"],
        "filiere": ["Informatique"] * 3 + ["Gestion"] * 3,
        "mention_bac": ["Passable", "Bien", "Passable", "Bien", "Bien", "Passable"],
        "note_bac": [11.0, 14.0, 10.5, 14.5, 15.0, None],
        "region_origine": ["Dakar", None, "Thiès", "Dakar", "Dakar", None],
        "distance_campus_km": [3.0, 12.5, 7.0, 1.0, 2.0, 30.0],
        "emploi_parallele": ["Oui", "Non", None, "Non", "Oui", "Non"],
    })


def test_profil_par_cohorte_effectifs_et_manquants():
    base = base_inventee()
    profil = eda.profil_par_cohorte(base)
    assert "cohorte" not in set(profil["variable"])
    qualitatives = profil[profil["moyenne"].isna()]
    # Pour une variable qualitative, les effectifs (manquants compris) font la taille de la cohorte.
    sommes = qualitatives.groupby(["variable", "cohorte"])["effectif"].sum()
    tailles = base["cohorte"].value_counts()
    for (variable, cohorte), somme in sommes.items():
        assert somme == tailles[cohorte], variable
    # Variable numérique : effectif renseigné + manquants = taille de la cohorte.
    age = profil[profil["variable"] == "age"].set_index("cohorte")
    assert age.loc[2024, "effectif"] == 2 and age.loc[2024, "manquants"] == 1
    assert age.loc[2024, "moyenne"] == pytest.approx(20)
    assert age.loc[2025, "manquants"] == 0
    region_2025 = profil[(profil["variable"] == "region_origine") & (profil["cohorte"] == 2025)]
    assert set(region_2025["manquants"]) == {1}
    manquant = region_2025[region_2025["modalite"] == config.MODALITE_MANQUANTE]
    assert manquant["effectif"].iloc[0] == 1 and manquant["pourcentage"].iloc[0] == pytest.approx(100 / 3)


def test_manquants_covariables():
    manquants = eda.manquants_covariables(base_inventee())["manquants"]
    assert manquants["age"] == 1 and manquants["note_bac"] == 1
    assert manquants["region_origine"] == 2 and manquants["emploi_parallele"] == 1
    assert manquants["genre"] == 0


def test_repartition_evenements():
    base = pd.DataFrame({"type_evenement": [config.EVENEMENT_ABANDON_DECLARE, config.EVENEMENT_FIN_DE_SUIVI,
                                            config.EVENEMENT_FIN_DE_SUIVI, config.EVENEMENT_TRANSFERT],
                         "E": [1, 0, 0, 0]})
    par_type, synthese = eda.repartition_evenements(base)
    assert par_type.loc[config.EVENEMENT_FIN_DE_SUIVI, "effectif"] == 2
    assert par_type.loc[config.EVENEMENT_FIN_DE_SUIVI, "pourcentage"] == pytest.approx(50)
    assert par_type.loc[config.EVENEMENT_ABANDON_DECLARE, "E"] == 1
    assert list(synthese["effectif"]) == [1, 3]


def test_activite_par_semaine():
    periode = pd.DataFrame({"semaine": [1, 1, 2, 2], "nb_connexions_lms": [4, None, 0, 6],
                            "etat_activite": [config.ETAT_ACTIF, config.ETAT_INCONNU,
                                              config.ETAT_INACTIF, config.ETAT_ACTIF]})
    activite = eda.activite_par_semaine(periode).set_index("semaine")
    assert activite.loc[1, "connexions_moyennes"] == pytest.approx(4)  # valeur manquante ignorée
    assert activite.loc[2, "pct_inactives"] == pytest.approx(50)
    assert list(activite["suivis"]) == [2, 2]


def test_debut_tutorat_sans_t_ni_e():
    # Base sans T ni E : la fonction doit marcher, preuve qu'elle n'utilise aucune donnée de décrochage.
    base = pd.DataFrame({
        "statut_tutorat": [config.STATUT_NON_TUTORE, config.STATUT_TUTORE, config.STATUT_TUTORE,
                           config.STATUT_TUTORAT_APRES_T, config.STATUT_TUTORAT_SEMAINE_INCONNUE],
        "semaine_debut_tutorat": pd.array([pd.NA, 3, 8, 12, pd.NA], dtype="Int64"),
        "motif_orientation": [None, "notes faibles", "absences répétées", "notes faibles", "demande personnelle"],
        "type_tuteur": [None, "pair", "enseignant", "pair", "pair"],
    })
    resultat = eda.debut_tutorat(base)
    assert resultat["nb_tutorats"] == 4 and resultat["nb_connues"] == 3
    assert resultat["nb_au_plus_tard_repere"] == 2  # semaines 3 et 8 (repère = 8)
    assert resultat["part_au_plus_tard_repere"] == pytest.approx(200 / 3)
    assert resultat["motifs"]["notes faibles"] == 2
    assert resultat["types_tuteur"]["pair"] == 3
    assert resultat["distribution"].to_dict() == {3: 1, 8: 1, 12: 1}
