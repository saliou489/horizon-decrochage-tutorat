"""Nettoyage et pseudonymisation de la table « messages ».

Rôle du module : appliquer, dans l'ordre imposé par la consigne C05, les règles
validées par Saliou (décisions D-28, D-29) à data/raw/messages.csv : contrôles de
structure, réparation de l'encodage, retrait des messages vides, remplacement des
données personnelles par des balises [EMAIL], [TEL], [NOM].
Protection des données (loi sénégalaise n° 2008-12, RGPD pour comparaison) : aucune
table de correspondance n'est conservée, et aucun texte original n'est écrit dans un
fichier, le journal ou un message d'erreur (les erreurs citent seulement id_message).

Tâche couverte : DA-05.
"""

import re

import pandas as pd

from src import config
from src.nettoyage.commun import ErreurNettoyage, convertir_nombres, entree_journal

TABLE = "messages"


# ---------------------------------------------------------------------------
# Règle 1 : contrôles de structure
# ---------------------------------------------------------------------------

def regle_controles(df, etudiants):
    """Contrôle id_message, id_etudiant, semaine et canal ; aucune correction.

    Écart -> arrêt (l'audit n'en a trouvé aucun). semaine est convertie en entier.
    """
    erreurs = []
    if df["id_message"].duplicated().any():
        erreurs.append("id_message en double")
    ids = df[config.COLONNE_ID]
    if not ids.str.fullmatch(config.FORMAT_ID_ETUDIANT).all():
        erreurs.append("id_etudiant mal formé")
    if not ids.isin(set(etudiants[config.COLONNE_ID])).all():
        erreurs.append("id_etudiant absent de etudiants")
    semaine = convertir_nombres(df["semaine"], "semaine", entier=True)
    if not semaine.between(1, config.N_SEMAINES).fillna(False).all():
        erreurs.append("semaine hors [1 ; 30]")
    if not df["canal"].isin(config.CANAUX_MESSAGES).all():
        erreurs.append("canal hors {forum, formulaire de suivi}")
    if erreurs:
        raise ErreurNettoyage("Table messages, contrôle de structure en échec : " + " ; ".join(erreurs))
    resultat = df.copy()
    resultat["semaine"] = semaine
    entrees = [entree_journal(TABLE, "Contrôle de structure : id_message unique, id_etudiant connu, semaine "
                              "dans [1 ; 30], canal autorisé", 0, "Aucun écart : rien à corriger", "D-18")]
    return resultat, 0, entrees


# ---------------------------------------------------------------------------
# Règle 2 : encodage
# ---------------------------------------------------------------------------

def reparer_texte(texte):
    """Refait la conversion cp1252 -> UTF-8 d'un texte cassé (« trouvÃ© » -> « trouvé »).

    Lève UnicodeError si la réparation est impossible.
    """
    return texte.encode(config.ENCODAGE_DE_LA_CASSE).decode(config.ENCODAGE)


def regle_encodage(df):
    """Répare les textes à accents cassés (D-28, audit MSG-01).

    Échec de réparation ou caractère cassé restant -> arrêt (seul id_message est cité).
    """
    resultat = df.copy()
    casses = df["texte"].str.contains(config.MOTIF_ENCODAGE_CASSE, regex=True)
    for index in df.index[casses]:
        try:
            resultat.at[index, "texte"] = reparer_texte(df.at[index, "texte"])
        except UnicodeError:
            raise ErreurNettoyage(f"Encodage irréparable : message {df.at[index, 'id_message']}") from None
    restants = resultat["texte"].str.contains(config.MOTIF_ENCODAGE_CASSE, regex=True)
    if restants.any():
        raise ErreurNettoyage(f"Caractères cassés restants : messages {list(resultat.loc[restants, 'id_message'])}")
    nb = int(casses.sum())
    entrees = [entree_journal(TABLE, "Accents cassés (« Ã© » pour « é », MSG-01)", nb,
                              "Texte réparé (conversion cp1252 -> UTF-8 refaite)", "D-28")]
    return resultat, nb, entrees


# ---------------------------------------------------------------------------
# Règle 3 : messages vides
# ---------------------------------------------------------------------------

def regle_messages_vides(df):
    """Retire les messages sans aucun caractère alphanumérique (D-29, MSG-02, MSG-03).

    Sortie : (table, nb lignes retirées, journal, rejets). Les rejets ne contiennent
    aucune donnée personnelle (textes vides, « . », espaces).
    """
    vides = ~df["texte"].str.contains(config.MOTIF_ALPHANUMERIQUE, regex=True)
    rejets = df[vides].reset_index(drop=True)
    resultat = df[~vides].reset_index(drop=True)
    nb = int(vides.sum())
    entrees = [entree_journal(TABLE, "Message vide ou sans aucun mot (« », « . », espaces ; MSG-02, MSG-03)", nb,
                              "Message retiré, conservé dans rejets/messages_vides.csv", "D-29")]
    return resultat, nb, entrees, rejets


# ---------------------------------------------------------------------------
# Règle 4 : pseudonymisation
# ---------------------------------------------------------------------------

def pseudonymiser(texte):
    """Remplace e-mails, téléphones puis noms par leurs balises (D-28).

    L'ordre compte : l'e-mail d'abord (il contient le nom de la personne), puis le
    téléphone, puis le nom introduit par « c'est » / « je suis ».
    Sortie : (texte pseudonymisé, {balise: nombre de remplacements}).
    """
    texte, nb_email = re.subn(config.MOTIF_PSEUDO_EMAIL, config.BALISE_EMAIL, texte)
    texte, nb_tel = re.subn(config.MOTIF_PSEUDO_TELEPHONE, config.BALISE_TELEPHONE, texte)
    texte, nb_nom = re.subn(config.MOTIF_PSEUDO_NOM, lambda m: f"{m.group('intro')} {config.BALISE_NOM}", texte)
    return texte, {config.BALISE_EMAIL: nb_email, config.BALISE_TELEPHONE: nb_tel, config.BALISE_NOM: nb_nom}


def residus(texte):
    """Liste des données personnelles qui resteraient après remplacement (contrôle obligatoire)."""
    trouves = []
    if "@" in texte:
        trouves.append("@")
    if re.search(config.MOTIF_RESIDU_CHIFFRES, texte):
        trouves.append("suite de 8 chiffres ou plus")
    if re.search(config.MOTIF_PSEUDO_NOM, texte):
        trouves.append("nom après « c'est » / « je suis »")
    return trouves


def regle_pseudonymisation(df):
    """Pseudonymise la colonne texte, puis contrôle qu'il ne reste rien (D-28, MSG-04 à MSG-06).

    Vient APRÈS la réparation de l'encodage : un nom accentué cassé ne serait pas reconnu.
    Un résidu arrête le nettoyage ; seul id_message est cité.
    """
    resultat = df.copy()
    totaux = {config.BALISE_EMAIL: 0, config.BALISE_TELEPHONE: 0, config.BALISE_NOM: 0}
    modifies = 0
    textes = []
    for texte in df["texte"]:
        nouveau, comptes = pseudonymiser(texte)
        textes.append(nouveau)
        modifies += int(nouveau != texte)
        for balise, nb in comptes.items():
            totaux[balise] += nb
    resultat["texte"] = textes
    avec_residu = [(i, r) for i, r in zip(resultat["id_message"], map(residus, textes)) if r]
    if avec_residu:
        raise ErreurNettoyage(f"Données personnelles restantes après pseudonymisation : {avec_residu[:10]}")
    entrees = [
        entree_journal(TABLE, "Adresse e-mail dans le texte (MSG-06)", totaux[config.BALISE_EMAIL],
                       "Remplacée par [EMAIL]", "D-28"),
        entree_journal(TABLE, "Numéro de téléphone sénégalais dans le texte (MSG-05)", totaux[config.BALISE_TELEPHONE],
                       "Remplacé par [TEL]", "D-28"),
        entree_journal(TABLE, "Prénom et nom introduits par « c'est » ou « je suis » (MSG-04)",
                       totaux[config.BALISE_NOM], "Nom remplacé par [NOM] (ex. « Bonjour, c'est [NOM]. »)", "D-28"),
        entree_journal(TABLE, "Messages contenant au moins une donnée personnelle (synthèse)", modifies,
                       "Pseudonymisés ; aucune table de correspondance conservée ; contrôle résiduel : 0 reste",
                       "D-28"),
    ]
    return resultat, modifies, entrees


# ---------------------------------------------------------------------------
# Enchaînement
# ---------------------------------------------------------------------------

def nettoyer(df_brut, etudiants):
    """Applique les 4 règles dans l'ordre.

    Sortie : (table nettoyée, rejets, lignes de journal, {règle: lignes touchées},
    {balise: nombre de remplacements}).
    """
    entrees, touchees = [], {}
    df, nb, journal = regle_controles(df_brut, etudiants)
    touchees["regle_controles"], entrees = nb, entrees + journal
    df, nb, journal = regle_encodage(df)
    touchees["regle_encodage"], entrees = nb, entrees + journal
    df, nb, journal, rejets = regle_messages_vides(df)
    touchees["regle_messages_vides"], entrees = nb, entrees + journal
    df, nb, journal = regle_pseudonymisation(df)
    touchees["regle_pseudonymisation"], entrees = nb, entrees + journal
    return df, rejets, entrees, touchees


def effectifs(df):
    """Nombre de balises [EMAIL], [TEL], [NOM] présentes dans la table nettoyée."""
    balises = [config.BALISE_EMAIL, config.BALISE_TELEPHONE, config.BALISE_NOM]
    comptes = {b: int(df["texte"].str.count(re.escape(b)).sum()) for b in balises}
    return [("balises dans texte", comptes)]
