"""Tests du nettoyage de la table inscriptions.

Rôle du module : (1) tester les règles sur de petits DataFrames construits ici ;
(2) vérifier les invariants de data/processed/inscriptions.csv (ignorés tant que le
fichier n'existe pas).

Tâche couverte : DA-03.
"""

from datetime import datetime

import pandas as pd
import pytest

from src import config
from src.nettoyage import inscriptions
from src.nettoyage.commun import ErreurNettoyage

COLONNES = config.FICHIERS_BRUTS["inscriptions"]["colonnes"]


def ligne(identifiant, annee="2024-2025", debut="2024-10-07", fin="", statut="inscrit"):
    """Une inscription brute (tout en texte)."""
    return {"id_etudiant": identifiant, "annee_universitaire": annee, "date_debut": debut,
            "date_fin": fin, "statut_final": statut}


def table(*lignes):
    """DataFrame brut construit à partir de lignes."""
    return pd.DataFrame(list(lignes), columns=COLONNES)


def etudiants(*couples):
    """Petite table etudiants nettoyée : (identifiant, cohorte)."""
    return pd.DataFrame({"id_etudiant": [i for i, _ in couples],
                         "cohorte": pd.array([c for _, c in couples], dtype="Int64")})


# Assez de lignes « normales » pour que la rentrée la plus fréquente soit la bonne.
NORMALES = [ligne(f"HZ0000{i}") for i in range(1, 4)]
ETUDIANTS_NORMAUX = [(f"HZ0000{i}", 2024) for i in range(1, 4)]


# ---------------------------------------------------------------------------
# Tests unitaires
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texte", ["2024-10-07", "07/10/2024", "2024/10/07", "7 oct. 2024",
                                   "7 Oct 2024", "7 octobre 2024"])
def test_lecture_des_formats_de_date(texte):
    assert inscriptions.lire_date(texte) == datetime(2024, 10, 7)


def test_mois_accentues_et_vide():
    assert inscriptions.lire_date("1 févr. 2026") == datetime(2026, 2, 1)
    assert inscriptions.lire_date("12 déc. 2024") == datetime(2024, 12, 12)
    assert inscriptions.lire_date("") is None


def test_date_illisible_arrete():
    with pytest.raises(ErreurNettoyage):
        inscriptions.lire_date("31/02/2025")
    with pytest.raises(ErreurNettoyage):
        inscriptions.lire_date("bientôt")


def test_statuts_harmonises_et_imprevu():
    propre, nb, _ = inscriptions.regle_statuts(table(ligne("HZ00001", statut="Abandon "),
                                                     ligne("HZ00002", statut="transféré"),
                                                     ligne("HZ00003", statut="")))
    assert list(propre["statut_final"]) == ["abandon", "transfert", ""]
    assert nb == 2
    with pytest.raises(ErreurNettoyage):
        inscriptions.regle_statuts(table(ligne("HZ00001", statut="exclu")))


def test_doublons_exacts_et_doublon_different():
    propre, nb, _ = inscriptions.regle_doublons(table(ligne("HZ00001"), ligne("HZ00001")))
    assert len(propre) == 1 and nb == 1
    with pytest.raises(ErreurNettoyage):
        inscriptions.regle_doublons(table(ligne("HZ00001"), ligne("HZ00001", statut="abandon")))


def test_echange_des_dates_inversees():
    brut = table(*NORMALES, ligne("HZ00009", debut="2025-01-22", fin="2024-10-07", statut="abandon"))
    propre, nb, _, masque = inscriptions.regle_dates_inversees(brut)
    assert nb == 1 and masque.iloc[-1]
    assert propre.iloc[-1]["date_debut"] == "2024-10-07"
    assert propre.iloc[-1]["date_fin"] == "2025-01-22"


def test_dates_inversees_non_echangeables_arretent():
    brut = table(*NORMALES, ligne("HZ00009", debut="2024-10-07", fin="2024-09-01", statut="abandon"))
    with pytest.raises(ErreurNettoyage):
        inscriptions.regle_dates_inversees(brut)


def test_orphelin_retire():
    propre, nb, _, rejets = inscriptions.regle_orphelins(table(ligne("HZ00001"), ligne("HZ99999")),
                                                         etudiants(("HZ00001", 2024)))
    assert list(propre["id_etudiant"]) == ["HZ00001"]
    assert list(rejets["id_etudiant"]) == ["HZ99999"] and nb == 1


def test_etudiant_sans_inscription_ajoute():
    df = table(ligne("HZ00001"), ligne("HZ00002", annee="2025-2026", debut="2025-10-06"))
    propre, nb, _, ajoutes = inscriptions.regle_inscriptions_reconstituees(
        df, etudiants(("HZ00001", 2024), ("HZ00002", 2025), ("HZ00003", 2025)))
    nouvelle = propre[propre["id_etudiant"] == "HZ00003"].iloc[0]
    assert nb == 1 and ajoutes == {"HZ00003"}
    assert nouvelle["annee_universitaire"] == "2025-2026"
    assert nouvelle["date_debut"] == "2025-10-06"
    assert nouvelle["statut_final"] == "" and pd.isna(nouvelle["date_fin"])


def nettoyer(*lignes_brutes, liste_etudiants):
    """Nettoyage complet d'une petite table, renvoie la table indexée par identifiant."""
    propre, _, _, _ = inscriptions.nettoyer(table(*lignes_brutes), etudiants(*liste_etudiants))
    return propre.set_index("id_etudiant")


def test_abandon_en_2027_aucune_sortie_declaree():
    propre = nettoyer(*NORMALES, ligne("HZ00009", fin="2027-03-15", statut="abandon"),
                      liste_etudiants=ETUDIANTS_NORMAUX + [("HZ00009", 2024)])
    assert propre.loc["HZ00009", "sortie_suivi"] == config.SORTIE_AUCUNE
    assert propre.loc["HZ00009", "drapeau_inscription"] == config.DRAPEAU_ABANDON_HORS_SUIVI
    assert propre.loc["HZ00009", "statut_final"] == "abandon"  # statut d'origine conservé


def test_statut_vide_aucune_sortie_declaree():
    propre = nettoyer(*NORMALES, ligne("HZ00009", statut=""),
                      liste_etudiants=ETUDIANTS_NORMAUX + [("HZ00009", 2024)])
    assert propre.loc["HZ00009", "sortie_suivi"] == config.SORTIE_AUCUNE
    assert propre.loc["HZ00009", "drapeau_inscription"] == config.DRAPEAU_STATUT_VIDE


def test_abandon_et_transfert_dans_le_suivi():
    propre = nettoyer(*NORMALES, ligne("HZ00008", fin="2024-12-01", statut="abandon"),
                      ligne("HZ00009", fin="15/01/2025", statut="Transfert"),
                      liste_etudiants=ETUDIANTS_NORMAUX + [("HZ00008", 2024), ("HZ00009", 2024)])
    assert propre.loc["HZ00008", "sortie_suivi"] == config.SORTIE_ABANDON
    assert propre.loc["HZ00009", "sortie_suivi"] == config.SORTIE_TRANSFERT
    assert propre.loc["HZ00009", "date_fin"] == "2025-01-15"


def test_abandon_sans_date_et_transfert_sans_date():
    propre = nettoyer(*NORMALES, ligne("HZ00009", statut="abandon"),
                      liste_etudiants=ETUDIANTS_NORMAUX + [("HZ00009", 2024)])
    assert propre.loc["HZ00009", "sortie_suivi"] == config.SORTIE_ABANDON
    assert propre.loc["HZ00009", "drapeau_inscription"] == config.DRAPEAU_ABANDON_SANS_DATE
    with pytest.raises(ErreurNettoyage):
        nettoyer(*NORMALES, ligne("HZ00009", statut="transfert"),
                 liste_etudiants=ETUDIANTS_NORMAUX + [("HZ00009", 2024)])


def test_cohorte_incoherente_arrete():
    with pytest.raises(ErreurNettoyage):
        nettoyer(*NORMALES, liste_etudiants=[("HZ00001", 2025), ("HZ00002", 2024), ("HZ00003", 2024)])


# ---------------------------------------------------------------------------
# Invariants sur data/processed/inscriptions.csv
# ---------------------------------------------------------------------------

FICHIER = config.DOSSIER_PROCESSED / "inscriptions.csv"
FICHIER_ETUDIANTS = config.DOSSIER_PROCESSED / "etudiants.csv"
sans_fichier = pytest.mark.skipif(not (FICHIER.exists() and FICHIER_ETUDIANTS.exists()),
                                  reason="tables nettoyées absentes")


@pytest.fixture(scope="module")
def propre():
    return pd.read_csv(FICHIER, dtype=str, encoding=config.ENCODAGE)


@pytest.fixture(scope="module")
def etudiants_propres():
    return pd.read_csv(FICHIER_ETUDIANTS, dtype=str, encoding=config.ENCODAGE)


@sans_fichier
def test_invariant_un_par_etudiant(propre, etudiants_propres):
    assert propre["id_etudiant"].is_unique
    assert set(propre["id_etudiant"]) == set(etudiants_propres["id_etudiant"])


@sans_fichier
def test_invariant_dates(propre):
    avec_fin = propre.dropna(subset=["date_fin"])
    assert (avec_fin["date_fin"] >= avec_fin["date_debut"]).all()


@sans_fichier
def test_invariant_rentree_de_la_cohorte(propre, etudiants_propres):
    cohorte = propre["id_etudiant"].map(etudiants_propres.set_index("id_etudiant")["cohorte"])
    assert (propre["annee_universitaire"].str[:4] == cohorte).all()
    rentree = propre.groupby("annee_universitaire")["date_debut"].nunique()
    assert (rentree == 1).all()  # une seule date de rentrée par cohorte


@sans_fichier
def test_invariant_sortie_suivi(propre):
    assert propre["sortie_suivi"].isin(config.VALEURS_SORTIE_SUIVI).all()
