# Consigne C02 — DA-02 : nettoyage de la table « etudiants » (issue #5)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`.

## Contexte
Lis `CLAUDE.md`, le cahier des charges (§4.2, annexe A), `docs/audit_qualite.md` (section `etudiants`) et **les décisions D-06 à D-11 de `docs/decisions.md`** : elles sont validées par Saliou et fixent toutes les règles ci-dessous.
Périmètre : **table `etudiants` uniquement** (DA-02). Les autres tables et les contrôles entre tables viendront dans les consignes suivantes.

## À produire

### 1. Code
- `src/nettoyage/__init__.py`, `src/nettoyage/commun.py` (outils partagés par toutes les tables), `src/nettoyage/etudiants.py`.
- `python -m src.nettoyage` : nettoie les tables déjà prises en charge (pour l'instant `etudiants`), écrit `data/processed/etudiants.csv` (UTF-8, séparateur `,`, sans index) et régénère `docs/journal_nettoyage.md`.
- `run_all.py` à la racine : pour l'instant, appelle simplement le nettoyage. Il sera complété au fil des tâches.
- Une règle = une fonction (DataFrame en entrée → DataFrame corrigé + nombre de lignes touchées). Chaque fonction renvoie aussi de quoi écrire sa ligne de journal.

### 2. Règles, dans cet ordre (l'ordre compte : normaliser avant de dédoublonner)
1. **En-têtes** : retirer les espaces ; renommer `Distance campus (km)` → `distance_campus_km`.
2. **Identifiants** : majuscules, espaces retirés. Après correction, tout identifiant ne respectant pas `HZ` + 5 chiffres → **s'arrêter et signaler** (l'audit n'en a trouvé aucun).
3. **Modalités** (D-06, D-11). Forme simplifiée d'une valeur = minuscules, accents retirés, **tirets remplacés par des espaces**, espaces multiples réduits à un, espaces de bord retirés (sans le remplacement des tirets, « St-Louis » ne serait pas reconnu). On compare la forme simplifiée de la valeur à la forme simplifiée de chaque modalité officielle du LISEZMOI, puis aux abréviations listées ci-dessous :
   - genre : f, femme, feminin → `F` ; m, h, homme, masculin → `M` ;
   - boursier : oui, o, yes, 1 → `Oui` ; non, n, no, 0 → `Non` ;
   - filière : `Informatique`, `Gestion`, `Droit`, `Génie civil`, `Communication` ; abréviations : info → `Informatique` ; gc → `Génie civil` ; com → `Communication` ;
   - mention : p → `Passable` ; ab → `Assez bien` ; b → `Bien` ; tb, tres bien → `Très bien` ;
   - région : les 14 régions officielles avec leurs accents (`Dakar`, `Diourbel`, `Fatick`, `Kaffrine`, `Kaolack`, `Kédougou`, `Kolda`, `Louga`, `Matam`, `Saint-Louis`, `Sédhiou`, `Tambacounda`, `Thiès`, `Ziguinchor`) ; abréviations : st louis → `Saint-Louis` ; zig → `Ziguinchor` ;
   - emploi_parallele : `Oui`, `Non`.
   - Une valeur qui ne correspond à aucune règle → **s'arrêter et signaler**, ne jamais la mettre à manquant en silence.
   - Les cases vides restent vides.
4. **Nombres** : virgule → point ; retirer « ans » et « km » ; conversion numérique. `age` et `cohorte` en entiers (type entier acceptant les manquants).
5. **Valeurs impossibles → manquant** (D-08, D-09) : `age` hors [17 ; 35] ; `note_bac` hors [10 ; 20] ; `distance_campus_km` ≤ 0 ou égale à 9999 (seule sentinelle présente ; **ne pas** traiter 99 ou 999 comme sentinelles pour la distance, ce serait une distance plausible). Les distances > 51,7 km sont **conservées**.
6. **Doublons** (D-06, D-07), après les étapes 1 à 5 : une seule ligne par `id_etudiant`, la **première du fichier**. Compter séparément dans le journal : lignes strictement identiques supprimées ; lignes du même étudiant avec des valeurs différentes supprimées. Si deux lignes d'un même étudiant diffèrent sur une autre colonne que la distance → **s'arrêter et signaler**.
7. **Mention / note** (D-10) : si `note_bac` est connue, `mention_bac` est recalculée (Passable [10 ; 12[, Assez bien [12 ; 14[, Bien [14 ; 16[, Très bien ≥ 16) ; compter à part les mentions **corrigées** (contradiction) et les mentions **complétées** (vides). Si la note est manquante, la mention d'origine est gardée. Normal : il y aura plus de mentions corrigées que les 37 incohérences de l'audit, car l'audit acceptait les deux mentions voisines pour une note de 12, 14 ou 16 tout rond, alors que D-10 tranche (12 → Assez bien).

### 3. Journal de nettoyage (`docs/journal_nettoyage.md`, généré)
- Gabarit annexe A : `# | Table | Anomalie constatée | Lignes | Traitement appliqué | Justification`. La justification cite la décision (ex. « D-08 »). Tous les nombres sont produits par le code.
- Tableau avant / après pour `etudiants` : nombre de lignes, valeurs manquantes par colonne, doublons d'identifiant.
- Les lignes où une valeur a été mise à manquant sont comptées par colonne.

### 4. Tests (`tests/test_nettoyage_etudiants.py`)
- Un test unitaire par règle, sur un petit DataFrame construit dans le test (dont : « 12 » → `Assez bien` ; « 135 » → manquant ; « -17.3 » → manquant ; « 79.5 » conservé ; doublon quasi identique → première ligne gardée ; valeur de modalité inconnue → erreur).
- Tests d'invariants sur `data/processed/etudiants.csv` (ignorés si le fichier n'existe pas) : identifiants uniques et au bon format ; modalités toutes dans la liste officielle ; âge dans [17 ; 35], note dans [10 ; 20], distance > 0 quand renseignés ; mention cohérente avec la note.

## Contrôles attendus
La session de pilotage a testé ces règles sur les données brutes avec un prototype. Résultats attendus, à comparer (ne pas forcer le code à les retrouver : en cas d'écart, le signaler et l'expliquer) :
- aucun identifiant mal formé, aucune modalité inconnue, aucune différence hors distance entre deux lignes d'un même étudiant : aucun arrêt ne devrait se déclencher ;
- 5 085 lignes → 61 lignes identiques après harmonisation supprimées → 24 lignes d'un même étudiant (distance différente) supprimées → **5 000 lignes** ;
- note_bac mise à manquant : 18 (valeurs −2, 0, 25,5, 112, 135) ; mentions corrigées : 46 ; mentions complétées : 150.

## Livraison
- Commit(s) : `DA-02 : nettoyage de la table etudiants (#5)` ; push sur `main`.
- Compte rendu au format du §10 de `CLAUDE.md`, avec en résultats clés : lignes avant / après, nombre d'étudiants, lignes touchées par chaque règle.
