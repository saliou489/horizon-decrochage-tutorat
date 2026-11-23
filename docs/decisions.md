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

## D-36 — Variables de base_survie : seulement celles connues à la rentrée (B1)
- Date / tâche : 19/11/2026 — DA-07
- Constat : un résumé de l'activité sur tout le suivi (ex. moyenne des connexions) dépend de la durée de présence de l'étudiant, donc du décrochage lui-même : l'utiliser comme variable explicative serait une fuite d'information.
- Décision : base_survie ne contient comme covariables que les variables de etudiants (connues à la rentrée) ; l'activité hebdomadaire va dans le format période-personne (D-39). Les variables de tutorat (type de tuteur, motif, nombre de séances) sont descriptives et ne servent pas de facteurs de confusion.
- Statut : validée (Saliou, 19/11)

## D-37 — Définition de « tutoré » dans base_survie (B2)
- Date / tâche : 19/11/2026 — DA-07 (complète D-25, D-26, D-27)
- Constat (pilotage) : sur 1 255 étudiants ayant un tutorat, 1 199 l'ont commencé avant la semaine T, 31 la semaine même de T, 20 après T, 5 à une semaine inconnue.
- Décision : tutoré = tutorat commencé strictement avant la semaine T (un tutorat qui démarre la semaine de l'événement n'a pas pu l'empêcher et a pu être déclenché par les difficultés) ; semaine inconnue (D-26) → tutoré, semaine inconnue, traitement décidé en CA-01. Résultat : 1 204 tutorés. Une colonne statut_tutorat indique le cas de chaque étudiant.
- Statut : validée (Saliou, 19/11)

## D-38 — Sensibilité du seuil d'inactivité (B3)
- Date / tâche : 19/11/2026 — DA-07
- Constat (pilotage) : 1 445 décrochages à 3 semaines, 1 440 à 4, 1 435 à 5 (écart < 0,5 %).
- Décision : base_survie contient T et E au seuil de référence (4 semaines) et à 3 et 5 semaines ; la lecture alternative de D-31 (semaines inconnues comptées inactives) est une option de la fonction de construction.
- Statut : validée (Saliou, 19/11)

## D-39 — Format période-personne (B4)
- Date / tâche : 19/11/2026 — DA-07
- Décision : une ligne par étudiant et par semaine, de 1 à T (121 938 lignes) : activité de la semaine, état (actif / inactif / inconnu, D-31), indicateur d'événement (1 seulement la semaine T si E = 1) et indicateur « tutorat commencé », qui vaut 1 à partir de la semaine qui suit le début du tutorat (cohérent avec D-37), et reste vide pour les 5 tutorats à semaine inconnue.
- Statut : validée (Saliou, 19/11)

## D-40 — Planning version 2
- Date / tâche : 19/11/2026 — GP-03
- Question : faut-il continuer à suivre le planning du cahier des charges ?
- Décision : le planning du cahier sert d'inspiration ; la référence est `docs/planning.md` (version 2 : CA-01 avancé au 20/11, même rythme de travail qu'au 18/11 pour garder une avance face aux imprévus). Les exigences notées du cahier (captures datées, revues et rétrospectives, livrables, date de rendu) restent obligatoires.
- Statut : validée (Saliou, 19/11)

## D-41 — Session de relecture indépendante
- Date / tâche : 19/11/2026 — GP-03
- Question (proposée par Saliou) : ajouter une session chargée uniquement de relire consignes, code et sécurité ?
- Constat : la session de pilotage rédige les consignes et vérifie leurs résultats ; elle relit donc en partie son propre travail (deux erreurs de consigne ont été trouvées par la session d'exécution : ETU-09 et la conséquence de D-14).
- Décision : une session Claude Code de relecture, dans un clone séparé, qui ne modifie rien et écrit seulement ses rapports dans `docs/revues/` ; mission dans `docs/consignes/R00_mission_relecteur.md` ; constats classés par gravité avec preuve ; pas de remise en cause d'une décision validée sans fait nouveau ; 4 points de contrôle (R01 nettoyage et base_survie, R02 spécification causale, R03 sécurité LLM, R04 contrôle final).
- Statut : validée (Saliou, 19/11)

## D-42 — Modèles semaine par semaine : seulement l'activité des semaines précédentes (suite de RV01-01)
- Date / tâche : 20/11/2026 — DA-07 (pour SV, ML et le score hebdomadaire)
- Constat (relecture RV01-01, vérifié par le pilotage) : dans `base_periode_personne.csv`, l'activité de la semaine T fait partie de la définition de l'événement (un décrochage silencieux commence par une semaine inactive) ; une semaine inactive contient un événement dans 59,1 % des cas contre 0,85 % pour une semaine active. Un modèle qui utiliserait l'activité de la semaine en cours lirait l'événement au lieu de le prédire ; en semaine T, les semaines T+1 à T+3 ne sont d'ailleurs pas encore connues.
- Décision : dans tout modèle semaine par semaine, les covariables d'activité sont celles de la **semaine précédente ou d'avant**, jamais celles de la semaine en cours ; le pipeline produit des colonnes décalées d'une semaine (`*_prec`) et les modèles n'utilisent que celles-là.
- Statut : validée (Saliou, 20/11)

## D-43 — Liste officielle des variables de la rentrée (suite de RV01-04)
- Date / tâche : 20/11/2026 — DA-07 (pour SV, ML, CA)
- Constat (RV01-04) : `base_survie.csv` contient aussi des colonnes connues après la rentrée (`nb_seances`, `tutore`, `statut_tutorat`, `type_tuteur`, `motif_orientation`, `semaine_debut_tutorat`) ; chez les tutorés, `nb_seances` suit surtout la durée de présence (corrélation de 0,73 avec T).
- Décision : `config.COVARIABLES_RENTREE` liste les 10 variables connues le jour de la rentrée (cohorte, genre, âge, boursier, filière, mention et note du bac, région, distance, emploi) ; les modèles sélectionnent leurs covariables fixes dans cette liste, jamais par exclusion (« tout sauf T et E ») ; un test vérifie qu'elle ne contient que des colonnes de la table `etudiants`.
- Statut : validée (Saliou, 20/11)

## D-44 — Pas de verrouillage de toutes les dépendances (suite de RV01-08)
- Date / tâche : 20/11/2026 — DO-01
- Constat (RV01-08) : `requirements.txt` fige les 5 paquets installés directement ; l'installation en compte 53. Un `pip freeze` fait sous Windows contient des paquets propres à Windows (ex. `pywin32`, utilisé par Jupyter) qui ne s'installent pas sous Linux : un fichier verrouillé empêcherait l'installation chez l'enseignant.
- Décision : garder les 5 paquets directs figés ; signaler dans le README que les dépendances indirectes ne sont pas figées et que le projet a été testé sous Windows avec Python 3.14.3.
- Statut : validée (Saliou, 20/11)

## D-45 — Rattrapage après la journée du 21/11 (option A)
- Date / tâche : 22/11/2026 — GP-05
- Constat : aucun travail le 21/11 ; environ 1,5 jour de retard sur le planning v2 ; environ 30 h de travail restant pour environ 26 h disponibles au rythme prévu.
- Options : (A) ajouter environ 1 h par jour jusqu'au 25/11 et travailler la journée complète du 22/11, en gardant le LLM et le tableau de bord ; (B) réduire le LLM et le tableau de bord à une version minimale.
- Décision : A (LLM et tableau de bord valent 2 points au barème).
- Statut : validée (Saliou, 22/11)

## D-46 — Kaplan-Meier : sous-groupes et tests multiples (SV-01, K1 et K3)
- Date / tâche : 22/11/2026 — SV-01
- Décision : sous-groupes du cahier (boursier, filière, mention, emploi) ; les valeurs manquantes d'une variable sont exclues de sa comparaison et leur nombre est indiqué ; test du log-rank (à k groupes pour filière et mention) ; 4 tests → seuil de Bonferroni 0,05 / 4 = 0,0125, en plus des p-valeurs brutes.
- Statut : validée (Saliou, 22/11)

## D-47 — Définition d'une semaine critique (SV-01, K2)
- Date / tâche : 22/11/2026 — SV-01
- Constat (pilotage) : risque hebdomadaire moyen = 1 440 décrochages / 121 938 semaines-étudiant = 1,18 %.
- Options : semaine dont le risque ≥ 1,5 fois le risque moyen (semaines 4 à 7, 15 et 16) ; semaine dont la borne basse de l'IC 95 % dépasse le risque moyen (semaines 3 à 8, 15 à 17).
- Décision : risque de la semaine ≥ 1,5 fois le risque moyen (règle simple à expliquer) ; l'IC 95 % de chaque semaine est aussi affiché.
- Statut : validée (Saliou, 22/11)

## D-48 — Cox explicatif sur tous les étudiants (SV-02, C1)
- Date / tâche : 22/11/2026 — SV-02
- Décision : le Cox de SV-02 (hazard ratios et interprétation) est ajusté sur les 5 000 étudiants ; le Cox prédictif, entraîné sur la cohorte 2024 et évalué sur 2025, est construit en SV-03 / SV-04.
- Statut : validée (Saliou, 22/11)

## D-49 — Variables du Cox (SV-02, C2)
- Date / tâche : 22/11/2026 — SV-02 (et SV-03 / SV-04)
- Constat (pilotage) : depuis D-10, la mention est calculée à partir de la note du bac (information redondante) ; les 14 régions n'apportent rien au-delà de la distance (AIC partiel 23 698,3 avec les 14 régions contre 23 694,4 avec Dakar / hors Dakar) ; la distance est très asymétrique (médiane 9,8 km, 1 % au-delà de 152 km).
- Décision : covariables issues de `COVARIABLES_RENTREE` : genre (réf. F), âge, boursier (réf. Non), filière (réf. Informatique, la plus nombreuse), note du bac (pas la mention), région regroupée en Dakar / hors Dakar (réf. Dakar), log2 de la distance (effet d'un doublement), emploi (réf. Non) ; la cohorte sert de strate (D-51).
- Statut : validée (Saliou, 22/11)

## D-50 — Valeurs manquantes dans les modèles (SV-02, C3)
- Date / tâche : 22/11/2026 — SV-02 (et SV-03 / SV-04)
- Constat : 405 étudiants (8 %) ont au moins une covariable manquante.
- Décision : variables qualitatives → modalité « (manquant) » ; variables numériques → médiane, calculée sur les données d'ajustement (pour SV-03 / SV-04 : sur la cohorte 2024 seulement) ; sensibilité : même modèle sur les dossiers complets (écart maximal des HR constaté par le pilotage : 0,033).
- Statut : validée (Saliou, 22/11)

## D-51 — Hypothèse des risques proportionnels (SV-02, C4)
- Date / tâche : 22/11/2026 — SV-02
- Décision (fixée avant l'analyse finale) : test des résidus de Schoenfeld par variable (lifelines, transformation « rank ») ; si p < 0,05 : variable qualitative → stratification ; variable numérique → interaction avec la période (semaines 1 à 8 / 9 à 30). Constat du pilotage : seule la cohorte viole l'hypothèse (p = 0,04) → Cox stratifié par cohorte ; après stratification, aucune variable sous 0,05 (p minimum 0,36).
- Statut : validée (Saliou, 22/11)

## D-52 — Version de pandas : 2.3.3 (SV-01, C09)
- Date / tâche : 22/11/2026 — SV-01
- Constat : lifelines 0.30.3 (dernière version, utilisée pour Kaplan-Meier et Cox) exige officiellement `pandas<3.0,>=2.1` ; son installation a fait passer pandas de 3.1.1 à 2.3.3. Avec 2.3.3 : 134 tests passent ; les notebooks 01 à 03, relancés par le pilotage, donnent les mêmes sorties ; seul `base_periode_personne.csv` change, sur 45 notes (écart de 1e-15, bruit de calcul sans effet).
- Options : garder pandas 2.3.3 ; forcer 3.1.1 (combinaison non supportée : avec des versions exactes, `pip install -r requirements.txt` échouerait chez l'enseignant) ; renoncer à lifelines.
- Décision : `pandas==2.3.3` tant que lifelines exige pandas < 3. Toute nouvelle bibliothèque doit être compatible avec pandas 2.3.3 (vérifié par le pilotage pour statsmodels 0.15.0 et scikit-survival 0.28.0).
- Statut : validée (Saliou, 22/11)

## D-53 — Approche contre le temps immortel : une « photo » (landmark) à la semaine 8 (CA-01, Q1)
- Date / tâche : 22/11/2026 — CA-01
- Constat (pilotage, sans regarder le décrochage par équipe) : 1 245 tutorats commencent pendant le suivi, entre les semaines 3 et 25 ; 851 (68,4 %) au plus tard en semaine 8. Photos comparées : L = 6 → 4 473 étudiants, 560 tutorés, 16,2 % de futurs tutorés chez les non-tutorés, plus grand écart standardisé après pondération 0,115 (critère non atteint) ; L = 8 → 4 316, 773, 11,0 %, 0,060 ; L = 10 → 4 225, 971, 5,3 %, 0,057 (mais 62 tutorés partis avant la photo et 20 semaines de suivi seulement).
- Options : (A) analyse landmark (photo à la semaine L) + pondération IPTW ; (B) Cox avec un tutorat « dépendant du temps » ; (C) essais séquentiels (une photo par semaine de 3 à 12, empilées).
- Décision : (A) en analyse principale, photo à la fin de la semaine L = 8 : bon compromis entre la part des tutorats pris en compte, la dilution et la durée de suivi ; la photo tombe juste après la vague de décrochage des semaines 4 à 7 et avant le pic des semaines 15-16 ; l'équilibre est atteignable ; c'est l'exemple du cahier. (B) = spécification alternative de CA-05 (D-58) ; (C) est citée dans le rapport comme piste d'amélioration.
- Statut : validée (Saliou, 22/11)

## D-54 — Règles de la photo (CA-01, Q2)
- Date / tâche : 22/11/2026 — CA-01 (complète D-25, D-26, D-37 ; répond à RV01-05)
- Décision :
  1. sur la photo : les étudiants encore suivis et sans décrochage à la fin de la semaine 8 (T > 8) ;
  2. tutoré à la photo : `semaine_debut_tutorat` ≤ 8 ;
  3. un tutorat commencé après la semaine 8 (ou hors suivi, D-25) compte comme « pas tutoré » à la photo : ni déplacé chez les tutorés (cela recréerait le temps immortel), ni retiré (ce serait choisir les équipes avec l'avenir) ; conséquence assumée : l'effet est un peu dilué ;
  4. semaine de début inconnue (D-26) : exclus de l'analyse causale (4 étudiants sur la photo de la semaine 8), conservés dans l'analyse de survie ;
  5. suivi de la semaine 9 à la semaine 30 (durée = T − 8, même E) ;
  6. variantes (seuils de 3 et 5 semaines, photos à L = 6 et 10) : population et équipes recalculées avec `T_seuilX` / `E_seuilX` et la semaine L de la variante (tutoré si début ≤ L < T).
- Résultat (pilotage) : 4 316 étudiants sur la photo, 773 tutorés (17,9 %), 3 543 non tutorés dont 389 futurs tutorés (11,0 %).
- Statut : validée (Saliou, 22/11)

## D-55 — DAG et variables du score de propension (CA-01, Q3)
- Date / tâche : 22/11/2026 — CA-01, CA-02
- Constat (pilotage) : 84 % des tutorats démarrent sur une difficulté (notes faibles 486, absences répétées 326, signalement enseignant 240 ; demande personnelle 203). Dans les 2 semaines qui précèdent leur début, les futurs tutorés ont des notes plus basses (écart standardisé de −0,44 à −0,93 selon la semaine de début) et plus d'absences (+0,43 à +0,64) que les étudiants encore suivis et pas encore tutorés : le tutorat arrive juste après une mauvaise passe. Pondération sur l'activité des semaines 1 à 2 : les tutorés restent plus faibles sur les semaines 1 à 8 (notes −0,33, absences +0,27) ; pondération sur les semaines 1 à 8 : tous les écarts ≤ 0,10.
- Décision :
  - DAG : profil à la rentrée → activité, tutorat, décrochage ; activité des semaines 1 à 8 → tutorat, décrochage ; tutorat → décrochage (effet cherché) et tutorat → activité après son début → décrochage (médiateur) ; facteurs non mesurés (motivation, famille, santé) → tutorat, activité, décrochage ;
  - variables du score : profil codé comme le Cox (D-49, D-50 : âge, note du bac, log2 de la distance, genre, boursier, filière, région Dakar / hors Dakar, emploi, cohorte en variable) + moyenne, sur les semaines 1 à 8, de `nb_connexions_lms`, `devoirs_rendus`, `note_moyenne` et `absences` (moyenne des semaines renseignées ; médiane de la photo si aucune) ;
  - jamais dans le score : l'activité postérieure à la photo, `nb_seances`, `type_tuteur`, `motif_orientation`, T, E et toute autre colonne de tutorat ;
  - facteurs non mesurés : E-value (D-58) ; fenêtre d'activité des semaines 1 à 2 (avant tout tutorat) en sensibilité.
- Limite écrite d'avance : pour les tutorats commencés tôt, une partie de la fenêtre 1 à 8 est postérieure au début ; si le tutorat a déjà amélioré l'activité, une partie de l'effet est absorbée.
- Statut : validée (Saliou, 22/11)

## D-56 — Score de propension, poids et équilibre (CA-02, CA-03)
- Date / tâche : 22/11/2026 — CA-02, CA-03
- Décision :
  - score : régression logistique sans pénalité (statsmodels, GLM binomial, effets principaux) ; AUC rapportée ;
  - poids stabilisés visant l'effet moyen sur toute la photo (ATE) : P(tutoré) / score pour les tutorés, (1 − P(tutoré)) / (1 − score) pour les autres ; troncature aux 1er et 99e percentiles de l'ensemble des poids ; taille effective de chaque équipe rapportée ;
  - équilibre : différence standardisée (dénominateur : écart-type combiné avant pondération) pour chaque variable numérique et chaque modalité de chaque variable qualitative (références et « (manquant) » comprises) ; critère |SMD| < 0,1 partout ; love plot ; si le critère n'est pas atteint : une seule retouche, fixée d'avance (ajout au score des carrés des variables numériques) ; si elle ne suffit pas, le résultat est rapporté tel quel ;
  - support commun : [plus grand des minimums ; plus petit des maximums] du score des deux équipes ; analyse principale sur tous les étudiants ; exclusion des étudiants hors support en sensibilité.
- Constat (pilotage, photo de la semaine 8) : AUC 0,727 ; 54 étudiants hors support (8 tutorés, 46 non) ; poids tronqués à [0,289 ; 2,794] ; tailles effectives 518 / 773 et 3 431 / 3 543 ; |SMD| maximal 0,757 avant pondération, 0,060 après.
- Statut : validée (Saliou, 22/11)

## D-57 — Mesures de l'effet et incertitude (CA-04)
- Date / tâche : 22/11/2026 — CA-04
- Décision, sur la photo de la semaine 8 (semaines 9 à 30) :
  - courbes de Kaplan-Meier pondérées des deux équipes ; risque de décrochage à la semaine 30 (1 − S) dans chaque équipe, leur différence et leur rapport (RR) ;
  - différence de RMST : aire sous les courbes pondérées entre la fin de la semaine 8 et la semaine 30 (22 semaines) ;
  - HR pondéré : Cox à une seule variable (tutoré à la photo), pondéré, liens d'Efron ; proportionnalité testée (Schoenfeld, « rank ») ; si p < 0,05, c'est écrit et le HR se lit comme une moyenne sur la période ;
  - phrases phares de la note de synthèse : le risque à 30 semaines dans chaque équipe et les semaines gagnées (RMST) ; le HR vient en complément ;
  - incertitude : bootstrap, IC percentile à 95 % ; 500 tirages avec remise des étudiants de la photo (graine `SEED` = 42) ; toute la chaîne est refaite à chaque tirage (score, poids, troncature, courbes, RMST, HR) ; 200 tirages pour chaque variante de sensibilité. Si `run_all.py` dépasse 15 min sur le PC de Saliou, seul le nombre de tirages des variantes peut baisser (100).
- Statut : validée (Saliou, 22/11)

## D-58 — Analyses de sensibilité (CA-05) et bonus F8
- Date / tâche : 22/11/2026 — CA-05 (et SV-05)
- Décision :
  1. seuils d'inactivité de 3 et 5 semaines (photo et équipes recalculées, D-54) ;
  2. E-value calculée sur le RR du décrochage à 30 semaines (estimation et borne de l'IC la plus proche de 1) ;
  3. spécification alternative : Cox avec un tutorat dépendant du temps sur `base_periode_personne` (tous les étudiants dès la semaine 1, sauf semaine de début inconnue ; variable `tutorat_commence` ; profil codé comme en D-55 + moyenne de chaque variable d'activité sur les semaines 1 à t − 1, médiane si aucune ; strates : cohorte ; IC du modèle) ;
  4. photos à L = 6 et L = 10 (fenêtre d'activité des semaines 1 à L) ;
  5. fenêtre d'activité des semaines 1 à 2 ;
  6. support commun strict ;
  les variantes sont présentées à côté de l'analyse principale, jamais à sa place ;
  bonus (Could, F8) : même chaîne séparément chez les boursiers et les non-boursiers (score refait sans la variable boursier) ; différence entre les deux différences de RMST, avec IC bootstrap.
- Statut : validée (Saliou, 22/11)
- Révision (22/11, relecture RV02) : le point 3 est remplacé par D-62 ; nombres de tirages, support strict et autres réglages précisés par D-61.

## D-59 — Garde-fous de l'analyse causale, écrits avant le résultat
- Date / tâche : 22/11/2026 — CA-01 à CA-05
- Décision :
  - conception d'abord : photo, score, poids et équilibre (CA-01 à CA-03) sont produits et relus (R02) avant tout calcul du décrochage par équipe (CA-04) ; aucune comparaison de T, E ou de la survie entre tutorés et non tutorés avant CA-04 ;
  - biais attendus, écrits d'avance : estimation plutôt prudente (plus proche de « aucun effet » que la réalité) à cause des 11 % de futurs tutorés chez les non-tutorés, de la fenêtre d'activité 1 à 8 et du caractère marginal du HR ; biais inverse possible : la motivation non mesurée (demandes personnelles) ;
  - vocabulaire : « effet » seulement pour cette estimation, avec ses trois conditions rappelées (pas de facteur caché important ; chaque profil pouvait être tutoré ou non ; score bien construit) ; le résultat est rapporté quel qu'il soit.
- Statut : validée (Saliou, 22/11)
- Complément (22/11, relecture RV02-07) : deux biais de plus et la phrase exacte de ce qui est estimé, en D-61 (point 11).

## D-60 — Modèle non linéaire de survie : gradient boosting à temps discret avec scikit-learn (SV-03, Q1)
- Date / tâche : 22/11/2026 — SV-03
- Constat (pilotage) : scikit-survival 0.28.0 (forêt aléatoire de survie, conseillée au cahier §7) dépend d'`ecos`, qui n'a de version précompilée que jusqu'à Python 3.12 (roues Windows cp37 à cp312 ; sur Linux, installation seulement en compilant). Le PC de Saliou est en Python 3.14, sans compilateur ; numpy 2.5 exige Python ≥ 3.12 (D-05) : l'enseignant devrait donc avoir exactement Python 3.12.
- Options : (A) forêt aléatoire de survie (scikit-survival) en imposant Python 3.12 ; (B) gradient boosting de survie à temps discret avec scikit-learn : un `HistGradientBoostingClassifier` estime, pour chaque étudiant encore suivi, le risque de décrocher dans la semaine (table semaine par semaine, D-39) ; la courbe de survie est le produit des (1 − risque) semaine après semaine.
- Décision : (B). Conforme au cahier (F4 : « gradient boosting de survie » ; « Random Survival Forest ou équivalent ») ; aucun changement d'environnement ; `scikit-learn==1.9.1` (s'installe sous Python 3.14 avec pandas 2.3.3). Le Brier score intégré et la calibration sont codés dans `src/ml_survie.py` et testés ; le pilotage les vérifie contre scikit-survival dans son propre environnement (ce n'est pas une dépendance du projet).
- Statut : validée (Saliou, 22/11)

## D-61 — Réglages figés de CA-04 et CA-05 (relecture RV02)
- Date / tâche : 22/11/2026 — CA-04, CA-05 (constats RV02-01, RV02-03 à RV02-07)
- Constat : la relecture RV02 a relevé 8 choix de CA-04 et CA-05 encore ouverts, qui auraient pu être tranchés après avoir vu le résultat, ainsi que des fragilités du code et des biais non écrits.
- Décision :
  1. **Bootstrap** : les covariables du score (X) et la matrice d'équilibre sont construites une fois sur la photo (médianes de la photo). Chaque tirage reprend des étudiants avec remise (index remis à zéro), puis ré-estime le score avec **la même spécification que l'analyse principale** (la retouche de D-56 n'est jamais appliquée dans un tirage), les poids, la troncature, les courbes, le RMST, le risque à 30 semaines et le HR. On rapporte la part des tirages où un |SMD| dépasse 0,1. Chaque analyse (principale, chaque variante, chaque groupe du bonus) part d'un générateur neuf `numpy.random.default_rng(SEED)`. Un tirage qui échoue (erreur, score non convergé) est remplacé par un nouveau tirage et compté.
  2. **Poids de CA-04** : les poids stabilisés tronqués, ceux du tableau d'équilibre.
  3. **Cox pondéré** : lifelines, liens d'Efron, `robust=True` pour l'ajustement principal (erreur standard « sandwich » donnée pour information ; l'IC officiel est celui du bootstrap) ; dans les tirages, seule l'estimation est utilisée. Le test de Schoenfeld sur un modèle pondéré est seulement indicatif.
  4. **Échelle et RMST** : durée = T − 8 (de 0 à 22) ; RMST = `lifelines.utils.restricted_mean_survival_time(kmf, t=22)` sur le Kaplan-Meier pondéré (aire exacte sous la courbe en escalier) ; risque à 30 semaines = 1 − S(22).
  5. **E-value** : RR = risque des tutorés / risque des non-tutorés à 30 semaines ; si RR < 1, on prend 1 / RR ; E = RR + racine(RR × (RR − 1)) ; pour l'IC, borne la plus proche de 1, et E-value = 1 si l'IC contient 1 (exemple de test : RR = 0,5 → E = 2 + √2 ≈ 3,41).
  6. **Nombre de tirages** : 500 pour l'analyse principale ; 200 pour chaque variante (seuils de 3 et 5 semaines, L = 6, L = 10, fenêtre 1 à 2, support strict) ; 200 par groupe pour le bonus. Le bootstrap est relancé par `run_all.py` ; les résultats sont enregistrés dans `data/processed/` et relus par le notebook 05 et le tableau de bord. Repli si `run_all.py` dépasse 15 min : 100 tirages pour les variantes et le bonus.
  7. **Variantes** : support strict = retirer les étudiants hors du support commun de l'analyse principale, puis refaire toute la chaîne ; L = 6 rapportée telle quelle même si l'équilibre n'est pas atteint (D-56) ; seuil de 5 semaines : les 2 étudiants de la photo qui ont moins de 8 semaines d'activité sont signalés ; fenêtre 1 à 2 : deux tableaux d'équilibre (le sien et celui de la fenêtre 1 à 8).
  8. **Diagnostic hors critère** (RV02-06) : notes et connexions des semaines 7 et 8, mention du bac, région détaillée, semaines inactives, affichés dans le notebook 05 avec leur lecture ; le score n'est pas modifié (l'activité récente est en partie un médiateur ; la mention découle de la note du bac).
  9. **Code** (RV02-03 à RV02-05) : liste positive des colonnes du score (variables numériques du score et indicatrices de `VARIABLES_COX_QUALITATIVES`, sur le principe de D-43) ; erreur si la fenêtre d'activité dépasse la semaine de la photo ; option pour retirer une variable du score (bonus) ; erreur si la régression logistique du score ne converge pas ; les 7 tests proposés par RV02-05.
  10. **Figure du DAG** (RV02-07) : ajout de la flèche en pointillés « facteurs non mesurés → activité ». Le recouvrement de la fenêtre 1 à 8 avec la période après le début (3,6 semaines sur 8 en moyenne chez les tutorés) est écrit sous la figure plutôt que dessiné (une flèche donnerait l'impression d'une boucle).
  11. **Compléments à D-59**, écrits avant le résultat : (a) la photo s'appuie sur jusqu'à 3 semaines postérieures à la semaine 8 : 83 décrochages silencieux avec T = 6, 7 ou 8 n'en sont exclus que grâce aux semaines 9 à 11, et 15 étudiants inactifs en semaine 8 y figurent parce que leur inactivité s'est arrêtée ; (b) l'effet du tutorat pendant les semaines 1 à 8 n'est pas mesuré (45 tutorés sont partis avant la photo). Ce qui est estimé : « l'effet d'avoir commencé le tutorat au plus tard en semaine 8, chez les étudiants encore présents à la fin de la semaine 8, sur le décrochage des semaines 9 à 30 ».
- Statut : validée (Saliou, 22/11)

## D-62 — Spécification alternative : Cox dépendant du temps, activité figée au début du tutorat (relecture RV02-02)
- Date / tâche : 22/11/2026 — CA-05 (remplace le point 3 de D-58)
- Constat : D-58 (point 3) ajustait sur la moyenne d'activité des semaines 1 à t − 1, y compris après le début du tutorat, c'est-à-dire sur le médiateur exclu par D-55.
- Options : (a) figer l'activité d'un tutoré à sa semaine de début ; (b) garder D-58 et présenter un « effet hors médiation par l'activité » ; (c) profil seul.
- Décision : (a). Covariable d'activité = moyenne des semaines 1 à min(t − 1, semaine de début) pour un tutoré (le tutorat compte à partir de la semaine qui suit le début, D-39), des semaines 1 à t − 1 pour les autres ; en semaine 1 (aucune semaine antérieure) : médiane de la covariable sur toutes les semaines-étudiant où elle est définie. Profil comme D-55 ; strates : cohorte ; IC du modèle. Ce modèle répond à une question voisine (tous les étudiants dès la semaine 1, HR « à profil et activité passée égaux ») : on le compare à l'analyse principale sur le sens et l'ordre de grandeur, pas sur le chiffre exact.
- Statut : validée (Saliou, 22/11)

## D-63 — Modèles prédictifs, validation temporelle et explication (SV-03, SV-04 ; Q2)
- Date / tâche : 22/11/2026 — SV-03, SV-04
- Décision :
  1. **Modèle « rentrée »** (comparaison officielle du cahier, F4) : Cox (lifelines, liens d'Efron) et gradient boosting à temps discret (D-60), entraînés sur la cohorte 2024 avec les variables de la rentrée codées comme le Cox (D-49, D-50 ; la cohorte est retirée, puisqu'il n'y en a qu'une par jeu), plus le numéro de la semaine pour le gradient boosting ; testés sur 2025 avec les médianes et la liste de colonnes de 2024.
  2. **Modèle « hebdomadaire »** : le même gradient boosting, avec en plus l'activité de la semaine précédente (D-42 : `nb_connexions_lms_prec`, `devoirs_rendus_prec`, `note_moyenne_prec`, `absences_prec`, valeurs manquantes laissées au modèle ; `etat_activite_prec` en indicatrices). C'est le score actualisable chaque semaine.
  3. **Réglages fixés d'avance**, sans aucun essai sur 2025 : `learning_rate` 0,05 ; `max_iter` 300 ; `max_leaf_nodes` 15 ; `min_samples_leaf` 100 ; `l2_regularization` 1,0 ; `early_stopping` désactivé ; `random_state` = `SEED`.
  4. **Mesures sur 2025**, mêmes étudiants pour tous les modèles : C-index de Harrell sur le risque à 30 semaines ; Brier score intégré (pondération par l'inverse de la probabilité de censure ; censure estimée par Kaplan-Meier sur 2024, décrochages comptés avant les censures à égalité de semaine, comme scikit-survival ; semaines 1 à 29, méthode des trapèzes) ; calibration à 20 semaines (10 groupes de risque prédit ; observé par Kaplan-Meier dans chaque groupe ; écart absolu moyen) ; référence « sans variable » (Kaplan-Meier 2024 pour tous). Modèle hebdomadaire : AUC sur les semaines-étudiants 2025 (risque de la semaine contre décrochage cette semaine-là), comparée à celle des modèles « rentrée », et décrochages attendus contre observés.
  5. **Explication** : importance par permutation (10 répétitions, `SEED`) : baisse du C-index pour le modèle « rentrée » (une variable = toutes ses indicatrices), baisse de l'AUC hebdomadaire pour le modèle hebdomadaire ; HR du Cox 2024 en regard.
  6. Aucune variable de tutorat (D-43). Résultats rapportés tels quels, même si le gradient boosting ne fait pas mieux que le Cox. Prédictions 2025 enregistrées pour le tableau de bord et les fiches LLM (le modèle qu'ils utiliseront sera choisi en LL-01 / DB-01).
- Statut : validée (Saliou, 22/11)

## D-64 — Cox prédictif de 2024 : proportionnalité de l'emploi non corrigée (SV-03, SV-04)
- Date / tâche : 22/11/2026 — SV-04
- Constat : dans le Cox entraîné sur la seule cohorte 2024 (modèle prédictif de SV-03), le test de Schoenfeld (« rank ») donne p = 0,030 pour l'emploi en parallèle ; les 12 autres colonnes ont toutes p > 0,3.
- Options : (a) ne pas corriger et l'écrire ; (b) stratifier par l'emploi ou ajouter une interaction avec la période (règle de D-51), c'est-à-dire modifier le modèle après avoir vu ses résultats sur 2025.
- Décision : (a). 13 colonnes sont testées à la fois : le seuil corrigé de Bonferroni vaut 0,05 / 13 ≈ 0,0038, que 0,030 ne franchit pas ; sur les 5 000 étudiants (SV-02), aucune violation après stratification par cohorte (p minimum 0,36) ; ce Cox sert à prédire, et sa calibration est mesurée directement sur 2025 (écart de 2,8 points). Ces raisons seront ajoutées aux limites du notebook 04 lors d'une prochaine consigne.
- Statut : validée (Saliou, 22/11)

## D-65 — Fiches d'alerte : LLM par API, protection des données et garde-fous (LL-01, étape 1)
- Date / tâche : 23/11/2026 — LL-01
- Contexte : au point d'étape M2 (23/11), l'enseignant demande un LLM appelé par API, comme pour le projet précédent (Gemini).
- Décision :
  1. **API Gemini**, SDK officiel `google-genai` (3.6.1) et `python-dotenv` (1.2.4). La clé `GEMINI_API_KEY` est lue dans `.env` (ignoré par git ; `.env.example` sans valeur) et passée explicitement au client : sinon, une variable `GOOGLE_API_KEY` présente sur la machine passerait en priorité. Jamais de clé dans le code, un notebook, une consigne, un journal, un message d'erreur ou une sortie.
  2. **Modèle** : constante `MODELE_LLM` de `config.py`, par défaut `gemini-3.5-flash-lite`, secours `gemini-3.1-flash-lite` (deux modèles stables). Un appel de test neutre, sans aucune donnée d'étudiant, précède la génération.
  3. **Liste fermée de champs envoyés** : semaine, horizon, risque arrondi, risque moyen de la promotion, au plus 3 facteurs (libellé, valeur arrondie, référence de la promotion, multiplicateur), activité récente arrondie et celle de la promotion, statut de tutorat. Jamais : identifiant, nom, contact, texte de message, genre, région. Chaque entrée est contrôlée avant l'envoi (clés autorisées, vocabulaire fermé, motifs d'identifiant, d'e-mail et de téléphone, longueur des textes) ; si le contrôle échoue, rien n'est envoyé. Aucun texte libre d'étudiant n'est transmis : pas de risque d'injection de prompt par les données.
  4. **Le LLM n'invente aucun chiffre** : chaque nombre de la fiche doit figurer dans l'entrée ; mots interdits (causalité, certitude, jugement de la personne, attributs sensibles, nombres en lettres) ; actions prises dans une liste fermée. Une fiche non conforme est redemandée (3 essais au plus), sinon enregistrée avec le statut « à revoir » et ses motifs.
  5. **Reproductibilité** : `run_all.py` n'appelle jamais l'API ; la génération est une commande séparée ; les fiches sont enregistrées (cache) avec le modèle, la version du prompt et la date, puis relues par le notebook 06 et le tableau de bord. Gabarit versionné dans `src/prompts/` (v1, puis v2 si l'évaluation LL-02 le demande). Les tests utilisent une fausse fonction d'appel, sans réseau.
  6. **Relecture de sécurité R03** avant le premier appel réel.
  7. **Cadre** : loi sénégalaise n° 2008-12 du 25 janvier 2008 sur la protection des données à caractère personnel ; RGPD pour comparaison. Au niveau gratuit de l'API, Google peut utiliser les requêtes pour améliorer ses produits : raison de plus pour n'envoyer aucune donnée personnelle. Chaque fiche porte un avertissement fixe et reste à vérifier par le conseiller.
- Statut : validée (Saliou, 23/11). Le point 2 a été révisé puis validé par Saliou le même jour : le pilotage avait d'abord proposé `gemini-3.8-flash`, mais son niveau gratuit est limité à 20 requêtes par jour, contre 500 pour les Flash-Lite (quotas à vérifier sur la page « Rate limit » d'AI Studio) ; les 54 fiches, avec jusqu'à 3 essais chacune, demandent jusqu'à 162 appels.

## D-66 — Fiches d'alerte : population, score, facteurs et contenu (LL-01, étape 2 ; LL-02)
- Date / tâche : 23/11/2026 — LL-01, LL-02
- Décision :
  1. **Quand et qui** : semaine 8 (celle de la photo causale), cohorte 2025 (jamais utilisée pour entraîner les modèles), étudiants encore suivis après la semaine 8 (T > 8) : 2 177 étudiants.
  2. **Score** : Cox 2024 (D-63). Risque de décrocher d'ici la semaine 30 pour un étudiant encore inscrit en semaine 8 : 1 − S(30) / S(8), tiré de `ml_predictions_2025.csv`. Une fiche si ce risque atteint 40 % : 54 étudiants (risque moyen de la promotion : 17,8 %). Pourquoi le Cox : ses facteurs s'expliquent par ses coefficients, et sa calibration est mesurée (D-64). Le score hebdomadaire du gradient boosting n'apparaît que dans le tableau de bord (DB-01), en colonne.
  3. **Facteurs** : contribution d'une variable = β × (x − moyenne de la promotion), en additionnant les indicatrices d'une variable qualitative ; affichée en multiplicateur exp(contribution) « par rapport à un étudiant moyen de la promotion, à autres caractéristiques égales ». Les 3 plus fortes contributions positives ; une valeur manquante n'est jamais un facteur.
  4. **Contenu** : JSON avec `situation` (2 phrases), `points_attention` (2 à 4) et `actions` (2 ou 3 parmi 7 : entretien individuel ; proposer un tutorat ; faire le point sur le tutorat en cours ; informer sur les aides ; aménager l'emploi du temps ; suivre l'assiduité ; relancer sur les devoirs). Le code ajoute localement l'identifiant et l'avertissement fixe : « Fiche générée automatiquement à partir d'un modèle statistique : à vérifier par le conseiller. Les facteurs sont des associations, pas des causes. »
  5. **Évaluation (LL-02)** : 20 fiches tirées au hasard (`SEED`) ; grille : exactitude (contrôle automatique et relecture humaine), ton (1 à 3), stigmatisation (oui / non), pertinence des actions (1 à 3) ; notées par Saliou.
  6. **Détails de mise en œuvre proposés par le pilotage** :
     - facteurs affichables : âge, note du bac, distance, bourse, emploi en parallèle, filière. Le genre et la région restent dans le score mais ne sont jamais affichés : ils ne sont pas significatifs dans le Cox 2024 (p = 0,18 et 0,82) et ce sont des attributs sensibles qu'une fiche ne doit pas pointer ;
     - un facteur n'est affiché que si son multiplicateur arrondi vaut au moins 1,1 ;
     - activité des semaines 7 et 8 (moyenne par semaine : connexions, devoirs rendus, séances manquées, note) et statut de tutorat à la semaine 8, comparés à la promotion : des observations, pas des facteurs du score ;
     - références : moyenne de la promotion pour l'âge et la note du bac ; pour la distance, la distance « typique » 2^(moyenne de log2 de la distance), qui correspond au centrage du Cox ; pour une modalité, la part de la promotion dans le même cas ;
     - contrôle automatique de cohérence : un tutorat en cours exclut l'action « proposer un tutorat » ; l'absence de tutorat exclut « faire le point sur le tutorat en cours ».
- Statut : validée (Saliou, 23/11) ; le point 6, proposé par le pilotage, a été validé le même jour, après l'exécution de C13.
