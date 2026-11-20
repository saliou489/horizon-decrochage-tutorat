"""Tests du nettoyage de la table activite_hebdo.

Rôle du module : (1) tester les règles sur de petits DataFrames construits ici ;
(2) vérifier les invariants de data/processed/activite_hebdo.csv (ignorés tant que
le fichier n'existe pas).

Tâche couverte : DA-04.
"""

import pandas as pd
import pytest

from src import config
from src.nettoyage import activite
from src.nettoyage.commun import ErreurNettoyage, semaine_depuis_date

COLONNES = config.FICHIERS_BRUTS["activite_hebdo"]["colonnes"]
ETUDIANTS = pd.DataFrame({"id_etudiant": ["HZ00001", "HZ00002"]})
AUCUNE_SORTIE = pd.Series(dtype="int64")


def ligne(identifiant="HZ00001", semaine="1", connexions="5.0", devoirs="1", note="", absences="2"):
    """Une ligne d'activité brute (tout en texte)."""
    return {"id_etudiant": identifiant, "semaine": semaine, "nb_connexions_lms": connexions,
            "devoirs_rendus": devoirs, "note_moyenne": note, "absences": absences}


def table(*lignes):
    """DataFrame brut construit à partir de lignes."""
    return pd.DataFrame(list(lignes), columns=COLONNES)


def suivi_complet(identifiant="HZ00001", jusqua=config.N_SEMAINES):
    """Lignes valides pour les semaines 1 à jusqua."""
    return [ligne(identifiant, semaine=str(s)) for s in range(1, jusqua + 1)]


def jusqua(df, derniere_regle, sorties=AUCUNE_SORTIE):
    """Applique les règles dans l'ordre jusqu'à derniere_regle incluse ; renvoie la table."""
    df, _, _ = activite.regle_identifiants(df, ETUDIANTS)
    etapes = [
        (activite.regle_nombres, False), (activite.regle_semaines_invalides, True),
        (activite.regle_valeurs_impossibles, False), (activite.regle_notes_decalees, False),
        (activite.regle_doublons, False), (activite.regle_apres_sortie, True),
    ]
    for regle, avec_sorties in etapes:
        df = (regle(df, sorties) if avec_sorties else regle(df))[0]
        if regle is derniere_regle:
            return df
    raise ValueError("règle inconnue")


# ---------------------------------------------------------------------------
# Tests unitaires
# ---------------------------------------------------------------------------

def test_semaine_depuis_date():
    assert semaine_depuis_date("2024-10-07", "2024-10-07") == 1
    assert semaine_depuis_date("2024-10-13", "2024-10-07") == 1  # rentrée + 6 jours
    assert semaine_depuis_date("2024-10-14", "2024-10-07") == 2  # rentrée + 7 jours


def test_identifiant_inconnu_arrete():
    with pytest.raises(ErreurNettoyage):
        activite.regle_identifiants(table(ligne("HZ99999")), ETUDIANTS)


def test_entier_avec_vraie_decimale_arrete():
    with pytest.raises(ErreurNettoyage):
        activite.regle_nombres(table(ligne(connexions="3.5")))


def test_semaine_99_retiree():
    brut = table(*suivi_complet(), ligne(semaine="99"))
    df = jusqua(brut, activite.regle_nombres)
    propre, nb, _, rejets = activite.regle_semaines_invalides(df, AUCUNE_SORTIE)
    assert nb == 1 and list(rejets["semaine"]) == [99]
    assert propre["semaine"].between(1, 30).all()


def test_semaine_invalide_avec_semaine_manquante_arrete():
    lignes = [l for l in suivi_complet() if l["semaine"] != "12"] + [ligne(semaine="0")]
    df = jusqua(table(*lignes), activite.regle_nombres)
    with pytest.raises(ErreurNettoyage):
        activite.regle_semaines_invalides(df, AUCUNE_SORTIE)


def test_semaine_invalide_apres_sortie_sans_trou_acceptee():
    sorties = pd.Series({"HZ00001": 5})
    df = jusqua(table(*suivi_complet(jusqua=5), ligne(semaine="31")), activite.regle_nombres)
    propre, nb, _, _ = activite.regle_semaines_invalides(df, sorties)
    assert nb == 1 and len(propre) == 5


def test_connexions_devoirs_et_note_impossibles():
    brut = table(ligne(semaine="1", connexions="-3.0"), ligne(semaine="2", connexions="6076.0"),
                 ligne(semaine="3", connexions="26.0"), ligne(semaine="4", devoirs="7"),
                 ligne(semaine="5", note="-1"))
    propre = jusqua(brut, activite.regle_valeurs_impossibles)
    assert pd.isna(propre.loc[0, "nb_connexions_lms"]) and pd.isna(propre.loc[1, "nb_connexions_lms"])
    assert propre.loc[2, "nb_connexions_lms"] == 26  # connexions plausibles conservées
    assert pd.isna(propre.loc[3, "devoirs_rendus"])
    assert pd.isna(propre.loc[4, "note_moyenne"])
    assert len(propre) == 5


def test_note_122_devient_12_2():
    propre = jusqua(table(ligne(note="122"), ligne(semaine="2", note="12,5")), activite.regle_notes_decalees)
    assert propre.loc[0, "note_moyenne"] == pytest.approx(12.2)
    assert propre.loc[1, "note_moyenne"] == pytest.approx(12.5)


def test_note_toujours_hors_bornes_arrete():
    df = jusqua(table(ligne(note="999")), activite.regle_valeurs_impossibles)
    with pytest.raises(ErreurNettoyage):
        activite.regle_notes_decalees(df)


def test_quasi_doublon_garde_le_maximum_d_activite():
    # La plus grande valeur est dans la PREMIÈRE copie : « garder la dernière ligne » donnerait
    # 0 connexion, alors que D-20 demande le maximum (RV01-06).
    brut = table(ligne(connexions="5.0", devoirs="1", note="11"),
                 ligne(connexions="0.0", devoirs="0", note="14"),
                 ligne(semaine="2"), ligne(semaine="2"))
    df = jusqua(brut, activite.regle_notes_decalees)
    propre, _, entrees = activite.regle_doublons(df)
    assert len(propre) == 2
    semaine_1 = propre[propre["semaine"] == 1].iloc[0]
    assert semaine_1["nb_connexions_lms"] == 5 and semaine_1["devoirs_rendus"] == 1
    assert semaine_1["note_moyenne"] == pytest.approx(11)  # note de la première ligne
    assert [e["lignes"] for e in entrees] == [1, 1, 1]  # 1 identique, 1 couple fusionné, 1 « 0 contre 5 »


def test_quasi_doublon_avec_une_connexion_manquante():
    # Une copie sans valeur de connexions : on garde la plus grande valeur RENSEIGNÉE (D-20).
    brut = table(ligne(connexions="3.0", devoirs="1", note="11"),
                 ligne(connexions="", devoirs="0", note="14"))
    df = jusqua(brut, activite.regle_notes_decalees)
    propre, _, entrees = activite.regle_doublons(df)
    assert len(propre) == 1
    assert propre.loc[0, "nb_connexions_lms"] == 3 and propre.loc[0, "devoirs_rendus"] == 1
    assert propre.loc[0, "note_moyenne"] == pytest.approx(11)
    assert [e["lignes"] for e in entrees] == [0, 1, 0]


def test_quasi_doublon_absences_differentes_arrete():
    df = jusqua(table(ligne(absences="2"), ligne(absences="3")), activite.regle_notes_decalees)
    with pytest.raises(ErreurNettoyage):
        activite.regle_doublons(df)


def test_activite_apres_la_sortie_retiree():
    sorties = pd.Series({"HZ00001": 3})
    brut = table(*suivi_complet(jusqua=5), *suivi_complet("HZ00002", jusqua=5))
    df = jusqua(brut, activite.regle_doublons, sorties)
    propre, nb, _, rejets = activite.regle_apres_sortie(df, sorties)
    assert nb == 2 and list(rejets["semaine"]) == [4, 5]
    assert propre[propre["id_etudiant"] == "HZ00001"]["semaine"].max() == 3
    assert (propre["id_etudiant"] == "HZ00002").sum() == 5  # étudiant sans sortie : rien retiré


# ---------------------------------------------------------------------------
# Invariants sur data/processed/activite_hebdo.csv
# ---------------------------------------------------------------------------

FICHIER = config.DOSSIER_PROCESSED / "activite_hebdo.csv"
FICHIER_ETUDIANTS = config.DOSSIER_PROCESSED / "etudiants.csv"
FICHIER_INSCRIPTIONS = config.DOSSIER_PROCESSED / "inscriptions.csv"
sans_fichier = pytest.mark.skipif(
    not (FICHIER.exists() and FICHIER_ETUDIANTS.exists() and FICHIER_INSCRIPTIONS.exists()),
    reason="tables nettoyées absentes")


@pytest.fixture(scope="module")
def propre():
    return pd.read_csv(FICHIER, encoding=config.ENCODAGE)


@sans_fichier
def test_invariant_cle_unique(propre):
    assert not propre.duplicated(["id_etudiant", "semaine"]).any()


@sans_fichier
def test_invariant_bornes(propre):
    assert propre["semaine"].between(1, config.N_SEMAINES).all()
    assert propre["nb_connexions_lms"].dropna().between(0, config.CONNEXIONS_MAX_PLAUSIBLE).all()
    assert propre["devoirs_rendus"].dropna().between(0, 2).all()
    assert propre["note_moyenne"].dropna().between(0, 20).all()
    assert propre["absences"].dropna().between(0, 20).all()


@sans_fichier
def test_invariant_identifiants_connus(propre):
    etudiants = pd.read_csv(FICHIER_ETUDIANTS, encoding=config.ENCODAGE)
    assert set(propre["id_etudiant"]) <= set(etudiants["id_etudiant"])


@sans_fichier
def test_invariant_rien_apres_la_sortie(propre):
    from src.nettoyage.commun import semaines_de_sortie
    inscriptions = pd.read_csv(FICHIER_INSCRIPTIONS, dtype=str, encoding=config.ENCODAGE)
    sortie = propre["id_etudiant"].map(semaines_de_sortie(inscriptions))
    assert not (sortie.notna() & (propre["semaine"] > sortie)).any()
