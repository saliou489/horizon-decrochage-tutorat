# R03 — Relecture de sécurité des fiches LLM (LL-01), avant le premier appel réel à l'API

Suis `docs/consignes/R00_mission_relecteur.md`. Prérequis : consigne C13 exécutée (commits `LL-01 : …` du 23/11).

**Règles propres à cette relecture (D-65)** :
- **Aucun appel réel à l'API** : tu ne crées pas de `.env`, tu ne lances ni `python -m src.llm --tester` ni `--generer`. Si ton clone contient un `.env`, c'est un constat : ne l'ouvre pas.
- Les fiches n'existent pas encore : tu relis le code, le prompt, les tests et le fichier d'entrées.
- Dans ton rapport, ne recopie aucune entrée complète : cite des clés, des comptes, des numéros de ligne.

## Périmètre
- Décisions : D-65 et D-66 de `docs/decisions.md` (et D-63, D-64 qu'elles citent).
- Consigne : `docs/consignes/C13_LL-01_fiches_llm.md`.
- Code : `src/llm.py`, section « Fiches d'alerte par LLM » de `src/config.py`, `src/prompts/fiche_v1.md`, `run_all.py`.
- Tests : `tests/test_llm.py`.
- Fichiers : `data/processed/resultats/llm_entrees_semaine8.json`, `.env.example`, `.gitignore`, `requirements.txt`, section « Fiches d'alerte (LLM) » du README, `notebooks/06_llm.ipynb`.
- Référentiel : cahier des charges (F6), `CLAUDE.md` (§4 « Secrets », §6 « LLM et données personnelles »).

## Questions à traiter en priorité
1. **Secrets** : la clé ne peut-elle venir que de `.env`, passée explicitement au client ? Peut-elle apparaître dans une sortie, un message d'erreur, une trace d'exception, un notebook, un fichier produit ou un commit ? Historique compris : `git log -p --all` à la recherche de `AIza`, de `GEMINI_API_KEY=` suivi d'une valeur, de `api_key=` suivi d'une chaîne. `.env` est-il ignoré (`git check-ignore -v .env`) ?
2. **Données envoyées** : en lisant le code (pas seulement les tests), un identifiant, un nom, un contact, un texte de message, le genre ou la région peuvent-ils atteindre la fonction d'appel ? `verifier_entree_sans_donnee_personnelle` est-elle appelée juste avant chaque appel, et ferme-t-elle vraiment toutes les clés et tous les textes ? Les 54 lignes du fichier d'entrées respectent-elles la liste fermée ?
3. **Injection de prompt** : un texte issu des données (filière, modalité) peut-il porter une instruction ? Tous les textes de l'entrée viennent-ils d'un vocabulaire fermé ou d'un format fixé par le code ?
4. **Contrôles de la réponse** : le contrôle des nombres, des mots interdits, des actions et de la cohérence du tutorat protège-t-il vraiment ? Cherche des contre-exemples (nombre calculé qui tombe par hasard sur un nombre de l'entrée, nombre en lettres, mot interdit avec majuscule ou apostrophe, action presque identique à une action de la liste) ; dis lesquels sont des limites acceptables à écrire et lesquels sont à corriger.
5. **Boucle de génération** : ni boucle infinie ni appels en rafale ; pause et attentes respectées ; arrêt propre quand le quota est atteint ; cache écrit après chaque fiche ; fiche « à revoir » bien signalée ; avertissement toujours ajouté par le code ; nombre maximal d'appels pour 54 fiches compatible avec le quota gratuit de D-65.
6. **Tests sans réseau** : aucun test n'appelle l'API ni ne lit un vrai `.env` ; `google.genai` n'est importé que dans `creer_appel_gemini` ; un test protège-t-il vraiment la règle « l'identifiant n'est jamais envoyé » ?
7. **Dépendances et reproductibilité** : `pip install -r requirements.txt` (google-genai 3.6.1, python-dotenv 1.2.4) ; `python run_all.py` deux fois → `git status` propre et aucun appel à l'API ; `pytest` ; notebook 06 exécutable de haut en bas sans clé.
8. **Textes destinés aux humains** (README, notebook 06, prompt) : cadre juridique cité sans exagération (des données pseudonymisées ne sont pas « anonymes ») ; vocabulaire « associé à » ; avertissement fixe présent ; rien qui promette plus que ce que fait le code.

## Livraison
- Rapport `docs/revues/RV03_securite_llm.md`, commit `RV03 : relecture de sécurité des fiches LLM`, push sur `main`.
- Le verdict dit clairement si le premier appel réel (`python -m src.llm --tester`) peut avoir lieu, et à quelles conditions.
