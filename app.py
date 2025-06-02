from flask import Flask, request, render_template, redirect, url_for
from io import BytesIO
import pandas as pd
import nettoyage
import git
import os
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # dossier où stocker temporairement les fichiers

# Crée le dossier uploads s'il n'existe pas
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Vérifie si le fichier est dans la requête
        if 'file' not in request.files:
            return render_template('upload.html', error="Aucun fichier sélectionné")

        file = request.files['file']

        # Vérifie que le fichier a bien un nom
        if file.filename == '':
            return render_template('upload.html', error="Aucun fichier sélectionné")
        
        if not file.filename.endswith('.xlsx'):
            return render_template('upload.html', error="Seuls les fichiers EXCEL sont acceptés")

        # Sauvegarde temporaire
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Traitement avec pandas
        try:
            df1 = pd.read_excel(filepath, sheet_name="BD_Quest")
            df2 = pd.read_excel(filepath, sheet_name="Accident")

            principal_BD_Quest = nettoyage.netoyage_principal(df1)
            sous_table_BD_Quest = nettoyage.netoyage_sous_table(df1)

            principal_BD_Quest = principal_BD_Quest.drop('Quelles sont les activités sportives que vous pratiquez ?', axis=1)
            principal_BD_Quest = principal_BD_Quest.drop('Quels sont les accidents que vous avez eu ?', axis=1)

            fusion_BD_Quest = pd.merge(principal_BD_Quest, sous_table_BD_Quest, on='VOLONTAIRE N°', how='inner')

            principal_Accident = df2
            sous_table_Accident = nettoyage.netoyage_sous_table(df2)

            principal_Accident = principal_Accident.drop("De quel type d'accident s'agissait-il ?", axis=1)
            principal_Accident = principal_Accident.drop("Quelle(s) blessure(s) l'accident a-t-il provoqué ?", axis=1)
        
            fusion_Accident = pd.merge(principal_Accident, sous_table_Accident, on='VOLONTAIRE N°', how='inner')


            git.clear_folder()
            git.push_file_to_github(fusion_BD_Quest, "MAVIE_BD_Quest_clean.xlsx")
            git.push_file_to_github(fusion_Accident, "MAVIE_BD_Accident_clean.xlsx")

            see = principal_BD_Quest
            if len(principal_BD_Quest) > 1000:
                see = principal_BD_Quest.head(1000)

            # Convertir en HTML
            table_html = see[['VOLONTAIRE N°'] + [col for col in see.columns if col != 'VOLONTAIRE N°']].to_html(
                classes='table table-striped table-bordered',
                table_id='myTable',
                index=False,
                border=0
            )

        except Exception as e:
            print(f"Erreur détectée : {e}")  # Affiche dans la console serveur
            return render_template('upload.html', error=f"Erreur lors de la lecture du fichier: {str(e)}")
        finally:
            # Supprimer le fichier temporaire
            if os.path.exists(filepath):
                os.remove(filepath)

        return render_template('upload.html', table_html=table_html)

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
