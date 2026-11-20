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
3. Tout relancer (nettoyage des 5 tables, puis `base_survie.csv` et `base_periode_personne.csv`) : `python run_all.py` (environ 15 s sur le PC de développement)
4. Lancer les tests : `pytest`
5. Exécuter un notebook de haut en bas et l'enregistrer avec ses sorties :
   `jupyter nbconvert --to notebook --execute --inplace notebooks/01_nettoyage.ipynb`

## Données

Les fichiers de `data/raw/` sont un jeu **synthétique** fourni par l'enseignant : aucun étudiant réel. Les messages bruts (`data/raw/messages.csv`) contiennent des noms, e-mails et numéros de téléphone **inventés** (tous les numéros sont de la forme « 7X 000 XX XX »), laissés pour l'exercice de pseudonymisation. Ils sont conservés tels quels, car les fichiers bruts ne doivent pas être modifiés (`data/raw_sha256.txt`). Toutes les tables produites (`data/processed/`) sont pseudonymisées (`[NOM]`, `[TEL]`, `[EMAIL]`, décision D-28) et aucun texte de message n'est envoyé à un service externe.

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

Les règles de nettoyage et les choix de méthode sont décidés par l'étudiant et tracés dans `docs/decisions.md`.
Tout le code est relu par l'étudiant et doit pouvoir être expliqué en soutenance.
