import requests
import time

url = "https://prod-150.westeurope.logic.azure.com:443/workflows/bafe2ef2e106467495ddf7111038f943/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=bM_w59Ql0BEIoUZy93D_iHElnSBKcCvk5VLphK1YUZ8"  # L'URL HTTP générée par Power Automate
data = {
    "fichier": "principal_BD_Quest.xlsx",
    "url": "https://raw.githubusercontent.com/quentinchirol/test_flask/main/data/principal_BD_Quest.xlsx"
}

def check_status():
    while True:
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("Succès : traitement terminé.")
            print("Réponse :", response.json())
            break  # Sort de la boucle, c’est fini

        elif response.status_code == 202:
            print("Requête acceptée, traitement en cours (202). Attente avant nouvelle vérification...")
            time.sleep(5)  # Attendre 5 secondes avant de refaire la requête

        else:
            print(f"Erreur ❌ : {response.status_code} - {response.text}")
            break  # Sort de la boucle en cas d’erreur

check_status()
