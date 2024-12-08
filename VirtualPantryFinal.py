from flask import Flask, request, jsonify
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from fuzzywuzzy import fuzz
import sqlite3
import os
import requests

# Flask app setup
app = Flask(__name__)

# Database path
db_path = os.path.join(os.getcwd(), "FoodData.db")

# GitHub URL to your FoodData.db
GITHUB_DB_URL = "https://raw.githubusercontent.com/username/repository/branch/path/to/FoodData.db"

# Download the database file if it doesn't exist locally
def download_database():
    if not os.path.exists(db_path):
        print("Downloading FoodData.db from GitHub...")
        try:
            response = requests.get(GITHUB_DB_URL)
            response.raise_for_status()  # Raise an error if the request fails
            with open(db_path, "wb") as db_file:
                db_file.write(response.content)
            print("Database downloaded successfully!")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download the database: {e}")
            exit(1)

# Call the download function
download_database()

# Database setup
def setup_database():
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        # Create the `Produce` table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Produce (
                Category TEXT,
                Name TEXT,
                Min_days INTEGER,
                Max_days INTEGER,
                Avg_days REAL,
                Tips TEXT
            );
        """)

        # Populate the table only if it's empty
        cur.execute("SELECT COUNT(*) FROM Produce;")
        if cur.fetchone()[0] == 0:
            data = [
                ('Fruit', 'Apples', 21, 21, 21, 'May extend life by one week in the refrigerator'),
                ('Fruit', 'Bananas', 3, 3, 3, 'Skin may blacken'),
                ('Vegetable', 'Potatoes', 30, 60, 45, 'Do not refrigerate'),
            ]
            cur.executemany("INSERT INTO Produce VALUES (?, ?, ?, ?, ?, ?);", data)
            con.commit()

        con.close()
    except sqlite3.Error as e:
        print(f"Database setup error: {e}")

setup_database()

# Preprocess image for better OCR results
def preprocess_image(filepath):
    img = Image.open(filepath)
    img = img.convert('L')  # Convert to grayscale
    img = img.filter(ImageFilter.MedianFilter())  # Denoise
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # Increase contrast
    img = img.resize((int(img.width * 1.5), int(img.height * 1.5)))  # Resize for better OCR
    img = img.point(lambda p: p > 128 and 255)  # Thresholding
    return img

# Endpoint to scan and process receipt image
@app.route('/scan-receipt', methods=['POST'])
def scan_receipt():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filepath = os.path.join(os.getcwd(), file.filename)
    file.save(filepath)

    try:
        img = preprocess_image(filepath)
        text = pytesseract.image_to_string(img)
        os.remove(filepath)  # Clean up the temporary file
        return extract_and_store_data(text)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Extract data from OCR and match with database
def extract_and_store_data(text):
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        food_pantry = []

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            # Fetch all rows from the database
            cur.execute("SELECT * FROM Produce")
            rows = cur.fetchall()

            # Match each row's name with the scanned text using fuzzy matching
            for row in rows:
                category, name, min_days, max_days, avg_days, tips = row
                if fuzz.partial_ratio(name.lower(), line.lower()) > 80:  # Adjust threshold
                    food_pantry.append({
                        "category": category,
                        "name": name,
                        "avg_days": avg_days,
                        "tips": tips
                    })
                    break

        con.close()
        return jsonify({'pantry': food_pantry})
    except sqlite3.Error as e:
        return jsonify({'error': f"Database error: {e}"}), 500

# Endpoint to fetch pantry data
@app.route('/api/pantry', methods=['GET'])
def get_pantry():
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT * FROM Produce")
        rows = cur.fetchall()
        con.close()

        pantry = [
            {"category": row[0], "name": row[1], "avg_days": row[4], "tips": row[5]}
            for row in rows
        ]
        return jsonify({'pantry': pantry})
    except sqlite3.Error as e:
        return jsonify({'error': f"Database error: {e}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
