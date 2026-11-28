# Temps réel par tâche — brouillon à valider (GP-06)

Brouillon préparé par la session de pilotage le 28/11, à la demande de Saliou. **Chaque valeur est à vérifier et corriger par Saliou avant d'entrer dans le dossier L6.**

## Méthode de reconstitution

- Heures du jour : les créneaux annoncés au planning (à une heure près, selon Saliou), corrigés le 28/11 avec Saliou : 21/11 sans travail (constat de D-45), 22/11 journée complète (retenue à 10 h), 24/11 6 à 7 h (6,5 h), 25/11 3,5 h, 26/11 sans travail ; 16 et 17/11 non relevés et non comptés.
- Répartition : les heures d'un jour sont partagées entre les tâches qui ont eu des commits ce jour-là, au prorata du nombre de commits (un commit qui cite deux tâches compte pour moitié à chacune). Un commit passé avant 4 h du matin est rattaché à la veille.
- Limites : un nombre de commits ne mesure pas l'effort ; le temps sans commit (lecture, décisions, vérification) est réparti sur les tâches du jour ; les commits de la session de pilotage (consignes) comptent comme du temps de la tâche.

## Heures retenues par jour

| Jour | Créneau annoncé | Heures retenues | Tâches du jour (commits) | À confirmer |
|---|---|---|---|---|
| 16/11 | — | ? | GP-01 | non relevé, et Saliou ne s'en souvient plus : non compté (seule GP-01 a des commits ce jour-là) |
| 17/11 | — | ? | — | non relevé, peu de temps (journal) ; aucun commit, donc sans effet sur le temps par tâche |
| 18/11 | 6 h | 6,0 h | DA-01, DA-02, DA-03, GP-01, GP-02, GP-03 |  |
| 19/11 | 6 h | 6,0 h | DA-04, DA-05, DA-06, DA-07, GP-03 |  |
| 20/11 | 6 h | 6,0 h | DA-06, DA-07, DA-08, DO-01 |  |
| 21/11 | 5 h | 0,0 h | — | aucun travail, constat de D-45 (validée par Saliou le 22/11) |
| 22/11 | 4 h, puis journée complète (D-45) | 10,0 h | CA-01, CA-02, CA-03, CA-04, CA-05, DA-03, DA-07, SV-01, SV-02, SV-03, SV-04 | journée complète selon Saliou, retenue à 10 h ; commits de 15 h 24 à 0 h 05 |
| 23/11 | 8 h | 8,0 h | CA-05, GP-04, GP-05, LL-01, LL-02, SV-04 |  |
| 24/11 | 5 h | 6,5 h | DB-01, GP-04, GP-05, LL-02 | 6 à 7 h selon Saliou |
| 25/11 | 4,5 h | 3,5 h | DB-01, LL-02 | imprévus dès l'après-midi : créneau − 1 h, confirmé par Saliou |
| 26/11 | 4 h | 0,0 h | — | imprévus : aucun travail |
| 27/11 | 2,5 h | 0,5 h | GP-06 | imprévus ; le soir, replanification et captures |
| 28/11 et 29/11 | — | à noter | DO-01 à DO-04, GP-06 | à remplir le 29/11 |

## Temps par tâche

| ID | Tâche | Estimation (h) | Temps reconstitué (h) | Écart (h) | Jours |
|---|---|---|---|---|---|
| GP-01 | Créer le dépôt GitHub, la structure de dossiers et l'environnement | 1,5 | 1,3 | −0,2 | 16/11, 18/11 |
| GP-02 | Créer le Kanban (GitHub Projects), saisir le backlog, fixer la limite WIP | 1,0 | 0,6 | −0,4 | 18/11 |
| GP-03 | Planifier le sprint 1, initialiser le registre des risques et le journal de bord | 1,0 | 2,7 | +1,7 | 18/11, 19/11 |
| DA-01 | Audit qualité des 5 fichiers bruts : profilage, inventaire des anomalies | 3,0 | 0,5 | −2,5 | 18/11 |
| DA-02 | Nettoyer « etudiants » : doublons, modalités, valeurs aberrantes, manquants | 3,0 | 1,3 | −1,7 | 18/11 |
| DA-03 | Nettoyer « inscriptions » : dates, statuts, cohérence avec « etudiants » | 2,5 | 1,7 | −0,8 | 18/11, 22/11 |
| DA-04 | Nettoyer « activite_hebdo » et « tutorat » : doublons, bornes, incohérences temporelles | 2,5 | 1,6 | −0,9 | 19/11 |
| DA-05 | Nettoyer et pseudonymiser « messages » (données personnelles, encodage) | 1,0 | 0,6 | −0,4 | 19/11 |
| DA-06 | Rédiger le journal de nettoyage et écrire les tests automatiques (≥ 5) | 2,0 | 1,6 | −0,4 | 19/11, 20/11 |
| DA-07 | Construire T et E (règle des 4 semaines), base_survie.csv et format période-personne | 3,0 | 4,1 | +1,1 | 19/11, 20/11, 22/11 |
| DA-08 | Analyse exploratoire : profils, taux de censure, distribution des durées | 2,0 | 2,0 | +0,0 | 20/11 |
| SV-01 | Kaplan-Meier global et par sous-groupes, tests du log-rank, semaines critiques | 2,0 | 1,2 | −0,8 | 22/11 |
| GP-04 | Revue et rétrospective du sprint 1, burndown, point d'étape avec l'enseignant | 1,0 | 0,9 | −0,1 | 23/11, 24/11 |
| GP-05 | Planifier le sprint 2 (réestimer, reprioriser le backlog) | 0,5 | 0,9 | +0,4 | 23/11, 24/11 |
| SV-02 | Modèle de Cox multivarié, vérification de la proportionnalité, interprétation | 3,0 | 0,7 | −2,3 | 22/11 |
| CA-01 | Construire et justifier le DAG ; analyser le moment d'entrée en tutorat ; choisir l'approche anti-temps immortel | 2,0 | 1,0 | −1,0 | 22/11 |
| SV-03 | Modèle ML de survie avec validation temporelle (cohorte 2024 → 2025) | 3,0 | 1,7 | −1,3 | 22/11 |
| SV-04 | Comparer Cox / ML (C-index, Brier intégré, calibration) et expliquer le modèle | 2,0 | 1,5 | −0,5 | 22/11, 23/11 |
| CA-02 | Score de propension et contrôle du support commun | 2,0 | 0,5 | −1,5 | 22/11 |
| CA-03 | Pondération IPTW (ou appariement) et tableau d'équilibre (SMD avant / après) | 2,0 | 1,2 | −0,8 | 22/11 |
| CA-04 | Estimer l'effet : HR pondéré, KM pondérées, différence de RMST, IC par bootstrap | 3,0 | 1,4 | −1,6 | 22/11 |
| CA-05 | Sensibilité : E-value, spécification alternative, règle des 3 et 5 semaines | 2,0 | 1,0 | −1,0 | 22/11, 23/11 |
| LL-01 | Prompt et pipeline de génération des fiches d'alerte à partir des sorties du modèle | 2,5 | 5,4 | +2,9 | 23/11 |
| LL-02 | Évaluer 20 fiches (exactitude, ton, stigmatisation) et corriger le prompt | 1,0 | 7,0 | +6,0 | 23/11, 24/11, 25/11 |
| DB-01 | Tableau de bord : liste à risque, courbe individuelle, fiche LLM, page tutorat | 3,0 | 2,7 | −0,3 | 24/11, 25/11 |
| SV-05 | Équité (genre, boursier) et effet du tutorat selon le statut de boursier | 1,5 | 0 | — | abandonnée au gel du 25/11 |
| DO-01 | README complet, reproductibilité de bout en bout, nettoyage du dépôt | 1,5 | 1,0 h jusqu'ici, à compléter le 29/11 | — | en cours |
| DO-02 | Rédiger le rapport technique (rédaction continue dès J6) | 4,0 | à compléter le 29/11 | — | en cours |
| DO-03 | Rédiger la note de synthèse de 2 pages, avec le lien du dépôt GitHub | 1,5 | à compléter le 29/11 | — | en cours |
| DO-04 | Préparer le support de soutenance et enregistrer la vidéo de démonstration | 2,0 | à compléter le 29/11 | — | en cours |
| GP-06 | Compiler le dossier de gestion de projet ; revue et rétrospective finales | 1,5 | 0,5 h jusqu'ici, à compléter le 29/11 | — | en cours |

Sur les 25 tâches terminées : 51,5 h estimées, 45,0 h reconstituées (87 % de l'estimation).

GP-01 : le temps du 16/11 (création du dépôt) n'est pas compté, faute de relevé.

## Écarts par famille de tâches

| Famille | Tâches terminées | Estimation (h) | Temps reconstitué (h) | Temps / estimation |
|---|---|---|---|---|
| Gestion de projet (GP) | 5 | 5,0 | 6,4 | 127 % |
| Données et nettoyage (DA) | 8 | 19,0 | 13,4 | 70 % |
| Survie et ML (SV) | 4 | 10,0 | 5,1 | 51 % |
| Causal (CA) | 5 | 11,0 | 5,1 | 46 % |
| LLM (LL) | 2 | 3,5 | 12,4 | 355 % |
| Tableau de bord (DB) | 1 | 3,0 | 2,7 | 89 % |

## Analyse des écarts (brouillon, à reprendre par Saliou)

- **Données, survie et causal** : environ 60 % du temps estimé. Les estimations du cahier supposent un étudiant qui code seul. Ici, la session d'exécution a écrit le code à partir de consignes testées avant par la session de pilotage ; le temps de Saliou est allé aux décisions (D-05 à D-64), aux vérifications et à la compréhension du code. Ce gain se paie plus tard : il faut du temps pour pouvoir expliquer chaque ligne en soutenance.
- **LLM** : environ 3,5 fois l'estimation. Causes : le quota gratuit trop bas du premier modèle (changement de modèle, D-65), les refus et les pannes de l'API (attentes, reprises), la relecture de sécurité R03, et surtout deux versions du prompt avec deux notations humaines de 20 fiches (la version 2 a été décidée après la première notation, D-69). L'estimation ne prévoyait ni la dépendance à un service extérieur, ni une deuxième itération.
- **Gestion de projet** : un peu au-dessus de l'estimation, à cause de la replanification après le démarrage tardif (D-02) et de la mise en place du cadre de travail avec les assistants IA (CLAUDE.md, consignes, registre des décisions).
- **Tableau de bord** : proche de l'estimation.
- **Bilan** : les estimations n'ont pas été le problème principal (87 % du temps estimé sur les tâches terminées). Le retard vient de la disponibilité : aucun travail le 21/11, puis environ 7 h de créneaux perdus du 25 au 27/11 à cause des imprévus, d'où le rendu repoussé au 29/11.

## Points à vérifier par Saliou

1. **22/11** : « toute la journée » est retenue à 10 h (premier commit à 15 h 24, après la discussion des décisions D-45 à D-51 ; dernier à 0 h 05). À changer si c'était plutôt 8 ou 12 h.
2. **Valeurs par tâche** : elles suivent le nombre de commits, qui ne mesure pas l'effort (exemples : l'audit DA-01 à 0,5 h, le Cox SV-02 à 0,7 h). Une valeur qui te semble fausse peut être corrigée, à condition de reprendre les heures sur une autre tâche du même jour, pour garder le total du jour.
3. **28 et 29/11** : noter les heures réelles chaque soir pour DO-01 à DO-04 et GP-06.
4. **Kanban** : reporter le temps réel sur chaque carte avant l'export (le §12.1 du cahier demande le temps réel de chaque tâche dans l'export de l'outil).

