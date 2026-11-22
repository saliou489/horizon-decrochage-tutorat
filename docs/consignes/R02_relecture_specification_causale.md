# R02 — Relecture de la spécification causale et de la conception (CA-01 à CA-03), avant le calcul de l'effet

Suis `docs/consignes/R00_mission_relecteur.md`. Prérequis : consigne C10 exécutée (commits `921ec62` à `211cfbf`).

**Règle propre à cette relecture (D-59)** : la méthode causale doit être figée **avant** que quiconque voie le résultat. Tu ne calcules donc **aucune** comparaison de T, E, de la survie ou du décrochage entre tutorés et non tutorés, même « pour vérifier ». Si une question ne peut être tranchée qu'en regardant ce résultat, écris-la dans « Questions » sans la trancher.

## Périmètre
- Décisions : D-52 à D-59 de `docs/decisions.md` (et D-25, D-26, D-37, D-42, D-43, D-49, D-50 qu'elles citent).
- Consigne : `docs/consignes/C10_CA-01_CA-02_CA-03_conception_causale.md`.
- Code : `src/causal.py`, section « Analyse causale » de `src/config.py`, `src/survie.py` (fonction `preparer_donnees_cox`, réutilisée par le score).
- Tests : `tests/test_causal.py`.
- Notebook et figures : `notebooks/05_causal.ipynb`, `docs/figures/05_*.png`.
- Référentiel : cahier des charges (F5, §4.3), `CLAUDE.md` (§5, §6 « Causal » et « Honnêteté »).

## Questions à traiter en priorité
1. **Spécification complète ?** Avec D-53 à D-59, CA-04 et CA-05 peuvent-elles être codées sans aucun choix laissé libre (calcul du RMST, risque à 30 semaines, HR pondéré et test de proportionnalité, bootstrap avec ou sans retouche, E-value, Cox dépendant du temps, variantes) ? Liste chaque choix encore ouvert : c'est le risque de « choisir après avoir vu le résultat ».
2. **DAG** : manque-t-il un facteur de confusion mesuré avant la photo ? Une variable du score est-elle une conséquence du tutorat, au-delà de la limite déjà écrite pour la fenêtre 1 à 8 (D-55) ? L'exclusion de `motif_orientation`, `type_tuteur` et `nb_seances` est-elle justifiée ? La cohorte en variable du score (et non en strate) pose-t-elle problème ?
3. **Temps immortel** : la photo (T > 8, tutoré si début ≤ 8, suivi à partir de la semaine 9) l'élimine-t-elle complètement ? Cherche des cas limites : début en semaine 8 et décrochage en semaine 9 ; censure exactement en semaine 8 ; tutorat la semaine de T (D-37) ; tutorat hors suivi (D-25) ; semaine de début inconnue (D-26) ; variantes à 3 et 5 semaines.
4. **Code** : exactitude de `difference_standardisee`, `poids_stabilises`, `tronquer_poids`, `taille_effective`, `support_commun`, `auc_par_les_rangs`, `activite_moyenne` (identifiants en double, comme dans un tirage bootstrap), `covariables_du_score` (médianes recalculées sur la population reçue) et de la retouche unique dans `chaine_de_conception`. La chaîne est-elle prête à être relancée sur des tirages bootstrap sans fuite ni erreur ?
5. **Garde-fous** : le contrôle des colonnes interdites est-il suffisant ? D-59 est-elle respectée partout (code exécuté, notebook, tests, figures) ?
6. **Tests** : lesquels ne protègent pas vraiment leur règle ? Quel test manque avant CA-04 ?
7. **Reproductibilité** depuis ton clone : `pip install -r requirements.txt` (statsmodels 0.15.0, pandas 2.3.3), `python run_all.py`, `pytest`, notebook 05 exécutable de haut en bas ; contrôles de la consigne C10 retrouvés ?
8. **Lisibilité** : les 3 fonctions de `causal.py` les plus difficiles à expliquer en soutenance, et pourquoi.

## Livraison
- Rapport `docs/revues/RV02_specification_causale.md`, commit `RV02 : relecture de la spécification causale et de la conception`, push sur `main`.
