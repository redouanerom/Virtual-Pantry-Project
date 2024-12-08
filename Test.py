from flask import Flask, request, jsonify
import sqlite3
import os
from fuzzywuzzy import fuzz
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# Flask app setup
app = Flask(__name__)

# Allow Cross-Origin Resource Sharing
from flask_cors import CORS
CORS(app)

# Database path
db_path = os.path.join(os.getcwd(), "FoodData.db")

# Preprocess the image for OCR
def preprocess_image(filepath):
    img = Image.open(filepath)
    img = img.convert('L')  # Convert to grayscale
    img = img.filter(ImageFilter.MedianFilter())  # Denoise
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # Increase contrast
    img = img.resize((int(img.width * 1.5), int(img.height * 1.5)))  # Resize for better OCR
    img = img.point(lambda p: p > 128 and 255)  # Thresholding
    return img

# Extract text from an image
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

# Extract data from scanned text and match it with the database
def extract_and_store_data(text):
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        food_pantry = []

        for line in text.splitlines():
            line = line.strip()  # Remove leading/trailing spaces
            if not line:  # Skip empty lines
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
                    break  # Stop looking for matches for this line

        con.close()
        return jsonify({'pantry': food_pantry})
    except sqlite3.Error as e:
        return jsonify({'error': f"Database error: {e}"}), 500

# Fetch all produce data
@app.route('/get-produce', methods=['GET'])
def get_produce():
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT * FROM Produce")
        rows = cur.fetchall()
        con.close()
        produce_list = [
            {"category": row[0], "name": row[1], "min_days": row[2], "max_days": row[3], "avg_days": row[4], "tips": row[5]}
            for row in rows
        ]
        return jsonify({'produce': produce_list})
    except sqlite3.Error as e:
        return jsonify({'error': f"Database error: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
