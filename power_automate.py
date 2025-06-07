import requests  # Pour faire des requêtes HTTP (POST ici)
import time      # Module time, pas utilisé dans ce code mais souvent utile pour pauses/timers
import base64    # Pour encoder/décoder en base64 (transfert de fichiers sous forme de texte)
import pandas as pd  # Manipulation de DataFrame
from io import BytesIO  # Buffer en mémoire pour manipuler fichiers binaires sans passer par disque

def df_to_xlsx_base64(df: pd.DataFrame):
    """
    Convertit un DataFrame pandas en un fichier Excel encodé en base64.
    - df : DataFrame à convertir
    Retourne la chaîne base64 représentant le fichier Excel.
    """
    # Création d'un buffer mémoire en mode binaire (comme un fichier en RAM)
    excel_buffer = BytesIO()
    
    # Avec un writer Excel pandas (xlsxwriter), on écrit le DataFrame dans le buffer
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)  # Ecriture du DataFrame dans Excel sans l'index
    
    # Récupération du contenu binaire complet du fichier Excel dans le buffer
    file_content = excel_buffer.getvalue()
    
    # Encodage du contenu binaire en base64 (format texte sûr pour transmission HTTP)
    content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # Retour de la chaîne base64
    return content_b64


def send_power_auto(nom, fichier):
    """
    Envoie un fichier Excel encodé en base64 à un service Power Automate via HTTP POST.
    - nom : nom associé au fichier (ex: nom du volontaire)
    - fichier : DataFrame pandas à envoyer (sera converti en Excel)
    Retourne la réponse HTTP du serveur.
    """
    # URL spécifique du flux Power Automate (endpoint pour recevoir la requête)
    url = "https://prod-78.westeurope.logic.azure.com:443/workflows/e97dce098c6349a3b0d88ccc7bb7dad4/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=4OaMnye9kF8P7hhTcturahWmdA-L6uJWScRwsIJ60fw"
    
    # Corps de la requête JSON contenant :
    # - "fichier" : le fichier Excel en base64
    # - "nom" : un nom texte
    data = {
        "fichier": df_to_xlsx_base64(fichier),
        "nom": nom
    }

    # Envoi de la requête POST avec les données JSON
    response = requests.post(url, json=data)
    
    # Retourne l'objet réponse (status code, contenu, etc.)
    return response


def clear_file():
    """
    Envoie une requête POST vide à un autre endpoint Power Automate
    pour vider ou réinitialiser un fichier/service (fonction selon contexte).
    Retourne la réponse HTTP.
    """
    # URL du flux Power Automate pour vider le fichier
    url = "https://prod-67.westeurope.logic.azure.com:443/workflows/51e3106f63884f02bb24cf16cdd07c89/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Aj73vxdS78LEuHjSXPD3Ra3ud9fVaI0E527JMuocWCE"
    
    # Données vides envoyées dans la requête POST
    data = {}
    
    # Envoi de la requête POST
    response = requests.post(url, json=data)
    
    # Retourne la réponse du serveur
    return response
