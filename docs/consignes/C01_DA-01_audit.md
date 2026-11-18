# Consigne C01 — Mise en place + DA-01 : audit qualité des 5 fichiers bruts

## Contexte
Lis d'abord `CLAUDE.md` (cadre du projet, à respecter en tout point), puis `docs/cahier_des_charges.pdf` (§4 et §6) et `data/raw/LISEZMOI.md`.
Périmètre : **mise en place de l'environnement + DA-01 (audit) uniquement.** Ne nettoie rien, ne modifie aucun fichier de `data/raw/`.

## Partie A — Mise en place (GP-01)
1. Créer le `.venv` (CLAUDE.md §4) et installer pandas, numpy, pytest. Écrire `requirements.txt` : les bibliothèques directement utilisées, avec la version installée (`==`).
2. `src/__init__.py` (vide) et `src/config.py` :
   - chemins construits avec pathlib à partir de l'emplacement de `config.py` (racine du dépôt, `data/raw`, `data/processed`, `docs`, `docs/figures`) ;
   - `SEED = 42`, `N_SEMAINES = 30`, `SEUIL_INACTIVITE = 4` ;
   - les valeurs attendues du `LISEZMOI.md` : séparateur de chaque fichier, format d'identifiant (`HZ` + 5 chiffres), bornes numériques, modalités attendues de chaque variable catégorielle.
3. `tests/test_raw_intact.py` : vérifie que chaque fichier de `data/raw/` a exactement l'empreinte SHA-256 inscrite dans `data/raw_sha256.txt`.

## Partie B — Audit (DA-01)
### À produire
1. `src/audit.py`, relançable avec `python -m src.audit` depuis la racine. Il utilise les constantes de `config.py` (aucune valeur codée en dur ailleurs).
2. `docs/audit_qualite.md`, **généré par le script**. Pour chaque table, une section avec :
   - la structure : séparateur, encodage détecté, noms de colonnes (bruts / attendus), types, nombre de lignes ;
   - un tableau d'anomalies : `# | colonne | anomalie | nb de lignes | 3 exemples`.

### Ce qu'il faut chercher (liste non exhaustive : aller plus loin)
- **Structure** : séparateurs, BOM, encodage cassé (mojibake type `Ã©`), espaces dans les en-têtes, colonnes renommées, lignes vides ou décalées.
- **Identifiants** : format `HZ` + 5 chiffres (casse, espaces, zéros manquants, préfixes), doublons exacts, doublons quasi exacts (même identifiant, valeurs différentes).
- **Modalités** : toutes les valeurs distinctes des colonnes catégorielles, avec leurs effectifs (genre, boursier, filière, mention, région, emploi, statut, type_tuteur, motif, canal).
- **Numériques** : formats (virgule décimale, unité dans le texte), bornes du LISEZMOI (âge 17–35, note_bac 10–20, semaine 1–30, devoirs 0–2, note 0–20, absences 0–20, distance > 0), valeurs sentinelles (-1, 99, 999, 9999…).
- **Cohérences internes** : mention_bac / note_bac ; cohorte / annee_universitaire / date_debut ; date_fin < date_debut ; statut « inscrit » avec une date_fin ; abandon ou transfert sans date_fin.
- **Dates** : formats hétérogènes, dates impossibles, date_debut hors octobre.
- **Entre tables** : identifiants absents de `etudiants` ; étudiants sans inscription ; activité ou tutorat **après** la sortie déclarée ; tutorat commencé après la semaine 30 ; doublons (identifiant, semaine) dans l'activité ; étudiants avec plusieurs lignes de tutorat ; semaines manquantes dans l'activité.
- **Données personnelles** dans `messages.texte` : noms, téléphones (formats sénégalais 77, 78, 76, 70, 75…), e-mails, adresses. Compter et montrer 3 exemples **masqués**.

### Contraintes
- L'audit **constate**, il ne tranche rien : les traitements seront décidés par Saliou (DA-02 à DA-05).
- Terminer `docs/audit_qualite.md` par un résumé : nombre d'anomalies par table, et les 5 anomalies qui risquent le plus de fausser T, E ou le tutorat.

## Livraison
- Deux commits poussés sur `main` :
  1. `GP-01 : environnement, configuration et test d'intégrité des fichiers bruts`
  2. `DA-01 : audit qualité des 5 fichiers bruts`
- Compte rendu au format du §10 de `CLAUDE.md`. Dans « Décisions en attente », lister les ambiguïtés constatées, sans les résoudre.
