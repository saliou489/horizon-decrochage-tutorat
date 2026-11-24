# Consigne C16 — LL-02 : version 2 du prompt et comparaison avec la version 1 (issue #24)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C15 terminée, grille v1 remplie par Saliou (commit 643b041), **D-69 validée**, texte du gabarit v2 (étape 3) validé par Saliou.

## Contexte
Lis `CLAUDE.md` (§6 « LLM et données personnelles » et « Honnêteté des résultats », §7), puis **D-65, D-66, D-67 et D-69** (`docs/decisions.md`).

LL-02 évalue les fiches : mesure « avant » (version 1, notée par Saliou), version 2 du prompt, même grille sur les mêmes 20 fiches. Les défauts de la version 1, mesurés par le pilotage sur les 54 fiches (indicateurs de l'étape 2) :
- décimales écrites avec un point dans 48 fiches ; tutorat formulé « le statut est aucun » dans 24 ; nom de champ « semaine d'observation » dans 23 ;
- le multiplicateur n'est comparé à « un étudiant moyen » que dans 5 fiches ;
- actions : « entretien individuel » dans les 54 (alors que la fiche prépare déjà un entretien) ; « aménager l'emploi du temps » jamais proposé (l'emploi est un facteur dans 52 fiches) ; « informer sur les aides » jamais proposé (13 fiches « non boursier ») ; 22 fiches proposent une action qu'aucun fait n'appuie (surtout « suivre l'assiduité » pour un étudiant qui manque moins de séances que la promotion).

**Ce qui ne change pas** (pour que la comparaison porte sur le seul prompt) : les 54 entrées (`llm_entrees_semaine8.json`, identiques octet pour octet), les champs envoyés, les contrôles bloquants (`verifier_fiche`, mots interdits, longueurs), le schéma JSON, la liste des actions, le modèle `gemini-3.5-flash-lite`. Les indicateurs de l'étape 2 servent à **évaluer**, jamais à rejeter une fiche.

**Règles API (inchangées depuis C14)** : appels réels seulement à l'étape 4. La clé est lue par le code dans `.env` : tu n'ouvres pas ce fichier, tu ne l'affiches pas, tu ne le copies pas. Avant chaque commit, `git status` ne liste aucun fichier `.env…` (sauf `.env.example`). Échec réseau (WARP) ou de l'API autre qu'un quota : arrête-toi et signale-le, sans contournement.

Tu ne notes pas les fiches à la place de Saliou, tu ne modifies ni `src/prompts/fiche_v1.md` ni les fiches v1.

## Étape 0 — Grille v1 remise au format, sans changer une valeur
Constat : dans `docs/evaluation_fiches_llm.csv`, chaque ligne (en-tête compris) est entourée de guillemets, donc lue comme **une seule colonne** (Excel en français a mis chaque ligne dans une cellule). Les valeurs de Saliou sont justes, seul le format est cassé.

1. Dans `src/llm.py`, section 6 :
   - constantes `COLONNES_GRILLE` (les 8 colonnes actuelles, dans l'ordre) et `VALEURS_GRILLE` : `exactitude_humaine` ∈ {oui, non}, `ton` ∈ {1, 2, 3}, `stigmatisation` ∈ {oui, non}, `actions_pertinentes` ∈ {1, 2, 3} ; une case vide veut dire « pas encore notée » ;
   - `ecrire_grille_evaluation` utilise `COLONNES_GRILLE` (même fichier produit qu'aujourd'hui) ;
   - `lire_grille_evaluation(chemin)` : lit en texte (`sep=";"`, `encoding="utf-8-sig"`, `dtype=str`, `keep_default_na=False`) ; `ErreurLLM` claire si les colonnes ne sont pas exactement `COLONNES_GRILLE`, si un identifiant est en double, ou si une valeur sort de `VALEURS_GRILLE` (en citant la colonne et la valeur) ;
   - `resume_grille(grille)` : nombre de fiches entièrement notées (les 4 critères remplis), nombre d'« oui » en exactitude, ton moyen, nombre d'« oui » en stigmatisation, actions pertinentes moyennes, nombre de commentaires non vides (moyennes sur les fiches notées ; `None` si aucune).
2. Réécris le fichier **à son chemin actuel** : enlève les guillemets qui entourent chaque ligne, garde le BOM utf-8, le séparateur `;`, des fins de ligne LF, l'ordre des lignes. Vérifie avec `lire_grille_evaluation` : 20 lignes, mêmes identifiants qu'avant, et que `git diff` ne montre que la disparition des guillemets.
3. `.gitattributes` : ajoute `docs/*.csv text eol=lf` (comme pour `docs/*.md`), avec un commentaire.
4. Tests :
   - `lire_grille_evaluation` accepte une grille conforme (dont des cases vides) et refuse : une ligne entourée de guillemets (le cas réel), une colonne en moins, une valeur hors liste (`ton` = 4), un identifiant en double ;
   - `resume_grille` sur une petite grille construite dans le test (moyennes, cases vides ignorées) ;
   - invariant (ignoré proprement si le fichier manque) : chaque grille de `config.FICHIERS_GRILLE_EVALUATION` présente passe `lire_grille_evaluation` et contient exactement les identifiants de `echantillon_evaluation` des fiches de la même version (à écrire après l'étape 1).
5. Commit : `LL-02 : grille v1 remise au format, valeurs inchangées, et lecture contrôlée des grilles (#24)`.

## Étape 1 — Un fichier de fiches et une grille par version du prompt
Aujourd'hui, passer à `VERSION_PROMPT = "v2"` ferait régénérer les 54 fiches **dans le même fichier** et effacerait la version 1 (D-69, point 3, demande de la garder).

1. `src/config.py` (commentaires sur le pourquoi) :
   ```python
   VERSIONS_PROMPT = ("v1", "v2")
   VERSION_PROMPT = "v1"   # passe à "v2" à l'étape 4 seulement
   FICHIERS_FICHES_LLM = {v: DOSSIER_RESULTATS / f"llm_fiches_semaine{SEMAINE_FICHES}_{v}.json" for v in VERSIONS_PROMPT}
   FICHIER_FICHES_LLM = FICHIERS_FICHES_LLM[VERSION_PROMPT]
   FICHIERS_GRILLE_EVALUATION = {v: RACINE / "docs" / f"evaluation_fiches_llm_{v}.csv" for v in VERSIONS_PROMPT}
   FICHIER_GRILLE_EVALUATION = FICHIERS_GRILLE_EVALUATION[VERSION_PROMPT]
   ```
2. Renomme avec `git mv` (simple changement de nom, contenu identique, l'historique suit) :
   - `data/processed/resultats/llm_fiches_semaine8.json` → `llm_fiches_semaine8_v1.json` ;
   - `docs/evaluation_fiches_llm.csv` → `docs/evaluation_fiches_llm_v1.csv`.
3. `--verifier` repasse les contrôles sur **chaque** cache présent de `FICHIERS_FICHES_LLM` et affiche le résultat par version ; erreur claire si aucun cache n'existe. `--generer` et `--grille` restent sur la version courante.
4. Mets à jour les chemins cités dans le README et le notebook 06 (le tableau de bord suit `config.FICHIER_FICHES_LLM` sans changement).
5. `pytest` (tout passe, le tableau de bord lit toujours les 54 fiches v1), puis commit : `LL-02 : un fichier de fiches et une grille par version du prompt (#24)`.

## Étape 2 — Indicateurs automatiques de qualité (pour l'évaluation, jamais bloquants)
Dans `src/llm.py`, nouvelle section « 7. Indicateurs de qualité (LL-02, D-69) » (la ligne de commande devient la section 8). Ces fonctions ne changent jamais le statut d'une fiche.

1. `actions_appuyees(entree)` : ensemble des actions qu'un fait de l'entrée appuie (« entretien individuel » n'en fait jamais partie) :
   - « proposer un tutorat » si le statut du tutorat est « aucun », sinon « faire le point sur le tutorat en cours » ;
   - « aménager l'emploi du temps » si un facteur « emploi en parallèle des études » vaut « oui » ;
   - « informer sur les aides » si un facteur « bourse » vaut « non boursier » ;
   - « relancer sur les devoirs » si `devoirs_rendus` de l'étudiant < celui de la promotion (les deux connus) ;
   - « suivre l'assiduité » si `seances_manquees` de l'étudiant > celui de la promotion (les deux connus).

   Libellés des facteurs pris dans `config.LIBELLES_FACTEURS_FICHE`.
2. `indicateurs_fiche(fiche)` : dictionnaire calculé sur le texte de `situation` et `points_attention` :
   - `decimale_avec_point` : le motif `\d\.\d` apparaît ;
   - `tutorat_est_aucun` : le motif `\b(?:est|statut|étant)\s+(?:actuellement\s+)?aucun\b` apparaît (texte en minuscules) ;
   - `nom_de_champ` : « semaine d'observation » apparaît ;
   - `multiplicateur_compare` : « étudiant moyen » apparaît ;
   - `facteurs_chiffres` : nombre de facteurs dont `valeur_etudiant` contient un nombre ; `valeurs_citees` : parmi eux, ceux dont tous les nombres de `valeur_etudiant` figurent dans la fiche (`nombres_de`) ;
   - `facteurs` et `references_citees` : même chose avec `reference_promotion`, sur tous les facteurs ;
   - `actions`, `appuyees` (liste triée) ;
   - `action_sans_appui` : une action autre que « entretien individuel » n'est pas appuyée ;
   - `oubli_evitable` : une action appuyée manque **alors qu'une place restait** (moins de 3 actions, ou « entretien individuel » parmi elles) ;
   - `entretien_individuel` : « entretien individuel » est proposé ;
   - `combinaison` : les actions triées, jointes par « | ».
3. `resume_indicateurs(fiches)` : `DataFrame` (colonnes `groupe`, `indicateur`, `nombre`, `sur`), dans cet ordre :
   - groupe « contrôles » : fiches validées ; validées dès le premier essai (sur toutes les fiches) ;
   - groupe « forme » (sur les fiches rédigées, c'est-à-dire avec une `situation`) : nombre décimal écrit avec un point ; tutorat formulé « est aucun » ou « statut aucun » ; nom de champ « semaine d'observation » ;
   - groupe « facteurs » : multiplicateur comparé à « un étudiant moyen » (fiches) ; valeur de l'étudiant citée (sur les facteurs chiffrés) ; référence de la promotion citée (sur les facteurs) ;
   - groupe « actions » : au moins une action qu'aucun fait n'appuie ; action appuyée oubliée alors qu'une place restait ; « entretien individuel » proposé ; puis, pour chacune de « aménager l'emploi du temps », « informer sur les aides », « relancer sur les devoirs », « suivre l'assiduité » : « « X » quand un fait l'appuie » (nombre de fiches où X est choisie, sur celles où X est appuyée) ; enfin « combinaisons d'actions différentes » (`sur` vide).

   Avec 3 actions au plus, une fiche à 4 ou 5 actions appuyées ne peut pas toutes les proposer : les lignes « quand un fait l'appuie » n'ont pas à atteindre 100 %.
4. Tests unitaires sur de petites entrées et fiches construites dans le test : chaque règle de `actions_appuyees` (dont les valeurs `None`) ; `oubli_evitable` vrai avec « entretien individuel » et faux avec 3 actions appuyées ; les motifs (« 1.7 » oui, « 1,7 » non ; « le statut est aucun » oui, « n'a pas commencé de tutorat » non) ; `resume_indicateurs` sur 2 fiches.
5. Contrôle sur le cache v1 : `resume_indicateurs` doit redonner **exactement** le tableau « Contrôles attendus » plus bas (sinon, signale l'écart sans ajuster le code au tableau). Commit : `LL-02 : indicateurs automatiques de qualité des fiches (#24)`.

## Étape 3 — Gabarit v2 (texte validé par Saliou) et option `--limite`
1. Crée `src/prompts/fiche_v2.md` avec **exactement** le texte ci-dessous (entre les deux lignes `~~~`, sans elles), sans reformulation. Les lignes `{actions}` et `{entree}` sont remplacées par le code comme pour la v1.

~~~
## Instructions système

Tu aides un conseiller pédagogique de l'Institut Supérieur Horizon à préparer un entretien avec un étudiant. À partir de l'ENTRÉE (un objet JSON), tu rédiges une fiche courte, factuelle et bienveillante, en français correct (accents compris, par exemple « À la semaine »).

Sens des champs de l'entrée :
- risque_decrochage_pct : risque, estimé par un modèle statistique, que l'étudiant décroche avant la semaine horizon_semaines, sachant qu'il est encore inscrit à la semaine semaine_observation ; risque_moyen_promotion_pct : le même risque, en moyenne, dans sa promotion.
- facteurs : au plus 3 caractéristiques connues dès la rentrée qui, dans le modèle, sont associées à un risque plus élevé. valeur_etudiant : la valeur de l'étudiant ; reference_promotion : la valeur de comparaison dans la promotion ; multiplicateur : dans le modèle, le risque de l'étudiant est multiplié par cette valeur par rapport à celui d'un étudiant moyen de la promotion, à autres caractéristiques égales.
- activite et activite_promotion : moyennes par semaine sur les semaines indiquées (connexions à la plateforme, devoirs rendus, séances manquées, note moyenne sur note_maximum) ; null signifie « non renseigné ». Ce sont des observations, pas des éléments du score.
- tutorat : situation du tutorat à la semaine semaine_observation ; semaine_debut : semaine où le tutorat a commencé.

Règles :
1. Utilise uniquement les informations de l'entrée. N'invente ni cause ni circonstance personnelle (famille, santé, argent, motivation…).
2. Recopie les nombres de l'entrée exactement, en chiffres. Ne calcule rien : ni différence, ni rapport, ni arrondi. Comparer deux nombres de l'entrée (« moins que », « plus que ») est permis.
3. Écriture des nombres : virgule décimale (« 1,5 » et non « 1.5 ») ; nombre entier sans décimale (« 1 » et non « 1,0 ») ; pourcentage avec le symbole % (« <nombre> % »), jamais « pour cent » ; aucun nombre en lettres. Écris « la semaine <numéro> », jamais « la semaine d'observation », et ne cite aucun nom de champ de l'entrée.
4. Parle d'association, jamais de cause : « est associé à », « va de pair avec ». Pas de certitude : c'est un risque estimé, pas une prédiction.
5. Reste neutre et respectueux, sans jugement sur la personne. Écris « l'étudiant », sans aucune référence au genre, à l'origine ou à la santé.
6. situation : exactement 2 phrases, 300 caractères au plus.
   - Phrase 1, sur ce modèle : « À la semaine <semaine_observation>, le risque estimé que l'étudiant décroche d'ici la semaine <horizon_semaines> est de <risque_decrochage_pct> %, contre <risque_moyen_promotion_pct> % en moyenne dans sa promotion. »
   - Phrase 2, selon le statut du tutorat, exactement l'une de ces phrases :
     - « aucun » : « L'étudiant n'a pas commencé de tutorat. »
     - « en cours » : « L'étudiant suit un tutorat depuis la semaine <semaine_debut>. »
     - « signalé, semaine de début inconnue » : « Un tutorat est signalé pour l'étudiant, sans semaine de début connue. »
7. points_attention : 2 à 4 points, chacun une phrase de 180 caractères au plus.
   - Un point par facteur, dans l'ordre de l'entrée, sur ce modèle : « <facteur, avec une majuscule> : <valeur_etudiant> (<reference_promotion>) ; ce facteur est associé à un risque multiplié par <multiplicateur> par rapport à un étudiant moyen. »
   - Puis un point sur l'activité récente, sur ce modèle : « Semaines <semaines, reliées par « et »> : <devoirs_rendus> devoir rendu par semaine (promotion : <devoirs_rendus de la promotion>), <seances_manquees> séance manquée par semaine (promotion : <seances_manquees de la promotion>) et une note moyenne de <note_moyenne> / <note_maximum> (promotion : <note_moyenne de la promotion>). » Accorde au pluriel si besoin ; pour une valeur null, écris « non renseigné ».
   - S'il n'y a aucun facteur, ajoute un second point sur les connexions à la plateforme (étudiant et promotion).
8. actions : 2 ou 3 actions, recopiées mot pour mot dans cette liste :
{actions}
   Chaque action choisie s'appuie sur un fait de l'entrée :
   - toujours une action sur le tutorat : « proposer un tutorat » si le statut est « aucun », sinon « faire le point sur le tutorat en cours » ;
   - « relancer sur les devoirs » : l'étudiant rend moins de devoirs que la promotion ;
   - « suivre l'assiduité » : l'étudiant manque plus de séances que la promotion ;
   - « aménager l'emploi du temps » : le facteur « emploi en parallèle des études » vaut « oui » ;
   - « informer sur les aides » : le facteur « bourse » vaut « non boursier ».
   S'il y en a plus de 3, garde les 3 qui te semblent les plus utiles pour cet étudiant. N'ajoute jamais une action qu'aucun fait n'appuie (par exemple « suivre l'assiduité » quand l'étudiant manque moins de séances que la promotion). La fiche prépare déjà un entretien : « entretien individuel » sert seulement à compléter quand le tutorat est la seule action appuyée par un fait.
9. Réponds uniquement par un objet JSON avec exactement trois clés : situation (texte), points_attention (liste de textes), actions (liste d'actions).

## Message

ENTRÉE :
{entree}
~~~

2. `--limite N` (seulement avec `--generer`, sinon erreur du parseur) : au plus N fiches **nouvelles** ; au-delà, les entrées suivantes ne sont plus envoyées : leur fiche du cache est gardée telle quelle si elle existe, sinon elles restent absentes du fichier (aucune fiche du cache n'est perdue). Le message final indique le nombre d'entrées non traitées.
3. Tests :
   - `test_gabarit_v2` (comme `test_gabarit_v1`) : lecture, actions insérées, entrée insérée, plus de `{actions}` ni `{entree}` ; le texte contient les 3 phrases imposées du tutorat ;
   - `--limite` avec une fausse fonction d'appel : entrées A, B, C, D, cache avec une fiche validée pour D, `limite=1` → seule A est demandée, B et C absentes, D gardée.
4. `VERSION_PROMPT` reste `"v1"` dans ce commit. Commit : `LL-02 : gabarit v2 du prompt et option --limite (#24)`.

## Étape 4 — Génération des 54 fiches v2 (seule étape avec l'API)
1. `VERSION_PROMPT = "v2"` dans `config.py` (commentaire : D-69).
2. `python -m src.llm --tester` (un appel neutre, sans donnée d'étudiant).
3. **Essai sur 5 fiches** : `python -m src.llm --generer --limite 5`, puis `resume_indicateurs` sur ces 5 fiches. Continue seulement si les 5 sont « validée », au plus 1 a demandé plus d'un essai, et aucune n'a de décimale avec un point, de tutorat « est aucun » ou d'action qu'aucun fait n'appuie. Sinon : arrête-toi, ne commite rien de l'étape 4, supprime le cache v2 de l'essai (un gabarit v2 corrigé ne doit pas réutiliser ces fiches) et rends compte avec les 5 fiches (sans identifiant) et leurs motifs.
4. `python -m src.llm --generer` (reprend après les 5). Note la durée, le nombre d'appels, la répartition des essais, les motifs des fiches « à revoir ». Quota atteint : commite le cache partiel (avec `config.py`), arrête-toi et signale-le ; on relancera plus tard.
5. `python -m src.llm --verifier` : 0 fiche rétrogradée attendue pour v1 et pour v2 (sinon, signale-le).
6. `python -m src.llm --grille` → `docs/evaluation_fiches_llm_v2.csv` (cases à remplir) ; vérifie que ses 20 identifiants sont **exactement** ceux de la grille v1, et que pour chaque étudiant l'entrée de la fiche v2 est identique à celle de la fiche v1.
7. Commit : `LL-02 : 54 fiches générées avec le prompt v2 et grille v2 à noter (#24)` (`config.py`, cache v2, grille v2).

## Étape 5 — Notebook 06 : comparaison des deux versions
1. En-tête : LL-01 et LL-02, gabarits `fiche_v1.md` et `fiche_v2.md`, décisions jusqu'à D-69. Sections 4 et 5 : elles présentent la version courante (v2) ; la section 5 dit que la v1 est gardée pour la comparaison.
2. Nouvelle section **« 6. Évaluation (LL-02) : version 1 puis version 2 »** :
   - les changements du gabarit v2 en 5 puces (virgule et « % », multiplicateur comparé à un étudiant moyen avec la valeur et la référence, tutorat dans la situation avec des phrases imposées, un point sur l'activité récente, actions appuyées par un fait sans « entretien individuel » par défaut), et ce qui ne change pas ;
   - tableau des indicateurs (`resume_indicateurs`) : colonnes v1 et v2, en « n / N (x %) », puis une phrase d'interprétation par groupe, compréhensible par un conseiller pédagogique ;
   - figure `docs/figures/06_comparaison_prompts.png` : barres horizontales groupées, en % des fiches, pour 6 indicateurs (décimale avec point, tutorat « est aucun », « semaine d'observation », multiplicateur comparé à un étudiant moyen, action qu'aucun fait n'appuie, « entretien individuel » proposé) ; v1 en gris, v2 en bleu, une légende, la valeur au bout de chaque barre, un seul axe de 0 à 100 % ;
   - notes humaines (`lire_grille_evaluation` puis `resume_grille`) : colonnes v1 et v2 ; si la grille v2 n'est pas encore remplie, afficher « en attente de la notation de Saliou » (le notebook tourne quand même) ;
   - une même fiche en v1 et en v2 (l'étudiant au risque le plus élevé), sans l'identifiant ;
   - limites, en clair : une seule personne note, en connaissant la version ; les indicateurs suivent des règles simples (ils ne jugent ni le ton ni l'utilité réelle) ; les mêmes entrées et les mêmes contrôles dans les deux versions.
3. Exécute le notebook de haut en bas et commite-le avec ses sorties.

## Étape 6 — Tableau de bord, README, vérifications
- Le tableau de bord montre les fiches v2 (légende « prompt v2 ») ; lance `streamlit run app/app.py` et regarde la page « Fiche étudiant » d'un étudiant en tutorat et d'un autre sans tutorat. Tests `AppTest` verts.
- README : fichiers par version, `--verifier` sur toutes les versions, `--limite`, une phrase sur LL-02 (v1 gardée, v2 affichée, grilles par version).
- `pytest` ; `python run_all.py` (n'appelle pas l'API ; `llm_entrees_semaine8.json` inchangé) ; `git status` propre.
- Commit : `LL-02 : notebook 06, comparaison v1 / v2, README (#24)`, puis push sur `main`.

## Contrôles attendus (prototype de la session de pilotage)
Indicateurs de l'étape 2 sur le cache v1 :

| Indicateur | 54 fiches v1 | 20 fiches notées |
|---|---:|---:|
| Fiches validées | 54 / 54 | 20 / 20 |
| Validées dès le premier essai | 48 / 54 | 18 / 20 |
| Nombre décimal écrit avec un point | 48 / 54 | 18 / 20 |
| Tutorat formulé « est aucun » ou « statut aucun » | 24 / 54 | 7 / 20 |
| Nom de champ « semaine d'observation » | 23 / 54 | 7 / 20 |
| Multiplicateur comparé à « un étudiant moyen » | 5 / 54 | 3 / 20 |
| Valeur de l'étudiant citée (facteurs chiffrés) | 86 / 97 | 33 / 39 |
| Référence de la promotion citée | 85 / 162 | 31 / 60 |
| Au moins une action qu'aucun fait n'appuie | 22 / 54 | 5 / 20 |
| Action appuyée oubliée alors qu'une place restait | 53 / 54 | 19 / 20 |
| « entretien individuel » proposé | 54 / 54 | 20 / 20 |
| « aménager l'emploi du temps » quand un fait l'appuie | 0 / 52 | 0 / 18 |
| « informer sur les aides » quand un fait l'appuie | 0 / 13 | 0 / 3 |
| « relancer sur les devoirs » quand un fait l'appuie | 6 / 29 | 3 / 16 |
| « suivre l'assiduité » quand un fait l'appuie | 26 / 28 | 12 / 13 |
| Combinaisons d'actions différentes | 4 | 3 |

Faisabilité du gabarit v2 (sans API) : des fiches construites mot pour mot selon les modèles de phrases, pour les 54 entrées, passent tous les contrôles actuels (0 rejet) ; situation de 179 caractères au plus (limite 350), point de 171 au plus (limite 200), aucun mot interdit dans les phrases imposées. Pour la v2 générée, il n'y a pas de valeur attendue : ce sont les mesures.

## Plus tard — après la notation de la version 2 par Saliou
Saliou te donnera le CSV de sa grille v2 (et, s'il l'a relue, celui de sa grille v1). Écris-le tel quel (BOM utf-8, `;`, LF) dans `docs/evaluation_fiches_llm_v2.csv` (et `_v1.csv`), vérifie-le avec `lire_grille_evaluation` et le test d'invariant, relance le notebook 06, puis commite : `LL-02 : grille v2 remplie par Saliou et comparaison des notes (#24)` (et `LL-02 : grille v1 relue par Saliou (#24)` à part, pour que l'historique garde la première notation).

## Livraison
- Commits des étapes 0 à 6 (messages ci-dessus), push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec : le résultat de l'essai sur 5 fiches ; la comparaison au tableau « Contrôles attendus » ; le tableau v1 / v2 des indicateurs ; durée, appels et essais de la génération ; 2 fiches v2 en exemple (un étudiant en tutorat, un sans tutorat), sans identifiant.
- Kanban (pour Saliou) : LL-02 reste « En cours » jusqu'à la notation de la version 2.
