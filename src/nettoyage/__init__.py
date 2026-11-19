"""Nettoyage des tables brutes : data/raw/ -> data/processed/.

Rôle du module : enchaîner le nettoyage des tables déjà prises en charge
(« etudiants », puis « inscriptions », qui a besoin de la première) et régénérer
docs/journal_nettoyage.md.
Lancement depuis la racine du dépôt : python -m src.nettoyage

Tâches couvertes : DA-02 à DA-05 (tables), DA-06 (journal complet).
"""

import pandas as pd

from src import config
from src.nettoyage import activite, commun, etudiants, inscriptions, messages, tutorat


def nettoyer_etudiants():
    """Nettoie etudiants, écrit data/processed/etudiants.csv et renvoie le résultat du journal."""
    brut = commun.lire_brut(etudiants.TABLE)
    propre, entrees, lignes_touchees = etudiants.nettoyer(brut)
    commun.ecrire_table(propre, etudiants.TABLE)
    return {
        "table": etudiants.TABLE,
        "entrees": entrees,
        "avant": commun.profil(etudiants.profil_brut_comparable(brut)),
        "apres": commun.profil(propre),
        "colonnes": list(propre.columns),
        "lignes_touchees": lignes_touchees,
    }


def lire_etudiants_propres():
    """Relit data/processed/etudiants.csv (prérequis du nettoyage des inscriptions)."""
    chemin = config.DOSSIER_PROCESSED / f"{etudiants.TABLE}.csv"
    return pd.read_csv(chemin, sep=config.SEPARATEUR_PROCESSED, dtype={"cohorte": "Int64", "age": "Int64"},
                       encoding=config.ENCODAGE)


def nettoyer_inscriptions():
    """Nettoie inscriptions, écrit la table et ses rejets, renvoie le résultat du journal."""
    brut = commun.lire_brut(inscriptions.TABLE)
    propre, rejets, entrees, lignes_touchees = inscriptions.nettoyer(brut, lire_etudiants_propres())
    commun.ecrire_table(propre, inscriptions.TABLE)
    commun.ecrire_rejets(rejets, config.FICHIER_REJETS_INSCRIPTIONS)
    return {
        "table": inscriptions.TABLE,
        "rejets": {config.FICHIER_REJETS_INSCRIPTIONS.name: len(rejets)},
        "entrees": entrees,
        "avant": commun.profil(brut),
        "apres": commun.profil(propre),
        "colonnes": list(propre.columns),
        "lignes_touchees": lignes_touchees,
        "effectifs": inscriptions.effectifs(propre),
    }


def lire_inscriptions_propres():
    """Relit data/processed/inscriptions.csv (prérequis : semaines de sortie)."""
    chemin = config.DOSSIER_PROCESSED / f"{inscriptions.TABLE}.csv"
    return pd.read_csv(chemin, sep=config.SEPARATEUR_PROCESSED, dtype=str, encoding=config.ENCODAGE)


def nettoyer_activite():
    """Nettoie activite_hebdo, écrit la table et ses deux fichiers de rejets."""
    brut = commun.lire_brut(activite.TABLE)
    sorties = commun.semaines_de_sortie(lire_inscriptions_propres())
    propre, rejets, entrees, lignes_touchees = activite.nettoyer(brut, lire_etudiants_propres(), sorties)
    commun.ecrire_table(propre, activite.TABLE)
    commun.ecrire_rejets(rejets["semaine_invalide"], config.FICHIER_REJETS_ACTIVITE_SEMAINE)
    commun.ecrire_rejets(rejets["apres_sortie"], config.FICHIER_REJETS_ACTIVITE_SORTIE)
    return {
        "table": activite.TABLE,
        "rejets": {config.FICHIER_REJETS_ACTIVITE_SEMAINE.name: len(rejets["semaine_invalide"]),
                   config.FICHIER_REJETS_ACTIVITE_SORTIE.name: len(rejets["apres_sortie"])},
        "entrees": entrees,
        "avant": commun.profil(brut, autres_colonnes_cle=activite.CLE[1:]),
        "apres": commun.profil(propre, autres_colonnes_cle=activite.CLE[1:]),
        "colonnes": list(propre.columns),
        "lignes_touchees": lignes_touchees,
    }


def nettoyer_tutorat():
    """Nettoie tutorat, écrit la table et ses rejets."""
    brut = commun.lire_brut(tutorat.TABLE)
    sorties = commun.semaines_de_sortie(lire_inscriptions_propres())
    propre, rejets, entrees, lignes_touchees = tutorat.nettoyer(brut, lire_etudiants_propres(), sorties)
    commun.ecrire_table(propre, tutorat.TABLE)
    commun.ecrire_rejets(rejets, config.FICHIER_REJETS_TUTORAT)
    return {
        "table": tutorat.TABLE,
        "rejets": {config.FICHIER_REJETS_TUTORAT.name: len(rejets)},
        "entrees": entrees,
        "avant": commun.profil(commun.renommer_par_position(brut, tutorat.TABLE)),
        "apres": commun.profil(propre),
        "colonnes": list(propre.columns),
        "lignes_touchees": lignes_touchees,
        "effectifs": tutorat.effectifs(propre),
    }


def nettoyer_messages():
    """Nettoie et pseudonymise messages, écrit la table et ses rejets (messages vides)."""
    brut = commun.lire_brut(messages.TABLE)
    propre, rejets, entrees, lignes_touchees = messages.nettoyer(brut, lire_etudiants_propres())
    commun.ecrire_table(propre, messages.TABLE)
    commun.ecrire_rejets(rejets, config.FICHIER_REJETS_MESSAGES)
    return {
        "table": messages.TABLE,
        "rejets": {config.FICHIER_REJETS_MESSAGES.name: len(rejets)},
        "entrees": entrees,
        "avant": commun.profil(brut, colonne_id="id_message"),
        "apres": commun.profil(propre, colonne_id="id_message"),
        "colonnes": list(propre.columns),
        "lignes_touchees": lignes_touchees,
        "effectifs": messages.effectifs(propre),
    }


def lancer_nettoyage():
    """Point d'entrée : nettoie toutes les tables prises en charge et écrit le journal."""
    resultats = [nettoyer_etudiants(), nettoyer_inscriptions(), nettoyer_activite(), nettoyer_tutorat(),
                 nettoyer_messages()]
    chemin = commun.ecrire_journal(resultats)
    for resultat in resultats:
        print(f"{resultat['table']} : {resultat['avant']['lignes']} lignes -> {resultat['apres']['lignes']} lignes")
        for regle, nb in resultat["lignes_touchees"].items():
            print(f"  {regle} : {nb} lignes touchées")
    print(f"Journal écrit dans {chemin.name}")
    return resultats
