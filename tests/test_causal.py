"""Tests de la phase de conception causale (photo, score, poids, équilibre).

Rôle du module : tester src/causal.py sur de petits jeux d'étudiants inventés, puis
vérifier quelques invariants de la photo de la semaine 8 sur data/processed/.
Aucun test ne compare T, E ou la survie entre tutorés et non tutorés (D-59).

Tâches couvertes : CA-01, CA-02, CA-03.
"""

import numpy as np
import pandas as pd
import pytest

from src import causal, config


# ---------------------------------------------------------------------------
# Population de la photo (D-54)
# ---------------------------------------------------------------------------

def petite_base():
    """7 étudiants inventés ; photo à la semaine 8."""
    return pd.DataFrame({
        "id_etudiant": ["A", "B", "C", "D", "E", "F", "G"],
        "T": [5, 12, 20, 30, 30, 15, 30],
        "E": [1, 1, 0, 0, 0, 1, 0],
        "T_seuil3": [5, 7, 20, 30, 30, 15, 30],
        "statut_tutorat": [config.STATUT_TUTORE, config.STATUT_TUTORE, config.STATUT_TUTORE,
                           config.STATUT_TUTORAT_APRES_T, config.STATUT_NON_TUTORE,
                           config.STATUT_TUTORAT_SEMAINE_INCONNUE, config.STATUT_TUTORE],
        "semaine_debut_tutorat": pd.array([3, 6, 10, 45, None, None, 8], dtype="Int64"),
    })


def test_population_photo():
    population = causal.population_photo(petite_base(), 8)
    equipes = dict(zip(population["id_etudiant"], population["tutore_photo"]))
    # A : sorti avant la photo (T = 5 <= 8) ; F : semaine de début inconnue -> exclus.
    assert equipes == {"B": 1, "C": 0, "D": 0, "E": 0, "G": 1}
    # B : début 6 <= 8 -> tutoré ; G : début 8 (la semaine même) -> tutoré ;
    # C : début 10 > 8 -> pas encore tutoré ; D : début hors suivi (45) -> non tutoré.
    assert (population["T"] > 8).all()


def test_population_photo_variante_seuil3():
    population = causal.population_photo(petite_base(), 8, duree="T_seuil3")
    # Avec le seuil de 3 semaines, B décroche en semaine 7 : il n'est plus sur la photo.
    assert "B" not in set(population["id_etudiant"])
    assert (population["T_seuil3"] > 8).all()


# ---------------------------------------------------------------------------
# Activité moyenne sur une fenêtre
# ---------------------------------------------------------------------------

def petite_periode():
    return pd.DataFrame({
        "id_etudiant": ["A", "A", "A", "B", "B"],
        "semaine": [1, 2, 3, 1, 2],
        "nb_connexions_lms": [2.0, 4.0, 100.0, np.nan, 6.0],
        "devoirs_rendus": [1.0, 0.0, 2.0, 1.0, 1.0],
        "note_moyenne": [np.nan, 12.0, 0.0, np.nan, np.nan],
        "absences": [0.0, 2.0, 9.0, 1.0, 3.0],
    })


def test_activite_moyenne():
    activite = causal.activite_moyenne(petite_periode(), ["A", "B", "A"], 1, 2)
    assert list(activite["id_etudiant"]) == ["A", "B", "A"]  # doublons gardés, ordre conservé
    ligne_a = activite.iloc[0]
    assert ligne_a["nb_connexions_lms_moy"] == 3.0  # semaine 3 (100) hors fenêtre
    assert ligne_a["note_moyenne_moy"] == 12.0  # le vide de la semaine 1 est ignoré
    ligne_b = activite.iloc[1]
    assert ligne_b["nb_connexions_lms_moy"] == 6.0
    assert pd.isna(ligne_b["note_moyenne_moy"])  # aucune note sur la fenêtre : manquant
    assert activite.iloc[2].equals(activite.iloc[0])


# ---------------------------------------------------------------------------
# Covariables du score (D-55)
# ---------------------------------------------------------------------------

def base_et_periode_inventees(n=60):
    """n étudiants inventés (graine fixe) avec les colonnes utiles, et leur activité."""
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
        "region_origine": generateur.choice(["Dakar", "Thiès"], n).astype(object),
        "distance_campus_km": generateur.uniform(1, 100, n).round(1),
        "emploi_parallele": generateur.choice(["Oui", "Non"], n).astype(object),
        "T": generateur.integers(9, 31, n),
        "E": generateur.integers(0, 2, n),
        "statut_tutorat": config.STATUT_NON_TUTORE,
        "semaine_debut_tutorat": pd.array([None] * n, dtype="Int64"),
        "motif_orientation": None,
        "nb_seances": 0,
    })
    base.loc[: n // 3, "statut_tutorat"] = config.STATUT_TUTORE
    base.loc[: n // 3, "semaine_debut_tutorat"] = 5
    lignes = []
    for identifiant in base["id_etudiant"]:
        for semaine in range(1, 9):
            lignes.append({"id_etudiant": identifiant, "semaine": semaine,
                           "nb_connexions_lms": float(generateur.integers(0, 10)),
                           "devoirs_rendus": float(generateur.integers(0, 3)),
                           "note_moyenne": float(generateur.uniform(5, 18)),
                           "absences": float(generateur.integers(0, 4))})
    return base, pd.DataFrame(lignes)


def test_covariables_sans_colonne_interdite():
    base, periode = base_et_periode_inventees()
    population = causal.population_photo(base, 8)
    X, medianes = causal.covariables_du_score(population, periode, (1, 8))
    for colonne in X.columns:
        assert colonne not in ("T", "E", "evenement")
        assert not any(mot in colonne.lower() for mot in causal.MOTS_INTERDITS)
    assert "absences_moy" in X.columns and "absences_moy" in medianes
    assert X.notna().all().all()


def test_colonne_interdite_detectee():
    for colonne in ["tutore_photo", "nb_seances", "T", "E_seuil3", "motif_orientation"]:
        with pytest.raises(causal.ErreurCausal):
            causal.verifier_colonnes_autorisees(["age", colonne])


# ---------------------------------------------------------------------------
# Poids, troncature, différence standardisée, support commun (D-56)
# ---------------------------------------------------------------------------



def test_difference_standardisee():
    valeurs = [1.0, 2.0, 3.0, 4.0]
    traite = [1, 1, 0, 0]
    # Moyennes 1,5 et 3,5 ; variances 0,5 et 0,5 -> SMD = -2 / racine(0,5).
    assert causal.difference_standardisee(valeurs, traite) == pytest.approx(-2 / np.sqrt(0.5))
    # Poids tous égaux : même résultat que sans poids.
    assert causal.difference_standardisee(valeurs, traite, [2, 2, 2, 2]) == pytest.approx(-2 / np.sqrt(0.5))
    # Poids [1, 3, 1, 1] : moyenne pondérée des tutorés 1,75 ; dénominateur inchangé.
    assert causal.difference_standardisee(valeurs, traite, [1, 3, 1, 1]) == pytest.approx(-1.75 / np.sqrt(0.5))




# ---------------------------------------------------------------------------
# Invariants de la photo de la semaine 8 sur data/processed/
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def photo_reelle():
    if not config.FICHIER_BASE_SURVIE.exists():
        pytest.skip("data/processed/base_survie.csv absent : lancer python run_all.py")
    from src import eda
    base, _ = eda.lire_bases()
    return causal.population_photo(base, config.SEMAINE_LANDMARK)


def test_invariants_photo_semaine_8(photo_reelle):
    assert (photo_reelle["T"] > config.SEMAINE_LANDMARK).all()
    assert set(photo_reelle["tutore_photo"].unique()) <= {0, 1}
    assert not causal.semaine_debut_inconnue(photo_reelle).any()
    tutores = photo_reelle[photo_reelle["tutore_photo"] == 1]
    assert (tutores["semaine_debut_tutorat"] <= config.SEMAINE_LANDMARK).all()
