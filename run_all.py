"""Commande unique qui relance tout le pipeline du projet Horizon.

Rôle du module : enchaîner les étapes dans l'ordre : nettoyage des 5 tables, puis
construction de T et E (base_survie.csv, base_periode_personne.csv), puis modèles
prédictifs de survie entraînés sur 2024 et testés sur 2025 (data/processed/resultats/).
Les étapes suivantes (causal, LLM) seront ajoutées au fil des tâches.
Lancement depuis la racine du dépôt : python run_all.py

Tâches couvertes : DA-02 à DA-07, SV-03, SV-04.
"""

from src import base_survie, ml_survie
from src.nettoyage import lancer_nettoyage


def main():
    """Lance toutes les étapes du pipeline, dans l'ordre."""
    lancer_nettoyage()
    base_survie.lancer()
    ml_survie.lancer()


if __name__ == "__main__":
    main()
