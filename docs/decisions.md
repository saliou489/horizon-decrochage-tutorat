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

## D-06 — Table etudiants : corrections de forme
- Date / tâche : 18/11/2026 — DA-02
- Question : comment traiter les écarts de forme relevés par l'audit (ETU-01 à ETU-04, ETU-12 à ETU-17, ETU-20, ETU-22, ETU-23) ?
- Options : corriger ; laisser tel quel ; mettre à manquant.
- Recommandation : corriger. Ce sont des écritures différentes d'une même information (casse, espaces, abréviations, virgule décimale, unité), sans perte ni invention.
- Décision : en-têtes renommés comme le LISEZMOI ; identifiants en majuscules sans espaces ; virgule → point, unités « ans » / « km » retirées ; genre → F / M ; filière, région, mention, emploi, boursier ramenés aux modalités du LISEZMOI ; doublons exacts supprimés ; cases vides laissées vides.
- Statut : validée (Saliou, 18/11)

## D-07 — Table etudiants : quasi-doublons (D1)
- Date / tâche : 18/11/2026 — DA-02
- Question : 24 étudiants apparaissent deux fois avec des valeurs différentes. Laquelle garder ?
- Constat (pilotage) : les deux lignes ne diffèrent que par la distance, de quelques dixièmes de km.
- Options : garder la première ligne ; moyenne des distances ; distance à manquant.
- Recommandation : garder la première ligne du fichier (écart sans effet, règle la plus simple).
- Décision : garder la première ligne.
- Statut : validée (Saliou, 18/11)

## D-08 — Table etudiants : notes du bac et âges impossibles (D2)
- Date / tâche : 18/11/2026 — DA-02
- Question : que faire des notes du bac hors [10 ; 20] (25,5, 112, 135) et des âges hors [17 ; 35] (0, 3, 99, 150, 210) ?
- Constat (pilotage) : l'hypothèse « virgule oubliée » est fausse : 135 apparaît avec « Passable », incompatible avec 13,5. Ce sont des valeurs sans sens. Aucune autre note antérieure au bac n'existe dans les données ; les notes universitaires (activite_hebdo) sont postérieures à la rentrée et ne doivent pas servir à corriger une variable de départ.
- Options : mettre à manquant ; tenter une correction (÷ 10) ; supprimer la ligne.
- Recommandation : mettre la valeur à manquant, garder la ligne et la mention.
- Décision : note_bac et age hors bornes (sentinelles comprises) → manquant ; mention_bac conservée.
- Statut : validée (Saliou, 18/11)

## D-09 — Table etudiants : distances (D3)
- Date / tâche : 18/11/2026 — DA-02
- Question : que faire des distances négatives, des sentinelles (9999) et des 514 distances supérieures à 51,7 km ?
- Constat (pilotage) : aucune distance > 51,7 km ne concerne un étudiant de Dakar ; elles viennent de régions éloignées du campus. Elles sont plausibles.
- Options : négatives → valeur absolue ou manquant ; grandes distances → garder ou plafonner.
- Recommandation : négatives et sentinelles → manquant (signe non vérifiable) ; grandes distances gardées.
- Décision : comme recommandé.
- Statut : validée (Saliou, 18/11)

## D-10 — Table etudiants : cohérence mention / note (D4)
- Date / tâche : 18/11/2026 — DA-02
- Question : 37 lignes ont une mention incompatible avec la note ; 154 mentions sont vides.
- Options : la note fait foi ; la mention fait foi ; les deux à manquant.
- Recommandation : la note fait foi (plus précise) ; la mention est recalculée à partir de la note quand elles se contredisent ou quand la mention est vide. Seuils du bac : Passable [10 ; 12[, Assez bien [12 ; 14[, Bien [14 ; 16[, Très bien ≥ 16 (une note de 12 exactement est Assez bien). La mention découle de la note par définition : ce n'est pas une imputation.
- Décision : comme recommandé ; si la note est manquante, la mention d'origine est conservée.
- Statut : validée (Saliou, 18/11)

## D-11 — Table etudiants : codage 0 / 1 de boursier (D5)
- Date / tâche : 18/11/2026 — DA-02
- Question : « 0 » et « 1 » valent-ils Non et Oui ?
- Recommandation : oui (codage standard).
- Décision : 0 → Non, 1 → Oui.
- Statut : validée (Saliou, 18/11)

## D-12 — Table inscriptions : corrections de forme
- Date / tâche : 18/11/2026 — DA-03
- Question : comment traiter les statuts écrits de plusieurs façons (INS-04), les 4 formats de date (INS-05, INS-06) et les doublons exacts (INS-01, INS-02) ?
- Constat (pilotage) : les 4 formats (AAAA-MM-JJ, JJ/MM/AAAA, AAAA/MM/JJ, « 7 oct. 2024 ») se lisent tous sans ambiguïté.
- Décision : statuts ramenés à `inscrit`, `abandon`, `transfert` ; dates converties en AAAA-MM-JJ ; doublons exacts supprimés.
- Statut : validée (Saliou, 18/11)

## D-13 — Table inscriptions : dates de début et de fin inversées (I1)
- Date / tâche : 18/11/2026 — DA-03
- Constat (pilotage) : les 12 lignes signalées par INS-07, INS-09 et INS-10 sont les mêmes étudiants ; pour chacun, date_fin est exactement la date de rentrée de sa cohorte (2024-10-07 ou 2025-10-06) et date_debut est postérieure. Les deux dates ont été saisies à l'envers.
- Options : échanger les dates ; mettre à manquant ; exclure.
- Décision : échanger date_debut et date_fin pour ces lignes (règle : date_fin < date_debut et date_fin = rentrée de la cohorte).
- Statut : validée (Saliou, 18/11)

## D-14 — Table inscriptions : abandons datés après la fin du suivi (I2)
- Date / tâche : 18/11/2026 — DA-03
- Constat : 6 abandons ont une date_fin en 2027, au-delà des 30 semaines de suivi.
- Décision : considérés comme « aucune sortie déclarée pendant le suivi » ; la ligne est gardée ; le décrochage éventuel sera repéré par la règle d'inactivité, sinon censure à la semaine 30.
- Statut : validée (Saliou, 18/11)
- **Révision (19/11) : conséquence corrigée par D-33.** L'hypothèse « la règle d'inactivité repérera leur décrochage » était fausse : leurs lignes d'activité s'arrêtent sans semaine inactive enregistrée.

## D-15 — Table inscriptions : statut vide (I3)
- Date / tâche : 18/11/2026 — DA-03
- Constat : 41 statuts vides, tous sans date_fin.
- Décision : traités comme « aucune sortie déclarée » ; statut d'origine laissé vide et cas marqué ; la règle d'inactivité repère les décrochages non déclarés.
- Statut : validée (Saliou, 18/11)

## D-16 — Table inscriptions : abandons sans date (I4)
- Date / tâche : 18/11/2026 — DA-03
- Constat : 22 abandons sans date_fin.
- Décision : statut `abandon` gardé, date_fin laissée vide ; la semaine de l'événement sera déterminée à partir de l'activité en DA-07 (règle à valider à ce moment-là).
- Statut : validée (Saliou, 18/11)

## D-17 — Identifiants sans correspondance entre etudiants et inscriptions (I5)
- Date / tâche : 18/11/2026 — DA-03
- Constat (pilotage) : 14 inscriptions concernent des identifiants absents de etudiants, sans faute de frappe évidente (un seul rapprochement possible, non convaincant). 10 étudiants n'ont aucune inscription ; or tous les étudiants d'une même cohorte ont la même date de rentrée (hors les 12 lignes inversées).
- Décision : les 14 inscriptions orphelines sont exclues de l'analyse et conservées dans un fichier de rejets ; les 10 étudiants sans inscription sont gardés avec la rentrée de leur cohorte et « aucune sortie déclarée », cas marqué.
- Statut : validée (Saliou, 18/11)

## D-18 — Table inscriptions : transfert daté après la fin du suivi
- Date / tâche : 18/11/2026 — DA-03
- Question (posée par la session d'exécution dans le compte rendu de C03) : aucune décision ne couvre un transfert dont la date_fin tombe après les 30 semaines de suivi (D-14 ne traite que les abandons).
- Constat : le cas n'existe pas dans les données (les 117 transferts sont datés pendant le suivi).
- Options : (A) ne rien changer, le code s'arrête si le cas se présente ; (B) le traiter comme D-14 (« aucune sortie déclarée »).
- Recommandation : A (cas absent ; s'arrêter devant un cas imprévu est le comportement le plus sûr ; pas de code sans usage).
- Décision : A. Si le cas apparaît, le nettoyage s'arrête et la règle sera décidée à ce moment-là.
- Statut : validée (Saliou, 18/11)

## D-19 — Table activite_hebdo : corrections de forme et valeurs impossibles
- Date / tâche : 19/11/2026 — DA-04
- Constat (pilotage) : les 70 lignes à semaine invalide (−1, 0, 31, 32, 99) appartiennent toutes à des étudiants qui ont déjà toutes leurs semaines de suivi : aucune semaine manquante qu'elles pourraient combler. Les connexions plausibles vont jusqu'à 26 par semaine, puis aucune valeur avant 3 604.
- Décision : identifiants en majuscules ; virgule décimale → point ; entiers écrits « 10.0 » → 10 ; lignes identiques (même étudiant, même semaine, même contenu) supprimées ; lignes à semaine hors [1 ; 30] supprimées ; connexions négatives ou > 100, devoirs_rendus hors [0 ; 2], note_moyenne = −1 → manquant ; connexions de 21 à 26 conservées.
- Statut : validée (Saliou, 19/11)

## D-20 — Table activite_hebdo : semaines en double avec des valeurs différentes (A1)
- Date / tâche : 19/11/2026 — DA-04
- Constat (pilotage) : 176 couples (étudiant, semaine) ; l'écart porte presque toujours sur nb_connexions_lms (5 au plus) ; dans 11 cas, une copie indique 0 connexion et l'autre une activité, ce qui peut changer la règle des 4 semaines.
- Options : garder la première ligne ; garder la valeur la plus haute pour l'activité ; moyenne.
- Recommandation : valeur la plus haute pour nb_connexions_lms et devoirs_rendus (si une source a vu de l'activité, l'étudiant n'était pas inactif : on évite de fabriquer de faux décrochages) ; première valeur pour note_moyenne et absences.
- Décision : comme recommandé.
- Statut : validée (Saliou, 19/11)

## D-21 — Table activite_hebdo : notes hebdomadaires supérieures à 20 (A2)
- Date / tâche : 19/11/2026 — DA-04
- Constat (pilotage) : 110 notes entre 34,4 et 163,6. Divisées par 10, elles ont une moyenne de 10,42 et un écart-type de 2,50, la même distribution que les notes valides (10,40 et 2,43) ; des valeurs au hasard entre 0 et 20 s'écarteraient nettement plus des notes habituelles de l'étudiant (écart médian 4,97 contre 1,67 observé). C'est un décalage de la virgule (12,2 saisi 122). Contrairement à D-08 (note du bac), les données confirment ici l'hypothèse.
- Options : diviser par 10 ; mettre à manquant.
- Décision : diviser par 10, avec cette justification dans le journal.
- Statut : validée (Saliou, 19/11)

## D-22 — Conversion d'une date en numéro de semaine (A3)
- Date / tâche : 19/11/2026 — DA-04 (point ouvert de DA-07, tranché ici car nécessaire à D-23)
- Décision : semaine = (date − date_debut en jours) // 7 + 1. Le jour de la rentrée et les 6 jours suivants forment la semaine 1, conformément au LISEZMOI (« la semaine 1 commence ce jour »).
- Statut : validée (Saliou, 19/11)

## D-23 — Table activite_hebdo : activité après la sortie déclarée (A4)
- Date / tâche : 19/11/2026 — DA-04
- Constat (pilotage, avec les dates corrigées par D-13 et la règle D-22) : 54 lignes, pour 34 étudiants ayant tous abandonné, montrent une activité 1 ou 2 semaines après la semaine de sortie. Elles ne changent pas l'événement (l'abandon déclaré fixe la semaine).
- Options : retirer ces lignes ; les garder.
- Décision : retirées de la table nettoyée et conservées dans un fichier de rejets (traçabilité, comme D-17).
- Statut : validée (Saliou, 19/11)

## D-24 — Table tutorat : corrections de forme
- Date / tâche : 19/11/2026 — DA-04
- Décision : en-tête « ID Etudiant » → id_etudiant ; doublons exacts supprimés (il reste une ligne par étudiant tutoré) ; type_tuteur ramené à `pair` (« pair (étudiant avancé) », « PAIR », « étudiant »…) ou `enseignant` (« ENSEIGNANT », « Prof »…) ; nb_seances ≤ 0 → manquant (semaine_debut est la semaine de la première séance : au moins une séance a eu lieu), l'étudiant reste tutoré ; tutorats d'identifiants absents de etudiants → fichier de rejets (comme D-17).
- Statut : validée (Saliou, 19/11)

## D-25 — Table tutorat : tutorat commencé après la fin du suivi (T1)
- Date / tâche : 19/11/2026 — DA-04
- Constat : semaine_debut = 45 ou 52 pour 5 étudiants.
- Décision : considérés comme non tutorés pendant le suivi (même logique que D-14) ; ligne et valeur gardées, cas marqué.
- Statut : validée (Saliou, 19/11)

## D-26 — Table tutorat : tutorat commencé en « semaine 0 » (T2)
- Date / tâche : 19/11/2026 — DA-04
- Constat : 5 étudiants ; la semaine 0 n'existe pas dans le suivi et la vraie semaine ne peut pas être devinée.
- Décision : semaine_debut mise à manquant, cas marqué ; l'étudiant reste tutoré ; le traitement de ces cas dans l'analyse causale sera décidé en CA-01 ; ils restent dans l'analyse de survie.
- Statut : validée (Saliou, 19/11)

## D-27 — Table tutorat : tutorat commencé après la sortie déclarée (T3)
- Date / tâche : 19/11/2026 — DA-04
- Constat (avec D-13 et D-22) : 9 étudiants, 2 à 4 semaines après leur sortie (dont un aussi concerné par D-25).
- Décision : ligne gardée, cas marqué ; un tutorat postérieur à la sortie n'a pas pu influencer le décrochage : ces étudiants compteront comme non tutorés pendant leur suivi (construction du traitement en DA-07).
- Statut : validée (Saliou, 19/11)

## D-28 — Table messages : encodage et pseudonymisation
- Date / tâche : 19/11/2026 — DA-05
- Constat (pilotage) : les 40 textes à accents cassés se réparent tous en refaisant la conversion (cp1252 → UTF-8), sans erreur ni « Ã » restant. Données personnelles : 45 téléphones (toujours au format « 77 123 45 67 »), 33 e-mails (toujours « prénom.nom@exemple.sn »), 96 noms (toujours prénom + nom, introduits par « c'est » ou « je suis ») ; 129 messages concernés. Aucun autre mot en majuscule en milieu de phrase dans le reste des messages : pas de nom non introduit. Les 3 messages « après la sortie » de l'audit (X-09) étaient dus aux dates inversées : il n'en reste aucun après D-13.
- Décision : encodage réparé ; données personnelles remplacées par des balises `[NOM]`, `[TEL]`, `[EMAIL]` ; aucune table de correspondance conservée (elle serait elle-même une donnée personnelle) ; obligation légale : loi sénégalaise n° 2008-12 (RGPD pour comparaison).
- Statut : validée (Saliou, 19/11)

## D-29 — Table messages : messages vides (M1)
- Date / tâche : 19/11/2026 — DA-05
- Constat : 25 messages sans aucun mot (« », « . », espaces).
- Décision : retirés de la table et conservés dans un fichier de rejets (aucun texte à analyser ; traçabilité).
- Statut : validée (Saliou, 19/11)

## D-30 — Construction de T et E : règles de base
- Date / tâche : 19/11/2026 — DA-07
- Constat (pilotage) : le système d'activité enregistre une ligne par semaine pour chaque inscrit, même inactif (8 476 semaines à zéro activité) ; pour 100 % des sorties datées (1 004 abandons et 117 transferts), la dernière ligne d'activité est exactement la semaine de sortie. Aucune série de 4 semaines inactives ne précède un abandon ou un transfert déclaré.
- Décision : abandon daté → E = 1, T = semaine de sortie (D-22) ; série de 4 semaines consécutives sans connexion ni devoir → E = 1, T = première semaine de la série ; transfert → E = 0, T = semaine du transfert ; ni sortie ni série → E = 0, T = 30 (une série coupée par la fin du suivi ne compte pas) ; série précédant un abandon ou un transfert déclaré → arrêt du code (cas absent, D-18).
- Statut : validée (Saliou, 19/11)

## D-31 — Semaines d'activité « inconnues » (E1)
- Date / tâche : 19/11/2026 — DA-07
- Constat : 216 semaines avec connexions manquantes et aucun devoir rendu (ou l'inverse) : l'inactivité ne peut pas être affirmée. L'autre lecture (les compter inactives) change T ou E pour 20 étudiants.
- Décision : une semaine inconnue ne compte pas comme inactive et coupe une série (même logique que D-20 : ne pas fabriquer de faux décrochages) ; l'autre lecture est gardée en sensibilité.
- Statut : validée (Saliou, 19/11)

## D-32 — Abandons sans date (E2)
- Date / tâche : 19/11/2026 — DA-07 (complète D-16)
- Décision : E = 1, T = dernière semaine d'activité enregistrée (règle constatée sur 1 121 sorties datées sur 1 121).
- Statut : validée (Saliou, 19/11)

## D-33 — Abandons datés après la fin du suivi (E3, révise D-14)
- Date / tâche : 19/11/2026 — DA-07
- Constat (pilotage) : les 6 étudiants concernés ont le statut « abandon » et leurs lignes d'activité s'arrêtent entre les semaines 3 et 26, sans aucune semaine inactive : avec D-14 seul, ils seraient comptés comme n'ayant jamais décroché. Les dates de 2027 ne correspondent à aucune faute de frappe sur l'année (année − 1 ou − 2 : aucune concordance avec la dernière semaine d'activité).
- Décision : traités comme les abandons sans date (D-32) : E = 1, T = dernière semaine d'activité ; la date de 2027 est jugée inutilisable, le statut « abandon » est retenu.
- Statut : validée (Saliou, 19/11)

## D-34 — Étudiants perdus de vue (E4)
- Date / tâche : 19/11/2026 — DA-07
- Constat : 2 étudiants sans inscription (lignes reconstituées, D-17) dont l'activité s'arrête avant la semaine 30 ; nature de la sortie inconnue.
- Décision : censurés (E = 0) à leur dernière semaine d'activité (« perdus de vue ») ; noté comme limite.
- Statut : validée (Saliou, 19/11)

## D-35 — Retour d'activité après une série de 4 semaines (E5)
- Date / tâche : 19/11/2026 — DA-07
- Constat : 8 étudiants redeviennent actifs après une série de 4 semaines inactives (séries débutant entre les semaines 2 et 12, retour entre les semaines 8 et 25).
- Décision : la définition imposée (§4.3) s'applique telle quelle : E = 1 au début de la série ; noté comme limite ; la sensibilité 3 / 5 semaines en mesure l'effet.
- Statut : validée (Saliou, 19/11)
