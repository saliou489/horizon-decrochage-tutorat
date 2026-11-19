"""Tests du nettoyage et de la pseudonymisation de la table messages.

Rôle du module : (1) tester les règles sur des messages INVENTÉS (jamais tirés des
vraies données) ; (2) vérifier les invariants de data/processed/messages.csv
(ignorés tant que le fichier n'existe pas).

Tâche couverte : DA-05.
"""

import pandas as pd
import pytest

from src import config
from src.nettoyage import messages
from src.nettoyage.commun import ErreurNettoyage

COLONNES = config.FICHIERS_BRUTS["messages"]["colonnes"]
ETUDIANTS = pd.DataFrame({"id_etudiant": ["HZ00001", "HZ00002"]})


def table(*textes, identifiant="HZ00001"):
    """Table brute de messages inventés, un par texte."""
    lignes = [[f"M9{i:04d}", identifiant, "3", "forum", texte] for i, texte in enumerate(textes)]
    return pd.DataFrame(lignes, columns=COLONNES)


# ---------------------------------------------------------------------------
# Tests unitaires
# ---------------------------------------------------------------------------

def test_reparation_de_l_encodage():
    casse = "J'ai trouvé la salle.".encode("utf-8").decode("cp1252")  # fabrique « trouvÃ© »
    assert "Ã" in casse
    propre, nb, _ = messages.regle_encodage(table(casse))
    assert propre.loc[0, "texte"] == "J'ai trouvé la salle." and nb == 1


def test_message_point_retire():
    propre, nb, _, rejets = messages.regle_messages_vides(table(".", "   ", "Bonjour."))
    assert list(propre["texte"]) == ["Bonjour."]
    assert nb == 2 and len(rejets) == 2


def test_nom_et_telephone_remplaces():
    texte, comptes = messages.pseudonymiser("Je suis Awa Ndiaye, appelez-moi au 77 123 45 67.")
    assert texte == "Je suis [NOM], appelez-moi au [TEL]."
    assert comptes[config.BALISE_NOM] == 1 and comptes[config.BALISE_TELEPHONE] == 1


def test_email_remplace():
    texte, _ = messages.pseudonymiser("Mon mail : awa.ndiaye@exemple.sn")
    assert texte == "Mon mail : [EMAIL]"


def test_nom_compose_apres_c_est():
    texte, _ = messages.pseudonymiser("Bonjour, c'est Marie-Anne Diop. Merci.")
    assert texte == "Bonjour, c'est [NOM]. Merci."


def test_telephone_avec_indicatif_et_points():
    texte, _ = messages.pseudonymiser("Joignable au +221 78.765.43.21 le soir.")
    assert texte == "Joignable au [TEL] le soir."


def test_je_suis_decourage_inchange():
    texte, comptes = messages.pseudonymiser("Je suis découragé après le partiel.")
    assert texte == "Je suis découragé après le partiel."
    assert sum(comptes.values()) == 0


def test_controle_residuel_arrete_sur_un_numero_restant():
    # Un numéro fixe (33…) n'est pas reconnu comme téléphone mobile : le contrôle doit l'attraper.
    with pytest.raises(ErreurNettoyage):
        messages.regle_pseudonymisation(table("Appelez le 33 821 00 00 svp."))


def test_controles_de_structure_arretent():
    with pytest.raises(ErreurNettoyage):
        messages.regle_controles(table("Bonjour.", identifiant="HZ99999"), ETUDIANTS)


# ---------------------------------------------------------------------------
# Invariants sur data/processed/messages.csv
# ---------------------------------------------------------------------------

FICHIER = config.DOSSIER_PROCESSED / "messages.csv"
FICHIER_ETUDIANTS = config.DOSSIER_PROCESSED / "etudiants.csv"
sans_fichier = pytest.mark.skipif(not (FICHIER.exists() and FICHIER_ETUDIANTS.exists()),
                                  reason="tables nettoyées absentes")


@pytest.fixture(scope="module")
def propre():
    return pd.read_csv(FICHIER, dtype=str, keep_default_na=False, encoding=config.ENCODAGE)


@sans_fichier
def test_invariant_aucune_donnee_personnelle(propre):
    assert not propre["texte"].str.contains("@", regex=False).any()
    assert not propre["texte"].str.contains(config.MOTIF_RESIDU_CHIFFRES, regex=True).any()


@sans_fichier
def test_invariant_textes_non_vides_et_encodage(propre):
    assert propre["texte"].str.contains(config.MOTIF_ALPHANUMERIQUE, regex=True).all()
    assert not propre["texte"].str.contains("Ã", regex=False).any()


@sans_fichier
def test_invariant_identifiants(propre):
    etudiants = pd.read_csv(FICHIER_ETUDIANTS, dtype=str, encoding=config.ENCODAGE)
    assert propre["id_message"].is_unique
    assert set(propre["id_etudiant"]) <= set(etudiants["id_etudiant"])
