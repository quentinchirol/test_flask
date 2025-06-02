import base64
import requests
import pandas as pd
from io import BytesIO

GITHUB_TOKEN = "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"
GITHUB_USER = "quentinchirol"
REPO_NAME = "test_flask"
BRANCH = "main"
TARGET_FOLDER = "data"
EXCLUDE_FILE = "explication.txt"  # fichier à ne pas supprimer


def df_to_xlsx_base64(df: pd.DataFrame):
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    file_content = excel_buffer.getvalue()
    content_b64 = base64.b64encode(file_content).decode('utf-8')
    return content_b64

def push_file_to_github(df, filename):
    # Lire fichier binaire
    #with open(local_path, "rb") as f:
        #file_content = f.read()
    
    # Encoder base64
    content_b64 = df_to_xlsx_base64(df)

    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{TARGET_FOLDER}/{filename}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Vérifier si fichier existe (pour récupérer le sha)
    response = requests.get(url, headers=headers)
    data = {
        "message": f"Ajout automatique du fichier {filename}",
        "content": content_b64,
        "branch": BRANCH
    }
    if response.status_code == 200:
        data["sha"] = response.json()["sha"]

    # Envoyer le fichier
    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        return f"✅ Fichier {filename} pushé avec succès !"
    else:
        return f"❌ Erreur {put_response.status_code} : {put_response.text}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_files_in_folder():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{TARGET_FOLDER}?ref={BRANCH}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # liste des fichiers
    elif response.status_code == 404:
        print(f"Le dossier '{TARGET_FOLDER}' est vide ou n'existe pas.")
        return []
    else:
        print("Erreur listage fichiers:", response.status_code, response.text)
        return []

def delete_files_one_commit(files):
    # Filtrer pour exclure explication.txt
    files_to_delete = [f for f in files if f["name"] != EXCLUDE_FILE]
    if not files_to_delete:
        print(f"Aucun fichier à supprimer (tout sauf {EXCLUDE_FILE}).")
        return

    url_ref = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/git/ref/heads/{BRANCH}"
    ref_resp = requests.get(url_ref, headers=headers)
    if ref_resp.status_code != 200:
        print("Erreur récupération ref:", ref_resp.status_code, ref_resp.text)
        return
    commit_sha = ref_resp.json()['object']['sha']

    url_commit = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/git/commits/{commit_sha}"
    commit_resp = requests.get(url_commit, headers=headers)
    if commit_resp.status_code != 200:
        print("Erreur récupération commit:", commit_resp.status_code, commit_resp.text)
        return
    tree_sha = commit_resp.json()['tree']['sha']

    tree_entries = []
    for file in files_to_delete:
        tree_entries.append({
            "path": f"{TARGET_FOLDER}/{file['name']}",
            "mode": "100644",
            "type": "blob",
            "sha": None  # suppression du fichier
        })

    url_tree = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/git/trees"
    data = {
        "base_tree": tree_sha,
        "tree": tree_entries
    }

    tree_resp = requests.post(url_tree, headers=headers, json=data)
    if tree_resp.status_code != 201:
        print("Erreur création nouveau tree:", tree_resp.status_code, tree_resp.text)
        return
    new_tree_sha = tree_resp.json()['sha']

    url_commit_create = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/git/commits"
    commit_data = {
        "message": f"Suppression de tous les fichiers sauf {EXCLUDE_FILE} dans {TARGET_FOLDER}",
        "tree": new_tree_sha,
        "parents": [commit_sha]
    }
    new_commit_resp = requests.post(url_commit_create, headers=headers, json=commit_data)
    if new_commit_resp.status_code != 201:
        print("Erreur création commit:", new_commit_resp.status_code, new_commit_resp.text)
        return
    new_commit_sha = new_commit_resp.json()['sha']

    url_update_ref = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/git/refs/heads/{BRANCH}"
    ref_data = {
        "sha": new_commit_sha
    }
    update_resp = requests.patch(url_update_ref, headers=headers, json=ref_data)
    if update_resp.status_code != 200:
        print("Erreur mise à jour ref:", update_resp.status_code, update_resp.text)
    else:
        print(f"✅ Tous les fichiers sauf '{EXCLUDE_FILE}' ont été supprimés du dossier '{TARGET_FOLDER}'.")

def clear_folder():
    files = get_files_in_folder()
    if not files:
        print("Aucun fichier à supprimer.")
        return
    delete_files_one_commit(files)
