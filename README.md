# horizon-decrochage-tutorat

Projet individuel — Institut Supérieur Horizon, filière Expert IA & LLM.
**Anticiper le décrochage et mesurer l'effet du tutorat** : nettoyage de données, analyse de survie, inférence causale, assistant LLM.

- Auteur : Saliou (GitHub : saliou489)
- Période : 13 → 27 novembre 2026 (rendu le 27/11 à 18 h)
- Cahier des charges : `docs/cahier_des_charges.pdf`

## Structure

| Dossier | Contenu |
|---|---|
| `data/raw/` | Fichiers bruts fournis (non modifiés) |
| `data/processed/` | Tables nettoyées + `base_survie.csv` |
| `src/` | Code Python (nettoyage, survie, causal, llm) |
| `notebooks/` | `01_nettoyage` … `06_llm` |
| `tests/` | Tests automatiques (pytest) |
| `app/` | Tableau de bord |
| `docs/` | Journal de nettoyage, rapport, note de synthèse, gestion de projet |

## Installation et exécution

Prérequis : Python 3.12 ou plus (décision D-05). Toutes les commandes se lancent depuis la racine du dépôt.

1. Créer et activer l'environnement virtuel :
   - Windows : `py -m venv .venv` puis `.venv\Scripts\activate`
   - Linux / macOS : `python3 -m venv .venv` puis `source .venv/bin/activate`
2. Installer les dépendances : `pip install -r requirements.txt`
3. Tout relancer (nettoyage des 5 tables, `base_survie.csv` et `base_periode_personne.csv`, modèles de survie, effet du tutorat, entrées des fiches d'alerte) : `python run_all.py` (environ 4 min sur le PC de développement, PC au repos sur secteur : 224 à 239 s mesurés le 23/11 ; un premier lancement après une installation neuve peut être nettement plus long : 16 min 41 s mesurées par la relecture RV03 ; aucune clé d'API nécessaire)
4. Lancer les tests : `pytest`
5. Exécuter un notebook de haut en bas et l'enregistrer avec ses sorties :
   `jupyter nbconvert --to notebook --execute --inplace notebooks/01_nettoyage.ipynb`

## Données

Les fichiers de `data/raw/` sont un jeu **synthétique** fourni par l'enseignant : aucun étudiant réel. Les messages bruts (`data/raw/messages.csv`) contiennent des noms, e-mails et numéros de téléphone **inventés** (tous les numéros sont de la forme « 7X 000 XX XX »), laissés pour l'exercice de pseudonymisation. Ils sont conservés tels quels, car les fichiers bruts ne doivent pas être modifiés (`data/raw_sha256.txt`). Toutes les tables produites (`data/processed/`) sont pseudonymisées (`[NOM]`, `[TEL]`, `[EMAIL]`, décision D-28) et aucun texte de message n'est envoyé à un service externe.

## Fiches d'alerte (LLM)

**À quoi servent-elles ?** À la semaine 8, le modèle de Cox estime pour chaque étudiant de la cohorte 2025 encore inscrit le risque de décrocher d'ici la semaine 30. Pour les étudiants dont ce risque atteint 40 % (54 étudiants), un LLM (Gemini, API de Google, modèle `gemini-3.5-flash-lite`) **rédige** une fiche courte pour préparer un entretien : situation, points d'attention, 2 ou 3 actions prises dans une liste fermée. Le LLM ne décide de rien : chaque fiche porte un avertissement fixe et reste à vérifier par le conseiller (décisions D-65, D-66, D-67).

**Ce qui est envoyé à Gemini** : une liste fermée de champs : semaine, horizon, risque arrondi et risque moyen de la promotion, au plus 3 facteurs (libellé, valeur arrondie, référence de la promotion, multiplicateur), activité moyenne des semaines 7 et 8 et celle de la promotion, statut de tutorat.
**Ce qui n'est jamais envoyé** : identifiant, nom, contact, texte de message, genre, région. Chaque entrée est contrôlée avant l'envoi (clés autorisées, type et format de chaque valeur, listes fermées, motifs d'identifiant, d'e-mail et de téléphone) ; si le contrôle échoue, rien n'est envoyé. Chaque fiche reçue est contrôlée à son tour (chaque nombre écrit en chiffres doit figurer dans l'entrée, mots interdits, actions de la liste) et redemandée si besoin (3 essais au plus, sinon statut « à revoir »). Ces contrôles ne voient pas tout (nombre calculé qui coïncide avec un nombre de l'entrée, nombre attribué au mauvais champ, ton) : c'est le rôle de la relecture humaine de LL-02.
**Des données pseudonymisées, pas anonymes** (D-67) : aucune donnée directement identifiante n'est envoyée, mais la combinaison des valeurs envoyées est propre à chaque étudiant de la promotion ; les entrées restent donc des données personnelles pseudonymisées. Le jeu étant synthétique, aucun étudiant réel n'est concerné ; un déploiement réel demanderait un LLM local ou une offre sans réutilisation des données, avec un contrat de sous-traitance et l'information des étudiants.

**Obtenir une clé** : se connecter à Google AI Studio, page « API keys », créer une clé ; copier `.env.example` en `.env` à la racine du dépôt (PowerShell : `Copy-Item .env.example .env` ; Linux / macOS : `cp .env.example .env`) et coller la clé après `GEMINI_API_KEY=`. `.env` et toutes ses variantes (`.env.txt`, `.env.local`…) sont ignorés par git, sauf `.env.example` : la clé n'est jamais commitée ni affichée. Vérification : après avoir collé la clé, `git status` ne doit lister aucun fichier `.env`.

**Commandes** (depuis la racine du dépôt) :
- `python -m src.llm --tester` : un seul appel neutre, sans aucune donnée d'étudiant, pour vérifier la clé et le modèle ;
- `python -m src.llm --generer` : génère les fiches manquantes (cache réutilisé et revérifié ; `--revoir` pour régénérer seulement les fiches « à revoir » ; `--forcer` pour tout régénérer ; `--modele` pour changer de modèle) ;
- `python -m src.llm --verifier` : repasse les contrôles actuels sur les fiches du cache, sans appel ; une fiche qui ne les passe plus devient « à revoir » ;
- `python -m src.llm --grille` : écrit la grille d'évaluation de 20 fiches tirées au hasard (`docs/evaluation_fiches_llm_<version>.csv`, une grille par version du prompt).

**Quotas** : le niveau gratuit limite le nombre de requêtes par minute et par jour (page « Rate limit » d'AI Studio) ; le code attend 7 s entre deux appels et, si le quota est atteint, s'arrête avec un simple message (sans trace Python, code de sortie 1), sans perdre les fiches déjà faites : le cache est écrit après chaque fiche, de façon atomique.

**Reproductibilité** : les fiches générées sont enregistrées dans le dépôt (`data/processed/resultats/llm_fiches_semaine8_<version>.json`, un fichier par version du prompt, avec le modèle, la version du prompt et la date). Ni l'enseignant ni `run_all.py` n'ont donc besoin d'une clé : `run_all.py` reconstruit seulement les entrées, sans appeler l'API.

**Cadre** : loi sénégalaise n° 2008-12 du 25 janvier 2008 sur la protection des données à caractère personnel ; RGPD pour comparaison (finalité, minimisation, sécurité). Au niveau gratuit, Google peut utiliser les requêtes pour améliorer ses produits : c'est acceptable ici seulement parce que le jeu est synthétique.

## Tableau de bord

Commande (depuis la racine du dépôt, après `python run_all.py`) : `streamlit run app/app.py`, puis ouvrir l'adresse affichée (par défaut http://localhost:8501). Aucune clé d'API n'est nécessaire : le tableau de bord relit les fichiers de `data/processed/` et le cache des fiches, sans recalculer de modèle ni appeler le LLM (décision D-68). Données synthétiques ; identifiants pseudonymisés.

Dans la barre latérale : la semaine L (1 à 29, 8 par défaut) et le seuil de risque (5 à 80 %, 40 % par défaut), communs aux 4 pages :
1. **Étudiants à risque** : étudiants de la cohorte 2025 encore suivis après la semaine L, classés par risque de décrocher d'ici la semaine 30 (Cox), avec le risque de la semaine suivante (gradient boosting), les facteurs associés, le tutorat et le statut de la fiche LLM ;
2. **Fiche étudiant** : risques, profil de rentrée (ni genre ni région), facteurs, activité des deux dernières semaines, courbe de survie individuelle et fiche LLM (semaine 8), avec son avertissement ;
3. **Effet du tutorat** : estimation de CA-04 (risques, différence, rapport, RMST, HR, E-value), courbes pondérées, variantes de CA-05 et hypothèses ;
4. **À propos** : données, validation des modèles 2024 → 2025, fiches LLM, limites.

Captures : `docs/figures/db_page1_risque.png` à `db_page4_apropos.png`.

## Limites connues

- Seules les dépendances directes sont figées dans `requirements.txt` ; leurs dépendances indirectes ne le sont pas (décision D-44 : un verrouillage complet fait sous Windows ne s'installerait pas sous Linux).
- Le projet a été testé sous Windows avec Python 3.14.3.

## Déclaration d'usage d'assistants IA

Conformément au cahier des charges (§6.2), l'usage d'assistants IA est déclaré :

| Outil | Usage |
|---|---|
| Claude Code (Anthropic) | Écriture du code, des tests et de la documentation technique, à partir de consignes écrites et versionnées dans `docs/consignes/`. Cadre de travail : `CLAUDE.md`. |
| Claude, en conversation (Anthropic) | Rédaction et test des consignes, vérification des résultats, explication du code et des méthodes à l'étudiant, brouillons de documents (journal de bord, registre des risques, rapport) relus et corrigés par l'étudiant. |
| Claude Code, session de relecture (Anthropic) | Relecture indépendante des consignes, du code, des tests et de la sécurité ; rapports dans `docs/revues/`. |
| Gemini, API de Google (**composant du produit**) | Rédaction des fiches d'alerte destinées aux conseillers, à partir d'une liste fermée de champs sans donnée directement identifiante (entrées pseudonymisées, D-67 ; `src/llm.py`, `src/prompts/`) ; chaque fiche est contrôlée automatiquement et reste à vérifier par le conseiller. |

Les règles de nettoyage et les choix de méthode sont décidés par l'étudiant et tracés dans `docs/decisions.md`.
Tout le code est relu par l'étudiant et doit pouvoir être expliqué en soutenance.
