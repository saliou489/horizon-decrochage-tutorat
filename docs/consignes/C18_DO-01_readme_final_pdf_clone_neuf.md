# Consigne C18 — DO-01 : PDF du rapport et de la note, test sur un clone neuf, README final (issues #27, #28, #29)

## Emplacement du projet
- Dossier du dépôt : `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (chemin entre guillemets).
- `git pull --rebase origin main`. Prérequis : dernier commit `dfaa0cf` ou plus récent.

## Contexte
- Le rendu est reporté au **dimanche 29/11 à 18 h** (planning version 4) ; objectif : tout pousser avant 15 h.
- Le rapport technique (L3) et la note de synthèse (L4) ont été rédigés dans des documents partagés, puis relus et validés par Saliou le 28/11. Saliou a enregistré leurs PDF dans `docs/` de sa copie de travail.
- Le pilotage a déjà testé un clone neuf sous **Linux** le 28/11 (résultat en fin de consigne). Il reste le test sous **Windows**.
- Ne modifie ni le code, ni les notebooks, ni les tests. Pas d'appel à l'API Gemini.

## Étape 1 — Vérifier et commiter les deux PDF
1. Ces deux fichiers doivent être présents, non suivis par git :
   - `docs/rapport_technique.pdf` ;
   - `docs/note_de_synthese.pdf`.

   S'il en manque un, ou s'il porte un autre nom, arrête-toi et demande à Saliou de l'enregistrer à cet endroit, sous ce nom.
2. Contrôle chaque fichier avec un `python -c` ponctuel, sans nouvelle bibliothèque et sans rien ajouter au dépôt :
   - taille inférieure à 50 Mo ;
   - nombre de pages : nombre de correspondances de `rb"/Type\s*/Page(?![s\w])"` dans les octets du fichier. Attendu : **19** pour le rapport (le cahier exige 15 à 20) et **2** pour la note (2 au plus) ;
   - la note contient l'adresse du dépôt : `b"github.com/saliou489/horizon-decrochage-tutorat"` figure dans ses octets (le cahier exige le lien en première page, −1 point sinon).

   Si un contrôle échoue, arrête-toi et signale-le, sans rien commiter.
3. Deux commits :
   - `DO-02 : rapport technique en PDF, 19 pages (#28)` ;
   - `DO-03 : note de synthèse en PDF, 2 pages, lien du dépôt en page 1 (#29)`.
4. `git pull --rebase origin main`, puis push : le clone de l'étape 2 doit contenir les PDF.

## Étape 2 — Reproductibilité sur un clone neuf (Windows)
1. Clone le dépôt dans un dossier temporaire hors OneDrive, par exemple `C:\Users\SERIGNE SALIOU SEYE\Projets\test_clone_horizon`, avec les chemins entre guillemets. S'il existe déjà, supprime-le d'abord.
   Commande : `git clone https://github.com/saliou489/horizon-decrochage-tutorat.git "<dossier>"`.
2. Dans ce clone, et en mesurant chaque durée :
   - `py -m venv .venv`, puis activation ;
   - `pip install -r requirements.txt` ;
   - `python run_all.py` ;
   - `pytest` : nombre de tests réussis et échoués.
3. Lance `git status --porcelain` dans le clone, après `run_all.py`. Aucun fichier suivi ne devrait être modifié. S'il y en a :
   - ne corrige rien ;
   - liste-les avec `git diff --stat` dans le compte rendu.
4. Lance `streamlit run app/app.py --server.headless true` en arrière-plan. Vérifie que `http://localhost:8501/_stcore/health` répond `ok`, puis arrête le serveur.
5. Supprime le dossier du clone : rien ne doit rester hors du dépôt.
6. Si une étape échoue (installation, `run_all.py`, tests) :
   - arrête-toi ;
   - recopie l'erreur dans le compte rendu.

   Ne corrige rien sans nouvelle consigne.

## Étape 3 — README final (DO-01)
Modifie seulement `README.md`. Les sections « Données », « Fiches d'alerte (LLM) » et « Tableau de bord » restent telles quelles.

1. **En-tête**
   - Remplace « Période : 13 → 27 novembre 2026 (rendu le 27/11 à 18 h) » par « Période : du 16 au 29 novembre 2026 (rendu reporté au dimanche 29/11 à 18 h) ».
   - Ajoute juste en dessous : « À lire en premier : la [note de synthèse](docs/note_de_synthese.pdf) (2 pages) et le [rapport technique](docs/rapport_technique.pdf) (19 pages). »
2. **Nouvelle section « Livrables »**, placée juste après l'en-tête. Mets des liens relatifs, cliquables sur GitHub.

   | Livrable | Où le trouver |
   |---|---|
   | L1 — Dépôt GitHub | ce dépôt |
   | L2 — Journal de nettoyage | `docs/journal_nettoyage.md` |
   | L3 — Rapport technique | `docs/rapport_technique.pdf` |
   | L4 — Note de synthèse | `docs/note_de_synthese.pdf` |
   | L5 — Tableau de bord | `app/app.py` (voir « Tableau de bord ») ; vidéo de démonstration : à venir le 29/11 |
   | L6 — Dossier de gestion de projet | `docs/gestion_projet/` ; dossier PDF et export du Kanban : à venir le 29/11 |
   | L7 — Support de soutenance | à venir le 29/11 |

3. **Nouvelle section « Résultats en bref »**, placée après « Livrables ». Quatre puces, avec exactement ces chiffres :
   - En 30 semaines, 28,8 % des étudiants décrochent, surtout aux semaines 4 à 7 et 15-16.
   - Les facteurs les plus associés au décrochage sont l'emploi en parallèle des études (HR 1,77) et une note du bac basse (HR 0,84 par point). Pour prédire la cohorte 2025, le Cox (C-index 0,638) fait mieux que le gradient boosting (0,610).
   - Effet du tutorat commencé au plus tard en semaine 8 (photo de la semaine 8, pondération par score de propension) : le risque de décrocher d'ici la semaine 30 passe de 19,9 % à 13,0 %, soit −6,9 points (IC à 95 % : −9,6 à −4,0). Le résultat est stable dans les variantes (de −4,7 à −7,1 points), sous les hypothèses de la section 5 du rapport.
   - Un LLM rédige 54 fiches d'alerte à partir de chiffres vérifiés automatiquement ; un tableau de bord Streamlit local les présente en 4 pages.

   Vérifie chaque nombre à sa source :
   - `data/processed/base_survie.csv` : les 28,8 % ;
   - sorties du notebook 03 : les semaines critiques et les HR 1,77 et 0,84 ;
   - `data/processed/resultats/ml_mesures_rentree.csv` : les C-index ;
   - `ca_effet_principal.csv` et `ca_sensibilite.csv` : l'effet du tutorat ;
   - `llm_fiches_semaine8_v2.json` : les 54 fiches.

   En cas d'écart, n'écris pas la puce concernée et signale-le.
4. **Section « Structure »**
   - Ligne `src/` : « Code Python (audit, nettoyage, base de survie, survie, ML, causal, LLM, tableau de bord) ».
   - Ligne `docs/` : « Journal de nettoyage, registre des décisions, rapport et note de synthèse (PDF), consignes, relectures, figures, gestion de projet ».
5. **Section « Installation et exécution »**
   - Étape 3 : ajoute la durée de `run_all.py` mesurée sur le clone neuf de l'étape 2, avec la date.
   - Étape 4 : « Lancer les tests : `pytest` (N tests) », avec le nombre mesuré à l'étape 2.
   - Ajoute une étape 6 : « Ouvrir le tableau de bord : `streamlit run app/app.py` (voir « Tableau de bord ») ».
6. **Section « Limites connues »**
   - Remplace « Le projet a été testé sous Windows avec Python 3.14.3. » par « Testé sur un clone neuf sous Linux (Python 3.13, le 28/11) et sous Windows (Python 3.14.3, le <date de ton test>). » Mentionne Windows seulement si ton test a réussi ; sinon, signale-le.
   - Ajoute : « Limites des résultats (données synthétiques, hypothèses causales, prédiction modeste) : section 7 du rapport technique. »
   - Ajoute : « L'équité du score entre groupes (tâche SV-05, priorité Could) n'a pas été mesurée : la tâche a été abandonnée au gel du 25/11. »
7. **Section « Déclaration d'usage d'assistants IA »**, ligne « Claude, en conversation » : remplace « brouillons de documents (journal de bord, registre des risques, rapport) relus et corrigés par l'étudiant » par « brouillons des documents (rapport technique, note de synthèse, journal de bord, registre des risques, temps par tâche), relus, corrigés et validés par l'étudiant ».
8. Commit : `DO-01 : README final pour le rendu : livrables, résultats en bref, liens vers le rapport et la note (#27)`.

## Étape 4 — Propreté du dépôt (DO-01)
Avec `git ls-files`, vérifie :
- qu'aucun fichier inutile n'est suivi : caches, checkpoints de notebooks, fichiers temporaires, `.env` ;
- qu'aucun fichier ne dépasse 50 Mo.

Le pilotage n'a rien trouvé le 28/11. Signale ce que tu trouves, sans rien supprimer sans l'accord de Saliou.

## Livraison
- Push sur `main` après `git pull --rebase origin main`. Pas de `closes #n` : Saliou passe les cartes à Terminé.
- Compte rendu au format du §10 de `CLAUDE.md`, avec les durées et le nombre de tests du clone neuf.

## Résultat du test Linux (pilotage, 28/11)
- Commit testé : `dfaa0cf`, avec Python 3.13.
- `pip install -r requirements.txt` : 27 s.
- `python run_all.py` : 121 s, sans erreur.
- `git status --porcelain` après la relance : vide. La relance redonne exactement les fichiers suivis.
- `pytest` : 291 tests réussis, 0 échoué, en 21 s. Il y a 2 avertissements de convergence de lifelines, liés à la modalité « (manquant) » de la région, très rare ; ils ne font échouer aucun test.
