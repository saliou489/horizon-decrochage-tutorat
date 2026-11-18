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

_À compléter (commande unique pour tout relancer)._

## Déclaration d'usage d'assistants IA

Conformément au cahier des charges (§6.2), l'usage d'assistants IA est déclaré :

| Outil | Usage |
|---|---|
| Claude Code (Anthropic) | Écriture du code, des tests et de la documentation technique, à partir de consignes écrites et versionnées dans `docs/consignes/`. Cadre de travail : `CLAUDE.md`. |
| Claude, en conversation (Anthropic) | Rédaction des consignes, vérification des résultats, explication du code et des méthodes à l'étudiant. |

Les règles de nettoyage et les choix de méthode sont décidés par l'étudiant et tracés dans `docs/decisions.md`.
Tout le code est relu par l'étudiant et doit pouvoir être expliqué en soutenance.
