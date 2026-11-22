# Consigne C10 — CA-01 : DAG, entrée en tutorat et photo de la semaine 8 (issue #16) + CA-02 : score de propension et support commun (issue #19) + CA-03 : poids et équilibre (issue #20)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C09 terminée.

## Contexte
Lis `CLAUDE.md` (§5, §6 « Causal » et « Honnêteté des résultats »), le cahier des charges (F5) et **les décisions D-52 à D-59** de `docs/decisions.md`, validées par Saliou. Elles fixent toute la méthode : ne t'en écarte pas ; un cas non couvert se signale (§2 de `CLAUDE.md`).

**Règle d'or de cette consigne (D-59) : phase de conception.** Dans tout ce que C10 produit (code exécuté, notebook, figures, tests, compte rendu), il est **interdit** de comparer T, E, la survie, le type d'événement ou le décrochage entre tutorés et non tutorés, que ce soit sur la photo ou sur tous les étudiants. Le décrochage par équipe ne sera calculé qu'en CA-04, après la relecture R02. Seule exception : compter les étudiants sortis avant la photo, **toutes équipes confondues** (tableau des photos). Si une étape semble demander davantage, arrête-toi et signale-le.

Données : `data/processed/base_survie.csv` et `data/processed/base_periode_personne.csv` (lus avec `eda.lire_bases()`, sans relancer le pipeline).
Bibliothèque : `statsmodels==0.15.0` (à ajouter à `requirements.txt` ; compatible avec pandas 2.3.3 et Python 3.14, D-52). Rien d'autre.

## Étape 0 — Petit correctif DA-03 (commit séparé, avant le reste)
L'avertissement numpy signalé en C09 (`inscriptions.py`) vient de `pd.Timedelta(weeks=...)` dans `fin_du_suivi`. Remplacer par `datetime.timedelta(weeks=config.N_SEMAINES)` (bibliothèque standard). Vérifier : `pytest` sans cet avertissement ; `python run_all.py` puis `git status` → **aucune** modification dans `data/processed/`. Commit : `DA-03 : date de fin du suivi sans pd.Timedelta (avertissement numpy) (#6)`.

## Partie A — `src/causal.py` (fonctions courtes, docstrings en français)
En-tête « Rôle du module » (tâches CA-01 à CA-03 ; CA-04 et CA-05 viendront s'y ajouter). Une exception `ErreurCausal` pour les cas non prévus.

Paramètres à ajouter dans `config.py` (section « Analyse causale ») : `SEMAINE_LANDMARK = 8` (D-53 ; la constante `SEMAINE_REPERE_TUTORAT` de l'EDA reste telle quelle) ; `SEMAINES_LANDMARK_SENSIBILITE = (6, 10)` ; `PHOTOS_COMPAREES = (4, 6, 8, 10, 12)` ; `FENETRE_ACTIVITE_SENSIBILITE = (1, 2)` (la fenêtre principale est 1 à `SEMAINE_LANDMARK`) ; `VARIABLES_ACTIVITE_PROPENSION` = `nb_connexions_lms`, `devoirs_rendus`, `note_moyenne`, `absences` ; `PERCENTILES_TRONCATURE = (1, 99)` ; `SEUIL_SMD = 0.1` ; `SEMAINES_AVANT_DEBUT = 2` ; `SEMAINES_DEBUT_ANALYSEES = range(3, 13)`.

1. **Moment d'entrée en tutorat** (CA-01), sans T ni E par équipe :
   - débuts connus pendant le suivi (semaines 1 à 30) : effectif par semaine, % cumulé, part au plus tard en semaine 8 ; motifs d'orientation (sur tous les tutorats) ;
   - « ce qui précède l'entrée » : pour chaque semaine k de `SEMAINES_DEBUT_ANALYSEES`, éligibles = étudiants avec T ≥ k, semaine de début non inconnue, pas de tutorat commencé avant k ; « commencent » = début en semaine k ; pour chacune des 4 variables d'activité, moyenne par étudiant sur les semaines max(1, k − 2) à k − 1 (semaines renseignées seulement ; étudiant ignoré pour cette variable s'il n'en a aucune), puis différence standardisée « commencent » contre autres éligibles (sans pondération, écart-type combiné). Sortie : une ligne par k (k, commencent, éligibles, 4 écarts).
2. **Tableau des photos** (CA-01, D-53) : pour chaque L de `PHOTOS_COMPAREES` : étudiants sur la photo (T > L, semaine de début non inconnue) ; sortis avant la photo (T ≤ L, toutes équipes) et, parmi eux, décrochages ; tutorés à la photo (effectif, %) ; non tutorés ; futurs tutorés parmi eux (début entre L + 1 et 30 : effectif, %) ; part des débuts connus pendant le suivi qui ont lieu au plus tard en L ; tutorés partis avant la photo (début ≤ L, début < T, T ≤ L) ; semaines de suivi après la photo (30 − L) ; étudiants à semaine de début inconnue retirés de la photo.
3. **Population de la photo** (D-54) : `population_photo(base, semaine, duree="T", evenement="E")` → les étudiants avec `duree > semaine`, sauf semaine de début inconnue, avec une colonne `tutore_photo` (1 si début ≤ semaine, sinon 0, y compris tutorat hors suivi). Les colonnes de durée et d'événement sont gardées telles quelles pour CA-04, **sans** aucun calcul dessus ici.
4. **Activité moyenne** : moyenne par étudiant, sur une fenêtre de semaines [première ; dernière], des 4 variables de `VARIABLES_ACTIVITE_PROPENSION` (colonnes de la semaine elle-même, pas `*_prec`), à partir de `base_periode_personne` ; colonnes nommées `<variable>_moy`. La fonction doit accepter une liste d'identifiants **avec doublons** (C11 la relancera sur des tirages bootstrap).
5. **Covariables du score** (D-55) : profil par `survie.preparer_donnees_cox(population, duree=..., evenement=...)` (même codage, mêmes références et même règle des manquants qu'en SV-02, médianes calculées sur la population reçue), sans les colonnes T et E, plus les 4 moyennes d'activité (manquante → médiane de la population reçue). Garde-fou : `ErreurCausal` si une colonne interdite apparaît (nom contenant `tutor`, `tuteur`, `seance`, `motif`, `statut` ou `seuil`, ou nom exactement égal à `T`, `E` ou `evenement`). Sortie : (X, médianes utilisées).
6. **Score de propension** (CA-02, D-56) : `statsmodels` GLM binomial avec constante, sans pénalité ; score = probabilité prédite ; AUC par la formule des rangs (somme des rangs des tutorés − n₁(n₁ + 1)/2) / (n₁ n₀) ; tableau des rapports de cotes (exp(coef), IC 95 %, p).
7. **Support commun** : bornes [plus grand des minimums ; plus petit des maximums] du score des deux équipes ; masque « dans le support » ; effectifs hors support par équipe.
8. **Poids** (CA-03) : poids stabilisés (D-56) ; troncature aux percentiles 1 et 99 de **l'ensemble** des poids (`numpy.percentile`, méthode par défaut) ; nombre de poids modifiés ; taille effective (Σw)² / Σw² par équipe.
9. **Équilibre** : matrice d'équilibre = variables numériques (âge, note du bac, log2 de la distance, 4 moyennes d'activité) + une colonne 0/1 **par modalité** de chaque variable qualitative du Cox, références et `(manquant)` comprises ; différence standardisée = (moyenne pondérée des tutorés − moyenne pondérée des autres) / racine((variance tutorés + variance autres) / 2), variances **non pondérées** ; tableau avant / après (poids tronqués) avec la colonne « |SMD| < 0,1 ».
10. **Retouche unique** (D-56) : si au moins une ligne a |SMD| ≥ 0,1 après pondération, refaire score → poids → équilibre une seule fois en ajoutant au score les carrés des variables numériques ; garder les deux tableaux ; rapporter le résultat final tel quel. Le résultat doit indiquer si la retouche a été appliquée.
11. **Chaîne de conception** : une fonction qui enchaîne 4 à 10 pour une population donnée et une fenêtre d'activité donnée et renvoie un dictionnaire (X, modèle, score, support, poids bruts et tronqués, bornes, tailles effectives, tableau d'équilibre, retouche appliquée ou non). Elle doit pouvoir être relancée telle quelle en C11 sur les variantes (L = 6, 10, fenêtre 1 à 2, seuils 3 et 5) et sur des tirages bootstrap.
12. **Figure du DAG** : `dessiner_dag(chemin)` avec matplotlib (aucune nouvelle bibliothèque), → `docs/figures/05_dag.png`. Boîtes arrondies (titre + sous-titre) :
    - en haut à gauche « Profil à la rentrée » / « âge, note du bac, bourse, emploi… » ; en haut à droite « Activité des semaines 1 à 8 » / « notes, absences, connexions, devoirs » → couleur « à prendre en compte » (vert-bleu) ;
    - au milieu à gauche « Tutorat commencé » / « au plus tard en semaine 8 » ; au milieu à droite « Décrochage » / « semaines 9 à 30 » → couleur « tutorat et résultat » (violet) ;
    - en bas au centre « Activité après le début du tutorat » / « médiateur : ne pas prendre en compte » → gris ;
    - tout en bas au centre « Facteurs non mesurés » / « motivation, famille, santé (E-value) » → gris, bordure en pointillés ;
    - flèches : profil → activité, tutorat, décrochage ; activité → tutorat, décrochage ; tutorat → décrochage (épaisse, violette, étiquette « effet cherché ») ; tutorat → activité après le début → décrochage ; facteurs non mesurés → tutorat et décrochage (pointillés) ;
    - légende des 4 couleurs ; aucune flèche ne traverse une boîte ni un texte ; texte lisible (taille ≥ 10).

## Partie B — `notebooks/05_causal.ipynb` (première partie)
Il importe `src/` et lit `data/processed/` (sans relancer le pipeline). Chaque tableau et chaque figure est suivi d'une phrase pour un conseiller pédagogique, avec des chiffres calculés par le code. Sections :
1. **Ce qu'on cherche** : la question causale, les deux pièges (biais de sélection, temps immortel) et la démarche « conception d'abord » (D-59), en quelques phrases, **sans** aucun chiffre de décrochage par équipe.
2. **Le moment d'entrée en tutorat** : répartition des semaines de début (réutiliser la figure `02_debut_tutorat.png` par un lien Markdown, pas de doublon), % cumulé, motifs ; tableau « ce qui précède l'entrée » et sa lecture (« le tutorat arrive juste après une mauvaise passe »).
3. **Le DAG** : figure `05_dag.png` ; les trois portes dérobées (profil, activité, facteurs non mesurés) ; ce qu'on prend en compte, ce qu'on ne prend surtout pas en compte (médiateur, `nb_seances`, `type_tuteur`, `motif_orientation`) et pourquoi ; la limite de la fenêtre 1 à 8 (D-55).
4. **Le choix de la photo** : tableau des photos (L = 4 à 12) et la justification de L = 8 (D-53, D-54) ; effectifs de la photo retenue.
5. **Le score de propension** (CA-02) : tableau des rapports de cotes avec une phrase sur les profils les plus souvent orientés vers le tutorat (vocabulaire : « associé à une orientation plus fréquente ») ; AUC et sa lecture ; distribution du score par équipe (deux histogrammes superposés, bornes du support commun en traits verticaux) → `docs/figures/05_score_propension.png` ; effectifs hors support.
6. **Les poids et l'équilibre** (CA-03) : résumé des poids (avant / après troncature, bornes, nombre modifiés, tailles effectives) ; tableau d'équilibre complet ; love plot (une ligne par variable, |SMD| ou SMD avant et après, traits à ±0,1, libellés en français lisibles) → `docs/figures/05_love_plot.png` ; conclusion sur le critère (atteint ou non, retouche ou non), écrite par le code.
7. **Et ensuite** : une phrase : l'effet (CA-04) ne sera calculé qu'après la relecture R02 de cette conception.
- Vocabulaire : aucune affirmation sur l'effet du tutorat dans ce notebook ; rien n'est encore connu de l'effet.
- Avant de commiter : relire le notebook pour vérifier qu'aucune sortie ne compare T, E ou la survie entre équipes.

## Partie C — Tests (`tests/test_causal.py`)
- Population de la photo sur une petite base inventée (6 à 8 étudiants) : T ≤ L exclu ; début ≤ L → `tutore_photo` = 1 ; début > L ou hors suivi (ex. 45) → 0 ; semaine de début inconnue exclue ; variante avec `T_seuil3`.
- Activité moyenne : moyenne sur la fenêtre en ignorant les vides ; semaines hors fenêtre ignorées ; identifiants en double acceptés.
- Covariables : aucune colonne interdite ; `ErreurCausal` si on en ajoute une.
- Poids stabilisés : score [0,2 ; 0,5 ; 0,8], tutoré [1 ; 0 ; 1] → poids [3,333 ; 0,667 ; 0,833] (P(tutoré) = 2/3).
- Troncature : bornes = percentiles 1 et 99 ; valeurs extrêmes ramenées aux bornes ; nombre de poids modifiés.
- Différence standardisée : valeur connue sur un petit exemple ; poids tous égaux → même résultat que sans poids ; le dénominateur ne change pas quand les poids changent.
- Support commun : bornes sur un petit exemple.
- Invariants sur `data/processed/` (ignorés proprement s'il manque) : sur la photo de la semaine 8, tous les T > 8 ; `tutore_photo` ∈ {0, 1} ; aucun étudiant à semaine de début inconnue ; `tutore_photo` = 1 ⇒ début ≤ 8.

## Contrôles attendus
Prototype de la session de pilotage (statsmodels 0.15.0, pandas 2.3.3, codage de `survie.preparer_donnees_cox`), à comparer ; en cas d'écart, le signaler et l'expliquer, sans forcer le code :
- Entrée en tutorat : 1 245 débuts connus pendant le suivi (semaines 3 à 25), dont 851 (68,4 %) au plus tard en semaine 8 ; motifs : notes faibles 486, absences répétées 326, signalement enseignant 240, demande personnelle 203.
- « Ce qui précède l'entrée » (k : commencent / éligibles ; écarts connexions, devoirs, notes, absences) : 3 : 180 / 4 879 ; −0,42 −0,36 −0,93 +0,59 · 4 : 143 / 4 617 ; −0,37 −0,28 −0,54 +0,47 · 5 : 130 / 4 384 ; −0,46 −0,38 −0,50 +0,46 · 6 : 150 / 4 158 ; −0,48 −0,41 −0,56 +0,60 · 7 : 131 / 3 913 ; −0,36 −0,34 −0,61 +0,52 · 8 : 113 / 3 716 ; −0,52 −0,32 −0,74 +0,57 · 9 : 120 / 3 543 ; −0,57 −0,30 −0,74 +0,64 · 10 : 95 / 3 375 ; −0,18 −0,15 −0,44 +0,43 · 11 : 91 / 3 254 ; −0,32 −0,32 −0,60 +0,45 · 12 : 77 / 3 145 ; −0,40 −0,43 −0,71 +0,43.
- Tableau des photos (L : sur la photo ; sortis avant [dont décrochages] ; tutorés (%) ; non tutorés ; futurs tutorés (%) ; débuts couverts ; tutorés partis avant ; inconnus retirés) :
  4 : 4 694 ; 301 [285] ; 310 (6,6 %) ; 4 384 ; 921 (21,0 %) ; 25,9 % ; 4 ; 5 · 6 : 4 473 ; 522 [501] ; 560 (12,5 %) ; 3 913 ; 635 (16,2 %) ; 48,4 % ; 23 ; 5 · **8 : 4 316 ; 680 [656] ; 773 (17,9 %) ; 3 543 ; 389 (11,0 %) ; 68,4 % ; 45 ; 4** · 10 : 4 225 ; 771 [733] ; 971 (23,0 %) ; 3 254 ; 174 (5,3 %) ; 85,9 % ; 62 ; 4 · 12 : 4 156 ; 840 [794] ; 1 116 (26,9 %) ; 3 040 ; 6 (0,2 %) ; 99,5 % ; 83 ; 4.
- Score (photo de la semaine 8, fenêtre 1 à 8) : 18 colonnes ; aucun étudiant sans note sur les semaines 1 à 8 ; AUC 0,727 ; score des tutorés [0,023 ; 0,871], des autres [0,010 ; 0,738] ; support commun [0,023 ; 0,738] ; 54 hors support (8 tutorés, 46 non) ; rapports de cotes les plus marqués : boursier 1,64 ; absences moyennes 1,30 (par absence) ; note moyenne 0,69 (par point) ; Génie civil 0,70.
- Poids : avant troncature moyenne 1,004, min 0,206, max 7,76 ; bornes de troncature [0,289 ; 2,794] ; 88 poids modifiés ; tailles effectives 518 / 773 (tutorés) et 3 431 / 3 543.
- Équilibre : 24 lignes ; |SMD| maximal 0,757 avant (note moyenne), 0,060 après (log2 de la distance) ; aucune ligne ≥ 0,1 → pas de retouche.

## Livraison
- Commits : `DA-03 : date de fin du suivi sans pd.Timedelta (avertissement numpy) (#6)` (étape 0) ; `CA-01 : DAG, entrée en tutorat et photo de la semaine 8 (#16)` ; `CA-02 : score de propension et support commun (#19)` ; `CA-03 : poids stabilisés, équilibre et love plot (#20)` (le notebook complet avec ce dernier) ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus.
- **Ne pas commencer CA-04** : le calcul de l'effet attend la relecture R02.
