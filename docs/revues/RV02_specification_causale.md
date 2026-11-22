# RV02 — Spécification causale et conception, CA-01 à CA-03 (relecture du 22/11/2026)

Demande : `docs/consignes/R02_relecture_specification_causale.md`. Clone relu : commit `1556fbd` (C10 exécutée, D-52 à D-60).
Règle D-59 respectée pendant la relecture : aucune comparaison de T, E, de la survie ou du décrochage entre tutorés et non tutorés. Les seuls calculs faits sur T et E sont des comptes toutes équipes confondues (exception prévue par C10) et une mesure de durée faite avec un groupe **tiré au hasard**, dont aucun résultat n'a été lu.

## Résumé

La conception est **conforme** à D-53 à D-56. Tous les contrôles de C10 sont retrouvés à l'identique, les fonctions vérifiées donnent les mêmes valeurs qu'un calcul indépendant, et aucun fichier ne compare le décrochage entre équipes (D-59). La photo de la semaine 8 élimine bien le temps immortel.
En revanche, **la spécification n'est pas encore figée** pour CA-04 et CA-05. Plusieurs choix restent ouverts : la retouche dans le bootstrap, les poids, le budget de 15 min et certaines variantes. Le Cox dépendant du temps de D-58 ajuste sur le médiateur que D-55 exclut. La chaîne de conception plante sur un tirage bootstrap brut et sur le bonus « boursiers ».
**Constats : 🔴 0 · 🟠 2 · 🟡 6.**

## Constats

### RV02-01 🟠 Des choix de CA-04 et CA-05 restent ouverts : à écrire avant le calcul de l'effet
- Où : `docs/decisions.md` (D-56, D-57, D-58) ; `src/causal.py:426-454` (`chaine_de_conception`).
- Constat : D-53 à D-59 fixent l'essentiel, mais les 8 points ci-dessous pourraient encore être tranchés **après** avoir vu le résultat.

  | # | Choix ouvert | Ce que disent les décisions | Fait mesuré | Proposition |
  |---|---|---|---|---|
  | 1 | Retouche (carrés) **dans le bootstrap** | D-57 : « toute la chaîne est refaite à chaque tirage » ; or la chaîne contient la retouche conditionnelle de D-56 | Sur 100 tirages de la photo (graine 42), la 1re tentative dépasse 0,1 dans **8** tirages : max \|SMD\| médian 0,073, 90e percentile 0,098, max 0,13. La retouche n'atteint le critère dans **aucun** des 8 | Choisir entre (a) la chaîne telle quelle, qui mélange deux estimateurs dans la distribution bootstrap, et (b) la spécification de l'analyse principale (sans carrés) figée pour tous les tirages, avec la part des tirages hors critère rapportée. Recommandation : (b), plus simple à expliquer ; de toute façon, la retouche ne corrige rien dans ces tirages |
  | 2 | Mécanique d'un tirage | « 500 tirages avec remise, graine 42 » | Un tirage brut plante (RV02-03). 0 échec et 0 avertissement sur 100 tirages remis à zéro | Écrire : un seul générateur `default_rng(SEED)` pour tous les tirages, index remis à zéro, et la règle en cas d'échec (tirage remplacé et compté), pour qu'aucun tirage ne soit écarté « à la main » |
  | 3 | Poids utilisés en CA-04 | D-56 : troncature ; D-57 ne dit pas lesquels | — | Écrire « poids tronqués, les mêmes que pour l'équilibre » |
  | 4 | Cox pondéré | Efron, Schoenfeld « rank » | lifelines émet un `StatisticalWarning` (poids non entiers) pour le Cox, le Kaplan-Meier et le test de proportionnalité, et conseille `robust=True` | Écrire le choix de `robust` (sans effet sur l'estimation ni sur l'IC bootstrap), et que le test de Schoenfeld sur un modèle pondéré n'est qu'indicatif |
  | 5 | RMST et risque à 30 semaines | « aire entre la fin de la semaine 8 et la semaine 30 » | — | Écrire l'échelle (durée = T − 8, de 0 à 22) et la fonction (`restricted_mean_survival_time` de lifelines, courbe en escalier). Une somme « à droite » des S(t) décalerait la différence de RMST d'exactement la différence des risques à 30 semaines |
  | 6 | E-value | « sur le RR… estimation et borne de l'IC la plus proche de 1 » | — | Écrire la formule quand RR < 1 (on inverse le RR) et la règle « E-value = 1 si l'IC contient 1 » |
  | 7 | Budget de 15 min (`CLAUDE.md` §4) | 500 tirages + 200 par variante ; repli : variantes à 100 | **0,35 s par tirage** sur ce PC : 0,23 s de conception, plus 0,12 s pour les courbes, le RMST et le Cox, mesurées avec un groupe tiré au hasard. Cela donne 2,9 min pour l'analyse principale, 7,0 min pour 6 variantes × 200 et 5,8 min pour le bonus 2 × 500, soit **15,7 min**, sans compter le reste de `run_all.py` | Fixer le nombre de tirages du **bonus**, que le repli de D-57 ne couvre pas (ex. 200 tirages → 2,3 min), et dire si le bootstrap est relancé par `run_all.py` |
  | 8 | Variantes de D-58 | Liste des variantes | **Support strict** : la règle n'est pas dite (nouvelle chaîne sur les étudiants dans le support, ou mêmes poids ?). **L = 6** : la retouche s'applique et le critère reste manqué (0,115 → 0,124 sur la note moyenne ; 2 → 1 ligne ≥ 0,1). **Seuil de 5 semaines** : 2 étudiants de la photo ont un T de référence ≤ 8, donc seulement 4 à 7 semaines d'activité sur 8 dans `base_periode_personne` | Écrire la règle du support strict ; à L = 6, rapporter le résultat tel quel (D-56 le prévoit déjà) ; signaler les 2 étudiants |
- Preuve : script temporaire hors dépôt (100 tirages avec `default_rng(42)`, chaîne relancée sur chaque tirage remis à zéro), chronométrage sur le PC de Saliou, avertissements capturés pendant un ajustement lifelines avec un groupe aléatoire.
- Impact : chaque point laissé ouvert peut être tranché au vu du résultat, ce que D-59 veut empêcher. Le point 7 met en jeu la limite de 15 min de `run_all.py`.
- Correction proposée : une décision (D-61, ou des compléments à D-57 et D-58) qui fixe ces 8 points avant C11.

### RV02-02 🟠 Le Cox dépendant du temps (D-58, point 3) ajuste sur le médiateur exclu par D-55
- Où : D-58 point 3, comparé à D-55 (DAG : « tutorat → activité après son début → décrochage (médiateur) ») et au notebook 05, cellule 10 (« l'ajuster effacerait une partie de l'effet que l'on cherche »).
- Constat : la spécification alternative ajoute « la moyenne de chaque variable d'activité sur les semaines 1 à t − 1 ». Chez un tutoré, cette moyenne contient l'activité **postérieure au début du tutorat** à partir de la deuxième semaine qui suit le début (convention de D-39). C'est exactement le médiateur que D-55 interdit d'ajuster.
- Preuve :
  - les textes de D-58 (point 3) et de D-55 se contredisent sur ce point ;
  - `tutorat_commence` vaut 1 sur 24 119 semaines-étudiant (contrôle de C06). Sur toutes ces semaines, sauf la première après le début, la covariable inclut au moins une semaine postérieure au début ;
  - la règle « médiane si aucune » n'est pas définie en semaine 1 : aucun étudiant n'a alors de semaine antérieure.
- Impact : ce modèle estime l'effet « à activité passée égale », c'est-à-dire **hors** de la part qui passe par l'activité. Il sera plus proche de zéro que l'effet total, par construction. Avec la flèche « facteurs non mesurés → activité » que D-55 écrit, l'ajustement ouvre en plus un chemin par collision. Présenté comme une simple sensibilité de l'analyse principale, il laisserait croire à un désaccord entre les méthodes alors qu'il répond à une autre question.
- Correction proposée (Saliou choisit, avant CA-05) :
  - (a) **figer** la covariable d'un tutoré à son début : moyenne des semaines 1 à min(t − 1, semaine de début) ;
  - (b) garder la spécification et la présenter comme un « effet hors médiation par l'activité », attendu plus faible ;
  - (c) profil seul, sans activité.

  Dans tous les cas, écrire la règle de la semaine 1. Recommandation : (a).

### RV02-03 🟡 La chaîne de conception plante sur un tirage bootstrap brut et sur le bonus F8
- Où : `src/survie.py:204-224` (`preparer_donnees_cox`, jointure sur l'index à la ligne 223) ; `src/survie.py:188-193` (`indicatrices`) ; `src/causal.py:234-252` et `273-280`.
- Constat et preuve :
  1. `population.sample(n=4316, replace=True, random_state=42)` garde 1 643 index en double. `preparer_donnees_cox` joint les indicatrices sur l'index et renvoie **4 498 232 lignes** au lieu de 4 316, sans erreur. `covariables_du_score` s'arrête ensuite sur une `ValueError`. Avec `reset_index(drop=True)`, 100 tirages passent sans erreur.
  2. Bonus (D-58), sous-groupe des boursiers : `ErreurSurvie : Modalité de référence « Non » absente pour boursier`. Le sous-groupe des non-boursiers passe, car l'indicatrice disparaît d'elle-même. La chaîne n'a pas d'option pour retirer une variable du score, alors que D-58 demande un « score refait sans la variable boursier ».
  3. `ajuster_score` ne vérifie pas `modele.converged`. Aucun cas de non-convergence sur 100 tirages, mais rien ne le signalerait.
- Impact : C11 s'arrêterait au premier tirage écrit de la façon la plus naturelle. Et si `preparer_donnees_cox` était appelé seul sur un tirage (par exemple pour les durées), la table exploserait sans message.
- Correction proposée :
  - remettre l'index à zéro au début de `chaine_de_conception` (ou dans une fonction `tirage_bootstrap`) ;
  - ajouter un paramètre `variables_exclues` pour le bonus ;
  - lever `ErreurCausal` si le modèle n'a pas convergé ;
  - ajouter un test sur un tirage avec doublons (RV02-05).

### RV02-04 🟡 Garde-fous : le contrôle par les noms laisse passer des colonnes, et la fenêtre n'est pas liée à la photo
- Où : `src/causal.py:26-29` et `226-231` (`verifier_colonnes_autorisees`) ; `src/causal.py:426-438`.
- Constat et preuve :
  - `verifier_colonnes_autorisees` accepte `type_evenement`, `duree_apres_photo`, `id_etudiant` et `etat_activite_prec` (« evenement » n'est interdit que comme nom exact) ;
  - `chaine_de_conception(photo de la semaine 8, …, fenetre=(1, 12))` s'exécute sans erreur. L'activité des semaines 9 à 12, postérieure à la photo et interdite par D-55, entre alors dans le score sans aucune alerte.
- Impact : en C11, les variantes L = 6 et L = 10 changent la fenêtre. Une fenêtre mal recopiée ferait entrer dans le score l'avenir et le médiateur sans que rien ne le signale.
- Correction proposée :
  - passer la semaine de la photo à `chaine_de_conception` et lever `ErreurCausal` si `fenetre[1] > semaine` ;
  - remplacer le contrôle par exclusion par une **liste positive** : X ne contient que `colonnes_numeriques_du_score()` et les indicatrices de `VARIABLES_COX_QUALITATIVES`, sur le principe de D-43 (« jamais par exclusion »).

### RV02-05 🟡 Tests : 6 mutations sur 8 passent inaperçues
- Où : `tests/test_causal.py`.
- Preuve : chaque mutation a été appliquée à `src/causal.py` sur une copie hors dépôt, puis `pytest tests/test_causal.py` a été relancé.

  | Mutation | Résultat |
  |---|---|
  | AUC : n0(n0 + 1)/2 au lieu de n1(n1 + 1)/2 | 11 réussis : le test n'a que n1 = n0 et aucun ex aequo |
  | Retouche jamais appliquée | 11 réussis |
  | Retouche toujours appliquée | 11 réussis |
  | Références retirées de la matrice d'équilibre | 11 réussis |
  | « Ce qui précède l'entrée » sur les semaines k − 2 à **k** (semaine du début incluse) | 11 réussis, alors que ce tableau fonde le constat de D-55 |
  | Futurs tutorés comptés jusqu'à la semaine 52 (hors suivi compris) | 11 réussis |
  | Photo avec T ≥ L au lieu de T > L | détectée (invariant sur les données) |
  | Troncature aux percentiles 5 et 95 | détectée |
- Impact : une erreur sur la retouche, la matrice d'équilibre ou les tableaux de CA-01 passerait inaperçue, et ce sont précisément les éléments qui fondent la spécification figée.
- Correction proposée (tests à écrire avant CA-04) :
  1. la chaîne sur un tirage avec doublons, et le même résultat sur une simple permutation de la population ;
  2. une retouche déclenchée sur un petit cas construit, avec `equilibre_initial` conservé ;
  3. la matrice d'équilibre avec ses références et la modalité « (manquant) » ;
  4. une fenêtre postérieure à la photo refusée ;
  5. l'AUC avec n1 ≠ n0 et des ex aequo ;
  6. pour CA-04, le risque à 30 semaines, le RMST et l'E-value sur des exemples calculés à la main (RR = 0,5 → E-value = 2 + √2 ≈ 3,41) ;
  7. la même graine donne les mêmes IC.

### RV02-06 🟡 Équilibre tenu de justesse sur des variables absentes du tableau d'équilibre
- Où : `src/causal.py:368-386` (`matrice_equilibre`, 24 lignes) ; notebook 05, cellule 21.
- Constat : le tableau ne vérifie que des moyennes sur les semaines 1 à 8 et les modalités du score. J'ai calculé les écarts, avec les poids tronqués de la chaîne principale, sur des variables mesurées avant la photo mais absentes du score. Plusieurs restent au bord du seuil :

  | Variable hors score | SMD avant | SMD après |
  |---|---:|---:|
  | Notes des semaines 7 et 8 | −0,382 | **+0,0997** |
  | Mention du bac : Passable | +0,388 | **+0,097** |
  | Mention du bac : Assez bien | −0,137 | −0,094 |
  | Connexions des semaines 7 et 8 | −0,494 | −0,092 |
  | Région la plus déséquilibrée (Kaolack) | +0,105 | +0,076 |

  Sans problème : messages des semaines 1 à 8 (+0,004), formulaire de suivi (−0,009), nombre de semaines inactives sur 1 à 8 (−0,028), inactif en semaine 8 (−0,020).
- Interprétation (prudente) :
  - la mention découle de la note du bac (D-10). L'écart montre que la pondération équilibre la **moyenne** de la note, pas la forme de sa distribution ;
  - pour 540 des 773 tutorés (début au plus tard en semaine 6), les semaines 7 et 8 sont postérieures au début. Leur écart peut donc venir de l'effet du tutorat (médiateur) plutôt que d'un facteur de confusion : il ne faut pas les ajouter au score sans décision.
- Impact : le « \|SMD\| maximal 0,060 » du notebook donne une image plus confortable que la réalité. Le critère est atteint, mais de justesse sur des variables liées au décrochage.
- Correction proposée : afficher ces lignes dans le notebook comme **diagnostic hors critère**, avec la phrase d'interprétation. Saliou décide si un ajustement est nécessaire. Le carré de la note du bac fait déjà partie de la retouche prévue ; l'activité des semaines 7 et 8 ne doit pas entrer dans le score, puisque c'est en partie un médiateur.

### RV02-07 🟡 Ce qui est écrit d'avance (figure du DAG, biais de D-59) est incomplet
- Où : `docs/figures/05_dag.png` (`src/causal.py:515-561`) ; C10 point 12 ; D-55 ; D-59.
- Constat 1 (figure) :
  - D-55 écrit « facteurs non mesurés → tutorat, **activité**, décrochage ». C10 n'a demandé que les flèches vers le tutorat et le décrochage : la figure omet donc « facteurs non mesurés → activité » (la consigne s'écarte ici de la décision) ;
  - la figure dessine « Activité des semaines 1 à 8 » et « Activité après le début du tutorat » comme deux boîtes distinctes, alors qu'elles se recouvrent. Chez les 773 tutorés de la photo, en moyenne 3,6 des 8 semaines de la fenêtre vont de la semaine du début à la semaine 8 (2,6 sans compter la semaine du début).
- Constat 2 (biais de D-59) : deux mécanismes propres à cette photo ne sont pas écrits.
  - (a) **La photo s'appuie sur jusqu'à 3 semaines d'information postérieure.** La semaine T d'un décrochage silencieux est la première des 4 semaines inactives. Les 83 décrochages silencieux avec T = 6, 7 ou 8 (34, 26 et 23 ; compte toutes équipes, exception de C10) ne sont exclus de la photo que grâce aux semaines 9 à 11. Inversement, 15 étudiants de la photo étaient inactifs en semaine 8 (dont 3 depuis la semaine 7) et ne sont sur la photo que parce que leur série d'inactivité ne s'est pas prolongée pendant les semaines 9 à 11. Si le tutorat aide à reprendre, il influence donc qui figure sur la photo. Les effectifs sont petits : l'effet est probablement faible.
  - (b) **L'effet du tutorat pendant les semaines 1 à 8 n'est pas mesuré** : 45 tutorés sont partis avant la photo. L'estimation porte sur « avoir commencé le tutorat au plus tard en semaine 8, chez les étudiants encore présents à la fin de la semaine 8, sur le décrochage des semaines 9 à 30 ».
- Impact : la note de synthèse doit dire exactement ce qui est estimé (`CLAUDE.md` §6, honnêteté), et D-59 demande que les biais soient écrits **avant** le résultat.
- Correction proposée :
  - ajouter à la figure deux flèches en pointillés : « facteurs non mesurés → activité » et « tutorat → activité des semaines 1 à 8 (débuts en semaines 3 à 7) » ;
  - compléter D-59 avec (a), (b) et la phrase qui décrit ce qui est estimé.

### RV02-08 🟡 Sous Windows, `run_all.py` réécrit les CSV avec des fins de ligne CRLF (pandas 2.3.3)
- Où : `src/base_survie.py:274` et `src/nettoyage/commun.py:50, 57` (`to_csv` sans `lineterminator`) ; `.gitattributes` (fins de ligne LF « comme le code les écrit »).
- Preuve : après `python run_all.py`, `git ls-files --eol data/processed/*.csv` affiche `w/crlf` pour les 7 CSV, et `git status` signale `data/processed/base_periode_personne.csv` et `docs/journal_nettoyage.md`. Pourtant `git diff` est vide, le journal est identique octet pour octet, et `base_periode_personne.csv` contient les mêmes valeurs. Ce fichier pèse 121 939 octets de plus, soit un retour chariot par ligne.
- Impact : `git status` signale une fausse modification, ce que la règle `.gitattributes` ajoutée après RV01 voulait éviter. Une session pourrait commiter un « changement » vide ou conclure à tort que le pipeline n'est pas reproductible. Le contenu, lui, est reproductible.
- Correction proposée : `lineterminator="\n"` dans les trois `to_csv`. Avec pandas 2.x, la valeur par défaut est `os.linesep`, donc CRLF sous Windows.

## Réponses aux questions de R02

1. **La spécification est-elle complète ?** Non : 8 choix restent ouverts (RV02-01), et le Cox dépendant du temps doit être redéfini (RV02-02). Le reste de D-57 et D-58 se code sans choix libre : courbes pondérées, risque à 30 semaines, différence et RR, HR d'Efron, IC percentile, seuils, L = 6 et 10, fenêtre 1 à 2.
2. **DAG.**
   - Je n'ai trouvé aucun autre facteur de confusion mesuré avant la photo : messages et formulaires de suivi des semaines 1 à 8, 14 régions et semaines d'inactivité sont équilibrés après pondération. Mention et activité récente sont équilibrées de justesse (RV02-06).
   - Aucune variable du score n'est une conséquence du tutorat, hormis la fenêtre 1 à 8 déjà signalée. Cette limite est plus large qu'il n'y paraît : 3,6 semaines sur 8 en moyenne chez les tutorés (RV02-07).
   - L'exclusion de `motif_orientation`, `type_tuteur` et `nb_seances` est justifiée : ces variables n'existent que pour les tutorés, ou décrivent le déroulement du tutorat (la dose).
   - La cohorte en variable du score ne pose pas de problème : SMD 0,039 avant, 0,003 après. Le Cox pondéré à une variable de D-57 n'a pas besoin de strate, puisque la pondération équilibre la cohorte.
3. **Temps immortel.** Il est éliminé dans l'analyse principale. Cas limites vérifiés sur le code et les tests :
   - début en semaine 8 et décrochage en semaine 9 : tutoré, suivi à partir de la semaine 9 ;
   - censure exactement en semaine 8 : exclu (T ≤ 8) ;
   - tutorat la semaine de T (D-37) : exclu si T ≤ 8, sinon non tutoré ;
   - tutorat hors suivi (D-25) : non tutoré (testé) ;
   - semaine de début inconnue (D-26) : exclu (4 étudiants) ;
   - seuils de 3 et 5 semaines : tutoré si début ≤ L < T_seuil (`population_photo(duree=…)`).

   Reste un résidu, sans rapport avec le temps immortel : l'information postérieure contenue dans la définition du décrochage silencieux (RV02-07 a).
4. **Code.**
   - `difference_standardisee`, `poids_stabilises`, `tronquer_poids`, `taille_effective`, `support_commun` et `auc_par_les_rangs` sont exacts. Les contre-calculs indépendants donnent les mêmes valeurs : AUC = Mann-Whitney = 0,727147 ; SMD de la note moyenne −0,047844 ; poids identiques ; taille effective 517,662.
   - `activite_moyenne` accepte les doublons, et `covariables_du_score` recalcule ses médianes sur la population reçue, ce qui est cohérent avec « toute la chaîne refaite ».
   - La logique de la retouche est juste, mais son usage dans le bootstrap n'est pas décidé (RV02-01), et la chaîne n'est pas prête pour un tirage brut (RV02-03).
5. **Garde-fous.** Insuffisants (RV02-04). D-59 est respectée partout :
   - le code ne contient qu'une exception, prévue par C10 (`dont_decrochages`, toutes équipes) ;
   - le notebook et ses 22 sorties, les tests et les trois figures `05_*` ne comparent jamais T, E ou la survie entre équipes.
6. **Tests.** Voir RV02-05 : mutations qui passent inaperçues et 7 tests à écrire avant CA-04.
7. **Reproductibilité.** Voir « Vérifié sans problème ». Seul écart : les fins de ligne sous Windows (RV02-08).
8. **Lisibilité : les 3 fonctions de `causal.py` les plus difficiles à expliquer en soutenance.**
   - `ce_qui_precede_entree` (lignes 132-158) : trois définitions imbriquées (début connu, déjà commencé avec `fillna(False).astype(bool)`, éligibles), une fenêtre `max(1, k − 2)` à `k − 1`, puis un passage par des masques numpy pour écarter les vides. Le « − 1 » décisif n'est protégé par aucun test (RV02-05).
   - `ligne_photo` (lignes 181-207) : 13 indicateurs dans un seul dictionnaire, dont « futurs tutorés » et « tutorés partis avant », définis par des conditions combinées avec `fillna(False)`. Une petite fonction par indicateur se lirait mieux.
   - `chaine_de_conception` avec `score_poids_equilibre` (lignes 404-454) : le résultat se construit en deux temps (dictionnaire, puis `update`), il y a deux tableaux d'équilibre, et la provenance des poids n'est pas évidente (`poids` = tronqués, `poids_bruts` = avant troncature). Il faut savoir expliquer pourquoi la matrice d'équilibre ne change pas après la retouche.

   À préparer aussi : `matrice_equilibre`, qui s'appuie sur des fonctions internes de `survie` (`variables_du_cox`, `modalites_ordonnees`).

## Questions (points sans preuve suffisante)
- La variante « fenêtre des semaines 1 à 2 » sera jugée équilibrée sur sa propre matrice (max \|SMD\| 0,066), alors que D-55 rapporte des écarts de −0,33 (notes) et +0,27 (absences) sur les semaines 1 à 8 avec ces poids. Faut-il afficher les deux tableaux pour cette variante ?
- Le Cox dépendant du temps (tous les étudiants dès la semaine 1, HR conditionnel) et la photo (étudiants présents en semaine 8, effet sur les semaines 9 à 30) n'estiment pas la même quantité. Comment les présenter côte à côte sans laisser croire qu'ils devraient coïncider ?

## Vérifié sans problème
- **Contrôles de C10 retrouvés à l'identique** :
  - entrée en tutorat : 1 245 débuts, dont 851 (68,4 %) au plus tard en semaine 8, et les 4 motifs ;
  - tableau « ce qui précède l'entrée » : les 10 lignes ;
  - tableau des photos L = 4 à 12 : 4 316 étudiants sur la photo, 773 tutorés, 389 futurs tutorés (11,0 %) ;
  - score : 18 colonnes, AUC 0,727, support [0,023 ; 0,738], 54 hors support (8 / 46) ;
  - poids : 1,004 / 0,206 / 7,76, bornes [0,289 ; 2,794], 88 modifiés, tailles effectives 518 et 3 431 ;
  - équilibre : 24 lignes, 0,757 → 0,060, pas de retouche.
- **Reproductibilité** depuis un clone neuf (Windows, Python 3.14.3) :
  - `pip install -r requirements.txt` réussi en 7 min 03 s (pandas 2.3.3, statsmodels 0.15.0, lifelines 0.30.3) ;
  - `pytest` : **145 réussis**, 0 échoué (42 s ; 2 avertissements de convergence dans `test_survie.py`, hors périmètre) ;
  - `python run_all.py` en 27 s ;
  - notebook 05 exécuté de haut en bas sans erreur (31 s), avec les 22 sorties texte identiques à celles commitées. Les figures `05_*` réécrites sont identiques octet pour octet (`git status` propre ensuite).
- **Bootstrap** (100 tirages remis à zéro) : aucune séparation et aucune non-convergence. Les plus petites modalités du score restent présentes dans les deux équipes : région manquante 14 tutorés / 58 autres, emploi manquant 33 / 142. Distance minimale 0,9 km, donc log2 toujours défini.
- **Secrets** : aucune clé ni aucun fichier `.env` dans l'historique (code et documents depuis RV01 ; noms de fichiers sur tout l'historique).

## Limites de la relecture
- Par respect de D-59, rien n'a été calculé sur le décrochage par équipe. La faisabilité de CA-04 n'a été testée qu'en durée, avec un groupe tiré au hasard.
- La fréquence de la retouche dans le bootstrap repose sur 100 tirages, pas 500 : 8 % ± 3 % environ.
- Les durées ont été mesurées sur ce PC avec d'autres processus actifs : ce sont des ordres de grandeur.
- Le cahier des charges (F5) n'a été relu qu'à travers `CLAUDE.md`, les décisions et C10. Dans `src/survie.py`, seules `preparer_donnees_cox` et ses fonctions auxiliaires ont été relues.
- Linux et macOS n'ont pas été testés.
