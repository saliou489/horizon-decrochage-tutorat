# Registre des risques

Gabarit de l'annexe D du cahier des charges. R1 à R6 reprennent les risques du §14 du cahier ; R7 à R12 sont propres au projet.
Mis à jour le 19/11/2026. Statuts : **ouvert** (à surveiller), **réduit** (mesure en place), **survenu** (s'est produit), **clos**.

| ID | Risque | Prob. | Impact | Mesure | Statut |
|---|---|---|---|---|---|
| R1 | Nettoyage trop long, analyses commencées en retard | Élevée | Fort | Traiter d'abord les anomalies qui faussent T, E et le tutorat ; chaque consigne testée par un prototype avant exécution ; décisions tranchées table par table. | **Réduit** — nettoyage des 5 tables terminé le 19/11 ; M1 atteint avec 2 à 3 jours de retard sur le cahier (17/11), en avance sur le planning replanifié (20/11). |
| R2 | Confusion entre corrélation et causalité | Élevée | Fort | Vocabulaire imposé (« associé à » hors partie causale, CLAUDE.md §6) ; conclusions relues avec le DAG ; spécification causale fixée avant le calcul de l'effet. | Ouvert — à surveiller en SV et CA. |
| R3 | Biais du temps immortel non traité | Élevée | Fort | CA-01 en sprint 1 ; tutorat compté seulement s'il commence avant T (D-37) ; comparaison naïve tutorés / non tutorés interdite hors partie causale. | Ouvert — traitement en CA-01. |
| R4 | Hallucinations du LLM dans les fiches | Moyenne | Moyen | Chiffres injectés dans le prompt ; contrôle automatique que chaque nombre de la fiche figure dans l'entrée ; évaluation de 20 fiches (LL-02). | Ouvert — LL-01. |
| R5 | Fuite de données personnelles vers une API | Moyenne | Fort | Pseudonymisation avant tout usage (DA-05, D-28 : 0 donnée personnelle restante) ; liste fermée de champs envoyés au LLM, sans identifiant ; choix du modèle en LL-01. | Réduit. |
| R6 | Rédaction repoussée à la fin | Élevée | Moyen | Matière rédigée au fil de l'eau (registre des décisions, journal de nettoyage, journal de bord) ; plan du rapport dès le 21/11 ; rédaction continue à partir du 23/11. | Ouvert. |
| R7 | Démarrage tardif (J2 au lieu de J1) et retard sur le planning du cahier | Survenu | Moyen | Replanification (D-02), week-end travaillé, avance prise sur le planning replanifié. | Survenu — environ 14 h de retard le 18/11, 11 à 12 h le 19/11, en rattrapage. |
| R8 | Erreur d'un assistant IA (code ou recommandation) non détectée | Moyenne | Fort | Consignes écrites et versionnées ; prototype indépendant ; vérification cellule par cellule du résultat ; écarts signalés dans chaque compte rendu ; décisions validées par Saliou. | Réduit — 3 erreurs survenues et détectées : version de Python (D-05), ETU-09 (C05), conséquence de D-14 (corrigée par D-33). |
| R9 | Accès réseau à GitHub bloqué sur le réseau local | Moyenne | Moyen | Cloudflare WARP ; travail poussé sur GitHub chaque jour. | Réduit. |
| R10 | Contraintes du poste de travail (droits limités, Python récent) | Faible | Moyen | Dépôt dans le dossier utilisateur (D-04) ; Python 3.12 ou plus exigé (D-05). | Clos. |
| R11 | Perte du travail local (panne du PC) | Faible | Fort | Tout le travail poussé sur GitHub au moins une fois par jour. | Réduit. |
| R12 | Exigences de gestion de projet non tenues (captures du Kanban, journal de bord) | Moyenne | Moyen | Captures aux dates imposées, journal de bord chaque soir, Kanban mis à jour à chaque tâche. | Survenu — captures du 13/11 et du 17/11 manquantes (écart documenté dans `docs/planning.md`) ; captures 19, 24 et 27/11 à faire. |
