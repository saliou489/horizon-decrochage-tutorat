# Consigne C05 — DA-05 : nettoyage et pseudonymisation de « messages » (issue #8) + DA-06 : journal complet et tests (issue #9)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C02 à C04 terminées.

## Contexte
Lis `CLAUDE.md`, `docs/audit_qualite.md` (section `messages`, contrôle X-09) et **les décisions D-28 et D-29 de `docs/decisions.md`**, validées par Saliou. Principe D-18 : pas de règle pour une anomalie absente ; cas imprévu → arrêt avec un message en français.

## Partie A — DA-05 : `src/nettoyage/messages.py`, branché dans `python -m src.nettoyage`
Règles, dans cet ordre :
1. **Contrôles de structure** : `id_message` unique ; `id_etudiant` au format `HZ` + 5 chiffres et présent dans `etudiants.csv` ; `semaine` dans [1 ; 30] ; `canal` dans {forum, formulaire de suivi}. Écart → s'arrêter et signaler (l'audit n'en a trouvé aucun).
2. **Encodage** (D-28) : textes contenant `Ã`, `Â` ou `â€` → réparés par `texte.encode("cp1252").decode("utf-8")`. Échec de réparation, ou caractère cassé restant → s'arrêter et signaler.
3. **Messages vides** (D-29) : texte sans aucun caractère alphanumérique → retiré, écrit dans `data/processed/rejets/messages_vides.csv`.
4. **Pseudonymisation** (D-28), **après** la réparation de l'encodage (sinon un nom accentué cassé ne serait pas reconnu), dans cet ordre :
   - e-mails → `[EMAIL]` ;
   - téléphones sénégalais (préfixe 70, 75, 76, 77, 78, avec ou sans +221, chiffres groupés par espaces ou points) → `[TEL]` ;
   - noms : prénom + nom (deux mots ou plus commençant par une majuscule, tirets autorisés) introduits par « c'est » ou « je suis » → seul le nom est remplacé : « Bonjour, c'est [NOM]. ».
   - Les expressions régulières vont dans `config.py`, chacune avec un commentaire qui explique ce qu'elle reconnaît.
   - **Contrôle résiduel obligatoire** après remplacement : plus aucun `@`, plus aucune suite de 8 chiffres ou plus (espaces et points ignorés), plus aucun « c'est » / « je suis » suivi de deux mots en majuscule. Reste → s'arrêter et signaler.
   - Ne conserver **aucune** table de correspondance, et ne jamais écrire un texte original (non pseudonymisé) dans un fichier, un journal ou une sortie de test. Les exemples du journal sont pris dans les textes **déjà** pseudonymisés.
5. Sortie : `data/processed/messages.csv` (mêmes colonnes, texte pseudonymisé).

## Partie B — DA-06 : journal complet
1. **Chaque ligne de traitement** du journal cite le ou les codes d'anomalie de l'audit qu'elle traite (ex. la ligne « Recodage vers F / M » cite ETU-12). Aujourd'hui, une trentaine de codes traités ne sont pas cités (ETU-12 à ETU-25, INS-05, INS-06, INS-08…).
2. **Nouvelle section** « Anomalies constatées sans traitement », une ligne par code concerné, avec la raison (texte imposé, à recopier) :
   - ETU-08 à ETU-11, ACT-05, TUT-04 : valeurs manquantes laissées manquantes (règle du projet, CLAUDE.md §6 : pas d'imputation dans les tables nettoyées) ;
   - ETU-26 : distances > 51,7 km conservées, toutes hors Dakar et plausibles (D-09) ;
   - X-04 : étudiants sans sortie déclarée dont l'activité s'arrête avant la semaine 30 — lecture renvoyée à DA-07 ;
   - X-05 : arrêt de l'activité après une sortie déclarée — situation normale, pas une anomalie ;
   - X-09 : messages après la sortie — disparus après la correction des dates inversées (D-13), 0 restant ;
   - MSG-07 : synthèse de MSG-04 à MSG-06 (un message peut contenir plusieurs données personnelles).
   - Si un autre code de l'audit n'est ni traité ni dans cette liste → s'arrêter et signaler, ne pas inventer de raison.
3. **Tableau avant / après** pour les 5 tables, et un **bilan global** : lignes avant / après par table, nombre total de règles appliquées, nombre de lignes envoyées dans chaque fichier de rejets.

## Tests
- `tests/test_nettoyage_messages.py` — unitaires : réparation de « trouvÃ© » → « trouvé » ; message « . » retiré ; « Je suis Awa Ndiaye, appelez-moi au 77 123 45 67. » → « Je suis [NOM], appelez-moi au [TEL]. » ; « Mon mail : awa.ndiaye@exemple.sn » → « Mon mail : [EMAIL] » ; « je suis découragé » **inchangé** (pas un nom) ; contrôle résiduel qui s'arrête sur un numéro restant. Les exemples des tests sont **inventés**, jamais tirés des vraies données.
- Invariants sur `data/processed/messages.csv` : aucun `@`, aucune suite de 8 chiffres ou plus, aucun texte vide, aucun « Ã », `id_message` unique, identifiants dans `etudiants.csv`.
- `tests/test_journal.py` : **chaque** code d'anomalie présent dans `docs/audit_qualite.md` apparaît dans `docs/journal_nettoyage.md` (DA-06).

## Contrôles attendus
Prototype de la session de pilotage (en cas d'écart, le signaler et l'expliquer, sans forcer le code) — aucun arrêt ne devrait se déclencher :
- 3 200 messages → 40 textes réparés → 25 messages vides retirés → **3 175 messages** (2 258 étudiants) ;
- remplacements : `[EMAIL]` 33, `[TEL]` 45, `[NOM]` 96 ; 129 messages pseudonymisés ; contrôle résiduel : 0 ;
- journal : les 79 codes d'anomalie de l'audit (ETU 27, INS 12, ACT 14, TUT 9, MSG 7, X 10) cités.

## Livraison
- Deux commits : `DA-05 : nettoyage et pseudonymisation de la table messages (#8)` puis `DA-06 : journal de nettoyage complet et tests (#9)` ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus. **N'y recopie aucun texte original de message.**
