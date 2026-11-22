# CLAUDE.md — Projet Horizon : décrochage & tutorat

> Lu automatiquement par Claude Code à chaque session : ce fichier fixe le cadre de travail de tout le projet.
> Priorité en cas de conflit : **cahier des charges** (`docs/cahier_des_charges.pdf`) > **ce fichier** > **consigne en cours**.
> Si une consigne contredit l'un des deux premiers, ne choisis pas : arrête-toi et signale-le.
> Ce fichier n'est modifié qu'à la demande de Saliou.

## 1. Le projet en bref

- Projet individuel de Saliou (GitHub `saliou489`), noté sur 20 — Institut Supérieur Horizon, filière Expert IA & LLM.
- La direction des études pose deux questions :
  1. **Prédictive** : quand un étudiant risque-t-il de décrocher, et quels facteurs y sont *associés* ? → analyse de survie.
  2. **Causale** : le tutorat *fait-il baisser* le décrochage ? → inférence causale. Deux pièges : le **biais de sélection** (on oriente vers le tutorat ceux qui vont déjà mal) et le **biais du temps immortel** (on ne peut être tutoré que si l'on est encore inscrit).
- Données synthétiques « Horizon » : 5 000 étudiants, cohortes 2024 et 2025, suivis 30 semaines. L'enseignant connaît le vrai effet du tutorat : notre estimation sera comparée à la vérité.
- Rendu : **vendredi 27/11/2026, 18 h**. Seul l'état du dépôt à 18 h est évalué ; −2 points par jour de retard.
- Barème : causal 5 · nettoyage 4 · survie 4 · gestion de projet 3 · LLM & tableau de bord 2 · rapport & soutenance 2 · bonus Could +1.

## 2. Qui fait quoi

| Acteur | Rôle |
|---|---|
| **Saliou** | Product owner et seul décideur. Valide chaque règle de nettoyage et chaque choix de méthode. Tient le Kanban (GitHub Projects) et le journal de bord. Doit pouvoir expliquer chaque ligne en soutenance. |
| **Session de pilotage** (chat Claude) | Rédige les consignes dans `docs/consignes/`, vérifie les résultats sur le dépôt, explique le code à Saliou. |
| **Session d'exécution** (Claude Code, rôle par défaut) | Exécute **une consigne à la fois** : code, tests et documentation demandés ; commit, push, compte rendu. |
| **Session de relecture** (Claude Code, clone séparé) | Relit consignes, code, tests et sécurité aux points de contrôle ; **ne modifie rien** ; écrit seulement ses rapports dans `docs/revues/`. Sa mission : `docs/consignes/R00_mission_relecteur.md`. |

Dans ce fichier, « tu » désigne la session d'exécution. Une session lancée avec la mission de relecture suit `R00_mission_relecteur.md`, qui prime pour son rôle ; le reste de ce fichier (contexte, définitions, règles de méthode) s'applique aussi à elle.

### Déroulé d'une consigne

1. `git pull --rebase origin main`.
2. Lire la consigne en entier (`docs/consignes/Cxx_<ID>_<sujet>.md`), puis les sections du cahier des charges qu'elle cite.
3. Faire **uniquement** ce qu'elle demande : ne pas commencer la tâche suivante, ne pas retoucher du code hors périmètre.
4. Exécuter le code concerné de bout en bout et lancer `pytest`.
5. Commit(s) avec l'identifiant de tâche, `git pull --rebase origin main`, push sur `main`.
6. Rendre compte au format du §10.

### Ce que tu ne tranches jamais seul

Toute règle de nettoyage (supprimer / corriger / mettre à manquant), les détails de T, E et de la censure, le choix des covariables, la semaine landmark, la spécification causale, le choix du LLM.

Si la consigne ne couvre pas un cas : décris-le dans `docs/decisions.md` (statut **proposée**, options et recommandation argumentée) et signale-le dans le compte rendu. Seul Saliou passe une décision à **validée**. Si le cas bloque la suite, arrête-toi là.

## 3. Emplacements

- Dépôt GitHub : https://github.com/saliou489/horizon-decrochage-tutorat (public, branche `main`).
- Copie de travail sur le PC de Saliou (Windows) : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` — hors OneDrive (la racine `C:\` n'est pas accessible en écriture sur ce PC). Le chemin contient des espaces (nom d'utilisateur) : dans toute commande shell, mettre les chemins entre guillemets.
- Dossier de cours d'origine (cahier des charges et archive de l'enseignant) : `C:\Users\SERIGNE SALIOU SEYE\OneDrive\Documents\cours école BEM TECH\TROISIEME ANNEE\Semestre 5\Projet-3`. **Ne rien y écrire** : les fichiers utiles sont déjà copiés dans le dépôt.
- Ne travaille **que** dans le dossier du dépôt.
- Dans le code : **uniquement des chemins relatifs à la racine du dépôt**, centralisés dans `src/config.py` (pathlib). Aucun chemin absolu.

### Arborescence (imposée par le cahier, §6.1)

| Chemin | Contenu | Qui écrit |
|---|---|---|
| `README.md` | présentation, installation, commande unique, déclaration d'usage de l'IA | exécution |
| `run_all.py` | commande unique qui relance tout le pipeline | exécution |
| `requirements.txt` | dépendances, versions exactes (`==`) | exécution |
| `data/raw/` | 5 CSV bruts + `LISEZMOI.md` | **personne — lecture seule** |
| `data/raw_sha256.txt` | empreintes des fichiers bruts (preuve qu'ils sont intacts) | personne |
| `data/processed/` | tables nettoyées, `base_survie.csv`, `base_periode_personne.csv` | le pipeline uniquement |
| `src/` | code Python : `config`, `audit`, `nettoyage`, `base_survie`, `survie`, `ml_survie`, `causal`, `llm` | exécution |
| `notebooks/` | `01_nettoyage`, `02_eda`, `03_survie`, `04_ml_survie`, `05_causal`, `06_llm` | exécution |
| `tests/` | tests pytest | exécution |
| `app/` | tableau de bord Streamlit (`app/app.py`) | exécution |
| `docs/consignes/` | consignes (Cxx) et demandes de relecture (Rxx) | **pilotage uniquement — ne pas modifier** |
| `docs/revues/` | rapports de relecture (RVxx) | session de relecture uniquement |
| `docs/decisions.md` | registre des décisions D-xx | exécution propose, Saliou valide |
| `docs/journal_nettoyage.md` | journal de nettoyage (livrable L2) | exécution (chiffres produits par le code) |
| `docs/figures/` | figures PNG | exécution |
| `docs/gestion_projet/` | journal de bord, registre des risques, rétrospectives, burndown, captures Kanban | Saliou (exécution seulement s'il le demande) |
| `docs/planning.md`, `docs/cahier_des_charges.pdf` | planning, cahier des charges | pilotage / lecture seule |

## 4. Environnement

- **Python 3.12 ou plus** (décision D-05 : numpy 2.5 l'exige ; PC de Saliou en Python 3.14), environnement virtuel `.venv/` à la racine (ignoré par git). Rien n'est installé hors du `.venv`.
  - Windows : `py -m venv .venv` puis `.venv\Scripts\activate`
  - Linux / macOS : `python3 -m venv .venv` puis `source .venv/bin/activate`
- `pip install -r requirements.txt`. Toute nouvelle bibliothèque est ajoutée à `requirements.txt` (version exacte) dans le même commit et justifiée dans le compte rendu.
- **pandas reste en 2.3.x** (décision D-52) : lifelines exige pandas < 3. Ne jamais monter pandas en 3.x ; une nouvelle bibliothèque doit être compatible avec les versions fixées dans `requirements.txt` et s'installer sous Python 3.14 sans compilation (sinon : s'arrêter et le signaler).
- Bibliothèques prévues (cahier §7) : pandas, numpy, pytest, lifelines, scikit-survival, scikit-learn, statsmodels, matplotlib, streamlit ; DoWhy et plotly en option.
- Si une bibliothèque refuse de s'installer avec la version de Python présente : s'arrêter et le signaler, ne pas bricoler.
- Commandes :
  - tout relancer : `python run_all.py`
  - tests : `pytest`
  - tableau de bord : `streamlit run app/app.py`
- Le code tourne sous **Windows** (PC de Saliou, démonstration) **et** sous Linux / macOS (machine de l'enseignant) : pathlib, aucune commande shell propre à un système.
- **Encodage** : toujours `encoding="utf-8"` explicite pour lire ou écrire un fichier texte. Sous Windows, Python peut sinon utiliser cp1252 et casser les accents.
- `run_all.py` doit tourner en moins de 15 min sur le PC de Saliou (HP EliteBook 840 G6) : nombre de bootstraps et taille des forêts réglés dans `config.py`.
- Réseau : chez Saliou, GitHub et certains sites peuvent être bloqués par le réseau local ; il utilise Cloudflare WARP. Si `git` ou `pip` échoue pour une raison réseau, le signaler (WARP à vérifier) sans tenter de contournement.
- Secrets : clés d'API uniquement dans `.env` (ignoré par git), avec un `.env.example` sans valeur. Jamais de clé dans le code, un notebook ou une sortie affichée.

## 5. Définitions imposées (cahier §4.3) — ne jamais s'en écarter

- **Unité** : l'étudiant. `base_survie.csv` = une ligne par étudiant (T, E, covariables, tutorat, semaine de début du tutorat).
- **Origine du temps** : semaine 1 = semaine de la date de rentrée **de l'étudiant** (`date_debut`). Temps en semaines, de 1 à 30.
- **Événement (E = 1, décrochage)** : abandon déclaré à la scolarité, **ou** 4 semaines consécutives sans **aucune** connexion **ni** devoir rendu. La semaine de l'événement est la **première** des 4 semaines.
- **Censure (E = 0)** : transfert vers un autre établissement, ou étudiant toujours inscrit à la semaine 30. **Ne jamais supprimer un censuré.**
- **Sensibilité** : le seuil d'inactivité est un paramètre (`SEUIL_INACTIVITE` dans `config.py`) ; les analyses sont refaites à 3 et 5 semaines (référence : 4).
- **Traitement** : avoir commencé le tutorat ; `semaine_debut_tutorat` est conservée. Interdit de comparer naïvement « tutoré un jour » et « jamais tutoré ».
- **Points de détail encore ouverts**, à faire valider par Saliou en DA-07 (ne pas les trancher seul) : conversion date → numéro de semaine ; semaine absente du fichier d'activité (inactivité ou donnée manquante ?) ; connexions ou devoirs manquants ; inactivité qui précède un abandon ou un transfert déclaré plus tard ; série d'inactivité coupée par la semaine 30.

## 6. Règles de méthode

### Nettoyage (F1)

- `data/raw/` n'est **jamais** modifié ; un test compare les fichiers à `data/raw_sha256.txt`. Le pipeline lit `data/raw/` et écrit `data/processed/` sans aucune intervention manuelle.
- Une anomalie traitée = une ligne de `docs/journal_nettoyage.md` : `# | Table | Anomalie constatée | Lignes | Traitement appliqué | Justification` (gabarit de l'annexe A), plus le tableau avant / après (lignes, valeurs manquantes, doublons par table). Les nombres sont **calculés par le code**, jamais recopiés à la main.
- Aucune ligne supprimée sans justification écrite. Quand une ligne porte d'autres informations utiles, préférer « mettre la valeur à manquant » à « supprimer la ligne ».
- Les valeurs manquantes **restent manquantes** dans `data/processed/`. L'imputation se fait seulement dans les pipelines de modélisation, avec des statistiques calculées sur les données d'entraînement (pas de fuite vers le test).
- Une règle de nettoyage = une fonction testable (DataFrame en entrée → DataFrame corrigé + nombre de lignes touchées).

### Survie et ML (F2 à F4)

- Graine unique `SEED = 42` dans `config.py`, passée explicitement à toute fonction aléatoire.
- **Covariables fixes** : uniquement celles de `config.COVARIABLES_RENTREE` (D-43), sélectionnées par cette liste, jamais par exclusion. `nb_seances`, `tutore`, `statut_tutorat` et les autres colonnes de tutorat ne sont jamais des covariables d'un modèle prédictif.
- **Modèles semaine par semaine** : activité de la semaine précédente ou d'avant uniquement (colonnes `*_prec`, D-42), jamais celle de la semaine en cours.
- Hypothèse des risques proportionnels vérifiée (résidus de Schoenfeld) ; si elle est violée, correction documentée (stratification, interaction avec le temps…).
- Validation temporelle imposée : entraînement sur la cohorte 2024, test sur la cohorte 2025. Rien de la cohorte 2025 ne sert à l'entraînement (ni imputation, ni normalisation, ni réglage).
- Métriques : C-index, Brier score intégré, calibration à 20 semaines, pour le Cox **et** le modèle non linéaire, sur le même jeu de test.

### Causal (F5)

- **Spécification fixée avant le résultat** : DAG, covariables, semaine landmark, troncature des poids et nombre de bootstraps sont écrits dans `docs/decisions.md` et validés par Saliou **avant** de calculer l'effet. Ne jamais changer la spécification après avoir vu le résultat ; les variantes sont présentées en sensibilité, pas en remplacement.
- Covariables du score de propension : uniquement des variables mesurées **avant** le début du tutorat (ou avant la semaine landmark).
- Temps immortel : analyse landmark (semaine L fixée en CA-01) ou covariable dépendante du temps.
- Équilibre : poids stabilisés, tronqués aux 1er et 99e percentiles ; SMD < 0,1 pour toutes les covariables après pondération ; love plot.
- Incertitude : IC par bootstrap (graine fixée). Sensibilité : E-value, au moins une spécification alternative, règles des 3 et 5 semaines.

### Honnêteté des résultats

- Un critère non atteint (SMD > 0,1, hypothèse PH violée, C-index faible…) est rapporté tel quel, jamais caché ni embelli.
- Vocabulaire : « associé à » partout ; « effet », « cause », « réduit » seulement pour l'estimation causale, avec ses hypothèses rappelées.
- Chaque chiffre ou figure clé est suivi d'une phrase compréhensible par un conseiller pédagogique.

### LLM et données personnelles (F6)

- Messages pseudonymisés (DA-05) avant tout traitement : noms, téléphones, e-mails et adresses remplacés par des balises (`[NOM]`, `[TEL]`, `[EMAIL]`…).
- **Aucune donnée personnelle envoyée à une API externe.** Le LLM ne reçoit qu'une liste fermée de champs (score, facteurs principaux…), sans identifiant étudiant.
- Le LLM n'invente aucun chiffre : les chiffres sont injectés dans le prompt et un contrôle automatique vérifie que chaque nombre de la fiche figure dans l'entrée.
- Gabarit de prompt versionné dans `src/prompts/`. Choix du modèle (local ou API) : décision à prendre en LL-01, ne pas l'anticiper.
- Cadre à citer : loi sénégalaise n° 2008-12 sur les données personnelles, RGPD pour comparaison.

## 7. Style de code — Saliou doit pouvoir tout expliquer

- Simple et lisible avant tout : pas d'astuce, pas de sur-ingénierie, pas de one-liner obscur. Trois lignes claires valent mieux qu'une ligne compacte.
- En tête de chaque module : un commentaire « Rôle du module » et les tâches couvertes (ex. `DA-02, DA-03`).
- Fonctions courtes, une seule responsabilité, docstring en français (but, entrées, sortie).
- Commentaires en français qui expliquent le **pourquoi** (règle métier, choix statistique), pas le quoi.
- Noms explicites en snake_case, alignés sur les colonnes des données (`id_etudiant`, `semaine`…).
- Paramètres et constantes dans `src/config.py` : aucun nombre magique ailleurs.
- La logique vit dans `src/` ; les notebooks importent `src/`, affichent et interprètent. Chaque notebook tourne de haut en bas sans erreur et est commité avec ses sorties.
- Figures enregistrées en PNG dans `docs/figures/`, nommées `<numéro du notebook>_<sujet>.png`.

## 8. Tests

- `pytest` à la racine ; au moins 5 tests (exigence), idéalement un par règle de qualité.
- Deux familles :
  1. **unitaires** : chaque fonction de nettoyage testée sur un petit DataFrame construit dans le test ;
  2. **invariants** sur `data/processed/` : identifiants uniques, semaines dans [1 ; 30], notes dans [0 ; 20], devoirs dans [0 ; 2], T dans [1 ; 30], E ∈ {0, 1}, une ligne par étudiant, aucun censuré perdu, `data/raw/` intact. Ces tests sont ignorés proprement (`skip`) tant que `data/processed/` n'existe pas.
- Un test qui échoue ne se corrige **jamais** en modifiant le test pour qu'il passe : on corrige le code, ou on signale le problème.

## 9. Git et traçabilité (l'historique est noté)

- `git pull --rebase origin main` avant de commencer et avant chaque push. La session de pilotage n'écrit que dans `docs/consignes/`, `docs/planning.md`, `docs/decisions.md` (décisions validées par Saliou), `docs/gestion_projet/` (brouillons demandés par Saliou) et, à sa demande, ce fichier ; la session de relecture n'écrit que dans `docs/revues/` : pas de conflit attendu ailleurs.
- Message de commit : `<ID> : <description>` (ex. `DA-02 : nettoyage de la table etudiants`). Ajouter ` (#n)` si l'issue GitHub de la tâche existe. Pas de `closes #n` : c'est Saliou qui passe la carte à Terminé après vérification.
- Petits commits fréquents, au moins un par tâche. Jamais de `push --force` ni de réécriture de l'historique.
- Jamais commités : `.venv/`, `.env`, caches, fichiers de plus de 50 Mo.

## 10. Compte rendu de fin de consigne (format fixe)

1. **Fait** — 3 à 6 puces.
2. **Fichiers** créés ou modifiés.
3. **Résultats clés** — chiffres principaux, chacun avec une phrase d'interprétation.
4. **Vérifications** — commandes lancées et résultat (`pytest` : n réussis / n échoués).
5. **Décisions en attente** — numérotées, avec options et recommandation ; non tranchées.
6. **Écarts** — ce qui n'a pas été fait, ou a été fait autrement que demandé, et pourquoi.
7. **Commit(s)** — hash et message.

## 11. Définition de « terminé » (cahier §11.3)

Le code tourne de bout en bout depuis le dépôt, sans erreur · les tests passent · chaque chiffre ou figure clé est interprété par écrit · tout est poussé avec l'ID de la tâche · Saliou met à jour la carte Kanban.

## 12. Repères

- Planning et jalons : `docs/planning.md` — M1 données propres (ven. 20/11) · M2 point d'étape avec l'enseignant, Cox + DAG (lun. 23/11) · M3 effet causal (mar. 24/11) · gel des fonctionnalités (mer. 25/11) · rendu (ven. 27/11, visé à 15 h).
- Préfixes des tâches : GP gestion de projet · DA données · SV survie · CA causal · LL LLM · DB tableau de bord · DO documentation (liste complète : cahier §10).
- En cas de retard : on abandonne d'abord les Could, puis les Should, jamais les Must.
- Déclaration d'usage de l'IA dans le README (outil et usage) : à tenir à jour.
