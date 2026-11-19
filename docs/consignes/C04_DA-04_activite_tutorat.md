# Consigne C04 — DA-04 : nettoyage des tables « activite_hebdo » et « tutorat » (issue #7)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C02 et C03 terminées (cette consigne lit `data/processed/etudiants.csv` et `data/processed/inscriptions.csv`).

## Contexte
Lis `CLAUDE.md`, `docs/audit_qualite.md` (sections `activite_hebdo`, `tutorat`, contrôles X-02 et X-04 à X-10) et **les décisions D-19 à D-27 de `docs/decisions.md`**, validées par Saliou.
Périmètre : **DA-04 uniquement**. Ajouter `src/nettoyage/activite.py` et `src/nettoyage/tutorat.py`, les brancher dans `python -m src.nettoyage`, réutiliser `commun.py`.
Principe validé par Saliou (D-18) : **pas de règle pour une anomalie absente des données**. Un cas imprévu → arrêt avec un message en français, pas de traitement en silence.

## Outil commun à ajouter dans `commun.py`
`semaine_depuis_date(date, date_debut)` = (date − date_debut en jours) // 7 + 1 (D-22). Sera réutilisé en DA-07. Semaine de sortie d'un étudiant = cette fonction appliquée à `date_fin` quand `sortie_suivi` vaut `abandon` ou `transfert` et que `date_fin` est renseignée ; sinon pas de semaine de sortie.

## Table `activite_hebdo` — règles, dans cet ordre
1. **Identifiants** : majuscules, sans espaces ; format `HZ` + 5 chiffres ; identifiant absent de `etudiants.csv` → s'arrêter et signaler.
2. **Nombres** (D-19) : virgule → point ; conversion numérique ; `semaine`, `nb_connexions_lms`, `devoirs_rendus`, `absences` en entiers (type entier acceptant les manquants). Un entier avec une vraie partie décimale (ex. 3.5 connexions) → s'arrêter et signaler.
3. **Semaines invalides** (D-19) : lignes avec `semaine` hors [1 ; 30] → retirées et écrites dans `data/processed/rejets/activite_semaine_invalide.csv`. **Contrôle** : si l'étudiant concerné a une semaine manquante entre 1 et sa semaine de sortie (ou 30), s'arrêter et signaler (la ligne aurait pu la combler).
4. **Valeurs impossibles → manquant** (D-19) : `nb_connexions_lms` < 0 ou > 100 ; `devoirs_rendus` hors [0 ; 2] ; `note_moyenne` = −1. Les connexions de 21 à 26 restent telles quelles.
5. **Notes décalées** (D-21) : `note_moyenne` > 20 → divisée par 10. Ensuite, toute note hors [0 ; 20] → s'arrêter et signaler. Justification dans le journal : la distribution après division (moyenne 10,42, écart-type 2,50) est celle des notes valides (10,40 et 2,43) ; ces deux chiffres sont **calculés par le code**.
6. **Doublons** (D-19, D-20), après les étapes 1 à 5 :
   - lignes strictement identiques → une seule gardée ;
   - même (étudiant, semaine) avec des valeurs différentes → une ligne : `nb_connexions_lms` et `devoirs_rendus` = la plus grande valeur renseignée ; `note_moyenne` et `absences` = celles de la première ligne du fichier. Si `absences` diffère entre les copies → s'arrêter et signaler. Compter à part les couples où une copie disait 0 connexion et l'autre plus.
7. **Activité après la sortie** (D-22, D-23) : lignes dont `semaine` > semaine de sortie → retirées et écrites dans `data/processed/rejets/activite_apres_sortie.csv`.
- Ne **pas** combler les semaines absentes ni les valeurs manquantes : leur lecture (inactivité ou donnée manquante) est un point de DA-07.

## Table `tutorat` — règles, dans cet ordre
1. **En-tête et identifiants** (D-24) : `ID Etudiant` → `id_etudiant` ; majuscules, sans espaces ; format `HZ` + 5 chiffres.
2. **Modalités** (D-24), forme simplifiée comme pour `etudiants` : `type_tuteur` → `pair` (pair, pair (etudiant avance), etudiant) ou `enseignant` (enseignant, prof) ; `motif_orientation` doit être l'une des 4 valeurs du LISEZMOI. Valeur imprévue → s'arrêter et signaler.
3. **Nombres** : `semaine_debut` et `nb_seances` en entiers (« -2.0 » → −2).
4. **Séances** (D-24) : `nb_seances` ≤ 0 → manquant, drapeau `nb_seances_invalide`.
5. **Doublons exacts** (D-24), après les étapes 1 à 4 : une ligne par étudiant ; s'il reste deux lignes différentes pour un étudiant → s'arrêter et signaler.
6. **Orphelins** (D-24) : identifiant absent de `etudiants.csv` → retiré, écrit dans `data/processed/rejets/tutorat_sans_etudiant.csv`.
7. **Semaine de début** : > 30 → valeur gardée, drapeau `debut_hors_suivi` (D-25) ; ≤ 0 → manquant, drapeau `debut_semaine_invalide` (D-26).
8. **Après la sortie** (D-27) : `semaine_debut` > semaine de sortie → valeur gardée, drapeau `debut_apres_sortie`.
- Colonne `drapeau_tutorat` : vide ou liste de drapeaux séparés par `;`. Ne **pas** créer ici de colonne « tutoré pendant le suivi » : le traitement sera construit en DA-07, à partir de T.

## Sorties
- `data/processed/activite_hebdo.csv` et `data/processed/tutorat.csv` (UTF-8, `,`, sans index) + les 3 fichiers de rejets.
- `docs/journal_nettoyage.md` régénéré : une ligne par règle (justification = numéro de décision et anomalie de l'audit), tableaux avant / après des deux tables, effectifs de chaque drapeau.

## Tests
`tests/test_nettoyage_activite.py` et `tests/test_nettoyage_tutorat.py` :
- unitaires : `semaine_depuis_date` (rentrée → 1 ; rentrée + 6 jours → 1 ; rentrée + 7 jours → 2) ; semaine 99 retirée ; contrôle « semaine manquante » qui s'arrête ; connexions −3 et 6 076 → manquant, 26 gardé ; devoirs 7 → manquant ; note −1 → manquant ; note 122 → 12,2 ; quasi-doublon 0 / 5 connexions → 5 ; activité après la sortie retirée ; « pair (étudiant avancé) » → pair ; « Prof » → enseignant ; type inconnu → erreur ; nb_seances 0 → manquant + drapeau ; semaine_debut 52 → gardée + drapeau ; 0 → manquant + drapeau ; début après la sortie → drapeau ; orphelin retiré ;
- invariants (ignorés si les fichiers n'existent pas) : activite — couple (étudiant, semaine) unique, semaine dans [1 ; 30], connexions dans [0 ; 100], devoirs dans [0 ; 2], note dans [0 ; 20], absences dans [0 ; 20], aucune ligne après la semaine de sortie, identifiants tous dans `etudiants.csv` ; tutorat — une ligne par étudiant, identifiants dans `etudiants.csv`, type_tuteur et motif dans les listes, nb_seances ≥ 1 ou manquant, semaine_debut dans [1 ; 30] sauf drapeau `debut_hors_suivi`.

## Contrôles attendus
Prototype de la session de pilotage sur les données (en cas d'écart, le signaler et l'expliquer, sans forcer le code) — aucun arrêt ne devrait se déclencher :
- `activite_hebdo` : 130 967 lignes → 70 lignes à semaine invalide retirées (aucune n'a de semaine à combler) → connexions mises à manquant 57 (45 négatives, 12 > 100), devoirs 30, notes −1 25 → notes divisées par 10 : 110 → 890 lignes identiques supprimées (plus que les 883 de l'audit : certaines copies deviennent identiques après les étapes 3 à 5) → 170 couples fusionnés (340 lignes → 170) → 54 lignes après la sortie retirées (34 étudiants) → **129 783 lignes**, 5 000 étudiants ; manquants : connexions 1 348, devoirs 29, notes 72 911 (semaines sans évaluation : normal).
- `tutorat` : 1 291 lignes → 880 type_tuteur recodés → 17 nb_seances mis à manquant → 30 doublons supprimés → 6 orphelins retirés → **1 255 lignes** (pair 831, enseignant 424) ; drapeaux : nb_seances_invalide 17, debut_hors_suivi 4, debut_semaine_invalide 5, debut_apres_sortie 8, « debut_hors_suivi;debut_apres_sortie » 1.

## Livraison
- Deux commits : `DA-04 : nettoyage de la table activite_hebdo (#7)` puis `DA-04 : nettoyage de la table tutorat (#7)` ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus.
