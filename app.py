from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
import os
from groq import Groq
import seaborn as sns
import pandas as pd
import io
import contextlib
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import base64
from scipy import stats
import seaborn as sns
import plotly
import plotly.express as px
from upload_handler import upload_dataset 


app = Flask(__name__, template_folder="templates")
app.secret_key = 'hamza_session'
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)
llama_model = "llama-3.3-70b-specdec"
current_dataset = None

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/prompt", methods=["POST"])
def prompt():
    try:
        if "conversation" not in session:
            session["conversation"] = []
        data = request.json
        user_prompt = data.get("prompt")
        session["conversation"].append({"role": "user", "content": user_prompt})
        if not user_prompt:
            return jsonify({"error": "The 'prompt' field is required."}), 400
        if current_dataset is None:
            return jsonify({"error": "No dataset is loaded. Please upload a file."}), 400
        dataset_info = f"Columns: {', '.join(current_dataset.columns)}"
        system_control = """
        The response must be only minimal Python code without using ``` or plt.show() and use print when you want to display the result. 
        Use the loaded dataset named 'current_dataset' to perform the requested operations.
        No comments, introductions, summaries, or additional explanations are required.
        Avoid using plotly. Use matplotlib or seaborn for static plots. Do not include plt.show().
        Each line after a 'for' statement must be indented with 4 spaces. Example:

        for i in range(10):
            print(i)

        If the user's question isn't about code, provide a plain answer.
        """
        final_prompt = f"{system_control}\n\nAvailable data: {dataset_info}\n\n{user_prompt}"
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_control},  # Add system role
                {"role": "user", "content": user_prompt}
            ],
            model=llama_model,
            temperature=0.3,
        )
        response = chat_completion.choices[0].message.content.strip()
        session["conversation"].append({"role": "assistant", "content": response})
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/execute_code", methods=["POST"])
def execute_code():
    try:
        data = request.json
        code = data.get("code")
        if not code:
            return jsonify({"error": "No code to execute"}), 400
        local_vars = {"current_dataset": current_dataset}
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            exec(code, {}, local_vars)
            output = buf.getvalue()
        has_graph = len(plt.get_fignums()) > 0
        img_html = ""
        download_link = ""
        if has_graph:
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png")
            img_buffer.seek(0)
            plt.close()
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            img_html = f'<img src="data:image/png;base64,{img_base64}" alt="Generated Graph" class="w-full h-auto">'
            file_name = "graph.png"
            file_path = os.path.join("static", file_name)
            with open(file_path, "wb") as f:
                f.write(img_buffer.getvalue())
            download_link = f'<a href="/static/{file_name}" download="graph.png" style="color: blue; text-decoration: underline; font-weight: bold; font-size: 16px;">Download the graph</a>'
        result_html = f"""
        <div class="text-lg text-gray-700 mb-4">
            <pre class="bg-gray-100 p-3 rounded-lg overflow-x-auto">{output}</pre>
        </div>
        """
        if img_html:
            result_html += f"""
            <div>
                {img_html}
            </div>
            <div class="mt-4">
                {download_link}
            </div>
            """
        return jsonify({"result": result_html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download_dataset", methods=["GET"])
def download_dataset():
    try:
        global current_dataset
        if current_dataset is None:
            return jsonify({"error": "Aucun dataset chargé pour téléchargement."}), 400
        output = io.BytesIO()
        current_dataset.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return (
            output.getvalue(),
            200,
            {
                "Content-Disposition": "attachment; filename=modified_dataset.csv",
                "Content-Type": "text/csv",
            },
        )
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération du fichier : {str(e)}"}), 500

@app.route("/api/upload", methods=["POST"])
def upload():
    global current_dataset
    file = request.files.get("datasetFile")
    response, status_code = upload_dataset(file, app.config["UPLOAD_FOLDER"])
    if status_code == 200:
        # Mettre à jour le dataset global
        current_dataset = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"], file.filename)) if file.filename.endswith('.csv') else pd.read_excel(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
    return response, status_code

import psycopg2

postgres_pass = os.getenv("postgres_pass")
DB_CONFIG = {
    "dbname": "plat_ai_user",
    "user": "postgres",
    "password": postgres_pass,
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_table_if_not_exists():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Erreur lors de la création de la table :", e)

create_table_if_not_exists()

@app.route('/save_message', methods=['POST'])
def save_message():
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"error": "Message vide"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (message) VALUES (%s)", (user_message,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Message enregistré"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY created_at ASC")
        rows = cursor.fetchall()
        conn.close()

        # Convertir les résultats en une liste de dictionnaires
        messages = [{"id": row[0], "message": row[1], "created_at": row[2], "sender": "user"} for row in rows]
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


    
if __name__ == "__main__":
    app.run(debug=True)