# Jeu de données « Horizon » — Décrochage et tutorat

Données **synthétiques** (fictives) de 5 000 étudiants de l'Institut Supérieur Horizon, répartis sur deux cohortes (2024-2025 et 2025-2026), suivis pendant 30 semaines à partir de la rentrée.

> ⚠️ Ces fichiers sont **bruts** : ils ont été extraits de plusieurs systèmes (scolarité, plateforme LMS, service de tutorat, formulaires de suivi) et contiennent des erreurs de saisie, des incohérences et des doublons. Votre premier travail est de les détecter, de les corriger et de documenter chaque décision dans un **journal de nettoyage**. Aucune liste des anomalies n'est fournie.

## Fichiers

| Fichier | Séparateur | Une ligne = | Lignes (≈) |
|---|---|---|---|
| `etudiants.csv` | `,` | un étudiant | 5 000 |
| `inscriptions.csv` | `;` | une inscription annuelle | 5 000 |
| `activite_hebdo.csv` | `,` | un étudiant × une semaine | 130 000 |
| `tutorat.csv` | `,` | une prise en charge en tutorat | 1 300 |
| `messages.csv` | `,` | un message (forum / formulaire de suivi) | 3 200 |

Encodage attendu : UTF-8. La clé de jointure est l'identifiant étudiant (format `HZ` + 5 chiffres, ex. `HZ38160`).

## Dictionnaire des variables

### etudiants
| Variable | Description | Valeurs attendues |
|---|---|---|
| id_etudiant | Identifiant pseudonymisé | `HZ00000` |
| cohorte | Année de rentrée | 2024, 2025 |
| genre | Genre déclaré | F, M |
| age | Âge à la rentrée (années) | 17 – 35 |
| boursier | Bénéficiaire d'une bourse | Oui, Non |
| filiere | Filière d'inscription | Informatique, Gestion, Droit, Génie civil, Communication |
| mention_bac | Mention obtenue au bac | Passable, Assez bien, Bien, Très bien |
| note_bac | Moyenne au bac (/20) | 10 – 20 (Passable 10–12, AB 12–14, B 14–16, TB ≥ 16) |
| region_origine | Région d'origine | 14 régions du Sénégal |
| distance_campus_km | Distance domicile actuel – campus (km) | > 0 |
| emploi_parallele | Exerce une activité rémunérée | Oui, Non |

### inscriptions
| Variable | Description |
|---|---|
| annee_universitaire | « 2024-2025 » ou « 2025-2026 » |
| date_debut | Date de rentrée (semaine 1 commence ce jour) |
| date_fin | Date de sortie déclarée à la scolarité (vide si toujours inscrit) |
| statut_final | abandon, transfert (départ vers un autre établissement), inscrit (toujours inscrit à la semaine 30) |

Attention : **tous les abandons ne sont pas déclarés** à la scolarité. Certains étudiants cessent simplement de venir. Le cahier des charges impose la règle : *abandon déclaré, ou 4 semaines consécutives sans aucune connexion ni devoir rendu*.

### activite_hebdo
| Variable | Description |
|---|---|
| semaine | Numéro de semaine depuis la rentrée (1 – 30) |
| nb_connexions_lms | Connexions à la plateforme pédagogique dans la semaine |
| devoirs_rendus | Devoirs rendus dans la semaine (0 – 2) |
| note_moyenne | Moyenne des évaluations de la semaine (/20) ; vide les semaines sans évaluation |
| absences | Nombre de séances manquées dans la semaine (0 – 20) |

### tutorat
| Variable | Description |
|---|---|
| semaine_debut | Semaine de la première séance de tutorat |
| nb_seances | Nombre total de séances suivies |
| type_tuteur | pair (étudiant avancé) ou enseignant |
| motif_orientation | notes faibles, absences répétées, signalement enseignant, demande personnelle |

Un étudiant absent de cette table n'a jamais été tutoré.

### messages
| Variable | Description |
|---|---|
| id_message | Identifiant du message |
| semaine | Semaine d'envoi |
| canal | forum ou formulaire de suivi |
| texte | Texte libre rédigé par l'étudiant |

Les messages doivent être **pseudonymisés** avant tout traitement par un LLM.

## Attendu minimal du nettoyage

1. Un script (ou notebook) qui passe de `data/raw/` à `data/processed/` sans intervention manuelle.
2. Un **journal de nettoyage** (`docs/journal_nettoyage.md`) : pour chaque anomalie trouvée → table, description, nombre de lignes concernées, traitement appliqué, justification.
3. Les tables nettoyées + une table d'analyse `base_survie.csv` (une ligne par étudiant : T, E, covariables, tutorat, semaine de début du tutorat).
4. Au moins 5 tests automatiques vérifiant les règles de qualité (ex. identifiants uniques, semaines dans [1 ; 30], notes dans [0 ; 20]).
