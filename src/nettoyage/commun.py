"""Outils partagés par le nettoyage de toutes les tables.

Rôle du module : lecture des fichiers bruts, forme simplifiée d'un texte,
harmonisation des modalités, conversion des nombres, écriture des tables nettoyées,
profil « avant / après » et génération du journal de nettoyage.

Tâches couvertes : DA-02 à DA-05 (outils), DA-06 (journal complet).
"""

import re
import unicodedata

import pandas as pd

from src import config


class ErreurNettoyage(Exception):
    """Cas non prévu par les règles validées : le nettoyage s'arrête et le signale.

    CLAUDE.md §2 : un cas non couvert ne se tranche jamais en silence.
    """


# ===========================================================================
# Lecture et écriture
# ===========================================================================

def lire_brut(table):
    """Lit un fichier de data/raw/ sans rien convertir.

    Entrée : nom de la table (clé de config.FICHIERS_BRUTS).
    Sortie : DataFrame dont toutes les valeurs sont des chaînes ; une case vide reste
    une chaîne vide. Les en-têtes sont gardés tels quels (ils sont corrigés par une règle).
    """
    description = config.FICHIERS_BRUTS[table]
    return pd.read_csv(
        config.DOSSIER_RAW / description["fichier"],
        sep=description["separateur"],
        dtype=str,
        keep_default_na=False,
        encoding=config.ENCODAGE,
    )


def ecrire_table(df, table):
    """Écrit une table nettoyée dans data/processed/<table>.csv (UTF-8, sans index)."""
    config.DOSSIER_PROCESSED.mkdir(parents=True, exist_ok=True)
    chemin = config.DOSSIER_PROCESSED / f"{table}.csv"
    df.to_csv(chemin, sep=config.SEPARATEUR_PROCESSED, index=False, encoding=config.ENCODAGE)
    return chemin


def ecrire_rejets(df, chemin):
    """Écrit des lignes retirées dans data/processed/rejets/ (traçabilité, D-17, D-23)."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(chemin, sep=config.SEPARATEUR_PROCESSED, index=False, encoding=config.ENCODAGE)
    return chemin


def renommer_par_position(df, table):
    """Copie de la table brute avec les en-têtes du LISEZMOI (par position).

    Sert seulement au tableau avant / après, pour comparer les mêmes colonnes.
    """
    comparable = df.copy()
    comparable.columns = config.FICHIERS_BRUTS[table]["colonnes"]
    return comparable


# ===========================================================================
# Semaines et drapeaux (réutilisés en DA-07)
# ===========================================================================

def semaine_depuis_date(date, date_debut):
    """Numéro de semaine d'une date depuis la rentrée de l'étudiant (D-22).

    semaine = (date − date_debut en jours) // 7 + 1 : le jour de la rentrée et les
    6 jours suivants forment la semaine 1. Entrées : dates (texte AAAA-MM-JJ ou date).
    """
    ecart = pd.Timestamp(date) - pd.Timestamp(date_debut)
    return ecart.days // config.JOURS_PAR_SEMAINE + 1


def semaines_de_sortie(inscriptions):
    """Semaine de sortie de chaque étudiant sorti pendant le suivi.

    Entrée : data/processed/inscriptions.csv (déjà nettoyée).
    Sortie : Series {id_etudiant: semaine}, seulement quand sortie_suivi vaut abandon
    ou transfert et que date_fin est renseignée ; les autres étudiants n'ont pas de
    semaine de sortie.
    """
    sortis = inscriptions[inscriptions["sortie_suivi"].isin([config.SORTIE_ABANDON, config.SORTIE_TRANSFERT])
                          & inscriptions["date_fin"].notna()]
    semaines = [semaine_depuis_date(fin, debut) for fin, debut in zip(sortis["date_fin"], sortis["date_debut"])]
    return pd.Series(semaines, index=sortis[config.COLONNE_ID].values, dtype="int64")


def ajouter_drapeau(drapeaux, masque, drapeau):
    """Ajoute un drapeau aux lignes repérées par le masque.

    Entrée : série de listes de drapeaux (une liste par ligne). Sortie : nouvelle série.
    """
    return pd.Series([liste + [drapeau] if marque else liste for liste, marque in zip(drapeaux, masque)],
                     index=drapeaux.index)


def drapeaux_en_texte(drapeaux):
    """Liste de drapeaux -> texte séparé par « ; » ; manquant si la liste est vide."""
    return drapeaux.map(lambda liste: config.SEPARATEUR_DRAPEAUX.join(liste) if liste else pd.NA)


# ===========================================================================
# Journal
# ===========================================================================

def entree_journal(table, anomalie, lignes, traitement, justification):
    """Une ligne du journal de nettoyage (gabarit de l'annexe A du cahier des charges)."""
    return {
        "table": table,
        "anomalie": anomalie,
        "lignes": int(lignes),
        "traitement": traitement,
        "justification": justification,
    }


# ===========================================================================
# Texte et modalités
# ===========================================================================

def est_vide(serie):
    """Vrai pour les cases vides ou ne contenant que des espaces."""
    return serie.str.strip() == ""


def forme_simplifiee(valeur):
    """Forme simplifiée d'un texte, pour comparer des écritures différentes.

    Minuscules, accents retirés, tirets remplacés par des espaces, espaces multiples
    réduits à un, espaces de bord retirés. Exemple : « St-Louis » -> « st louis ».
    Sans le remplacement des tirets, « St-Louis » ne serait pas reconnu.
    """
    decomposee = unicodedata.normalize("NFKD", valeur)
    sans_accents = "".join(c for c in decomposee if not unicodedata.combining(c))
    texte = sans_accents.lower().replace("-", " ")
    return " ".join(texte.split())


def table_de_correspondance(officielles, abreviations):
    """Dictionnaire {forme simplifiée -> modalité officielle}.

    Entrées : liste des modalités officielles (LISEZMOI), dictionnaire des
    abréviations déjà écrites en forme simplifiée.
    """
    correspondance = {forme_simplifiee(m): m for m in officielles}
    for abreviation, modalite in abreviations.items():
        correspondance[forme_simplifiee(abreviation)] = modalite
    return correspondance


def harmoniser_modalites(serie, officielles, abreviations, nom_colonne):
    """Ramène chaque valeur à sa modalité officielle.

    Sortie : (série harmonisée, nombre de valeurs dont l'écriture a changé).
    Les cases vides restent vides. Une valeur qui ne correspond à aucune règle
    déclenche ErreurNettoyage : on ne la met jamais à manquant en silence.
    """
    correspondance = table_de_correspondance(officielles, abreviations)
    vides = est_vide(serie)
    simplifiees = serie.map(forme_simplifiee)
    inconnues = sorted(set(serie[~vides & ~simplifiees.isin(correspondance)]))
    if inconnues:
        raise ErreurNettoyage(
            f"Colonne {nom_colonne} : valeur(s) sans règle de correspondance {inconnues}. "
            "Règle à faire valider par Saliou avant de continuer."
        )
    harmonisee = simplifiees.map(correspondance).where(~vides, "")
    nb_changees = int((harmonisee != serie).sum())
    return harmonisee, nb_changees


# ===========================================================================
# Nombres
# ===========================================================================

def retirer_unites(serie, unites):
    """Retire une unité écrite après le nombre (« 19 ans » -> « 19 »).

    Sortie : (série sans unités, nombre de valeurs modifiées).
    """
    motif = r"\s*(?:" + "|".join(unites) + r")\s*$"
    nettoyee = serie.str.replace(motif, "", regex=True)
    return nettoyee, int((nettoyee != serie).sum())


def remplacer_virgule(serie):
    """Virgule décimale -> point (« 12,71 » -> « 12.71 »).

    Sortie : (série corrigée, nombre de valeurs modifiées).
    """
    corrigee = serie.str.replace(",", ".", regex=False)
    return corrigee, int((corrigee != serie).sum())


def convertir_nombres(serie, nom_colonne, entier):
    """Convertit des chaînes en nombres ; vide -> manquant.

    Entrées : la série (déjà sans virgule ni unité), son nom, entier=True pour le
    type entier de pandas (« Int64 », qui accepte les manquants).
    Une valeur non vide impossible à lire déclenche ErreurNettoyage.
    """
    texte = serie.str.strip()
    nombres = pd.to_numeric(texte.where(texte != ""), errors="coerce")
    illisibles = sorted(set(texte[(texte != "") & nombres.isna()]))
    if illisibles:
        raise ErreurNettoyage(f"Colonne {nom_colonne} : valeur(s) non numériques {illisibles}.")
    if not entier:
        return nombres.astype("float64")
    non_entiers = nombres.notna() & (nombres != nombres.round())
    if non_entiers.any():
        raise ErreurNettoyage(
            f"Colonne {nom_colonne} : valeur(s) non entières {sorted(set(texte[non_entiers]))}.")
    return nombres.astype("Int64")


# ===========================================================================
# Profil avant / après
# ===========================================================================

def profil(df, colonne_id=config.COLONNE_ID, autres_colonnes_cle=()):
    """Lignes, valeurs manquantes par colonne, doublons de clé et étudiants distincts.

    Une valeur manquante = case vide (table brute, en texte) ou NA (table nettoyée).
    La clé est l'identifiant, plus d'autres colonnes si la table en a besoin (ex.
    semaine pour activite_hebdo). L'identifiant est mis en majuscules sans espaces,
    pour que l'avant et l'après soient comparables.
    Sortie : dictionnaire {"lignes", "manquants", "doublons_id", "cle", "etudiants"}.
    """
    manquants = {}
    for colonne in df.columns:
        valeurs = df[colonne]
        manque = valeurs.isna()
        if valeurs.dtype == object or pd.api.types.is_string_dtype(valeurs):
            manque = manque | (valeurs.fillna("").astype(str).str.strip() == "")
        manquants[colonne] = int(manque.sum())
    cle = pd.DataFrame({colonne_id: df[colonne_id].astype(str).str.strip().str.upper()})
    for colonne in autres_colonnes_cle:
        cle[colonne] = df[colonne].astype(str).str.strip()
    return {
        "lignes": len(df),
        "manquants": manquants,
        "doublons_id": int(cle.duplicated().sum()),
        "cle": ", ".join([colonne_id, *autres_colonnes_cle]),
        # Étudiants distincts : toujours comptés sur id_etudiant, même quand la clé de
        # la table est une autre colonne (ex. id_message pour messages).
        "etudiants": int(df[config.COLONNE_ID].astype(str).str.strip().str.upper().nunique()),
    }


# ===========================================================================
# Génération du journal Markdown
# ===========================================================================

def texte_cellule(valeur):
    """Protège le caractère « | » qui casserait un tableau Markdown."""
    return str(valeur).replace("|", "\\|")


def tableau_journal(entrees):
    """Tableau du gabarit annexe A : # | Table | Anomalie | Lignes | Traitement | Justification."""
    lignes = [
        "| # | Table | Anomalie constatée | Lignes | Traitement appliqué | Justification |",
        "|---:|---|---|---:|---|---|",
    ]
    for numero, entree in enumerate(entrees, start=1):
        lignes.append(
            f"| {numero} | {entree['table']} | {texte_cellule(entree['anomalie'])} | "
            f"{entree['lignes']} | {texte_cellule(entree['traitement'])} | "
            f"{texte_cellule(entree['justification'])} |"
        )
    return lignes


def tableau_avant_apres(table, avant, apres, colonnes_apres):
    """Tableau avant / après : lignes, manquants par colonne, doublons d'identifiant.

    Entrées : profils avant (table brute, colonnes renommées par position pour la
    comparaison) et après ; liste des colonnes de la table nettoyée.
    """
    lignes = [
        f"#### `{table}`",
        "",
        "| Indicateur | Avant | Après |",
        "|---|---:|---:|",
        f"| Lignes | {avant['lignes']} | {apres['lignes']} |",
        f"| Étudiants distincts | {avant['etudiants']} | {apres['etudiants']} |",
        f"| Doublons de la clé ({apres['cle']} ; identifiant en majuscules, sans espaces) | "
        f"{avant['doublons_id']} | {apres['doublons_id']} |",
    ]
    # Une colonne créée par le nettoyage (ex. drapeau_inscription) n'existait pas avant :
    # ses cases vides veulent dire « rien à signaler », pas « valeur manquante ».
    # Elle est montrée à part et exclue du total.
    colonnes_d_origine = [c for c in colonnes_apres if c in avant["manquants"]]
    for colonne in colonnes_apres:
        if colonne in avant["manquants"]:
            lignes.append(f"| Valeurs manquantes : {colonne} | {avant['manquants'][colonne]} | "
                          f"{apres['manquants'][colonne]} |")
        else:
            lignes.append(f"| Cases vides : {colonne} (colonne créée) | — | {apres['manquants'][colonne]} |")
    total_apres = sum(apres["manquants"][c] for c in colonnes_d_origine)
    lignes.append(f"| Valeurs manquantes : total (colonnes d'origine) | {sum(avant['manquants'].values())} | "
                  f"{total_apres} |")
    return lignes


def tableaux_effectifs(effectifs):
    """Tableaux « valeur | effectif » des colonnes dérivées (ex. sortie_suivi).

    Entrée : liste de (nom de colonne, {valeur: effectif}).
    """
    lignes = []
    for colonne, comptes in effectifs:
        lignes += [f"Effectifs de `{colonne}` :", "", "| Valeur | Effectif |", "|---|---:|"]
        lignes += [f"| {valeur} | {effectif} |" for valeur, effectif in comptes.items()]
        lignes.append("")
    return lignes


def codes_de_l_audit():
    """Codes d'anomalie présents dans docs/audit_qualite.md (lignes des tableaux d'anomalies)."""
    texte = config.FICHIER_AUDIT.read_text(encoding=config.ENCODAGE)
    # Une anomalie de l'audit est une ligne de tableau qui commence par « | <code> | ».
    motif = r"^\| (" + config.CODE_AUDIT + r") \|"
    return sorted(set(re.findall(motif, texte, flags=re.MULTILINE)))


def verifier_codes(entrees):
    """Chaque code de l'audit doit être traité (cité dans le journal) ou listé sans traitement.

    Un code qui n'est ni l'un ni l'autre arrête le nettoyage : on n'invente pas de raison.
    Sortie : liste triée des codes cités par les traitements.
    """
    cites = set()
    for entree in entrees:
        cites |= set(re.findall(config.MOTIF_CODE_AUDIT, entree["anomalie"]))
    oublies = [c for c in codes_de_l_audit() if c not in cites and c not in config.ANOMALIES_SANS_TRAITEMENT]
    if oublies:
        raise ErreurNettoyage(f"Code(s) de l'audit ni traité(s) ni justifié(s) : {oublies}")
    return sorted(cites)


def section_sans_traitement():
    """Tableau « Anomalies constatées sans traitement » : un code par ligne, avec sa raison."""
    lignes = ["| Code | Raison |", "|---|---|"]
    lignes += [f"| {code} | {texte_cellule(raison)} |" for code, raison in config.ANOMALIES_SANS_TRAITEMENT.items()]
    return lignes


def section_bilan(resultats, nb_codes_traites):
    """Bilan global : lignes par table, règles appliquées, lignes envoyées en rejets."""
    lignes = ["| Table | Lignes avant | Lignes après | Règles appliquées |", "|---|---:|---:|---:|"]
    for resultat in resultats:
        lignes.append(f"| {resultat['table']} | {resultat['avant']['lignes']} | {resultat['apres']['lignes']} | "
                      f"{len(resultat['lignes_touchees'])} |")
    total_regles = sum(len(r["lignes_touchees"]) for r in resultats)
    lignes.append(f"| **Total** | {sum(r['avant']['lignes'] for r in resultats)} | "
                  f"{sum(r['apres']['lignes'] for r in resultats)} | {total_regles} |")
    lignes += ["", "| Fichier de rejets | Lignes |", "|---|---:|"]
    for resultat in resultats:
        for fichier, nb in resultat.get("rejets", {}).items():
            lignes.append(f"| `data/processed/rejets/{fichier}` | {nb} |")
    lignes += ["", f"Codes d'anomalie de l'audit : {len(codes_de_l_audit())} ; cités par un traitement : "
               f"{nb_codes_traites} ; laissés sans traitement (raison donnée) : "
               f"{len(config.ANOMALIES_SANS_TRAITEMENT)}."]
    return lignes


def ecrire_journal(resultats):
    """Régénère docs/journal_nettoyage.md à partir des résultats de chaque table.

    Entrée : liste de dictionnaires {"table", "entrees", "avant", "apres", "colonnes",
    "lignes_touchees", et en option "effectifs", "rejets"}.
    Tous les nombres viennent du code : ce fichier ne se modifie jamais à la main.
    """
    entrees = [e for resultat in resultats for e in resultat["entrees"]]
    codes_traites = verifier_codes(entrees)
    lignes = [
        "# Journal de nettoyage",
        "",
        "> Fichier généré par `python -m src.nettoyage` — ne pas modifier à la main.",
        "> Chaque traitement applique une décision validée par Saliou (`docs/decisions.md`).",
        "> Les codes d'anomalie (ETU-xx, INS-xx, ACT-xx, TUT-xx, MSG-xx, X-xx) renvoient à `docs/audit_qualite.md`.",
        "",
        "## Bilan global",
        "",
        *section_bilan(resultats, len(codes_traites)),
        "",
        "## Traitements appliqués",
        "",
        *tableau_journal(entrees),
        "",
        "## Anomalies constatées sans traitement",
        "",
        *section_sans_traitement(),
        "",
        "## Tableau avant / après",
        "",
    ]
    for resultat in resultats:
        lignes += tableau_avant_apres(resultat["table"], resultat["avant"], resultat["apres"],
                                      resultat["colonnes"])
        lignes.append("")
        lignes += tableaux_effectifs(resultat.get("effectifs", []))
    config.FICHIER_JOURNAL.write_text("\n".join(lignes), encoding=config.ENCODAGE, newline="\n")
    return config.FICHIER_JOURNAL
