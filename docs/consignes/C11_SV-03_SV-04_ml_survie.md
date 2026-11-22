# Consigne C11 — SV-03 : modèles de survie, validation 2024 → 2025 (issue #17) + SV-04 : comparaison Cox / gradient boosting et explication (issue #18)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C10 terminée.

## Contexte
Lis `CLAUDE.md` (§6 « Survie et ML » : D-42, D-43, validation temporelle ; « Honnêteté »), le cahier des charges (F4) et **les décisions D-60 et D-63**, validées par Saliou. Elles fixent toute la méthode : ne t'en écarte pas ; un cas non couvert se signale.

**Règle de cette consigne : la cohorte 2025 est l'examen final.** Rien de 2025 ne sert à l'entraînement : ni médianes, ni liste de colonnes, ni réglages. Les réglages du gradient boosting sont ceux de D-63 : **aucun autre essai**, ni sur 2025 ni ailleurs. Si le gradient boosting fait moins bien que le Cox, c'est un résultat : on l'écrit tel quel. Aucune variable de tutorat (D-43), aucune activité de la semaine en cours (D-42).

Données : `data/processed/base_survie.csv` et `data/processed/base_periode_personne.csv`.
Bibliothèque : `scikit-learn==1.9.1` (à ajouter à `requirements.txt` ; compatible avec Python 3.14 et pandas 2.3.3, D-60). Rien d'autre.

## Étape 0 — Correctif RV02-08 (commit séparé, avant le reste)
Sous Windows, pandas 2.x écrit les CSV avec des fins de ligne Windows (`os.linesep`), et `git status` signale alors de fausses modifications. Ajouter `lineterminator="\n"` aux trois `to_csv` : `src/base_survie.py` (vers la ligne 274) et `src/nettoyage/commun.py` (vers les lignes 50 et 57). Toute nouvelle écriture de CSV dans le projet fera de même. Vérifier : `python run_all.py` puis `git status` → aucune modification dans `data/processed/` ; `pytest`. Commit : `DA-07 : CSV écrits avec des fins de ligne LF sous Windows (RV02-08) (#10)`.

## Partie A — Préparation commune
1. **`survie.preparer_donnees_cox`** : nouveau paramètre `variables_exclues=()` (variables qualitatives ou numériques à ne pas mettre dans la table). Par défaut, rien ne change : les résultats de SV-02 et de C10 restent identiques (le vérifier). Il servira ici à retirer la cohorte (une seule cohorte par jeu, sinon la modalité de référence « 2024 » manque en 2025) et, en C12, la variable boursier pour le bonus.
2. Paramètres dans `config.py` (section « ML de survie ») : `COHORTE_ENTRAINEMENT = 2024`, `COHORTE_TEST = 2025`, `REGLAGES_GRADIENT_BOOSTING` (les 7 réglages de D-63), `SEMAINES_BRIER = range(1, 30)`, `SEMAINE_CALIBRATION = 20`, `NB_GROUPES_CALIBRATION = 10`, `NB_REPETITIONS_PERMUTATION = 10`, `ETATS_ACTIVITE = ("actif", "inactif", "inconnu")`, `DOSSIER_RESULTATS = DOSSIER_PROCESSED / "resultats"` (créé par le code).

## Partie B — `src/ml_survie.py` (fonctions courtes, docstrings en français)
En-tête « Rôle du module » (SV-03, SV-04). Une exception `ErreurMLSurvie`.
1. **Séparer les cohortes** : 2024 (entraînement) et 2025 (test).
2. **Variables de la rentrée** : `preparer_donnees_cox(2024, variables_exclues=("cohorte",))` → table d'entraînement et médianes de 2024 ; même appel sur 2025 **avec les médianes de 2024** ; colonnes de 2025 alignées sur celles de 2024 (indicatrice absente en 2025 → 0 ; colonne de 2025 inconnue en 2024 → `ErreurMLSurvie`). Liste positive (principe de D-43) : les colonnes sont uniquement les variables numériques du Cox et les indicatrices des variables qualitatives du Cox sans la cohorte.
3. **Lignes semaine-étudiant** pour le gradient boosting, à partir de `base_periode_personne` : une ligne par semaine où l'étudiant est encore suivi ; cible = `evenement` ; variables = `semaine` + variables de la rentrée de l'étudiant (jointure sur `id_etudiant`, sans jointure sur l'index) ; pour le modèle hebdomadaire, en plus : les 4 colonnes numériques `*_prec` (valeurs manquantes laissées telles quelles, le modèle les gère) et une indicatrice par état de `ETATS_ACTIVITE` pour `etat_activite_prec` (manquante si l'état précédent est manquant). Liste positive ici aussi.
4. **Entraînement** sur 2024 uniquement : `HistGradientBoostingClassifier(**REGLAGES_GRADIENT_BOOSTING)` pour les deux modèles ; `CoxPHFitter()` (liens d'Efron) sur la table de la rentrée 2024 ; test de Schoenfeld du Cox 2024 (`time_transform="rank"`), rapporté pour information.
5. **Courbes de survie prédites** pour les étudiants 2025, semaines 1 à 30 : gradient boosting « rentrée » → risque h(k) prédit pour chaque semaine k = 1 à 30, puis S(t) = produit des (1 − h(k)) pour k ≤ t ; Cox → `predict_survival_function` aux semaines 1 à 30 ; référence → Kaplan-Meier 2024 aux semaines 1 à 30, la même pour tous.
6. **C-index** : `lifelines.utils.concordance_index(T, S(30), E)` sur 2025.
7. **Brier score intégré** (D-63) :
   - G(t) = survie de la censure estimée sur 2024, par Kaplan-Meier « à l'envers » : à chaque semaine t, à risque = étudiants avec T ≥ t moins les décrochages de la semaine t (à égalité, les décrochages passent avant les censures) ; G recule du nombre de censures de la semaine divisé par ce nombre à risque (si ce nombre vaut 0, G ne change pas) ;
   - pour chaque semaine t de `SEMAINES_BRIER` : BS(t) = moyenne sur les étudiants 2025 de [S(t)² / G(T) si T ≤ t et E = 1] + [(1 − S(t))² / G(t) si T > t] (0 sinon) ;
   - Brier intégré = aire par la méthode des trapèzes de BS sur les semaines 1 à 29, divisée par (29 − 1).
8. **Calibration à 20 semaines** : risque prédit = 1 − S(20) ; 10 groupes de même taille selon le rang du risque prédit ; dans chaque groupe : effectif, risque prédit moyen, risque observé = 1 − Kaplan-Meier(20) du groupe ; écart absolu moyen sur les 10 groupes. Pour le Cox et le gradient boosting (pas pour la référence, dont le risque est le même pour tous).
9. **AUC hebdomadaire** sur les semaines-étudiants 2025 : `roc_auc_score(evenement, risque de la semaine)` pour le gradient boosting hebdomadaire, le gradient boosting « rentrée » (h(k) de la semaine) et le Cox (h(t) = 1 − S(t) / S(t − 1), avec S(0) = 1) ; décrochages attendus (somme des risques du modèle hebdomadaire) contre observés.
10. **Importance par permutation** (graine `SEED`, `numpy.random.default_rng`) : modèle « rentrée » : pour chacune des 8 variables (âge, note du bac, distance, genre, boursier, filière, région, emploi ; une variable qualitative = toutes ses indicatrices mélangées ensemble, au niveau de l'étudiant), baisse moyenne et écart-type du C-index sur 10 répétitions ; modèle hebdomadaire : les mêmes 8 variables plus les 4 `*_prec` et `etat_activite_prec` (indicatrices ensemble), mélange au niveau des lignes semaine-étudiant, baisse de l'AUC hebdomadaire.
11. **Enregistrement** dans `config.DOSSIER_RESULTATS` (UTF-8, `lineterminator="\n"`) : mesures du modèle « rentrée » ; BS(t) par semaine ; table de calibration ; AUC hebdomadaires et décrochages attendus / observés ; importances ; HR du Cox 2024 avec IC 95 % ; prédictions 2025 en format long (`id_etudiant`, `semaine`, survie Cox, survie gradient boosting) ; scores hebdomadaires 2025 (`id_etudiant`, `semaine`, risque du modèle hebdomadaire, risque du Cox).
12. **Une fonction qui enchaîne tout**, appelée par `run_all.py` après la construction des bases (durée à rapporter).

## Partie C — `notebooks/04_ml_survie.ipynb`
Il importe `src/` et **lit les résultats enregistrés** par `run_all.py` (sans réentraîner). Chaque tableau et chaque figure est suivi d'une phrase pour un conseiller pédagogique, avec des chiffres calculés par le code :
1. **La question et la règle** : prédire le décrochage ; entraînement 2024, test 2025, réglages fixés d'avance (D-63) ; principe du gradient boosting à temps discret expliqué simplement (le risque de chaque semaine, puis la courbe de survie).
2. **Les données** : étudiants, décrochages et semaines-étudiants par cohorte.
3. **Le modèle « rentrée »** : tableau C-index, Brier intégré, Brier à 20 semaines, écart de calibration (Cox, gradient boosting, référence) avec leur lecture ; HR du Cox 2024 avec IC (tableau) et test de Schoenfeld.
4. **Calibration à 20 semaines** : figure prédit / observé des deux modèles avec la diagonale → `docs/figures/04_calibration_20_semaines.png` ; lecture des groupes extrêmes.
5. **Brier semaine par semaine** : figure des trois courbes → `04_brier_par_semaine.png`.
6. **Courbe moyenne prédite contre observée en 2025** : survie moyenne prédite (Cox, gradient boosting) et Kaplan-Meier observé 2025 → `04_survie_moyenne_2025.png`.
7. **Le score hebdomadaire** : AUC des trois modèles, décrochages attendus contre observés ; ce qu'apporte l'activité de la semaine précédente.
8. **Expliquer les modèles** : importances par permutation (deux figures → `04_importance_rentree.png`, `04_importance_hebdomadaire.png`) mises en regard des HR du Cox.
9. **Conclusion** : quel modèle fait le mieux, sur quelle mesure, et les limites (réglages non optimisés, fixés d'avance ; une seule cohorte de test). Le choix du modèle utilisé par le tableau de bord et les fiches LLM n'est **pas** fait ici (LL-01, DB-01).
- Vocabulaire : « associé à », « prédit », jamais « cause » ni « effet ».

## Partie D — Tests (`tests/test_ml_survie.py`)
- Survie à partir des risques hebdomadaires : risques [0,1 ; 0,2] → survie [0,9 ; 0,72].
- Survie de la censure avec égalités : T = [1, 1, 2, 3], E = [1, 0, 0, 1] → G(1) = 2/3, G(2) = 1/3, G(3) = 1/3.
- Brier (exemple calculé à la main, identique à scikit-survival) : entraînement T = [1, 2, 2, 3, 4], E = [1, 0, 1, 0, 1] ; test T = [1, 2, 3, 3], E = [1, 0, 1, 0] ; S(1) = [0,8 ; 0,9 ; 0,95 ; 0,7], S(2) = [0,6 ; 0,8 ; 0,85 ; 0,5] → BS(1) = 0,185625, BS(2) = 0,1921875, Brier intégré sur les semaines 1 à 2 = 0,18890625.
- Calibration : 10 groupes de tailles égales (à 1 près) ; risque observé par Kaplan-Meier sur un petit exemple.
- Alignement des colonnes : indicatrice absente en 2025 → 0 ; colonne nouvelle en 2025 → `ErreurMLSurvie`.
- Séparation temporelle : aucune ligne d'entraînement de 2025 ; les médianes de 2024 sont bien celles utilisées pour 2025.
- `preparer_donnees_cox` avec `variables_exclues=("cohorte",)` sur une seule cohorte ; sans exclusion, résultat inchangé.
- Liste positive : aucune colonne de tutorat, de T, de E ou d'activité de la semaine en cours parmi les variables.
- Importance par permutation : même graine → mêmes résultats.

## Contrôles attendus
Prototype de la session de pilotage (scikit-learn 1.9.1, lifelines 0.30.3, pandas 2.3.3), à comparer. Le gradient boosting peut varier légèrement d'une machine à l'autre (calculs en parallèle) : signaler un écart de plus de 0,005 ; pour le reste, signaler tout écart et l'expliquer, sans forcer le code :
- Médianes 2024 : âge 20,0 ; note du bac 12,31 ; log2 de la distance 3,2928. 13 colonnes : âge, note du bac, log2 distance, genre M, boursier Oui, Gestion, Droit, Génie civil, Communication, Hors Dakar, région manquante, emploi Oui, emploi manquant ; aucune colonne de 2025 absente de 2024.
- Semaines-étudiants : 2024 → 60 691 lignes (715 décrochages) ; 2025 → 61 247 (725).
- Modèle « rentrée » sur 2025 (C-index ; Brier intégré ; Brier à 20 semaines ; écart de calibration) : **Cox 0,6382 ; 0,1332 ; 0,1740 ; 0,028** · **gradient boosting 0,6100 ; 0,1401 ; 0,1838 ; 0,059** · référence 0,5 ; 0,1410 ; 0,1857. Brier intégré identique à scikit-survival au millionième (Cox 0,133223 ; gradient boosting 0,140072 ; référence 0,140974). Risque observé à 20 semaines en 2025 : 0,2468.
- Calibration (risque prédit, observé) par groupe, du moins au plus risqué : Cox (0,098 ; 0,105) … (0,500 ; 0,462) ; gradient boosting (0,083 ; 0,097) … (0,601 ; 0,363).
- AUC hebdomadaire 2025 : Cox 0,688 ; gradient boosting « rentrée » 0,658 ; gradient boosting hebdomadaire 0,685 ; décrochages attendus 749 pour 725 observés.
- Importance (baisse du C-index), modèle « rentrée » : note du bac 0,045 ; emploi 0,024 ; distance 0,013 ; boursier 0,012 ; filière 0,008 ; région 0,004 ; âge 0,004 ; genre 0,001. Modèle hebdomadaire (baisse de l'AUC) : note du bac 0,019 ; absences de la semaine précédente 0,015 ; connexions 0,012 ; note de la semaine précédente 0,008 ; emploi 0,007 ; devoirs 0,006 ; boursier 0,003 ; les autres ≤ 0,002.
- HR du Cox 2024 : âge 1,098 ; note du bac 0,836 ; log2 distance 1,126 ; genre M 1,106 ; boursier 0,732 ; Gestion 0,845 ; Droit 1,015 ; Génie civil 0,838 ; Communication 0,886 ; Hors Dakar 1,020 ; région manquante 1,133 ; emploi 1,718 ; emploi manquant 0,943.
- Durée de l'étape ML : environ 1 min chez le pilotage (la permutation domine) ; la rapporter sur ton PC.

## Livraison
- Commits : `DA-07 : CSV écrits avec des fins de ligne LF sous Windows (RV02-08) (#10)` (étape 0) ; `SV-03 : Cox et gradient boosting à temps discret, validation 2024 → 2025 (#17)` ; `SV-04 : comparaison Cox / gradient boosting et importance par permutation (#18)` (le notebook avec ce dernier) ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus et la durée totale de `run_all.py`.
