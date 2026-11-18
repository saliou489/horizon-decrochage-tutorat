# Planning du projet — replanifié le 18/11/2026

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
