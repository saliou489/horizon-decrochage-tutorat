"""Outils partagés par le nettoyage de toutes les tables.

Rôle du module : lecture des fichiers bruts, forme simplifiée d'un texte,
harmonisation des modalités, conversion des nombres, écriture des tables nettoyées,
profil « avant / après » et génération du journal de nettoyage.

Tâches couvertes : DA-02 (et suivantes, qui réutiliseront ces outils).
"""

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

def profil(df, colonne_id=config.COLONNE_ID):
    """Lignes, valeurs manquantes par colonne et doublons d'identifiant d'une table.

    Une valeur manquante = case vide (table brute, en texte) ou NA (table nettoyée).
    Les doublons d'identifiant sont comptés après mise en majuscules et retrait des
    espaces, pour que l'avant et l'après soient comparables.
    Sortie : dictionnaire {"lignes", "manquants" (dict par colonne), "doublons_id"}.
    """
    manquants = {}
    for colonne in df.columns:
        valeurs = df[colonne]
        manque = valeurs.isna()
        if valeurs.dtype == object or pd.api.types.is_string_dtype(valeurs):
            manque = manque | (valeurs.fillna("").astype(str).str.strip() == "")
        manquants[colonne] = int(manque.sum())
    identifiants = df[colonne_id].astype(str).str.strip().str.upper()
    return {
        "lignes": len(df),
        "manquants": manquants,
        "doublons_id": int(identifiants.duplicated().sum()),
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
        f"| Doublons d'identifiant (majuscules, sans espaces) | {avant['doublons_id']} | {apres['doublons_id']} |",
    ]
    for colonne in colonnes_apres:
        lignes.append(f"| Valeurs manquantes : {colonne} | {avant['manquants'].get(colonne, 0)} | "
                      f"{apres['manquants'][colonne]} |")
    lignes.append(f"| Valeurs manquantes : total | {sum(avant['manquants'].values())} | "
                  f"{sum(apres['manquants'].values())} |")
    return lignes


def ecrire_journal(resultats):
    """Régénère docs/journal_nettoyage.md à partir des résultats de chaque table.

    Entrée : liste de dictionnaires {"table", "entrees", "avant", "apres", "colonnes"}.
    Tous les nombres viennent du code : ce fichier ne se modifie jamais à la main.
    """
    entrees = [e for resultat in resultats for e in resultat["entrees"]]
    lignes = [
        "# Journal de nettoyage",
        "",
        "> Fichier généré par `python -m src.nettoyage` — ne pas modifier à la main.",
        "> Chaque traitement applique une décision validée par Saliou (`docs/decisions.md`).",
        "> Les numéros d'anomalie « ETU-xx » renvoient à `docs/audit_qualite.md`.",
        "",
        "## Traitements appliqués",
        "",
        *tableau_journal(entrees),
        "",
        "## Tableau avant / après",
        "",
    ]
    for resultat in resultats:
        lignes += tableau_avant_apres(resultat["table"], resultat["avant"], resultat["apres"],
                                      resultat["colonnes"])
        lignes.append("")
    config.FICHIER_JOURNAL.write_text("\n".join(lignes), encoding=config.ENCODAGE, newline="\n")
    return config.FICHIER_JOURNAL
