# Consigne C07 — Correctifs issus de la relecture RV01 (issues #9, #10, #27)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`.

## Contexte
Lis `CLAUDE.md` (§6 mis à jour), le rapport `docs/revues/RV01_nettoyage_base_survie.md` et **les décisions D-42 à D-44** de `docs/decisions.md`, validées par Saliou.
Périmètre : **uniquement les correctifs listés ci-dessous**. Aucun changement de règle de nettoyage, de T, de E ou du tutorat : `base_survie.csv` et les tables nettoyées doivent rester **identiques octet pour octet** (seul `base_periode_personne.csv` gagne des colonnes).

| Constat | Suite donnée |
|---|---|
| RV01-01 | Partie A (D-42) |
| RV01-02, RV01-03 | Partie D |
| RV01-04 | Partie B (D-43) |
| RV01-05 | **Pas ici** : sera traité dans la consigne CA-05 (statut de tutorat recalculé pour chaque variante de sensibilité) |
| RV01-06 | Partie C |
| RV01-07 | Partie B |
| RV01-08 ① | Partie C ; ② refusé (D-44), limite écrite en partie D |
| Questions de RV01 | Partie E |

## Partie A — Activité décalée (D-42) : `src/base_survie.py`
1. Dans `base_periode_personne.csv`, ajouter à la fin les colonnes `nb_connexions_lms_prec`, `devoirs_rendus_prec`, `note_moyenne_prec`, `absences_prec`, `etat_activite_prec` : valeurs de la **semaine précédente** du même étudiant ; vides en semaine 1.
2. Dans `config.py` : `COLONNES_ACTIVITE_PREC` (ces 5 colonnes), avec un commentaire qui cite D-42 : ce sont les seules colonnes d'activité utilisables dans un modèle semaine par semaine.
3. Écrire la règle dans la docstring de `construire_periode_personne`.

## Partie B — Garde-fous (D-43, RV01-07)
1. `config.COVARIABLES_RENTREE` = `["cohorte", "genre", "age", "boursier", "filiere", "mention_bac", "note_bac", "region_origine", "distance_campus_km", "emploi_parallele"]`, avec un commentaire citant D-43.
2. RV01-07 : dans `t_et_e`, **avant** de chercher la série, vérifier que les semaines de l'étudiant sont exactement 1, 2, …, dernière semaine ; sinon s'arrêter avec un message en français (D-18).

## Partie C — Tests (RV01-06, RV01-08 ①)
1. Quasi-doublon (D-20) : mettre la plus grande valeur dans la **première** copie, et ajouter un cas où une copie a une connexion manquante.
2. Test unitaire de `construire_periode_personne` sur 3 ou 4 étudiants inventés : tutoré avant T (`tutorat_commence` = 0 jusqu'à la semaine de début incluse, puis 1), tutorat la semaine de T (0 partout), semaine inconnue (vide partout), non tutoré (0 partout) ; colonnes `*_prec` décalées d'une semaine, vides en semaine 1.
3. Les 3 cas d'arrêt manquants de C06 : abandon à date invalide **avec** série ; série avant un **transfert** ; série avant un **abandon sans date**. Plus : trou de semaine après le début d'une série (RV01-07).
4. Invariants de sensibilité : pour `abandon_declare`, `abandon_sans_date`, `abandon_date_invalide` et `transfert`, `T_seuil3` = `T_seuil5` = `T` et `E_seuil3` = `E_seuil5` = `E` ; `T_seuilX` dans [1 ; 30].
5. Test de `COVARIABLES_RENTREE` : chaque colonne existe dans `data/processed/etudiants.csv` ; aucune n'est `T`, `E`, une colonne `*_seuil*`, ni une colonne de tutorat.
6. **Données d'exemple inventées** (RV01-08 ①) : remplacer **tous** les noms de personnes des tests et des commentaires (`tests/`, `src/config.py`…) par des noms manifestement inventés, par exemple « Prénom Testnom » ou « Fatou Exemple », et les numéros de téléphone d'exemple par la forme `77 000 00 00`. Vérifier par une recherche qu'aucun nom d'exemple n'apparaît dans `data/raw/` (sans jamais afficher le contenu des messages).
7. **Contrôle des tests par mutation** (comme le relecteur) : sur une copie de travail, refaire les deux mutations de RV01-06 (`"max"` → `"last"` dans la fusion des quasi-doublons ; `>` → `>=` pour `tutorat_commence`) et vérifier que **chacune fait échouer au moins un test** ; annuler ensuite les mutations. Rapporter le résultat.

## Partie D — README (RV01-02, RV01-03, D-44) — tâche DO-01, issue #27
1. Section **« Installation et exécution »** : prérequis Python 3.12 ou plus (D-05) ; création et activation du `.venv` sous Windows et sous Linux / macOS (commandes du §4 de `CLAUDE.md`) ; `pip install -r requirements.txt` ; `python run_all.py` (durée indicative mesurée) ; `pytest` ; exécution d'un notebook : `jupyter nbconvert --to notebook --execute --inplace notebooks/01_nettoyage.ipynb`.
2. Section **« Données »**, avec ce texte (à recopier) :
   > Les fichiers de `data/raw/` sont un jeu **synthétique** fourni par l'enseignant : aucun étudiant réel. Les messages bruts (`data/raw/messages.csv`) contiennent des noms, e-mails et numéros de téléphone **inventés** (tous les numéros sont de la forme « 7X 000 XX XX »), laissés pour l'exercice de pseudonymisation. Ils sont conservés tels quels, car les fichiers bruts ne doivent pas être modifiés (`data/raw_sha256.txt`). Toutes les tables produites (`data/processed/`) sont pseudonymisées (`[NOM]`, `[TEL]`, `[EMAIL]`, décision D-28) et aucun texte de message n'est envoyé à un service externe.
3. Section **« Limites connues »** (D-44) : seules les dépendances directes sont figées dans `requirements.txt` ; projet testé sous Windows avec Python 3.14.3.

## Partie E — Questions de RV01
1. Première cellule de `notebooks/01_nettoyage.ipynb` : une phrase qui prévient que le notebook relance le pipeline et réécrit `data/processed/` et le journal (résultat identique à chaque exécution). Ré-exécuter le notebook et le commiter avec ses sorties.
2. Fins de ligne : le journal est déjà écrit avec `\n`, mais sous Windows git l'extrait avec `\r\n`, d'où une fausse modification après `run_all.py`. Ajouter à `.gitattributes` : `data/processed/** text eol=lf`, `docs/*.md text eol=lf` et `notebooks/*.ipynb text eol=lf`, puis `git add --renormalize .`. **Ne pas toucher** à la règle existante `data/raw/** -text`. Vérifier qu'après `python run_all.py`, `git status` est propre.

## Contrôles attendus
- `base_survie.csv` et les 5 tables nettoyées : identiques octet pour octet à avant C07 ; `data/raw/` intact.
- `base_periode_personne.csv` : toujours 121 938 lignes ; 5 colonnes de plus ; `*_prec` vides sur exactement 5 000 lignes (la semaine 1 de chaque étudiant).
- Chaque mutation de la partie C.7 fait échouer au moins un test ; `pytest` passe sur le code non modifié.
- Après `python run_all.py` : `git status` propre.

## Livraison
Trois commits, push sur `main` :
1. `DA-07 : correctifs RV01, activité décalée, garde-fous et tests (#10)` (parties A, B, C.2 à C.5, C.7) ;
2. `DA-06 : correctifs RV01, tests de nettoyage et données d'exemple inventées (#9)` (parties C.1, C.6, E.2) ;
3. `DO-01 : README, installation, données fictives et limites (RV01) (#27)` (parties D et E.1).
Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus et le résultat des mutations.
