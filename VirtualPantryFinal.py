from flask import Flask, render_template, request, redirect, url_for, session, flash
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from fuzzywuzzy import fuzz
import sqlite3
import os
import requests

# Flask application setup
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# GitHub URL to your FoodData.db
GITHUB_DB_URL = "https://raw.githubusercontent.com/username/repository/branch/path/to/FoodData.db"
db_path = os.path.join(os.getcwd(), "FoodData.db")

# Pantry array to store matched items
food_pantry = []

# Download the database file if it doesn't exist locally
def download_database():
    if not os.path.exists(db_path):
        print("Downloading FoodData.db from GitHub...")
        try:
            response = requests.get(GITHUB_DB_URL)
            response.raise_for_status()
            with open(db_path, "wb") as db_file:
                db_file.write(response.content)
            print("Database downloaded successfully!")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download the database: {e}")
            exit(1)

download_database()

# Database setup
def setup_database():
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
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
        con.commit()
        con.close()
    except sqlite3.Error as e:
        print(f"Database setup error: {e}")

setup_database()

from flask import jsonify

@app.route('/get_produce', methods=['GET'])
def get_produce():
    """Endpoint to fetch pantry items."""
    return jsonify({"produce": food_pantry})


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Authentication logic (example)
        if email == "test@example.com" and password == "password":
            session['logged_in'] = True
            return redirect(url_for('pantry'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/pantry')
def pantry():
    return render_template('pantry.html', items=food_pantry)

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        file = request.files.get('receipt')
        if file and file.filename != '':
            try:
                # Preprocess the image
                img = preprocess_image(file)

                # Extract text using OCR
                text = pytesseract.image_to_string(img)

                # Extract and store data in the pantry
                extract_and_store_data(text)

                # Provide user feedback
                flash('Items successfully scanned and added to your pantry!')
                return redirect(url_for('pantry'))
            except Exception as e:
                flash(f"Error processing receipt: {e}")
                return redirect(url_for('scan'))
        else:
            flash("No file selected. Please upload a receipt.")
            return redirect(url_for('scan'))
    return render_template('scan.html')

def preprocess_image(file):
    """Preprocess the uploaded image for better OCR results."""
    img = Image.open(file)
    img = img.convert('L')
    img = img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    img = img.resize((int(img.width * 1.5), int(img.height * 1.5)))
    img = img.point(lambda p: p > 128 and 255)
    return img

def extract_and_store_data(text):
    """Extract data from scanned text and match it with the database."""
    global food_pantry
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cur.execute("SELECT * FROM Produce")
            rows = cur.fetchall()
            for row in rows:
                category, name, min_days, max_days, avg_days, tips = row
                if fuzz.partial_ratio(name.lower(), line.lower()) > 80:
                    food_pantry.append({
                        "category": category,
                        "name": name,
                        "avg_days": avg_days,
                        "tips": tips
                    })
                    break
        con.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
