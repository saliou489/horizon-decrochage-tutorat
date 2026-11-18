# Registre des décisions

Une décision = une question de méthode ou de règle métier qui aurait pu être tranchée autrement.
Statuts : **proposée** (en attente de Saliou) · **validée** (par Saliou) · **rejetée**. Seul Saliou passe une décision à « validée ».

Gabarit :

```
## D-xx — Titre court
- Date / tâche :
- Question :
- Options :
- Recommandation (et pourquoi) :
- Décision :
- Statut :
```

---

## D-01 — Visibilité du dépôt
- Date / tâche : 16/11/2026 — GP-01
- Question : dépôt public ou privé avec accès enseignant ?
- Options : public ; privé + invitation de l'enseignant.
- Recommandation : public (données fictives, aucun accès à gérer).
- Décision : dépôt public.
- Statut : validée (Saliou, 16/11)

## D-02 — Replanification du projet
- Date / tâche : 18/11/2026 — GP-03
- Question : le projet a démarré le 16/11 au lieu du 13/11 ; comment répartir le travail restant ?
- Options : garder le planning du cahier des charges ; replanifier du 18 au 27/11, week-end inclus, charge en baisse vers la fin.
- Recommandation : replanifier (`docs/planning.md`).
- Décision : planning replanifié, week-end inclus ; point d'étape avec l'enseignant déplacé au lundi 23/11.
- Statut : validée (Saliou, 18/11)

## D-03 — Organisation du travail avec les assistants IA
- Date / tâche : 18/11/2026 — GP-03
- Question : comment utiliser Claude tout en restant capable d'expliquer chaque ligne ?
- Options : tout faire générer d'un coup ; une session d'exécution (Claude Code) qui suit des consignes écrites, une session de pilotage qui vérifie et explique.
- Recommandation : deux sessions, consignes versionnées dans `docs/consignes/`, cadre dans `CLAUDE.md`.
- Décision : deux sessions comme recommandé.
- Statut : validée (Saliou, 18/11)

## D-04 — Emplacement de la copie locale du dépôt
- Date / tâche : 18/11/2026 — GP-01
- Question : où cloner le dépôt sur le PC de Saliou ?
- Options : dans le dossier OneDrive `…\Semestre 5\Projet-3` ; hors OneDrive.
- Recommandation : hors OneDrive. OneDrive synchroniserait le `.venv` (environ 1 Go de bibliothèques) et le dossier `.git`, avec des risques de fichiers verrouillés pendant la synchronisation ; le chemin OneDrive contient aussi un accent. GitHub sert déjà de sauvegarde.
- Contrainte constatée : la racine `C:\` n'est pas accessible en écriture sur le PC de Saliou (`C:\Projets` impossible à créer).
- Décision : copie locale dans `C:\Users\SERIGNE SALIOU SEYE\Projets\horizon-decrochage-tutorat` (hors OneDrive ; espaces du nom d'utilisateur à gérer par des guillemets).
- Statut : validée (Saliou, 18/11)

## D-05 — Version de Python et de pandas
- Date / tâche : 18/11/2026 — GP-01
- Question : le `.venv` a été créé avec le Python du PC (3.14.3) ; `requirements.txt` fixe donc pandas 3.1.1 et numpy 2.5.5. Or pandas 3.x n'existe pas pour Python 3.10 (vérifié : `pip download pandas==3.1.1 --python-version 3.10` ne trouve aucune version), alors que CLAUDE.md §4 annonce « Python 3.10 ou plus ». Sur une machine en 3.10, `pip install -r requirements.txt` échouerait.
- Options : (a) garder pandas 3.1.1 et écrire « Python 3.11 ou plus » dans le README et CLAUDE.md ; (b) revenir à pandas 2.3.x et numpy 2.2.x, installables de Python 3.10 à 3.14 ; (c) ne rien changer.
- Recommandation : (b) si la version de Python de l'enseignant est inconnue, car c'est la seule option qui respecte « 3.10 ou plus » ; sinon (a). Demander la version de l'enseignant au point d'étape serait le plus sûr.
- Vérification (session de pilotage, 18/11) : l'option (b) est impossible, car numpy 2.2.x n'existe pas pour Python 3.14 (Python du PC de Saliou). Avec les versions actuelles, numpy 2.5.5 exige Python 3.12 au minimum ; scikit-survival, lifelines, scikit-learn et statsmodels existent tous pour Python 3.14 sous Windows.
- Décision : option (a) adaptée : garder les versions installées et exiger **Python 3.12 ou plus** (README et CLAUDE.md).
- Statut : validée (Saliou, 18/11)
