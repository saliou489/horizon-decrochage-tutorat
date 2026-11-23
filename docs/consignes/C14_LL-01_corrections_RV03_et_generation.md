# Consigne C14 — LL-01 : corrections de RV03, repli de D-61, puis génération des 54 fiches (issue #23)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C13 exécutée, relecture RV03 poussée, **D-67 validée** par Saliou.

## Contexte
Lis `docs/revues/RV03_securite_llm.md` en entier, puis **D-65, D-66 et D-67** (`docs/decisions.md`), et D-61 (point 6) pour la partie B.

**Règles de cette consigne :**
- Les appels réels à l'API ne sont permis **que dans la partie D**, après les parties 0, A, C et B. La clé est lue par le code dans `.env` : tu n'ouvres pas ce fichier, tu ne l'affiches pas, tu ne le copies pas.
- Avant **chaque** commit : `git status` ne doit lister aucun fichier `.env…` (sauf `.env.example`). Sinon, arrête-toi.
- Échec réseau (WARP) ou de l'API autre qu'un quota : arrête-toi et signale-le, sans contournement.
- Ordre imposé : 0 → A → C → B → D → E.

## Étape 0 — `.gitignore` d'abord (RV03-01, commit séparé)
- Remplacer la ligne `.env` de `.gitignore` par `.env*` puis `!.env.example` (avec un commentaire : le Bloc-notes de Windows peut créer `.env.txt`).
- Vérifier : `git check-ignore -v .env .env.txt .env.local ".env - Copie"` → tous ignorés ; `git check-ignore .env.example` → rien ; `git ls-files .env.example` → toujours suivi.
- README : commande de copie (PowerShell : `Copy-Item .env.example .env` ; Linux / macOS : `cp .env.example .env`) et vérification « après avoir collé la clé, `git status` ne doit pas lister de fichier `.env` ».
- Commit : `LL-01 : .gitignore couvre toutes les variantes de .env (RV03-01) (#23)`.

## Partie A — Corrections du code (`src/llm.py`, `src/config.py`, tests)
1. **Contrôle d'entrée strict (RV03-04).** `verifier_entree_sans_donnee_personnelle` vérifie, en plus des clés (ordre compris) :
   - nombres (jamais un booléen ni un texte) : `semaine_observation` entier de 1 à 30 ; `horizon_semaines` = `N_SEMAINES` ; risques entiers de 0 à 100 ; `multiplicateur` de `MULTIPLICATEUR_MIN_FACTEUR` à 100 ; `semaines` = liste d'entiers de 1 à `semaine_observation` ; `note_maximum` = 20 ; valeurs d'activité `None` ou nombre dans les bornes de `config.BORNES` (`connexions_plateforme` ↔ `nb_connexions_lms`, ≥ 0 et au plus 100 faute de borne haute ; `devoirs_rendus` ↔ `devoirs_rendus` ; `seances_manquees` ↔ `absences` ; `note_moyenne` ↔ `note_moyenne`) ; `activite_promotion` sans `None` ; `semaine_debut` entier de 1 à `semaine_observation`, seulement si « en cours » ;
   - textes **en correspondance complète** (`re.fullmatch`) avec le format écrit par le code pour le facteur concerné : âge `\d{1,2} ans` ; note du bac `\d{1,2},\d / 20` ; distance `\d{1,4} km` ; bourse `boursier` ou `non boursier` ; emploi `oui` ou `non` ; filière dans `config.MODALITES[("etudiants", "filiere")]` ; références `\d{1,2},\d ans en moyenne dans la promotion`, `\d{1,2},\d / 20 en moyenne dans la promotion`, `\d{1,4} km pour un étudiant typique de la promotion`, `\d{1,3} % de la promotion dans ce cas` (le format attendu dépend du facteur) ;
   - les contrôles de C13 restent (longueur, identifiant, e-mail, téléphone). Les 54 entrées réelles doivent toutes passer (RV03 l'a vérifié avec les mêmes formats) : après la partie A, `python -m src.llm --entrees` doit laisser le fichier d'entrées inchangé (`git diff` vide).
2. **Mots interdits (RV03-03).** Ajouter à `MOTS_INTERDITS_FICHE` (mêmes règles : minuscules, mots entiers) :
   - nombres en lettres : deux, trois, quatre, cinq, six, sept, huit, neuf, dix, vingt, trente, cent, quart, tiers, quadruple (« un » reste permis) ;
   - causalité : entraîner, entrainer, entraînent, entrainent, provoquer, provoquent, causer, causent, causal, causale, causaux, causalité, du à, dus à, dues à ;
   - circonstances inventées : familial, familiale, familiaux, familiales, financier, financière, financiers, financières, argent, motivation, motivé, motivée ;
   - certitude : décrochera, abandonnera, sûrement, surement, certain, certaine.

   Si un test existant échoue parce que son texte d'exemple contient un mot désormais interdit (par exemple « deux »), remplace ce mot dans l'exemple (la règle a changé avec D-67) et signale-le ; ne retire jamais un contrôle.
3. **Cache revérifié (RV03-03).** Fonction `reverifier_fiches(fiches)` : repasse `verifier_fiche` (contrôles actuels) sur chaque fiche « validée » du cache, avec le texte JSON reconstruit à partir de `situation`, `points_attention` et `actions` ; une fiche qui échoue passe « à revoir » avec ses nouveaux motifs ; aucun appel. Appelée au début de `--generer` et par une nouvelle commande `--verifier` (affiche le nombre de fiches rétrogradées, réécrit le cache).
4. **Client Gemini (RV03-06).** `config.URL_API_GEMINI = "https://generativelanguage.googleapis.com/"`. Dans `creer_appel_gemini` : `genai.Client(api_key=cle, vertexai=False, http_options=types.HttpOptions(base_url=config.URL_API_GEMINI, timeout=config.DELAI_MAX_APPEL_LLM_MS))`, et plus de `http_options` dans `GenerateContentConfig`. Commentaire : l'adresse fixée dans le code l'emporte sur `GOOGLE_GEMINI_BASE_URL`, et `vertexai=False` neutralise `GOOGLE_GENAI_USE_VERTEXAI`.
5. **Finitions (RV03-07).**
   - `main` intercepte `ErreurLLM` : affiche le message seul, puis `sys.exit(1)` (pas de trace Python).
   - `ecrire_json` écrit dans un fichier temporaire du même dossier, puis `os.replace` (écriture atomique) ; le fichier temporaire est supprimé si l'écriture échoue.
   - Dans `creer_appel_gemini`, toute autre exception de l'appel (réseau, délai dépassé) devient une `ErreurLLM` qui ne cite que le type de l'exception, avec `from None`.
   - Option `--revoir` (avec `--generer`) : ne régénère que les fiches « à revoir » ; `--forcer` régénère tout, comme avant.
6. **Tests (RV03-05)** : un test qui échoue pour chacune des 7 mutations de RV03 restées inaperçues :
   - entrée non conforme passée à `generer_fiches` → `ErreurLLM`, **aucun appel** ;
   - clé en trop dans `activite`, puis dans un facteur → `ErreurLLM` ;
   - mot interdit en majuscules (« Entraîne », « CAUSE ») → trouvé ;
   - `ErreurLLM` ordinaire levée par la fausse API → arrêt immédiat, un seul appel, aucune attente ;
   - entrée modifiée → la fiche du cache n'est pas réutilisée ;
   - réponse contenant un identifiant `HZ` + 5 chiffres, un e-mail ou un téléphone (valeurs inventées) → refusée.
   Plus :
   - les nouveaux formats d'entrée (un nom propre dans `valeur_etudiant`, une instruction, une filière hors liste, un texte dans `multiplicateur` ou dans un risque, un booléen à la place d'un nombre → refusés) ;
   - quelques mots ajoutés au point 2 ;
   - `reverifier_fiches` ;
   - `--revoir` ;
   - l'écriture atomique (le fichier précédent reste lisible si l'écriture échoue) ;
   - `creer_appel_gemini` avec un **faux module** `google.genai` (`monkeypatch.setitem(sys.modules, …)` pour `google`, `google.genai`, `google.genai.types`, `google.genai.errors`), qui vérifie : client créé avec la clé, `vertexai=False`, l'adresse et le délai ; `system_instruction` à `None` si les instructions sont vides ; type JSON et schéma seulement si un schéma est donné ; erreur 429 ou 503 → `ErreurQuotaLLM` ; erreur 400 → `ErreurLLM` dont le message ne contient que le code (pas le texte de l'API).
7. Commit : `LL-01 : corrections de la relecture RV03 (contrôles, cache, client Gemini) (#23)`.

## Partie C — Fins de ligne de `data/processed` (RV03-08)
1. `git add --renormalize data/processed`, puis `git status`.
2. Si les 11 fichiers sont encore listés : `git rm -r -q --cached data/processed`, puis `git add data/processed` (seul l'index est reconstruit, aucun fichier du disque n'est touché), puis `git status`.
3. Si `git diff --cached` montre un vrai changement de contenu : arrête-toi et signale-le. Sinon, commite ce qui est indexé (`DO-01 : index de data/processed renormalisé (RV03-08) (#27)`) ; s'il n'y a rien à commiter, dis-le.

## Partie B — Repli de D-61 (D-67, point 8)
- `NB_TIRAGES_VARIANTE = 100` (au lieu de 200), avec un commentaire : repli de D-61 déclenché le 23/11 (16 min 41 s au premier lancement après une installation neuve, RV03). `NB_TIRAGES_PRINCIPAL` reste à 500.
- `python run_all.py` **deux fois de suite** (Saliou laisse le PC sur secteur, sans autre programme lourd) ; noter la durée de chaque étape et la durée totale ; après le second passage, `git status` ne doit lister que les fichiers attendus ci-dessous, et aucun des 11 fichiers de RV03-08 (vérification de la partie C).
- Attendu : `ca_effet_principal.csv` et `ca_tirages_principal.csv` **inchangés** ; dans `ca_sensibilite.csv`, seuls changent `tirages` (100 pour les variantes), les intervalles de confiance des variantes et les colonnes de diagnostic du bootstrap ; dans `ca_diagnostic_bootstrap.csv`, seules les lignes des variantes changent ; la figure `05_sensibilite.png` peut changer (intervalles des variantes) ; les estimations ponctuelles ne bougent pas. Tout autre changement : arrête-toi et signale-le.
- Réexécuter `notebooks/05_causal.ipynb` de haut en bas ; mettre à jour tout chiffre d'intervalle de variante écrit en Markdown, s'il a changé ; mentionner les 100 tirages et D-67.
- README : durée mesurée (et rappel : un premier lancement après une installation neuve peut être nettement plus long).
- Commit : `CA-05 : repli de D-61, 100 tirages pour les variantes (D-67) (#22)`.

## Partie D — Premiers appels réels, génération et grille
1. `python -m src.llm --tester`. Si le modèle est introuvable (erreur 404) : `python -m src.llm --tester --modele gemini-3.1-flash-lite`, puis utilise ce modèle pour la suite et signale-le. Tout autre échec : arrête-toi (code d'erreur seulement).
2. `python -m src.llm --generer` (ajoute `--modele …` si le modèle de secours a été retenu). Note : la durée, le nombre total d'appels, le nombre de fiches « validée » et « à revoir », la répartition du nombre d'essais et les motifs de rejet les plus fréquents. Quota atteint : commite les fiches déjà faites (cache partiel, même commit qu'au point 7, sans la grille), arrête-toi et signale-le ; on relancera plus tard, le cache évitera de refaire les fiches.
3. S'il y a des fiches « à revoir » : **une seule** passe `python -m src.llm --generer --revoir`.
4. `python -m src.llm --verifier` → doit annoncer 0 fiche rétrogradée.
5. `python -m src.llm --grille` → `docs/evaluation_fiches_llm.csv` (20 fiches).
6. Lis toi-même 5 fiches au hasard et signale dans le compte rendu tout défaut que les contrôles n'attrapent pas (chiffre calculé, mauvais champ, ton, action citée hors du champ `actions`). Recopie dans le compte rendu **une** fiche validée complète, sans son identifiant.
7. Commit : `LL-01 : 54 fiches générées (prompt v1) et grille d'évaluation LL-02 (#23)`, avec `llm_fiches_semaine8.json` et la grille.

## Partie E — Notebook 06 et README
- Notebook 06 :
  - section 1 : « aucune donnée directement identifiante ; entrées pseudonymisées, pas anonymes (RV03-02, D-67) ; jeu synthétique ; conditions d'un déploiement réel » ;
  - section 4 : « chaque nombre écrit **en chiffres** dans la fiche figure dans l'entrée », et la liste des limites des contrôles (D-67, point 3) ;
  - section 5 : effectifs par statut, nombre d'essais, motifs de rejet, et 3 fiches complètes avec l'avertissement (le risque le plus élevé, un étudiant en tutorat, et une fiche « à revoir » s'il y en a) ; une phrase : l'évaluation LL-02 viendra de la grille remplie par Saliou.
  - Réexécuter de haut en bas.
- README : même reformulation (« pseudonymisées »), commandes `--verifier` et `--revoir`, modèle réellement utilisé, arrêt sans trace Python sur quota.
- Commit : `LL-01 : notebook 06 et README avec les fiches générées (#23)`.

## Livraison
- Vérifier à la fin : `pytest` ; `git status` propre ; aucun fichier `.env…` suivi (`git ls-files ".env*"` ne montre que `.env.example`) ; `git grep -n "AIza"` ne trouve que les consignes.
- Compte rendu au format du §10 de `CLAUDE.md`, avec : modèle utilisé ; durée et nombre d'appels de la génération ; fiches « validée » et « à revoir » ; durées de `run_all.py` ; effet du repli sur `ca_sensibilite.csv` ; résultat de la partie C ; la fiche recopiée ; et, pour chaque constat RV03-01 à RV03-08, ce qui a été fait (ou pourquoi non).
- Kanban (pour Saliou) : LL-01 passe à Terminé après vérification ; LL-02 commence avec la grille.
