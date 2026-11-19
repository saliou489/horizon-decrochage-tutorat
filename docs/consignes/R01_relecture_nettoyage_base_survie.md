# R01 — Relecture du nettoyage et de la construction de base_survie

Suis `docs/consignes/R00_mission_relecteur.md`. Prérequis : consignes C01 à C06 exécutées.

## Périmètre
- Code : `src/config.py`, `src/audit.py`, `src/nettoyage/`, `src/base_survie.py`, `run_all.py`.
- Tests : `tests/`.
- Documents : `docs/journal_nettoyage.md`, `notebooks/01_nettoyage.ipynb`, `README.md` (installation, déclaration d'usage de l'IA).
- Données produites : `data/processed/` (tables nettoyées, rejets, `base_survie.csv`, `base_periode_personne.csv`).
- Référentiel : cahier des charges (§4, §6, annexe A), `CLAUDE.md` (§5, §6), décisions D-01 à D-41, consignes C01 à C06.

## Questions à traiter en priorité
1. Une règle de nettoyage peut-elle masquer ou créer une anomalie (ordre des étapes, valeur mise à manquant qui change T ou E) ?
2. La construction de T et E respecte-t-elle exactement le §5 de `CLAUDE.md` et les décisions D-30 à D-37 ? Cherche des cas limites qui la mettraient en défaut : inactivité seulement en fin de suivi, semaine inconnue au milieu d'une série, sortie en semaine 1, étudiant reconstitué (D-17), abandon daté hors suivi (D-33), tutorat commencé la semaine de T.
3. `base_periode_personne.csv` est-il cohérent avec `base_survie.csv` (lignes par étudiant, ligne d'événement, `tutorat_commence`) ?
4. `base_survie.csv` contient-il une variable qui ferait fuir l'information du futur (D-36) ?
5. Données personnelles : aucune ne doit rester dans `data/processed/`, les rejets, le journal, le notebook ou les tests. Les données brutes (`data/raw/`) contiennent des données personnelles **fictives** (jeu synthétique fourni par l'enseignant) dans un dépôt public : est-ce signalé clairement aux lecteurs ? Si non, propose le texte à ajouter.
6. Quels tests ne protègent pas vraiment leur règle ?
7. Reproductibilité depuis ton clone : installation, `python run_all.py` (durée), `pytest`, notebook exécutable de haut en bas.
8. Lisibilité : les 3 fonctions les plus difficiles à expliquer en soutenance, et pourquoi.

## Livraison
- Rapport `docs/revues/RV01_nettoyage_base_survie.md`, commit `RV01 : relecture du nettoyage et de base_survie`, push sur `main`.
