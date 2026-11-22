# Consigne C09 — SV-01 : Kaplan-Meier, log-rank, semaines critiques (issue #12) + SV-02 : modèle de Cox (issue #15)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C06 à C08 terminées.

## Contexte
Lis `CLAUDE.md` (§5, §6 : D-42, D-43, vocabulaire, honnêteté), le cahier des charges (F2, F3) et **les décisions D-46 à D-51** de `docs/decisions.md`, validées par Saliou.
Données : `data/processed/base_survie.csv` uniquement (T, E, covariables de la rentrée). **Aucune variable de tutorat** dans ces analyses (D-43) : le tutorat relève de la partie causale.
Bibliothèque : `lifelines` (à ajouter à `requirements.txt`, version exacte installée).

## Partie A — `src/survie.py` (fonctions courtes, docstrings en français)
Paramètres dans `config.py` : `SEMAINES_SURVIE = (10, 20, 30)`, `FACTEUR_SEMAINE_CRITIQUE = 1.5`, `ALPHA = 0.05`, les références des modalités et la liste des variables du Cox (D-49), le découpage de période (1 à 8 / 9 à 30, D-51).
1. **Kaplan-Meier global** : survie à 10, 20, 30 semaines avec IC 95 % ; médiane, ou « non atteinte » si la courbe ne passe pas sous 50 %.
2. **Kaplan-Meier par sous-groupe** (D-46) : boursier, filière, mention, emploi ; pour chaque groupe : effectif, nombre de décrochages, survie à 10, 20, 30 semaines ; test du log-rank (à k groupes si plus de 2 modalités) ; seuil de Bonferroni 0,05 / 4 ; valeurs manquantes exclues de la comparaison de leur variable, leur nombre est rapporté.
3. **Risque hebdomadaire et semaines critiques** (D-47) : réutiliser `eda.taux_hebdomadaire` ; risque moyen = total des décrochages / total des semaines-étudiant à risque ; IC 95 % de chaque semaine (approximation normale) ; semaine critique si risque ≥ 1,5 × risque moyen.
4. **Préparation des données du Cox** (D-49, D-50) : à partir de `config.COVARIABLES_RENTREE`, **sans** `mention_bac` ; région → `Dakar` / `Hors Dakar` / `(manquant)` ; `log2_distance` ; qualitatives manquantes → `(manquant)` ; numériques manquantes → médiane. La fonction reçoit en option les médianes à utiliser (pour réutiliser en SV-03 les médianes de la cohorte 2024 sur 2025) ; sinon elle les calcule sur les données reçues et les renvoie. Codage en indicatrices avec les modalités de référence de D-49.
5. **Cox** (D-48, D-51) :
   - modèle 1 : cohorte en covariable ; test de Schoenfeld par variable (`proportional_hazard_test`, `time_transform="rank"`) ;
   - appliquer la règle de D-51 aux variables avec p < 0,05 (attendu : la cohorte seule → stratification) ;
   - modèle final : stratifié selon cette règle ; HR, IC 95 %, p ; C-index ; nouveau test de Schoenfeld ;
   - sensibilité : modèle final sur les dossiers complets ; écart maximal des HR ;
   - robustesse au seuil d'inactivité : survie globale à 10, 20, 30 semaines et HR du modèle final avec `T_seuil3`/`E_seuil3` et `T_seuil5`/`E_seuil5`.
   - Si une règle de D-51 doit s'appliquer à une **autre** variable que la cohorte : appliquer la règle telle quelle **et** le signaler dans le compte rendu.

## Partie B — `notebooks/03_survie.ipynb`
Il importe `src/` et lit `data/processed/` (sans relancer le pipeline). Sections, chacune suivie d'une interprétation pour un conseiller pédagogique dont les chiffres sont calculés par le code :
1. Courbe de survie globale avec son IC → `docs/figures/03_km_global.png` (axe vertical de 0 à 100 %) ; survie à 10, 20, 30 semaines ; médiane non atteinte expliquée en une phrase.
2. Risque hebdomadaire avec la ligne du seuil « 1,5 × risque moyen » → `03_risque_hebdomadaire.png` ; liste des semaines critiques.
3. Courbes par sous-groupe (une figure 2 × 2) → `03_km_sous_groupes.png` ; si l'axe vertical ne part pas de 0, l'écrire dans le titre ; tableau du log-rank (p brute, seuil de Bonferroni, conclusion).
4. Cox : tableau des HR (IC 95 %) avec une phrase par variable (« associé à un risque … fois plus élevé / plus faible, à autres variables égales ») ; graphique des HR avec leurs IC (échelle logarithmique) → `03_cox_hazard_ratios.png`.
5. Proportionnalité : tests avant et après correction, en expliquant la stratification en une phrase.
6. Sensibilité : dossiers complets ; seuils de 3 et 5 semaines.
- **Vocabulaire** : « associé à », jamais « cause », « effet » ou « réduit ». Rappeler une fois que ces associations ne sont pas causales (exemple : la bourse).

## Partie C — Tests (`tests/test_survie.py`)
- Kaplan-Meier sur l'exemple de 10 étudiants inventés (1 décrochage en semaine 1, 1 censuré en semaine 2, 2 décrochages en semaine 3, le reste censuré en semaine 4) : survie 0,90 en semaine 1 et 2, 0,675 en semaine 3.
- Semaines critiques sur une série de risques inventée.
- Préparation du Cox : `mention_bac` absente ; aucune colonne de tutorat ni `T_seuil*`/`E_seuil*` parmi les covariables ; références absentes des indicatrices ; modalité `(manquant)` créée ; les médianes fournies sont bien utilisées (et pas recalculées).
- Le Cox stratifié s'ajuste sans erreur sur un petit jeu inventé.

## Contrôles attendus
Prototype de la session de pilotage (`lifelines`), à comparer ; en cas d'écart, le signaler et l'expliquer, sans forcer le code :
- Kaplan-Meier global : S(10) = 0,853 [0,843 ; 0,862] ; S(20) = 0,752 [0,740 ; 0,764] ; S(30) = 0,709 [0,696 ; 0,722] ; médiane non atteinte.
- Risque moyen 1,18 % ; semaines critiques : **4, 5, 6, 7, 15, 16**.
- Log-rank : boursier p = 2,1e-06 ; filière p = 0,0023 ; mention p = 3,7e-32 ; emploi p = 5,3e-30 (tous sous 0,0125).
- Survie à 30 semaines : boursiers 0,745 / non-boursiers 0,683 ; emploi 0,567 / sans emploi 0,742 ; mention Passable 0,633, Assez bien 0,734, Bien 0,802, Très bien 0,873 ; filières de 0,682 (Informatique) à 0,744 (Gestion).
- Cox modèle 1 : seule la cohorte viole la proportionnalité (p ≈ 0,04).
- Cox final stratifié par cohorte (n = 5 000, 1 440 événements, C-index 0,642) : âge 1,090 [1,055 ; 1,125] ; note du bac 0,838 [0,813 ; 0,863] ; log2 distance 1,109 [1,066 ; 1,154] ; genre M 1,086 (p = 0,12) ; boursier 0,768 [0,689 ; 0,855] ; Communication 0,926 (p = 0,35) ; Droit 0,959 (p = 0,60) ; Gestion 0,775 [0,671 ; 0,895] ; Génie civil 0,805 [0,680 ; 0,953] ; hors Dakar 1,027 (p = 0,66) ; région manquante 1,240 (p = 0,23) ; emploi 1,771 [1,571 ; 1,998] ; emploi manquant 1,056 (p = 0,71) ; après stratification, aucune variable sous 0,05 au test de Schoenfeld (p minimum 0,36).
- Dossiers complets : n = 4 595 ; écart maximal des HR 0,033.

## Livraison
- Commits : `SV-01 : Kaplan-Meier, log-rank et semaines critiques (#12)` puis `SV-02 : modèle de Cox et proportionnalité (#15)` (le notebook avec le second) ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus.
