import os
import pandas as pd
from flask import jsonify

def upload_dataset(file, upload_folder):
    """
    Gère l'upload d'un fichier dataset.
    :param file: Le fichier envoyé via la requête POST.
    :param upload_folder: Le répertoire où sauvegarder le fichier.
    :return: Une réponse JSON indiquant le succès ou l'échec de l'upload.
    """
    if not file:
        return jsonify({"error": "Aucun fichier fourni"}), 400

    if file.filename == "":
        return jsonify({"error": "Le fichier n'a pas de nom"}), 400

    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    try:
        # Charger le dataset en fonction du format
        if file_path.endswith('.csv'):
            dataset = pd.read_csv(file_path, encoding='utf-8')
        elif file_path.endswith(('.xls', '.xlsx')):
            dataset = pd.read_excel(file_path)
        else:
            return jsonify({"error": "Format de fichier non pris en charge"}), 400

        # Informations sur le dataset chargé
        dataset_info = {
            "rows": len(dataset),
            "columns": list(dataset.columns)
        }

        print(f"Dataset loaded: {len(dataset)} rows")
        return jsonify({
            "message": f"Fichier {file.filename} uploadé avec succès",
            "dataset_info": dataset_info
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erreur lors du chargement du fichier : {str(e)}"}), 500