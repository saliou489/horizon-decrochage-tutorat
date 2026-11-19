# RV01 — Nettoyage et construction de base_survie (relecture du 19/11/2026)

Demande : `docs/consignes/R01_relecture_nettoyage_base_survie.md`. Clone relu : `horizon-revue`, commit `eb8ac79` (C01 à C06 exécutées).

## Résumé

Le nettoyage et la construction de T et E sont **conformes** au §5 de `CLAUDE.md` et aux décisions D-06 à D-39. Tous les chiffres de contrôle de C06 sont retrouvés à l'identique. Le pipeline est reproductible depuis un clone neuf (`run_all.py` en 29 s, 110 tests réussis, notebook exécutable de haut en bas). Aucun résultat faux, aucune fuite de données réelles.
Les risques portent sur la **suite** : la table période-personne contient l'activité de la semaine de l'événement, et `base_survie` des colonnes connues après la rentrée. Ces deux points deviendront des fuites si les consignes SV/ML ne les encadrent pas. Côté rendu : le README n'a pas encore sa section d'installation, et le dépôt public ne signale pas que les données brutes contiennent des coordonnées fictives. Plusieurs tests ne protègent pas leur règle (vérifié par mutation).
**Constats : 🔴 0 · 🟠 3 · 🟡 5.**

## Constats

### RV01-01 🟠 Période-personne : l'activité de la semaine T fait partie de la définition de l'événement
- Où : `src/base_survie.py:229-245` (`construire_periode_personne`) ; `data/processed/base_periode_personne.csv`.
- Constat : pour un décrochage silencieux, T est la première des 4 semaines inactives. La ligne de la semaine T porte donc toujours `etat_activite = inactif` et 0 connexion. L'activité de cette semaine **définit** l'événement : elle ne le prédit pas. En plus, savoir que la série dure 4 semaines exige les semaines T+1 à T+3, c'est-à-dire le futur.
- Preuve (script temporaire sur le fichier commité) :
  - semaine T des 408 `decrochage_silencieux` : 408 `inactif`, 0 `actif` ;
  - taux de `evenement = 1` par état de la semaine : `inactif` 411 / 695 = **59,1 %**, `actif` 1 027 / 121 083 = 0,85 %, `inconnu` 2 / 160.
- Impact : un modèle à temps discret (SV/ML) qui prendrait comme covariable l'activité de la **même** semaine verrait un C-index gonflé par construction, puisque l'événement s'y lit directement. Le résultat serait faux sans qu'aucun test ne le signale. D-36 traite cette fuite pour `base_survie`, mais rien ne la traite pour la période-personne.
- Correction proposée : écrire dans D-39 (ou dans une nouvelle décision) que les covariables d'activité d'un modèle période-personne sont **décalées** : semaine t−1 ou avant, jamais la semaine t. La session de pilotage peut l'imposer dans les consignes SV/ML. Option : faire produire par le pipeline des colonnes décalées (`nb_connexions_lms_prec`, etc.), avec un test qui vérifie le décalage.

### RV01-02 🟠 README : installation et commande unique encore « À compléter »
- Où : `README.md:26`.
- Constat : la section « Installation et exécution » ne contient que « _À compléter (commande unique pour tout relancer)._ ». Le §3 de `CLAUDE.md` et le §6 du cahier demandent l'installation et la commande unique dans le README.
- Preuve : `grep -n "À compléter" README.md` → ligne 26.
- Impact : sur sa machine Linux, l'enseignant n'a aucune indication pour créer le `.venv`, installer les dépendances et lancer `python run_all.py` puis `pytest`. Le rendu est reproductible en pratique (voir « Vérifié »), mais la marche à suivre n'est écrite nulle part.
- Correction proposée : ajouter au README les commandes du §4 de `CLAUDE.md` (Windows et Linux/macOS), `pip install -r requirements.txt`, `python run_all.py` (durée mesurée ici : environ 30 s), `pytest`, et la commande d'exécution du notebook (`jupyter nbconvert --to notebook --execute --inplace notebooks/01_nettoyage.ipynb`).

### RV01-03 🟠 Dépôt public : la présence de coordonnées fictives dans `data/raw/` n'est pas signalée
- Où : `README.md` (aucune mention) ; `data/raw/LISEZMOI.md:3` ; `data/raw/messages.csv`.
- Constat : le LISEZMOI de l'enseignant dit que les données sont « synthétiques (fictives) ». Il ne dit pas que `messages.csv` contient des noms, des e-mails et des numéros de téléphone en clair (D-28 : 96 noms, 33 e-mails, 45 téléphones). Le README ne dit rien des données.
- Preuve : `grep -n -i "fictiv\|synth\|personnel" README.md` ne renvoie que « note de synthèse ». Les téléphones suivent le format réel des mobiles sénégalais (préfixes 70 à 78, 9 chiffres), donc rien ne garantit qu'aucun n'est attribué à une vraie personne.
- Impact : un lecteur du dépôt public (jury, recruteur) voit des coordonnées en clair sans savoir qu'elles sont fictives. Le projet insiste par ailleurs sur la loi 2008-12 : c'est incohérent et cela peut être mal reçu en soutenance. `data/raw/` ne peut pas être modifié (empreintes SHA-256) : la seule correction possible est de le signaler.
- Correction proposée : ajouter au README, par exemple dans une section « Données » :
  > **Données.** Les fichiers de `data/raw/` sont un jeu **synthétique** fourni par l'enseignant : aucun étudiant réel. Les messages bruts (`data/raw/messages.csv`) contiennent des noms, e-mails et numéros de téléphone **inventés**, laissés volontairement pour l'exercice de pseudonymisation. Ils sont conservés tels quels, car les fichiers bruts ne doivent pas être modifiés (`data/raw_sha256.txt`). Toutes les tables produites (`data/processed/`) sont pseudonymisées (`[NOM]`, `[TEL]`, `[EMAIL]`, décision D-28) et aucun texte de message n'est envoyé à un service externe.

  Saliou peut aussi demander à l'enseignant si les numéros ont été choisis dans une plage non attribuée.

### RV01-04 🟡 `base_survie` contient des colonnes connues seulement après la rentrée, sans garde-fou
- Où : `src/config.py` (`COLONNES_BASE_SURVIE`) ; `data/processed/base_survie.csv` (colonnes `nb_seances`, `motif_orientation`, `type_tuteur`, `tutore`, `statut_tutorat`).
- Constat : D-36 les classe comme « descriptives ». Pourtant, rien dans le fichier ni dans le code ne les sépare des covariables de la rentrée. `nb_seances` est un cumul sur tout le suivi, et `tutore` / `statut_tutorat` sont calculés à partir de T.
- Preuve : chez les 1 204 tutorés, corr(`nb_seances`, T) = **0,73** ; corr(`nb_seances`, T − `semaine_debut_tutorat`) = 0,80. Le nombre de séances mesure donc surtout la durée de présence. Ce fait confirme D-36 sans la remettre en cause.
- Impact : avec un Cox ou une forêt de survie qui prendrait « toutes les colonnes sauf T et E », `nb_seances` ferait fuir T, et `tutore` en covariable fixe réintroduirait le biais du temps immortel.
- Correction proposée : définir dans `config.py` une liste explicite `COVARIABLES_RENTREE`, que les modules `survie` et `ml_survie` utiliseraient sans jamais sélectionner par exclusion. Ajouter un test qui vérifie que cette liste ne contient que des colonnes de `etudiants`.

### RV01-05 🟡 `tutore` n'est défini que pour le T de référence, pas pour les variantes de sensibilité
- Où : `src/base_survie.py:190-202` (`ajouter_tutorat` utilise `T` seulement).
- Constat : la sensibilité (§5 de `CLAUDE.md`, D-38) refait les analyses avec `T_seuil3`, `T_seuil5` et la lecture « inconnu = inactif ». Le statut de tutorat n'est pas recalculé pour ces T.
- Preuve : aux seuils 3 et 5, 0 tutoré n'aurait commencé son tutorat à T_seuil ou après. En lecture « inconnu = inactif », **1** tutoré l'aurait commencé à son nouveau T ou après : il resterait compté `tutore = 1` alors que son tutorat ne précède plus l'événement.
- Impact : faible sur les données actuelles (1 étudiant). Mais la règle D-37 (« strictement avant T ») ne serait plus respectée dans les analyses de sensibilité causales.
- Correction proposée : dans la consigne CA, recalculer `statut_tutorat` avec le T de chaque variante (même fonction `statut_tutorat`), ou documenter l'écart comme limite.

### RV01-06 🟡 Tests qui ne protègent pas leur règle
- Où : `tests/test_nettoyage_activite.py:119-130`, `tests/test_base_survie.py` (invariants), absence de test unitaire de `construire_periode_personne`.
- Constat et preuve (mutations faites sur une copie hors dépôt, puis `pytest`) :
  1. Dans `activite.regle_doublons`, remplacer `"max"` par `"last"` pour les connexions et les devoirs (D-20) : **110 tests réussis**. Le test des quasi-doublons place la plus grande valeur dans la dernière copie : « dernière ligne » et « maximum » y donnent le même résultat.
  2. Dans `construire_periode_personne`, remplacer `semaine > semaine_debut_tutorat` par `>=` (contraire de D-39) : **110 tests réussis**. Les invariants lisent les CSV **commités**, pas ceux que produirait le code modifié, et aucun test unitaire n'appelle la fonction.
  3. Cas de C06 sans test : abandon à date invalide **avec** série (seul le cas « activité jusqu'à 30 » est testé), série avant un **transfert** ou un abandon sans date. Pour les colonnes `E_seuil3` / `E_seuil5`, seul E ∈ {0, 1} est vérifié, alors que C06 demande « E = 1 exactement pour les types… idem pour les colonnes de sensibilité ».
- Impact : une régression sur D-20 ou D-39 passerait inaperçue tant que `run_all.py` n'est pas relancé, et même après dans le cas 1.
- Correction proposée : dans le test des quasi-doublons, mettre la plus grande valeur dans la **première** copie (ou mettre un manquant dans l'une des deux) ; ajouter un test unitaire de `construire_periode_personne` sur 2 ou 3 étudiants inventés (tutoré avant T, même semaine, semaine inconnue) ; ajouter les 3 cas d'arrêt manquants.

### RV01-07 🟡 `premiere_serie` compte des positions, pas des semaines : un trou dans une série n'est pas détecté
- Où : `src/base_survie.py:67-84` et contrôle `src/base_survie.py:149`.
- Constat : la série est cherchée sur la position dans la liste. Le contrôle « semaine manquante entre 1 et T » ne regarde que les semaines ≤ T. Un trou **après** le début de la série n'est donc pas vu.
- Preuve : `t_et_e('X', [1..9, 10, 12, 13, 14], [actif]*9 + [inactif]*4, aucune sortie, 4, 'active')` renvoie `(10, 1, 'decrochage_silencieux')` : 4 semaines « consécutives » alors que la semaine 11 manque, et sans arrêt. Dans les données actuelles, aucun étudiant n'a de trou (0 sur 5 000) : le résultat n'est pas touché.
- Impact : aucun aujourd'hui. Le principe D-18 (arrêt sur un cas imprévu) n'est pas tenu pour ce cas.
- Correction proposée : vérifier que la liste des semaines est exactement 1 … dernière **avant** de chercher la série (déplacer le contrôle de la ligne 149 en tête de `t_et_e`, sur toute la liste).

### RV01-08 🟡 Noms fictifs des données brutes recopiés dans un test et dans un commentaire ; dépendances transitives non figées
- Où : `tests/test_nettoyage_messages.py:45` et `:51` ; commentaire au-dessus de `MOTIF_PSEUDO_NOM` (`src/config.py:390-395`) ; `requirements.txt`.
- Constat :
  1. Le prénom et le nom utilisés en exemple dans le test et dans le commentaire figurent tels quels dans **2 messages** de `data/raw/messages.csv` (deux étudiants différents). L'e-mail du test est construit sur ce même nom. Le §5 de R00 demande qu'aucune donnée personnelle, même fictive, ne soit reprise dans un test.
  2. `requirements.txt` fige 5 paquets, mais l'installation en compte 53 (`pip freeze`). Les dépendances de jupyter, nbconvert et pytest ne sont pas figées.
- Preuve : `grep -c` du nom complet dans `data/raw/messages.csv` → 2 (non recopié ici) ; `pip freeze | wc -l` → 53.
- Impact : 1. faible, la donnée est fictive, mais c'est contraire à la règle du projet ; 2. une nouvelle version d'un paquet transitif peut casser l'exécution du notebook chez l'enseignant.
- Correction proposée : 1. remplacer par un nom manifestement inventé et absent des données (par exemple « Prénom Testnom ») ; 2. option : fichier de contraintes issu de `pip freeze` (`requirements-lock.txt`) cité dans le README.

## Réponses aux questions de R01

1. **Une règle peut-elle masquer ou créer une anomalie ?** Rien de tel dans les données actuelles. Les deux cas qui pouvaient poser problème ont été vérifiés :
   - D-19 met à manquant les connexions impossibles **avant** la fusion des quasi-doublons (D-20). Ce cas pourrait remplacer une activité par un 0, mais il ne se produit pas : 0 des 57 lignes à connexion impossible n'a de doublon.
   - 7 semaines deviennent « inconnues » parce qu'une connexion impossible est mise à manquant avec 0 devoir. La lecture de référence les compte actives (D-31) et la lecture inverse est couverte par la sensibilité (20 étudiants).
2. **T et E** : conformes au §5 et à D-30 à D-37. Cas limites vérifiés :
   - inactivité seulement en fin de suivi : 27 `fin_de_suivi` ont une semaine 30 inactive (série coupée, non comptée), comme le veut D-30 ;
   - semaine inconnue au milieu d'une série : coupe la série (test unitaire) ;
   - sortie en semaine 1 : 49 étudiants avec T = 1 (29 abandons datés, 16 silencieux, 3 transferts, 1 abandon sans date), avec une ligne période-personne chacun ;
   - D-17 : 10 reconstitués (7 fin de suivi, 2 perdus de vue, 1 silencieux) ;
   - D-33 : 6 étudiants, E = 1, T de 3 à 26 ;
   - tutorat commencé la semaine de T : 31, non tutorés (D-37) ;
   - D-35 : 8 silencieux redevenus actifs, comme le constat.

   Seul défaut trouvé : un trou dans une série n'est pas détecté (RV01-07), cas absent des données.
3. **Période-personne / base_survie** : cohérentes. Pour chaque étudiant, le nombre de lignes vaut T et il y a une seule ligne `evenement = 1`, à la semaine T, si E = 1. `tutorat_commence` vaut 1 sur 24 119 lignes et reste vide sur 127 lignes, comme le prévoit C06. Le défaut est méthodologique (RV01-01).
4. **Fuite dans base_survie** : aucune covariable d'activité. Les colonnes de tutorat et `nb_seances` sont postérieures à la rentrée (RV01-04).
5. **Données personnelles** : `data/processed/`, les rejets, le journal et le notebook sont propres (0 e-mail, 0 téléphone, 0 nom introduit restant ; 129 messages balisés). Le notebook n'affiche aucun texte de message. Restent l'exemple du test (RV01-08) et l'absence d'avertissement dans le README (RV01-03, texte proposé).
6. **Tests** : voir RV01-06.
7. **Reproductibilité** : voir « Vérifié ».
8. **Lisibilité : les 3 fonctions les plus difficiles à expliquer en soutenance**
   - `activite.regle_doublons` (`src/nettoyage/activite.py:186-235`) : trois étapes dans une fonction (identiques, quasi-doublons, ordre du fichier). La colonne `_ordre` vient de `groupes.head(1).index` : il faut savoir que `groupby(sort=False)` suit l'ordre de première apparition pour comprendre pourquoi l'ordre est conservé.
   - `base_survie.premiere_serie` (`src/base_survie.py:83`) : `position - seuil + 2` mélange une position commençant à 0 et une semaine commençant à 1. Il faut faire le calcul au tableau pour s'en convaincre. Écrire `semaine_debut = (position + 1) - seuil + 1`, ou parcourir directement les numéros de semaine, serait plus parlant.
   - `base_survie.construire_periode_personne` (`src/base_survie.py:240-244`) : un masque booléen combiné à une comparaison avec des manquants (`fillna(False)`), une conversion en `Int64` par `pd.array`, puis l'écrasement des semaines inconnues par `pd.NA`. Trois lignes denses pour une règle simple (0, 1 ou vide) : une petite fonction `tutorat_commence(semaine, statut, debut)` appliquée ligne par ligne, sur le modèle de `statut_tutorat`, serait plus facile à expliquer.

   À préparer aussi : `t_et_e`, dont l'ordre des branches et le contrôle `semaines[:T]` décident de tout.

## Questions (points sans preuve suffisante)
- Les numéros de téléphone des messages bruts sont-ils dans une plage non attribuée ? Seul l'enseignant peut le dire (voir RV01-03).
- Le notebook relance le nettoyage et réécrit `data/processed/` et le journal. C06 le demande, mais un lecteur qui ouvre le notebook pour le consulter modifie des fichiers suivis par git. À la relance, seul le journal change, et uniquement par ses fins de ligne. Faut-il le signaler dans la première cellule ?

## Vérifié sans problème
- **Contrôles attendus de C06 retrouvés à l'identique** : types d'événement (3 441 / 1 004 / 408 / 117 / 22 / 6 / 2), E = 1 440, E_seuil3 = 1 445, E_seuil5 = 1 435, T moyen 24,39, lecture « inconnu = inactif » E = 1 441 et 20 étudiants changés, statuts de tutorat (3 745 / 1 199 / 31 / 20 / 5), 1 204 tutorés, 121 938 lignes période-personne.
- **Reproductibilité** depuis un clone neuf (Windows, Python 3.14.3) : `.venv` et `pip install -r requirements.txt` réussis (4 min 44 s) ; `python run_all.py` sans erreur en **29 s** ; `git status` ensuite : seul `docs/journal_nettoyage.md` apparaît, pour une différence de fins de ligne seulement (`git diff --ignore-cr-at-eol` vide) ; toutes les tables produites sont identiques octet pour octet ; `pytest` : **110 réussis, 0 échoué** (6,6 s) ; notebook exécuté de haut en bas sans erreur (43 s).
- **Intégrité des bruts** : `.gitattributes` (`data/raw/** -text`) protège les CSV de la conversion des fins de ligne. Test SHA-256 réussi.
- **Secrets** : aucune clé, aucun jeton ni fichier `.env` dans tout l'historique git (`git log --all -p`).
- **Notebook** : aucun chiffre écrit à la main dans les cellules de texte (les phrases chiffrées sont produites par le code). Aucune comparaison naïve tutorés / non tutorés, avec un avertissement explicite.
- **Données** : aucun trou dans les semaines d'activité (0 étudiant) ; chaque étudiant a de l'activité ; la règle D-26 (`<= 0` → manquant) ne touche que des 0 dans les données.

## Limites de la relecture
- Le cahier des charges (PDF) n'a pas été relu en entier. La conformité a été jugée sur `CLAUDE.md` (§5, §6), les décisions et les consignes, qui le citent.
- `src/audit.py` (1 108 lignes) et `src/nettoyage/etudiants.py` n'ont été relus que par leurs sorties (journal, invariants, tests réussis), pas ligne par ligne.
- La reproductibilité n'a été testée que sous Windows : la machine Linux / macOS de l'enseignant n'a pas été simulée.
- La recherche de noms restants dans les messages pseudonymisés repose sur des motifs (majuscules consécutives, « je m'appelle », « moi c'est », signatures). Un nom écrit tout en minuscules ne serait pas trouvé.
