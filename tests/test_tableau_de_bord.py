"""Tests du tableau de bord (DB-01), sans réseau ni clé d'API.

Rôle du module : tester src/tableau_de_bord.py sur de petites tables inventées, vérifier
des invariants sur les fichiers produits par run_all.py, et démarrer app/app.py avec
l'outil de test de Streamlit (chaque page, semaines 8 et 4).

Tâches couvertes : DB-01.
"""

import numpy as np
import pandas as pd
import pytest

from src import config
from src import tableau_de_bord as tb


# ---------------------------------------------------------------------------
# Petites tables inventées
# ---------------------------------------------------------------------------

def donnees_inventees():
    """4 étudiants de 2025 (A à D) et 1 de 2024 (Z) ; courbes Cox et scores hebdomadaires simples."""
    base = pd.DataFrame({
        "id_etudiant": ["A", "B", "C", "D", "Z"],
        "cohorte": [2025, 2025, 2025, 2025, 2024],
        "T": [30, 8, 12, 30, 30],
        "semaine_debut_tutorat": pd.array([pd.NA, pd.NA, 3, 10, pd.NA], dtype="Int64"),
        "statut_tutorat": ["non_tutore", "non_tutore", "tutore", "tutore", "non_tutore"],
        "age": [19, 20, 28, 21, 22], "note_bac": [12.0, 11.0, 10.5, 14.0, 13.0],
        "distance_campus_km": [5.0, 12.0, 130.0, 8.0, 3.0], "boursier": ["Oui", "Non", "Non", "Oui", "Non"],
        "emploi_parallele": ["Non", "Oui", "Oui", "Non", "Non"],
        "filiere": ["Droit", "Gestion", "Droit", "Informatique", "Droit"],
        "genre": ["F", "M", "F", "M", "F"], "region_origine": ["Dakar", "Thiès", "Kolda", "Dakar", "Dakar"],
    })
    # Survie Cox : S(8) et S(30) choisies pour que les risques soient faciles à vérifier.
    s8 = {"A": 0.9, "B": 0.8, "C": 0.5, "D": 0.8}
    s30 = {"A": 0.81, "B": 0.4, "C": 0.25, "D": 0.6}
    lignes = []
    for i in s8:
        for semaine in range(1, config.N_SEMAINES + 1):
            survie = 1.0 if semaine < 8 else (s8[i] if semaine < config.N_SEMAINES else s30[i])
            lignes.append({"id_etudiant": i, "semaine": semaine, "survie_cox": survie})
    predictions = pd.DataFrame(lignes)
    scores = pd.DataFrame({"id_etudiant": ["A", "C", "D", "A", "C", "D"], "semaine": [8, 8, 8, 9, 9, 9],
                           "risque_hebdomadaire": [0.5, 0.5, 0.5, 0.01, 0.03, 0.02]})
    return {"base": base, "predictions": predictions, "scores_hebdomadaires": scores, "hr": None,
            "fiches": [{"id_etudiant": "C", "statut": config.STATUT_FICHE_A_REVOIR}]}


@pytest.fixture
def sans_facteurs(monkeypatch):
    """Les facteurs demandent le Cox complet : remplacés ici par un seul facteur fixe (les vrais
    facteurs sont testés sur les fichiers produits)."""
    facteur = [{"facteur": "âge", "valeur_etudiant": "20 ans", "reference_promotion": "-", "multiplicateur": 1.5}]
    monkeypatch.setattr(tb, "facteurs_de_la_semaine", lambda base, population, hr: [facteur] * len(population))


def test_table_a_risque(sans_facteurs):
    table = tb.table_a_risque(donnees_inventees(), 8)
    # B (T = 8) n'est plus suivi après la semaine 8 ; Z est de 2024.
    assert table["id_etudiant"].tolist() == ["C", "D", "A"]
    # Risque 1 − S(30) / S(8) : C 1 − 0,25 / 0,5 = 50 % ; D 25 % ; A 10 %.
    assert table["risque_cox_pct"].tolist() == pytest.approx([50.0, 25.0, 10.0])
    # Risque de la semaine suivante pris à la semaine 9, pas à la semaine 8.
    assert table["risque_semaine_suivante_pct"].tolist() == pytest.approx([3.0, 2.0, 1.0])
    # Tutorat connu à la semaine 8 seulement : D commence en semaine 10.
    assert table["tutorat"].tolist() == ["en cours depuis la semaine 3", "aucun", "aucun"]
    assert table["fiche"].tolist() == [config.STATUT_FICHE_A_REVOIR, "", ""]
    assert table["facteurs"].eq("âge ×1,5").all()
    assert tb.table_a_risque(donnees_inventees(), 7)["fiche"].eq("").all()


def test_tri_a_egalite_par_identifiant(sans_facteurs):
    donnees = donnees_inventees()
    predictions = donnees["predictions"]
    predictions.loc[(predictions["id_etudiant"] == "D") & (predictions["semaine"] == 30), "survie_cox"] = 0.4
    donnees["fiches"] = []
    table = tb.table_a_risque(donnees, 8)
    assert table["id_etudiant"].tolist() == ["C", "D", "A"]  # C et D à 50 % : ordre alphabétique
    donnees["predictions"] = predictions.replace({"id_etudiant": {"C": "E"}})
    donnees["base"] = donnees["base"].replace({"id_etudiant": {"C": "E"}})
    assert tb.table_a_risque(donnees, 8)["id_etudiant"].tolist()[:2] == ["D", "E"]


def test_fiche_llm_absente():
    donnees = donnees_inventees()
    assert tb.fiche_llm(donnees, "A") is None
    assert tb.fiche_llm(donnees, "C")["statut"] == config.STATUT_FICHE_A_REVOIR


def test_profil_sans_genre_ni_region():
    profil = tb.profil(donnees_inventees(), "C")
    assert list(profil) == config.COLONNES_PROFIL_TABLEAU
    assert "genre" not in profil and "region_origine" not in profil
    assert profil["age"] == 28 and profil["filiere"] == "Droit"


def test_courbe_individuelle_et_moyenne():
    courbe = tb.courbe_individuelle(donnees_inventees(), "C")
    assert courbe["semaine"].tolist() == list(range(1, config.N_SEMAINES + 1))
    derniere = courbe.iloc[-1]
    assert derniere["survie_etudiant"] == pytest.approx(0.25)
    assert derniere["survie_moyenne_cohorte"] == pytest.approx(np.mean([0.81, 0.4, 0.25, 0.6]))
    assert courbe.loc[courbe["semaine"] == 8, "survie_moyenne_cohorte"].item() == pytest.approx(0.75)


def test_semaines_recentes():
    assert tb.semaines_recentes(1) == [1]
    assert tb.semaines_recentes(8) == [7, 8]


def test_texte_facteurs_et_tutorat():
    facteurs = [{"facteur": "âge", "multiplicateur": 2.1}, {"facteur": "emploi en parallèle des études",
                                                            "multiplicateur": 1.6}]
    assert tb.texte_facteurs(facteurs) == "âge ×2,1 ; emploi ×1,6"
    assert tb.texte_tutorat({"statut": "en cours", "semaine_debut": 5}) == "en cours depuis la semaine 5"
    assert tb.texte_tutorat({"statut": "aucun"}) == "aucun"


def test_texte_tutorat_court():
    assert tb.texte_tutorat_court({"statut": "en cours", "semaine_debut": 5}) == "en cours"
    assert tb.texte_tutorat_court({"statut": "aucun"}) == "aucun"
    assert tb.texte_tutorat_court({"statut": "signalé, semaine de début inconnue"}) == "signalé"
    assert tb.statut_tutorat_etudiant(donnees_inventees(), "C", 8) == {"statut": "en cours", "semaine_debut": 3}
    assert tb.statut_tutorat_etudiant(donnees_inventees(), "D", 8) == {"statut": "aucun"}


def test_resume_effet_meme_sens():
    effet = pd.DataFrame({"mesure": ["difference_risque", "hr"], "estimation": [-0.07, 0.6],
                          "ic_bas": [-0.1, 0.5], "ic_haut": [-0.04, 0.76]})
    lignes = {c: [0] * 3 for c in tb.COLONNES_VARIANTES}
    lignes["analyse"] = ["analyse principale", "variante 1", "variante 2"]
    lignes["difference_risque"] = [-0.07, -0.05, -0.02]
    resume = tb.resume_effet({"effet": effet, "sensibilite": pd.DataFrame(lignes)})
    assert resume["mesures"]["hr"] == (0.6, 0.5, 0.76)
    assert resume["variantes"]["analyse"].tolist() == ["variante 1", "variante 2"] and resume["meme_sens"]
    lignes["difference_risque"] = [-0.07, -0.05, 0.01]
    assert not tb.resume_effet({"effet": effet, "sensibilite": pd.DataFrame(lignes)})["meme_sens"]


# ---------------------------------------------------------------------------
# Invariants sur les fichiers produits par run_all.py
# ---------------------------------------------------------------------------

def fichiers_presents():
    return (config.FICHIER_BASE_SURVIE.exists() and config.FICHIER_PERIODE_PERSONNE.exists()
            and all((config.DOSSIER_RESULTATS / nom).exists() for nom in tb.FICHIERS_RESULTATS.values()))


@pytest.fixture(scope="module")
def donnees_reelles():
    if not fichiers_presents():
        pytest.skip("résultats absents : lancer python run_all.py")
    return tb.charger_donnees()


def test_semaine_8_seuil_40_les_54_etudiants_des_fiches(donnees_reelles):
    table = tb.table_a_risque(donnees_reelles, config.SEMAINE_FICHES)
    retenus = table[table["risque_cox_pct"] >= config.SEUIL_DEFAUT_TABLEAU_PCT]
    assert len(retenus) == 54
    if donnees_reelles["fiches"]:
        assert set(retenus["id_etudiant"]) == {f["id_etudiant"] for f in donnees_reelles["fiches"]}
        assert retenus["fiche"].ne("").all() and table.loc[~table.index.isin(retenus.index), "fiche"].eq("").all()


def test_tables_de_chaque_semaine(donnees_reelles):
    for semaine in range(config.SEMAINE_MIN_TABLEAU, config.SEMAINE_MAX_TABLEAU + 1):
        table = tb.table_a_risque(donnees_reelles, semaine)
        assert len(table) > 0, semaine
        for colonne in ("risque_cox_pct", "risque_semaine_suivante_pct"):
            assert table[colonne].between(0, 100).all(), (semaine, colonne)
        textes = " ".join(table["facteurs"])
        assert "genre" not in textes and "région" not in textes, semaine


# ---------------------------------------------------------------------------
# Démarrage de l'application (outil de test de Streamlit, sans navigateur)
# ---------------------------------------------------------------------------

PAGES = ["Étudiants à risque", "Fiche étudiant", "Effet du tutorat", "À propos"]


@pytest.mark.parametrize("semaine", [config.SEMAINE_FICHES, 4])
def test_application_chaque_page(donnees_reelles, semaine):
    from streamlit.testing.v1 import AppTest

    application = AppTest.from_file(str(config.RACINE / "app" / "app.py"), default_timeout=120)
    application.run()
    assert not application.exception
    application.sidebar.slider(key="semaine").set_value(semaine).run()
    for page in PAGES:
        application.sidebar.radio(key="page").set_value(page).run()
        assert not application.exception, (page, semaine, application.exception)
        assert application.title[0].value == page


def test_fiche_etudiant_legende_tutorat_complete(donnees_reelles):
    from streamlit.testing.v1 import AppTest

    semaine, seuil = config.SEMAINE_FICHES, config.SEUIL_DEFAUT_TABLEAU_PCT
    table = tb.table_a_risque(donnees_reelles, semaine)
    signales = table[table["risque_cox_pct"] >= seuil]
    application = AppTest.from_file(str(config.RACINE / "app" / "app.py"), default_timeout=120)
    application.run()
    application.sidebar.radio(key="page").set_value("Fiche étudiant").run()
    # Un étudiant en tutorat et un sans tutorat : texte court dans la métrique, complet dans la légende.
    for prefixe in ("en cours", "aucun"):
        ligne = signales[signales["tutorat"].str.startswith(prefixe)].iloc[0]
        application.selectbox(key=f"etudiant_{semaine}_{seuil}").set_value(ligne["id_etudiant"]).run()
        assert not application.exception
        legendes = [c.value for c in application.caption]
        assert f"Tutorat : {ligne['tutorat']}." in legendes
        assert application.metric[2].value == prefixe
