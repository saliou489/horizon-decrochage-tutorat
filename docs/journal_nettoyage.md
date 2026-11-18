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
| Valeurs manquantes : total | 522 | 417 |
