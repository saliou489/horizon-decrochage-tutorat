"""Tests du nettoyage de la table etudiants.

Rôle du module : (1) tester chaque règle sur un petit DataFrame construit ici ;
(2) vérifier les invariants de data/processed/etudiants.csv (ignorés tant que le
fichier n'existe pas).

Tâche couverte : DA-02.
"""

import pandas as pd
import pytest

from src import config
from src.nettoyage import etudiants
from src.nettoyage.commun import ErreurNettoyage, forme_simplifiee

COLONNES = config.FICHIERS_BRUTS["etudiants"]["colonnes"]


def ligne(**valeurs):
    """Une ligne brute valide (tout en texte), dont on remplace certaines valeurs."""
    base = {
        "id_etudiant": "HZ00001", "cohorte": "2024", "genre": "F", "age": "19",
        "boursier": "Oui", "filiere": "Droit", "mention_bac": "Passable", "note_bac": "11.0",
        "region_origine": "Dakar", "distance_campus_km": "5.0", "emploi_parallele": "Non",
    }
    base.update(valeurs)
    return base


def table(*lignes):
    """DataFrame brut construit à partir de lignes (colonnes du LISEZMOI)."""
    return pd.DataFrame(list(lignes), columns=COLONNES)


def jusqua(df, derniere_regle):
    """Applique les règles dans l'ordre jusqu'à derniere_regle incluse."""
    for regle in etudiants.REGLES:
        df, _, _ = regle(df)
        if regle is derniere_regle:
            return df
    raise ValueError("règle inconnue")


# ---------------------------------------------------------------------------
# Tests unitaires : une règle par test
# ---------------------------------------------------------------------------

def test_entetes_espaces_et_renommage():
    brut = table(ligne())
    colonnes_brutes = list(COLONNES)
    colonnes_brutes[0] = "id_etudiant "
    colonnes_brutes[9] = "Distance campus (km)"
    brut.columns = colonnes_brutes
    propre, _, entrees = etudiants.regle_entetes(brut)
    assert list(propre.columns) == COLONNES
    assert [e["lignes"] for e in entrees] == [1, 1]


def test_entete_inconnu_arrete():
    brut = table(ligne()).rename(columns={"genre": "sexe"})
    with pytest.raises(ErreurNettoyage):
        etudiants.regle_entetes(brut)


def test_identifiants_majuscules_sans_espaces():
    propre, nb, _ = etudiants.regle_identifiants(table(ligne(id_etudiant=" hz12345 ")))
    assert propre.loc[0, "id_etudiant"] == "HZ12345"
    assert nb == 1


def test_identifiant_mal_forme_arrete():
    with pytest.raises(ErreurNettoyage):
        etudiants.regle_identifiants(table(ligne(id_etudiant="HZ1234")))


def test_forme_simplifiee_tirets_et_accents():
    assert forme_simplifiee("  St-Louis ") == "st louis"
    assert forme_simplifiee("THIÈS") == "thies"


def test_modalites_harmonisees():
    brut = table(ligne(genre="Masculin", boursier="0", filiere="GC", mention_bac="tres bien",
                       region_origine="ST LOUIS", emploi_parallele="oui"),
                 ligne(genre="f ", boursier="1", filiere="Info", mention_bac="AB",
                       region_origine="Sedhiou", emploi_parallele=""))
    propre, nb, _ = etudiants.regle_modalites(brut)
    assert list(propre["genre"]) == ["M", "F"]
    assert list(propre["boursier"]) == ["Non", "Oui"]
    assert list(propre["filiere"]) == ["Génie civil", "Informatique"]
    assert list(propre["mention_bac"]) == ["Très bien", "Assez bien"]
    assert list(propre["region_origine"]) == ["Saint-Louis", "Sédhiou"]
    assert list(propre["emploi_parallele"]) == ["Oui", ""]  # la case vide reste vide
    assert nb == 2


def test_modalite_inconnue_arrete():
    with pytest.raises(ErreurNettoyage):
        etudiants.regle_modalites(table(ligne(genre="X")))


def test_nombres_virgule_et_unites():
    brut = table(ligne(age="19 ans", note_bac="12,71", distance_campus_km="9.1 km"))
    propre, nb, _ = etudiants.regle_nombres(brut)
    assert propre.loc[0, "age"] == 19
    assert str(propre["age"].dtype) == "Int64"
    assert propre.loc[0, "note_bac"] == pytest.approx(12.71)
    assert propre.loc[0, "distance_campus_km"] == pytest.approx(9.1)
    assert nb == 1


def test_valeurs_impossibles_a_manquant():
    brut = table(ligne(age="150", note_bac="135", distance_campus_km="-17.3"),
                 ligne(id_etudiant="HZ00002", age="99", note_bac="12", distance_campus_km="9999"),
                 ligne(id_etudiant="HZ00003", distance_campus_km="79.5"))
    propre = jusqua(brut, etudiants.regle_valeurs_impossibles)
    assert pd.isna(propre.loc[0, "age"]) and pd.isna(propre.loc[1, "age"])
    assert pd.isna(propre.loc[0, "note_bac"])
    assert pd.isna(propre.loc[0, "distance_campus_km"]) and pd.isna(propre.loc[1, "distance_campus_km"])
    assert propre.loc[2, "distance_campus_km"] == pytest.approx(79.5)  # grande distance conservée
    assert len(propre) == 3  # aucune ligne supprimée


def test_distance_99_conservee():
    propre = jusqua(table(ligne(distance_campus_km="99")), etudiants.regle_valeurs_impossibles)
    assert propre.loc[0, "distance_campus_km"] == 99


def test_doublons_premiere_ligne_gardee():
    brut = table(ligne(distance_campus_km="10.8"),
                 ligne(id_etudiant="hz00001", distance_campus_km="11.1"),
                 ligne(id_etudiant="HZ00002"),
                 ligne(id_etudiant=" HZ00002"))
    propre = jusqua(brut, etudiants.regle_doublons)
    assert list(propre["id_etudiant"]) == ["HZ00001", "HZ00002"]
    assert propre.loc[0, "distance_campus_km"] == pytest.approx(10.8)
    _, _, entrees = etudiants.regle_doublons(jusqua(brut, etudiants.regle_valeurs_impossibles))
    assert [e["lignes"] for e in entrees] == [1, 1]  # 1 identique, 1 distance différente


def test_doublon_different_hors_distance_arrete():
    brut = table(ligne(), ligne(genre="M"))
    with pytest.raises(ErreurNettoyage):
        jusqua(brut, etudiants.regle_doublons)


def test_mention_recalculee_depuis_note():
    brut = table(ligne(mention_bac="Passable", note_bac="12"),
                 ligne(id_etudiant="HZ00002", mention_bac="", note_bac="16"),
                 ligne(id_etudiant="HZ00003", mention_bac="Bien", note_bac="135"))
    propre, _, entrees = etudiants.regle_mention_note(jusqua(brut, etudiants.regle_doublons))
    assert propre.loc[0, "mention_bac"] == "Assez bien"  # 12 tout rond -> Assez bien (D-10)
    assert propre.loc[1, "mention_bac"] == "Très bien"
    assert propre.loc[2, "mention_bac"] == "Bien"  # note impossible -> mention d'origine gardée
    assert [e["lignes"] for e in entrees] == [1, 1]


# ---------------------------------------------------------------------------
# Invariants sur data/processed/etudiants.csv
# ---------------------------------------------------------------------------

FICHIER = config.DOSSIER_PROCESSED / "etudiants.csv"
sans_fichier = pytest.mark.skipif(not FICHIER.exists(), reason="data/processed/etudiants.csv absent")


@pytest.fixture(scope="module")
def propre():
    return pd.read_csv(FICHIER, dtype={"cohorte": "Int64", "age": "Int64"}, encoding=config.ENCODAGE)


@sans_fichier
def test_invariant_identifiants(propre):
    assert propre["id_etudiant"].is_unique
    assert propre["id_etudiant"].str.fullmatch(config.FORMAT_ID_ETUDIANT).all()


@sans_fichier
def test_invariant_modalites(propre):
    for colonne in etudiants.COLONNES_CATEGORIELLES:
        renseignees = propre[colonne].dropna()
        assert renseignees.isin(config.MODALITES[("etudiants", colonne)]).all(), colonne
    assert propre["cohorte"].dropna().astype(str).isin(config.MODALITES[("etudiants", "cohorte")]).all()


@sans_fichier
def test_invariant_bornes(propre):
    assert propre["age"].dropna().between(17, 35).all()
    assert propre["note_bac"].dropna().between(10, 20).all()
    assert (propre["distance_campus_km"].dropna() > 0).all()


@sans_fichier
def test_invariant_mention_coherente(propre):
    avec_note = propre.dropna(subset=["note_bac"])
    attendue = avec_note["note_bac"].map(etudiants.mention_depuis_note)
    assert (avec_note["mention_bac"] == attendue).all()
