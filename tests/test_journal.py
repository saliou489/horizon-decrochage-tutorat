"""Tests du journal de nettoyage complet.

Rôle du module : vérifier que chaque anomalie constatée par l'audit (docs/audit_qualite.md)
est citée dans docs/journal_nettoyage.md, soit par un traitement, soit dans la section
« Anomalies constatées sans traitement » ; et que le contrôle s'arrête sur un code oublié.

Tâche couverte : DA-06.
"""

import re

import pytest

from src import config
from src.nettoyage import commun
from src.nettoyage.commun import ErreurNettoyage

sans_journal = pytest.mark.skipif(not (config.FICHIER_JOURNAL.exists() and config.FICHIER_AUDIT.exists()),
                                  reason="journal ou audit absent")


@sans_journal
def test_chaque_code_de_l_audit_est_dans_le_journal():
    journal = config.FICHIER_JOURNAL.read_text(encoding=config.ENCODAGE)
    cites = set(re.findall(config.MOTIF_CODE_AUDIT, journal))
    codes = commun.codes_de_l_audit()
    assert len(codes) > 0
    assert [c for c in codes if c not in cites] == []


@sans_journal
def test_codes_sans_traitement_existent_dans_l_audit():
    """La liste des anomalies sans traitement ne cite que des codes réels de l'audit."""
    assert set(config.ANOMALIES_SANS_TRAITEMENT) <= set(commun.codes_de_l_audit())


@sans_journal
def test_code_oublie_arrete():
    # Seulement deux traitements cités : tous les autres codes sont « oubliés ».
    entrees = [commun.entree_journal("etudiants", "Test (ETU-01)", 1, "x", "D-06"),
               commun.entree_journal("etudiants", "Test (ETU-02)", 1, "x", "D-06")]
    with pytest.raises(ErreurNettoyage):
        commun.verifier_codes(entrees)
