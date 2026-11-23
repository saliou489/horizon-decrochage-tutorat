"""Tests des fiches d'alerte par LLM, sans aucun accès réseau.

Rôle du module : tester src/llm.py (entrées, contrôles, génération avec une fausse
fonction d'appel, clé d'API, gabarit, grille d'évaluation) et quelques invariants sur
les entrées produites par run_all.py. Toutes les valeurs « personnelles » sont inventées.

Tâches couvertes : LL-01, LL-02.
"""

import copy
import json
import math

import numpy as np
import pandas as pd
import pytest

from src import config, llm


# ---------------------------------------------------------------------------
# Entrées : population, risques, contributions, facteurs
# ---------------------------------------------------------------------------

def test_risques_conditionnels_et_population_suivie():
    predictions = pd.DataFrame({"id_etudiant": ["A"] * 2 + ["B"] * 2, "semaine": [8, 30, 8, 30],
                                "survie_cox": [0.8, 0.4, 0.9, 0.9]})
    risques = llm.risques_conditionnels(predictions, ["B", "A"], 8)
    assert list(risques) == pytest.approx([0.0, 0.5])  # 1 − 0,4 / 0,8 = 0,5
    with pytest.raises(llm.ErreurLLM):
        llm.risques_conditionnels(predictions, ["A", "Z"], 8)
    base = pd.DataFrame({"id_etudiant": ["A", "B", "C", "D"], "cohorte": [2025, 2025, 2024, 2025],
                         "T": [9, 8, 20, 30]})
    assert list(llm.population_suivie(base, 8)["id_etudiant"]) == ["A", "D"]


def test_contributions_centrees_et_indicatrices_additionnees():
    table = pd.DataFrame({"id_etudiant": ["A", "B", "C"], "T": [1, 2, 3], "E": [1, 0, 1],
                          "age": [20.0, 22.0, 24.0], "note_bac": [10.0, 12.0, 14.0],
                          "filiere=Droit": [1, 0, 0], "filiere=Gestion": [0, 1, 0]})
    hr = pd.DataFrame({"variable": ["age", "note_bac", "filiere=Droit", "filiere=Gestion"],
                       "HR": [2.0, 0.5, 3.0, 1.5]})
    apports = llm.contributions(table, hr)
    assert list(apports.columns) == ["age", "note_bac", "filiere"]
    assert apports.loc[0, "age"] == pytest.approx(math.log(2.0) * (20 - 22))
    # Filière de A : log(3) × (1 − 1/3) + log(1,5) × (0 − 1/3).
    assert apports.loc[0, "filiere"] == pytest.approx(math.log(3) * (2 / 3) + math.log(1.5) * (-1 / 3))
    # Somme = prédicteur linéaire moins sa moyenne.
    betas = np.log([2.0, 0.5, 3.0, 1.5])
    lineaire = table[["age", "note_bac", "filiere=Droit", "filiere=Gestion"]].to_numpy() @ betas
    assert apports.sum(axis=1).to_numpy() == pytest.approx(lineaire - lineaire.mean())
    with pytest.raises(llm.ErreurLLM):
        llm.contributions(table.assign(genre_x=1), hr)


REFERENCES = {"age": "20,1 ans en moyenne dans la promotion", "note_bac": "12,8 / 20 en moyenne dans la promotion",
              "log2_distance": "11 km pour un étudiant typique de la promotion",
              "boursier": {"Oui": "43 % de la promotion dans ce cas", "Non": "57 % de la promotion dans ce cas"},
              "emploi_parallele": {"Oui": "18 % de la promotion dans ce cas", "Non": "82 % de la promotion dans ce cas"},
              "filiere": {"Droit": "20 % de la promotion dans ce cas"}}


def ligne_brute(**changements):
    ligne = {"age": 28, "note_bac": 10.62, "distance_campus_km": 131.2, "boursier": "Non",
             "emploi_parallele": "Oui", "filiere": "Droit", "genre": "M", "region_origine": "Kolda"}
    ligne.update(changements)
    return pd.Series(ligne)


def test_facteurs_principaux():
    apports = pd.Series({"age": math.log(2.1), "note_bac": math.log(1.04), "log2_distance": math.log(1.12),
                         "boursier": math.log(1.3), "emploi_parallele": math.log(1.6), "filiere": math.log(1.2),
                         "genre": math.log(5.0), "region_dakar": math.log(4.0)})
    facteurs = llm.facteurs_principaux(apports, ligne_brute(), REFERENCES)
    assert [f["facteur"] for f in facteurs] == ["âge", "emploi en parallèle des études", "bourse"]
    assert [f["multiplicateur"] for f in facteurs] == [2.1, 1.6, 1.3]
    assert facteurs[0]["valeur_etudiant"] == "28 ans" and facteurs[2]["valeur_etudiant"] == "non boursier"
    # Genre et région jamais affichés, même avec la plus forte contribution.
    libelles = {f["facteur"] for f in facteurs}
    assert not libelles & {"genre", "région"}
    # Multiplicateur 1,04 (arrondi 1,0) exclu ; 1,12 (arrondi 1,1) gardé ; valeur manquante exclue.
    seuls = apports[["note_bac", "log2_distance"]]
    gardes = llm.facteurs_principaux(seuls, ligne_brute(), REFERENCES)
    assert [(f["facteur"], f["multiplicateur"], f["valeur_etudiant"]) for f in gardes] == [
        ("distance domicile-campus", 1.1, "131 km")]
    sans_age = llm.facteurs_principaux(apports, ligne_brute(age=np.nan), REFERENCES)
    assert "âge" not in {f["facteur"] for f in sans_age} and len(sans_age) == config.NB_FACTEURS_FICHE


# ---------------------------------------------------------------------------
# Contrôle des entrées avant envoi (aucune donnée personnelle)
# ---------------------------------------------------------------------------

def entree_conforme(statut="aucun"):
    tutorat = {"statut": statut, "semaine_debut": 5} if statut == "en cours" else {"statut": statut}
    return {
        "semaine_observation": 8, "horizon_semaines": 30, "risque_decrochage_pct": 71, "risque_moyen_promotion_pct": 18,
        "facteurs": [{"facteur": "âge", "valeur_etudiant": "28 ans",
                      "reference_promotion": "20,1 ans en moyenne dans la promotion", "multiplicateur": 2.1}],
        "activite": {"semaines": [7, 8], "note_maximum": 20, "connexions_plateforme": 3.0, "devoirs_rendus": 0.5,
                     "seances_manquees": 4.5, "note_moyenne": None},
        "activite_promotion": {"connexions_plateforme": 6.1, "devoirs_rendus": 1.4, "seances_manquees": 2.5,
                               "note_moyenne": 10.4},
        "tutorat": tutorat,
    }


def test_entree_conforme_acceptee():
    llm.verifier_entree_sans_donnee_personnelle(entree_conforme())
    llm.verifier_entree_sans_donnee_personnelle(entree_conforme("en cours"))


@pytest.mark.parametrize("modifier", [
    lambda e: e.update(id_etudiant="HZ00001"),                                      # clé en trop
    lambda e: e["facteurs"][0].update(valeur_etudiant="HZ12345"),                    # identifiant
    lambda e: e["facteurs"][0].update(valeur_etudiant="prenom.testnom@exemple.sn"),  # e-mail
    lambda e: e["facteurs"][0].update(valeur_etudiant="77 000 00 00"),               # téléphone
    lambda e: e["facteurs"][0].update(reference_promotion="x" * 81),                  # texte trop long
    lambda e: e["facteurs"][0].update(facteur="genre"),                              # libellé hors liste
    lambda e: e["tutorat"].update(statut="inconnu"),                                 # statut hors liste
    lambda e: e["tutorat"].update(semaine_debut=3),                                  # « aucun » avec une semaine
])
def test_entree_non_conforme_refusee(modifier):
    entree = entree_conforme()
    modifier(entree)
    with pytest.raises(llm.ErreurLLM):
        llm.verifier_entree_sans_donnee_personnelle(entree)


# ---------------------------------------------------------------------------
# Contrôles automatiques des fiches
# ---------------------------------------------------------------------------

def reponse(situation="Le risque estimé est de 71 %, contre 18 % en moyenne. L'âge est associé à ce risque.",
            points=("L'étudiant a 28 ans, contre 20,1 ans en moyenne.", "Les connexions sont de 3 par semaine."),
            actions=("entretien individuel", "proposer un tutorat")):
    return json.dumps({"situation": situation, "points_attention": list(points), "actions": list(actions)},
                      ensure_ascii=False)


def test_nombres_et_fiche_conforme():
    assert llm.nombres_de({"a": "6,1 km", "b": [3.0, True, None]}) == {6.1, 3.0}
    fiche, motifs = llm.verifier_fiche(reponse(), entree_conforme())
    assert motifs == [] and fiche["actions"] == ["entretien individuel", "proposer un tutorat"]
    _, motifs = llm.verifier_fiche(reponse(points=("Les connexions sont de 6,1 par semaine dans la promotion.",
                                                   "3 connexions par semaine.")), entree_conforme())
    assert motifs == []
    _, motifs = llm.verifier_fiche(reponse(points=("Les devoirs sont de 3,5 par semaine.", "Âge : 28 ans.")),
                                   entree_conforme())
    assert any("3,5" in m for m in motifs)


@pytest.mark.parametrize("texte, statut", [
    ("pas du JSON", "aucun"),
    (json.dumps({"situation": "a", "points_attention": ["b", "c"], "actions": ["entretien individuel",
                                                                             "suivre l'assiduité"], "x": 1}), "aucun"),
    (reponse(actions=("entretien individuel",)), "aucun"),
    (reponse(actions=("entretien individuel", "appeler les parents")), "aucun"),
    (reponse(actions=("entretien individuel", "entretien individuel")), "aucun"),
    (reponse(actions=("entretien individuel", "faire le point sur le tutorat en cours")), "aucun"),
    (reponse(actions=("entretien individuel", "proposer un tutorat")), "en cours"),
])
def test_fiche_non_conforme_refusee(texte, statut):
    _, motifs = llm.verifier_fiche(texte, entree_conforme(statut))
    assert motifs


def test_mots_interdits_mots_entiers():
    assert "à cause" in llm.mots_interdits_presents("Le risque est élevé à cause de l'âge.")
    assert llm.mots_interdits_presents("Un entraînement régulier en filière Droit.") == []
    assert llm.mots_interdits_presents("Un risque 2,1 fois plus élevé.") == []
    assert llm.mots_interdits_presents("Il va décrocher.") == ["va décrocher"]


# ---------------------------------------------------------------------------
# Génération avec une fausse fonction d'appel (aucun réseau)
# ---------------------------------------------------------------------------

class FausseApi:
    """Fausse fonction d'appel : renvoie les réponses prévues, garde les messages reçus."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.messages = []

    def __call__(self, instructions, message):
        self.messages.append(instructions + message)
        suivante = self.reponses.pop(0)
        if isinstance(suivante, Exception):
            raise suivante
        return suivante


def entrees_inventees(n=1):
    return [{"id_etudiant": f"HZ{90000 + i}", "entree": entree_conforme()} for i in range(n)]


def test_generation_deuxieme_essai_valide_sans_identifiant_dans_le_message():
    api = FausseApi(["pas du JSON", reponse()])
    pauses = []
    fiches = llm.generer_fiches(entrees_inventees(), api, [], "modele-test", attendre=pauses.append)
    fiche = fiches[0]
    assert fiche["statut"] == config.STATUT_FICHE_VALIDEE and fiche["nb_essais"] == 2
    assert fiche["avertissement"] == config.AVERTISSEMENT_FICHE and fiche["id_etudiant"] == "HZ90000"
    assert pauses == [config.PAUSE_ENTRE_APPELS_LLM]
    assert all("HZ90000" not in message for message in api.messages)


def test_generation_toujours_non_conforme_a_revoir():
    api = FausseApi(["pas du JSON"] * config.NB_ESSAIS_FICHE)
    fiche = llm.generer_fiches(entrees_inventees(), api, [], "modele-test", attendre=lambda s: None)[0]
    assert fiche["statut"] == config.STATUT_FICHE_A_REVOIR and fiche["nb_essais"] == config.NB_ESSAIS_FICHE
    assert fiche["motifs_rejet"] == ["réponse non JSON"] and fiche["reponse_brute"] == "pas du JSON"
    assert fiche["situation"] is None


def test_generation_quota_puis_succes_et_quota_jamais_retabli():
    pauses = []
    api = FausseApi([llm.ErreurQuotaLLM("429"), reponse()])
    fiche = llm.generer_fiches(entrees_inventees(), api, [], "modele-test", attendre=pauses.append)[0]
    assert fiche["statut"] == config.STATUT_FICHE_VALIDEE and pauses == [config.ATTENTES_QUOTA_LLM[0]]
    enregistrees = []
    api = FausseApi([reponse()] + [llm.ErreurQuotaLLM("429")] * (len(config.ATTENTES_QUOTA_LLM) + 1))
    with pytest.raises(llm.ErreurQuotaLLM):
        llm.generer_fiches(entrees_inventees(2), api, [], "modele-test", attendre=lambda s: None,
                           enregistrer=lambda f: enregistrees.append(copy.deepcopy(f)))
    assert [f["id_etudiant"] for f in enregistrees[-1]] == ["HZ90000"]


def test_cache_reutilise_sauf_forcer_ou_autre_version(monkeypatch):
    api = FausseApi([reponse()])
    fiches = llm.generer_fiches(entrees_inventees(), api, [], "modele-test", attendre=lambda s: None)
    api_vide = FausseApi([])
    assert llm.generer_fiches(entrees_inventees(), api_vide, fiches, "modele-test") == fiches
    assert api_vide.messages == []
    api = FausseApi([reponse()])
    llm.generer_fiches(entrees_inventees(), api, fiches, "modele-test", forcer=True, attendre=lambda s: None)
    assert len(api.messages) == 1
    autre = [dict(f, version_prompt="v0") for f in fiches]
    api = FausseApi([reponse()])
    llm.generer_fiches(entrees_inventees(), api, autre, "modele-test", attendre=lambda s: None)
    assert len(api.messages) == 1


# ---------------------------------------------------------------------------
# Clé d'API, gabarit, grille d'évaluation
# ---------------------------------------------------------------------------

def test_lire_cle_api(tmp_path, monkeypatch):
    fichier = tmp_path / ".env"
    fichier.write_text("GEMINI_API_KEY=cle-inventee-pour-le-test\n", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_API_KEY", "autre-cle-de-la-machine")
    monkeypatch.setenv("GEMINI_API_KEY", "cle-de-l-environnement")
    assert llm.lire_cle_api(fichier) == "cle-inventee-pour-le-test"
    with pytest.raises(llm.ErreurLLM) as erreur:
        llm.lire_cle_api(tmp_path / "absent.env")
    assert "cle-" not in str(erreur.value)
    vide = tmp_path / "vide.env"
    vide.write_text("GEMINI_API_KEY=\n", encoding="utf-8")
    with pytest.raises(llm.ErreurLLM):
        llm.lire_cle_api(vide)


def test_gabarit_v1():
    instructions, message = llm.lire_gabarit("v1")
    assert instructions and message
    entree = entree_conforme()
    instructions, message = llm.construire_prompt(entree, "v1")
    for action in config.ACTIONS_FICHE:
        assert f"- {action}" in instructions
    assert json.dumps(entree, ensure_ascii=False, indent=2) in message
    assert "{actions}" not in instructions and "{entree}" not in message


def test_grille_evaluation(tmp_path):
    fiches = [{"id_etudiant": f"HZ{90000 + i}", "statut": config.STATUT_FICHE_VALIDEE, "motifs_rejet": []}
              for i in range(54)]
    chemin = llm.ecrire_grille_evaluation(fiches, tmp_path / "grille.csv")
    grille = pd.read_csv(chemin, sep=";", encoding="utf-8-sig")
    assert len(grille) == config.NB_FICHES_EVALUATION and grille["id_etudiant"].is_unique
    assert list(grille.columns) == ["id_etudiant", "statut_automatique", "motifs_rejet", "exactitude_humaine", "ton",
                                    "stigmatisation", "actions_pertinentes", "commentaire"]
    second = llm.ecrire_grille_evaluation(fiches, tmp_path / "autre.csv")
    assert pd.read_csv(second, sep=";", encoding="utf-8-sig")["id_etudiant"].tolist() == grille["id_etudiant"].tolist()
    with pytest.raises(llm.ErreurLLM):
        llm.ecrire_grille_evaluation(fiches, chemin)


# ---------------------------------------------------------------------------
# Invariants sur les entrées produites par run_all.py
# ---------------------------------------------------------------------------

def test_invariants_entrees_produites():
    if not config.FICHIER_ENTREES_LLM.exists():
        pytest.skip("entrées absentes : lancer python run_all.py")
    entrees = llm.lire_json(config.FICHIER_ENTREES_LLM)
    identifiants = [e["id_etudiant"] for e in entrees]
    assert len(entrees) == 54 and len(set(identifiants)) == len(identifiants)
    assert all(pd.Series(identifiants).str.fullmatch(config.FORMAT_ID_ETUDIANT))
    for element in entrees:
        entree = element["entree"]
        assert entree["risque_decrochage_pct"] >= round(100 * config.SEUIL_RISQUE_FICHE)
        assert element["id_etudiant"] not in json.dumps(entree, ensure_ascii=False)
        llm.verifier_entree_sans_donnee_personnelle(entree)
