# Journal de nettoyage

> Fichier généré par `python -m src.nettoyage` — ne pas modifier à la main.
> Chaque traitement applique une décision validée par Saliou (`docs/decisions.md`).
> Les codes d'anomalie (ETU-xx, INS-xx, ACT-xx, TUT-xx, MSG-xx, X-xx) renvoient à `docs/audit_qualite.md`.

## Bilan global

| Table | Lignes avant | Lignes après | Règles appliquées |
|---|---:|---:|---:|
| etudiants | 5085 | 5000 | 7 |
| inscriptions | 5024 | 5000 | 9 |
| activite_hebdo | 130967 | 129783 | 7 |
| tutorat | 1291 | 1255 | 8 |
| messages | 3200 | 3175 | 4 |
| **Total** | 145567 | 144213 | 35 |

| Fichier de rejets | Lignes |
|---|---:|
| `data/processed/rejets/inscriptions_sans_etudiant.csv` | 14 |
| `data/processed/rejets/activite_semaine_invalide.csv` | 70 |
| `data/processed/rejets/activite_apres_sortie.csv` | 54 |
| `data/processed/rejets/tutorat_sans_etudiant.csv` | 6 |
| `data/processed/rejets/messages_vides.csv` | 25 |

Codes d'anomalie de l'audit : 79 ; cités par un traitement : 69 ; laissés sans traitement (raison donnée) : 10.

## Traitements appliqués

| # | Table | Anomalie constatée | Lignes | Traitement appliqué | Justification |
|---:|---|---|---:|---|---|
| 1 | etudiants | En-tête entouré d'espaces (« id_etudiant  », ETU-01) | 1 | Espaces retirés | D-06 |
| 2 | etudiants | En-tête nommé autrement que dans le LISEZMOI (« Distance campus (km) », ETU-02) | 1 | Renommé en distance_campus_km | D-06 |
| 3 | etudiants | Identifiant entouré d'espaces (ETU-03) | 12 | Espaces retirés | D-06 |
| 4 | etudiants | Identifiant en minuscules (ETU-04) | 13 | Mis en majuscules | D-06 |
| 5 | etudiants | Modalités de genre non harmonisées (casse, espaces, accents, abréviations ; ETU-12) | 407 | Recodage vers F / M | D-06 |
| 6 | etudiants | Modalités de boursier non harmonisées (casse, espaces, accents, abréviations ; ETU-13) | 513 | Recodage vers Oui / Non | D-06, D-11 |
| 7 | etudiants | Modalités de filiere non harmonisées (casse, espaces, accents, abréviations ; ETU-14) | 458 | Recodage vers Informatique / Gestion / Droit / Génie civil / Communication | D-06 |
| 8 | etudiants | Modalités de mention_bac non harmonisées (casse, espaces, accents, abréviations ; ETU-15) | 349 | Recodage vers Passable / Assez bien / Bien / Très bien | D-06 |
| 9 | etudiants | Modalités de region_origine non harmonisées (casse, espaces, accents, abréviations ; ETU-16) | 256 | Recodage vers les 14 régions officielles | D-06 |
| 10 | etudiants | Modalités de emploi_parallele non harmonisées (casse, espaces, accents, abréviations ; aucune anomalie à l'audit) | 0 | Recodage vers Oui / Non | D-06 |
| 11 | etudiants | age écrit avec son unité (ex. « 19 ans », ETU-17) | 46 | Unité retirée | D-06 |
| 12 | etudiants | note_bac écrit avec une virgule décimale (ETU-20) | 250 | Virgule remplacée par un point | D-06 |
| 13 | etudiants | distance_campus_km écrit avec une virgule décimale (ETU-22) | 197 | Virgule remplacée par un point | D-06 |
| 14 | etudiants | distance_campus_km écrit avec son unité (ex. « 11.8 km », ETU-23) | 41 | Unité retirée | D-06 |
| 15 | etudiants | age hors [17 ; 35] (sentinelle 99 comprise ; ETU-18, ETU-19) | 14 | age mis à manquant, ligne conservée | D-08 |
| 16 | etudiants | note_bac hors [10 ; 20] (ETU-21) | 18 | note_bac mis à manquant, ligne conservée | D-08 |
| 17 | etudiants | distance_campus_km négative ou nulle, ou sentinelle 9999 (ETU-24, ETU-25) | 25 | distance_campus_km mis à manquant, ligne conservée | D-09 |
| 18 | etudiants | Ligne strictement identique à une ligne précédente (après harmonisation, ETU-05, ETU-06) | 61 | Ligne supprimée | D-06 |
| 19 | etudiants | Même étudiant présent deux fois avec une distance différente (ETU-07) | 24 | Première ligne du fichier gardée, l'autre supprimée | D-07 |
| 20 | etudiants | mention_bac en contradiction avec note_bac (ETU-27 ; une note de 12, 14 ou 16 tout rond est tranchée par D-10) | 46 | Mention recalculée à partir de la note | D-10 |
| 21 | etudiants | mention_bac vide alors que note_bac est connue (ETU-09) | 150 | Mention calculée à partir de la note | D-10 |
| 22 | inscriptions | Identifiant en minuscules ou entouré d'espaces | 0 | Mis en majuscules, espaces retirés | D-12 |
| 23 | inscriptions | statut_final écrit de plusieurs façons (casse, espaces, accents, INS-04) | 400 | Recodage vers inscrit / abandon / transfert | D-12 |
| 24 | inscriptions | date_debut dans un autre format que AAAA-MM-JJ (JJ/MM/AAAA, AAAA/MM/JJ, « 7 oct. 2024 » ; INS-05) | 1300 | Date convertie en AAAA-MM-JJ | D-12 |
| 25 | inscriptions | date_fin dans un autre format que AAAA-MM-JJ (JJ/MM/AAAA, AAAA/MM/JJ, « 7 oct. 2024 » ; INS-06) | 289 | Date convertie en AAAA-MM-JJ | D-12 |
| 26 | inscriptions | Inscription strictement identique à une ligne précédente (INS-01, INS-02) | 20 | Ligne supprimée | D-12 |
| 27 | inscriptions | date_fin antérieure à date_debut, date_fin égale à la rentrée de la cohorte (INS-07, INS-08, INS-09, INS-10) | 12 | date_debut et date_fin échangées | D-13 |
| 28 | inscriptions | Inscription d'un identifiant absent de etudiants (X-01) | 14 | Ligne retirée et conservée dans data/processed/rejets/inscriptions_sans_etudiant.csv | D-17 |
| 29 | inscriptions | Contrôle : date_debut différente de la rentrée de référence, ou année universitaire différente de la cohorte | 0 | Aucun écart après échange des dates inversées : rien à corriger | D-13, D-17 |
| 30 | inscriptions | Étudiant sans aucune inscription (X-03) | 10 | Inscription ajoutée : année et rentrée de sa cohorte, statut et date_fin vides | D-17 |
| 31 | inscriptions | Abandon daté après la fin du suivi (date_fin ≥ date_debut + 30 semaines, INS-11) | 6 | sortie_suivi = aucune_sortie_declaree, ligne gardée, drapeau abandon_hors_suivi | D-14 |
| 32 | inscriptions | statut_final vide (INS-03) | 40 | sortie_suivi = aucune_sortie_declaree, statut laissé vide, drapeau statut_vide | D-15 |
| 33 | inscriptions | Abandon sans date_fin (INS-12) | 22 | sortie_suivi = abandon, date_fin laissée vide (semaine à déterminer en DA-07), drapeau abandon_sans_date | D-16 |
| 34 | activite_hebdo | Identifiant en minuscules (ACT-01) | 1310 | Mis en majuscules | D-19 |
| 35 | activite_hebdo | nb_connexions_lms entier écrit « 10.0 » (ACT-12) | 129669 | Converti en entier | D-19 |
| 36 | activite_hebdo | note_moyenne écrit avec une virgule décimale (ACT-09) | 1703 | Virgule remplacée par un point | D-19 |
| 37 | activite_hebdo | semaine hors [1 ; 30] (valeurs −1, 0, 31, 32, 99 ; ACT-06, ACT-07) | 70 | Ligne retirée, conservée dans rejets/activite_semaine_invalide.csv (aucune semaine à combler chez ces étudiants) | D-19 |
| 38 | activite_hebdo | nb_connexions_lms négatif ou > 100 (ACT-13, ACT-14) | 57 | nb_connexions_lms mis à manquant, ligne conservée | D-19 |
| 39 | activite_hebdo | devoirs_rendus hors [0 ; 2] (ACT-08) | 30 | devoirs_rendus mis à manquant, ligne conservée | D-19 |
| 40 | activite_hebdo | note_moyenne = −1, valeur sentinelle (ACT-10) | 25 | note_moyenne mis à manquant, ligne conservée | D-19 |
| 41 | activite_hebdo | note_moyenne > 20 (entre 34,4 et 163,6 ; virgule décalée, ACT-11) | 110 | Note divisée par 10 | D-21 : après division, moyenne 10.42 et écart-type 2.50, comme les notes valides (10.40 et 2.43) |
| 42 | activite_hebdo | Ligne strictement identique à une ligne précédente (ACT-02, ACT-03 ; plus nombreuses qu'à l'audit car certaines copies deviennent identiques après les règles 3 à 5) | 890 | Ligne supprimée | D-19 |
| 43 | activite_hebdo | Même (étudiant, semaine) avec des valeurs différentes (ACT-04) : 340 lignes pour 170 couples | 170 | Fusion en une ligne : connexions et devoirs = maximum, note et absences = première ligne | D-20 |
| 44 | activite_hebdo | dont couples où une copie indique 0 connexion et l'autre une activité | 11 | Activité gardée (maximum) : évite un faux jour d'inactivité | D-20 |
| 45 | activite_hebdo | Activité après la semaine de sortie déclarée (34 étudiants ; X-06, X-07) | 54 | Ligne retirée, conservée dans rejets/activite_apres_sortie.csv | D-22, D-23 |
| 46 | tutorat | En-tête « ID Etudiant » au lieu de id_etudiant (TUT-01) | 1 | Renommé en id_etudiant | D-24 |
| 47 | tutorat | Identifiant en minuscules ou entouré d'espaces | 0 | Mis en majuscules, espaces retirés | D-24 |
| 48 | tutorat | type_tuteur écrit de plusieurs façons (« pair (étudiant avancé) », « PAIR », « Prof »…, TUT-05) | 880 | Recodage vers pair / enseignant | D-24 |
| 49 | tutorat | motif_orientation hors des 4 valeurs du LISEZMOI | 0 | Recodage vers notes faibles / absences répétées / signalement enseignant / demande personnelle | D-24 |
| 50 | tutorat | nb_seances entier écrit « -2.0 » ou « 0.0 » (TUT-07) | 17 | Converti en entier | D-24 |
| 51 | tutorat | nb_seances nul ou négatif (0, −2 ; TUT-08) | 17 | nb_seances mis à manquant, drapeau nb_seances_invalide, étudiant gardé tutoré | D-24 |
| 52 | tutorat | Ligne de tutorat strictement identique à une ligne précédente (TUT-02, TUT-03, X-10) | 30 | Ligne supprimée | D-24 |
| 53 | tutorat | Tutorat d'un identifiant absent de etudiants (X-02) | 6 | Ligne retirée, conservée dans rejets/tutorat_sans_etudiant.csv | D-24 |
| 54 | tutorat | Tutorat commencé après la semaine 30 (45, 52 ; TUT-09) | 5 | Valeur gardée, drapeau debut_hors_suivi (non tutoré pendant le suivi) | D-25 |
| 55 | tutorat | Tutorat commencé en « semaine 0 » (TUT-06) | 5 | semaine_debut mise à manquant, drapeau debut_semaine_invalide, étudiant gardé tutoré | D-26 |
| 56 | tutorat | Tutorat commencé après la semaine de sortie déclarée (X-08) | 9 | Valeur gardée, drapeau debut_apres_sortie (non tutoré pendant son suivi) | D-22, D-27 |
| 57 | messages | Contrôle de structure : id_message unique, id_etudiant connu, semaine dans [1 ; 30], canal autorisé | 0 | Aucun écart : rien à corriger | D-18 |
| 58 | messages | Accents cassés (« Ã© » pour « é », MSG-01) | 40 | Texte réparé (conversion cp1252 -> UTF-8 refaite) | D-28 |
| 59 | messages | Message vide ou sans aucun mot (« », « . », espaces ; MSG-02, MSG-03) | 25 | Message retiré, conservé dans rejets/messages_vides.csv | D-29 |
| 60 | messages | Adresse e-mail dans le texte (MSG-06) | 33 | Remplacée par [EMAIL] | D-28 |
| 61 | messages | Numéro de téléphone sénégalais dans le texte (MSG-05) | 45 | Remplacé par [TEL] | D-28 |
| 62 | messages | Prénom et nom introduits par « c'est » ou « je suis » (MSG-04) | 96 | Nom remplacé par [NOM] (ex. « Bonjour, c'est [NOM]. ») | D-28 |
| 63 | messages | Messages contenant au moins une donnée personnelle (synthèse) | 129 | Pseudonymisés ; aucune table de correspondance conservée ; contrôle résiduel : 0 reste | D-28 |

## Anomalies constatées sans traitement

| Code | Raison |
|---|---|
| ETU-08 | valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : pas d'imputation dans les tables nettoyées) |
| ETU-10 | valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : pas d'imputation dans les tables nettoyées) |
| ETU-11 | valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : pas d'imputation dans les tables nettoyées) |
| ACT-05 | valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : pas d'imputation dans les tables nettoyées) |
| TUT-04 | valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : pas d'imputation dans les tables nettoyées) |
| ETU-26 | distances > 51,7 km conservées, toutes hors Dakar et plausibles (D-09) |
| X-04 | étudiants sans sortie déclarée dont l'activité s'arrête avant la semaine 30 — lecture renvoyée à DA-07 |
| X-05 | arrêt de l'activité après une sortie déclarée — situation normale, pas une anomalie |
| X-09 | messages après la sortie — disparus après la correction des dates inversées (D-13), 0 restant |
| MSG-07 | synthèse de MSG-04 à MSG-06 (un message peut contenir plusieurs données personnelles) |

## Tableau avant / après

#### `etudiants`

| Indicateur | Avant | Après |
|---|---:|---:|
| Lignes | 5085 | 5000 |
| Étudiants distincts | 5000 | 5000 |
| Doublons de la clé (id_etudiant ; identifiant en majuscules, sans espaces) | 85 | 0 |
| Valeurs manquantes : id_etudiant | 0 | 0 |
| Valeurs manquantes : cohorte | 0 | 0 |
| Valeurs manquantes : genre | 0 | 0 |
| Valeurs manquantes : age | 72 | 84 |
| Valeurs manquantes : boursier | 0 | 0 |
| Valeurs manquantes : filiere | 0 | 0 |
| Valeurs manquantes : mention_bac | 154 | 0 |
| Valeurs manquantes : note_bac | 0 | 18 |
| Valeurs manquantes : region_origine | 91 | 90 |
| Valeurs manquantes : distance_campus_km | 0 | 25 |
| Valeurs manquantes : emploi_parallele | 205 | 200 |
| Valeurs manquantes : total (colonnes d'origine) | 522 | 417 |

#### `inscriptions`

| Indicateur | Avant | Après |
|---|---:|---:|
| Lignes | 5024 | 5000 |
| Étudiants distincts | 5004 | 5000 |
| Doublons de la clé (id_etudiant ; identifiant en majuscules, sans espaces) | 20 | 0 |
| Valeurs manquantes : id_etudiant | 0 | 0 |
| Valeurs manquantes : annee_universitaire | 0 | 0 |
| Valeurs manquantes : date_debut | 0 | 0 |
| Valeurs manquantes : date_fin | 3890 | 3873 |
| Valeurs manquantes : statut_final | 41 | 50 |
| Cases vides : sortie_suivi (colonne créée) | — | 0 |
| Cases vides : drapeau_inscription (colonne créée) | — | 4910 |
| Valeurs manquantes : total (colonnes d'origine) | 3931 | 3923 |

Effectifs de `sortie_suivi` :

| Valeur | Effectif |
|---|---:|
| abandon | 1026 |
| transfert | 117 |
| aucune_sortie_declaree | 3857 |

Effectifs de `drapeau_inscription` :

| Valeur | Effectif |
|---|---:|
| dates_inversees | 12 |
| abandon_hors_suivi | 6 |
| statut_vide | 40 |
| abandon_sans_date | 22 |
| inscription_reconstituee | 10 |

#### `activite_hebdo`

| Indicateur | Avant | Après |
|---|---:|---:|
| Lignes | 130967 | 129783 |
| Étudiants distincts | 5000 | 5000 |
| Doublons de la clé (id_etudiant, semaine ; identifiant en majuscules, sans espaces) | 1060 | 0 |
| Valeurs manquantes : id_etudiant | 0 | 0 |
| Valeurs manquantes : semaine | 0 | 0 |
| Valeurs manquantes : nb_connexions_lms | 1298 | 1348 |
| Valeurs manquantes : devoirs_rendus | 0 | 29 |
| Valeurs manquantes : note_moyenne | 73574 | 72911 |
| Valeurs manquantes : absences | 0 | 0 |
| Valeurs manquantes : total (colonnes d'origine) | 74872 | 74288 |

#### `tutorat`

| Indicateur | Avant | Après |
|---|---:|---:|
| Lignes | 1291 | 1255 |
| Étudiants distincts | 1261 | 1255 |
| Doublons de la clé (id_etudiant ; identifiant en majuscules, sans espaces) | 30 | 0 |
| Valeurs manquantes : id_etudiant | 0 | 0 |
| Valeurs manquantes : semaine_debut | 0 | 5 |
| Valeurs manquantes : nb_seances | 8 | 25 |
| Valeurs manquantes : type_tuteur | 0 | 0 |
| Valeurs manquantes : motif_orientation | 0 | 0 |
| Cases vides : drapeau_tutorat (colonne créée) | — | 1220 |
| Valeurs manquantes : total (colonnes d'origine) | 8 | 30 |

Effectifs de `type_tuteur` :

| Valeur | Effectif |
|---|---:|
| pair | 831 |
| enseignant | 424 |

Effectifs de `drapeau_tutorat (par drapeau)` :

| Valeur | Effectif |
|---|---:|
| nb_seances_invalide | 17 |
| debut_hors_suivi | 5 |
| debut_semaine_invalide | 5 |
| debut_apres_sortie | 9 |

Effectifs de `drapeau_tutorat (par valeur de la colonne)` :

| Valeur | Effectif |
|---|---:|
| nb_seances_invalide | 17 |
| debut_apres_sortie | 8 |
| debut_semaine_invalide | 5 |
| debut_hors_suivi | 4 |
| debut_hors_suivi;debut_apres_sortie | 1 |

#### `messages`

| Indicateur | Avant | Après |
|---|---:|---:|
| Lignes | 3200 | 3175 |
| Étudiants distincts | 2273 | 2258 |
| Doublons de la clé (id_message ; identifiant en majuscules, sans espaces) | 0 | 0 |
| Valeurs manquantes : id_message | 0 | 0 |
| Valeurs manquantes : id_etudiant | 0 | 0 |
| Valeurs manquantes : semaine | 0 | 0 |
| Valeurs manquantes : canal | 0 | 0 |
| Valeurs manquantes : texte | 18 | 0 |
| Valeurs manquantes : total (colonnes d'origine) | 18 | 0 |

Effectifs de `balises dans texte` :

| Valeur | Effectif |
|---|---:|
| [EMAIL] | 33 |
| [TEL] | 45 |
| [NOM] | 96 |
