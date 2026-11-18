# Journal de nettoyage

> Fichier généré par `python -m src.nettoyage` — ne pas modifier à la main.
> Chaque traitement applique une décision validée par Saliou (`docs/decisions.md`).
> Les numéros d'anomalie « ETU-xx » renvoient à `docs/audit_qualite.md`.

## Traitements appliqués

| # | Table | Anomalie constatée | Lignes | Traitement appliqué | Justification |
|---:|---|---|---:|---|---|
| 1 | etudiants | En-tête entouré d'espaces (« id_etudiant  », ETU-01) | 1 | Espaces retirés | D-06 |
| 2 | etudiants | En-tête nommé autrement que dans le LISEZMOI (« Distance campus (km) », ETU-02) | 1 | Renommé en distance_campus_km | D-06 |
| 3 | etudiants | Identifiant entouré d'espaces (ETU-03) | 12 | Espaces retirés | D-06 |
| 4 | etudiants | Identifiant en minuscules (ETU-04) | 13 | Mis en majuscules | D-06 |
| 5 | etudiants | Modalités de genre non harmonisées (casse, espaces, accents, abréviations) | 407 | Recodage vers F / M | D-06 |
| 6 | etudiants | Modalités de boursier non harmonisées (casse, espaces, accents, abréviations) | 513 | Recodage vers Oui / Non | D-06, D-11 |
| 7 | etudiants | Modalités de filiere non harmonisées (casse, espaces, accents, abréviations) | 458 | Recodage vers Informatique / Gestion / Droit / Génie civil / Communication | D-06 |
| 8 | etudiants | Modalités de mention_bac non harmonisées (casse, espaces, accents, abréviations) | 349 | Recodage vers Passable / Assez bien / Bien / Très bien | D-06 |
| 9 | etudiants | Modalités de region_origine non harmonisées (casse, espaces, accents, abréviations) | 256 | Recodage vers les 14 régions officielles | D-06 |
| 10 | etudiants | Modalités de emploi_parallele non harmonisées (casse, espaces, accents, abréviations) | 0 | Recodage vers Oui / Non | D-06 |
| 11 | etudiants | age écrit avec son unité (ex. « 19 ans ») | 46 | Unité retirée | D-06 |
| 12 | etudiants | note_bac écrit avec une virgule décimale | 250 | Virgule remplacée par un point | D-06 |
| 13 | etudiants | distance_campus_km écrit avec une virgule décimale | 197 | Virgule remplacée par un point | D-06 |
| 14 | etudiants | distance_campus_km écrit avec son unité (ex. « 11.8 km ») | 41 | Unité retirée | D-06 |
| 15 | etudiants | age hors [17 ; 35] (sentinelle 99 comprise) | 14 | age mis à manquant, ligne conservée | D-08 |
| 16 | etudiants | note_bac hors [10 ; 20] | 18 | note_bac mis à manquant, ligne conservée | D-08 |
| 17 | etudiants | distance_campus_km négative ou nulle, ou sentinelle 9999 | 25 | distance_campus_km mis à manquant, ligne conservée | D-09 |
| 18 | etudiants | Ligne strictement identique à une ligne précédente (après harmonisation, ETU-05, ETU-06) | 61 | Ligne supprimée | D-06 |
| 19 | etudiants | Même étudiant présent deux fois avec une distance différente (ETU-07) | 24 | Première ligne du fichier gardée, l'autre supprimée | D-07 |
| 20 | etudiants | mention_bac en contradiction avec note_bac (ETU-27 ; une note de 12, 14 ou 16 tout rond est tranchée par D-10) | 46 | Mention recalculée à partir de la note | D-10 |
| 21 | etudiants | mention_bac vide alors que note_bac est connue | 150 | Mention calculée à partir de la note | D-10 |
| 22 | inscriptions | Identifiant en minuscules ou entouré d'espaces | 0 | Mis en majuscules, espaces retirés | D-12 |
| 23 | inscriptions | statut_final écrit de plusieurs façons (casse, espaces, accents, INS-04) | 400 | Recodage vers inscrit / abandon / transfert | D-12 |
| 24 | inscriptions | date_debut dans un autre format que AAAA-MM-JJ (JJ/MM/AAAA, AAAA/MM/JJ, « 7 oct. 2024 ») | 1300 | Date convertie en AAAA-MM-JJ | D-12 |
| 25 | inscriptions | date_fin dans un autre format que AAAA-MM-JJ (JJ/MM/AAAA, AAAA/MM/JJ, « 7 oct. 2024 ») | 289 | Date convertie en AAAA-MM-JJ | D-12 |
| 26 | inscriptions | Inscription strictement identique à une ligne précédente (INS-01, INS-02) | 20 | Ligne supprimée | D-12 |
| 27 | inscriptions | date_fin antérieure à date_debut, date_fin égale à la rentrée de la cohorte (INS-07, INS-09, INS-10) | 12 | date_debut et date_fin échangées | D-13 |
| 28 | inscriptions | Inscription d'un identifiant absent de etudiants (X-01) | 14 | Ligne retirée et conservée dans data/processed/rejets/inscriptions_sans_etudiant.csv | D-17 |
| 29 | inscriptions | Contrôle : date_debut différente de la rentrée de référence, ou année universitaire différente de la cohorte | 0 | Aucun écart après échange des dates inversées : rien à corriger | D-13, D-17 |
| 30 | inscriptions | Étudiant sans aucune inscription (X-03) | 10 | Inscription ajoutée : année et rentrée de sa cohorte, statut et date_fin vides | D-17 |
| 31 | inscriptions | Abandon daté après la fin du suivi (date_fin ≥ date_debut + 30 semaines, INS-11) | 6 | sortie_suivi = aucune_sortie_declaree, ligne gardée, drapeau abandon_hors_suivi | D-14 |
| 32 | inscriptions | statut_final vide (INS-03) | 40 | sortie_suivi = aucune_sortie_declaree, statut laissé vide, drapeau statut_vide | D-15 |
| 33 | inscriptions | Abandon sans date_fin (INS-12) | 22 | sortie_suivi = abandon, date_fin laissée vide (semaine à déterminer en DA-07), drapeau abandon_sans_date | D-16 |

## Tableau avant / après

#### `etudiants`

| Indicateur | Avant | Après |
|---|---:|---:|
| Lignes | 5085 | 5000 |
| Doublons d'identifiant (majuscules, sans espaces) | 85 | 0 |
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
| Doublons d'identifiant (majuscules, sans espaces) | 20 | 0 |
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
