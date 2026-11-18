# Audit qualité des fichiers bruts (DA-01)

> Fichier généré par `python -m src.audit` — ne pas modifier à la main.
> L'audit **constate** sans rien corriger : les traitements seront décidés par Saliou (DA-02 à DA-05).
> Les valeurs sont montrées entre « » pour rendre visibles les espaces. « l. n » = numéro de ligne
> dans le fichier (ligne 1 = en-tête).
> Rapprochements entre tables : identifiant mis en majuscules et sans espaces (normalisation provisoire).
> Semaine de sortie : (date_fin − date_debut) // 7 + 1 (convention provisoire, à valider en DA-07).

## Table `etudiants`

### Structure

- Fichier : `etudiants.csv`
- Séparateur attendu : «,» · détecté : «,»
- Encodage : UTF-8 (décodage strict réussi) · BOM : non · fins de ligne : LF
- Lignes de données : 5085 (annoncées ≈ 5000) · lignes physiques (en-tête compris) : 5086

| # | colonne brute | colonne attendue | type lu par pandas (inférence par défaut) |
|---|---|---|---|
| 1 | «id_etudiant » | id_etudiant | str |
| 2 | «cohorte» | cohorte | int64 |
| 3 | «genre» | genre | str |
| 4 | «age» | age | str |
| 5 | «boursier» | boursier | str |
| 6 | «filiere» | filiere | str |
| 7 | «mention_bac» | mention_bac | str |
| 8 | «note_bac» | note_bac | str |
| 9 | «region_origine» | region_origine | str |
| 10 | «Distance campus (km)» | distance_campus_km | str |
| 11 | «emploi_parallele» | emploi_parallele | str |

#### Modalités observées (⚠ = absente de la liste attendue)

- **cohorte** (2 valeurs distinctes) : «2025» 2554, «2024» 2531
- **genre** (10 valeurs distinctes) : «M» 2563, «F» 2115, «Femme» ⚠ 61, «Masculin» ⚠ 57, «Homme» ⚠ 56, «m» ⚠ 55, «F » ⚠ 47, «H» ⚠ 46, «FEMININ» ⚠ 45, «f» ⚠ 40
- **boursier** (12 valeurs distinctes) : «Non» 2660, «Oui» 1912, «N» ⚠ 71, «non» ⚠ 63, «NON» ⚠ 59, «0» ⚠ 58, «no» ⚠ 53, «O» ⚠ 51, «oui» ⚠ 49, «1» ⚠ 39, «OUI» ⚠ 39, «yes» ⚠ 31
- **filiere** (22 valeurs distinctes) : «Informatique» 1322, «Gestion» 1143, «Droit» 775, «Communication» 704, «Génie civil» 683, «gestion» ⚠ 46, «Informatique » ⚠ 38, «Gestion » ⚠ 38, «INFO» ⚠ 37, «GESTION» ⚠ 37, «Communication » ⚠ 32, «informatique» ⚠ 30, «Info» ⚠ 28, «Genie civil» ⚠ 23, «Droit » ⚠ 22, «Com» ⚠ 21, «Génie Civil» ⚠ 21, «communication» ⚠ 20, «DROIT» ⚠ 18, «droit» ⚠ 18, «GC» ⚠ 17, «genie civil» ⚠ 12
- **mention_bac** (16 valeurs distinctes) : «Passable» 2061, «Assez bien» 1362, «Bien» 857, «Très bien» 302, «» ⚠ 154, «PASSABLE» ⚠ 62, «passable» ⚠ 61, «P» ⚠ 50, «assez bien» ⚠ 34, «Assez Bien» ⚠ 33, «AB» ⚠ 32, «bien» ⚠ 29, «B» ⚠ 24, «tres bien» ⚠ 10, «Tres bien» ⚠ 8, «TB» ⚠ 6
- **region_origine** (29 valeurs distinctes) : «Dakar» 1883, «Thiès» 585, «Diourbel» 366, «Saint-Louis» 305, «Kaolack» 259, «Ziguinchor» 237, «Louga» 231, «Fatick» 200, «Tambacounda» 158, «Kolda» 145, «Matam» 101, «Kaffrine» 99, «» ⚠ 91, «Sédhiou» 88, «Kédougou» 81, «Dakar » ⚠ 54, «dakar» ⚠ 53, «DAKAR» ⚠ 41, «kaolack» ⚠ 24, «Thies» ⚠ 14, «thiès» ⚠ 12, «THIES» ⚠ 11, «ziguinchor» ⚠ 10, «Saint Louis» ⚠ 9, «St-Louis» ⚠ 8, «Kedougou» ⚠ 6, «ST LOUIS» ⚠ 6, «Zig» ⚠ 5, «Sedhiou» ⚠ 3
- **emploi_parallele** (3 valeurs distinctes) : «Non» 3913, «Oui» 967, «» ⚠ 205

### Anomalies

| # | colonne | anomalie | nb de lignes | 3 exemples |
|---|---|---|---:|---|
| ETU-01 | (en-tête) | nom de colonne entouré d'espaces | 1 | «id_etudiant » |
| ETU-02 | (en-tête) | colonne nommée autrement que dans le LISEZMOI | 1 | «Distance campus (km)» au lieu de «distance_campus_km» |
| ETU-03 | id_etudiant | identifiant entouré d'espaces | 12 | l. 1522  HZ49965 : « HZ49965»<br>l. 1593 HZ26733  : «HZ26733 »<br>l. 1739 HZ12280  : «HZ12280 » |
| ETU-04 | id_etudiant | identifiant en minuscules (« hz » au lieu de « HZ ») | 13 | l. 778 hz86247 : «hz86247»<br>l. 807 hz41252 : «hz41252»<br>l. 898 hz97044 : «hz97044» |
| ETU-05 | (ligne entière) | doublon exact (ligne identique à une ligne précédente) — nombre de lignes en trop | 60 | l. 426 HZ89101 : «HZ89101»<br>l. 2017 HZ14973 : «HZ14973»<br>l. 2039 HZ88152 : «HZ88152» |
| ETU-06 | id_etudiant | même id_etudiant répété avec le même contenu (après mise en majuscules de l'identifiant ; doublons exacts compris) — nombre de lignes en trop | 61 | l. 13 HZ55748 : «HZ55748»<br>l. 178 HZ75024 : «HZ75024»<br>l. 209 HZ81337 : «HZ81337» |
| ETU-07 | id_etudiant | même id_etudiant répété avec des valeurs différentes (quasi-doublon) — 24 clés concernées, nombre de lignes | 48 | HZ12280 : distance_campus_km = «10.8» / «11.1»<br>HZ15625 : distance_campus_km = «6.1» / «5.5»<br>HZ25093 : distance_campus_km = «19.7» / «19.6» |
| ETU-08 | age | valeur manquante (case vide ou espaces) | 72 | l. 6 HZ44228 : «» |
| ETU-09 | mention_bac | valeur manquante (case vide ou espaces) | 154 | l. 54 HZ38956 : «» |
| ETU-10 | region_origine | valeur manquante (case vide ou espaces) | 91 | l. 33 HZ24400 : «» |
| ETU-11 | emploi_parallele | valeur manquante (case vide ou espaces) | 205 | l. 14 HZ59587 : «» |
| ETU-12 | genre | modalité non conforme au LISEZMOI (8 écritures différentes) | 407 | «Femme» (61)<br>«Masculin» (57)<br>«Homme» (56) |
| ETU-13 | boursier | modalité non conforme au LISEZMOI (10 écritures différentes) | 513 | «N» (71)<br>«non» (63)<br>«NON» (59) |
| ETU-14 | filiere | modalité non conforme au LISEZMOI (17 écritures différentes) | 458 | «gestion» (46)<br>«Informatique » (38)<br>«Gestion » (38) |
| ETU-15 | mention_bac | modalité non conforme au LISEZMOI (11 écritures différentes) | 349 | «PASSABLE» (62)<br>«passable» (61)<br>«P» (50) |
| ETU-16 | region_origine | modalité non conforme au LISEZMOI (14 écritures différentes) | 256 | «Dakar » (54)<br>«dakar» (53)<br>«DAKAR» (41) |
| ETU-17 | age | nombre écrit au format « avec unité » | 46 | l. 231 HZ45294 : «19 ans»<br>l. 237 HZ79757 : «21 ans»<br>l. 392 HZ77436 : «18 ans» |
| ETU-18 | age | valeur sentinelle (-1, 99, 999, 9999) | 2 | l. 4499 HZ17072 : «99» |
| ETU-19 | age | valeur hors bornes (attendu : 17 à 35) | 12 | l. 81 HZ74502 : «210»<br>l. 245 HZ50344 : «0»<br>l. 249 HZ41612 : «150» |
| ETU-20 | note_bac | nombre écrit au format « décimal (virgule) » | 250 | l. 7 HZ86647 : «17,46»<br>l. 37 HZ98131 : «12,71»<br>l. 49 HZ97805 : «16,43» |
| ETU-21 | note_bac | valeur hors bornes (attendu : 10 à 20) | 18 | l. 203 HZ76735 : «25.5»<br>l. 554 HZ80508 : «135.0»<br>l. 860 HZ58508 : «112.0» |
| ETU-22 | distance_campus_km | nombre écrit au format « décimal (virgule) » | 197 | l. 14 HZ59587 : «14,6»<br>l. 33 HZ24400 : «3,8»<br>l. 91 HZ67433 : «7,6» |
| ETU-23 | distance_campus_km | nombre écrit au format « avec unité » | 41 | l. 251 HZ93144 : «11.8 km»<br>l. 586 HZ63745 : «13.7 km»<br>l. 643 HZ47924 : «9.1 km» |
| ETU-24 | distance_campus_km | valeur sentinelle (-1, 99, 999, 9999) | 10 | l. 193 HZ51469 : «9999» |
| ETU-25 | distance_campus_km | valeur hors bornes (attendu : > 0) | 15 | l. 425 HZ92373 : «-17.3»<br>l. 460 HZ67619 : «-12.0»<br>l. 1351 HZ41171 : «-9.0» |
| ETU-26 | distance_campus_km | valeur très éloignée du reste (> 51.7, Q3 + 3×IQR) — à examiner | 514 | l. 16 HZ54915 : «79.5»<br>l. 17 HZ39215 : «109.2»<br>l. 18 HZ91643 : «91.7» |
| ETU-27 | mention_bac / note_bac | note_bac hors de l'intervalle de la mention (parmi les 4564 lignes comparables) | 37 | l. 39 HZ99935 : «Bien» avec «10.66»<br>l. 97 HZ10819 : «Bien» avec «10.39»<br>l. 111 HZ55847 : «Bien» avec «10.93» |

Contrôles effectués sans anomalie : (lignes) : ligne vide au milieu du fichier · (lignes) : ligne décalée (nombre de champs différent de 11) · id_etudiant : identifiant vide · id_etudiant : identifiant d'un autre format (préfixe, nombre de chiffres…) · cohorte : valeur manquante (case vide ou espaces) · genre : valeur manquante (case vide ou espaces) · boursier : valeur manquante (case vide ou espaces) · filiere : valeur manquante (case vide ou espaces) · note_bac : valeur manquante (case vide ou espaces) · distance_campus_km : valeur manquante (case vide ou espaces) · cohorte : modalité non conforme au LISEZMOI · emploi_parallele : modalité non conforme au LISEZMOI · age : nombre écrit au format « décimal (virgule) » · age : nombre écrit au format « non numérique » · age : nombre entier écrit avec une partie décimale (ex. « 5.0 ») · note_bac : nombre écrit au format « avec unité » · note_bac : nombre écrit au format « non numérique » · note_bac : valeur sentinelle (-1, 99, 999, 9999) · distance_campus_km : nombre écrit au format « non numérique » · cohorte : nombre écrit au format « décimal (virgule) » · cohorte : nombre écrit au format « avec unité » · cohorte : nombre écrit au format « non numérique » · cohorte : nombre entier écrit avec une partie décimale (ex. « 5.0 »).

## Table `inscriptions`

### Structure

- Fichier : `inscriptions.csv`
- Séparateur attendu : «;» · détecté : «;»
- Encodage : UTF-8 (décodage strict réussi) · BOM : non · fins de ligne : LF
- Lignes de données : 5024 (annoncées ≈ 5000) · lignes physiques (en-tête compris) : 5025

| # | colonne brute | colonne attendue | type lu par pandas (inférence par défaut) |
|---|---|---|---|
| 1 | «id_etudiant» | id_etudiant | str |
| 2 | «annee_universitaire» | annee_universitaire | str |
| 3 | «date_debut» | date_debut | str |
| 4 | «date_fin» | date_fin | str |
| 5 | «statut_final» | statut_final | str |

#### Modalités observées (⚠ = absente de la liste attendue)

- **annee_universitaire** (2 valeurs distinctes) : «2025-2026» 2525, «2024-2025» 2499
- **statut_final** (14 valeurs distinctes) : «inscrit» 3507, «abandon» 968, «transfert» 108, «INSCRIT» ⚠ 108, «Inscrit» ⚠ 107, «inscrit » ⚠ 105, «» ⚠ 41, «Abandon » ⚠ 20, «abandonné» ⚠ 20, «Abandon» ⚠ 17, «ABANDON» ⚠ 14, «transfere» ⚠ 6, «Transfert» ⚠ 2, «transféré» ⚠ 1

### Anomalies

| # | colonne | anomalie | nb de lignes | 3 exemples |
|---|---|---|---:|---|
| INS-01 | (ligne entière) | doublon exact (ligne identique à une ligne précédente) — nombre de lignes en trop | 20 | l. 798 HZ37149 : «HZ37149»<br>l. 1097 HZ77451 : «HZ77451»<br>l. 1134 HZ92160 : «HZ92160» |
| INS-02 | id_etudiant | même id_etudiant répété avec le même contenu (après mise en majuscules de l'identifiant ; doublons exacts compris) — nombre de lignes en trop | 20 | l. 108 HZ66458 : «HZ66458»<br>l. 247 HZ90446 : «HZ90446»<br>l. 441 HZ42249 : «HZ42249» |
| INS-03 | statut_final | valeur manquante (case vide ou espaces) | 41 | l. 155 HZ52568 : «» |
| INS-04 | statut_final | modalité non conforme au LISEZMOI (10 écritures différentes) | 400 | «INSCRIT» (108)<br>«Inscrit» (107)<br>«inscrit » (105) |
| INS-05 | date_debut | date dans un autre format que AAAA-MM-JJ — répartition : AAAA-MM-JJ 3724, JJ/MM/AAAA 748, AAAA/MM/JJ 340, J mois AAAA (français) 212 | 1300 | l. 5 HZ73806 : «06/10/2025»<br>l. 6 HZ26666 : «7 oct. 2024»<br>l. 12 HZ39272 : «2025/10/06» |
| INS-06 | date_fin | date dans un autre format que AAAA-MM-JJ — répartition : AAAA-MM-JJ 845, JJ/MM/AAAA 170, AAAA/MM/JJ 76, J mois AAAA (français) 43 | 289 | l. 17 HZ46698 : «14/11/2025»<br>l. 43 HZ19302 : «2026/03/14»<br>l. 82 HZ40295 : «2026/02/16» |
| INS-07 | date_debut | date_debut hors du mois d'octobre | 8 | l. 613 HZ29974 : «2026-04-16»<br>l. 1778 HZ62218 : «16/01/2026»<br>l. 2528 HZ71798 : «2025-01-22» |
| INS-08 | date_debut | année de date_debut différente de l'année de rentrée de annee_universitaire | 5 | l. 613 HZ29974 : «2026-04-16»<br>l. 1778 HZ62218 : «16/01/2026»<br>l. 2528 HZ71798 : «2025-01-22» |
| INS-09 | date_debut | date_debut en octobre mais différente de la rentrée la plus fréquente de la cohorte (2024 : 2024-10-07, 2025 : 2025-10-06) | 4 | l. 2609 HZ72375 : «2024-10-29»<br>l. 3192 HZ20999 : «2025-10-16»<br>l. 3287 HZ93888 : «27/10/2024» |
| INS-10 | date_fin | date_fin antérieure à date_debut | 12 | l. 613 HZ29974 : «2025-10-06»<br>l. 2528 HZ71798 : «2024-10-07»<br>l. 3192 HZ20999 : «06/10/2025» |
| INS-11 | date_fin | date_fin après la fin du suivi (≥ date_debut + 30 semaines) | 6 | l. 284 HZ73374 : «2027-03-15»<br>l. 1202 HZ90568 : «2027-07-15»<br>l. 3252 HZ38086 : «2027-04-15» |
| INS-12 | statut_final / date_fin | abandon ou transfert (toutes écritures) sans date_fin | 22 | l. 392 HZ47677 : «abandon» |

Contrôles effectués sans anomalie : (en-tête) : nom de colonne entouré d'espaces · (en-tête) : colonne nommée autrement que dans le LISEZMOI · (lignes) : ligne vide au milieu du fichier · (lignes) : ligne décalée (nombre de champs différent de 5) · id_etudiant : identifiant entouré d'espaces · id_etudiant : identifiant en minuscules (« hz » au lieu de « HZ ») · id_etudiant : identifiant vide · id_etudiant : identifiant d'un autre format (préfixe, nombre de chiffres…) · id_etudiant : même id_etudiant répété avec des valeurs différentes (quasi-doublon) · annee_universitaire : valeur manquante (case vide ou espaces) · date_debut : valeur manquante (case vide ou espaces) · annee_universitaire : modalité non conforme au LISEZMOI · date_debut : date illisible (format non reconnu) · date_debut : date impossible (ex. 31/02) · date_fin : date illisible (format non reconnu) · date_fin : date impossible (ex. 31/02) · statut_final / date_fin : statut « inscrit » (toutes écritures) avec une date_fin renseignée.

## Table `activite_hebdo`

### Structure

- Fichier : `activite_hebdo.csv`
- Séparateur attendu : «,» · détecté : «,»
- Encodage : UTF-8 (décodage strict réussi) · BOM : non · fins de ligne : LF
- Lignes de données : 130967 (annoncées ≈ 130000) · lignes physiques (en-tête compris) : 130968

| # | colonne brute | colonne attendue | type lu par pandas (inférence par défaut) |
|---|---|---|---|
| 1 | «id_etudiant» | id_etudiant | str |
| 2 | «semaine» | semaine | int64 |
| 3 | «nb_connexions_lms» | nb_connexions_lms | float64 |
| 4 | «devoirs_rendus» | devoirs_rendus | int64 |
| 5 | «note_moyenne» | note_moyenne | str |
| 6 | «absences» | absences | int64 |

### Anomalies

| # | colonne | anomalie | nb de lignes | 3 exemples |
|---|---|---|---:|---|
| ACT-01 | id_etudiant | identifiant en minuscules (« hz » au lieu de « HZ ») | 1310 | l. 125 hz74084 : «hz74084»<br>l. 138 hz87940 : «hz87940»<br>l. 184 hz88026 : «hz88026» |
| ACT-02 | (ligne entière) | doublon exact (ligne identique à une ligne précédente) — nombre de lignes en trop | 870 | l. 3553 HZ28229 : «HZ28229»<br>l. 4389 HZ93285 : «HZ93285»<br>l. 4764 HZ92337 : «HZ92337» |
| ACT-03 | (id_etudiant, semaine) | même (id_etudiant, semaine) répété avec le même contenu (après mise en majuscules de l'identifiant ; doublons exacts compris) — nombre de lignes en trop | 883 | l. 37 HZ56370 : «HZ56370»<br>l. 46 HZ57544 : «HZ57544»<br>l. 51 HZ79635 : «HZ79635» |
| ACT-04 | (id_etudiant, semaine) | même (id_etudiant, semaine) répété avec des valeurs différentes (quasi-doublon) — 176 clés concernées, nombre de lignes | 353 | HZ11106 20 : nb_connexions_lms = «13.0» / «10.0»<br>HZ11318 18 : nb_connexions_lms = «8.0» / «12.0»<br>HZ11584 8 : nb_connexions_lms = «9.0» / «13.0» |
| ACT-05 | nb_connexions_lms | valeur manquante (case vide ou espaces) | 1298 | l. 2 HZ40832 : «» |
| ACT-06 | semaine | valeur sentinelle (-1, 99, 999, 9999) | 27 | l. 3394 HZ88386 : «99»<br>l. 8344 HZ26330 : «-1» |
| ACT-07 | semaine | valeur hors bornes (attendu : 1 à 30) | 43 | l. 9792 HZ93077 : «0»<br>l. 13527 HZ17438 : «31»<br>l. 20788 HZ97954 : «32» |
| ACT-08 | devoirs_rendus | valeur hors bornes (attendu : 0 à 2) | 30 | l. 1213 HZ51900 : «3»<br>l. 4360 HZ55167 : «4»<br>l. 9939 HZ58448 : «7» |
| ACT-09 | note_moyenne | nombre écrit au format « décimal (virgule) » | 1703 | l. 48 HZ79182 : «9,72»<br>l. 59 HZ97878 : «13,24»<br>l. 136 HZ56149 : «15,11» |
| ACT-10 | note_moyenne | valeur sentinelle (-1, 99, 999, 9999) | 25 | l. 1322 HZ84175 : «-1» |
| ACT-11 | note_moyenne | valeur hors bornes (attendu : 0 à 20) | 110 | l. 2091 HZ60737 : «122.0»<br>l. 2874 HZ31577 : «72.2»<br>l. 3357 HZ51426 : «85.9» |
| ACT-12 | nb_connexions_lms | nombre entier écrit avec une partie décimale (ex. « 5.0 ») | 129669 | l. 3 HZ36707 : «10.0»<br>l. 4 HZ40562 : «0.0»<br>l. 5 HZ73285 : «4.0» |
| ACT-13 | nb_connexions_lms | valeur hors bornes (attendu : ≥ 0) | 45 | l. 997 HZ42505 : «-7.0»<br>l. 1370 HZ31561 : «-3.0»<br>l. 5659 HZ60648 : «-4.0» |
| ACT-14 | nb_connexions_lms | valeur très éloignée du reste (> 20, Q3 + 3×IQR) — à examiner | 47 | l. 1921 HZ81558 : «21.0»<br>l. 5427 HZ91107 : «6076.0»<br>l. 6055 HZ31818 : «22.0» |

Contrôles effectués sans anomalie : (en-tête) : nom de colonne entouré d'espaces · (en-tête) : colonne nommée autrement que dans le LISEZMOI · (lignes) : ligne vide au milieu du fichier · (lignes) : ligne décalée (nombre de champs différent de 6) · id_etudiant : identifiant entouré d'espaces · id_etudiant : identifiant vide · id_etudiant : identifiant d'un autre format (préfixe, nombre de chiffres…) · semaine : valeur manquante (case vide ou espaces) · devoirs_rendus : valeur manquante (case vide ou espaces) · absences : valeur manquante (case vide ou espaces) · semaine : nombre écrit au format « décimal (virgule) » · semaine : nombre écrit au format « avec unité » · semaine : nombre écrit au format « non numérique » · semaine : nombre entier écrit avec une partie décimale (ex. « 5.0 ») · devoirs_rendus : nombre écrit au format « décimal (virgule) » · devoirs_rendus : nombre écrit au format « avec unité » · devoirs_rendus : nombre écrit au format « non numérique » · devoirs_rendus : nombre entier écrit avec une partie décimale (ex. « 5.0 ») · devoirs_rendus : valeur sentinelle (-1, 99, 999, 9999) · note_moyenne : nombre écrit au format « avec unité » · note_moyenne : nombre écrit au format « non numérique » · absences : nombre écrit au format « décimal (virgule) » · absences : nombre écrit au format « avec unité » · absences : nombre écrit au format « non numérique » · absences : nombre entier écrit avec une partie décimale (ex. « 5.0 ») · absences : valeur sentinelle (-1, 99, 999, 9999) · absences : valeur hors bornes (attendu : 0 à 20) · nb_connexions_lms : nombre écrit au format « décimal (virgule) » · nb_connexions_lms : nombre écrit au format « avec unité » · nb_connexions_lms : nombre écrit au format « non numérique » · nb_connexions_lms : valeur sentinelle (-1, 99, 999, 9999).

## Table `tutorat`

### Structure

- Fichier : `tutorat.csv`
- Séparateur attendu : «,» · détecté : «,»
- Encodage : UTF-8 (décodage strict réussi) · BOM : non · fins de ligne : LF
- Lignes de données : 1291 (annoncées ≈ 1300) · lignes physiques (en-tête compris) : 1292

| # | colonne brute | colonne attendue | type lu par pandas (inférence par défaut) |
|---|---|---|---|
| 1 | «ID Etudiant» | id_etudiant | str |
| 2 | «semaine_debut» | semaine_debut | int64 |
| 3 | «nb_seances» | nb_seances | float64 |
| 4 | «type_tuteur» | type_tuteur | str |
| 5 | «motif_orientation» | motif_orientation | str |

#### Modalités observées (⚠ = absente de la liste attendue)

- **type_tuteur** (9 valeurs distinctes) : «pair (étudiant avancé)» ⚠ 775, «enseignant» 388, «PAIR» ⚠ 24, «pair» 23, «enseignant » ⚠ 21, «Pair» ⚠ 18, «étudiant» ⚠ 17, «ENSEIGNANT» ⚠ 16, «Prof» ⚠ 9
- **motif_orientation** (4 valeurs distinctes) : «notes faibles» 510, «absences répétées» 329, «signalement enseignant» 245, «demande personnelle» 207

### Anomalies

| # | colonne | anomalie | nb de lignes | 3 exemples |
|---|---|---|---:|---|
| TUT-01 | (en-tête) | colonne nommée autrement que dans le LISEZMOI | 1 | «ID Etudiant» au lieu de «id_etudiant» |
| TUT-02 | (ligne entière) | doublon exact (ligne identique à une ligne précédente) — nombre de lignes en trop | 30 | l. 85 HZ70667 : «HZ70667»<br>l. 178 HZ90929 : «HZ90929»<br>l. 179 HZ38269 : «HZ38269» |
| TUT-03 | id_etudiant | même id_etudiant répété avec le même contenu (après mise en majuscules de l'identifiant ; doublons exacts compris) — nombre de lignes en trop | 30 | l. 10 HZ82600 : «HZ82600»<br>l. 35 HZ70667 : «HZ70667»<br>l. 47 HZ90929 : «HZ90929» |
| TUT-04 | nb_seances | valeur manquante (case vide ou espaces) | 8 | l. 33 HZ11648 : «» |
| TUT-05 | type_tuteur | modalité non conforme au LISEZMOI (7 écritures différentes) | 880 | «pair (étudiant avancé)» (775)<br>«PAIR» (24)<br>«enseignant » (21) |
| TUT-06 | semaine_debut | valeur hors bornes (attendu : 1 à 30) | 10 | l. 87 HZ19393 : «52»<br>l. 97 HZ93907 : «0»<br>l. 484 HZ38800 : «45» |
| TUT-07 | nb_seances | nombre entier écrit avec une partie décimale (ex. « 5.0 ») | 17 | l. 128 HZ81429 : «-2.0»<br>l. 144 HZ80680 : «0.0» |
| TUT-08 | nb_seances | valeur hors bornes (attendu : ≥ 1) | 17 | l. 128 HZ81429 : «-2.0»<br>l. 144 HZ80680 : «0.0» |
| TUT-09 | semaine_debut | tutorat commencé après la semaine 30 (déjà compté dans « hors bornes ») | 5 | l. 87 HZ19393 : «52»<br>l. 484 HZ38800 : «45» |

Contrôles effectués sans anomalie : (en-tête) : nom de colonne entouré d'espaces · (lignes) : ligne vide au milieu du fichier · (lignes) : ligne décalée (nombre de champs différent de 5) · id_etudiant : identifiant entouré d'espaces · id_etudiant : identifiant en minuscules (« hz » au lieu de « HZ ») · id_etudiant : identifiant vide · id_etudiant : identifiant d'un autre format (préfixe, nombre de chiffres…) · id_etudiant : même id_etudiant répété avec des valeurs différentes (quasi-doublon) · semaine_debut : valeur manquante (case vide ou espaces) · type_tuteur : valeur manquante (case vide ou espaces) · motif_orientation : valeur manquante (case vide ou espaces) · motif_orientation : modalité non conforme au LISEZMOI · semaine_debut : nombre écrit au format « décimal (virgule) » · semaine_debut : nombre écrit au format « avec unité » · semaine_debut : nombre écrit au format « non numérique » · semaine_debut : nombre entier écrit avec une partie décimale (ex. « 5.0 ») · semaine_debut : valeur sentinelle (-1, 99, 999, 9999) · nb_seances : nombre écrit au format « décimal (virgule) » · nb_seances : nombre écrit au format « avec unité » · nb_seances : nombre écrit au format « non numérique » · nb_seances : valeur sentinelle (-1, 99, 999, 9999) · nb_seances : valeur très éloignée du reste (> 44, Q3 + 3×IQR).

## Table `messages`

### Structure

- Fichier : `messages.csv`
- Séparateur attendu : «,» · détecté : «,»
- Encodage : UTF-8 (décodage strict réussi) · BOM : non · fins de ligne : LF
- Lignes de données : 3200 (annoncées ≈ 3200) · lignes physiques (en-tête compris) : 3201

| # | colonne brute | colonne attendue | type lu par pandas (inférence par défaut) |
|---|---|---|---|
| 1 | «id_message» | id_message | str |
| 2 | «id_etudiant» | id_etudiant | str |
| 3 | «semaine» | semaine | int64 |
| 4 | «canal» | canal | str |
| 5 | «texte» | texte | str |

#### Modalités observées (⚠ = absente de la liste attendue)

- **canal** (2 valeurs distinctes) : «formulaire de suivi» 1932, «forum» 1268

### Anomalies

| # | colonne | anomalie | nb de lignes | 3 exemples |
|---|---|---|---:|---|
| MSG-01 | texte | encodage cassé (mojibake, ex. « Ã© » pour « é ») | 40 | l. 22 HZ10791 : «Est-ce que le devoir est Ã  rendre vendredi ?»<br>l. 89 HZ12590 : «Je n'ai pas trouvÃ© le support du cours sur la plateforme.»<br>l. 102 HZ12910 : «Je travaille le soir et je suis Ã©puisÃ©.» |
| MSG-02 | texte | valeur manquante (case vide ou espaces) | 18 | l. 90 HZ12595 : « »<br>l. 197 HZ15779 : «»<br>l. 319 HZ19115 : «   » |
| MSG-03 | texte | message vide ou sans aucun mot (ex. « . ») | 25 | l. 52 HZ11681 : «.»<br>l. 90 HZ12595 : « »<br>l. 197 HZ15779 : «» |
| MSG-04 | texte | donnée personnelle : nom propre introduit par « je suis », « c'est »… | 96 | M00039 : «Bonjour, c'est A••• N•••. Le groupe de travail m'aide à avancer.»<br>M00103 : «Bonjour, c'est O••• D•••. Je voudrais changer de groupe de TD.»<br>M00181 : «Bonjour, c'est M••• D•••. Tout se passe bien, je suis à jour dans mes cours.» |
| MSG-05 | texte | donnée personnelle : numéro de téléphone (format sénégalais 70, 75, 76, 77, 78) | 45 | M00254 : «J'ai bien compris le dernier chapitre. Je suis M••• N•••, appelez-moi au 77 ••• •• ••.»<br>M00266 : «Les TD m'aident beaucoup, merci. Je suis K••• C•••, appelez-moi au 77 ••• •• ••.»<br>M00343 : «Tout se passe bien, je suis à jour dans mes cours. Je suis M••• S•••, appelez-moi au 77 ••• •• ••.» |
| MSG-06 | texte | donnée personnelle : adresse e-mail | 33 | M00004 : «Je suis découragé après les notes du partiel. Mon mail : m•••@•••»<br>M00093 : «Le planning de la semaine a changé ? Mon mail : m•••@•••»<br>M00329 : «Tout se passe bien, je suis à jour dans mes cours. Mon mail : m•••@•••» |
| MSG-07 | texte | message contenant au moins une donnée personnelle (un message peut en contenir plusieurs) | 129 | — |

Contrôles effectués sans anomalie : (en-tête) : nom de colonne entouré d'espaces · (en-tête) : colonne nommée autrement que dans le LISEZMOI · (lignes) : ligne vide au milieu du fichier · (lignes) : ligne décalée (nombre de champs différent de 5) · id_etudiant : identifiant entouré d'espaces · id_etudiant : identifiant en minuscules (« hz » au lieu de « HZ ») · id_etudiant : identifiant vide · id_etudiant : identifiant d'un autre format (préfixe, nombre de chiffres…) · (ligne entière) : doublon exact (ligne identique à une ligne précédente) · id_message : id_message en double · id_message : valeur manquante (case vide ou espaces) · semaine : valeur manquante (case vide ou espaces) · canal : valeur manquante (case vide ou espaces) · canal : modalité non conforme au LISEZMOI · semaine : nombre écrit au format « décimal (virgule) » · semaine : nombre écrit au format « avec unité » · semaine : nombre écrit au format « non numérique » · semaine : nombre entier écrit avec une partie décimale (ex. « 5.0 ») · semaine : valeur sentinelle (-1, 99, 999, 9999) · semaine : valeur hors bornes (attendu : 1 à 30) · texte : donnée personnelle : adresse postale (rue, quartier, villa…).

## Contrôles entre tables

| # | colonne | anomalie | nb de lignes | 3 exemples |
|---|---|---|---:|---|
| X-01 | inscriptions.id_etudiant | identifiant absent de etudiants (14 identifiants distincts) — nombre de lignes | 14 | l. 562 HZ96836 : «HZ96836»<br>l. 1080 HZ99803 : «HZ99803»<br>l. 1357 HZ97757 : «HZ97757» |
| X-02 | tutorat.id_etudiant | identifiant absent de etudiants (6 identifiants distincts) — nombre de lignes | 6 | l. 223 HZ88484 : «HZ88484»<br>l. 266 HZ82856 : «HZ82856»<br>l. 1031 HZ81487 : «HZ81487» |
| X-03 | etudiants.id_etudiant | étudiant sans aucune inscription — nombre d'étudiants | 10 | l. 994 HZ26334 : «HZ26334»<br>l. 1217 HZ59964 : «HZ59964»<br>l. 1441 HZ98561 : «HZ98561» |
| X-04 | activite_hebdo.semaine | étudiant SANS sortie déclarée ayant moins de 30 semaines d'activité — nombre d'étudiants | 24 | HZ12230 : 6 semaines (dernière : 6)<br>HZ20355 : 11 semaines (dernière : 11)<br>HZ20684 : 18 semaines (dernière : 18) |
| X-05 | activite_hebdo.semaine | étudiant AVEC sortie déclarée ayant moins de 30 semaines d'activité (arrêt possiblement normal) — nombre d'étudiants | 1110 | HZ10199 : 7 semaines (dernière : 7)<br>HZ10621 : 27 semaines (dernière : 27)<br>HZ10643 : 2 semaines (dernière : 2) |
| X-06 | activite_hebdo.semaine | ligne d'activité après la semaine de sortie déclarée (conversion date → semaine provisoire) | 195 | l. 397 HZ44147 : semaine 3, sortie en semaine -5<br>l. 839 HZ79122 : semaine 4, sortie en semaine -8<br>l. 2192 HZ19404 : semaine 21, sortie en semaine 19 |
| X-07 | activite_hebdo.semaine | dont lignes montrant une activité réelle (connexion ou devoir > 0) | 195 | l. 397 HZ44147 : semaine 3, sortie en semaine -5<br>l. 839 HZ79122 : semaine 4, sortie en semaine -8<br>l. 2192 HZ19404 : semaine 21, sortie en semaine 19 |
| X-08 | tutorat.semaine_debut | tutorat commencé après la semaine de sortie déclarée (conversion date → semaine provisoire) | 10 | l. 8 HZ87846 : semaine_debut 19, sortie en semaine 16<br>l. 624 HZ61263 : semaine_debut 10, sortie en semaine 6<br>l. 699 HZ82636 : semaine_debut 25, sortie en semaine 23 |
| X-09 | messages.semaine | message envoyé après la semaine de sortie déclarée (conversion date → semaine provisoire) | 3 | l. 384 HZ21515 : semaine 6, sortie en semaine -23<br>l. 689 HZ29974 : semaine 11, sortie en semaine -27<br>l. 2220 HZ71798 : semaine 1, sortie en semaine -15 |
| X-10 | tutorat.id_etudiant | étudiant avec plusieurs lignes de tutorat — nombre d'étudiants | 30 | HZ82600 : 2 lignes<br>HZ70667 : 2 lignes<br>HZ90929 : 2 lignes |

Contrôles effectués sans anomalie : activite_hebdo.id_etudiant : identifiant absent de etudiants · messages.id_etudiant : identifiant absent de etudiants · etudiants.id_etudiant : étudiant sans aucune ligne d'activité · inscriptions.annee_universitaire / etudiants.cohorte : année universitaire incompatible avec la cohorte · activite_hebdo.semaine : semaines manquantes au milieu de la série (trou) · activite_hebdo.semaine : série d'activité qui ne commence pas en semaine 1.

## Résumé

| Table | lignes de données | anomalies constatées (types) | lignes concernées (somme, une ligne peut compter plusieurs fois) |
|---|---:|---:|---:|
| etudiants | 5085 | 27 | 3843 |
| inscriptions | 5024 | 12 | 2127 |
| activite_hebdo | 130967 | 14 | 136413 |
| tutorat | 1291 | 9 | 998 |
| messages | 3200 | 7 | 386 |
| entre tables | — | 10 | 1597 |

### Les 5 anomalies qui risquent le plus de fausser T, E ou le tutorat

1. **Entrées de la règle d'inactivité (connexions et devoirs)** — ACT-05 valeur manquante (case vide ou espaces) (1298) ; ACT-13 valeur hors bornes (attendu : ≥ 0) (45) ; ACT-14 valeur très éloignée du reste (> 20, Q3 + 3×IQR) (47) ; ACT-08 valeur hors bornes (attendu : 0 à 2) (30). E : le décrochage non déclaré se lit sur « aucune connexion ni devoir rendu » pendant 4 semaines ; une connexion manquante, négative ou aberrante fait apparaître ou disparaître un décrochage.
2. **Statut de sortie et date de sortie** — INS-03 valeur manquante (case vide ou espaces) (41) ; INS-04 modalité non conforme au LISEZMOI (400) ; INS-12 abandon ou transfert (toutes écritures) sans date_fin (22) ; INS-10 date_fin antérieure à date_debut (12) ; INS-11 date_fin après la fin du suivi (≥ date_debut + 30 semaines) (6). E et T : le statut sépare l'abandon déclaré (E = 1) de la censure (transfert, inscrit) et date_fin donne la semaine de l'événement ; un statut vide ou un abandon sans date empêche de calculer T et E.
3. **Date de rentrée (origine du temps)** — INS-05 date dans un autre format que AAAA-MM-JJ (1300) ; INS-07 date_debut hors du mois d'octobre (8) ; INS-08 année de date_debut différente de l'année de rentrée de annee_universitaire (5) ; INS-09 date_debut en octobre mais différente de la rentrée la plus fréquente de la cohorte (4). T : date_debut fixe la semaine 1 de l'étudiant ; quatre formats coexistent et quelques dates sortent de la rentrée habituelle, ce qui décale toutes ses semaines (et la semaine de sortie calculée).
4. **Clé (étudiant, semaine) de l'activité** — ACT-01 identifiant en minuscules (« hz » au lieu de « HZ ») (1310) ; ACT-03 même (id_etudiant, semaine) répété avec le même contenu (après mise en majuscules de l'identifiant ; doublons exacts compris) (883) ; ACT-04 même (id_etudiant, semaine) répété avec des valeurs différentes (quasi-doublon) (353) ; ACT-06 valeur sentinelle (-1, 99, 999, 9999) (27) ; ACT-07 valeur hors bornes (attendu : 1 à 30) (43) ; X-04 étudiant SANS sortie déclarée ayant moins de 30 semaines d'activité (24). E : la règle des 4 semaines consécutives suppose une ligne par étudiant et par semaine ; des identifiants mal écrits, des semaines en double avec des valeurs différentes ou des semaines manquantes créent de fausses séries d'inactivité.
5. **Semaine de début du tutorat** — TUT-06 valeur hors bornes (attendu : 1 à 30) (10) ; X-08 tutorat commencé après la semaine de sortie déclarée (conversion date → semaine provisoire) (10) ; X-10 étudiant avec plusieurs lignes de tutorat (30) ; TUT-08 valeur hors bornes (attendu : ≥ 1) (17). Tutorat : la semaine de début porte le biais du temps immortel et l'analyse landmark ; une semaine 0 ou > 30, un tutorat après la sortie ou 0 séance suivie faussent la définition du traitement.
