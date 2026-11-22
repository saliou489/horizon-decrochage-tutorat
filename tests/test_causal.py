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

def test_poids_stabilises():
    poids = causal.poids_stabilises([0.2, 0.5, 0.8], [1, 0, 1])
    # P(tutoré) = 2/3 : 0,667 / 0,2 ; 0,333 / 0,5 ; 0,667 / 0,8.
    assert poids == pytest.approx([3.333, 0.667, 0.833], abs=1e-3)


def test_troncature():
    poids = np.array(list(range(1, 100)) + [1000], dtype=float)
    tronques, (bas, haut), nb_modifies = causal.tronquer_poids(poids)
    assert (bas, haut) == pytest.approx(tuple(np.percentile(poids, config.PERCENTILES_TRONCATURE)))
    assert tronques.min() == pytest.approx(bas) and tronques.max() == pytest.approx(haut)
    assert nb_modifies == 2  # le poids 1 et le poids 1000


def test_difference_standardisee():
    valeurs = [1.0, 2.0, 3.0, 4.0]
    traite = [1, 1, 0, 0]
    # Moyennes 1,5 et 3,5 ; variances 0,5 et 0,5 -> SMD = -2 / racine(0,5).
    assert causal.difference_standardisee(valeurs, traite) == pytest.approx(-2 / np.sqrt(0.5))
    # Poids tous égaux : même résultat que sans poids.
    assert causal.difference_standardisee(valeurs, traite, [2, 2, 2, 2]) == pytest.approx(-2 / np.sqrt(0.5))
    # Poids [1, 3, 1, 1] : moyenne pondérée des tutorés 1,75 ; dénominateur inchangé.
    assert causal.difference_standardisee(valeurs, traite, [1, 3, 1, 1]) == pytest.approx(-1.75 / np.sqrt(0.5))


def test_support_commun():
    support = causal.support_commun([0.1, 0.4, 0.6, 0.2, 0.5, 0.9], [1, 1, 1, 0, 0, 0])
    assert support["bornes"] == pytest.approx((0.2, 0.6))
    assert support["hors_support_tutores"] == 1  # score 0,1
    assert support["hors_support_autres"] == 1  # score 0,9
    assert list(support["dans_support"]) == [False, True, True, True, True, False]


def test_auc_par_les_rangs():
    # Tous les tutorés au-dessus des autres : AUC = 1 ; ordre inverse : 0.
    assert causal.auc_par_les_rangs([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == pytest.approx(1.0)
    assert causal.auc_par_les_rangs([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]) == pytest.approx(0.0)


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


# ---------------------------------------------------------------------------
# Corrections de la relecture RV02 (RV02-03 à RV02-05, D-61)
# ---------------------------------------------------------------------------

def test_chaine_sur_tirage_avec_doublons_et_permutation():
    base, periode = base_et_periode_inventees(n=200)
    population = causal.population_photo(base, 8)
    # Tirage bootstrap brut : index en double (la chaîne doit le remettre à zéro).
    tirage = population.sample(n=len(population), replace=True, random_state=config.SEED)
    assert tirage.index.duplicated().any()
    resultat = causal.chaine_de_conception(tirage, periode, (1, 8), 8)
    assert len(resultat["X"]) == len(tirage) == len(resultat["poids"])
    # Simple permutation : chaque étudiant garde le même score.
    reference = causal.chaine_de_conception(population, periode, (1, 8), 8)
    melangee = population.sample(frac=1, random_state=config.SEED)
    permutee = causal.chaine_de_conception(melangee, periode, (1, 8), 8)
    score_reference = pd.Series(reference["score"], index=population["id_etudiant"])
    score_permute = pd.Series(permutee["score"], index=melangee["id_etudiant"].to_numpy())
    pd.testing.assert_series_equal(score_reference.sort_index(), score_permute.sort_index(), check_names=False)


def test_retouche_declenchee_et_equilibre_initial_garde(monkeypatch):
    base, periode = base_et_periode_inventees(n=200)
    population = causal.population_photo(base, 8)
    # Seuil minuscule : le critère ne peut pas être atteint, la retouche doit être faite une fois.
    monkeypatch.setattr(config, "SEUIL_SMD", 1e-12)
    resultat = causal.chaine_de_conception(population, periode, (1, 8), 8)
    assert resultat["retouche"] and not resultat["critere_atteint"]
    assert any(c.startswith(causal.PREFIXE_CARRE) for c in resultat["X"].columns)
    initial = resultat["equilibre_initial"]
    assert list(initial["variable"]) == list(resultat["equilibre"]["variable"])
    assert not np.allclose(initial["smd_apres"], resultat["equilibre"]["smd_apres"])
    # Seuil énorme : jamais de retouche.
    monkeypatch.setattr(config, "SEUIL_SMD", 1e12)
    sans = causal.chaine_de_conception(population, periode, (1, 8), 8)
    assert not sans["retouche"]
    assert not any(c.startswith(causal.PREFIXE_CARRE) for c in sans["X"].columns)


def test_matrice_equilibre_avec_references_et_manquant():
    base, periode = base_et_periode_inventees(n=200)
    base.loc[3, "region_origine"] = np.nan
    population = causal.population_photo(base, 8)
    X, _ = causal.covariables_du_score(population, periode, (1, 8))
    colonnes = causal.matrice_equilibre(population, X).columns
    for reference in ["genre=F", "boursier=Non", "filiere=Informatique", "region_dakar=Dakar",
                      "emploi_parallele=Non", "cohorte=2024"]:
        assert reference in colonnes
    assert f"region_dakar={config.MODALITE_MANQUANTE}" in colonnes
    assert "note_moyenne_moy" in colonnes


def test_fenetre_posterieure_a_la_photo_refusee():
    base, periode = base_et_periode_inventees(n=200)
    population = causal.population_photo(base, 8)
    with pytest.raises(causal.ErreurCausal):
        causal.chaine_de_conception(population, periode, (1, 12), 8)


def test_auc_effectifs_differents_et_ex_aequo():
    # n1 = 2, n0 = 3. Tutoré à 0,4 : bat 0,1 et fait égalité avec deux 0,4 -> 2 ;
    # tutoré à 0,8 : bat les trois -> 3. AUC = 5 / 6.
    assert causal.auc_par_les_rangs([0.1, 0.4, 0.4, 0.8, 0.4], [0, 1, 0, 1, 0]) == pytest.approx(5 / 6)


def test_colonne_hors_liste_positive_refusee():
    for colonne in ["type_evenement", "duree_apres_photo", "id_etudiant", "etat_activite_prec",
                    "note_moyenne_prec", "mention_bac=Bien"]:
        with pytest.raises(causal.ErreurCausal):
            causal.verifier_liste_positive(["age", colonne])
    causal.verifier_liste_positive(["age", "filiere=Droit", "absences_moy"])
    # Variable exclue (bonus F8) : ses indicatrices sont refusées.
    with pytest.raises(causal.ErreurCausal):
        causal.verifier_liste_positive(["age", "boursier=Oui"], variables_exclues=("boursier",))
