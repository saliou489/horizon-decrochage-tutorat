# Consigne C03 — DA-03 : nettoyage de la table « inscriptions » (issue #6)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. **Prérequis : C02 (DA-02) terminée**, car cette consigne utilise `data/processed/etudiants.csv`.

## Contexte
Lis `CLAUDE.md`, `docs/audit_qualite.md` (section `inscriptions` et contrôles X-01, X-03) et **les décisions D-12 à D-17 de `docs/decisions.md`**, validées par Saliou.
Périmètre : **table `inscriptions` et sa cohérence avec `etudiants` uniquement** (DA-03). Réutiliser `src/nettoyage/commun.py` ; ajouter `src/nettoyage/inscriptions.py` et le brancher dans `python -m src.nettoyage`.

## Règles, dans cet ordre
1. **Identifiants** : majuscules, sans espaces ; format `HZ` + 5 chiffres, sinon s'arrêter et signaler.
2. **Statuts** (D-12) : forme simplifiée (minuscules, sans accents ni espaces superflus) puis `inscrit` / `abandon` / `transfert` (abandonne → abandon ; transfere → transfert). Une valeur imprévue → s'arrêter et signaler. Statut vide → reste vide.
3. **Dates** (D-12) : lire les 4 formats (AAAA-MM-JJ, JJ/MM/AAAA, AAAA/MM/JJ, « J mois AAAA » en français, avec ou sans point d'abréviation) ; écrire en AAAA-MM-JJ. Une date illisible → s'arrêter et signaler.
4. **Doublons exacts** (D-12), après les étapes 1 à 3 : une seule ligne par étudiant. Si un étudiant a encore deux lignes différentes → s'arrêter et signaler.
5. **Dates inversées** (D-13) : si date_fin < date_debut **et** date_fin = date de rentrée la plus fréquente de la cohorte → échanger les deux dates. Tout autre cas date_fin < date_debut → s'arrêter et signaler.
6. **Contrôle de la rentrée** : après l'étape 5, vérifier que chaque date_debut est la rentrée de sa cohorte (cohorte lue dans `etudiants`, et cohérente avec annee_universitaire). Écart → s'arrêter et signaler.
7. **Orphelins** (D-17) : inscriptions dont l'identifiant est absent de `data/processed/etudiants.csv` → retirées de la table et écrites dans `data/processed/rejets/inscriptions_sans_etudiant.csv`.
8. **Étudiants sans inscription** (D-17) : ajouter une ligne avec annee_universitaire et date_debut de leur cohorte, statut vide, date_fin vide.
9. **Colonne dérivée `sortie_suivi`** (valeurs `abandon`, `transfert`, `aucune_sortie_declaree`) :
   - abandon ou transfert avec date_fin dans le suivi (date_fin < date_debut + 30 semaines) → `abandon` / `transfert` ;
   - abandon avec date_fin au-delà du suivi (D-14) → `aucune_sortie_declaree` ;
   - abandon sans date_fin (D-16) → `abandon` (date à déterminer en DA-07) ; transfert sans date_fin → s'arrêter et signaler ;
   - inscrit, statut vide (D-15), ligne ajoutée à l'étape 8 → `aucune_sortie_declaree`.
   - `statut_final` et `date_fin` d'origine (normalisés) sont **conservés** tels quels à côté.
10. **Colonne `drapeau_inscription`** : vide, ou `dates_inversees`, `abandon_hors_suivi`, `statut_vide`, `abandon_sans_date`, `inscription_reconstituee`.

Ne pas calculer de numéro de semaine ici : la conversion date → semaine est un point ouvert de DA-07.

## Sorties
- `data/processed/inscriptions.csv` (UTF-8, `,`, sans index) : une ligne par étudiant de `etudiants.csv`, ni plus ni moins.
- `docs/journal_nettoyage.md` régénéré : une ligne par règle appliquée (justification = numéro de décision), tableau avant / après pour `inscriptions`, effectif de chaque valeur de `sortie_suivi` et de `drapeau_inscription`.

## Tests (`tests/test_nettoyage_inscriptions.py`)
- Unitaires : lecture des 4 formats de date ; échange des dates inversées ; abandon en 2027 → `aucune_sortie_declaree` ; statut vide → `aucune_sortie_declaree` ; orphelin retiré ; étudiant sans inscription ajouté avec la rentrée de sa cohorte ; statut imprévu → erreur.
- Invariants sur `data/processed/inscriptions.csv` (ignorés si absent) : mêmes identifiants que `etudiants.csv`, un par étudiant ; date_fin ≥ date_debut quand renseignée ; date_debut = rentrée de la cohorte ; `sortie_suivi` dans les 3 valeurs autorisées.

## Livraison
- Commit : `DA-03 : nettoyage de la table inscriptions (#6)` ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec : lignes avant / après, effectifs de `sortie_suivi` et de chaque drapeau.
