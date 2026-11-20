# Consigne C08 — DA-08 : analyse exploratoire, notebook 02_eda (issue #11)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C06 et C07 terminées.

## Contexte
Lis `CLAUDE.md` (§6 : vocabulaire, honnêteté, D-42 et D-43) et le cahier des charges (DA-08, F2).
But : décrire les étudiants, la censure, la distribution des durées et l'activité, pour préparer la survie (SV-01) et la partie causale (CA-01). **Description seulement** : aucun modèle, aucun test statistique.

## Règles propres à cette consigne
- **Aucune comparaison du décrochage entre groupes** (boursiers / non-boursiers, filières, tutorés / non tutorés…) : avec la censure, un taux brut par groupe est biaisé. Ces comparaisons viendront en SV-01 avec Kaplan-Meier. Seule exception : le **taux hebdomadaire global** de la partie B.4, qui tient compte de la censure.
- Vocabulaire descriptif : « on observe », « associé à ». Jamais « cause » ni « effet ».
- Chaque tableau et chaque figure est suivi d'une phrase d'interprétation pour un conseiller pédagogique, **dont les chiffres sont calculés par le code**.
- Figures en PNG dans `docs/figures/`, nommées `02_<sujet>.png`, titres et axes en français.

## Partie A — `src/eda.py` (fonctions courtes, testées)
- `profil_par_cohorte(base)` : pour chaque variable de `config.COVARIABLES_RENTREE` (sauf `cohorte`), effectifs et % des modalités, ou moyenne et écart-type, par cohorte, avec le nombre de manquants.
- `repartition_evenements(base)` : effectifs et % de `type_evenement`, de E et de la censure.
- `taux_hebdomadaire(base)` : pour chaque semaine s de 1 à 30, nombre d'étudiants **encore suivis au début de la semaine** (T ≥ s), nombre de décrochages (T = s et E = 1) et taux = décrochages / suivis.
- `activite_par_semaine(periode)` : pour chaque semaine, moyenne des connexions des étudiants encore suivis et % de semaines inactives.
- `debut_tutorat(base)` : distribution de `semaine_debut_tutorat` (semaines connues), motifs et types de tuteur. **Sans** aucune donnée de décrochage.

## Partie B — `notebooks/02_eda.ipynb`
Il importe `src/` et lit les fichiers de `data/processed/` (il ne relance pas le pipeline). Sections :
1. **Profil des étudiants par cohorte** : tableau. Interprétation : les deux cohortes sont-elles comparables ? C'est important pour la validation 2024 → 2025.
2. **Valeurs manquantes** des covariables : tableau. Rappel : elles seront imputées dans les modèles, avec des statistiques de l'entraînement seulement.
3. **Décrochage et censure** : répartition des types d'événement ; histogramme des semaines de décrochage (E = 1) → `02_semaines_decrochage.png`.
4. **Taux de décrochage hebdomadaire** (B.4) : courbe → `02_taux_hebdomadaire.png`. Interprétation : les semaines où le risque est le plus élevé, en précisant que SV-01 les confirmera.
5. **Activité au fil des semaines** : connexions moyennes et % de semaines inactives → `02_activite_hebdomadaire.png`.
6. **Moment d'entrée en tutorat** : histogramme de la semaine de début → `02_debut_tutorat.png` ; motifs et types de tuteur. Interprétation : part des tutorats commencés au plus tard en semaine 8, utile pour choisir la semaine landmark en CA-01. **Sans** comparaison avec le décrochage.
- Exécuté de haut en bas sans erreur, commité avec ses sorties. Ajouter `matplotlib` à `requirements.txt` (version exacte installée ; une roue existe pour Python 3.14 sous Windows).

## Partie C — Tests (`tests/test_eda.py`)
- `taux_hebdomadaire` sur 4 étudiants inventés (ex. T = 2 avec E = 1, T = 3 avec E = 0, T = 3 avec E = 1, T = 30 avec E = 0) : suivis en semaines 1, 2 et 3 = 4, 4 et 3 ; décrochages = 0, 1 et 1 ; taux = 0, 0,25 et 0,33.
- `profil_par_cohorte` : effectifs par cohorte égaux au nombre de lignes ; manquants comptés.
- `debut_tutorat` : n'utilise ni `T` ni `E` (le test vérifie qu'il marche sur une base sans ces colonnes).

## Contrôles attendus
Prototype de la session de pilotage (en cas d'écart, le signaler et l'expliquer, sans forcer le code) :
- censure : 3 560 étudiants (71,2 %) ; T : premier quartile 19, médiane 30 ;
- cohortes comparables : âge moyen 20,18 et 20,17 ; boursiers 41,1 % et 42,0 % ; emploi 18,9 % et 19,0 % ; note du bac moyenne 12,73 et 12,69 ;
- manquants : âge 84, note du bac 18, région 90, distance 25, emploi 200 ;
- taux hebdomadaire : maximum en **semaine 16** (124 décrochages sur 4 000 étudiants suivis, 3,1 %) ; puis semaines 6 (2,4 %), 5 (2,3 %) et 4 (2,0 %) ; semaine 1 : 46 sur 5 000 (0,9 %) ; moyenne de 1,1 % sur les semaines 7 à 15 et de 0,7 % sur les semaines 17 à 30 ;
- semaines de décrochage les plus fréquentes : 16 (124), 6 (110), 5 (106), 4 (94), 3 (84) ;
- connexions moyennes : 5,87 (semaine 1), 6,12 (semaine 15), 6,23 (semaine 30) ; 3 458 étudiants encore suivis en semaine 30 ;
- début du tutorat (1 250 semaines connues) : quartiles 4, 7 et 9 ; 851 tutorats (68 %) commencés au plus tard en semaine 8 ; motifs : notes faibles 486, absences répétées 326, signalement enseignant 240, demande personnelle 203.

## Livraison
- Commit : `DA-08 : analyse exploratoire, notebook 02_eda (#11)` ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus.
