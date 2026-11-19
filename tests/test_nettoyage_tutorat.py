"""Tests du nettoyage de la table tutorat.

Rôle du module : (1) tester les règles sur de petits DataFrames construits ici ;
(2) vérifier les invariants de data/processed/tutorat.csv (ignorés tant que le
fichier n'existe pas).

Tâche couverte : DA-04.
"""

import pandas as pd
import pytest

from src import config
from src.nettoyage import tutorat
from src.nettoyage.commun import ErreurNettoyage

COLONNES_BRUTES = ["ID Etudiant", "semaine_debut", "nb_seances", "type_tuteur", "motif_orientation"]
ETUDIANTS = pd.DataFrame({"id_etudiant": [f"HZ0000{i}" for i in range(1, 6)]})
AUCUNE_SORTIE = pd.Series(dtype="int64")


def ligne(identifiant="HZ00001", debut="5", seances="10", tuteur="pair", motif="notes faibles"):
    """Une ligne de tutorat brute (tout en texte)."""
    return [identifiant, debut, seances, tuteur, motif]


def table(*lignes):
    """DataFrame brut, avec l'en-tête « ID Etudiant » du fichier d'origine."""
    return pd.DataFrame(list(lignes), columns=COLONNES_BRUTES)


def nettoyer(*lignes, sorties=AUCUNE_SORTIE):
    """Nettoyage complet ; renvoie (table indexée par identifiant, rejets)."""
    propre, rejets, _, _ = tutorat.nettoyer(table(*lignes), ETUDIANTS, sorties)
    return propre.set_index("id_etudiant"), rejets


# ---------------------------------------------------------------------------
# Tests unitaires
# ---------------------------------------------------------------------------

def test_entete_et_identifiants():
    propre, _, _ = tutorat.regle_entete_identifiants(table(ligne(" hz00001")))
    assert list(propre.columns[:5]) == config.FICHIERS_BRUTS["tutorat"]["colonnes"]
    assert propre.loc[0, "id_etudiant"] == "HZ00001"


def test_types_de_tuteur_recodes():
    propre, _ = nettoyer(ligne("HZ00001", tuteur="pair (étudiant avancé)"), ligne("HZ00002", tuteur="Prof"),
                         ligne("HZ00003", tuteur="étudiant"), ligne("HZ00004", tuteur="ENSEIGNANT "))
    assert list(propre["type_tuteur"]) == ["pair", "enseignant", "pair", "enseignant"]


def test_type_inconnu_arrete():
    with pytest.raises(ErreurNettoyage):
        nettoyer(ligne(tuteur="coach"))


def test_motif_inconnu_arrete():
    with pytest.raises(ErreurNettoyage):
        nettoyer(ligne(motif="ennui"))


def test_nb_seances_nul_ou_negatif_manquant_et_drapeau():
    propre, _ = nettoyer(ligne("HZ00001", seances="0.0"), ligne("HZ00002", seances="-2.0"),
                         ligne("HZ00003", seances="12"))
    assert pd.isna(propre.loc["HZ00001", "nb_seances"]) and pd.isna(propre.loc["HZ00002", "nb_seances"])
    assert propre.loc["HZ00001", "drapeau_tutorat"] == config.DRAPEAU_NB_SEANCES_INVALIDE
    assert propre.loc["HZ00003", "nb_seances"] == 12 and pd.isna(propre.loc["HZ00003", "drapeau_tutorat"])


def test_doublon_exact_supprime_et_doublon_different_arrete():
    propre, _ = nettoyer(ligne(), ligne())
    assert len(propre) == 1
    with pytest.raises(ErreurNettoyage):
        nettoyer(ligne(), ligne(seances="11"))


def test_orphelin_retire():
    propre, rejets = nettoyer(ligne("HZ00001"), ligne("HZ99999"))
    assert list(propre.index) == ["HZ00001"]
    assert list(rejets["id_etudiant"]) == ["HZ99999"]


def test_semaine_debut_52_gardee_avec_drapeau():
    propre, _ = nettoyer(ligne(debut="52"))
    assert propre.loc["HZ00001", "semaine_debut"] == 52
    assert propre.loc["HZ00001", "drapeau_tutorat"] == config.DRAPEAU_DEBUT_HORS_SUIVI


def test_semaine_debut_0_manquante_avec_drapeau():
    propre, _ = nettoyer(ligne(debut="0"))
    assert pd.isna(propre.loc["HZ00001", "semaine_debut"])
    assert propre.loc["HZ00001", "drapeau_tutorat"] == config.DRAPEAU_DEBUT_SEMAINE_INVALIDE


def test_debut_apres_la_sortie_drapeau():
    sorties = pd.Series({"HZ00001": 6, "HZ00002": 20, "HZ00003": 10})
    propre, _ = nettoyer(ligne("HZ00001", debut="8"), ligne("HZ00002", debut="8"),
                         ligne("HZ00003", debut="45"), sorties=sorties)
    assert propre.loc["HZ00001", "drapeau_tutorat"] == config.DRAPEAU_DEBUT_APRES_SORTIE
    assert propre.loc["HZ00001", "semaine_debut"] == 8  # valeur gardée
    assert pd.isna(propre.loc["HZ00002", "drapeau_tutorat"])
    assert propre.loc["HZ00003", "drapeau_tutorat"] == "debut_hors_suivi;debut_apres_sortie"


# ---------------------------------------------------------------------------
# Invariants sur data/processed/tutorat.csv
# ---------------------------------------------------------------------------

FICHIER = config.DOSSIER_PROCESSED / "tutorat.csv"
FICHIER_ETUDIANTS = config.DOSSIER_PROCESSED / "etudiants.csv"
sans_fichier = pytest.mark.skipif(not (FICHIER.exists() and FICHIER_ETUDIANTS.exists()),
                                  reason="tables nettoyées absentes")


@pytest.fixture(scope="module")
def propre():
    return pd.read_csv(FICHIER, dtype={"semaine_debut": "Int64", "nb_seances": "Int64"},
                       encoding=config.ENCODAGE)


@sans_fichier
def test_invariant_un_par_etudiant_connu(propre):
    etudiants = pd.read_csv(FICHIER_ETUDIANTS, encoding=config.ENCODAGE)
    assert propre["id_etudiant"].is_unique
    assert set(propre["id_etudiant"]) <= set(etudiants["id_etudiant"])


@sans_fichier
def test_invariant_modalites(propre):
    assert propre["type_tuteur"].isin(config.MODALITES[("tutorat", "type_tuteur")]).all()
    assert propre["motif_orientation"].isin(config.MODALITES[("tutorat", "motif_orientation")]).all()


@sans_fichier
def test_invariant_seances_et_semaine_debut(propre):
    assert (propre["nb_seances"].dropna() >= 1).all()
    hors_suivi = propre["drapeau_tutorat"].fillna("").str.contains(config.DRAPEAU_DEBUT_HORS_SUIVI)
    semaines = propre.loc[~hors_suivi, "semaine_debut"].dropna()
    assert semaines.between(1, config.N_SEMAINES).all()
