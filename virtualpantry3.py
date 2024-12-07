import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from fuzzywuzzy import fuzz
from tkinter import Tk, filedialog
import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

# SQLite database path
db_path = r"C:\Users\saz16\Virtual-Pantry\database\FoodData.db"

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
                ('Fruit', 'Strawberries', 2, 3, 2.5, 'Can be stored up to one year if frozen'),
                ('Fruit', 'Blueberries', 7, 14, 10.5, ''),
                ('Fruit', 'Grapes', 7, 7, 7, ''),
                ('Fruit', 'Strawberries', 2, 3, 2.5, 'Can be stored up to one year if frozen'),
                ('Fruit', 'Mango', 7, 7, 7, 'Can be safely frozen'),
                ('Fruit', 'Lemon', 10, 21, 15.5, 'Can be stored outside of fridge for max 10 days'),
                ('Fruit', 'Lime', 10, 21, 15.5, 'Can be stored outside of fridge for max 10 days'),
                ('Fruit', 'Avocado', 3, 4, 3.5, 'Applies to ripe fruit'),
                ('Fruit', 'Cherries', 2, 3, 2.5, ''),
                ('Vegetable', 'Potatoes', 30, 60, 45, 'Do not refrigerate'),
                ('Vegetable', 'Mushrooms', 3, 7, 3.5, ''),
                ('Vegetable', 'Pepper', 4, 14, 9, ''),
                ('Vegetable', 'Celery', 7, 14, 10.5, ''),
                ('Vegetable', 'Cauliflower', 3, 5, 4, ''),
                ('Vegetable', 'Broccoli', 3, 5, 4, ''),
                ('Vegetable', 'Asparagus', 3, 4, 3.5, ''),
                ('Vegetable', 'Corn', 1, 2, 1.5, ''),
                ('Vegetable', 'Cucumbers', 4, 6, 5, ''),
                ('Vegetable', 'Garlic', 3, 14, 8.5, 'Store unbroken bulbs in pantry, individual cloves in refrigerator'),
                ('Vegetable', 'Onion', 30, 30, 30, 'Can be stored in pantry for less time'),
                ('Vegetable', 'Cilantro', 14, 21, 17.5, ''),
                # Add more entries as needed
            ]
            cur.executemany("INSERT INTO Produce VALUES (?, ?, ?, ?, ?, ?);", data)
            con.commit()

        con.close()
    except sqlite3.Error as e:
        print(f"Database setup error: {e}")

setup_database()

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.food_pantry = []  # Store matched items with detailed info
        self.build_main_menu()

    def build_main_menu(self):
        """Builds the main menu UI."""
        self.clear_widgets()

        # Header
        self.header = Label(text="Virtual Pantry", font_size=24, size_hint_y=0.1)
        self.add_widget(self.header)

        # Menu Buttons
        view_button = Button(text="View Pantry", size_hint_y=0.1)
        view_button.bind(on_press=self.view_pantry)
        self.add_widget(view_button)

        scan_button = Button(text="Scan Receipt", size_hint_y=0.1)
        scan_button.bind(on_press=self.scan_receipt)
        self.add_widget(scan_button)

    def preprocess_image(self, filepath):
        """Preprocess the image for better OCR results."""
        img = Image.open(filepath)
        img = img.convert('L')  # Convert to grayscale
        img = img.filter(ImageFilter.MedianFilter())  # Denoise
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)  # Increase contrast
        img = img.resize((int(img.width * 1.5), int(img.height * 1.5)))  # Resize for better OCR
        img = img.point(lambda p: p > 128 and 255)  # Thresholding
        return img

    def scan_receipt(self, instance):
        """Use tkinter file dialog to select and scan a receipt image."""
        root = Tk()
        root.withdraw()  # Hide the tkinter root window
        filepath = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if filepath:
            try:
                img = self.preprocess_image(filepath)
                text = pytesseract.image_to_string(img)
                self.extract_and_store_data(text)
            except Exception as e:
                self.show_error(str(e))

    def extract_and_store_data(self, text):
        """Extract data from scanned text and match it with the database."""
        print("Extracted Text:")
        print(text)  # Debugging: Print raw text

        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()

            # Clear previous pantry data
            self.food_pantry = []

            for line in text.splitlines():
                line = line.strip()  # Remove leading/trailing spaces
                if not line:  # Skip empty lines
                    continue

                print(f"Processing line: {line}")  # Debugging

                # Fetch all rows from the database
                cur.execute("SELECT * FROM Produce")
                rows = cur.fetchall()

                # Match each row's name with the scanned text using fuzzy matching
                for row in rows:
                    category, name, min_days, max_days, avg_days, tips = row
                    if fuzz.partial_ratio(name.lower(), line.lower()) > 80:  # Adjust threshold
                        print(f"Matched: {line} -> {name}")
                        self.food_pantry.append({
                            "category": category,
                            "name": name,
                            "avg_days": avg_days,
                            "tips": tips
                        })
                        break  # Stop looking for matches for this line

            con.close()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.show_error(f"Error accessing database: {e}")

        self.view_pantry()

    def view_pantry(self, instance=None):
        """Display the pantry list."""
        self.clear_widgets()  # Clear previous UI
        self.add_widget(self.header)  # Re-add header

        scroll_view = ScrollView(size_hint=(1, 0.8))
        content = BoxLayout(orientation='vertical', size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        content.add_widget(Label(text="", size_hint_y=None, height=20))  # Spacer at the top

        if not self.food_pantry:
            content.add_widget(Label(text="No items in the pantry."))
        else:
            # Add each item in the pantry as its own block
            for item in self.food_pantry:
                item_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=10, spacing=10)
                item_layout.add_widget(Label(text=f"Category: {item['category']}", font_size=16, halign="left", valign="middle"))
                item_layout.add_widget(Label(text=f"Name: {item['name']}", font_size=16, halign="left", valign="middle"))
                item_layout.add_widget(Label(text=f"Average Shelf Life: {item['avg_days']} days", font_size=16, halign="left", valign="middle"))
                item_layout.add_widget(Label(text=f"Tips: {item['tips'] if item['tips'] else 'No tips available'}", font_size=16, halign="left", valign="middle"))
                item_layout.add_widget(Label(text="", size_hint_y=None, height=10))  # Spacer between items
                content.add_widget(item_layout)

        scroll_view.add_widget(content)
        self.add_widget(scroll_view)

        back_button = Button(text="Back to Main Menu", size_hint_y=0.1)
        back_button.bind(on_press=lambda instance: self.build_main_menu())
        self.add_widget(back_button)

    def show_error(self, message):
        """Display an error popup."""
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()


class VirtualPantryApp(App):
    def build(self):
        return MainScreen()


if __name__ == "__main__":
    VirtualPantryApp().run()
