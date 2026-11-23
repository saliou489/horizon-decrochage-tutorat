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
3. Tout relancer (nettoyage des 5 tables, `base_survie.csv` et `base_periode_personne.csv`, modèles de survie, effet du tutorat, entrées des fiches d'alerte) : `python run_all.py` (environ 6 min sur le PC de développement ; aucune clé d'API nécessaire)
4. Lancer les tests : `pytest`
5. Exécuter un notebook de haut en bas et l'enregistrer avec ses sorties :
   `jupyter nbconvert --to notebook --execute --inplace notebooks/01_nettoyage.ipynb`

## Données

Les fichiers de `data/raw/` sont un jeu **synthétique** fourni par l'enseignant : aucun étudiant réel. Les messages bruts (`data/raw/messages.csv`) contiennent des noms, e-mails et numéros de téléphone **inventés** (tous les numéros sont de la forme « 7X 000 XX XX »), laissés pour l'exercice de pseudonymisation. Ils sont conservés tels quels, car les fichiers bruts ne doivent pas être modifiés (`data/raw_sha256.txt`). Toutes les tables produites (`data/processed/`) sont pseudonymisées (`[NOM]`, `[TEL]`, `[EMAIL]`, décision D-28) et aucun texte de message n'est envoyé à un service externe.

## Fiches d'alerte (LLM)

**À quoi servent-elles ?** À la semaine 8, le modèle de Cox estime pour chaque étudiant de la cohorte 2025 encore inscrit le risque de décrocher d'ici la semaine 30. Pour les étudiants dont ce risque atteint 40 %, un LLM (Gemini, API de Google) **rédige** une fiche courte pour préparer un entretien : situation, points d'attention, 2 ou 3 actions prises dans une liste fermée. Le LLM ne décide de rien : chaque fiche porte un avertissement fixe et reste à vérifier par le conseiller (décisions D-65, D-66).

**Ce qui est envoyé à Gemini** : une liste fermée de champs : semaine, horizon, risque arrondi et risque moyen de la promotion, au plus 3 facteurs (libellé, valeur arrondie, référence de la promotion, multiplicateur), activité moyenne des semaines 7 et 8 et celle de la promotion, statut de tutorat.
**Ce qui n'est jamais envoyé** : identifiant, nom, contact, texte de message, genre, région. Chaque entrée est contrôlée avant l'envoi (clés autorisées, vocabulaire fermé, motifs d'identifiant, d'e-mail et de téléphone) ; si le contrôle échoue, rien n'est envoyé. Chaque fiche reçue est contrôlée à son tour (chaque nombre doit figurer dans l'entrée, mots interdits, actions de la liste) et redemandée si besoin (3 essais au plus, sinon statut « à revoir »).

**Obtenir une clé** : se connecter à Google AI Studio, page « API keys », créer une clé ; copier `.env.example` en `.env` à la racine du dépôt (PowerShell : `Copy-Item .env.example .env` ; Linux / macOS : `cp .env.example .env`) et coller la clé après `GEMINI_API_KEY=`. `.env` et toutes ses variantes (`.env.txt`, `.env.local`…) sont ignorés par git, sauf `.env.example` : la clé n'est jamais commitée ni affichée. Vérification : après avoir collé la clé, `git status` ne doit lister aucun fichier `.env`.

**Commandes** (depuis la racine du dépôt) :
- `python -m src.llm --tester` : un seul appel neutre, sans aucune donnée d'étudiant, pour vérifier la clé et le modèle ;
- `python -m src.llm --generer` : génère les fiches manquantes (cache réutilisé ; `--forcer` pour tout régénérer ; `--modele` pour changer de modèle) ;
- `python -m src.llm --grille` : écrit la grille d'évaluation de 20 fiches tirées au hasard (`docs/evaluation_fiches_llm.csv`).

**Quotas** : le niveau gratuit limite le nombre de requêtes par minute et par jour (page « Rate limit » d'AI Studio) ; le code attend 7 s entre deux appels et s'arrête proprement si le quota est atteint, sans perdre les fiches déjà faites.

**Reproductibilité** : les fiches générées sont enregistrées dans le dépôt (`data/processed/resultats/llm_fiches_semaine8.json`, avec le modèle, la version du prompt et la date). Ni l'enseignant ni `run_all.py` n'ont donc besoin d'une clé : `run_all.py` reconstruit seulement les entrées, sans appeler l'API.

**Cadre** : loi sénégalaise n° 2008-12 du 25 janvier 2008 sur la protection des données à caractère personnel ; RGPD pour comparaison (finalité, minimisation, sécurité). Au niveau gratuit, Google peut utiliser les requêtes pour améliorer ses produits : raison de plus pour n'envoyer aucune donnée personnelle.

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
| Gemini, API de Google (**composant du produit**) | Rédaction des fiches d'alerte destinées aux conseillers, à partir d'une liste fermée de champs sans donnée personnelle (`src/llm.py`, `src/prompts/`) ; chaque fiche est contrôlée automatiquement et reste à vérifier par le conseiller. |

Les règles de nettoyage et les choix de méthode sont décidés par l'étudiant et tracés dans `docs/decisions.md`.
Tout le code est relu par l'étudiant et doit pouvoir être expliqué en soutenance.
