"""Tests de l'analyse de survie (Kaplan-Meier, semaines critiques).

Rôle du module : tester src/survie.py sur de petits jeux d'étudiants inventés.

Tâche couverte : SV-01.
"""

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
