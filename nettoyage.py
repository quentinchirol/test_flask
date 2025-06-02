import json
import pandas as pd
from datetime import datetime

def netoyage_sous_table(df):
    # Liste pour stocker tous les petits DataFrames
    dfs = []


    def est_json(valeur):
        try:
            json.loads(valeur)  # Essaie de parser la chaîne JSON
            return True
        except (ValueError, TypeError):
            return False


    for idx, row in df.iterrows():
        for i in range(len(row)):  
            if est_json(row.iloc[i]):
                if pd.isna(row.iloc[i]):
                    # Si la cellule est vide ou NaN, on l'ignore
                    continue
                try:
                    # Convertir la chaîne JSON en liste/dict Python
                    data = json.loads(row.iloc[i])
                    # Créer un DataFrame pour cette entrée
                    df_temp = pd.DataFrame(data)
                    df_temp["VOLONTAIRE N°"] = row.iloc[0]
                    # Ajouter le DataFrame temporaire à la liste
                    dfs.append(df_temp)
                except Exception as e:
                    print(f"Erreur avec la donnée : {e}")
            

    # Concaténer tous les DataFrames ensemble
    df_final = pd.concat(dfs, ignore_index=True)
    return df_final


def netoyage_principal(df):
    df = df[df["VOLONTAIRE N°"].notna()]
    ####################### -- Année cohérente -- #######################

    # Définir les limites d'âge
    annee_limite_sup = datetime.now().year - 14
    annee_limite_inf = datetime.now().year - 110

    # Extraire les 4 derniers caractères
    df["ANNEE DE NAISSANCE"] = df["ANNEE DE NAISSANCE"].astype(str).str[-4:]

    # Convertir en numérique, remplacer erreurs par NaN
    df["ANNEE DE NAISSANCE"] = pd.to_numeric(df["ANNEE DE NAISSANCE"], errors="coerce")

    # Remplacer les valeurs hors bornes ou NaN par "Pas de données"
    df.loc[
        (df["ANNEE DE NAISSANCE"].isna()) |
        (df["ANNEE DE NAISSANCE"] < annee_limite_inf) |
        (df["ANNEE DE NAISSANCE"] > annee_limite_sup),
        "ANNEE DE NAISSANCE"
    ] = pd.NA


    # 1. Calculer l’âge dans une variable temporaire
    annee_actuelle = datetime.now().year
    age_calcule = annee_actuelle - pd.to_numeric(df["ANNEE DE NAISSANCE"], errors="coerce")

    # 2. Trouver l'index de la colonne "ANNEE DE NAISSANCE"
    index_colonne = df.columns.get_loc("ANNEE DE NAISSANCE")

    # 3. Insérer la colonne "ÂGE" juste après
    df.insert(loc=index_colonne + 1, column="ÂGE", value=age_calcule)

    # print(df.columns)

    ####################### -- AGE -- #######################

    # 1. Convertir la colonne d'âge d'arrivée en France en numérique
    df["AGE_ARRIVEE_FR"] = pd.to_numeric(df["À quel âge êtes-vous arrivé(e) en France ? "], errors="coerce")

    # 2. Créer un masque des valeurs incohérentes
    masque_incoherent = df["AGE_ARRIVEE_FR"] > df["ÂGE"]

    # 3. Remplacer les valeurs incohérentes par "Pas de données"
    df.loc[masque_incoherent, "À quel âge êtes-vous arrivé(e) en France ? "] = pd.NA


    ####################### -- TAILLE -- #######################

    # 1. Remplacer les virgules par des points
    df["TAILLE_STR"] = df["Quelle est votre taille actuelle en cm ?"].astype(str).str.replace(",", ".")

    # 2. Convertir en float (après nettoyage)
    df["TAILLE_CM"] = pd.to_numeric(df["TAILLE_STR"], errors="coerce")

    # 3. Corriger les réponses en mètres (par ex. 1.78 → 178 cm)
    df.loc[df["TAILLE_CM"] < 3, "TAILLE_CM"] = df["TAILLE_CM"] * 100

    # 4. Appliquer le test de cohérence (entre 50 et 250 cm)
    masque_incoherent = (df["TAILLE_CM"] < 50) | (df["TAILLE_CM"] > 250)

    # 6. Remplacer les incohérences par "Pas de données"
    df.loc[masque_incoherent, "Quelle est votre taille actuelle en cm ?"] = pd.NA


    # 7. (Optionnel) Remettre la valeur corrigée sinon :
    df.loc[~masque_incoherent, "Quelle est votre taille actuelle en cm ?"] = df.loc[~masque_incoherent, "TAILLE_CM"].round(1)

    ####################### -- POIDS -- #######################

    # 1. Nettoyer : remplacer les virgules par des points
    df["POIDS_STR"] = df["Quel est votre poids actuel en kg ?"].astype(str).str.replace(",", ".")

    # 2. Convertir en float
    df.loc[:, "POIDS_KG"] = pd.to_numeric(df["POIDS_STR"], errors="coerce")

    # 3. Définir un masque d'incohérence (hors bornes)
    masque_incoherent_poids = (df["POIDS_KG"] < 30) | (df["POIDS_KG"] > 300)

    # 5. Remplacer les valeurs incohérentes par "Pas de données"
    df.loc[masque_incoherent_poids, "Quel est votre poids actuel en kg ?"] = pd.NA


    # 6. Remettre les valeurs propres dans la colonne originale (arrondies)
    df.loc[~masque_incoherent_poids, "Quel est votre poids actuel en kg ?"] = df.loc[~masque_incoherent_poids, "POIDS_KG"].round(1)

    return df
