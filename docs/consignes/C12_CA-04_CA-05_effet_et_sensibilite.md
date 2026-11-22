# Consigne C12 — CA-04 : effet du tutorat (issue #21) + CA-05 : analyses de sensibilité (issue #22), avec les corrections de la relecture RV02

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C10 et C11 terminées.

## Contexte
Lis `CLAUDE.md` (§6 « Causal » et « Honnêteté »), le cahier des charges (F5), **les décisions D-53 à D-62** (surtout D-57, D-58, D-61, D-62) et le rapport `docs/revues/RV02_specification_causale.md`.

**Règle de cette consigne : la méthode est figée.** Tu appliques D-53 à D-62 à la lettre, sans rien choisir d'autre. Si un résultat te surprend, tu le rapportes tel quel : tu ne changes ni les variables, ni les poids, ni la photo, ni les réglages. Un cas non couvert se signale (§2 de `CLAUDE.md`) ; s'il bloque, arrête-toi.
Cette consigne tourne **pendant la nuit, sans Saliou** : aucune nouvelle bibliothèque n'est nécessaire (lifelines, statsmodels, numpy, pandas sont déjà installés).

## Étape 0 — Résultats identiques d'une machine à l'autre (commit séparé)
Relancé sous Linux, `run_all.py` redonne les mêmes résultats à 5e-16 près (bruit de calcul), mais le texte des CSV change au dernier chiffre et `git status` les signale. Dans `ml_survie.ecrire_resultat` (et dans toute écriture de résultats de cette consigne) : `float_format="%.8g"`, en plus de `lineterminator="\n"` et `encoding="utf-8"`. Relancer `run_all.py`, commiter les résultats réécrits, vérifier qu'une seconde exécution laisse `git status` propre. Commit : `SV-03 : résultats écrits avec 8 chiffres significatifs, identiques d'une machine à l'autre (#17)`.

## Partie A — Corrections de la relecture RV02 (D-61, points 1, 9, 10 et 8)
1. **Liste positive** (RV02-04) : `covariables_du_score` n'accepte que `colonnes_numeriques_du_score()` et les indicatrices des variables qualitatives du Cox (moins les variables exclues) ; toute autre colonne → `ErreurCausal`. Le contrôle par mots interdits peut rester en plus.
2. **`chaine_de_conception`** reçoit la semaine de la photo (`semaine`) : `ErreurCausal` si la fenêtre d'activité se termine après elle. Nouveau paramètre `variables_exclues=()`, transmis à `preparer_donnees_cox` et à la matrice d'équilibre (pour le bonus F8, plus tard).
3. **Convergence** : `ajuster_score` lève `ErreurCausal` si `modele.converged` est faux.
4. **Figure du DAG** (RV02-07) : ajouter la flèche en pointillés « facteurs non mesurés → activité des semaines 1 à 8 », sans traverser de boîte ni de texte.
5. **Notebook 05, nouvelles sections avant l'effet** :
   - « Diagnostic hors critère » (RV02-06) : SMD avant / après (poids de l'analyse principale) des notes et des connexions des semaines 7 et 8, de chaque modalité de la mention du bac, de chaque région d'origine détaillée et du nombre de semaines inactives sur les semaines 1 à 8 ; une phrase de lecture ; le score n'est **pas** modifié.
   - « Ce qu'on estime exactement » : la phrase de D-61 (point 11), les trois conditions de D-59 et les biais écrits d'avance (D-59, D-61 point 11), dont le recouvrement de la fenêtre 1 à 8 avec la période après le début (en moyenne 3,6 semaines sur 8 chez les tutorés, à calculer par le code).
6. **Tests** (RV02-05) : la chaîne sur un tirage avec doublons (index remis à zéro) et le même résultat sur une simple permutation de la population ; une retouche déclenchée sur un petit cas construit, avec `equilibre_initial` conservé ; la matrice d'équilibre contient les références et la modalité « (manquant) » ; une fenêtre qui dépasse la photo est refusée ; l'AUC avec n1 ≠ n0 et des ex aequo ; une colonne hors liste positive est refusée.
Commit : `CA-03 : corrections de la relecture RV02 (garde-fous, tests, DAG, diagnostic) (#20)`.

## Partie B — CA-04 : l'effet (`src/causal.py`, D-57 et D-61)
Paramètres dans `config.py` : `NB_TIRAGES_PRINCIPAL = 500`, `NB_TIRAGES_VARIANTE = 200`, `QUANTILES_IC = (2.5, 97.5)`.
1. **Effet pondéré** sur une population, avec durée = T − L, l'événement E, l'équipe et les poids tronqués, et l'horizon H = 30 − L :
   - pour chaque équipe, Kaplan-Meier pondéré (`KaplanMeierFitter(...).fit(durée, E, weights=poids)`) ; risque à 30 semaines = 1 − S(H) ; RMST = `restricted_mean_survival_time(kmf, t=H)` ;
   - différence de risque (tutorés − non tutorés), rapport des risques (RR), différence de RMST ;
   - HR : `CoxPHFitter()` sur les colonnes durée, E, équipe (0/1), `weights_col` = poids ; `robust=True` pour l'ajustement de l'analyse principale (IC « sandwich » rapporté pour information) ; dans les tirages, l'estimation seule ;
   - test de Schoenfeld (`time_transform="rank"`) sur le Cox pondéré principal, rapporté comme indicatif.
2. **Bootstrap** (D-61, point 1) : X et la matrice d'équilibre sont construits une fois (chaîne de conception de l'analyse) ; un générateur `numpy.random.default_rng(config.SEED)` neuf par analyse ; à chaque tirage, indices `rng.integers(0, n, size=n)` ; X, matrice, équipe, durée et E pris à ces indices (index remis à zéro) ; score ré-estimé avec la spécification de l'analyse (si la retouche a été appliquée à l'analyse, les carrés restent ; on ne redécide jamais dans un tirage) ; poids stabilisés, troncature, plus grand |SMD| du tirage (compté s'il atteint 0,1) ; effet pondéré. Un tirage qui échoue (erreur ou score non convergé) est remplacé par le tirage suivant et compté. IC = percentiles 2,5 et 97,5 (`numpy.percentile`, méthode par défaut).
3. **E-value** (D-61, point 5) sur le RR : estimation, et borne de l'IC la plus proche de 1 (1 si l'IC contient 1).
4. **Analyse principale** : photo de la semaine 8, fenêtre 1 à 8, 500 tirages.
5. **Enregistrement** dans `config.DOSSIER_RESULTATS` (`%.8g`, LF, UTF-8) : tableau de l'effet (mesure, estimation, borne basse, borne haute), les 500 tirages, les courbes pondérées des deux équipes (semaines 8 à 30), le diagnostic du bootstrap (tirages hors critère, échecs), le test de Schoenfeld.
6. Le tout est appelé par `run_all.py` après l'étape ML (durée à rapporter).
Commit : `CA-04 : effet du tutorat, courbes pondérées, RMST, HR et bootstrap (#21)`.

## Partie C — CA-05 : sensibilité (D-58, D-61, D-62)
1. **Variantes**, chacune avec toute la chaîne (conception puis effet) et 200 tirages :
   - seuils de 3 et 5 semaines : `population_photo(base, 8, "T_seuil3", "E_seuil3")` et `("T_seuil5", "E_seuil5")`, durées et événements de ces colonnes ;
   - photos à L = 6 (fenêtre 1 à 6) et L = 10 (fenêtre 1 à 10), horizon 30 − L (le RMST n'a donc pas le même horizon : l'écrire) ;
   - fenêtre 1 à 2 (photo de la semaine 8) : son tableau d'équilibre **et** l'équilibre de ses poids sur la matrice de la fenêtre 1 à 8 ;
   - support strict : on retire les étudiants hors du support commun de l'analyse principale, puis on refait toute la chaîne sur les autres.
   Si la retouche est appliquée à une variante ou si son critère n'est pas atteint, on le rapporte tel quel (attendu pour L = 6).
2. **Cox dépendant du temps** (D-62) sur `base_periode_personne`, tous les étudiants sauf semaine de début inconnue :
   - intervalle (semaine − 1, semaine], événement = `evenement`, traitement = `tutorat_commence` ;
   - activité (4 variables de `VARIABLES_ACTIVITE_PROPENSION`) : moyenne des valeurs renseignées des semaines 1 à t − 1 ; pour un tutoré (statut « tutore », début s), moyenne des semaines 1 à min(t − 1, s) : elle est donc figée à partir de la semaine s + 1 ; aucune valeur → médiane de la colonne sur toutes les semaines-étudiants où elle est définie ;
   - profil : `preparer_donnees_cox(..., variables_exclues=("cohorte",))` sur ces étudiants ; strates : cohorte (`CoxTimeVaryingFitter(...).fit(..., strata=["cohorte"])`) ;
   - HR de `tutorat_commence`, IC 95 % du modèle, p. Présenté comme une question voisine (D-62).
3. **Enregistrement** : tableau de sensibilité (une ligne par analyse : effectifs, |SMD| maximal, retouche, critère, part des tirages hors critère, risques, différence de risque, RR, différence de RMST et horizon, HR, avec IC), les deux tableaux d'équilibre de la fenêtre 1 à 2, le résultat du Cox dépendant du temps.

## Partie D — `notebooks/05_causal.ipynb` (suite)
Après les sections de la partie A, toujours en lisant les résultats enregistrés :
- **L'effet du tutorat (CA-04)** : courbes de Kaplan-Meier pondérées des deux équipes, semaines 8 à 30, risques à 30 semaines indiqués → `docs/figures/05_km_ponderees.png` ; tableau des mesures avec IC ; tirages hors critère et échecs ; test de Schoenfeld (si p < 0,05 : le HR se lit comme une moyenne sur la période, et ce sont le risque à 30 semaines et le RMST qui portent la conclusion, D-57) ; deux phrases pour un conseiller pédagogique.
- **La sensibilité (CA-05)** : tableau des variantes ; graphique des HR avec IC (échelle logarithmique ; analyse principale mise en évidence ; Cox dépendant du temps à part, comme question voisine) → `05_sensibilite.png` ; E-value et sa lecture ; les deux tableaux d'équilibre de la fenêtre 1 à 2.
- **Conclusion prudente** : ce qui est estimé (phrase de D-61), le résultat avec ses IC, les trois conditions, les limites, l'accord ou le désaccord des variantes.
- Vocabulaire : « effet », « réduit » seulement dans ces sections, toujours avec les conditions rappelées.

## Partie E — Tests (`tests/test_causal.py`)
- Effet pondéré, poids tous égaux à 1, durées [1, 2, 3, 3], E [1, 0, 1, 0], horizon 3 : S(1) = 0,75, S(3) = 0,375, risque à l'horizon 0,625, RMST 2,5 (identiques au Kaplan-Meier non pondéré).
- E-value : RR = 0,5 → 3,414 ; RR = 2 → 3,414 ; IC contenant 1 → 1.
- Bootstrap : même graine → mêmes IC (petit exemple, peu de tirages) ; un tirage en échec est remplacé et compté.
- Activité figée du Cox dépendant du temps : tutoré avec s = 2 et activité [10, 20, 30, 40] aux semaines 1 à 4 → semaine 1 : médiane ; semaine 2 : 10 ; semaine 3 : 15 ; semaine 4 : 15 (et non 20) ; un non-tutoré aux mêmes valeurs → 20 en semaine 4.

## Contrôles attendus
Prototype de la session de pilotage (même méthode, lifelines 0.30.3, statsmodels 0.15.0), à comparer ; signaler et expliquer tout écart (un écart au 3e chiffre des IC peut venir d'une façon différente de tirer : vérifier `rng.integers(0, n, size=n)`) :
- **Analyse principale** (4 316 étudiants, 773 tutorés, |SMD| maximal 0,060, pas de retouche, 0 échec, 12 % des tirages avec un |SMD| ≥ 0,1) :
  - risque de décrochage à 30 semaines : tutorés 0,1296 [0,1060 ; 0,1577], non tutorés 0,1990 [0,1852 ; 0,2123] ;
  - différence −0,0695 [−0,0956 ; −0,0398] ; RR 0,651 [0,534 ; 0,797] ;
  - RMST sur 22 semaines : 20,660 contre 19,459, différence +1,201 semaine [0,820 ; 1,479] ;
  - HR 0,613 [0,500 ; 0,759] (IC sandwich, pour information : [0,491 ; 0,766]) ; Schoenfeld p = 0,014 ;
  - E-value 2,443 ; borne de l'IC 1,820 ;
  - survie pondérée (tutorés ; non) : semaine 12 (0,983 ; 0,963), 16 (0,955 ; 0,893), 20 (0,923 ; 0,850), 30 (0,870 ; 0,801).
- **Variantes** (200 tirages ; différence de risque [IC] ; HR [IC]) :
  - seuil 3 : 4 314 / 772 ; −0,0675 [−0,0928 ; −0,0349] ; 0,623 [0,502 ; 0,785] ;
  - seuil 5 : 4 318 / 774 ; −0,0688 [−0,0938 ; −0,0439] ; 0,615 [0,498 ; 0,738] ;
  - L = 6 : 4 473 / 560 ; retouche appliquée, critère non atteint (|SMD| 0,124) ; −0,0645 [−0,1016 ; −0,0279] ; 0,673 [0,511 ; 0,840] ;
  - L = 10 : 4 225 / 971 ; −0,0593 [−0,0855 ; −0,0332] ; 0,650 [0,534 ; 0,786] ; RMST sur 20 semaines +0,849 ;
  - fenêtre 1 à 2 : −0,0469 [−0,0719 ; −0,0150] ; 0,727 [0,603 ; 0,896] ;
  - support strict : 4 262 / 765 ; −0,0711 [−0,0955 ; −0,0416] ; 0,607 [0,494 ; 0,752].
- **Cox dépendant du temps** : 4 995 étudiants, 121 811 semaines-étudiants dont 24 119 tutorées ; HR 0,540 [0,462 ; 0,631].
- Durée de l'étape causale : environ 100 s chez le pilotage ; la rapporter sur ton PC (budget total de `run_all.py` : 15 min).

## Livraison
- Commits : `SV-03 : … (#17)` (étape 0) ; `CA-03 : corrections de la relecture RV02 … (#20)` (partie A) ; `CA-04 : effet du tutorat, courbes pondérées, RMST, HR et bootstrap (#21)` (partie B) ; `CA-05 : sensibilité, E-value et Cox dépendant du temps (#22)` (parties C, D, E) ; push sur `main`.
- Vérifier à la fin : `pytest` ; `python run_all.py` deux fois de suite → `git status` propre ; notebook 05 exécuté de haut en bas.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus et la durée de `run_all.py`.
