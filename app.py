from flask import Flask, request, jsonify, render_template,send_file
import sqlite3
import os

import io
import google.generativeai as genai
from flask_cors import CORS
from dotenv import load_dotenv


load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("Please set your GEMINI_API_KEY in the environment variables.")

print("GEMINI_API_KEY loaded successfully")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')


app = Flask(__name__)
CORS(app)


DB_FILE = 'water_samples.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sample (
        sample_id INTEGER PRIMARY KEY,
        latitude TEXT,
        longitude TEXT,
        date_collected DATE,
        date_tested DATE,
        image BLOB  DEFAULT  NULL
    )
''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Nile_red (
            test_id INTEGER PRIMARY KEY,
            sample_id INTEGER,
            microplastic_concentration REAL,
            POLYMER_TYPE TEXT,
            active_status TEXT,
            FOREIGN KEY (sample_id) REFERENCES Sample (sample_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Rhodamine_B (
            test_id INTEGER PRIMARY KEY,
            sample_id INTEGER,
            concentration REAL,
            active_status REAL,
            FOREIGN KEY (sample_id) REFERENCES Sample (sample_id)
        )
    ''')


    sample_data = [
        (1, '19.8375 N', '83.9730 E', '2025-09-01', '2025-09-03', None),
        (2, '19.8380 N', '83.9740 E', '2025-09-03', '2025-09-05', None),
        (3, '19.8360 N', '83.9725 E', '2025-09-01', '2025-09-04', None),
        (4, '19.8355 N', '83.9750 E', '2025-09-05', '2025-09-07', None),
        (5, '19.8378 N', '83.9710 E', '2025-09-02', '2025-09-03', None),
        (6, '19.8390 N', '83.9735 E', '2025-09-04', '2025-09-06', None),
        (7, '19.8345 N', '83.9745 E', '2025-09-03', '2025-09-05',  None),
        (8, '19.8365 N', '83.9755 E', '2025-09-06', '2025-09-08', None),
        (9, '19.8372 N', '83.9720 E', '2025-09-02', '2025-09-04', None),
        (10, '19.8358 N', '83.9715 E', '2025-09-01', '2025-09-03', None)
    ]
    nile_red_data = [
        (1, 1, 0.85, 'PE', 'Active'),
        (2, 2, 0.62, 'PP', 'Active'),
        (3, 3, 1.23, 'PET', 'Active'),
        (4, 4, 1.05, 'PS', 'Active'),
        (5, 5, 0.48, 'PVC', 'Active'),
        (6, 6, 0.77, 'PE', 'Active'),
        (7, 7, 1.12, 'PP', 'Active'),
        (8, 8, 0.91, 'PET', 'Active'),
        (9, 9, 0.69, 'PS', 'Active'),
        (10, 10, 1.34, 'PVC', 'Active')
    ]
    rhodamine_b_data = [
        (1, 1, 0.342, 0.05),
        (2, 2, 0.289, 0.05),
        (3, 3, 0.456, 0.05),
        (4, 4, 0.398, 0.05),
        (5, 5, 0.234, 0.05),
        (6, 6, 0.312, 0.05),
        (7, 7, 0.401, 0.05),
        (8, 8, 0.367, 0.05),
        (9, 9, 0.298, 0.05),
        (10, 10, 0.422, 0.05)
    ]

    cursor.executemany('INSERT OR REPLACE INTO Sample VALUES (?, ?, ?, ?, ?,?)', sample_data)
    cursor.executemany('INSERT OR REPLACE INTO Nile_red VALUES (?, ?, ?, ?, ?)', nile_red_data)
    cursor.executemany('INSERT OR REPLACE INTO Rhodamine_B VALUES (?, ?, ?, ?)', rhodamine_b_data)

    conn.commit()
    conn.close()
    print("Database initialized successfully with sample data")


@app.route('/api/upload_image/<int:sample_id>', methods=['POST'])
def upload_image(sample_id):
    if 'image' not in request.files:
        return jsonify({"error": "No image file uploaded"}), 400
    
    file = request.files['image']
    img_data = file.read()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE Sample SET image=? WHERE sample_id=?", (img_data, sample_id))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Image uploaded for sample {sample_id}"}), 200


@app.route('/analyze', methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return "No file part"

    file = request.files["image"]

    if file.filename == "":
        return "No selected file"

    if file:
        
        filepath = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(filepath)

        # Send to Gemini
        with open(filepath, "rb") as img_file:
            response = model.generate_content(["Describe this image:", img_file])

        return f"<h2>Gemini Response:</h2><p>{response.text}</p>"
    
@app.route('/api/sample_image/<int:sample_id>')
def get_sample_image(sample_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT image FROM Sample WHERE sample_id=?", (sample_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return send_file(io.BytesIO(row[0]), mimetype="image/jpeg")
    else:
        return jsonify({"error": "Image not found"}), 404


def query_database(sql):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return {"error": str(e)}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        context = """
        You are an AI assistant for PRISM (Plastic Recognition using Integrated Scattered Monitoring),
        a water sample testing system. You have access to three database tables: Sample, Nile_red, Rhodamine_B.
        Provide accurate answers based on the database and testing methodology.
        Dont use any data outside the database.
        dont use quotes in your answers. If you don't know the answer, just say you don't know. Do not make up an answer.
        dont use underscores in your answers.
        Here are the table schemas:
        Sample(sample_id, latitude, longitude, date_collected, date_tested)
        Nile_red(test_id, sample_id, microplastic_concentration, POLYMER_TYPE, active_status)
        Rhodamine_B(test_id, sample_id, concentration, active_status)
        Use the following format for your answers:
        [Your answer here]
        Only use the data from the database tables to answer questions about sample locations, dates, and microplastic concentrations.
        1. For questions about sample locations, provide latitude and longitude from the Sample table.
        2. For questions about microplastic concentrations, provide data from the Nile_red table.
        3. For questions about Rhodamine B concentrations, provide data from the Rhodamine_B table.
        4. For questions about sample collection or testing dates, provide data from the Sample table.
        5. If a question cannot be answered with the available data, respond with "I don't know".
        6. Always refer to the tables and columns as they are named, without adding or changing names.
        7. Do not reference any data outside of the provided database tables.
        8. Provide concise and accurate answers based solely on the database content.
        9. Avoid using any special characters or formatting in your answers.
        10. Ensure your responses are clear and directly address the user's question using only the data provided.
        11. Do not make assumptions or provide information that is not explicitly present in the database.
        12. If multiple entries are relevant, summarize the information without quoting entire rows.
        13. Always maintain the integrity of the data and do not alter any values when presenting information.
        14. If asked about the methodology, explain that PRISM uses Nile Red and Rhodamine B staining techniques to identify and quantify microplastics in water samples.
        15. Remember to keep your answers factual and based on the data available in the tables.
        16. Do not use any abbreviations or acronyms unless they are part of the database content.
        17. Always prioritize clarity and accuracy in your responses.
        18. If the user asks for a summary of findings, provide an overview based on the data without quoting entire rows.
        19. If the user asks about trends or patterns, analyze the data and provide insights based on the available information.
        20. If the user asks about specific sample IDs, provide detailed information from all relevant tables for those IDs.
        21. If the user asks about the testing process, explain that PRISM collects water samples, stains them with Nile Red and Rhodamine B, and then analyzes them under a microscope to identify and quantify microplastics.
        22. Always ensure that your responses are easy to understand and free from technical jargon unless necessary.
        23. If the user asks about the significance of the findings, explain the environmental impact of microplastics and the importance of monitoring their presence in water bodies.
        24. If the user asks about the limitations of the data, acknowledge any gaps or uncertainties in the dataset.
        25. If the user asks about future steps or recommendations, suggest further testing, data collection, or analysis based on the current findings.
        26. Always remain neutral and objective in your responses, avoiding any bias or subjective opinions.
        27. If the user asks about the source of the data, explain that it is collected through PRISM's water sampling and testing process.

        28. If the user asks about the accuracy of the data, explain that while every effort is made to ensure accuracy, there may be inherent limitations in the testing methods and data collection process.
        29. If the user asks about the frequency of testing, explain that it depends on various factors such as environmental conditions, regulatory requirements, and research objectives.
        30. If the user asks about the geographical scope of the data, explain that it is based on the locations where water samples were collected and tested using PRISM.
        INSTEAD OF SAYING "I DONT KNOW " , SAY "Sorry , unable to provide the details about it right now".When user appreciates you, respond with "Happy to help!".
        31. If the user asks about the types of microplastics detected, refer to the POLYMER_TYPE column in the Nile_red table for specific types identified in the samples.
        32. If the user inquires about the active status of tests, refer to the active_status columns in both the Nile_red and Rhodamine_B tables to provide current status information.
        33. If the user asks about the relationship between sample collection dates and microplastic concentrations, analyze the date_collected from the Sample table in relation to microplastic_concentration from the Nile_red table to provide insights.
        34. If the user asks about any correlations between geographical locations and microplastic concentrations, analyze the latitude and longitude from the Sample table in relation to microplastic_concentration from the Nile_red table to provide insights.
        35. If the user asks about the overall findings from the samples, provide a summary based on the data from all three tables without quoting entire rows.
        36. If the user asks about the testing methodology in detail, explain that PRISM employs a systematic approach involving sample collection, staining with Nile Red and Rhodamine B, microscopic analysis, and data recording to ensure accurate identification and quantification of microplastics in water samples.

        if the user only enters a digit , assume it as a sample id.
        provide these all the details in a structured manner.

        """

        
        if any(keyword in user_message.lower() for keyword in ['sample', 'data', 'results', 'test', 'location', 'concentration']):
            samples = query_database("SELECT * FROM Sample")
            nile_red = query_database("SELECT * FROM Nile_red")
            rhodamine_b = query_database("SELECT * FROM Rhodamine_B")
            db_context = f"Samples: {samples}\nNile Red Tests: {nile_red}\nRhodamine B Tests: {rhodamine_b}"
            full_prompt = f"{context}\n\n{db_context}\n\nUser question: {user_message}"
        else:
            full_prompt = f"{context}\n\nUser question: {user_message}"

        # Call Gemini AI safely
        try:
            response = model.generate_content(full_prompt)
            reply = response.text
        except Exception as e:
            print("Gemini API error:", str(e))
            reply = "Sorry, the AI server could not process your request."

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}", "error": True}), 500


def store_sample_image(sample_id, image_path):
    with open(image_path, "rb") as f:
        img_data = f.read()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE Sample SET image=? WHERE sample_id=?", (img_data, sample_id))
    conn.commit()
    conn.close()

# -------------------------
# Test Gemini API
# -------------------------
@app.route('/test_gemini')
def test_gemini():
    try:
        response = model.generate_content("Hello from PRISM test")
        return response.text
    except Exception as e:
        return f"Gemini API error: {str(e)}"

# -------------------------
# Run App
# -------------------------






if __name__ == '__main__':
    init_db()
    
    print("Starting PRISM Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
