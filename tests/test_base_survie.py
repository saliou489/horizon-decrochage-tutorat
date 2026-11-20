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


def test_abandon_date_invalide_avec_serie_arrete():
    etats = [ACTIF] * 5 + [INACTIF] * 4 + [ACTIF] * 3
    with pytest.raises(ErreurNettoyage):
        calcul(etats, (config.EVENEMENT_ABANDON_DATE_INVALIDE, None))


def test_serie_avant_un_transfert_arrete():
    etats = [ACTIF] * 3 + [INACTIF] * 4 + [ACTIF] * 5
    with pytest.raises(ErreurNettoyage):
        calcul(etats, (config.EVENEMENT_TRANSFERT, 12))


def test_serie_avant_un_abandon_sans_date_arrete():
    etats = [ACTIF] * 3 + [INACTIF] * 4 + [ACTIF] * 3
    with pytest.raises(ErreurNettoyage):
        calcul(etats, (config.EVENEMENT_ABANDON_SANS_DATE, None))


def test_trou_apres_le_debut_d_une_serie_arrete():
    # RV01-07 : semaines 10, 12, 13, 14 inactives, la semaine 11 manque. Ce ne sont pas
    # 4 semaines consécutives : le calcul doit s'arrêter au lieu de compter une série.
    semaines_avec_trou = list(range(1, 11)) + [12, 13, 14]
    etats = [ACTIF] * 9 + [INACTIF] * 4
    with pytest.raises(ErreurNettoyage):
        base_survie.t_et_e("HZ00001", semaines_avec_trou, etats, AUCUNE,
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
# Format période-personne
# ---------------------------------------------------------------------------

def periode_inventee():
    """Période-personne de 4 étudiants inventés (un par statut de tutorat).

    HZ00001 : tutoré avant T (début semaine 3, T = 6, E = 1) ;
    HZ00002 : tutorat la semaine de T (début 5, T = 5) ;
    HZ00003 : tutorat à semaine inconnue (T = 4, E = 1) ;
    HZ00004 : non tutoré (T = 4).
    Chaque étudiant a 8 semaines d'activité ; connexions = 10 × semaine + numéro de
    l'étudiant, pour reconnaître la semaine d'origine d'une valeur décalée.
    """
    base = pd.DataFrame({
        "id_etudiant": ["HZ00001", "HZ00002", "HZ00003", "HZ00004"],
        "T": [6, 5, 4, 4], "E": [1, 0, 1, 0],
        "statut_tutorat": [config.STATUT_TUTORE, config.STATUT_TUTORAT_MEME_SEMAINE,
                           config.STATUT_TUTORAT_SEMAINE_INCONNUE, config.STATUT_NON_TUTORE],
        "semaine_debut_tutorat": pd.array([3, 5, pd.NA, pd.NA], dtype="Int64"),
    })
    lignes = []
    for numero, identifiant in enumerate(base["id_etudiant"], start=1):
        for semaine in range(1, 9):
            lignes.append({"id_etudiant": identifiant, "semaine": semaine,
                           "nb_connexions_lms": 10 * semaine + numero, "devoirs_rendus": 1,
                           "note_moyenne": 10.0 + semaine, "absences": semaine % 3})
    activite = pd.DataFrame(lignes)
    for colonne in ["semaine", "nb_connexions_lms", "devoirs_rendus", "absences"]:
        activite[colonne] = activite[colonne].astype("Int64")
    activite = base_survie.ajouter_etats(activite)
    return base_survie.construire_periode_personne(base, activite).set_index(["id_etudiant", "semaine"])


def test_periode_personne_lignes_et_evenement():
    periode = periode_inventee()
    assert list(periode.columns) == config.COLONNES_PERIODE_PERSONNE[2:]
    lignes = periode.groupby(level="id_etudiant").size()
    assert list(lignes) == [6, 5, 4, 4]  # une ligne par semaine 1 … T, rien après T
    assert periode["evenement"].sum() == 2
    assert periode.loc[("HZ00001", 6), "evenement"] == 1
    assert periode.loc[("HZ00003", 4), "evenement"] == 1


def test_periode_personne_tutorat_commence():
    periode = periode_inventee()
    # Tutoré avant T : 0 jusqu'à la semaine de début incluse (semaine 3), puis 1 (D-39).
    assert list(periode.loc["HZ00001", "tutorat_commence"]) == [0, 0, 0, 1, 1, 1]
    # Tutorat la semaine de T : jamais compté comme commencé (D-37).
    assert list(periode.loc["HZ00002", "tutorat_commence"]) == [0] * 5
    # Semaine de début inconnue : vide partout.
    assert periode.loc["HZ00003", "tutorat_commence"].isna().all()
    # Non tutoré : 0 partout.
    assert list(periode.loc["HZ00004", "tutorat_commence"]) == [0] * 4


def test_periode_personne_colonnes_prec_decalees():
    periode = periode_inventee()
    semaine_1 = periode.xs(1, level="semaine")
    assert semaine_1[config.COLONNES_ACTIVITE_PREC].isna().all().all()
    for numero, identifiant in enumerate(["HZ00001", "HZ00002", "HZ00003", "HZ00004"], start=1):
        etudiant = periode.loc[identifiant]
        for semaine in etudiant.index[1:]:
            # La ligne de la semaine s porte l'activité de la semaine s − 1 du MÊME étudiant.
            assert etudiant.loc[semaine, "nb_connexions_lms_prec"] == 10 * (semaine - 1) + numero
            for colonne in config.COLONNES_ACTIVITE_SEMAINE:
                assert etudiant.loc[semaine, colonne + config.SUFFIXE_PREC] == etudiant.loc[semaine - 1, colonne]


# ---------------------------------------------------------------------------
# Covariables de la rentrée (D-43)
# ---------------------------------------------------------------------------

def test_covariables_rentree_hors_resultat_et_tutorat():
    interdites = {"T", "E", "type_evenement", "tutore", "statut_tutorat", "semaine_debut_tutorat",
                  "type_tuteur", "motif_orientation", "nb_seances"}
    for colonne in config.COVARIABLES_RENTREE:
        assert colonne not in interdites
        assert "_seuil" not in colonne
        assert "tutor" not in colonne


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
        assert base[f"T{suffixe}"].between(1, config.N_SEMAINES).all()
        assert base[f"E{suffixe}"].isin([0, 1]).all()
    # Les abandons ont E = 1 et les transferts E = 0, quel que soit le seuil.
    abandons = base["type_evenement"].isin([config.EVENEMENT_ABANDON_DECLARE, config.EVENEMENT_ABANDON_SANS_DATE,
                                            config.EVENEMENT_ABANDON_DATE_INVALIDE])
    transferts = base["type_evenement"] == config.EVENEMENT_TRANSFERT
    for colonne in ["E", "E_seuil3", "E_seuil5"]:
        assert (base.loc[abandons, colonne] == 1).all()
        assert (base.loc[transferts, colonne] == 0).all()


@sans_fichier
def test_invariant_covariables_rentree_dans_etudiants():
    colonnes_etudiants = pd.read_csv(FICHIERS[2], encoding=config.ENCODAGE, nrows=0).columns
    for colonne in config.COVARIABLES_RENTREE:
        assert colonne in colonnes_etudiants
    assert config.COLONNE_ID not in config.COVARIABLES_RENTREE


@sans_fichier
def test_invariant_colonnes_prec(periode):
    assert list(periode.columns) == config.COLONNES_PERIODE_PERSONNE
    semaine_1 = periode["semaine"] == 1
    assert semaine_1.sum() == 5000
    # etat_activite est toujours renseigné : son décalage n'est vide qu'en semaine 1.
    assert (periode["etat_activite_prec"].isna() == semaine_1).all()
    assert periode.loc[semaine_1, config.COLONNES_ACTIVITE_PREC].isna().all().all()


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
