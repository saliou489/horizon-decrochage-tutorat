# Consigne C13 — LL-01 : fiches d'alerte par LLM — entrées, prompt v1, contrôles et génération, sans appel réel (issue #23)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C12 terminée.

## Contexte
Lis `CLAUDE.md` (§6 « LLM et données personnelles » et « Honnêteté »), le cahier des charges (F6) et **les décisions D-63 à D-66** (surtout D-65 et D-66).

**Règles de cette consigne :**
- **Aucun appel réel à l'API.** La relecture de sécurité R03 passe avant le premier appel (D-65). Tu ne lances ni `--tester` ni `--generer` ; tous les tests utilisent une fausse fonction d'appel.
- **Tu ne crées pas de `.env` et tu n'ouvres pas celui de Saliou** s'il existe déjà (ne pas le lire, ne pas afficher son contenu, ne pas le copier).
- La méthode est figée par D-65 et D-66 : un cas non couvert se signale (§2 de `CLAUDE.md`) ; s'il bloque, arrête-toi.
- Nouvelles bibliothèques : `google-genai==3.6.1` et `python-dotenv==1.2.4` (roues Windows pour Python 3.14 vérifiées par le pilotage). Si l'installation échoue : arrête-toi et signale-le.

## Étape 0 — Notebook 04 : raisons de D-64 (commit séparé)
Dans la cellule Markdown « **Limites** » de `notebooks/04_ml_survie.ipynb` :
- remplacer la puce sur l'emploi par : le Cox appris sur 2024 donne p = 0,030 pour l'emploi en parallèle au test de Schoenfeld ; non corrigé (D-64), car 13 colonnes sont testées à la fois (seuil de Bonferroni 0,05 / 13 ≈ 0,0038, non franchi), aucune violation sur les 5 000 étudiants stratifiés par cohorte (SV-02, p minimum 0,36), et ce Cox sert à prédire : sa calibration est mesurée directement sur 2025 (écart de 2,8 points) ; le modifier après avoir vu 2025 reviendrait à l'ajuster au jeu de test ;
- remplacer le dernier paragraphe par : les fiches d'alerte utilisent le Cox (risque et facteurs, D-66) ; le tableau de bord affichera aussi le score hebdomadaire du gradient boosting (DB-01).

Modifier **seulement** cette cellule (avec `nbformat`), sans réexécuter ; `git diff --stat` doit montrer un petit changement. Si le diff touche des sorties, réexécuter le notebook de haut en bas à la place.
Commit : `SV-04 : raisons de D-64 dans les limites du notebook 04 (#18)`.

## Partie A — Paramètres (`src/config.py`, nouvelle section « Fiches d'alerte par LLM (LL-01, D-65, D-66) »)
Chaque constante avec un commentaire qui dit pourquoi :
- `MODELE_LLM = "gemini-3.5-flash-lite"` ; `MODELE_LLM_SECOURS = "gemini-3.1-flash-lite"` ; `VERSION_PROMPT = "v1"` ; `DOSSIER_PROMPTS = RACINE / "src" / "prompts"` ; `FICHIER_ENV = RACINE / ".env"` ; `NOM_CLE_API = "GEMINI_API_KEY"`.
- `SEMAINE_FICHES = SEMAINE_LANDMARK` ; `SEMAINES_ACTIVITE_FICHE = (7, 8)` ; `SEUIL_RISQUE_FICHE = 0.40`.
- `VARIABLES_FACTEURS_FICHE = ["age", "note_bac", COLONNE_DISTANCE_COX, "boursier", "emploi_parallele", "filiere"]` (liste positive : le genre et la région ne sont jamais affichés, D-66) ; `LIBELLES_FACTEURS_FICHE` : dictionnaire variable → libellé (âge, note du bac, distance domicile-campus, bourse, emploi en parallèle des études, filière, dans l'ordre de la liste) ; `NB_FACTEURS_FICHE = 3` ; `MULTIPLICATEUR_MIN_FACTEUR = 1.1`.
- `ACTIONS_FICHE` (cet ordre, ces mots exacts) : `entretien individuel`, `proposer un tutorat`, `faire le point sur le tutorat en cours`, `informer sur les aides`, `aménager l'emploi du temps`, `suivre l'assiduité`, `relancer sur les devoirs`.
- `STATUTS_TUTORAT_FICHE = ("en cours", "aucun", "signalé, semaine de début inconnue")`.
- `MOTS_INTERDITS_FICHE` (minuscules ; recherchés comme mots entiers, voir partie C) :
  - causalité : cause, causes, causé, causée, à cause, provoque, provoqué, provoquée, entraîne, entraîné, entraînée, entraine, entrainé, entrainée, parce que, dû à, due à ;
  - certitude : certainement, forcément, inévitable, inévitablement, à coup sûr, sans aucun doute, va décrocher, va abandonner ;
  - jugement : paresseux, paresseuse, fainéant, fainéante, incapable, démotivé, démotivée, mauvais étudiant ;
  - attributs sensibles : homme, hommes, femme, femmes, garçon, garçons, fille, filles, genre, sexe, origine, ethnie, religion, santé, maladie, handicap, famille, pauvre, pauvreté ;
  - nombres en lettres : double, triple, moitié, deux fois, trois fois, quatre fois.
- `NB_ESSAIS_FICHE = 3` ; `PAUSE_ENTRE_APPELS_LLM = 7` (secondes ; niveau gratuit : 10 requêtes par minute) ; `ATTENTES_QUOTA_LLM = (30, 60)` (secondes, après une erreur 429 ou 503) ; `DELAI_MAX_APPEL_LLM_MS = 60000`.
- `LONGUEUR_MAX_SITUATION = 350` ; `LONGUEUR_MAX_POINT = 200` ; `LONGUEUR_MAX_TEXTE_ENTREE = 80`.
- `STATUT_FICHE_VALIDEE = "validée"` ; `STATUT_FICHE_A_REVOIR = "à revoir"`.
- `AVERTISSEMENT_FICHE` = « Fiche générée automatiquement à partir d'un modèle statistique : à vérifier par le conseiller. Les facteurs sont des associations, pas des causes. »
- `FICHIER_ENTREES_LLM = DOSSIER_RESULTATS / f"llm_entrees_semaine{SEMAINE_FICHES}.json"` ; `FICHIER_FICHES_LLM = DOSSIER_RESULTATS / f"llm_fiches_semaine{SEMAINE_FICHES}.json"` ; `NB_FICHES_EVALUATION = 20` ; `FICHIER_GRILLE_EVALUATION = RACINE / "docs" / "evaluation_fiches_llm.csv"`.

## Partie B — Entrées des fiches (`src/llm.py`, sans réseau)
Module avec « Rôle du module » (LL-01, LL-02), exception `ErreurLLM` et `ErreurQuotaLLM(ErreurLLM)`. Fonctions paramétrées par `semaine` (le tableau de bord les réutilisera pour d'autres semaines).
1. `population_suivie(base, semaine)` : cohorte `COHORTE_TEST`, `T > semaine`, index remis à zéro.
2. `risques_conditionnels(predictions, ids, semaine)` : 1 − S(30) / S(semaine), colonne `survie_cox` de `ml_predictions_2025.csv`, dans l'ordre de `ids` ; `ErreurLLM` si un identifiant manque.
3. `contributions(table_codee, hr)` : β = log(HR) de `ml_hr_cox_2024.csv` ; pour chaque variable d'origine du Cox (`survie.variable_d_origine`), somme sur ses colonnes de β × (x − moyenne des lignes reçues). La table codée vient de `ml_survie.variables_rentree(entrainement, test)["test"]` (médianes de 2024), restreinte à la population. `ErreurLLM` si une colonne n'a pas de HR. Propriété : la somme des contributions d'un étudiant = son prédicteur linéaire moins la moyenne de la population.
4. `references_promotion(population)` : textes de référence, calculés sur les valeurs connues de la population (format français, virgule décimale) :
   - âge : « 20,1 ans en moyenne dans la promotion » ; note du bac : « 12,8 / 20 en moyenne dans la promotion » ;
   - distance : « 11 km pour un étudiant typique de la promotion », avec 2^(moyenne de log2 de la distance), arrondi au km (correspond au centrage du Cox) ;
   - modalité (bourse, emploi, filière) : « 57 % de la promotion dans ce cas » (part des valeurs connues ayant la même modalité, arrondie à l'unité).
5. `facteurs_principaux(contributions_etudiant, ligne_brute, references)` : candidats = `VARIABLES_FACTEURS_FICHE` seulement ; valeur brute manquante → exclu ; multiplicateur = exp(contribution) arrondi à 0,1, gardé s'il vaut au moins `MULTIPLICATEUR_MIN_FACTEUR` ; les `NB_FACTEURS_FICHE` plus fortes contributions, par ordre décroissant (égalité : ordre de la liste). Chaque facteur : `{"facteur": libellé, "valeur_etudiant": texte, "reference_promotion": texte, "multiplicateur": nombre}`. Valeurs : « 28 ans » ; « 10,6 / 20 » ; « 131 km » (arrondi au km) ; « boursier » / « non boursier » ; emploi : « oui » / « non » ; filière : son nom.
6. `activite_recente(periode, ids, semaines)` : par étudiant, moyenne par semaine des valeurs **renseignées** des semaines indiquées pour `nb_connexions_lms`, `devoirs_rendus`, `absences` et `note_moyenne`, arrondie à 0,1 ; aucune valeur → `None`. Moyenne de la promotion = moyenne de ces moyennes sur les étudiants qui en ont une, arrondie à 0,1.
7. `statut_tutorat(ligne, semaine)` : `{"statut": "en cours", "semaine_debut": s}` si `semaine_debut_tutorat` ≤ semaine ; `{"statut": "signalé, semaine de début inconnue"}` si `statut_tutorat` vaut `tutorat_semaine_inconnue` ; sinon `{"statut": "aucun"}` (un tutorat commencé plus tard n'est pas connu à la semaine 8).
8. `construire_entrees(base, periode, predictions, hr, semaine=config.SEMAINE_FICHES)` : liste de `{"id_etudiant": ..., "entree": {...}}` pour les étudiants dont le risque atteint `SEUIL_RISQUE_FICHE`, triée par risque décroissant puis identifiant. **L'identifiant reste hors de `entree`** : seul `entree` part vers le LLM. Format exact de `entree` (clés et ordre), exemple du premier étudiant :
   ```json
   {"semaine_observation": 8, "horizon_semaines": 30, "risque_decrochage_pct": 71, "risque_moyen_promotion_pct": 18,
    "facteurs": [{"facteur": "âge", "valeur_etudiant": "28 ans", "reference_promotion": "20,1 ans en moyenne dans la promotion", "multiplicateur": 2.1}, "…"],
    "activite": {"semaines": [7, 8], "note_maximum": 20, "connexions_plateforme": 3.0, "devoirs_rendus": 0.5, "seances_manquees": 4.5, "note_moyenne": 9.0},
    "activite_promotion": {"connexions_plateforme": 6.1, "devoirs_rendus": 1.4, "seances_manquees": 2.5, "note_moyenne": 10.4},
    "tutorat": {"statut": "aucun"}}
   ```
   Risques en pourcentage entier (`round(100 × risque)`) ; risque moyen = moyenne des risques de la population.
9. `verifier_entree_sans_donnee_personnelle(entree)` : `ErreurLLM` (avant tout envoi) si une clé n'est pas exactement celles du format ci-dessus, à chaque niveau (pour `tutorat` : `statut`, plus `semaine_debut` seulement si « en cours »), si `facteur` n'est pas un libellé de `LIBELLES_FACTEURS_FICHE` ou `statut` pas dans `STATUTS_TUTORAT_FICHE`, si un texte dépasse `LONGUEUR_MAX_TEXTE_ENTREE` caractères, ou s'il contient un motif de `FORMAT_ID_ETUDIANT`, `MOTIF_EMAIL` ou `MOTIF_TELEPHONE` (motifs déjà dans `config.py`). Appelée par `construire_entrees` et juste avant chaque appel.
10. `lancer_entrees()` : écrit `FICHIER_ENTREES_LLM` (JSON, UTF-8, `ensure_ascii=False`, `indent=2`, fins de ligne LF) ; affiche le nombre d'étudiants et l'état du cache (« n fiches en cache (modèle, version, date) » ou « aucune fiche : lancer python -m src.llm --generer après la relecture R03 »). **N'appelle jamais l'API.**

## Partie C — Prompt, appel et contrôles (`src/llm.py`, `src/prompts/`)
1. **Gabarit** `src/prompts/fiche_v1.md`, à recopier tel quel (`{actions}` reçoit la liste `ACTIONS_FICHE`, une action par ligne précédée de « - » ; `{entree}` reçoit `json.dumps(entree, ensure_ascii=False, indent=2)`, remplacés avec `str.replace`) :
   ```markdown
   ## Instructions système

   Tu aides un conseiller pédagogique de l'Institut Supérieur Horizon à préparer un entretien avec un étudiant. À partir de l'ENTRÉE (un objet JSON), tu rédiges une fiche courte, factuelle et bienveillante.

   Sens des champs de l'entrée :
   - risque_decrochage_pct : risque, estimé par un modèle statistique, que l'étudiant décroche avant la semaine horizon_semaines, sachant qu'il est encore inscrit à la semaine semaine_observation ; risque_moyen_promotion_pct : le même risque, en moyenne, dans sa promotion.
   - facteurs : au plus 3 caractéristiques connues dès la rentrée qui, dans le modèle, sont associées à un risque plus élevé ; multiplicateur : le risque est multiplié par cette valeur par rapport à un étudiant moyen de la promotion, à autres caractéristiques égales.
   - activite et activite_promotion : moyennes par semaine sur les semaines indiquées (connexions à la plateforme, devoirs rendus, séances manquées, note moyenne sur note_maximum) ; null signifie « non renseigné ». Ce sont des observations, pas des éléments du score.
   - tutorat : situation du tutorat à la semaine d'observation.

   Règles :
   1. Utilise uniquement les informations de l'entrée. N'invente ni cause ni circonstance personnelle (famille, santé, argent, motivation…).
   2. Recopie les nombres exactement comme ils figurent dans l'entrée, écrits en chiffres. Ne calcule rien : ni différence, ni rapport, ni arrondi.
   3. Parle d'association, jamais de cause : « est associé à », « va de pair avec ». Pas de certitude : c'est un risque estimé, pas une prédiction.
   4. Reste neutre et respectueux, sans jugement sur la personne. Écris « l'étudiant », sans aucune référence au genre, à l'origine ou à la santé.
   5. actions : 2 ou 3 actions, recopiées mot pour mot dans cette liste :
   {actions}
      Si un tutorat est en cours, ne choisis pas « proposer un tutorat » ; s'il n'y en a pas, ne choisis pas « faire le point sur le tutorat en cours ».
   6. Réponds uniquement par un objet JSON avec exactement trois clés :
      - situation : 2 phrases qui résument le risque et ses principaux facteurs ;
      - points_attention : 2 à 4 phrases courtes, chacune sur un fait de l'entrée (facteur, activité ou tutorat) ;
      - actions : la liste des actions choisies.

   ## Message

   ENTRÉE :
   {entree}
   ```
   `lire_gabarit(version)` lit `fiche_<version>.md` (UTF-8) et renvoie (instructions, message) ; `ErreurLLM` si un des deux titres manque.
2. `schema_fiche()` : schéma JSON de la réponse : objet, clés requises `situation` (chaîne), `points_attention` (liste de chaînes, 2 à 4), `actions` (liste de chaînes de `ACTIONS_FICHE` en `enum`, 2 à 3), `additionalProperties: false`.
3. `lire_cle_api(chemin=config.FICHIER_ENV)` : `dotenv.dotenv_values(chemin).get(config.NOM_CLE_API)` ; **ne lit pas `os.environ`** ; clé absente ou vide → `ErreurLLM` qui explique quoi faire (copier `.env.example` en `.env`, coller la clé après `GEMINI_API_KEY=`) sans jamais reprendre le contenu du fichier.
4. `creer_appel_gemini(cle, modele, schema=None)` → fonction `appeler(instructions, message) -> str`. Importer `google.genai` **dans** cette fonction (ni les tests ni `run_all.py` ne le chargent). `genai.Client(api_key=cle)` ; `client.models.generate_content(model=modele, contents=message, config=types.GenerateContentConfig(system_instruction=instructions or None, response_mime_type="application/json" si un schéma est donné, response_json_schema=schema, http_options=types.HttpOptions(timeout=config.DELAI_MAX_APPEL_LLM_MS)))` ; renvoie `reponse.text` (chaîne vide si `None`). Pas de `temperature` (valeur par défaut recommandée pour Gemini 3). `google.genai.errors.APIError` : code 429 ou 503 → `ErreurQuotaLLM` ; autre → `ErreurLLM(f"Erreur de l'API Gemini (code {code})")`, avec `from None`. Rien d'autre n'est affiché ni journalisé.
5. `nombres_de(objet)` : ensemble des nombres d'un objet JSON (nombres et nombres écrits dans les textes, motif `\d+(?:[.,]\d+)?`, virgule lue comme un point, arrondis à 6 décimales) ; booléens et `None` ignorés. `mots_interdits_presents(texte)` : expressions de `MOTS_INTERDITS_FICHE` trouvées dans le texte en minuscules, comme mots entiers : motif `(?<!\w)` + `re.escape(expression)` + `(?!\w)` (« entraînement » ne déclenche pas « entraîne », « filière » ne déclenche pas « fille »).
6. `verifier_fiche(texte, entree)` → `(fiche ou None, motifs)` ; `motifs` vide = fiche conforme. Motifs (phrases courtes) : réponse non JSON ou vide ; clés différentes des trois attendues ; types ; `situation` vide ou plus longue que `LONGUEUR_MAX_SITUATION` ; 2 à 4 points, chacun non vide et d'au plus `LONGUEUR_MAX_POINT` caractères ; 2 ou 3 actions distinctes de `ACTIONS_FICHE` ; cohérence avec le tutorat (« en cours » exclut `proposer un tutorat`, « aucun » exclut `faire le point sur le tutorat en cours`) ; nombre absent de l'entrée (lister les nombres fautifs) ; mot interdit (lister) ; motif d'identifiant, d'e-mail ou de téléphone.
7. `generer_fiches(entrees, appeler, fiches_existantes, modele, forcer=False, attendre=time.sleep, enregistrer=None)` :
   - fiche existante réutilisée (aucun appel) si même `id_etudiant`, même `version_prompt`, même `modele` et même `entree`, sauf `forcer` ;
   - sinon : `verifier_entree_sans_donnee_personnelle`, prompt construit avec `lire_gabarit(config.VERSION_PROMPT)`, puis jusqu'à `NB_ESSAIS_FICHE` essais (appel, puis `verifier_fiche`) ; `attendre(PAUSE_ENTRE_APPELS_LLM)` avant chaque appel sauf le tout premier ;
   - `ErreurQuotaLLM` : `attendre` chaque durée de `ATTENTES_QUOTA_LLM` puis réessayer le même essai ; après la dernière, arrêter toute la génération par une `ErreurQuotaLLM` explicite (« quota atteint : relancer plus tard ; les fiches déjà faites sont gardées ») ; toute autre `ErreurLLM` arrête aussi ;
   - fiche enregistrée : `id_etudiant`, `semaine`, `risque_decrochage_pct`, `statut` (`validée`, ou `à revoir` après le dernier essai non conforme), `situation`, `points_attention`, `actions` (du dernier essai lisible ; `None` sinon), `motifs_rejet` (du dernier essai), `nb_essais`, `avertissement` (`AVERTISSEMENT_FICHE`, ajouté par le code), `modele`, `version_prompt`, `date_generation` (`datetime.now().isoformat(timespec="seconds")`), `entree` ; et `reponse_brute` (2 000 caractères au plus) seulement pour une fiche « à revoir » sans JSON lisible ;
   - `enregistrer(fiches)` appelé après **chaque** fiche (une interruption ne perd rien) ; sortie : la liste des fiches, dans l'ordre des entrées.
8. `echantillon_evaluation(fiches, n=NB_FICHES_EVALUATION, graine=SEED)` : `numpy.random.default_rng(graine).choice` sur les identifiants triés, sans remise, puis remis dans l'ordre des fiches. `ecrire_grille_evaluation(fiches, chemin)` : colonnes `id_etudiant`, `statut_automatique`, `motifs_rejet`, puis, vides pour Saliou, `exactitude_humaine` (oui / non), `ton` (1 à 3), `stigmatisation` (oui / non), `actions_pertinentes` (1 à 3), `commentaire` ; séparateur `;` et `encoding="utf-8-sig"` (pour qu'Excel en français l'ouvre en colonnes avec les accents : le dire en commentaire) ; **refuse d'écraser** une grille existante (`ErreurLLM`).
9. **Ligne de commande** `python -m src.llm` (argparse) : `--entrees` (comme `lancer_entrees`) ; `--tester` (un seul appel neutre, sans schéma et sans aucune donnée d'étudiant : pas d'instructions système, message « Réponds uniquement par le mot OK. » ; affiche le modèle et la réponse) ; `--generer` (lit `FICHIER_ENTREES_LLM`, la clé, le gabarit et le cache, génère, écrit `FICHIER_FICHES_LLM` après chaque fiche, puis affiche le nombre de fiches validées et à revoir) avec `--forcer` ; `--grille` (lit le cache ; `ErreurLLM` s'il n'existe pas) ; `--modele` (défaut `MODELE_LLM`) pour `--tester` et `--generer`. Aucune commande n'affiche la clé.

## Partie D — `run_all.py`, dépendances, `.env.example`, README
- `run_all.py` : après l'étape causale, `llm.lancer_entrees()` ; docstring mise à jour (l'API n'est jamais appelée par `run_all.py`).
- `requirements.txt` : `google-genai==3.6.1` et `python-dotenv==1.2.4` (ordre alphabétique).
- `.env.example`, sans valeur :
  ```
  # Copier ce fichier en .env (même dossier) et coller la clé après le signe =.
  # .env est ignoré par git : la clé ne doit jamais être commitée.
  GEMINI_API_KEY=
  ```
  Vérifier que `.env` est bien ignoré : `git check-ignore -v .env` (résultat dans le compte rendu).
- README, nouvelle section « Fiches d'alerte (LLM) » : à quoi servent les fiches ; ce qui est envoyé à Gemini et ce qui ne l'est jamais ; obtenir une clé (Google AI Studio, page « API keys ») et la placer dans `.env` ; les commandes `--tester`, `--generer`, `--grille` ; quotas du niveau gratuit (page « Rate limit » d'AI Studio) ; les fiches sont enregistrées dans le dépôt, donc ni l'enseignant ni `run_all.py` n'ont besoin d'une clé ; cadre (loi n° 2008-12, RGPD) ; dans la déclaration d'usage de l'IA, Gemini comme **composant du produit** (rédaction des fiches), à côté de l'usage de Claude pour le développement.

## Partie E — `notebooks/06_llm.ipynb` (première version)
Lit les fichiers produits (ne relance pas le pipeline, n'appelle jamais l'API) ; tourne de haut en bas sans clé.
1. **Rôle des fiches et protection des données** : ce que fait le LLM (rédiger, pas décider) ; la liste fermée des champs envoyés et ce qui n'est jamais envoyé ; pourquoi aucun texte d'étudiant ; niveau gratuit et usage des requêtes par Google ; loi n° 2008-12 et RGPD (finalité, minimisation, sécurité) ; l'avertissement fixe ; le conseiller vérifie et décide.
2. **Les étudiants à risque à la semaine 8** : histogramme des 2 177 risques conditionnels avec la ligne des 40 % → `docs/figures/06_risque_semaine8.png` ; effectifs selon le seuil (30, 35, 40, 45 et 50 %) ; vérification a posteriori, **non utilisée pour choisir** : décrochages observés après la semaine 8 parmi les 54 et parmi les autres (simple proportion ; les transferts comptent comme non-décrocheurs, ce qui la sous-estime un peu) ; une phrase pour un conseiller.
3. **Les facteurs affichés** : fréquence de chaque facteur dans les 54 entrées ; statut de tutorat ; activité des semaines 7 et 8 des 54 contre la promotion ; rappel : association, pas cause.
4. **Ce qui part vers le LLM** : la première entrée (sans identifiant), le prompt complet tel qu'il serait envoyé (instructions et message), le schéma de réponse, la liste des contrôles automatiques.
5. **Fiches générées et évaluation** : si `FICHIER_FICHES_LLM` existe, les afficher ; sinon, une phrase : « à compléter après la relecture R03 (génération) et l'évaluation LL-02 ».

## Partie F — Tests (`tests/test_llm.py`, aucun accès réseau)
- `risques_conditionnels` : S(8) = 0,8 et S(30) = 0,4 → 0,5 ; `population_suivie` ne garde que 2025 et T > 8.
- `contributions` sur un petit cas (2 variables numériques, une qualitative à 2 indicatrices, HR connus) : β × (x − moyenne) ; somme = prédicteur linéaire centré ; indicatrices additionnées.
- `facteurs_principaux` : valeur brute manquante exclue ; contribution donnant un multiplicateur de 1,04 exclue (arrondi 1,0), de 1,12 gardée (arrondi 1,1) ; 3 au plus, ordre décroissant ; genre et région jamais présents, même avec la plus forte contribution.
- `verifier_entree_sans_donnee_personnelle` : passe sur une entrée conforme ; `ErreurLLM` sur une clé en trop, un identifiant `HZ` + 5 chiffres, un e-mail, un téléphone (valeurs inventées), un texte trop long, un libellé hors liste.
- `nombres_de` et `verifier_fiche` : « 6,1 » accepté si 6.1 est dans l'entrée, « 3 » accepté pour 3.0 ; « 3,5 » refusé ; JSON invalide, clé en trop, 1 seule action, action hors liste, actions en double, tutorat incohérent (dans les deux sens) : refusés avec un motif.
- `mots_interdits_presents` : « à cause de » trouvé ; « entraînement » et « filière » non trouvés ; « 2,1 fois plus élevé » non trouvé.
- `generer_fiches` avec une fausse fonction d'appel : réponses [non conforme, conforme] → `validée`, `nb_essais` = 2, avertissement présent ; toujours non conforme → `à revoir` après 3 essais, motifs gardés ; `ErreurQuotaLLM` puis succès → `attendre` reçoit 30 ; quota jamais rétabli → `ErreurQuotaLLM` et les fiches déjà faites ont été passées à `enregistrer` ; **aucun message reçu par la fausse fonction ne contient l'identifiant** ; second passage sur le même cache → 0 appel ; `forcer=True` ou autre `version_prompt` → nouveaux appels.
- `lire_cle_api` : lit la clé d'un `.env` temporaire (`tmp_path`, clé inventée) ; avec `GOOGLE_API_KEY` posée par `monkeypatch`, renvoie quand même la valeur du fichier ; fichier absent → `ErreurLLM` dont le message ne contient pas la clé.
- `lire_gabarit("v1")` : deux parties non vides ; après remplacement, chaque action figure dans les instructions et l'entrée dans le message.
- `ecrire_grille_evaluation` : 20 identifiants distincts, même tirage à chaque fois ; refuse d'écraser.
- Invariants sur les fichiers produits (ignorés proprement s'ils n'existent pas) : 54 entrées, identifiants uniques au format attendu, risques ≥ 40, aucune entrée ne contient d'identifiant, chaque entrée passe `verifier_entree_sans_donnee_personnelle`.

## Contrôles attendus
Prototype de la session de pilotage (mêmes définitions), à comparer ; signaler et expliquer tout écart :
- Cohorte 2025 : 2 505 étudiants ; encore suivis après la semaine 8 : **2 177**. Risque conditionnel moyen 17,79 % (médiane 16,23 %).
- Risque ≥ 40 % : **54** étudiants (max 71,0 %, min 40,0 %, moyenne 45,9 %). Autres seuils : 30 % → 196 ; 35 % → 102 ; 45 % → 24 ; 50 % → 9.
- A posteriori : 23 décrochages après la semaine 8 parmi les 54 (42,6 %) ; 387 sur les 2 123 autres (18,2 %).
- Facteurs des 54 fiches (162 en tout, 3 par fiche) : emploi en parallèle 52, note du bac 45, âge 29, distance 23, bourse 13, filière 0 ; l'emploi est le premier facteur de 31 fiches.
- Références : 20,1 ans ; 12,8 / 20 ; 11 km ; non boursiers 57 % ; emploi 18 %.
- Activité (moyenne par semaine, semaines 7 et 8), promotion : connexions 6,1 ; devoirs rendus 1,4 ; séances manquées 2,5 ; note 10,4. Moyenne des 54 : 4,6 ; 1,1 ; 3,3 ; 9,1.
- Tutorat à la semaine 8 : 54 → 17 « en cours », 37 « aucun » ; promotion → 402, 1 774 et 1 « semaine de début inconnue ».
- Première entrée : risque 71 %, moyenne 18 % ; âge « 28 ans » ×2,1 ; emploi « oui » ×1,6 ; distance « 131 km » ×1,5 ; activité 3,0 / 0,5 / 4,5 / 9,0 ; tutorat « aucun ».

## Livraison
- Commits : `SV-04 : raisons de D-64 dans les limites du notebook 04 (#18)` (étape 0) ; `LL-01 : entrées des fiches d'alerte, prompt v1 et contrôles automatiques (#23)` (parties A, B, C, F, dépendances, `.env.example`) ; `LL-01 : run_all, README et notebook 06 (première version) (#23)` ; push sur `main`.
- Vérifier à la fin : `pytest` ; `python -m src.llm --entrees` ; `python run_all.py` deux fois de suite → `git status` propre ; notebook 06 exécuté de haut en bas ; `git grep -n "AIza"` ne renvoie rien ; `git check-ignore -v .env`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus et la durée de `run_all.py`. Rappel : ni `--tester` ni `--generer` (ce sera après R03).
