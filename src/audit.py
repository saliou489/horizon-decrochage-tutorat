"""Audit qualité des 5 fichiers bruts du jeu Horizon.

Rôle du module : lire data/raw/ sans rien modifier, recenser les anomalies
(structure, identifiants, modalités, nombres, dates, cohérences internes et entre
tables, données personnelles) et écrire le rapport docs/audit_qualite.md.
L'audit CONSTATE seulement : aucune correction n'est faite ici. Les traitements
seront décidés par Saliou (tâches DA-02 à DA-05).

Tâche couverte : DA-01.
Lancement depuis la racine du dépôt : python -m src.audit
"""

import csv
import io
import re
from datetime import datetime

import pandas as pd

from src import config


# ===========================================================================
# 1. Lecture des fichiers
# ===========================================================================

def lire_texte_brut(table):
    """Lit un fichier brut en octets puis le décode.

    Entrée : nom de la table (clé de config.FICHIERS_BRUTS).
    Sortie : (octets, texte décodé, description de l'encodage).
    On tente d'abord un décodage UTF-8 strict : s'il réussit, le fichier est du
    UTF-8 valide. Sinon on le signale et on relit en remplaçant les octets invalides.
    """
    chemin = config.DOSSIER_RAW / config.FICHIERS_BRUTS[table]["fichier"]
    octets = chemin.read_bytes()
    try:
        texte = octets.decode(config.ENCODAGE)
        encodage = "UTF-8 (décodage strict réussi)"
    except UnicodeDecodeError:
        texte = octets.decode(config.ENCODAGE, errors="replace")
        encodage = "non UTF-8 : octets invalides remplacés à la lecture"
    return octets, texte, encodage


def lire_table(table):
    """Lit une table brute avec pandas, toutes les colonnes en texte.

    Entrée : nom de la table.
    Sortie : DataFrame dont les colonnes portent les noms ATTENDUS (dictionnaire
    du LISEZMOI) et dont les valeurs sont les chaînes brutes, sans conversion :
    une case vide reste une chaîne vide, pour que l'audit voie exactement le fichier.
    Les colonnes sont renommées par position (l'ordre des fichiers suit celui du
    LISEZMOI) ; les noms bruts sont rapportés à part dans la section « Structure ».
    """
    description = config.FICHIERS_BRUTS[table]
    chemin = config.DOSSIER_RAW / description["fichier"]
    df = pd.read_csv(
        chemin,
        sep=description["separateur"],
        dtype=str,
        keep_default_na=False,
        encoding=config.ENCODAGE,
    )
    if len(df.columns) == len(description["colonnes"]):
        df.columns = description["colonnes"]
    return df


def numero_ligne_fichier(index):
    """Numéro de la ligne dans le fichier CSV (ligne 1 = en-tête).

    Valable car aucun fichier ne contient de retour à la ligne à l'intérieur d'un champ
    (vérifié par le décompte des lignes physiques dans la section Structure).
    """
    return index + 2


# ===========================================================================
# 2. Outils de présentation
# ===========================================================================

def montrer(valeur):
    """Met une valeur entre guillemets français pour rendre visibles les espaces."""
    texte = str(valeur).replace("|", "\\|").replace("\n", " ")
    return f"«{texte}»"


def exemples_lignes(df, masque, colonne, nb=config.NB_EXEMPLES):
    """Construit des exemples « l. <n> <id> : «valeur» » pour les lignes repérées.

    Entrées : la table, un masque booléen des lignes concernées, la colonne à montrer.
    Sortie : liste d'au plus nb chaînes. On prend des valeurs distinctes quand c'est
    possible, pour montrer la variété des cas plutôt que trois fois le même.
    """
    lignes = df[masque]
    if len(lignes) == 0:
        return []
    lignes = lignes.drop_duplicates(subset=[colonne]) if colonne in df.columns else lignes
    exemples = []
    for index, ligne in lignes.head(nb).iterrows():
        identifiant = ligne.get(config.COLONNE_ID, "")
        exemples.append(f"l. {numero_ligne_fichier(index)} {identifiant} : {montrer(ligne[colonne])}")
    return exemples


def nouvelle_anomalie(colonne, anomalie, nb_lignes, exemples, code=None):
    """Crée l'enregistrement d'une anomalie (une ligne du tableau du rapport)."""
    return {
        "colonne": colonne,
        "anomalie": anomalie,
        "lignes": int(nb_lignes),
        "exemples": exemples,
        "code": code,
    }


def est_vide(serie):
    """Vrai pour les cases vides ou ne contenant que des espaces."""
    return serie.str.strip() == ""


def normaliser_id(serie):
    """Identifiant en majuscules, sans espaces autour.

    Normalisation PROVISOIRE, utilisée seulement pour rapprocher les tables dans
    l'audit ; la vraie règle sera décidée en DA-02.
    """
    return serie.str.strip().str.upper()


# ===========================================================================
# 3. Structure du fichier
# ===========================================================================

def detecter_separateur(premiere_ligne):
    """Retourne le séparateur candidat le plus fréquent dans la ligne d'en-tête."""
    comptes = {sep: premiere_ligne.count(sep) for sep in config.SEPARATEURS_CANDIDATS}
    return max(comptes, key=comptes.get)


def decrire_fins_de_ligne(octets):
    """Indique le type de fins de ligne : LF (Unix), CRLF (Windows) ou mélange."""
    nb_crlf = octets.count(b"\r\n")
    nb_lf_seuls = octets.count(b"\n") - nb_crlf
    if nb_crlf == 0:
        return "LF"
    if nb_lf_seuls == 0:
        return "CRLF"
    return f"mélange ({nb_crlf} CRLF, {nb_lf_seuls} LF)"


def compter_champs_par_ligne(texte, separateur):
    """Lit le fichier avec le module csv (qui respecte les guillemets).

    Sortie : liste du nombre de champs de chaque enregistrement, en-tête compris.
    Une ligne vide donne 0 champ.
    """
    lecteur = csv.reader(io.StringIO(texte), delimiter=separateur)
    return [len(champs) for champs in lecteur]


def analyser_structure(table, df):
    """Rassemble les informations de structure d'un fichier brut.

    Sortie : (dictionnaire de description, liste d'anomalies de structure).
    """
    description = config.FICHIERS_BRUTS[table]
    octets, texte, encodage = lire_texte_brut(table)
    premiere_ligne = texte.split("\n", 1)[0]
    separateur = detecter_separateur(premiere_ligne)
    colonnes_brutes = next(csv.reader([premiere_ligne], delimiter=description["separateur"]))
    champs = compter_champs_par_ligne(texte, description["separateur"])
    nb_attendu = len(description["colonnes"])
    types_pandas = pd.read_csv(
        config.DOSSIER_RAW / description["fichier"],
        sep=description["separateur"],
        encoding=config.ENCODAGE,
    ).dtypes

    infos = {
        "fichier": description["fichier"],
        "separateur_attendu": description["separateur"],
        "separateur_detecte": separateur,
        "encodage": encodage,
        "bom": octets.startswith(b"\xef\xbb\xbf"),
        "fins_de_ligne": decrire_fins_de_ligne(octets),
        "lignes_physiques": texte.count("\n"),
        "lignes_donnees": len(df),
        "lignes_annoncees": description["lignes_annoncees"],
        "colonnes_brutes": colonnes_brutes,
        "colonnes_attendues": description["colonnes"],
        "types": [str(t) for t in types_pandas],
    }

    anomalies = []
    if separateur != description["separateur"]:
        anomalies.append(nouvelle_anomalie(
            "(fichier)", f"séparateur détecté {montrer(separateur)} au lieu de "
            f"{montrer(description['separateur'])}", 1, []))
    if infos["bom"]:
        anomalies.append(nouvelle_anomalie("(fichier)", "marque BOM en tête de fichier", 1, []))

    a_espaces = [c for c in colonnes_brutes if c != c.strip()]
    anomalies.append(nouvelle_anomalie(
        "(en-tête)", "nom de colonne entouré d'espaces", len(a_espaces),
        [montrer(c) for c in a_espaces[:config.NB_EXEMPLES]]))
    renommees = [
        f"{montrer(brut)} au lieu de {montrer(attendu)}"
        for brut, attendu in zip(colonnes_brutes, description["colonnes"])
        if brut.strip() != attendu
    ]
    anomalies.append(nouvelle_anomalie(
        "(en-tête)", "colonne nommée autrement que dans le LISEZMOI", len(renommees),
        renommees[:config.NB_EXEMPLES]))

    enregistrements = champs[1:]
    vides = [i + 2 for i, n in enumerate(enregistrements) if n == 0]
    decalees = [i + 2 for i, n in enumerate(enregistrements) if n not in (0, nb_attendu)]
    anomalies.append(nouvelle_anomalie(
        "(lignes)", "ligne vide au milieu du fichier", len(vides),
        [f"l. {n}" for n in vides[:config.NB_EXEMPLES]]))
    anomalies.append(nouvelle_anomalie(
        "(lignes)", f"ligne décalée (nombre de champs différent de {nb_attendu})",
        len(decalees), [f"l. {n}" for n in decalees[:config.NB_EXEMPLES]]))
    return infos, anomalies


# ===========================================================================
# 4. Contrôles génériques d'une table
# ===========================================================================

def controler_mojibake(df):
    """Repère les caractères accentués cassés (UTF-8 relu comme Latin-1, ex. « Ã© »)."""
    anomalies = []
    for colonne in df.columns:
        masque = df[colonne].str.contains(config.MOTIF_MOJIBAKE, regex=True)
        if masque.any():
            anomalies.append(nouvelle_anomalie(
                colonne, "encodage cassé (mojibake, ex. « Ã© » pour « é »)", masque.sum(),
                exemples_lignes(df, masque, colonne)))
    return anomalies


def controler_identifiants(df, colonne=config.COLONNE_ID):
    """Contrôle le format « HZ + 5 chiffres » et détaille les écarts rencontrés."""
    valeurs = df[colonne]
    conforme = valeurs.str.fullmatch(config.FORMAT_ID_ETUDIANT)
    espaces = (valeurs != valeurs.str.strip()) & valeurs.str.strip().str.fullmatch(
        config.FORMAT_ID_ETUDIANT, case=False)
    minuscules = (~conforme) & (~espaces) & normaliser_id(valeurs).str.fullmatch(
        config.FORMAT_ID_ETUDIANT)
    vides = est_vide(valeurs)
    autres = (~conforme) & (~espaces) & (~minuscules) & (~vides)
    return [
        nouvelle_anomalie(colonne, "identifiant entouré d'espaces", espaces.sum(),
                          exemples_lignes(df, espaces, colonne)),
        nouvelle_anomalie(colonne, "identifiant en minuscules (« hz » au lieu de « HZ »)",
                          minuscules.sum(), exemples_lignes(df, minuscules, colonne)),
        nouvelle_anomalie(colonne, "identifiant vide", vides.sum(), exemples_lignes(df, vides, colonne)),
        nouvelle_anomalie(colonne, "identifiant d'un autre format (préfixe, nombre de chiffres…)",
                          autres.sum(), exemples_lignes(df, autres, colonne)),
    ]


def controler_doublons_exacts(df):
    """Lignes strictement identiques à une ligne précédente (copie exacte)."""
    masque = df.duplicated(keep="first")
    return nouvelle_anomalie(
        "(ligne entière)", "doublon exact (ligne identique à une ligne précédente) — "
        "nombre de lignes en trop", masque.sum(),
        exemples_lignes(df, masque, df.columns[0]))


def controler_doublons_cle(df, cle, libelle_cle):
    """Doublons sur une clé (après normalisation provisoire de l'identifiant).

    Sépare deux cas :
    - « même contenu » : les lignes ne diffèrent que par l'écriture de l'identifiant
      ou sont des copies exactes ;
    - « contenu différent » (quasi-doublon) : même clé, mais au moins une autre
      valeur diffère, il faudra choisir quelle ligne croire.
    """
    travail = df.copy()
    travail["_id_norm"] = normaliser_id(travail[config.COLONNE_ID])
    cle_norm = ["_id_norm"] + [c for c in cle if c != config.COLONNE_ID]
    autres_colonnes = [c for c in df.columns if c not in cle]
    en_double = travail.duplicated(subset=cle_norm, keep=False)
    groupes = travail[en_double].groupby(cle_norm)
    nb_versions = groupes[autres_colonnes].nunique().max(axis=1) if autres_colonnes else None
    cles_differentes = set(nb_versions[nb_versions > 1].index) if nb_versions is not None else set()

    index_cle = travail.set_index(cle_norm).index
    masque_diff = en_double & index_cle.isin(cles_differentes)
    masque_meme = en_double & ~index_cle.isin(cles_differentes)
    # Lignes « en trop » parmi les groupes au même contenu : toutes sauf la première.
    en_trop_meme = masque_meme & travail.duplicated(subset=cle_norm, keep="first")
    return [
        nouvelle_anomalie(
            libelle_cle, f"même {libelle_cle} répété avec le même contenu (après mise en "
            "majuscules de l'identifiant ; doublons exacts compris) — nombre de lignes en trop",
            en_trop_meme.sum(),
            exemples_lignes(df, masque_meme, config.COLONNE_ID)),
        nouvelle_anomalie(
            libelle_cle, f"même {libelle_cle} répété avec des valeurs différentes "
            f"(quasi-doublon) — {len(cles_differentes)} clés concernées, nombre de lignes",
            masque_diff.sum(), exemples_quasi_doublons(df, masque_diff, travail, cle_norm)),
    ]


def exemples_quasi_doublons(df, masque, travail, cle_norm):
    """Exemples de quasi-doublons : pour une clé, les colonnes qui diffèrent."""
    exemples = []
    for valeurs_cle, groupe in df[masque].groupby([travail.loc[masque, c] for c in cle_norm]):
        differences = []
        for colonne in df.columns:
            versions = groupe[colonne].unique()
            if colonne != config.COLONNE_ID and len(versions) > 1:
                differences.append(f"{colonne} = " + " / ".join(montrer(v) for v in versions))
        cle_texte = " ".join(str(v) for v in (valeurs_cle if isinstance(valeurs_cle, tuple) else [valeurs_cle]))
        exemples.append(f"{cle_texte} : " + " ; ".join(differences))
        if len(exemples) == config.NB_EXEMPLES:
            break
    return exemples


def controler_vides(table, df):
    """Valeurs manquantes dans les colonnes qui ne devraient jamais être vides."""
    anomalies = []
    for colonne in df.columns:
        if (table, colonne) in config.VIDES_AUTORISES or colonne == config.COLONNE_ID:
            continue
        masque = est_vide(df[colonne])
        anomalies.append(nouvelle_anomalie(
            colonne, "valeur manquante (case vide ou espaces)", masque.sum(),
            exemples_lignes(df, masque, colonne)))
    return anomalies


def controler_modalites(table, df):
    """Valeurs des colonnes catégorielles absentes de la liste attendue du LISEZMOI."""
    anomalies = []
    for (nom_table, colonne), attendues in config.MODALITES.items():
        if nom_table != table:
            continue
        valeurs = df[colonne]
        masque = ~valeurs.isin(attendues) & ~est_vide(valeurs)
        distinctes = valeurs[masque].value_counts()
        exemples = [f"{montrer(v)} ({n})" for v, n in distinctes.head(config.NB_EXEMPLES).items()]
        anomalies.append(nouvelle_anomalie(
            colonne, f"modalité non conforme au LISEZMOI ({len(distinctes)} écritures différentes)",
            masque.sum(), exemples))
    return anomalies


# ===========================================================================
# 5. Contrôles numériques
# ===========================================================================

def classer_format_numerique(valeur):
    """Classe l'écriture d'une valeur numérique brute.

    Sortie : un des libellés « vide », « entier », « décimal (point) »,
    « décimal (virgule) », « avec unité », « non numérique ».
    """
    texte = valeur.strip()
    unites = "|".join(config.UNITES_TEXTE)
    if texte == "":
        return "vide"
    if re.fullmatch(r"-?\d+", texte):
        return "entier"
    if re.fullmatch(r"-?\d+\.\d+", texte):
        return "décimal (point)"
    if re.fullmatch(r"-?\d+,\d+", texte):
        return "décimal (virgule)"
    if re.fullmatch(rf"-?\d+(?:[.,]\d+)?\s*(?:{unites})", texte):
        return "avec unité"
    return "non numérique"


def lire_nombre(valeur):
    """Convertit une écriture brute en nombre, pour CONSTATER les bornes.

    La virgule est lue comme un point et l'unité est ignorée : c'est seulement pour
    savoir si la valeur est dans les bornes, pas une correction.
    Sortie : float, ou None si la valeur est vide ou illisible.
    """
    unites = "|".join(config.UNITES_TEXTE)
    texte = re.sub(rf"\s*(?:{unites})$", "", valeur.strip()).replace(",", ".")
    try:
        return float(texte)
    except ValueError:
        return None


def controler_formats_numeriques(table, df, colonne):
    """Signale les écritures non standard d'une colonne numérique."""
    formats = df[colonne].map(classer_format_numerique)
    entiere = (table, colonne) in config.COLONNES_ENTIERES
    anomalies = []
    for libelle in ["décimal (virgule)", "avec unité", "non numérique"]:
        masque = formats == libelle
        anomalies.append(nouvelle_anomalie(
            colonne, f"nombre écrit au format « {libelle} »", masque.sum(),
            exemples_lignes(df, masque, colonne)))
    if entiere:
        masque = formats.isin(["décimal (point)", "décimal (virgule)"])
        anomalies.append(nouvelle_anomalie(
            colonne, "nombre entier écrit avec une partie décimale (ex. « 5.0 »)",
            masque.sum(), exemples_lignes(df, masque, colonne)))
    return anomalies


def hors_bornes(nombre, bornes):
    """Vrai si le nombre sort des bornes attendues (None = pas de borne)."""
    if bornes["min"] is not None:
        if nombre < bornes["min"] or (bornes["strict"] and nombre == bornes["min"]):
            return True
    if bornes["max"] is not None and nombre > bornes["max"]:
        return True
    return False


def controler_bornes(table, df, colonne):
    """Valeurs sentinelles, valeurs hors bornes et valeurs très éloignées.

    Une valeur sentinelle (-1, 99, 999, 9999) hors des bornes est comptée comme
    sentinelle et non comme « hors bornes », pour ne pas la compter deux fois.
    Quand il n'y a pas de borne haute, on signale à part les valeurs très éloignées
    du reste (au-delà de Q3 + 3 × IQR) : elles sont « à examiner », pas forcément fausses.
    """
    bornes = config.BORNES[(table, colonne)]
    nombres = df[colonne].map(lire_nombre)
    lisibles = nombres.notna()
    sentinelle = lisibles & nombres.isin(config.VALEURS_SENTINELLES) & nombres.map(
        lambda x: x is not None and (hors_bornes(x, bornes) or bornes["max"] is None))
    dehors = lisibles & ~sentinelle & nombres.map(lambda x: x is not None and hors_bornes(x, bornes))
    texte_bornes = decrire_bornes(bornes)
    anomalies = [
        nouvelle_anomalie(colonne, f"valeur sentinelle ({', '.join(str(v) for v in config.VALEURS_SENTINELLES)})",
                          sentinelle.sum(), exemples_lignes(df, sentinelle, colonne)),
        nouvelle_anomalie(colonne, f"valeur hors bornes (attendu : {texte_bornes})",
                          dehors.sum(), exemples_lignes(df, dehors, colonne)),
    ]
    if bornes["max"] is None:
        anomalies.append(controler_valeurs_eloignees(df, colonne, nombres, lisibles & ~sentinelle & ~dehors))
    return anomalies


def decrire_bornes(bornes):
    """Texte lisible des bornes, ex. « 17 à 35 » ou « > 0 »."""
    if bornes["max"] is None:
        signe = ">" if bornes["strict"] else "≥"
        return f"{signe} {bornes['min']}"
    return f"{bornes['min']} à {bornes['max']}"


def controler_valeurs_eloignees(df, colonne, nombres, retenues):
    """Valeurs au-delà de Q3 + COEF_IQR_EXTREMES × IQR (règle de Tukey)."""
    valeurs = nombres[retenues].astype(float)
    q1, q3 = valeurs.quantile(0.25), valeurs.quantile(0.75)
    limite = q3 + config.COEF_IQR_EXTREMES * (q3 - q1)
    masque = retenues & (nombres.astype(float) > limite)
    return nouvelle_anomalie(
        colonne, f"valeur très éloignée du reste (> {limite:g}, Q3 + {config.COEF_IQR_EXTREMES}×IQR) "
        "— à examiner", masque.sum(), exemples_lignes(df, masque, colonne))


def controles_numeriques(table, df):
    """Applique les contrôles de format et de bornes à toutes les colonnes concernées."""
    colonnes = [c for (t, c) in config.BORNES if t == table]
    colonnes += [c for (t, c) in config.COLONNES_ENTIERES if t == table and c not in colonnes]
    anomalies = []
    for colonne in colonnes:
        anomalies += controler_formats_numeriques(table, df, colonne)
        if (table, colonne) in config.BORNES:
            anomalies += controler_bornes(table, df, colonne)
    return anomalies


# ===========================================================================
# 6. Dates
# ===========================================================================

def lire_date(valeur):
    """Reconnaît le format d'une date brute et la convertit si possible.

    Sortie : (format reconnu, date ou None). Formats : ceux de config.FORMATS_DATE,
    « J mois AAAA » (mois abrégé en français), « vide », « illisible ».
    Une date au bon format mais qui n'existe pas (ex. 31/02) donne « date impossible ».
    """
    texte = valeur.strip()
    if texte == "":
        return "vide", None
    for nom, motif in config.FORMATS_DATE.items():
        if re.fullmatch(motif_regex_date(motif), texte):
            try:
                return nom, datetime.strptime(texte, motif)
            except ValueError:
                return "date impossible", None
    morceaux = re.fullmatch(r"(\d{1,2}) (\S+) (\d{4})", texte)
    if morceaux and morceaux.group(2) in config.MOIS_FR:
        jour, mois, annee = int(morceaux.group(1)), config.MOIS_FR[morceaux.group(2)], int(morceaux.group(3))
        try:
            return "J mois AAAA (français)", datetime(annee, mois, jour)
        except ValueError:
            return "date impossible", None
    return "illisible", None


def motif_regex_date(format_strptime):
    """Transforme un format strptime (%Y-%m-%d) en expression régulière de forme."""
    return (format_strptime.replace("%Y", r"\d{4}").replace("%m", r"\d{1,2}")
            .replace("%d", r"\d{1,2}"))


def ajouter_dates(df):
    """Ajoute aux inscriptions les colonnes de travail : format et date lue.

    Sortie : copie de la table avec _format_debut, _debut, _format_fin, _fin.
    """
    travail = df.copy()
    for colonne, suffixe in [("date_debut", "debut"), ("date_fin", "fin")]:
        lues = travail[colonne].map(lire_date)
        travail[f"_format_{suffixe}"] = lues.map(lambda x: x[0])
        # Conversion en type date de pandas : une date absente devient NaT.
        travail[f"_{suffixe}"] = pd.to_datetime(lues.map(lambda x: x[1]))
    return travail


def controler_formats_dates(df, travail):
    """Hétérogénéité des formats et dates illisibles ou impossibles."""
    anomalies = []
    format_reference = next(iter(config.FORMATS_DATE))
    for colonne, suffixe in [("date_debut", "debut"), ("date_fin", "fin")]:
        formats = travail[f"_format_{suffixe}"]
        repartition = formats[formats != "vide"].value_counts()
        masque_autre = ~formats.isin(["vide", format_reference])
        anomalies.append(nouvelle_anomalie(
            colonne, f"date dans un autre format que {format_reference} — répartition : "
            + ", ".join(f"{f} {n}" for f, n in repartition.items()),
            masque_autre.sum(), exemples_lignes(df, masque_autre, colonne)))
        libelles = {"illisible": "date illisible (format non reconnu)",
                    "date impossible": "date impossible (ex. 31/02)"}
        for format_lu, libelle in libelles.items():
            masque = formats == format_lu
            anomalies.append(nouvelle_anomalie(
                colonne, libelle, masque.sum(), exemples_lignes(df, masque, colonne)))
    return anomalies


def controler_coherences_inscriptions(df, travail):
    """Cohérences internes de la table inscriptions (dates, statut, année)."""
    debut, fin = travail["_debut"], travail["_fin"]
    statut = df["statut_final"]
    a_debut = debut.notna()
    cohorte_annee = df["annee_universitaire"].map(config.ANNEE_VERS_COHORTE)
    cohorte_nombre = pd.to_numeric(cohorte_annee)
    rentree_habituelle = travail.loc[a_debut].groupby(cohorte_annee[a_debut])["_debut"].agg(
        lambda s: s.mode().iloc[0])
    date_habituelle = cohorte_annee.map(rentree_habituelle)
    fin_suivi = debut + pd.Timedelta(days=config.N_SEMAINES * config.JOURS_PAR_SEMAINE)

    hors_octobre = a_debut & (debut.dt.month != config.MOIS_RENTREE)
    annee_fausse = a_debut & cohorte_nombre.notna() & (debut.dt.year != cohorte_nombre)
    autre_jour = a_debut & ~hors_octobre & ~annee_fausse & (debut != date_habituelle)
    fin_avant = debut.notna() & fin.notna() & (fin < debut)
    fin_apres_suivi = fin.notna() & fin_suivi.notna() & (fin >= fin_suivi)
    # Statut comparé sans tenir compte de la casse ni des espaces, pour couvrir toutes
    # les écritures observées (« INSCRIT », « inscrit », « abandonné »…).
    statut_simple = statut.str.strip().str.lower()
    inscrit_avec_fin = (statut_simple == "inscrit") & ~est_vide(df["date_fin"])
    sortie_sans_fin = statut_simple.str.startswith(("abandon", "transf")) & est_vide(df["date_fin"])

    texte_habituel = ", ".join(f"{c} : {d:%Y-%m-%d}" for c, d in rentree_habituelle.items())
    return [
        nouvelle_anomalie("date_debut", "date_debut hors du mois d'octobre", hors_octobre.sum(),
                          exemples_lignes(df, hors_octobre, "date_debut")),
        nouvelle_anomalie("date_debut", "année de date_debut différente de l'année de rentrée de "
                          "annee_universitaire", annee_fausse.sum(), exemples_lignes(df, annee_fausse, "date_debut")),
        nouvelle_anomalie("date_debut", f"date_debut en octobre mais différente de la rentrée la plus "
                          f"fréquente de la cohorte ({texte_habituel})", autre_jour.sum(),
                          exemples_lignes(df, autre_jour, "date_debut")),
        nouvelle_anomalie("date_fin", "date_fin antérieure à date_debut", fin_avant.sum(),
                          exemples_lignes(df, fin_avant, "date_fin")),
        nouvelle_anomalie("date_fin", f"date_fin après la fin du suivi (≥ date_debut + {config.N_SEMAINES} semaines)",
                          fin_apres_suivi.sum(), exemples_lignes(df, fin_apres_suivi, "date_fin")),
        nouvelle_anomalie("statut_final / date_fin", "statut « inscrit » (toutes écritures) avec une date_fin renseignée",
                          inscrit_avec_fin.sum(), exemples_lignes(df, inscrit_avec_fin, "date_fin")),
        nouvelle_anomalie("statut_final / date_fin", "abandon ou transfert (toutes écritures) sans date_fin",
                          sortie_sans_fin.sum(), exemples_lignes(df, sortie_sans_fin, "statut_final")),
    ]


# ===========================================================================
# 7. Contrôles propres à certaines tables
# ===========================================================================

def controler_mention_note(df):
    """Note du bac incompatible avec la mention déclarée.

    Seules les lignes à mention conforme au LISEZMOI et à note lisible dans [10 ; 20]
    sont comparées (les autres sont déjà signalées ailleurs). Une note égale à une
    borne commune (12, 14, 16) est acceptée pour les deux mentions voisines.
    """
    notes = df["note_bac"].map(lire_nombre)
    mention = df["mention_bac"]
    comparables = mention.isin(config.INTERVALLES_MENTION) & notes.map(
        lambda x: x is not None and 10 <= x <= 20)

    def incoherente(i):
        mini, maxi = config.INTERVALLES_MENTION[mention[i]]
        return not (mini <= notes[i] <= maxi)

    masque = pd.Series([comparables[i] and incoherente(i) for i in df.index], index=df.index)
    exemples = [
        f"l. {numero_ligne_fichier(i)} {df.at[i, config.COLONNE_ID]} : {montrer(mention[i])} avec {montrer(df.at[i, 'note_bac'])}"
        for i in df.index[masque][:config.NB_EXEMPLES]
    ]
    return nouvelle_anomalie(
        "mention_bac / note_bac", f"note_bac hors de l'intervalle de la mention (parmi les "
        f"{int(comparables.sum())} lignes comparables)", masque.sum(), exemples)


def controler_messages(df):
    """Messages vides et données personnelles dans le texte libre."""
    texte = df["texte"]
    vides = est_vide(texte) | texte.str.strip().str.fullmatch(r"[\W_]*")
    anomalies = [nouvelle_anomalie("texte", "message vide ou sans aucun mot (ex. « . »)", vides.sum(),
                                   exemples_lignes(df, vides, "texte"))]
    motifs = [
        ("nom propre introduit par « je suis », « c'est »…", config.MOTIF_NOM, "nom"),
        ("numéro de téléphone (format sénégalais 70, 75, 76, 77, 78)", config.MOTIF_TELEPHONE, "telephone"),
        ("adresse e-mail", config.MOTIF_EMAIL, "email"),
        ("adresse postale (rue, quartier, villa…)", config.MOTIF_ADRESSE, "adresse"),
    ]
    toutes = pd.Series(False, index=df.index)
    for libelle, motif, code in motifs:
        masque = contient(texte, motif)
        toutes = toutes | masque
        exemples = [f"{df.at[i, 'id_message']} : {montrer(masquer_texte(texte[i]))}"
                    for i in df.index[masque][:config.NB_EXEMPLES]]
        anomalies.append(nouvelle_anomalie("texte", f"donnée personnelle : {libelle}", masque.sum(),
                                           exemples, code=f"pii_{code}"))
    anomalies.append(nouvelle_anomalie("texte", "message contenant au moins une donnée personnelle "
                                       "(un message peut en contenir plusieurs)", toutes.sum(), []))
    return anomalies


def contient(serie, motif):
    """Vrai pour chaque texte où l'expression régulière est trouvée au moins une fois."""
    return serie.map(lambda texte: re.search(motif, texte) is not None)


def masquer_texte(texte):
    """Masque les données personnelles d'un message, pour l'affichage dans l'audit.

    Ce n'est PAS la pseudonymisation (DA-05) : on garde seulement la première lettre
    ou les deux premiers chiffres, pour que le lecteur voie le type de donnée.
    """
    def masquer_groupe(correspondance, groupe):
        """Remplace chaque mot du groupe nommé par sa première lettre suivie de •••."""
        debut = correspondance.start(groupe) - correspondance.start(0)
        fin = correspondance.end(groupe) - correspondance.start(0)
        texte_trouve = correspondance.group(0)
        mots = texte_trouve[debut:fin].split()
        return texte_trouve[:debut] + " ".join(m[0] + "•••" for m in mots) + texte_trouve[fin:]

    def masquer_telephone(correspondance):
        chiffres_vus = 0
        sortie = ""
        for caractere in correspondance.group(0):
            if caractere.isdigit():
                chiffres_vus += 1
                sortie += caractere if chiffres_vus <= 2 else "•"
            else:
                sortie += caractere
        return sortie

    def masquer_email(correspondance):
        return correspondance.group(0)[0] + "•••@•••"

    texte = re.sub(config.MOTIF_EMAIL, masquer_email, texte)
    texte = re.sub(config.MOTIF_TELEPHONE, masquer_telephone, texte)
    texte = re.sub(config.MOTIF_NOM, lambda m: masquer_groupe(m, "nom"), texte)
    return re.sub(config.MOTIF_ADRESSE, lambda m: masquer_groupe(m, "lieu"), texte)


# ===========================================================================
# 8. Contrôles entre tables
# ===========================================================================

def semaines_valides(df, colonne="semaine"):
    """Semaine convertie en entier, ou None si elle sort de [1 ; N_SEMAINES] ou est illisible."""
    nombres = df[colonne].map(lire_nombre)
    return nombres.map(lambda x: int(x) if pd.notna(x) and x == int(x) and 1 <= x <= config.N_SEMAINES else None)


def semaine_de_sortie(inscriptions_dates):
    """Semaine de sortie déclarée de chaque étudiant (convention PROVISOIRE).

    Convention utilisée pour l'audit seulement : semaine = (date_fin − date_debut) en
    jours, divisé par 7 (division entière), plus 1. La vraie règle de conversion est
    un point ouvert à faire valider par Saliou en DA-07 (CLAUDE.md §5).
    Sortie : Series indexée par identifiant normalisé (première inscription gardée).
    """
    travail = inscriptions_dates.copy()
    travail["_id_norm"] = normaliser_id(travail[config.COLONNE_ID])
    travail = travail.drop_duplicates("_id_norm")
    avec_dates = travail["_debut"].notna() & travail["_fin"].notna()
    ecart = (travail.loc[avec_dates, "_fin"] - travail.loc[avec_dates, "_debut"]).dt.days
    semaines = ecart // config.JOURS_PAR_SEMAINE + 1
    return pd.Series(semaines.values, index=travail.loc[avec_dates, "_id_norm"].values)


def controles_entre_tables(tables, inscriptions_dates):
    """Cohérence des identifiants et du calendrier entre les 5 tables."""
    ids = {nom: normaliser_id(df[config.COLONNE_ID]) for nom, df in tables.items()}
    connus = set(ids["etudiants"])
    anomalies = []

    for nom in ["inscriptions", "activite_hebdo", "tutorat", "messages"]:
        masque = ~ids[nom].isin(connus)
        anomalies.append(nouvelle_anomalie(
            f"{nom}.id_etudiant", f"identifiant absent de etudiants ({ids[nom][masque].nunique()} "
            "identifiants distincts) — nombre de lignes", masque.sum(),
            exemples_lignes(tables[nom], masque, config.COLONNE_ID)))

    etudiants = tables["etudiants"]
    for nom, libelle in [("inscriptions", "inscription"), ("activite_hebdo", "ligne d'activité")]:
        masque = ~ids["etudiants"].isin(set(ids[nom]))
        # On compte des étudiants distincts : un étudiant en double dans etudiants ne compte qu'une fois.
        anomalies.append(nouvelle_anomalie(
            "etudiants.id_etudiant", f"étudiant sans aucune {libelle} — nombre d'étudiants",
            ids["etudiants"][masque].nunique(), exemples_lignes(etudiants, masque, config.COLONNE_ID)))

    anomalies.append(controler_cohorte_annee(tables, ids))
    anomalies += controler_semaines_activite(tables, ids, inscriptions_dates)
    anomalies += controler_apres_sortie(tables, ids, inscriptions_dates)
    anomalies.append(controler_tutorat_multiple(tables["tutorat"], ids["tutorat"]))
    return anomalies


def controler_cohorte_annee(tables, ids):
    """La cohorte de etudiants doit correspondre à l'année universitaire de inscriptions."""
    cohorte = pd.Series(tables["etudiants"]["cohorte"].values, index=ids["etudiants"].values)
    cohorte = cohorte[~cohorte.index.duplicated()]
    inscriptions = tables["inscriptions"]
    attendue = inscriptions["annee_universitaire"].map(config.ANNEE_VERS_COHORTE)
    declaree = ids["inscriptions"].map(cohorte)
    masque = declaree.notna() & attendue.notna() & (declaree != attendue)
    return nouvelle_anomalie("inscriptions.annee_universitaire / etudiants.cohorte",
                             "année universitaire incompatible avec la cohorte", masque.sum(),
                             exemples_lignes(inscriptions, masque, "annee_universitaire"))


def controler_semaines_activite(tables, ids, inscriptions_dates):
    """Semaines manquantes dans l'activité hebdomadaire.

    Un étudiant toujours inscrit devrait avoir 30 semaines d'activité. On sépare les
    étudiants sans sortie déclarée (date_fin vide) de ceux qui sont sortis, pour qui
    l'arrêt du suivi peut être normal. On cherche aussi les « trous » au milieu.
    """
    activite = tables["activite_hebdo"].copy()
    activite["_id_norm"] = ids["activite_hebdo"]
    activite["_semaine"] = semaines_valides(activite)
    par_etudiant = activite.dropna(subset=["_semaine"]).groupby("_id_norm")["_semaine"].agg(
        ["min", "max", "nunique"])
    incomplets = par_etudiant[par_etudiant["nunique"] < config.N_SEMAINES]
    trous = par_etudiant[(par_etudiant["max"] - par_etudiant["min"] + 1) != par_etudiant["nunique"]]
    debut_tardif = par_etudiant[par_etudiant["min"] != 1]

    sorties = set(semaine_de_sortie(inscriptions_dates).index)
    sans_sortie = [i for i in incomplets.index if i not in sorties]
    avec_sortie = [i for i in incomplets.index if i in sorties]

    def exemples(liste):
        return [f"{i} : {int(incomplets.at[i, 'nunique'])} semaines (dernière : "
                f"{int(incomplets.at[i, 'max'])})" for i in liste[:config.NB_EXEMPLES]]

    return [
        nouvelle_anomalie("activite_hebdo.semaine", "étudiant SANS sortie déclarée ayant moins de "
                          f"{config.N_SEMAINES} semaines d'activité — nombre d'étudiants",
                          len(sans_sortie), exemples(sans_sortie)),
        nouvelle_anomalie("activite_hebdo.semaine", "étudiant AVEC sortie déclarée ayant moins de "
                          f"{config.N_SEMAINES} semaines d'activité (arrêt possiblement normal) — "
                          "nombre d'étudiants", len(avec_sortie), exemples(avec_sortie)),
        nouvelle_anomalie("activite_hebdo.semaine", "semaines manquantes au milieu de la série "
                          "(trou) — nombre d'étudiants", len(trous), list(trous.index[:config.NB_EXEMPLES])),
        nouvelle_anomalie("activite_hebdo.semaine", "série d'activité qui ne commence pas en semaine 1 "
                          "— nombre d'étudiants", len(debut_tardif), list(debut_tardif.index[:config.NB_EXEMPLES])),
    ]


def controler_apres_sortie(tables, ids, inscriptions_dates):
    """Activité, tutorat ou message datés APRÈS la semaine de sortie déclarée."""
    sortie = semaine_de_sortie(inscriptions_dates)
    anomalies = []
    cas = [
        ("activite_hebdo", "semaine", "ligne d'activité après la semaine de sortie déclarée"),
        ("tutorat", "semaine_debut", "tutorat commencé après la semaine de sortie déclarée"),
        ("messages", "semaine", "message envoyé après la semaine de sortie déclarée"),
    ]
    for nom, colonne, libelle in cas:
        df = tables[nom]
        semaine = df[colonne].map(lire_nombre)
        semaine_sortie = ids[nom].map(sortie)
        masque = semaine.notna() & semaine_sortie.notna() & (semaine > semaine_sortie)
        anomalies.append(nouvelle_anomalie(
            f"{nom}.{colonne}", f"{libelle} (conversion date → semaine provisoire)", masque.sum(),
            exemples_apres_sortie(df, masque, colonne, semaine_sortie)))
        if nom == "activite_hebdo":
            connexions = df["nb_connexions_lms"].map(lire_nombre).fillna(0)
            devoirs = df["devoirs_rendus"].map(lire_nombre).fillna(0)
            actif = masque & ((connexions > 0) | (devoirs > 0))
            anomalies.append(nouvelle_anomalie(
                f"{nom}.{colonne}", "dont lignes montrant une activité réelle (connexion ou devoir > 0)",
                actif.sum(), exemples_apres_sortie(df, actif, colonne, semaine_sortie)))
    return anomalies


def exemples_apres_sortie(df, masque, colonne, semaine_sortie):
    """Exemples « id : semaine x, sortie en semaine y »."""
    return [
        f"l. {numero_ligne_fichier(i)} {df.at[i, config.COLONNE_ID]} : {colonne} {df.at[i, colonne]}, "
        f"sortie en semaine {int(semaine_sortie[i])}"
        for i in df.index[masque][:config.NB_EXEMPLES]
    ]


def controler_tutorat_multiple(tutorat, ids_tutorat):
    """Étudiants ayant plusieurs lignes de tutorat (copies ou prises en charge multiples)."""
    comptes = ids_tutorat.value_counts()
    multiples = comptes[comptes > 1]
    return nouvelle_anomalie("tutorat.id_etudiant", "étudiant avec plusieurs lignes de tutorat — "
                             "nombre d'étudiants", len(multiples),
                             [f"{i} : {n} lignes" for i, n in multiples.head(config.NB_EXEMPLES).items()])


# ===========================================================================
# 9. Audit complet d'une table
# ===========================================================================

def auditer_table(table, df, inscriptions_dates):
    """Lance tous les contrôles d'une table. Sortie : (infos de structure, anomalies)."""
    infos, anomalies = analyser_structure(table, df)
    anomalies += controler_mojibake(df)
    anomalies += controler_identifiants(df)
    anomalies.append(controler_doublons_exacts(df))
    cles = {
        "etudiants": ([config.COLONNE_ID], "id_etudiant"),
        "inscriptions": ([config.COLONNE_ID], "id_etudiant"),
        "activite_hebdo": ([config.COLONNE_ID, "semaine"], "(id_etudiant, semaine)"),
        "tutorat": ([config.COLONNE_ID], "id_etudiant"),
        "messages": (["id_message"], "id_message"),
    }
    cle, libelle = cles[table]
    if table == "messages":
        masque = df.duplicated("id_message", keep=False)
        anomalies.append(nouvelle_anomalie("id_message", "id_message en double", masque.sum(),
                                           exemples_lignes(df, masque, "id_message")))
    else:
        anomalies += controler_doublons_cle(df, cle, libelle)
    anomalies += controler_vides(table, df)
    anomalies += controler_modalites(table, df)
    anomalies += controles_numeriques(table, df)
    if table == "etudiants":
        anomalies.append(controler_mention_note(df))
    if table == "inscriptions":
        anomalies += controler_formats_dates(df, inscriptions_dates)
        anomalies += controler_coherences_inscriptions(df, inscriptions_dates)
    if table == "tutorat":
        anomalies.append(controler_tutorat_apres_suivi(df))
    if table == "messages":
        anomalies += controler_messages(df)
    return infos, anomalies


def controler_tutorat_apres_suivi(df):
    """Tutorat commencé après la fin du suivi (semaine_debut > N_SEMAINES).

    Ces lignes sont aussi comptées dans « hors bornes » ; on les isole car un tutorat
    commencé après la semaine 30 ne peut pas avoir agi pendant le suivi.
    """
    semaine = df["semaine_debut"].map(lire_nombre)
    masque = semaine.notna() & (semaine > config.N_SEMAINES)
    return nouvelle_anomalie("semaine_debut", f"tutorat commencé après la semaine {config.N_SEMAINES} "
                             "(déjà compté dans « hors bornes »)", masque.sum(),
                             exemples_lignes(df, masque, "semaine_debut"))


# ===========================================================================
# 10. Rapport Markdown
# ===========================================================================

def tableau_anomalies(prefixe, anomalies):
    """Tableau Markdown « # | colonne | anomalie | nb de lignes | 3 exemples » (anomalies > 0)."""
    lignes = ["| # | colonne | anomalie | nb de lignes | 3 exemples |", "|---|---|---|---:|---|"]
    numero = 0
    for anomalie in anomalies:
        if anomalie["lignes"] == 0:
            continue
        numero += 1
        anomalie["numero"] = f"{prefixe}-{numero:02d}"
        exemples = "<br>".join(anomalie["exemples"]) if anomalie["exemples"] else "—"
        lignes.append(f"| {anomalie['numero']} | {anomalie['colonne']} | {anomalie['anomalie']} | "
                      f"{anomalie['lignes']} | {exemples} |")
    if numero == 0:
        lignes.append("| — | — | aucune anomalie | 0 | — |")
    return lignes


def libelle_court(anomalie):
    """Libellé coupé avant ses précisions chiffrées (« (0 écritures…) », « — nombre… »)."""
    return re.split(r" \(\d| — ", anomalie["anomalie"])[0]


def controles_sans_anomalie(anomalies):
    """Liste des contrôles effectués qui n'ont rien trouvé (pour montrer qu'ils ont été faits)."""
    vides = [f"{a['colonne']} : {libelle_court(a)}" for a in anomalies if a["lignes"] == 0]
    if not vides:
        return []
    return ["", "Contrôles effectués sans anomalie : " + " · ".join(vides) + "."]


def section_structure(infos):
    """Lignes Markdown décrivant la structure d'un fichier."""
    colonnes = [
        f"| {i + 1} | {montrer(brut)} | {attendu} | {type_} |"
        for i, (brut, attendu, type_) in enumerate(zip(infos["colonnes_brutes"], infos["colonnes_attendues"],
                                                     infos["types"]))
    ]
    return [
        f"- Fichier : `{infos['fichier']}`",
        f"- Séparateur attendu : {montrer(infos['separateur_attendu'])} · détecté : {montrer(infos['separateur_detecte'])}",
        f"- Encodage : {infos['encodage']} · BOM : {'oui' if infos['bom'] else 'non'} · fins de ligne : {infos['fins_de_ligne']}",
        f"- Lignes de données : {infos['lignes_donnees']} (annoncées ≈ {infos['lignes_annoncees']}) · "
        f"lignes physiques (en-tête compris) : {infos['lignes_physiques']}",
        "",
        "| # | colonne brute | colonne attendue | type lu par pandas (inférence par défaut) |",
        "|---|---|---|---|",
        *colonnes,
    ]


def section_modalites(table, df):
    """Toutes les valeurs distinctes des colonnes catégorielles, avec leurs effectifs."""
    lignes = []
    for (nom_table, colonne), attendues in config.MODALITES.items():
        if nom_table != table:
            continue
        comptes = df[colonne].value_counts()
        valeurs = ", ".join(
            f"{montrer(v)}{'' if v in attendues else ' ⚠'} {n}" for v, n in comptes.items())
        lignes.append(f"- **{colonne}** ({len(comptes)} valeurs distinctes) : {valeurs}")
    if not lignes:
        return []
    return ["", "#### Modalités observées (⚠ = absente de la liste attendue)", "", *lignes]


# Anomalies jugées les plus dangereuses pour T, E ou le tutorat (jugement de l'audit,
# à discuter avec Saliou). Chaque entrée regroupe des anomalies liées, retrouvées par
# (table, colonne, début du libellé) ; « entre tables » désigne la section croisée.
ANOMALIES_CRITIQUES = [
    {
        "titre": "Entrées de la règle d'inactivité (connexions et devoirs)",
        "references": [
            ("activite_hebdo", "nb_connexions_lms", "valeur manquante"),
            ("activite_hebdo", "nb_connexions_lms", "valeur hors bornes"),
            ("activite_hebdo", "nb_connexions_lms", "valeur très éloignée"),
            ("activite_hebdo", "devoirs_rendus", "valeur hors bornes"),
        ],
        "raison": "E : le décrochage non déclaré se lit sur « aucune connexion ni devoir rendu » "
                  "pendant 4 semaines ; une connexion manquante, négative ou aberrante fait "
                  "apparaître ou disparaître un décrochage.",
    },
    {
        "titre": "Statut de sortie et date de sortie",
        "references": [
            ("inscriptions", "statut_final", "valeur manquante"),
            ("inscriptions", "statut_final", "modalité non conforme"),
            ("inscriptions", "statut_final / date_fin", "abandon ou transfert"),
            ("inscriptions", "date_fin", "date_fin antérieure"),
            ("inscriptions", "date_fin", "date_fin après la fin du suivi"),
        ],
        "raison": "E et T : le statut sépare l'abandon déclaré (E = 1) de la censure (transfert, "
                  "inscrit) et date_fin donne la semaine de l'événement ; un statut vide ou un "
                  "abandon sans date empêche de calculer T et E.",
    },
    {
        "titre": "Date de rentrée (origine du temps)",
        "references": [
            ("inscriptions", "date_debut", "date dans un autre format"),
            ("inscriptions", "date_debut", "date_debut hors du mois"),
            ("inscriptions", "date_debut", "année de date_debut"),
            ("inscriptions", "date_debut", "date_debut en octobre"),
        ],
        "raison": "T : date_debut fixe la semaine 1 de l'étudiant ; quatre formats coexistent et "
                  "quelques dates sortent de la rentrée habituelle, ce qui décale toutes ses semaines "
                  "(et la semaine de sortie calculée).",
    },
    {
        "titre": "Clé (étudiant, semaine) de l'activité",
        "references": [
            ("activite_hebdo", "id_etudiant", "identifiant en minuscules"),
            ("activite_hebdo", "(id_etudiant, semaine)", "même (id_etudiant, semaine) répété avec le même"),
            ("activite_hebdo", "(id_etudiant, semaine)", "même (id_etudiant, semaine) répété avec des"),
            ("activite_hebdo", "semaine", "valeur sentinelle"),
            ("activite_hebdo", "semaine", "valeur hors bornes"),
            ("entre tables", "activite_hebdo.semaine", "étudiant SANS sortie"),
        ],
        "raison": "E : la règle des 4 semaines consécutives suppose une ligne par étudiant et par "
                  "semaine ; des identifiants mal écrits, des semaines en double avec des valeurs "
                  "différentes ou des semaines manquantes créent de fausses séries d'inactivité.",
    },
    {
        "titre": "Semaine de début du tutorat",
        "references": [
            ("tutorat", "semaine_debut", "valeur hors bornes"),
            ("entre tables", "tutorat.semaine_debut", "tutorat commencé après la semaine de sortie"),
            ("entre tables", "tutorat.id_etudiant", "étudiant avec plusieurs lignes"),
            ("tutorat", "nb_seances", "valeur hors bornes"),
        ],
        "raison": "Tutorat : la semaine de début porte le biais du temps immortel et l'analyse "
                  "landmark ; une semaine 0 ou > 30, un tutorat après la sortie ou 0 séance suivie "
                  "faussent la définition du traitement.",
    },
]


def trouver_anomalie(resultats, anomalies_croisees, table, colonne, debut_libelle):
    """Retrouve une anomalie calculée à partir de sa table, sa colonne et son libellé."""
    candidates = anomalies_croisees if table == "entre tables" else resultats[table]["anomalies"]
    for anomalie in candidates:
        if anomalie["colonne"] == colonne and anomalie["anomalie"].startswith(debut_libelle):
            return anomalie
    return None


def section_resume(resultats, anomalies_croisees):
    """Résumé final : nombre d'anomalies par table et les 5 anomalies les plus critiques."""
    lignes = ["## Résumé", "", "| Table | lignes de données | anomalies constatées (types) | "
              "lignes concernées (somme, une ligne peut compter plusieurs fois) |", "|---|---:|---:|---:|"]
    for table, resultat in resultats.items():
        actives = [a for a in resultat["anomalies"] if a["lignes"] > 0]
        lignes.append(f"| {table} | {resultat['infos']['lignes_donnees']} | {len(actives)} | "
                      f"{sum(a['lignes'] for a in actives)} |")
    actives = [a for a in anomalies_croisees if a["lignes"] > 0]
    lignes.append(f"| entre tables | — | {len(actives)} | {sum(a['lignes'] for a in actives)} |")
    lignes += ["", "### Les 5 anomalies qui risquent le plus de fausser T, E ou le tutorat", ""]
    for rang, critique in enumerate(ANOMALIES_CRITIQUES, start=1):
        constats = []
        for table, colonne, debut in critique["references"]:
            anomalie = trouver_anomalie(resultats, anomalies_croisees, table, colonne, debut)
            if anomalie is not None and anomalie["lignes"] > 0:
                constats.append(f"{anomalie['numero']} {libelle_court(anomalie)} ({anomalie['lignes']})")
        detail = " ; ".join(constats) if constats else "aucune constatée"
        lignes.append(f"{rang}. **{critique['titre']}** — {detail}. {critique['raison']}")
    return lignes


def construire_rapport(resultats, anomalies_croisees):
    """Assemble le texte complet de docs/audit_qualite.md."""
    prefixes = {"etudiants": "ETU", "inscriptions": "INS", "activite_hebdo": "ACT",
                "tutorat": "TUT", "messages": "MSG"}
    lignes = [
        "# Audit qualité des fichiers bruts (DA-01)",
        "",
        "> Fichier généré par `python -m src.audit` — ne pas modifier à la main.",
        "> L'audit **constate** sans rien corriger : les traitements seront décidés par Saliou (DA-02 à DA-05).",
        "> Les valeurs sont montrées entre « » pour rendre visibles les espaces. « l. n » = numéro de ligne",
        "> dans le fichier (ligne 1 = en-tête).",
        "> Rapprochements entre tables : identifiant mis en majuscules et sans espaces (normalisation provisoire).",
        f"> Semaine de sortie : (date_fin − date_debut) // {config.JOURS_PAR_SEMAINE} + 1 (convention provisoire, à valider en DA-07).",
        "",
    ]
    for table, resultat in resultats.items():
        lignes += [f"## Table `{table}`", "", "### Structure", ""]
        lignes += section_structure(resultat["infos"])
        lignes += section_modalites(table, resultat["df"])
        lignes += ["", "### Anomalies", ""]
        lignes += tableau_anomalies(prefixes[table], resultat["anomalies"])
        lignes += controles_sans_anomalie(resultat["anomalies"])
        lignes.append("")
    lignes += ["## Contrôles entre tables", ""]
    lignes += tableau_anomalies("X", anomalies_croisees)
    lignes += controles_sans_anomalie(anomalies_croisees)
    lignes.append("")
    lignes += section_resume(resultats, anomalies_croisees)
    return "\n".join(lignes) + "\n"


def lancer_audit():
    """Point d'entrée : audite les 5 tables et écrit docs/audit_qualite.md."""
    tables = {table: lire_table(table) for table in config.FICHIERS_BRUTS}
    inscriptions_dates = ajouter_dates(tables["inscriptions"])
    resultats = {}
    for table, df in tables.items():
        infos, anomalies = auditer_table(table, df, inscriptions_dates)
        resultats[table] = {"infos": infos, "anomalies": anomalies, "df": df}
    anomalies_croisees = controles_entre_tables(tables, inscriptions_dates)
    rapport = construire_rapport(resultats, anomalies_croisees)
    config.FICHIER_AUDIT.write_text(rapport, encoding=config.ENCODAGE, newline="\n")
    print(f"Audit écrit dans {config.FICHIER_AUDIT.relative_to(config.RACINE)}")


if __name__ == "__main__":
    lancer_audit()
