"""Tests de la construction de T, E, base_survie et période-personne.

Rôle du module : (1) tester les règles sur des suites d'états et des étudiants
inventés ; (2) vérifier les invariants de base_survie.csv et base_periode_personne.csv
(ignorés tant que les fichiers n'existent pas).

Tâche couverte : DA-07.
"""

import pandas as pd
import pytest

from src import base_survie, config
from src.nettoyage.commun import ErreurNettoyage

ACTIF, INACTIF, INCONNU = config.ETAT_ACTIF, config.ETAT_INACTIF, config.ETAT_INCONNU
AUCUNE = ("aucune", None)


def semaines(n):
    """Semaines 1 à n."""
    return list(range(1, n + 1))


def calcul(etats, situation=AUCUNE, seuil=config.SEUIL_INACTIVITE, lecture=config.LECTURE_INCONNU_REFERENCE):
    """T, E, type_evenement d'un étudiant inventé dont les états sont donnés semaine par semaine."""
    return base_survie.t_et_e("HZ00001", semaines(len(etats)), etats, situation, seuil, lecture)


# ---------------------------------------------------------------------------
# États et séries
# ---------------------------------------------------------------------------

def test_etat_semaine():
    assert base_survie.etat_semaine(3, 0) == ACTIF
    assert base_survie.etat_semaine(pd.NA, 1) == ACTIF
    assert base_survie.etat_semaine(0, 0) == INACTIF
    assert base_survie.etat_semaine(pd.NA, 0) == INCONNU
    assert base_survie.etat_semaine(0, pd.NA) == INCONNU


def test_serie_en_semaine_11():
    etats = [ACTIF] * 10 + [INACTIF] * 4 + [ACTIF] * 16
    assert base_survie.premiere_serie(etats, 4) == 11
    assert calcul(etats) == (11, 1, config.EVENEMENT_DECROCHAGE_SILENCIEUX)


def test_serie_coupee_par_la_fin_du_suivi():
    etats = [ACTIF] * 27 + [INACTIF] * 3
    assert base_survie.premiere_serie(etats, 4) is None
    assert calcul(etats) == (30, 0, config.EVENEMENT_FIN_DE_SUIVI)


def test_semaine_inconnue_selon_la_lecture():
    etats = [ACTIF] * 5 + [INACTIF, INACTIF, INCONNU, INACTIF, INACTIF] + [ACTIF] * 20
    assert base_survie.premiere_serie(etats, 4, config.LECTURE_INCONNU_REFERENCE) is None
    assert base_survie.premiere_serie(etats, 4, config.LECTURE_INCONNU_SENSIBILITE) == 6


def test_seuils_3_et_5():
    etats = [ACTIF] * 5 + [INACTIF] * 3 + [ACTIF] * 5 + [INACTIF] * 5 + [ACTIF] * 12
    assert base_survie.premiere_serie(etats, 3) == 6
    assert base_survie.premiere_serie(etats, 4) == 14
    assert base_survie.premiere_serie(etats, 5) == 14


# ---------------------------------------------------------------------------
# T et E selon la situation de sortie
# ---------------------------------------------------------------------------

def test_abandon_date():
    etats = [ACTIF] * 12
    assert calcul(etats, (config.EVENEMENT_ABANDON_DECLARE, 12)) == (12, 1, config.EVENEMENT_ABANDON_DECLARE)


def test_abandon_sans_date_derniere_semaine_d_activite():
    etats = [ACTIF] * 9
    assert calcul(etats, (config.EVENEMENT_ABANDON_SANS_DATE, None)) == (9, 1, config.EVENEMENT_ABANDON_SANS_DATE)


def test_abandon_date_invalide():
    etats = [ACTIF] * 15
    assert calcul(etats, (config.EVENEMENT_ABANDON_DATE_INVALIDE, None)) == (
        15, 1, config.EVENEMENT_ABANDON_DATE_INVALIDE)
    with pytest.raises(ErreurNettoyage):
        calcul([ACTIF] * 30, (config.EVENEMENT_ABANDON_DATE_INVALIDE, None))


def test_transfert_censure():
    assert calcul([ACTIF] * 8, (config.EVENEMENT_TRANSFERT, 8)) == (8, 0, config.EVENEMENT_TRANSFERT)


def test_perdu_de_vue():
    assert calcul([ACTIF] * 20) == (20, 0, config.EVENEMENT_PERDU_DE_VUE)


def test_serie_avant_un_abandon_declare_arrete():
    etats = [ACTIF] * 3 + [INACTIF] * 4 + [ACTIF] * 3
    with pytest.raises(ErreurNettoyage):
        calcul(etats, (config.EVENEMENT_ABANDON_DECLARE, 10))


def test_semaine_manquante_arrete():
    with pytest.raises(ErreurNettoyage):
        base_survie.t_et_e("HZ00001", [1, 2, 4], [ACTIF] * 3, (config.EVENEMENT_ABANDON_DECLARE, 4),
                           config.SEUIL_INACTIVITE, config.LECTURE_INCONNU_REFERENCE)


# ---------------------------------------------------------------------------
# Tutorat
# ---------------------------------------------------------------------------

def test_statut_tutorat():
    assert base_survie.statut_tutorat(5, True, 10) == config.STATUT_TUTORE
    assert base_survie.statut_tutorat(10, True, 10) == config.STATUT_TUTORAT_MEME_SEMAINE
    assert base_survie.statut_tutorat(12, True, 10) == config.STATUT_TUTORAT_APRES_T
    assert base_survie.statut_tutorat(pd.NA, True, 10) == config.STATUT_TUTORAT_SEMAINE_INCONNUE
    assert base_survie.statut_tutorat(pd.NA, False, 10) == config.STATUT_NON_TUTORE


def test_colonne_tutore():
    base = pd.DataFrame({"id_etudiant": ["HZ00001", "HZ00002", "HZ00003", "HZ00004"], "T": [10, 10, 10, 10]})
    tutorat = pd.DataFrame({"id_etudiant": ["HZ00001", "HZ00002", "HZ00003"],
                            "semaine_debut": pd.array([4, 10, pd.NA], dtype="Int64"),
                            "type_tuteur": ["pair"] * 3, "motif_orientation": ["notes faibles"] * 3,
                            "nb_seances": pd.array([5, 5, 5], dtype="Int64")})
    resultat = base_survie.ajouter_tutorat(base, tutorat).set_index("id_etudiant")
    assert list(resultat["tutore"]) == [1, 0, 1, 0]
    assert list(resultat["statut_tutorat"]) == [config.STATUT_TUTORE, config.STATUT_TUTORAT_MEME_SEMAINE,
                                                config.STATUT_TUTORAT_SEMAINE_INCONNUE, config.STATUT_NON_TUTORE]


# ---------------------------------------------------------------------------
# Invariants sur les fichiers produits
# ---------------------------------------------------------------------------

FICHIERS = [config.FICHIER_BASE_SURVIE, config.FICHIER_PERIODE_PERSONNE, config.DOSSIER_PROCESSED / "etudiants.csv"]
sans_fichier = pytest.mark.skipif(not all(f.exists() for f in FICHIERS), reason="bases absentes")


@pytest.fixture(scope="module")
def base():
    return pd.read_csv(config.FICHIER_BASE_SURVIE, dtype={"semaine_debut_tutorat": "Int64"},
                       encoding=config.ENCODAGE)


@pytest.fixture(scope="module")
def periode():
    return pd.read_csv(config.FICHIER_PERIODE_PERSONNE, dtype={"tutorat_commence": "Int64"},
                       encoding=config.ENCODAGE)


@sans_fichier
def test_invariant_aucun_etudiant_perdu(base):
    etudiants = pd.read_csv(FICHIERS[2], encoding=config.ENCODAGE)
    assert len(base) == len(etudiants) == 5000
    assert base["id_etudiant"].is_unique
    assert set(base["id_etudiant"]) == set(etudiants["id_etudiant"])
    assert list(base.columns) == config.COLONNES_BASE_SURVIE


@sans_fichier
def test_invariant_t_et_e(base):
    for suffixe in ["", "_seuil3", "_seuil5"]:
        assert base[f"T{suffixe}"].between(1, config.N_SEMAINES).all()
        assert base[f"E{suffixe}"].isin([0, 1]).all()
    attendu = base["type_evenement"].isin(config.TYPES_AVEC_EVENEMENT).astype(int)
    assert (base["E"] == attendu).all()
    assert base["type_evenement"].isin(config.TYPES_AVEC_EVENEMENT + config.TYPES_CENSURES).all()


@sans_fichier
def test_invariant_sensibilite_coherente(base):
    # Les sorties déclarées ne dépendent pas du seuil : seuls les décrochages silencieux
    # et les fins de suivi peuvent changer.
    declares = base["type_evenement"].isin([config.EVENEMENT_ABANDON_DECLARE, config.EVENEMENT_ABANDON_SANS_DATE,
                                            config.EVENEMENT_ABANDON_DATE_INVALIDE, config.EVENEMENT_TRANSFERT])
    for suffixe in ["_seuil3", "_seuil5"]:
        assert (base.loc[declares, f"E{suffixe}"] == base.loc[declares, "E"]).all()
        assert (base.loc[declares, f"T{suffixe}"] == base.loc[declares, "T"]).all()


@sans_fichier
def test_invariant_periode_personne(base, periode):
    lignes = periode.groupby("id_etudiant").size()
    assert (lignes.reindex(base["id_etudiant"]).values == base["T"].values).all()
    evenements = periode.groupby("id_etudiant")["evenement"].sum().reindex(base["id_etudiant"])
    assert (evenements.values == base["E"].values).all()
    derniere = periode.loc[periode["evenement"] == 1]
    t_par_etudiant = base.set_index("id_etudiant")["T"]
    assert (derniere["semaine"].values == derniere["id_etudiant"].map(t_par_etudiant).values).all()


@sans_fichier
def test_invariant_tutorat_commence(base, periode):
    statut = periode["id_etudiant"].map(base.set_index("id_etudiant")["statut_tutorat"])
    inconnu = statut == config.STATUT_TUTORAT_SEMAINE_INCONNUE
    assert periode.loc[inconnu, "tutorat_commence"].isna().all()
    assert (periode.loc[~inconnu & (statut != config.STATUT_TUTORE), "tutorat_commence"] == 0).all()
    tutores = periode[statut == config.STATUT_TUTORE]
    debut = tutores["id_etudiant"].map(base.set_index("id_etudiant")["semaine_debut_tutorat"])
    assert (tutores["tutorat_commence"] == (tutores["semaine"] > debut).astype(int)).all()
