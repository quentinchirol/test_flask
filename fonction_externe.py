from scipy.stats import chi2_contingency  # Pour effectuer le test du chi²
import pandas as pd  # Pour manipuler les fichiers Excel et les tableaux de données
import numpy as np  # Pour les calculs mathématiques
import pandas as pd
import numpy as np
from scipy.stats import norm

def chi2_test(df, var1, var2):
    # Cette fonction prend deux colonnes de ton DataFrame (questionnaires),
    # et applique un test du chi² + V de Cramér pour mesurer la force de l'association.

    data = df[[var1, var2]].dropna()  # On supprime les lignes avec des valeurs manquantes
    contingency = pd.crosstab(data[var1], data[var2])  # Table de contingence entre les deux variables

    # Calcul du test du chi² sur cette table
    chi2, p, dof, expected = chi2_contingency(contingency)

    # Calcul du V de Cramér
    n = contingency.sum().sum()  # Nombre total d'observations
    min_dim = min(contingency.shape) - 1  # La plus petite dimension - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else np.nan  # V de Cramér

    return contingency.to_html(), chi2, p, dof, cramers_v



# 3. Proportions de référence (INSEE ou conventions)
ref_age = {
    "15-24": 0.12,
    "25-34": 0.16,
    "35-44": 0.17,
    "45-54": 0.18,
    "55-64": 0.17,
    "65+": 0.20
}

ref_genre = {
    "FEMME": 0.514,
    "HOMME": 0.486
}

ref_diplome = {
    "Aucun": 0.16,
    "CAP/BEP": 0.21,
    "Bac": 0.20,
    "Bac+2": 0.21,
    "Licence ou plus": 0.22
}

# 4. Fonction de test de représentativité corrigée avec renommage des colonnes
def test_representativité(df, colonne, ref_props):
    df_clean = df[[colonne]].dropna()
    n = df_clean.shape[0]
    résultats = []

    for catégorie, p0 in ref_props.items():
        x = (df_clean[colonne] == catégorie).sum()
        p_obs = x / n
        se = np.sqrt(p0 * (1 - p0) / n)
        z = (p_obs - p0) / se if se > 0 else np.nan
        p_val = 2 * (1 - norm.cdf(abs(z))) if not np.isnan(z) else np.nan
        ic_min = p_obs - norm.ppf(0.975) * np.sqrt(p_obs * (1 - p_obs) / n)
        ic_max = p_obs + norm.ppf(0.975) * np.sqrt(p_obs * (1 - p_obs) / n)
        représentatif = "OUI" if p_val > 0.05 else "NON"

        résultats.append({
            "Catégorie": catégorie,
            "Proportion attendue": round(p0 * 100, 2),   # en pourcentage
            "Proportion observée": round(p_obs * 100, 2), # en pourcentage
            "Intervalle 95%": f"[{round(ic_min * 100, 2)} ; {round(ic_max * 100, 2)}]",
            "p-value": round(p_val, 4),
            "Représentatif": représentatif
        })

    df_resultats = pd.DataFrame(résultats)
    df_resultats.rename(columns={
        "Proportion observée": "Échantillon (%)",
        "Proportion attendue": "Population (%)"
    }, inplace=True)
    return df_resultats

def interpretation_simple(resultats, variable):
    col_pct = "Échantillon (%)" if "Échantillon (%)" in resultats.columns else "Echantillon (%)"
    col_pop = "Population (%)"

    if all(res == "OUI" for res in resultats["Représentatif"]):
        if variable == "âge":
            détails = []
            for _, row in resultats.iterrows():
                détails.append(
                    f"{row['Catégorie']}: {row[col_pct]:.1f}% dans l’échantillon contre {row[col_pop]:.1f}% dans la population"
                )
            description = "; ".join(détails)
            return (
                "La répartition par âge dans l’échantillon est globalement conforme à celle de la population française. "
                f"Les écarts sont minimes entre les tranches d’âge : {description}. "
                "Cela garantit une bonne fiabilité des analyses liées à cette variable."
            )

        elif variable == "genre":
            try:
                femme = resultats[resultats["Catégorie"] == "FEMME"].iloc[0]
                homme = resultats[resultats["Catégorie"] == "HOMME"].iloc[0]
                return (
                    "La variable « genre » est bien équilibrée dans l’échantillon. "
                    f"On y compte {femme[col_pct]:.1f}% de femmes contre {femme[col_pop]:.1f}% dans la population, "
                    f"et {homme[col_pct]:.1f}% d’hommes contre {homme[col_pop]:.1f}%. "
                    "Cette proximité garantit une bonne représentativité sur ce critère."
                )
            except:
                return (
                    "La variable « genre » est bien répartie dans l’échantillon, avec une répartition très proche de celle "
                    "de la population française. Cette concordance garantit une représentativité satisfaisante sur ce critère."
                )

        elif variable == "diplôme":
            détails = []
            for _, row in resultats.iterrows():
                détails.append(
                    f"{row['Catégorie']}: {row[col_pct]:.1f}% (échantillon) vs {row[col_pop]:.1f}% (population)"
                )
            description = "; ".join(détails)
            return (
                "Le niveau d’études des répondants correspond globalement à celui de la population française. "
                f"{description}. Aucun groupe n’est significativement sur- ou sous-représenté, "
                "ce qui permet une lecture fiable des résultats selon le niveau de formation."
            )

    else:
        if variable == "âge":
            lignes = []
            for _, row in resultats.iterrows():
                if row["Représentatif"] == "NON":
                    lignes.append(
                        f"{row['Catégorie']}: {row[col_pct]:.1f}% (échantillon) vs {row[col_pop]:.1f}% (population)"
                    )
            erreurs = "; ".join(lignes[:3])
            return (
                "La répartition des âges dans l’échantillon diffère de celle de la population française. "
                f"Certaines tranches d’âge sont mal représentées, notamment : {erreurs}. "
                "Cela peut introduire un biais si ces catégories sont particulièrement impliquées dans le phénomène étudié."
            )

        elif variable == "genre":
            try:
                femme = resultats[resultats["Catégorie"] == "FEMME"].iloc[0]
                homme = resultats[resultats["Catégorie"] == "HOMME"].iloc[0]
                return (
                    "La variable « genre » présente un déséquilibre dans l’échantillon. "
                    f"On y trouve {femme[col_pct]:.1f}% de femmes (contre {femme[col_pop]:.1f}%) et {homme[col_pct]:.1f}% d’hommes "
                    f"(contre {homme[col_pop]:.1f}%). Cette différence peut affecter les résultats selon les thèmes abordés."
                )
            except:
                return (
                    "La répartition hommes/femmes dans l’échantillon diffère de celle de la population française. "
                    "Ce déséquilibre peut influencer les résultats si le genre joue un rôle dans les réponses ou comportements observés."
                )

        elif variable == "diplôme":
            lignes = []
            for _, row in resultats.iterrows():
                if row["Représentatif"] == "NON":
                    lignes.append(
                        f"{row['Catégorie']}: {row[col_pct]:.1f}% (échantillon) vs {row[col_pop]:.1f}% (population)"
                    )
            erreurs = "; ".join(lignes[:3])
            return (
                "La structure des niveaux de diplôme dans l’échantillon s’écarte de celle de la population française. "
                f"Les plus grands écarts concernent : {erreurs}. "
                "Cela peut fausser l’interprétation des résultats si le niveau d’études influence fortement les opinions ou comportements étudiés."
            )

# --- Fonction de conversion des résultats pour HTML ---
def to_table_data(resultats):
    # Convertir DataFrame en liste de dicts (une dict par ligne)
    records = resultats.to_dict(orient='records')

    # Si la liste est vide (pas de résultats), gérer ce cas
    if not records:
        return [], []

    # Clés de la première ligne → en-têtes de colonnes
    headers = records[0].keys()

    # Liste des listes, chaque sous-liste = valeurs d'une ligne
    rows = [list(r.values()) for r in records]

    return headers, rows


def flask_return(filepath):

    df = pd.read_excel(filepath, sheet_name="Sheet1")
    

    def categoriser_age(age):
        if pd.isna(age):
            return None
        try:
            age = int(age)
            if age < 15:
                return "<15"
            elif 15 <= age <= 24:
                return "15-24"
            elif 25 <= age <= 34:
                return "25-34"
            elif 35 <= age <= 44:
                return "35-44"
            elif 45 <= age <= 54:
                return "45-54"
            elif 55 <= age <= 64:
                return "55-64"
            else:
                return "65+"
        except:
            return None

    df["Tranche_d_âge"] = df["ÂGE"].apply(categoriser_age)

    # --- Regroupement des diplômes ---
    def regrouper_diplome(val):
        if pd.isna(val):
            return None
        val = val.lower()
        if any(mot in val for mot in [
            "aucun diplôme", "certificat d'études primaires", "cfg", "brevet des collèges", "diplôme national du brevet"
        ]):
            return "Aucun diplôme"
        elif any(mot in val for mot in ["cap", "certificat d'aptitude", "bep", "études professionnelles"]):
            return "CAP/BEP"
        elif "baccalauréat" in val or "bac" in val:
            return "Bac"
        elif "bac +2" in val or "bac+2" in val or "+2" in val:
            return "Bac+2"
        elif "bac +3" in val or "bac+3" in val or "+3" in val or "+4" in val or "+5" in val:
            return "Bac+3 et plus"
        else:
            return None

    df["Diplôme_regroupé"] = df["Quel est le diplôme le plus élevé que vous avez obtenu ?"].apply(regrouper_diplome)

    r_age = test_representativité(df, "Tranche_d_âge", ref_age)
    r_genre = test_representativité(df, "GENRE", ref_genre)
    r_diplome = test_representativité(df, "Diplôme_regroupé", ref_diplome)

    return {
        "age": {
            "headers": to_table_data(r_age)[0],
            "rows": to_table_data(r_age)[1],
            "texte": interpretation_simple(r_age, "âge")
        },
        "genre": {
            "headers": to_table_data(r_genre)[0],
            "rows": to_table_data(r_genre)[1],
            "texte": interpretation_simple(r_genre, "genre")
        },
        "diplome": {
            "headers": to_table_data(r_diplome)[0],
            "rows": to_table_data(r_diplome)[1],
            "texte": interpretation_simple(r_diplome, "diplôme")
        }
    }
