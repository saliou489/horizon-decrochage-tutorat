"""Nettoyage des tables brutes : data/raw/ -> data/processed/.

Rôle du module : enchaîner le nettoyage des tables déjà prises en charge (pour
l'instant « etudiants ») et régénérer docs/journal_nettoyage.md.
Lancement depuis la racine du dépôt : python -m src.nettoyage

Tâches couvertes : DA-02 (les tables suivantes seront ajoutées en DA-03 à DA-05).
"""

from src.nettoyage import commun, etudiants


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


def lancer_nettoyage():
    """Point d'entrée : nettoie toutes les tables prises en charge et écrit le journal."""
    resultats = [nettoyer_etudiants()]
    chemin = commun.ecrire_journal(resultats)
    for resultat in resultats:
        print(f"{resultat['table']} : {resultat['avant']['lignes']} lignes -> {resultat['apres']['lignes']} lignes")
        for regle, nb in resultat["lignes_touchees"].items():
            print(f"  {regle} : {nb} lignes touchées")
    print(f"Journal écrit dans {chemin.name}")
    return resultats
