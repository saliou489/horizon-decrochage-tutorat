"""Commande unique qui relance tout le pipeline du projet Horizon.

Rôle du module : enchaîner les étapes dans l'ordre : nettoyage des 5 tables, puis
construction de T et E (base_survie.csv, base_periode_personne.csv), puis modèles
prédictifs de survie entraînés sur 2024 et testés sur 2025, puis effet du tutorat, puis
entrées des fiches d'alerte (résultats dans data/processed/resultats/).
run_all.py n'appelle JAMAIS l'API du LLM : la génération des fiches est une commande
séparée (python -m src.llm --generer), et les fiches générées sont enregistrées dans le
dépôt (D-65, point 5). Aucune clé d'API n'est donc nécessaire pour tout relancer.
Lancement depuis la racine du dépôt : python run_all.py

Tâches couvertes : DA-02 à DA-07, SV-03, SV-04, CA-04, CA-05, LL-01.
"""

from src import base_survie, causal, llm, ml_survie
from src.nettoyage import lancer_nettoyage


def main():
    """Lance toutes les étapes du pipeline, dans l'ordre."""
    lancer_nettoyage()
    base_survie.lancer()
    ml_survie.lancer()
    causal.lancer()
    llm.lancer_entrees()


if __name__ == "__main__":
    main()
