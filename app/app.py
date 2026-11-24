"""Tableau de bord Streamlit du projet Horizon : décrochage et tutorat.

Rôle du module : afficher, pour un conseiller pédagogique, les étudiants de la cohorte
2025 à risque de décrocher à une semaine L choisie, la fiche d'un étudiant (risque, profil,
facteurs, activité, courbe de survie, fiche LLM), l'effet estimé du tutorat et une page
« À propos ». Rien n'est recalculé et l'API du LLM n'est jamais appelée : la logique est
dans src/tableau_de_bord.py, qui relit les résultats de run_all.py (D-68).
Lancement depuis la racine du dépôt : streamlit run app/app.py

Tâches couvertes : DB-01.
"""

import sys
from datetime import datetime
from pathlib import Path

# Racine du dépôt (dossier parent de app/) ajoutée au chemin d'import, pour trouver src/.
RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import matplotlib  # noqa: E402

# Les figures sont rendues en images pour la page web, jamais dans une fenêtre : le moteur
# « Agg » évite le moteur de fenêtres par défaut (TkAgg sous Windows), qui plante quand
# Streamlit dessine hors du fil d'exécution principal.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MultipleLocator  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src import config  # noqa: E402
from src import tableau_de_bord as tb  # noqa: E402

PAGE_RISQUE = "Étudiants à risque"
PAGE_FICHE = "Fiche étudiant"
PAGE_EFFET = "Effet du tutorat"
PAGE_A_PROPOS = "À propos"
PAGES = [PAGE_RISQUE, PAGE_FICHE, PAGE_EFFET, PAGE_A_PROPOS]
NOMS_ACTIVITE = {"connexions_plateforme": "Connexions à la plateforme", "devoirs_rendus": "Devoirs rendus",
                 "seances_manquees": "Séances manquées", "note_moyenne": "Note moyenne (sur 20)"}
# Colonnes de la table de la page 1 : titre -> (largeur en pixels, infobulle).
COLONNES_TABLE = {
    "Identifiant": (90, "Identifiant pseudonymisé de l'étudiant."),
    "Risque Cox": (100, "Probabilité estimée de décrocher d'ici la semaine 30 (modèle de Cox, profil de rentrée)."),
    "Risque sem. suivante": (140, "Signal à court terme du gradient boosting (activité jusqu'à la semaine L)."),
    "Facteurs associés": (280, "Multiplicateur du risque par rapport à un étudiant moyen de la promotion ; "
                               "association, pas cause."),
    "Tutorat": (185, "Situation du tutorat connue à la semaine L."),
    "Fiche LLM": (90, "Statut de la fiche d'entretien (semaine 8 seulement)."),
}
COULEUR_ETUDIANT = "#C44E52"
COULEUR_REFERENCE = "#4C72B0"


# ===========================================================================
# Données (lues une seule fois, puis gardées en cache)
# ===========================================================================

@st.cache_data(show_spinner="Lecture des résultats de run_all.py…")
def donnees():
    """Toutes les tables, lues une fois pour toute la session."""
    return tb.charger_donnees()


@st.cache_data(show_spinner="Calcul de la table de la semaine…")
def table_semaine(semaine):
    """Table des étudiants suivis après `semaine` (une fois par semaine choisie)."""
    return tb.table_a_risque(donnees(), semaine)


@st.cache_data(show_spinner=False)
def facteurs_semaine(semaine):
    """Facteurs détaillés de chaque étudiant suivi après `semaine`."""
    return tb.facteurs_par_etudiant(donnees(), semaine)


# ===========================================================================
# Format français
# ===========================================================================

def nombre(valeur, decimales=1):
    """Nombre au format français : 17,8 ; signe moins typographique."""
    return f"{valeur:.{decimales}f}".replace(".", ",").replace("-", "−")


def pct(valeur, decimales=1):
    """Pourcentage au format français : 17,8 % (espace insécable : « % » ne passe pas seul à la ligne)."""
    return f"{nombre(valeur, decimales)} %"


def entier(valeur):
    """Entier avec espace des milliers : 2 177."""
    return f"{int(valeur):,}".replace(",", " ")


def intervalle(bas, haut, decimales=1, facteur=1):
    """Intervalle de confiance au format français : [−9,6 ; −4,0]."""
    return f"[{nombre(facteur * bas, decimales)} ; {nombre(facteur * haut, decimales)}]"


# ===========================================================================
# Barre latérale
# ===========================================================================

def barre_laterale():
    """Navigation, semaine L et seuil, partagés entre les pages. Sortie : (page, semaine, seuil)."""
    st.sidebar.title("Horizon")
    st.sidebar.caption("Décrochage et tutorat — cohorte 2025")
    page = st.sidebar.radio("Page", PAGES, key="page")
    semaine = st.sidebar.slider("Semaine L (photo de la promotion)", config.SEMAINE_MIN_TABLEAU,
                                config.SEMAINE_MAX_TABLEAU, config.SEMAINE_DEFAUT_TABLEAU, key="semaine",
                                help="On regarde les étudiants encore inscrits après cette semaine.")
    seuil = st.sidebar.slider("Seuil de risque (%)", config.SEUIL_MIN_TABLEAU_PCT, config.SEUIL_MAX_TABLEAU_PCT,
                              config.SEUIL_DEFAUT_TABLEAU_PCT, key="seuil",
                              help="Un étudiant est signalé si son risque Cox atteint ce seuil.")
    st.sidebar.divider()
    st.sidebar.caption("Données synthétiques ; identifiants pseudonymisés.")
    return page, semaine, seuil


# ===========================================================================
# Page 1 — Étudiants à risque
# ===========================================================================

def table_affichee(table):
    """Table lisible : colonnes en français, nombres au format français."""
    colonnes = list(COLONNES_TABLE)
    return pd.DataFrame({
        colonnes[0]: table["id_etudiant"],
        colonnes[1]: table["risque_cox_pct"].map(pct),
        colonnes[2]: table["risque_semaine_suivante_pct"].map(lambda v: pct(v, 2)),
        colonnes[3]: table["facteurs"].replace("", "—"),
        colonnes[4]: table["tutorat"],
        colonnes[5]: table["fiche"].replace("", "—"),
    })


def page_risque(semaine, seuil):
    """Chiffres clés, table des étudiants au-dessus du seuil, phrases d'explication."""
    st.title(PAGE_RISQUE)
    table = table_semaine(semaine)
    signales = table[table["risque_cox_pct"] >= seuil]
    colonnes = st.columns(3)
    colonnes[0].metric(f"Encore suivis après la semaine {semaine}", entier(len(table)))
    colonnes[1].metric(f"Risque d'au moins {seuil} %", entier(len(signales)))
    colonnes[2].metric("Risque Cox moyen", pct(table["risque_cox_pct"].mean()))
    tous = st.checkbox("Afficher toute la population suivie", key="toute_population")
    affichee = table if tous else signales
    if affichee.empty:
        st.info(f"Aucun étudiant n'atteint {seuil} % en semaine {semaine} : baisser le seuil.")
    else:
        st.dataframe(table_affichee(affichee), hide_index=True, width="stretch",
                     height=min(600, 38 + 35 * len(affichee)),
                     column_config={nom: st.column_config.TextColumn(nom, width=largeur, help=aide)
                                    for nom, (largeur, aide) in COLONNES_TABLE.items()})
        st.caption("Table triée par risque Cox décroissant.")
    st.markdown(
        f"- **Risque Cox** : probabilité estimée de décrocher d'ici la semaine 30 pour un étudiant encore inscrit "
        f"après la semaine {semaine}, d'après son profil de rentrée.\n"
        f"- **Risque de la semaine suivante** : signal à court terme du gradient boosting, tiré de l'activité "
        f"jusqu'à la semaine {semaine}.\n"
        "- **Facteurs** : caractéristiques de rentrée **associées** à un risque plus élevé (multiplicateur par "
        "rapport à un étudiant moyen de la promotion) ; ce ne sont pas des causes. Le genre et la région ne sont "
        "jamais affichés.\n"
        "- Le risque restant baisse au fil des semaines (il reste moins de semaines pour décrocher) : le seuil est "
        "à adapter à la semaine choisie.")


# ===========================================================================
# Page 2 — Fiche étudiant
# ===========================================================================

def choisir_etudiant(semaine, seuil):
    """Liste déroulante des étudiants signalés (toute la population si aucun) ; le plus à risque d'abord."""
    table = table_semaine(semaine)
    candidats = table[table["risque_cox_pct"] >= seuil]
    if candidats.empty:
        st.info(f"Aucun étudiant n'atteint {seuil} % : choix parmi toute la population suivie.")
        candidats = table
    risques = dict(zip(candidats["id_etudiant"], candidats["risque_cox_pct"]))
    identifiant = st.selectbox("Étudiant", list(risques), format_func=lambda i: f"{i} — risque {pct(risques[i])}",
                               key=f"etudiant_{semaine}_{seuil}")
    return table[table["id_etudiant"] == identifiant].iloc[0]


def texte_profil(profil):
    """Profil de rentrée lisible (ni genre ni région)."""
    lignes = {
        "Âge": "non renseigné" if pd.isna(profil["age"]) else f"{int(profil['age'])} ans",
        "Note du bac": "non renseignée" if pd.isna(profil["note_bac"]) else f"{nombre(profil['note_bac'])} / 20",
        "Distance domicile-campus": ("non renseignée" if pd.isna(profil["distance_campus_km"])
                                     else f"{nombre(profil['distance_campus_km'], 0)} km"),
        "Boursier": profil["boursier"] if isinstance(profil["boursier"], str) else "non renseigné",
        "Emploi en parallèle des études": (profil["emploi_parallele"] if isinstance(profil["emploi_parallele"], str)
                                           else "non renseigné"),
        "Filière": profil["filiere"] if isinstance(profil["filiere"], str) else "non renseignée",
    }
    return pd.DataFrame({"Caractéristique": list(lignes), "Valeur": list(lignes.values())})


def afficher_facteurs(facteurs):
    """Facteurs et multiplicateurs, expliqués par rapport à un étudiant moyen de la promotion."""
    if not facteurs:
        st.write("Aucun facteur de rentrée n'augmente nettement le risque (multiplicateur d'au moins 1,1).")
        return
    for facteur in facteurs:
        st.markdown(f"- **{facteur['facteur']}** : {facteur['valeur_etudiant']} "
                    f"({facteur['reference_promotion']}) — risque **×{nombre(facteur['multiplicateur'])}**")
    st.caption("Multiplicateur : le risque est multiplié par cette valeur par rapport à un étudiant moyen de la "
               "promotion, à autres caractéristiques égales. C'est une association, pas une cause.")


def afficher_activite(identifiant, semaine):
    """Activité moyenne des deux dernières semaines, étudiant contre promotion suivie."""
    semaines, etudiant, promotion = tb.activite_semaines(donnees(), identifiant, semaine)
    titre = f"semaine {semaines[0]}" if len(semaines) == 1 else f"semaines {semaines[0]} et {semaines[1]}"
    st.markdown(f"**Activité moyenne par semaine ({titre})**")
    st.dataframe(pd.DataFrame({
        "Indicateur": list(NOMS_ACTIVITE.values()),
        "Étudiant": ["non renseigné" if etudiant[c] is None or pd.isna(etudiant[c]) else nombre(etudiant[c])
                     for c in NOMS_ACTIVITE],
        "Promotion suivie": [nombre(promotion[c]) for c in NOMS_ACTIVITE],
    }), hide_index=True, width="stretch")
    st.caption("Observations récentes, décrites pour l'entretien : elles ne font pas partie du risque Cox, qui ne "
               "connaît que la rentrée.")


def figure_survie(identifiant, semaine):
    """Courbe de survie Cox de l'étudiant et courbe moyenne de la cohorte 2025."""
    courbe = tb.courbe_individuelle(donnees(), identifiant)
    figure, axe = plt.subplots(figsize=(6.5, 3.6))
    axe.plot(courbe["semaine"], courbe["survie_etudiant"], color=COULEUR_ETUDIANT, linewidth=2.2,
             label="cet étudiant")
    axe.plot(courbe["semaine"], courbe["survie_moyenne_cohorte"], color=COULEUR_REFERENCE, linewidth=1.8,
             linestyle="--", label="moyenne de la cohorte 2025")
    # La semaine L est dans la légende (une étiquette sur le graphique pourrait chevaucher une courbe).
    axe.axvline(semaine, color="grey", linestyle=":", linewidth=1.4, label=f"semaine {semaine} (photo)")
    axe.set_xlim(1, config.N_SEMAINES)
    axe.set_ylim(0, 1.02)
    axe.yaxis.set_major_formatter(lambda valeur, _: pct(100 * valeur, 0))
    axe.set_xlabel("Semaine depuis la rentrée")
    axe.set_ylabel("Probabilité d'être encore inscrit")
    axe.grid(alpha=0.3)
    axe.legend(loc="lower left")
    figure.tight_layout()
    return figure


def afficher_fiche_llm(identifiant, semaine):
    """Fiche LLM du cache à la semaine des fiches, avec l'avertissement ; bandeau si « à revoir »."""
    st.markdown("**Fiche d'entretien rédigée par le LLM**")
    if semaine != config.SEMAINE_FICHES:
        st.info(f"Les fiches sont rédigées pour la semaine {config.SEMAINE_FICHES} (D-66).")
        return
    fiche = tb.fiche_llm(donnees(), identifiant)
    if fiche is None:
        st.info(f"Pas de fiche : risque inférieur à {config.SEUIL_DEFAUT_TABLEAU_PCT} %.")
        return
    if fiche["statut"] == config.STATUT_FICHE_VALIDEE:
        st.badge("validée par les contrôles automatiques", icon=":material/check:", color="green")
    else:
        st.warning("**À revoir** : cette fiche n'a pas passé les contrôles automatiques. Motifs : "
                   + " ; ".join(fiche["motifs_rejet"]))
    st.markdown(f"**Situation.** {fiche['situation'] or '—'}")
    st.markdown("**Points d'attention.**\n" + "\n".join(f"- {point}" for point in fiche["points_attention"] or []))
    st.markdown("**Actions proposées.** " + ", ".join(fiche["actions"] or []))
    st.caption(f"⚠️ {fiche['avertissement']}")
    date = datetime.fromisoformat(fiche["date_generation"])
    st.caption(f"Modèle {fiche['modele']} · prompt {fiche['version_prompt']} · générée le "
               f"{date:%d/%m/%Y à %H h %M}")


def page_fiche(semaine, seuil):
    """Risques, profil, facteurs, activité, tutorat, courbe de survie et fiche LLM d'un étudiant."""
    st.title(PAGE_FICHE)
    ligne = choisir_etudiant(semaine, seuil)
    identifiant = ligne["id_etudiant"]
    colonnes = st.columns(3)
    colonnes[0].metric("Risque Cox (d'ici la semaine 30)", pct(ligne["risque_cox_pct"]))
    colonnes[1].metric(f"Risque la semaine {semaine + 1}", pct(ligne["risque_semaine_suivante_pct"], 2))
    colonnes[2].metric(f"Tutorat (semaine {semaine})", ligne["tutorat"])
    # À gauche, les données de l'étudiant ; à droite, la courbe et la fiche : tout tient sur un écran.
    gauche, droite = st.columns([5, 6], gap="large")
    with gauche:
        st.markdown("**Profil de rentrée**")
        st.dataframe(texte_profil(tb.profil(donnees(), identifiant)), hide_index=True, width="stretch")
        st.markdown("**Facteurs associés au risque**")
        afficher_facteurs(facteurs_semaine(semaine)[identifiant])
        afficher_activite(identifiant, semaine)
    with droite:
        st.markdown("**Courbe de survie estimée (modèle de Cox)**")
        figure = figure_survie(identifiant, semaine)
        st.pyplot(figure)
        plt.close(figure)
        st.caption("Lecture : semaine après semaine, la probabilité estimée que l'étudiant soit encore inscrit, "
                   "d'après son profil de rentrée ; en pointillés, la moyenne de la cohorte 2025.")
        afficher_fiche_llm(identifiant, semaine)


# ===========================================================================
# Page 3 — Effet du tutorat
# ===========================================================================

def figure_km_ponderees():
    """Courbes de Kaplan-Meier pondérées des deux équipes (photo de la semaine 8)."""
    courbes = donnees()["courbes_ponderees"]
    figure, axe = plt.subplots(figsize=(6.5, 3.6))
    axe.step(courbes["semaine"], courbes["survie_tutores"], where="post", color="#55A868", linewidth=2,
             label="tutorat commencé au plus tard en semaine 8")
    axe.step(courbes["semaine"], courbes["survie_non_tutores"], where="post", color="#8172B2", linewidth=2,
             label="pas de tutorat en semaine 8")
    axe.set_xlim(courbes["semaine"].min(), config.N_SEMAINES)
    # Graduations tous les 5 points : des pourcentages entiers, sans arrondi trompeur ; semaines entières.
    axe.yaxis.set_major_locator(MultipleLocator(0.05))
    axe.xaxis.set_major_locator(MultipleLocator(2))
    axe.yaxis.set_major_formatter(lambda valeur, _: pct(100 * valeur, 0))
    axe.set_xlabel("Semaine depuis la rentrée")
    axe.set_ylabel("Probabilité d'être encore inscrit")
    axe.grid(alpha=0.3)
    axe.legend(loc="lower left")
    figure.tight_layout()
    return figure


def table_variantes(variantes):
    """Table des variantes (CA-05) au format français."""
    return pd.DataFrame({
        "Variante": variantes["analyse"],
        "Étudiants": variantes["etudiants"].map(entier),
        "Tutorés": variantes["tutores"].map(entier),
        "Équilibre atteint (SMD < 0,1)": variantes["critere_atteint"].map(lambda v: "oui" if v else "non"),
        "Tirages": variantes["tirages"].map(entier),
        "Différence de risque (points) [IC 95 %]": [
            f"{nombre(100 * d)} {intervalle(b, h, facteur=100)}"
            for d, b, h in zip(variantes["difference_risque"], variantes["difference_risque_ic_bas"],
                               variantes["difference_risque_ic_haut"])],
        "HR [IC 95 %]": [f"{nombre(hr, 2)} {intervalle(b, h, 2)}"
                         for hr, b, h in zip(variantes["hr"], variantes["hr_ic_bas"], variantes["hr_ic_haut"])],
    })


def page_effet():
    """Effet estimé du tutorat (CA-04), variantes (CA-05) et hypothèses ; seule page qui parle d'« effet »."""
    st.title(PAGE_EFFET)
    resume = tb.resume_effet(donnees())
    m = resume["mesures"]
    principale = donnees()["sensibilite"].set_index("analyse").loc["analyse principale"]
    semaine, horizon = int(principale["semaine_photo"]), int(principale["horizon_rmst"])
    sans, avec = m["risque_non_tutores"][0], m["risque_tutores"][0]
    diff = m["difference_risque"]
    st.markdown(
        f"### Chez les étudiants encore inscrits en semaine {semaine}, commencer le tutorat au plus tard en semaine "
        f"{semaine} fait passer le risque de décrocher d'ici la semaine {config.N_SEMAINES} de **{pct(100 * sans)}** "
        f"à **{pct(100 * avec)}**, soit **{nombre(100 * diff[0])} points** (IC à 95 % de {nombre(100 * diff[1])} à "
        f"{nombre(100 * diff[2])}).")
    st.caption("Estimation par pondération sur le score de propension (photo de la semaine 8), intervalle par "
               f"bootstrap de {entier(principale['tirages'])} tirages (CA-04, D-57, D-61).")
    rr, rmst, hr = m["rapport_risques"], m["difference_rmst"], m["hr"]
    colonnes = st.columns(4)
    colonnes[0].metric("Rapport des risques", nombre(rr[0], 2), help=None)
    colonnes[0].caption(f"IC {intervalle(rr[1], rr[2], 2)}. Le risque des tutorés vaut environ "
                        f"{pct(100 * rr[0], 0)} de celui des non-tutorés.")
    colonnes[1].metric(f"Gain de RMST sur {horizon} semaines", f"+{nombre(rmst[0])} semaine")
    colonnes[1].caption(f"IC {intervalle(rmst[1], rmst[2])}. Sur les {horizon} semaines suivantes, un étudiant "
                        f"tutoré reste inscrit en moyenne {nombre(rmst[0])} semaine de plus.")
    colonnes[2].metric("Hazard ratio (HR)", nombre(hr[0], 2))
    colonnes[2].caption(f"IC {intervalle(hr[1], hr[2], 2)}. Chaque semaine, le risque de décrocher des tutorés est "
                        f"environ {nombre(hr[0], 2)} fois celui des non-tutorés (en moyenne sur la période).")
    colonnes[3].metric("E-value", nombre(m["e_value"][0], 2))
    colonnes[3].caption(f"Borne de l'IC : {nombre(m['e_value_borne_ic'][0], 2)}. Un facteur caché devrait être lié "
                        f"au tutorat et au décrochage par un rapport d'au moins {nombre(m['e_value'][0], 2)} pour "
                        "annuler l'estimation.")
    st.subheader("Courbes de survie pondérées des deux équipes")
    graphique, lecture = st.columns([3, 2], gap="large")
    with graphique:
        figure = figure_km_ponderees()
        st.pyplot(figure)
        plt.close(figure)
    with lecture:
        st.markdown(f"Kaplan-Meier **pondéré**, de la semaine {semaine} à la semaine {config.N_SEMAINES} : après "
                    f"pondération, les deux équipes se ressemblent sur le profil et l'activité jusqu'à la semaine "
                    f"{semaine}. L'écart entre les courbes est l'effet estimé du tutorat : à la semaine "
                    f"{config.N_SEMAINES}, la probabilité estimée de ne pas avoir décroché est de "
                    f"{pct(100 * (1 - avec))} avec le tutorat, contre {pct(100 * (1 - sans))} sans.")
    st.subheader("Sensibilité : la même analyse avec un seul choix modifié (CA-05)")
    st.dataframe(table_variantes(resume["variantes"]), hide_index=True, width="stretch")
    variantes = resume["variantes"]
    if resume["meme_sens"]:
        st.markdown("Toutes les variantes vont dans le même sens que l'analyse principale (différence de risque "
                    f"{'négative' if diff[0] < 0 else 'positive'}).")
    else:
        st.markdown("Les variantes ne vont **pas** toutes dans le même sens que l'analyse principale : le résultat "
                    "dépend des choix de l'analyse.")
    desequilibrees = variantes.loc[~variantes["critere_atteint"].astype(bool), "analyse"].tolist()
    if desequilibrees:
        st.markdown(f"Sans équilibre atteint (SMD > 0,1), à lire avec prudence : {', '.join(desequilibrees)}.")
    st.subheader("Hypothèses (à rappeler avec le résultat)")
    st.markdown(
        "Ce résultat est un effet **seulement si** ces conditions sont réunies (D-59) :\n"
        "1. **pas de facteur de confusion non mesuré important** : aucune variable absente des données "
        "(motivation, famille, santé…) ne pousse à la fois vers le tutorat et vers le décrochage au-delà de ce que "
        "le profil et l'activité captent (l'E-value dit quelle force il lui faudrait) ;\n"
        "2. **positivité** : chaque profil d'étudiant pouvait être tutoré ou non (support commun) ;\n"
        "3. **un score bien construit** : après pondération, les deux équipes se ressemblent sur les variables "
        "mesurées.\n\n"
        f"**Photo de la semaine {semaine}** : on compare les étudiants tutorés au plus tard en semaine {semaine} aux "
        f"autres ; les tutorats commencés plus tard comptent comme non tutorés, ce qui tire l'estimation vers "
        f"« aucun effet ». L'effet du tutorat pendant les semaines 1 à {semaine} n'est pas mesuré. Le HR varie au fil "
        f"des semaines : la conclusion repose sur le risque à {config.N_SEMAINES} semaines et le RMST.\n\n"
        "**Données synthétiques** : l'estimation sera comparée au vrai effet, connu de l'enseignant.")


# ===========================================================================
# Page 4 — À propos
# ===========================================================================

def page_a_propos():
    """Données, modèles et validation, fiches LLM, limites, commande de régénération."""
    st.title(PAGE_A_PROPOS)
    st.subheader("Données")
    st.markdown("Jeu **synthétique** de l'Institut Supérieur Horizon : 5 000 étudiants, cohortes 2024 et 2025, "
                "suivis 30 semaines depuis leur rentrée. Aucun étudiant réel ; identifiants pseudonymisés. Le "
                "tableau de bord montre la cohorte 2025.")
    st.subheader("Modèles et validation")
    st.markdown("Les modèles sont appris sur la cohorte **2024** et évalués sur la cohorte **2025**, jamais vue "
                "pendant l'apprentissage : modèle de **Cox** sur les variables de la rentrée (risque d'ici la "
                "semaine 30) et **gradient boosting** à temps discret (signal de la semaine suivante).")
    mesures = donnees()["mesures"]
    st.dataframe(pd.DataFrame({
        "Modèle": mesures["modele"],
        "C-index": mesures["c_index"].map(lambda v: nombre(v, 3)),
        "Brier intégré": mesures["brier_integre"].map(lambda v: nombre(v, 3)),
        "Écart de calibration à 20 semaines (points)": mesures["ecart_calibration"].map(
            lambda v: "—" if pd.isna(v) else nombre(100 * v)),
    }), hide_index=True, width="stretch")
    cox = mesures.set_index("modele").loc["Cox"]
    st.caption(f"C-index du Cox : {nombre(cox['c_index'], 2)} (0,5 = hasard, 1 = classement parfait) : le modèle "
               "classe mieux que le hasard, sans plus ; il sert à prioriser des entretiens, pas à prédire le sort "
               "d'un étudiant. Brier intégré : erreur moyenne des probabilités (plus bas = mieux), à comparer à la "
               "référence sans variable. Écart de calibration : écart moyen, en points de pourcentage, entre le "
               f"risque prédit et le risque observé à 20 semaines ({nombre(100 * cox['ecart_calibration'])} points "
               "pour le Cox).")
    st.subheader("Fiches d'entretien (LLM)")
    st.markdown(
        f"À la semaine {config.SEMAINE_FICHES}, pour chaque étudiant dont le risque atteint "
        f"{config.SEUIL_DEFAUT_TABLEAU_PCT} %, un LLM (Gemini) a rédigé une fiche courte, enregistrée dans le "
        "dépôt : le tableau de bord ne l'appelle jamais. Le LLM reçoit une liste fermée de champs, sans identifiant "
        "ni texte libre ; ces entrées restent des données **pseudonymisées** (D-65 à D-67). Les fiches affichées "
        f"sont celles du prompt {config.VERSION_PROMPT} (LL-02, D-69) ; celles de la version 1 sont gardées dans le "
        "dépôt pour la comparaison. Chaque fiche est contrôlée automatiquement (nombres présents dans l'entrée, mots "
        "interdits, actions d'une liste fermée) et porte un avertissement fixe :")
    st.caption(config.AVERTISSEMENT_FICHE)
    st.subheader("Limites principales")
    st.markdown(
        "- Les facteurs sont des **associations** issues d'un modèle prédictif, pas des causes.\n"
        "- Le C-index est modeste : beaucoup d'étudiants signalés ne décrochent pas, et l'inverse.\n"
        "- Le risque restant baisse au fil des semaines : un même seuil signale de moins en moins d'étudiants.\n"
        "- Les fiches sont rédigées pour la semaine 8 seulement et restent à vérifier par le conseiller.\n"
        "- Données synthétiques : les résultats ne valent pas pour une vraie promotion.")
    st.subheader("Tout régénérer")
    st.code("python run_all.py", language="bash")
    st.caption("Depuis la racine du dépôt : nettoyage, bases de survie, modèles, analyse causale et entrées des "
               "fiches (aucune clé d'API nécessaire). Le tableau de bord relit ensuite ces fichiers.")


# ===========================================================================
# Programme principal
# ===========================================================================

st.set_page_config(page_title="Horizon — décrochage et tutorat", layout="wide")
page_choisie, semaine_choisie, seuil_choisi = barre_laterale()
if page_choisie == PAGE_RISQUE:
    page_risque(semaine_choisie, seuil_choisi)
elif page_choisie == PAGE_FICHE:
    page_fiche(semaine_choisie, seuil_choisi)
elif page_choisie == PAGE_EFFET:
    page_effet()
else:
    page_a_propos()
