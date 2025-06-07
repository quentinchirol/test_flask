# -*- coding: utf-8 -*-
"""
Script complet : nettoyage, extraction JSON, création de tables longues,
et suppression des colonnes contenant des dictionnaires JSON.
"""

import pandas as pd
import json
from datetime import datetime
import unicodedata

# --- Paramètres ---
fichier_source = "MAVIE_BD_SD_mai_2025.xlsx"
col_id = "VOLONTAIRE N°"
feuilles = ["BD_Quest", "Accident"]

# --- Colonnes avec dictionnaires JSON ---
colonnes_avec_dicts = {
    "BD_Quest": {
        "Quelles sont les activités sportives que vous pratiquez ?": ["Type d'activité"]
    },
    "Accident": {
        "De quel type d'accident s'agissait-il ?": ["Type d'accident", "Type précis"],
        "Quelle(s) blessure(s) l'accident a-t-il provoqué ?": ["Blessure", "Localisation"]
    }
}

# --- Fonctions ---
def extraire_cles(cellule, cles_a_extraire):
    try:
        liste_dict = json.loads(cellule) if isinstance(cellule, str) else []
        if not isinstance(liste_dict, list):
            liste_dict = [liste_dict]
        données = {clé: [] for clé in cles_a_extraire}
        for d in liste_dict:
            if isinstance(d, dict):
                for clé in cles_a_extraire:
                    if clé in d:
                        données[clé].append(d[clé])
        return {clé: "; ".join(map(str, données[clé])) if données[clé] else None for clé in cles_a_extraire}
    except:
        return {clé: None for clé in cles_a_extraire}

def transformer_colonne_multiple(df: pd.DataFrame, id_col: str, target_col: str) -> pd.DataFrame:
    df_transforme = df[[id_col, target_col]].dropna()
    df_transforme[target_col] = df_transforme[target_col].astype(str).str.split(r";\s*")
    df_transforme = df_transforme.explode(target_col)
    df_transforme[target_col] = df_transforme[target_col].str.strip()
    return df_transforme

def nettoyer_bd_quest(df):
    df = df[df["VOLONTAIRE N°"].notna()].copy()
    annee_limite_sup = datetime.now().year - 14
    annee_limite_inf = datetime.now().year - 110
    df["ANNEE DE NAISSANCE"] = df["ANNEE DE NAISSANCE"].astype(str).str[-4:]
    df["ANNEE DE NAISSANCE"] = pd.to_numeric(df["ANNEE DE NAISSANCE"], errors="coerce")
    df.loc[
        (df["ANNEE DE NAISSANCE"].isna()) |
        (df["ANNEE DE NAISSANCE"] < annee_limite_inf) |
        (df["ANNEE DE NAISSANCE"] > annee_limite_sup),
        "ANNEE DE NAISSANCE"
    ] = pd.NA
    age_calcule = datetime.now().year - pd.to_numeric(df["ANNEE DE NAISSANCE"], errors="coerce")
    index_colonne = df.columns.get_loc("ANNEE DE NAISSANCE")
    df.insert(loc=index_colonne + 1, column="ÂGE", value=age_calcule)

    df["AGE_ARRIVEE_FR"] = pd.to_numeric(df["À quel âge êtes-vous arrivé(e) en France ? "], errors="coerce")
    df.loc[df["AGE_ARRIVEE_FR"] > df["ÂGE"], "À quel âge êtes-vous arrivé(e) en France ? "] = pd.NA

    df["TAILLE_STR"] = df["Quelle est votre taille actuelle en cm ?"].astype(str).str.replace(",", ".")
    df["TAILLE_CM"] = pd.to_numeric(df["TAILLE_STR"], errors="coerce")
    df.loc[df["TAILLE_CM"] < 3, "TAILLE_CM"] *= 100
    masque_taille = (df["TAILLE_CM"] < 140) | (df["TAILLE_CM"] > 250)
    df.loc[masque_taille, "Quelle est votre taille actuelle en cm ?"] = pd.NA
    df.loc[~masque_taille, "Quelle est votre taille actuelle en cm ?"] = df.loc[~masque_taille, "TAILLE_CM"].round(1)

    df["POIDS_STR"] = df["Quel est votre poids actuel en kg ?"].astype(str).str.replace(",", ".")
    df["POIDS_KG"] = pd.to_numeric(df["POIDS_STR"], errors="coerce")
    masque_poids = (df["POIDS_KG"] < 30) | (df["POIDS_KG"] > 300)
    df.loc[masque_poids, "Quel est votre poids actuel en kg ?"] = pd.NA
    df.loc[~masque_poids, "Quel est votre poids actuel en kg ?"] = df.loc[~masque_poids, "POIDS_KG"].round(1)

    return df

def remove_accents_and_upper(text):
    if isinstance(text, str):
        # Supprimer les accents
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        # Mettre en majuscules
        return text.upper()
    return text

def transformer_chaine_dataframe(df):
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(remove_accents_and_upper)
    return df

# --- Script principal ---
def main(filepath):
    df_bdq = pd.read_excel(filepath, sheet_name="BD_Quest")
    df_bdq = nettoyer_bd_quest(df_bdq)

    for col, cles in colonnes_avec_dicts["BD_Quest"].items():
        if col in df_bdq.columns:
            extraits = df_bdq[col].apply(lambda x: extraire_cles(x, cles))
            extraits_df = pd.DataFrame(extraits.tolist())
            extraits_df.columns = [f"{col} - {clé}" for clé in extraits_df.columns]
            df_bdq = pd.concat([df_bdq, extraits_df], axis=1)
            df_bdq = df_bdq.drop(columns=[col])  # Suppression de la colonne JSON
            
    # Supprimer la colonne "Qui sont les personnes vivant avec vous dans votre foyer ?" si elle existe
    if "Qui sont les personnes vivant avec vous dans votre foyer ?" in df_bdq.columns:
        df_bdq.drop(columns=["Qui sont les personnes vivant avec vous dans votre foyer ?"], inplace=True)

    df_activite = transformer_colonne_multiple(
        df_bdq, col_id, "Quelles sont les activités sportives que vous pratiquez ? - Type d'activité"
    )

    df_acc = pd.read_excel(filepath, sheet_name="Accident")
    for col, cles in colonnes_avec_dicts["Accident"].items():
        if col in df_acc.columns:
            extraits = df_acc[col].apply(lambda x: extraire_cles(x, cles))
            extraits_df = pd.DataFrame(extraits.tolist())
            extraits_df.columns = [f"{col} - {clé}" for clé in extraits_df.columns]
            df_acc = pd.concat([df_acc, extraits_df], axis=1)
            df_acc = df_acc.drop(columns=[col])  # Suppression de la colonne JSON

    
    df_accident = transformer_colonne_multiple(
        df_acc, col_id, "De quel type d'accident s'agissait-il ? - Type d'accident"
    )

    df_blessure = transformer_colonne_multiple(
        df_acc, col_id, "Quelle(s) blessure(s) l'accident a-t-il provoqué ? - Blessure"
    )

    df_localisation = transformer_colonne_multiple(
        df_acc, col_id, "Quelle(s) blessure(s) l'accident a-t-il provoqué ? - Localisation"
    )
    # Supprimer toute colonne contenant encore des dictionnaires ou listes (résidus JSON)
    for df in [df_bdq, df_acc]:
        cols_json = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, (dict, list))).any()]
        df.drop(columns=cols_json, inplace=True)


    df_bdq = transformer_chaine_dataframe(df_bdq)
    df_acc = transformer_chaine_dataframe(df_acc)
    df_activite = transformer_chaine_dataframe(df_activite)
    df_accident = transformer_chaine_dataframe(df_accident)
    df_blessure = transformer_chaine_dataframe(df_blessure)
    df_localisation = transformer_chaine_dataframe(df_localisation)

    return {
        "df_bdq_nettoye": df_bdq,
        "df_accident_complet": df_acc,
        "table_activite": df_activite,
        "table_accident": df_accident,
        "table_blessure": df_blessure,
        "table_localisation": df_localisation
    }