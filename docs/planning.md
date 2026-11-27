# Planning du projet — version 4 (27/11/2026)

**Pourquoi une version 4.** Des imprévus ont arrêté le travail du mercredi 25/11 après-midi au vendredi 27/11. Le dernier commit date du 25/11 à 11 h 49 : le code était fini, gel des fonctionnalités tenu, mais les documents L3 à L7 n'étaient pas déposés le 27/11 à 18 h. Le rendu est désormais fixé au **dimanche 29/11 à 18 h** (nouvelle échéance annoncée par Saliou le 27/11). L'objectif est que tout soit poussé à **15 h**, pour garder 3 h de marge. La soutenance reste prévue le **lundi 30/11**.

**État au 27/11.**
- **Terminé :** le code, les notebooks, les tests (291) et le tableau de bord (F1 à F7), ainsi que LL-02 (prompt v2 évalué) et DB-01.
- **Abandonné au gel du 25/11 :** SV-05 (F8, priorité Could), selon la règle « les Could d'abord ».

## Ce qui reste à faire

| # | Tâche | Livrable | Qui | Quand |
|---|---|---|---|---|
| 1 | DO-02 : rapport technique (sections 5 à 9, résumé, annexes, figures, lien du dépôt), relecture, export PDF de 15 à 20 pages | L3 | pilotage rédige ; Saliou relit et exporte | samedi 28/11 |
| 2 | DO-03 : note de synthèse de 2 pages, lien du dépôt en page 1, export PDF | L4 | pilotage rédige ; Saliou relit et exporte | samedi 28/11 au soir |
| 3 | DO-01 : README final (liens vers le rapport et la note, déclaration d'usage de l'IA), test sur un clone neuf | L1 | exécution (consigne C18) | samedi 28/11 au soir |
| 4 | DO-04 : vidéo de 3 minutes du tableau de bord (fichier de 50 Mo au plus, sinon lien dans le README) | L5 | Saliou | samedi 28/11 après-midi |
| 5 | DO-04 : support de soutenance, en PDF ou PPTX | L7 | pilotage rédige ; Saliou relit | dimanche 29/11 au matin |
| 6 | GP-06 : dossier de gestion de projet (temps réel de chaque tâche, journal de bord du 24 au 29/11, burndown et revue / rétrospective du sprint 2, registre des risques, tableau estimation / temps réel, bilan personnel), en PDF avec l'export du Kanban | L6 | Saliou, sur des brouillons du pilotage | samedi et dimanche au matin |
| 7 | R04 : relecture finale avant le dépôt | — | session de relecture | dimanche 29/11 au matin |
| 8 | Dépôt final : tout dans `docs/`, push, capture du Kanban | — | Saliou | dimanche 29/11, 15 h |
| 9 | Préparation de la soutenance : explication de l'application (étapes 3 à 7), puis une répétition | — | Saliou, avec le pilotage | dimanche 29/11 au soir |

## Écarts assumés
- La capture du Kanban du 27/11 sera faite le 27 au soir ou le 28 ; les captures du 13 et du 17/11 manquent (projet démarré le 16, premier Kanban le 18). Le dossier L6 le dira tel quel.
- Le temps réel de chaque tâche sera reconstitué par Saliou à partir du journal de bord ; le dossier le signalera.

## Historique — version 3 (23/11/2026)

**Référence du projet.** Le planning du cahier des charges sert d'inspiration, pas de fil conducteur (décision D-40) ; ses **exigences notées** restent obligatoires : captures du Kanban (24/11 et 27/11), revue et rétrospective de chaque sprint, livrables L1 à L7 déposés dans `docs/`, rendu le **vendredi 27/11 à 18 h** (visé : 15 h). Soutenance le **lundi 30/11** (15 min de présentation, 10 min de questions), date donnée par l'enseignant au point d'étape M2.

**Pourquoi une version 3.** Le sprint 1 a été clos le 23/11 par sa revue (GP-04), et le sprint 2 est planifié en GP-05 (`docs/gestion_projet/sprint2_planification.md`). Depuis la version 2, l'effet causal (M3) a été obtenu un jour en avance, le point d'étape M2 a eu lieu et la date de soutenance est connue.

## Organisation du travail

Inchangée (voir la version 2 ci-dessous) : Saliou décide et valide ; la session de pilotage rédige et teste les consignes, vérifie les résultats et rédige les brouillons de documents ; la session d'exécution code ; la session de relecture relit aux points de contrôle R03 (sécurité du LLM) et R04 (relecture finale).

## Planning journalier

Heures de Saliou : celles du lundi 23/11 sont celles qu'il a annoncées ; celles du mardi au vendredi reprennent la version 2, **à confirmer**.

| Jour | Heures | Tâches | Jalon / contrôle |
|---|---|---|---|
| Lun. 23/11 | 8 (10 h-16 h, 22 h-0 h) | Matin (fait) : point d'étape M2 ; C13 (LL-01 : entrées, prompt v1 et contrôles des fiches) ; brouillon de GP-04. Après-midi : relecture R03 (sécurité du LLM) ; GP-05 (ce planning). Soir : premier appel réel (`--tester`), génération des 54 fiches et corrections de R03 (C14) ; mesure de la durée de `run_all.py` ; journal de bord du 19 au 23/11. | M2 fait ; M3 effet causal fait (nuit du 22 au 23/11, un jour d'avance) |
| Mar. 24/11 | 5 | Capture du Kanban (date imposée). LL-02 : Saliou note 20 fiches, prompt v2 si besoin. DB-01 : consigne et exécution du tableau de bord. DO-02 : plan du rapport, sections contexte, données et nettoyage. | |
| Mer. 25/11 | 4,5 | Fin et vérification de DB-01 ; notebook 06 complété (fiches et évaluation) ; SV-05 (Could) seulement si DB-01 est vérifié. DO-02 : survie, ML, causal. | **Gel des fonctionnalités** (soir) |
| Jeu. 26/11 | 4 | Relecture finale R04 et corrections ; DO-02 : LLM, tableau de bord, limites, éthique, export PDF ; DO-03 (note de synthèse) ; DO-04 (support de soutenance, vidéo de 3 min). | Rapport, note et support finalisés |
| Ven. 27/11 | 2,5 (jusqu'à 15 h) | DO-01 (README final, test sur un clone neuf) ; GP-06 (dossier de gestion de projet, export du Kanban, revue et rétrospective finales) ; capture du Kanban (date imposée) ; vérification finale. | **M4 rendu visé 15 h** (limite 18 h) |
| Sam. 28 et dim. 29/11 | à fixer | Répétition chronométrée de la soutenance, questions probables, relecture du code clé. Plus aucun commit après le rendu. | |
| Lun. 30/11 | | Soutenance (15 min + 10 min de questions). | |

Charge restante réestimée au 23/11 (15 h) : 19,5 h, dont 1,5 h pour SV-05 (Could), pour environ 19 h disponibles jusqu'au rendu. Pas de marge : SV-05 n'est faite que si le tableau de bord est vérifié mercredi, et les brouillons de la session de pilotage sont indispensables pour tenir le rapport, la note et le support.

## Règles

- Au moins un commit par jour, avec l'identifiant de la tâche dans le message.
- Une entrée du journal de bord chaque soir, avec les heures réelles.
- Au plus 2 cartes « En cours » sur le Kanban ; une carte change de colonne dès que la tâche change d'état.
- En cas de retard : on abandonne d'abord SV-05 (Could), puis le prompt v2 (LL-02) et les options du tableau de bord (Should), jamais les Must (DO-01 à DO-04, GP-06).

## Écarts assumés par rapport au cahier des charges

- Démarrage effectif le 16/11 (J2) au lieu du 13/11 ; Kanban créé le 18/11 (pas de captures au 13/11 ni au 17/11).
- Point d'étape avec l'enseignant déplacé au lundi 23/11 (à la demande de l'enseignant).
- Sprint 1 clos le 23/11, deux jours après la fin prévue au planning v2 ; tâches du sprint 2 tirées en avance le 22/11 (SV-03, SV-04, CA-02 à CA-05).
- Soutenance le 30/11, après le rendu : le support (L7) est déposé avec le dossier le 27/11.

---

## Historique — version 2 (19/11/2026)

Version 2, remplacée le 23/11 par la version 3 ci-dessus.

**Référence du projet.** Le planning du cahier des charges sert d'inspiration, pas de fil conducteur (décision D-40) ; ses **exigences notées** restent obligatoires : captures du Kanban (19/11, 24/11, 27/11), revue et rétrospective de chaque sprint, livrables, rendu le **vendredi 27/11 à 18 h** (visé : 15 h).

## Organisation du travail

- **Saliou** : product owner et seul décideur ; valide chaque règle et chaque choix de méthode ; tient le Kanban et le journal de bord ; doit pouvoir expliquer chaque ligne en soutenance.
- **Session de pilotage** (chat Claude) : rédige et teste les consignes (`docs/consignes/`), vérifie les résultats, explique le code, rédige les brouillons de documents que Saliou relit.
- **Session d'exécution** (Claude Code) : écrit le code à partir des consignes.
- **Session de relecture** (Claude Code, clone séparé, décision D-41) : relit consignes, code, tests et sécurité aux points de contrôle R01 à R04 ; ne modifie rien, rédige des rapports dans `docs/revues/`.

## Planning journalier (même rythme qu'au 18/11)

| Jour | Heures | Tâches | Jalon / contrôle |
|---|---|---|---|
| Mer. 18/11 | 6 | GP-01 à GP-03, DA-01 à DA-03 | Kanban créé (fait) |
| Jeu. 19/11 | 6 | DA-04 à DA-07 | M1 données propres et base_survie (fait, 1 jour d'avance sur la version 1) |
| Ven. 20/11 | 6 | Relecture R01 ; DA-08, SV-01, CA-01 | fin du contenu du sprint 1 |
| Sam. 21/11 | 5 | GP-04 (revue, rétrospective et burndown du sprint 1), GP-05 (planification du sprint 2), SV-02 | début du sprint 2 |
| Dim. 22/11 | 4 | SV-03, SV-04 | |
| Lun. 23/11 | 6 | Point d'étape avec l'enseignant (Cox + DAG) ; relecture R02 de la spécification causale ; CA-02, CA-03 ; DO-02 (plan, données, méthodes) | M2 |
| Mar. 24/11 | 5 | CA-04, CA-05 ; DO-02 (résultats de survie) ; capture du Kanban | M3 effet causal |
| Mer. 25/11 | 4,5 | Relecture R03 (sécurité LLM) ; LL-01, LL-02, DB-01 | |
| Jeu. 26/11 | 4 | Fin de DB-01 ; DO-04 (support, vidéo) ; DO-02 (causal, limites) ; relecture finale R04 | gel des fonctionnalités |
| Ven. 27/11 | 2,5 | DO-01 (README, test sur un clone neuf), DO-03 (note de synthèse), GP-06 ; capture du Kanban | rendu visé 15 h |

Charge restante estimée au 19/11 : environ 36 h pour environ 37 h disponibles. La marge vient de SV-05 (« Could », fait seulement s'il reste du temps) et des brouillons rédigés par la session de pilotage.

## Règles

- Au moins un commit par jour, avec l'identifiant de la tâche dans le message.
- Une entrée du journal de bord par jour ouvré.
- En cas de retard : on abandonne d'abord SV-05 (Could), puis LL/DB (Should), jamais les Must.

## Écarts assumés par rapport au cahier des charges

- Démarrage effectif le 16/11 (J2) au lieu du 13/11.
- Kanban créé le 18/11 : pas de captures au 13/11 ni au 17/11.
- Point d'étape avec l'enseignant déplacé au lundi 23/11 (à la demande de l'enseignant).

---

## Historique — version 1 (18/11/2026)

Version 1, remplacée le 19/11 par la version 2 ci-dessus.

Le projet a réellement démarré le 16/11 (création du dépôt). Le planning initial du cahier des charges
(démarrage 13/11) a été replanifié le 18/11 sur la période restante, jusqu'au rendu du **vendredi 27/11, 18 h**.

## Organisation du travail

- **Session Claude Code (exécution)** : écrit le code à partir de consignes écrites, versionnées dans `docs/consignes/`.
- **Session de chat Claude (pilotage)** : rédige les consignes, vérifie les résultats, explique le code à l'étudiant.
- **Étudiant (Saliou)** : product owner et décideur ; valide chaque règle de nettoyage et chaque choix de méthode,
  tient le Kanban et le journal de bord, doit pouvoir expliquer chaque ligne en soutenance.

Ressources réutilisées des projets précédents : structure du pipeline de nettoyage (règles numérotées, contrôles,
tests pytest), registre des décisions, garde-fous LLM (pseudonymisation, chiffres injectés par gabarit), structure Streamlit.

## Planning journalier

| Jour | Heures | Tâches | Jalon |
|---|---|---|---|
| Mer. 18/11 | 6 | GP-02, GP-03, DA-01, début DA-02/03 | Kanban créé |
| Jeu. 19/11 | 6 | DA-02 à DA-06 | |
| Ven. 20/11 | 6 | DA-07, DA-08, SV-01, GP-04, GP-05 | M1 données propres, fin sprint 1 |
| Sam. 21/11 | 5 | SV-02, CA-01 | |
| Dim. 22/11 | 4 | SV-03, SV-04 | |
| Lun. 23/11 | 6 | Point d'étape enseignant, CA-02, CA-03, début CA-04, début DO-02 | M2 point d'étape (Cox + DAG) |
| Mar. 24/11 | 5 | CA-04, CA-05 | M3 effet causal |
| Mer. 25/11 | 4,5 | LL-01, LL-02, DB-01 | Gel des fonctionnalités |
| Jeu. 26/11 | 4 | DO-01, DO-03, DO-04, SV-05 (si temps) | |
| Ven. 27/11 | 2,5 | GP-06, vérification finale | M4 rendu visé 15 h (limite 18 h) |

Total prévu : 49 h (backlog du cahier des charges : 63,5 h, dont GP-01 fait le 16/11).

## Règles

- Au moins un commit par jour, avec l'identifiant de la tâche dans le message.
- Une entrée du journal de bord par jour ouvré.
- En cas de retard : on abandonne d'abord SV-05 (Could), puis LL/DB (Should), jamais les Must.

## Écarts assumés par rapport au cahier des charges

- Kanban créé le 18/11 : pas de captures au 13/11 ni au 17/11. Captures prévues les 19, 20, 24 et 27/11.
- Point d'étape avec l'enseignant déplacé au lundi 23/11 (à la demande de l'enseignant) : il portera sur le Cox et le DAG, comme prévu en M2.
