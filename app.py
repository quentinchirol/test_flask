# Import des modules nécessaires
from flask import Flask, request, session, render_template, redirect, url_for, flash # Pour creer une instance webserveur 
import pandas as pd  # Pour manipuler les fichiers Excel et les tableaux de données
import nettoyage  # Module personnalisé pour nettoyer les données (à toi)
import power_automate  # Module personnalisé pour envoyer des fichiers (à toi)
from werkzeug.utils import secure_filename  # Pour sécuriser le nom du fichier uploadé
import os  # Pour gérer les fichiers et les dossiers
import time  # Pour faire des pauses (utile pour enchaîner les traitements)
import fonction_externe

# Création de l'application Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Dossier où les fichiers sont temporairement stockés
app.secret_key = "6a4f7e3d2c1b9a8f"  # Clé secrète pour sécuriser les sessions utilisateur

# Création du dossier 'uploads' s'il n'existe pas déjà
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --------------------- ROUTES POUR LES PAGES HTML ---------------------

@app.route("/")
def index():
    # Page d'accueil
    return render_template("index.html")

@app.route('/upload')
def upload():
    # Page d'import de fichiers
    return render_template('upload.html')  

@app.route('/tab_bord')
def tab_bord():
    # Tableau de bord (page personnalisée à développer)
    return render_template('tab_bord.html')  

@app.route('/ki2')
def ki2():
    # Page du test du chi² (appelée en GET)
    return render_template('ki2.html')  

@app.route('/representativite')
def representativite():
    return render_template('représentativité.html', resultats=None)

# --------------------- PAGE KI2 EN POST ---------------------

@app.route('/ki2', methods=['GET', 'POST'])
def ki2_send():
    columns = []  # Liste des colonnes à afficher dans les menus déroulants
    result = None  # Résultat du test à afficher

    if request.method == 'POST':
        file = request.files.get('file')  # Fichier envoyé par l'utilisateur
        var1 = request.form.get('var1')  # Nom de la première variable
        var2 = request.form.get('var2')  # Nom de la seconde variable
        filepath = None  # Chemin du fichier

        # Si un fichier a été envoyé
        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)  # On enregistre le fichier dans 'uploads'
            session['filepath'] = filepath  # On sauvegarde le chemin dans la session
        elif 'filepath' in session:
            filepath = session['filepath']  # On réutilise un fichier déjà uploadé
        else:
            flash("Veuillez uploader un fichier Excel.")
            return render_template('ki2.html')

        try:
            # Lecture du fichier Excel (feuille BD_Quest)
            df = pd.read_excel(filepath, sheet_name="Sheet1")
            columns = df.columns.tolist()  # On récupère toutes les colonnes pour les menus déroulants

            # Si les deux variables ont été choisies
            if var1 and var2:
                table, chi2, p, dof, v = fonction_externe.chi2_test(df, var1, var2)
                result = {
                    'var1': var1,
                    'var2': var2,
                    'table': table,
                    'chi2': round(chi2, 4),
                    'p': round(p, 4),
                    'dof': dof,
                    'v': round(v, 4)
                }

        except Exception as e:
            # Gestion des erreurs (ex : mauvaise feuille, fichier vide...)
            flash(f"Erreur : {e}")
            columns = []
            result = None

    # On affiche la page avec les résultats s'il y en a
    return render_template('ki2.html', columns=columns, result=result)

# --------------------- BOUTON DE RÉINITIALISATION ---------------------

@app.route('/ki2_reset')
def ki2_reset():
    # Cette route supprime le fichier uploadé et réinitialise la page
    filepath = session.pop('filepath', None)  # On supprime le chemin du fichier de la session
    if filepath and os.path.exists(filepath):
        os.remove(filepath)  # Suppression physique du fichier
    flash("Fichier supprimé. Vous pouvez en charger un nouveau.")
    return redirect(url_for('ki2'))

# ---------------------  ---------------------

@app.route('/send_representativité', methods=['POST'])
def send_representativité():
    if 'file' not in request.files:
        flash("Aucun fichier sélectionné")
        return redirect(url_for("representativite"))

    file = request.files['file']
    if file.filename == '':
        flash("Aucun fichier sélectionné")
        return redirect(url_for("representativite"))

    if not file.filename.endswith('.xlsx'):
        flash("Seuls les fichiers EXCEL sont acceptés")
        return redirect(url_for("representativite"))

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        resultats = fonction_externe.flask_return(filepath)
        # Vérification minimale
        if not isinstance(resultats, dict):
            flash("Le fichier est mal formaté ou la fonction a retourné un format incorrect.")
            return redirect(url_for("representativite"))

        # On pourrait aussi vérifier que certaines clés sont présentes, cf message précédent
    except Exception as e:
        import traceback
        flash(f"Erreur lors du traitement du fichier : {str(e)}")
        print(traceback.format_exc())  # Cela affichera la trace complète dans la console
        return redirect(url_for("representativite"))

    return render_template("représentativité.html", resultats=resultats)


# --------------------- ENVOI DU FICHIER POUR NETTOYAGE ---------------------

@app.route('/send', methods=['POST'])
def upload_file():
    # Cette route traite le fichier Excel, le nettoie avec le module 'nettoyage',
    # puis l'envoie avec Power Automate (automatisation via ton script).

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Aucun fichier sélectionné")
            return redirect(url_for("upload"))

        file = request.files['file']

        if file.filename == '':
            flash("Aucun fichier sélectionné")
            return redirect(url_for("upload"))
        
        if not file.filename.endswith('.xlsx'):
            flash("Seuls les fichiers EXCEL sont acceptés")
            return redirect(url_for("upload"))

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)  # Sauvegarde du fichier

        try:
            # Appel du module de nettoyage : retourne des DataFrames nettoyés
            table_clean = nettoyage.main(filepath)

            # On envoie chaque table nettoyée à Power Automate
            for nom_table, df in table_clean.items():
                print(f"Nom de la table : {nom_table}")
                power_automate.send_power_auto(nom_table + ".xlsx", df)
                time.sleep(1)  # Pause de 2 secondes entre les envois

        except Exception as e:
            flash(f"Erreur détectée : {str(e)}")
            return redirect(url_for("upload"))

        finally:
            # Nettoyage : on supprime le fichier uploadé
            if os.path.exists(filepath):
                os.remove(filepath)

        flash("Les données ont été Importer")
        return redirect(url_for("upload"))
    
    flash("")
    return redirect(url_for("upload"))

# --------------------- SUPPRESSION DES DONNÉES ---------------------

@app.route("/clear", methods=["POST"])
def import_files():
    # Cette route déclenche la suppression des données côté Power Automate
    power_automate.clear_file()
    flash("Les données ont été supprimées")
    return redirect(url_for("upload"))

# --------------------- LANCEMENT DU SERVEUR ---------------------

if __name__ == '__main__':
    app.run(debug=True)  # Démarrage de l'application en mode debug

