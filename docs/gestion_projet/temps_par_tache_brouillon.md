# Temps réel par tâche — brouillon à valider (GP-06)

Brouillon préparé par la session de pilotage le 28/11, à la demande de Saliou. **Chaque valeur est à vérifier et corriger par Saliou avant d'entrer dans le dossier L6.**

## Méthode de reconstitution

- Heures du jour : les créneaux annoncés au planning (à une heure près, selon Saliou), mis à 0 les jours sans travail d'après le journal de bord.
- Répartition : les heures d'un jour sont partagées entre les tâches qui ont eu des commits ce jour-là, au prorata du nombre de commits (un commit qui cite deux tâches compte pour moitié à chacune). Un commit passé avant 4 h du matin est rattaché à la veille.
- Limites : un nombre de commits ne mesure pas l'effort ; le temps sans commit (lecture, décisions, vérification) est réparti sur les tâches du jour ; les commits de la session de pilotage (consignes) comptent comme du temps de la tâche.

## Heures retenues par jour

| Jour | Créneau annoncé | Heures retenues | Tâches du jour (commits) | À confirmer |
|---|---|---|---|---|
| 16/11 | — | ? | GP-01 | non relevé : à indiquer |
| 17/11 | — | ? | — | non relevé, peu de temps (journal) : à indiquer ; aucun commit |
| 18/11 | 6 h | 6,0 h | DA-01, DA-02, DA-03, GP-01, GP-02, GP-03 |  |
| 19/11 | 6 h | 6,0 h | DA-04, DA-05, DA-06, DA-07, GP-03 |  |
| 20/11 | 6 h | 6,0 h | DA-06, DA-07, DA-08, DO-01 |  |
| 21/11 | 5 h | 0,0 h | — | aucun commit après 0 h 12 : 0 h proposé, à confirmer |
| 22/11 | 4 h | 4,0 h | CA-01, CA-02, CA-03, CA-04, CA-05, DA-03, DA-07, SV-01, SV-02, SV-03, SV-04 | journée bien plus chargée que 4 h (revue du sprint 1) : à corriger |
| 23/11 | 8 h | 8,0 h | CA-05, GP-04, GP-05, LL-01, LL-02, SV-04 |  |
| 24/11 | 5 h | 5,0 h | DB-01, GP-04, GP-05, LL-02 |  |
| 25/11 | 4,5 h | 3,5 h | DB-01, LL-02 | imprévus dès l'après-midi : créneau − 1 h proposé |
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
| DA-03 | Nettoyer « inscriptions » : dates, statuts, cohérence avec « etudiants » | 2,5 | 1,5 | −1,0 | 18/11, 22/11 |
| DA-04 | Nettoyer « activite_hebdo » et « tutorat » : doublons, bornes, incohérences temporelles | 2,5 | 1,6 | −0,9 | 19/11 |
| DA-05 | Nettoyer et pseudonymiser « messages » (données personnelles, encodage) | 1,0 | 0,6 | −0,4 | 19/11 |
| DA-06 | Rédiger le journal de nettoyage et écrire les tests automatiques (≥ 5) | 2,0 | 1,6 | −0,4 | 19/11, 20/11 |
| DA-07 | Construire T et E (règle des 4 semaines), base_survie.csv et format période-personne | 3,0 | 3,8 | +0,8 | 19/11, 20/11, 22/11 |
| DA-08 | Analyse exploratoire : profils, taux de censure, distribution des durées | 2,0 | 2,0 | +0,0 | 20/11 |
| SV-01 | Kaplan-Meier global et par sous-groupes, tests du log-rank, semaines critiques | 2,0 | 0,5 | −1,5 | 22/11 |
| GP-04 | Revue et rétrospective du sprint 1, burndown, point d'étape avec l'enseignant | 1,0 | 0,8 | −0,2 | 23/11, 24/11 |
| GP-05 | Planifier le sprint 2 (réestimer, reprioriser le backlog) | 0,5 | 0,8 | +0,3 | 23/11, 24/11 |
| SV-02 | Modèle de Cox multivarié, vérification de la proportionnalité, interprétation | 3,0 | 0,3 | −2,7 | 22/11 |
| CA-01 | Construire et justifier le DAG ; analyser le moment d'entrée en tutorat ; choisir l'approche anti-temps immortel | 2,0 | 0,4 | −1,6 | 22/11 |
| SV-03 | Modèle ML de survie avec validation temporelle (cohorte 2024 → 2025) | 3,0 | 0,7 | −2,3 | 22/11 |
| SV-04 | Comparer Cox / ML (C-index, Brier intégré, calibration) et expliquer le modèle | 2,0 | 1,0 | −1,0 | 22/11, 23/11 |
| CA-02 | Score de propension et contrôle du support commun | 2,0 | 0,2 | −1,8 | 22/11 |
| CA-03 | Pondération IPTW (ou appariement) et tableau d'équilibre (SMD avant / après) | 2,0 | 0,5 | −1,5 | 22/11 |
| CA-04 | Estimer l'effet : HR pondéré, KM pondérées, différence de RMST, IC par bootstrap | 3,0 | 0,6 | −2,4 | 22/11 |
| CA-05 | Sensibilité : E-value, spécification alternative, règle des 3 et 5 semaines | 2,0 | 0,8 | −1,2 | 22/11, 23/11 |
| LL-01 | Prompt et pipeline de génération des fiches d'alerte à partir des sorties du modèle | 2,5 | 5,4 | +2,9 | 23/11 |
| LL-02 | Évaluer 20 fiches (exactitude, ton, stigmatisation) et corriger le prompt | 1,0 | 5,8 | +4,8 | 23/11, 24/11, 25/11 |
| DB-01 | Tableau de bord : liste à risque, courbe individuelle, fiche LLM, page tutorat | 3,0 | 2,5 | −0,5 | 24/11, 25/11 |
| SV-05 | Équité (genre, boursier) et effet du tutorat selon le statut de boursier | 1,5 | 0 | — | abandonnée au gel du 25/11 |
| DO-01 | README complet, reproductibilité de bout en bout, nettoyage du dépôt | 1,5 | 1,0 h jusqu'ici, à compléter le 29/11 | — | en cours |
| DO-02 | Rédiger le rapport technique (rédaction continue dès J6) | 4,0 | à compléter le 29/11 | — | en cours |
| DO-03 | Rédiger la note de synthèse de 2 pages, avec le lien du dépôt GitHub | 1,5 | à compléter le 29/11 | — | en cours |
| DO-04 | Préparer le support de soutenance et enregistrer la vidéo de démonstration | 2,0 | à compléter le 29/11 | — | en cours |
| GP-06 | Compiler le dossier de gestion de projet ; revue et rétrospective finales | 1,5 | 0,5 h jusqu'ici, à compléter le 29/11 | — | en cours |

Sur les 25 tâches terminées : 51,5 h estimées, 37,5 h reconstituées, avec les heures du 22/11 encore à corriger.

## Points à vérifier par Saliou

1. **22/11** : 4 h réparties sur 11 tâches donnent des temps irréalistes pour SV-01 à SV-04 et CA-01 à CA-05. La revue du sprint 1 dit que la journée a été bien plus chargée : indiquer le vrai nombre d'heures.
2. **LL-02** : 16 commits le 24/11, dont beaucoup de la session de pilotage, gonflent son temps (5,8 h). À réduire si une partie de la journée est allée à DB-01 ou au rapport.
3. **DO-02** : le rapport a commencé le 24/11 dans un document partagé, sans commit : ce temps n'apparaît pas encore. À ajouter.
4. **16, 17 et 21/11** : heures non relevées, ou journée sans travail. À indiquer.
5. **28 et 29/11** : noter les heures réelles chaque soir pour DO-01 à DO-04 et GP-06.

