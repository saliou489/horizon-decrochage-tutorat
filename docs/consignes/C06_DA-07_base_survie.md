# Consigne C06 — DA-07 : construire T et E, base_survie.csv et le format période-personne (issue #10)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C02 à C05 terminées.

## Contexte
Lis `CLAUDE.md` (§5 surtout), le cahier des charges (§4.3, F1) et **les décisions D-22, D-25 à D-27 et D-30 à D-39 de `docs/decisions.md`**, validées par Saliou. Elles tranchent tous les points ouverts du §5 de CLAUDE.md. Principe D-18 : cas imprévu → arrêt avec un message en français.
Périmètre : DA-07 + le notebook `01_nettoyage` (présentation du nettoyage et de la construction de T et E, jalon M1). Pas d'analyse exploratoire (DA-08) ni de survie (SV-01).

## Partie A — `src/base_survie.py` (tâche DA-07)
Fonctions courtes, docstrings en français, paramètres dans `config.py` (`SEUIL_INACTIVITE = 4`, `SEUILS_SENSIBILITE = (3, 5)`, `N_SEMAINES = 30`) :
1. **État d'une semaine** (D-31) : `actif` si connexions > 0 ou devoirs > 0 ; `inactif` si connexions = 0 et devoirs = 0 ; `inconnu` sinon (une des deux valeurs manque et l'autre ne montre aucune activité).
2. **Première série d'inactivité** : première semaine d'une suite de `seuil` semaines consécutives `inactif`. Option `lecture_inconnu` : `"active"` (référence, D-31 : une semaine inconnue coupe la série) ou `"inactive"` (sensibilité).
3. **T et E par étudiant** (D-30, D-32 à D-35), avec une colonne `type_evenement` :
   | Situation (inscriptions nettoyées + activité) | T | E | type_evenement |
   |---|---|---|---|
   | `sortie_suivi` = abandon avec date | semaine de sortie (D-22) | 1 | `abandon_declare` |
   | abandon sans date (D-16, D-32) | dernière semaine d'activité | 1 | `abandon_sans_date` |
   | drapeau `abandon_hors_suivi` (D-33) | dernière semaine d'activité | 1 | `abandon_date_invalide` |
   | `sortie_suivi` = transfert | semaine du transfert | 0 | `transfert` |
   | aucune sortie, série d'inactivité trouvée | 1ʳᵉ semaine de la série | 1 | `decrochage_silencieux` |
   | aucune sortie, pas de série, activité arrêtée avant 30 (D-34) | dernière semaine d'activité | 0 | `perdu_de_vue` |
   | aucune sortie, pas de série, activité jusqu'à 30 | 30 | 0 | `fin_de_suivi` |
   - Pour D-33 : si un étudiant `abandon_hors_suivi` avait une série d'inactivité, ou une activité jusqu'à la semaine 30 → s'arrêter et signaler (cas absent).
   - Série d'inactivité **avant** une sortie déclarée (abandon ou transfert) → s'arrêter et signaler (D-30, cas absent).
   - Une semaine manquante entre 1 et T → s'arrêter et signaler (aucune dans les données).
4. **Tutorat** (D-37), à partir de `data/processed/tutorat.csv` et du T de référence : `statut_tutorat` ∈ {`non_tutore`, `tutore` (début < T), `tutorat_meme_semaine_que_T`, `tutorat_apres_T`, `tutorat_semaine_inconnue`} ; `tutore` = 1 pour `tutore` et `tutorat_semaine_inconnue`, 0 sinon ; `semaine_debut_tutorat` = valeur de la table tutorat (vide si pas de tutorat ou semaine inconnue).
5. **`data/processed/base_survie.csv`** (D-36, D-38), une ligne par étudiant de `etudiants.csv`, colonnes dans cet ordre : `id_etudiant`, `cohorte`, `genre`, `age`, `boursier`, `filiere`, `mention_bac`, `note_bac`, `region_origine`, `distance_campus_km`, `emploi_parallele`, `T`, `E`, `type_evenement`, `T_seuil3`, `E_seuil3`, `T_seuil5`, `E_seuil5`, `tutore`, `statut_tutorat`, `semaine_debut_tutorat`, `type_tuteur`, `motif_orientation`, `nb_seances`. **Aucune** variable calculée sur l'activité de tout le suivi (D-36). Les valeurs manquantes restent manquantes.
6. **`data/processed/base_periode_personne.csv`** (D-39) : une ligne par (étudiant, semaine) pour semaine = 1 … T ; colonnes `id_etudiant`, `semaine`, `evenement` (1 seulement à la semaine T si E = 1), `nb_connexions_lms`, `devoirs_rendus`, `note_moyenne`, `absences`, `etat_activite`, `tutorat_commence` (1 si `semaine` > `semaine_debut_tutorat` pour les `tutore`, 0 pour les autres, vide pour `tutorat_semaine_inconnue`).
7. `python -m src.base_survie` écrit les deux fichiers ; `run_all.py` l'appelle après le nettoyage.

## Partie B — `notebooks/01_nettoyage.ipynb`
Il importe `src/`, relance le nettoyage et la construction de la base, puis affiche, **chaque tableau suivi d'une phrase d'interprétation pour un conseiller pédagogique** :
- le tableau avant / après des 5 tables et les fichiers de rejets ;
- le nombre de décisions appliquées (renvoi vers `docs/decisions.md` et `docs/journal_nettoyage.md`) ;
- la répartition de `type_evenement` (effectifs et %) et le taux de décrochage ;
- la sensibilité au seuil (3 / 4 / 5 semaines) et à la lecture des semaines inconnues ;
- la répartition de `statut_tutorat`.
- **Ne pas** comparer les taux de décrochage entre tutorés et non tutorés : ce serait une comparaison naïve, biaisée (temps immortel) ; elle relève de la partie causale.
- Exécuté de haut en bas sans erreur et commité avec ses sorties. Ajouter à `requirements.txt` ce qu'il faut pour exécuter les notebooks (ex. `ipykernel`, `nbconvert`, versions exactes), en le justifiant dans le compte rendu.

## Tests (`tests/test_base_survie.py`)
- Unitaires, sur des suites d'états inventées : 10 actives + 4 inactives + 16 actives → série en semaine 11 ; inactif semaines 28 à 30 seulement → pas de série (T = 30, E = 0) ; inactif, inactif, inconnu, inactif, inactif → pas de série en lecture « active », série en lecture « inactive » ; seuil 3 et 5 ; abandon daté → T = semaine de sortie ; abandon sans date → dernière semaine d'activité ; transfert → E = 0 ; perdu de vue ; série avant un abandon déclaré → erreur ; tutorat début < T, = T, > T, inconnu → bon statut.
- Invariants sur les fichiers (ignorés s'ils n'existent pas) : 5 000 lignes et mêmes identifiants que `etudiants.csv` (aucun censuré perdu) ; T dans [1 ; 30] ; E ∈ {0, 1} ; E = 1 exactement pour les types d'abandon et de décrochage ; idem pour les colonnes de sensibilité ; période-personne : nombre de lignes de chaque étudiant = T, une seule ligne `evenement` = 1 par étudiant avec E = 1 (à la semaine T), aucune pour E = 0 ; `tutorat_commence` cohérent avec `statut_tutorat`.

## Contrôles attendus
Prototype de la session de pilotage (en cas d'écart, le signaler et l'expliquer, sans forcer le code) — aucun arrêt ne devrait se déclencher :
- `type_evenement` : fin_de_suivi 3 441, abandon_declare 1 004, decrochage_silencieux 408, transfert 117, abandon_sans_date 22, abandon_date_invalide 6, perdu_de_vue 2 ;
- E = 1 : **1 440** (28,8 %) ; cohorte 2024 : 715 sur 2 495 (28,7 %) ; cohorte 2025 : 725 sur 2 505 (28,9 %) ; T moyen 24,39 ;
- sensibilité : E_seuil3 = 1 445, E_seuil5 = 1 435 ; lecture « inconnu = inactif » : E = 1 441, T ou E différent pour 20 étudiants ;
- `statut_tutorat` : non_tutore 3 745, tutore 1 199, tutorat_meme_semaine_que_T 31, tutorat_apres_T 20, tutorat_semaine_inconnue 5 ; `tutore` = 1 : **1 204** ;
- période-personne : **121 938 lignes**, 1 440 lignes `evenement` = 1, `tutorat_commence` = 1 sur 24 119 lignes, vide sur 127 lignes (les 5 tutorats à semaine inconnue).

## Livraison
- Commits : `DA-07 : construction de T, E, base_survie et période-personne (#10)` puis `DA-07 : notebook 01_nettoyage (#10)` ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus.
