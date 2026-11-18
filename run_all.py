"""Commande unique qui relance tout le pipeline du projet Horizon.

Rôle du module : enchaîner les étapes dans l'ordre. Pour l'instant, seul le
nettoyage existe ; les étapes suivantes (base de survie, modèles, causal, LLM)
seront ajoutées au fil des tâches.
Lancement depuis la racine du dépôt : python run_all.py

Tâche couverte : DA-02.
"""

from src.nettoyage import lancer_nettoyage


def main():
    """Lance toutes les étapes du pipeline, dans l'ordre."""
    lancer_nettoyage()


if __name__ == "__main__":
    main()
