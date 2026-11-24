# Consigne C15 — DB-01 : tableau de bord Streamlit (issue #25)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- Avant toute chose : `git pull --rebase origin main`. Prérequis : C14 terminée, **D-68 validée** par Saliou.

## Contexte
Lis `CLAUDE.md` (§6 « Honnêteté des résultats », §7 « Style »), le cahier des charges (F7, livrable L5) et les décisions **D-63, D-66, D-67 (point 9) et D-68**.
- F7 demande : liste des étudiants à risque, courbe de survie individuelle, fiche LLM, page « effet du tutorat ». Le tableau de bord sera montré dans une vidéo de 3 min (L5) et doit être « utilisable » (barème).
- **Aucun recalcul de modèle, aucun appel à l'API** : le tableau de bord relit les fichiers de `data/processed/` et `data/processed/resultats/`, et doit démarrer sans clé.
- Ne touche pas au code des fiches (`src/llm.py`) sauf pour **réutiliser** ses fonctions ; la version 2 du prompt fera l'objet d'une autre consigne.
- Nouvelle bibliothèque : `streamlit==1.67.0` (le pilotage a vérifié que toutes les dépendances existent en roues Windows pour Python 3.14 avec les versions figées). Si l'installation échoue : arrête-toi et signale-le.

## Partie A — Logique (`src/tableau_de_bord.py`, testable, sans Streamlit)
Module avec « Rôle du module » (DB-01). Fonctions courtes, docstrings en français :
1. `charger_donnees()` : dictionnaire des tables utiles (base de survie et table période-personne, `ml_predictions_2025.csv`, `ml_scores_hebdomadaires_2025.csv`, `ml_hr_cox_2024.csv`, `ml_mesures_rentree.csv`, `ca_effet_principal.csv`, `ca_courbes_ponderees.csv`, `ca_sensibilite.csv`, et la liste des fiches de `config.FICHIER_FICHES_LLM`, vide si le fichier n'existe pas). Chemins tirés de `config.py`.
2. `table_a_risque(donnees, semaine)` : une ligne par étudiant de 2025 encore suivi après la semaine (`llm.population_suivie`), avec :
   - `risque_cox_pct` : 1 − S(30) / S(semaine), en % (`llm.risques_conditionnels`) ;
   - `risque_semaine_suivante_pct` : `risque_hebdomadaire` de la semaine `semaine + 1` dans `ml_scores_hebdomadaires_2025.csv` (activité connue jusqu'à la semaine choisie), en % ;
   - `facteurs` : texte court des facteurs affichables, par exemple « âge ×2,1 ; emploi ×1,6 ; distance ×1,5 », calculés comme pour les fiches (`llm.contributions`, `llm.references_promotion`, `llm.facteurs_principaux`, avec la table codée de `ml_survie.variables_rentree`, comme dans `llm.construire_entrees`) sur la population de cette semaine ;
   - `tutorat` : statut à cette semaine (`llm.statut_tutorat`), en texte lisible ;
   - `fiche` : statut de la fiche LLM (« validée » ou « à revoir ») si `semaine == config.SEMAINE_FICHES` et qu'une fiche existe, sinon vide.

   Tri par risque décroissant puis identifiant. Les nombres de la table restent numériques ; le formatage français se fait à l'affichage.
3. `courbe_individuelle(donnees, id_etudiant)` : semaines 1 à 30, survie Cox de l'étudiant et moyenne des courbes Cox de la cohorte 2025.
4. `profil(donnees, id_etudiant)` : âge, note du bac, distance, bourse, emploi, filière (**ni genre ni région**, D-68).
5. `activite_semaines(donnees, id_etudiant, semaine)` : activité des semaines `semaine − 1` et `semaine` (la semaine 1 seule si `semaine` vaut 1) de l'étudiant et de la population de la semaine (`llm.activite_recente`).
6. `fiche_llm(donnees, id_etudiant)` : la fiche du cache, ou `None`.
7. `resume_effet(donnees)` : les mesures de `ca_effet_principal.csv` (estimation et IC) et la table des variantes de `ca_sensibilite.csv`, prêtes à afficher.

## Partie B — Application (`app/app.py`)
- En tête : « Rôle du module » ; ajout de la racine du dépôt au chemin d'import à partir de `Path(__file__)` (aucun chemin absolu écrit en dur), pour que `streamlit run app/app.py` lancé depuis la racine trouve `src`.
- `st.set_page_config(page_title="Horizon — décrochage et tutorat", layout="wide")` ; données chargées une seule fois (`st.cache_data`) ; la table de chaque semaine aussi.
- Barre latérale : navigation entre 4 pages ; curseur de la **semaine** (1 à 29, 8 par défaut) et du **seuil** de risque (5 à 80 %, 40 % par défaut), partagés entre les pages ; rappel : « Données synthétiques ; identifiants pseudonymisés. »
- Nombres affichés au format français (virgule, « % »).

**Page 1 — Étudiants à risque.**
- Trois chiffres en tête : étudiants encore suivis après la semaine L, nombre au-dessus du seuil, risque moyen.
- Table des étudiants au-dessus du seuil (case à cocher : toute la population), colonnes lisibles.
- Deux phrases sous la table :
  - « Risque Cox : probabilité estimée de décrocher d'ici la semaine 30 pour un étudiant encore inscrit après la semaine L, d'après son profil de rentrée. » ;
  - « Risque de la semaine suivante : signal à court terme du gradient boosting, tiré de l'activité jusqu'à la semaine L. »
- Rappels : les facteurs sont **associés** au risque, ce ne sont pas des causes ; le risque restant baisse au fil des semaines, donc le seuil est à adapter.

**Page 2 — Fiche étudiant.**
- Choix de l'étudiant parmi la table de la page 1 (le plus à risque par défaut).
- Risques Cox et de la semaine suivante ; profil (D-68, point 3) ; facteurs et multiplicateurs, expliqués « par rapport à un étudiant moyen de la promotion » ; activité des deux dernières semaines contre la promotion ; statut de tutorat.
- **Courbe de survie individuelle** (matplotlib) : courbe Cox de l'étudiant et courbe moyenne de la cohorte, ligne verticale à la semaine L, axe « probabilité d'être encore inscrit ».
- **Fiche LLM** :
  - à la semaine 8, si elle existe : situation, points d'attention, actions, puis l'avertissement fixe ; badge « validée » ; une fiche « à revoir » porte un bandeau d'avertissement (`st.warning`) et ses motifs (D-67) ; modèle, version du prompt et date en petit ;
  - semaine 8 sans fiche : « Pas de fiche : risque inférieur à 40 % » ;
  - autre semaine : « Les fiches sont rédigées pour la semaine 8 (D-66). »

**Page 3 — Effet du tutorat.**
- Phrase principale, chiffres lus dans `ca_effet_principal.csv` : chez les étudiants encore inscrits en semaine 8, commencer le tutorat au plus tard en semaine 8 fait passer le risque de décrocher d'ici la semaine 30 de 19,9 % à 13,0 %, soit −6,9 points (IC à 95 % de −9,6 à −4,0).
- Puis : rapport des risques, gain de RMST sur 22 semaines, HR, E-value (et borne de l'IC), chacun avec une phrase pour un conseiller.
- Courbes de Kaplan-Meier pondérées (`ca_courbes_ponderees.csv`).
- Table des variantes, avec la phrase : « toutes les variantes vont dans le même sens » (seulement si c'est vrai dans le fichier).
- Hypothèses rappelées, reprises du notebook 05 : pas de facteur de confusion non mesuré, positivité, photo de la semaine 8 (les tutorats commencés plus tard comptent comme non tutorés), données synthétiques. Seule page où le mot « effet » est permis.

**Page 4 — À propos.**
- Données (synthétiques, cohortes 2024 et 2025) ; modèles et validation 2024 → 2025, avec le C-index, le Brier intégré et l'écart de calibration lus dans `ml_mesures_rentree.csv`.
- Fiches LLM : pseudonymisées, contrôles, avertissement (D-65 à D-67).
- Limites principales ; commande `python run_all.py` pour tout régénérer.

## Partie C — Tests (`tests/test_tableau_de_bord.py`)
- **Unitaires, sur de petites tables construites dans le test** :
  - `table_a_risque` : seuls les étudiants avec T > L, risque 1 − S(30)/S(L), risque de la semaine suivante pris à L + 1, tri ;
  - `fiche_llm` : `None` si l'étudiant n'a pas de fiche ;
  - `profil` : sans genre ni région ;
  - `courbe_individuelle` : moyenne correcte.
- **Invariants sur les fichiers produits** (ignorés proprement s'ils manquent) :
  - semaine 8 et seuil 40 % → **54** étudiants, exactement ceux du cache des fiches ;
  - risques entre 0 et 100 ;
  - jamais « genre » ni « région » dans la colonne `facteurs` ;
  - une table non vide pour chaque semaine de 1 à 29.
- **Démarrage de l'application** avec `streamlit.testing.v1.AppTest.from_file(str(config.RACINE / "app" / "app.py"))` : aucune exception sur chacune des 4 pages, à la semaine 8, puis à la semaine 4 (ignoré proprement si les données manquent).

## Partie D — Dépendance, README, vérification visuelle
- `requirements.txt` : `streamlit==1.67.0`.
- README, section « Tableau de bord » : commande `streamlit run app/app.py` ; les 4 pages ; aucune clé nécessaire ; données synthétiques, identifiants pseudonymisés.
- Lance réellement `streamlit run app/app.py`, ouvre les 4 pages (semaines 8 et 4), et corrige tout ce qui est illisible ou faux (chevauchements, nombres non formatés, colonnes incompréhensibles).
- Fais 4 captures d'écran (une par page, semaine 8) dans `docs/figures/` (`db_page1_risque.png`, `db_page2_fiche.png`, `db_page3_effet.png`, `db_page4_apropos.png`) : elles serviront au rapport et à la soutenance. Si tu ne peux pas faire de capture, dis-le.

## Contrôles attendus (prototype de la session de pilotage)
| Semaine | Suivis après la semaine | Risque ≥ 40 % | Risque Cox moyen | Risque de la semaine suivante moyen |
|---:|---:|---:|---:|---:|
| 1 | 2 489 | 385 | 28,13 % | 1,29 % |
| 4 | 2 353 | 233 | 24,80 % | 2,34 % |
| 8 | 2 177 | **54** | 17,79 % | 1,10 % |
| 12 | 2 102 | 15 | 14,78 % | 0,72 % |
| 16 | 1 951 | 1 | 9,08 % | 1,44 % |
| 20 | 1 846 | 0 | 5,34 % | 0,70 % |

- Semaine 8 : risque de la semaine suivante moyen des 54 = 3,61 % (1,10 % pour la promotion).
- Courbe moyenne Cox de la cohorte 2025 : S(8) = 0,8628 ; S(30) = 0,7101.
- Page 3 : 13,0 % contre 19,9 % ; −6,9 points [−9,6 ; −4,0] ; RR 0,65 [0,53 ; 0,80] ; RMST +1,2 semaine [0,8 ; 1,5] ; HR 0,61 [0,50 ; 0,76] ; E-value 2,44 (borne de l'IC : 1,82).

## Livraison
- Commits :
  - `DB-01 : logique et tests du tableau de bord (#25)` (parties A et C) ;
  - `DB-01 : application Streamlit à 4 pages, README et captures (#25)` (parties B et D) ;
  - push sur `main`.
- Vérifier à la fin : `pytest` ; `python run_all.py` inchangé ; `streamlit run app/app.py` démarre sans clé ; `git status` propre.
- Compte rendu au format du §10 de `CLAUDE.md`, avec la comparaison aux contrôles attendus, le temps de démarrage du tableau de bord et ce que tu as corrigé en le regardant.
- Kanban (pour Saliou) : DB-01 « En cours » pendant l'exécution.
