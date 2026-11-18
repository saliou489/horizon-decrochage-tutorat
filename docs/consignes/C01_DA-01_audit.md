# Consigne C01 — DA-01 : audit qualité des 5 fichiers bruts

## Contexte
Dépôt `horizon-decrochage-tutorat`. Lis d'abord `docs/cahier_des_charges.pdf` (§4 et §6) et `data/raw/LISEZMOI.md`.
Tâche : **DA-01 uniquement** (audit). **Ne nettoie rien, ne modifie aucun fichier de `data/raw/`.**

## À produire
1. `src/audit.py` : script relançable (`python -m src.audit`), chemins relatifs, aucune valeur codée en dur
   sauf les valeurs attendues du `LISEZMOI.md`. Fonctions courtes et documentées (docstrings en français).
2. `docs/audit_qualite.md` généré par le script : pour chaque table, une section avec
   - structure : séparateur, encodage détecté, noms de colonnes (bruts vs attendus), types, nb de lignes ;
   - un tableau d'anomalies : `# | colonne | anomalie | nb de lignes | 3 exemples`.
3. `requirements.txt` avec les versions installées (pandas, numpy, pytest au minimum).

## Ce qu'il faut chercher (liste non exhaustive, aller plus loin)
- **Structure** : séparateurs, BOM, encodage cassé (mojibake type `Ã©`), espaces dans les en-têtes, colonnes renommées, lignes vides ou décalées.
- **Identifiants** : format `HZ` + 5 chiffres (casse, espaces, zéros manquants, préfixes), doublons exacts, doublons quasi exacts (même id, valeurs différentes).
- **Modalités** : toutes les valeurs distinctes des colonnes catégorielles avec leurs effectifs (genre, boursier, filière, mention, région, emploi, statut, type_tuteur, motif, canal).
- **Numériques** : formats (virgule décimale, unités dans le texte), bornes du LISEZMOI (âge 17–35, note_bac 10–20, semaine 1–30, devoirs 0–2, note 0–20, absences 0–20, distance > 0), valeurs sentinelles (-1, 99, 999, 9999…).
- **Cohérences internes** : mention_bac vs note_bac ; cohorte vs annee_universitaire vs date_debut ; date_fin < date_debut ; statut « inscrit » avec date_fin ; abandon/transfert sans date_fin.
- **Dates** : formats hétérogènes, dates impossibles, date_debut hors octobre.
- **Entre tables** : ids présents dans une table et pas dans `etudiants` ; étudiants sans inscription ; activité ou tutorat **après** la sortie déclarée ; tutorat commencé après la semaine 30 ; doublons (id, semaine) dans l'activité ; étudiants avec plusieurs lignes de tutorat ; semaines manquantes dans l'activité.
- **Données personnelles** dans `messages.texte` : noms, téléphones (formats sénégalais 77/78/76/70/75 …), e-mails, adresses — compter et montrer 3 exemples **masqués**.

## Contraintes
- Graine fixée si tirage aléatoire. Pas de chemin absolu.
- Ne tranche aucun traitement : l'audit **constate**, les décisions seront prises par l'étudiant (DA-02 à DA-05).
- Termine par un résumé : nombre d'anomalies par table, et les 5 anomalies qui risquent le plus de fausser T, E ou le tutorat.

## Livraison
- Commit unique : `DA-01 : audit qualité des 5 fichiers bruts` ; push sur `main`.
- Réponds avec : le résumé, la liste des fichiers créés, et toute ambiguïté rencontrée (sans la résoudre).
