# Sprint 2 — planification (GP-05)

> **Brouillon** rédigé par la session de pilotage le 23/11/2026 (15 h), à valider par Saliou, en particulier les heures disponibles du mardi au vendredi et les réestimations.

## 1. Cadre

| | Cahier des charges | Réel |
|---|---|---|
| Objectif | « Prédire, prouver, restituer » : modèle ML de survie, effet causal du tutorat, fiches LLM, tableau de bord, rapport, note, support | idem |
| Dates | ven. 20/11 → ven. 27/11 (J6 → J11) | commencé de fait le dim. 22/11 (tâches tirées en avance), planifié le lun. 23/11 après la revue du sprint 1 ; fin le ven. 27/11 (rendu) |
| Charge | 16 tâches, 33 h | 6 tâches terminées (14 h) au 23/11 ; reste 19 h d'estimation initiale, 19,5 h réestimées |
| Capacité | | environ 19 h de Saliou du lun. 23/11 (15 h) au ven. 27/11 (15 h) ; heures du mardi au vendredi **à confirmer** |

## 2. Backlog du sprint 2, réestimé

La réestimation porte sur le temps de Saliou (relire, vérifier, décider, s'approprier), pas sur le temps des sessions Claude.

| ID | Tâche | Prio. | Estim. initiale (h) | Statut au 23/11 (15 h) | Reste réestimé (h) | Jour cible (planning v3) |
|---|---|---|---:|---|---:|---|
| SV-03 | Modèle ML de survie, validation 2024 → 2025 | Must | 3 | Terminé (22/11) | 0 | — |
| SV-04 | Comparaison Cox / ML, explication du modèle | Must | 2 | Terminé (22/11) | 0 | — |
| CA-02 | Score de propension, support commun | Must | 2 | Terminé (22/11) | 0 | — |
| CA-03 | Pondération, équilibre, love plot | Must | 2 | Terminé (22/11) | 0 | — |
| CA-04 | Effet du tutorat, bootstrap | Must | 3 | Terminé (22/11) | 0 | — |
| CA-05 | Sensibilité, E-value, Cox dépendant du temps | Must | 2 | Terminé (23/11, 0 h 05) | 0 | — |
| GP-05 | Planifier le sprint 2 | Must | 0,5 | En cours | 0,5 | lun. 23/11 |
| LL-01 | Fiches d'alerte par LLM | Should | 2,5 | En cours : code, prompt et entrées faits (C13) ; génération après R03 | 1 | lun. 23/11 (soir) |
| LL-02 | Évaluer 20 fiches, prompt v2 si besoin | Should | 1 | À faire | 1 | mar. 24/11 |
| DB-01 | Tableau de bord | Should | 3 | À faire | 2,5 | mar. 24 → mer. 25/11 |
| SV-05 | Équité et effet du tutorat selon la bourse (bonus) | Could | 1,5 | À faire, seulement si DB-01 est vérifié | 1,5 | mer. 25/11 |
| DO-01 | README complet, test sur un clone neuf | Must | 1,5 | À faire (README déjà tenu à jour au fil des tâches) | 1 | ven. 27/11 |
| DO-02 | Rapport technique (PDF, 15 à 20 pages) | Must | 4 | À faire | 5 | mar. 24 → jeu. 26/11 |
| DO-03 | Note de synthèse (2 pages, lien du dépôt) | Must | 1,5 | À faire | 1,5 | jeu. 26/11 |
| DO-04 | Support de soutenance, vidéo de 3 min | Must | 2 | À faire | 3 | jeu. 26/11 |
| GP-06 | Dossier de gestion de projet, revue et rétrospective finales | Must | 1,5 | À faire | 2 | ven. 27/11 |
| **Total** | | | **33** | 14 h terminées | **19,5** | |

**Pourquoi ces réestimations :**
- LL-01 (2,5 → 1 h restante) : le code est écrit et vérifié ; il reste le premier appel, la génération et la vérification des 54 fiches.
- DB-01 (3 → 2,5 h) et DO-01 (1,5 → 1 h) : le code est écrit par la session d'exécution, et le README est déjà à jour pour les parties faites.
- DO-02 (4 → 5 h), DO-04 (2 → 3 h) et GP-06 (1,5 → 2 h) : 15 à 20 pages à relire, corriger et assumer en soutenance, une vidéo à enregistrer, un dossier de gestion de projet à compiler en PDF ; c'est du temps de Saliou que les brouillons ne remplacent pas.

## 3. Dépendances et ordre

1. R03 (relecture de sécurité) → premier appel réel → génération des 54 fiches → LL-02 (évaluation de 20 fiches) → notebook 06 complété.
2. DB-01 peut commencer avant la génération (il affiche « aucune fiche » sans cache) ; la vidéo de DO-04 attend que DB-01 soit vérifié.
3. Gel des fonctionnalités le mercredi 25/11 au soir : après, on ne corrige que des erreurs ; les chiffres du rapport sont alors définitifs.
4. R04 (relecture finale) le jeudi 26/11, sur le dépôt complet ; DO-03 reprend les chiffres de DO-02.

## 4. Règles du sprint

- Au plus 2 cartes « En cours » (limite WIP fixée en GP-02).
- Captures du Kanban le mardi 24/11 et le vendredi 27/11 (dates imposées).
- Journal de bord chaque soir, avec les heures réelles.
- En cas de retard : SV-05 d'abord, puis le prompt v2 et les options du tableau de bord ; jamais DO-01 à DO-04 ni GP-06.
- Revue et rétrospective du sprint 2 dans GP-06 (vendredi 27/11), avec le burndown du sprint 2.
