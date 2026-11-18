"""Test d'intégrité des fichiers bruts.

Rôle du module : prouver que data/raw/ n'a jamais été modifié, en comparant
l'empreinte SHA-256 de chaque fichier à celle inscrite dans data/raw_sha256.txt.

Tâche couverte : GP-01.
"""

import hashlib

import pytest

from src import config


def lire_empreintes_attendues():
    """Lit data/raw_sha256.txt.

    Entrée : aucune (chemin pris dans config).
    Sortie : dictionnaire {nom de fichier: empreinte SHA-256 attendue}.
    Format d'une ligne : « <empreinte>  <nom du fichier> » (format de sha256sum).
    """
    empreintes = {}
    texte = config.FICHIER_SHA256.read_text(encoding=config.ENCODAGE)
    for ligne in texte.splitlines():
        if ligne.strip() == "":
            continue
        empreinte, nom_fichier = ligne.split(maxsplit=1)
        empreintes[nom_fichier.strip()] = empreinte.lower()
    return empreintes


def calculer_sha256(chemin):
    """Calcule l'empreinte SHA-256 d'un fichier, lu en binaire.

    La lecture binaire compte chaque octet tel quel : une simple conversion des fins
    de ligne ou de l'encodage changerait l'empreinte.
    """
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


EMPREINTES = lire_empreintes_attendues()


def test_registre_couvre_tous_les_fichiers_bruts():
    """Chaque fichier de data/raw/ doit avoir une empreinte inscrite, et inversement."""
    fichiers_presents = {chemin.name for chemin in config.DOSSIER_RAW.iterdir() if chemin.is_file()}
    assert fichiers_presents == set(EMPREINTES)


@pytest.mark.parametrize("nom_fichier", sorted(EMPREINTES))
def test_fichier_brut_intact(nom_fichier):
    """Le fichier brut a exactement l'empreinte SHA-256 inscrite dans le registre."""
    chemin = config.DOSSIER_RAW / nom_fichier
    assert chemin.exists(), f"Fichier brut absent : {nom_fichier}"
    assert calculer_sha256(chemin) == EMPREINTES[nom_fichier]
