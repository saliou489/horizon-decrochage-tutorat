# Consigne C16b — LL-02 : reprise de la génération v2 (issue #24)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- `git pull --rebase origin main`. Prérequis : C16 étapes 0 à 3 poussées ; cache v2 partiel (7 fiches sur 54, commit 07fa160). Garde ton travail local non commité (README, page « À propos », script du notebook 06) : il servira à la fin.

## Contexte
Le 24/11, les refus de l'API sont arrivés par vagues : 2 ou 3 appels réussis, puis 3 refus en 90 s, puis de nouveau des appels réussis quelques minutes plus tard. D'après AI Studio, Gemini 3.5 Flash Lite a atteint au plus 5 requêtes par minute ce mois-ci, pour une limite de 15. Un quota du jour épuisé ne reviendrait pas avant 8 h UTC : les vagues ressemblent plutôt à une surcharge passagère (code 503). On ne le sait pas, car le message final ne garde pas le code du refus. Cette consigne fait trois choses :
- elle montre la cause de chaque refus ;
- elle attend plus longtemps avant d'abandonner ;
- elle génère d'abord les 20 fiches de la grille, pour que Saliou puisse noter même si la suite bloque.

**Correction de la consigne C16 (erreur du pilotage).** L'étape 4.4 de C16 demandait de commiter `VERSION_PROMPT = "v2"` avec un cache partiel. Avec ce réglage, le test du tableau de bord échoue. Tu as bien fait de ne pas le faire. Règle à suivre désormais :
- `VERSION_PROMPT = "v2"` n'est commité qu'avec les 54 fiches v2 ;
- un cache partiel est commité avec `"v1"`, comme 07fa160.

Ce qui ne change pas : le gabarit v2, les entrées, les contrôles, le schéma et le modèle. Ce qui part vers l'API reste identique. Les règles API de C16 s'appliquent toujours, notamment : tu n'ouvres pas `.env`.

## Étape 1 — Montrer la cause d'un refus
1. Dans `creer_appel_gemini`, pour un code de `CODES_QUOTA`, le message d'`ErreurQuotaLLM` donne :
   - le code et le statut (`429 RESOURCE_EXHAUSTED`, `503 UNAVAILABLE`…) ;
   - pour un 429, s'ils sont présents dans `erreur.details` : `quotaId` et `quotaValue` de la violation `QuotaFailure`, et `retryDelay` de `RetryInfo`.

   Lis ces champs avec prudence : si un champ manque, rien ne doit planter. Ne recopie jamais le texte libre du message : comme pour les autres erreurs (D-67), il pourrait citer la requête.
2. Dans `appeler_avec_quota`, chaque refus affiche une ligne. Exemple : `Refus de l'API (429 RESOURCE_EXHAUSTED, GenerateRequestsPerDay…, limite 20) : nouvel essai dans 120 s.` Si les essais sont épuisés, l'erreur finale reprend la description du dernier refus.
3. Tests :
   - une fausse erreur 429 avec des `details` complets donne le bon message ;
   - une erreur sans `details` donne juste le code et le statut ;
   - avec un faux `attendre` qui enregistre les durées, l'erreur finale reprend le dernier refus, et les attentes suivent `ATTENTES_QUOTA_LLM`.

## Étape 2 — Attendre plus longtemps
Dans `config.py`, avec un commentaire qui cite C16b et les refus par vagues du 24/11 :
- `ATTENTES_QUOTA_LLM = (30, 60, 120, 300, 600)` : environ 18 minutes de patience par appel avant d'abandonner ;
- `PAUSE_ENTRE_APPELS_LLM = 20` : 3 appels par minute, loin de la limite de 15.

## Étape 3 — Les 20 fiches de la grille d'abord
1. Nouvelle fonction `ids_evaluation()` : elle renvoie les identifiants de la grille v1, dans l'ordre du fichier. D-69, point 3, demande de noter les mêmes 20 fiches en v2. Si la grille v1 n'existe pas, `ErreurLLM` claire.
2. Nouvelle option `--ids-grille`, seulement avec `--generer` (comme `--limite`, avec laquelle elle se combine).
   - Seules les entrées dont l'identifiant est dans `ids_evaluation()` sont envoyées.
   - Pour les autres, c'est le même mécanisme que `--limite` : rien n'est envoyé, leur fiche du cache est gardée si elle existe, et aucune fiche du cache n'est perdue.
3. `--grille` :
   - pour une version autre que `v1`, la grille prend les identifiants de `ids_evaluation()`, sans nouveau tirage ;
   - `ErreurLLM` si l'une de ces fiches manque dans le cache de la version ;
   - le refus d'écraser une grille existante ne change pas.
4. Le test d'invariant des grilles change, parce qu'un cache partiel ferait un autre tirage :
   - la grille v1 garde les identifiants de `echantillon_evaluation` sur le cache v1 ;
   - toute autre grille a exactement les identifiants de `ids_evaluation()`, et chacun existe dans le cache de sa version.
5. Test `--ids-grille`, avec une fausse fonction d'appel :
   - entrées A, B, C, D ; identifiants permis : A et C ; cache : une fiche validée pour D ;
   - attendu : seules A et C sont envoyées, B est absente, D est gardée.
6. `pytest`, puis commit : `LL-02 : refus de l'API expliqués, attentes plus longues, fiches de la grille d'abord (#24)`, et push.

## Étape 4 — Génération en deux temps (seule étape avec l'API)
La génération peut durer plus d'une heure : le PC ne doit pas se mettre en veille.

1. **Temps 1 : les fiches de la grille.**
   - Passe `VERSION_PROMPT = "v2"` en local, sans le commiter.
   - `python -m src.llm --tester`, puis `python -m src.llm --generer --ids-grille`. Il reste 15 fiches à faire, puisque 5 des 7 déjà faites sont dans la grille.
   - Si les 20 fiches sont là : `python -m src.llm --grille` crée `docs/evaluation_fiches_llm_v2.csv` avec les 20 identifiants de la grille v1.
   - Remets `"v1"`, lance `pytest`, puis commit : `LL-02 : fiches v2 de la grille et grille v2 à noter (#24)`. Ce commit contient le cache partiel et la grille v2. Push, pour que le pilotage prépare la page de notation.
2. **Temps 2 : les autres fiches.**
   - Repasse `"v2"`, puis `python -m src.llm --generer` (environ 32 fiches).
   - **Avec les 54 fiches :**
     - `python -m src.llm --verifier` : 0 fiche rétrogradée attendue en v1 comme en v2 ;
     - vérifie que les entrées sont identiques en v1 et en v2 ;
     - termine les étapes 5 et 6 de C16 (notebook 06, tableau de bord, README), en gardant `"v2"` ;
     - commite le cache complet avec `config.py` en `"v2"`.
   - **Si l'API s'arrête encore** (au temps 1 ou au temps 2) : remets `"v1"`, commite le cache partiel (et la grille v2 si elle existe), push, et rends compte.
3. Ne lance pas `--forcer` : les 7 fiches v2 déjà faites sont bonnes et restent dans le cache.

## Livraison
Compte rendu au format du §10 de `CLAUDE.md`, avec :
- les lignes de refus vues (code, statut, quota) ;
- le nombre d'appels, de refus et de minutes d'attente, et la durée totale ;
- `resume_indicateurs` sur les fiches v2 ;
- l'état final (54 fiches ou cache partiel).

Kanban : LL-02 reste « En cours » jusqu'à la notation v2.
