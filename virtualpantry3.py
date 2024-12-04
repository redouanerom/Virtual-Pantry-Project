import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import sqlite3
from tkinter import Tk, filedialog
from fuzzywuzzy import fuzz
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

# Connect to the SQLite database
db_path = r"C:\Users\saz16\Virtual-Pantry\database\FoodData.db"

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
        print(text)  # Debug: Print the raw text extracted from the image
        
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()

            # Clear previous pantry data
            self.food_pantry = []

            # Loop through each line of the scanned text
            for line in text.splitlines():
                for row in cur.execute("SELECT * FROM Produce"):
                    category, name, min_days, max_days, avg_days, tips = row
                    if fuzz.partial_ratio(name.lower(), line.lower()) > 80:  # Match threshold
                        self.food_pantry.append({
                            "category": category,
                            "name": name,
                            "avg_days": avg_days,
                            "tips": tips
                        })

            con.close()
        except Exception as e:
            self.show_error(f"Error accessing database: {e}")

        self.view_pantry()

    def view_pantry(self, instance=None):
        """Display the pantry list."""
        self.clear_widgets()  # Clear previous UI
        self.add_widget(self.header)  # Re-add header

        scroll_view = ScrollView(size_hint=(1, 0.8))
        content = BoxLayout(orientation='vertical', size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Add space at the top
        content.add_widget(Label(text="", size_hint_y=None, height=20))  # Spacer at the top

        if not self.food_pantry:
            content.add_widget(Label(text="No items in the pantry."))
        else:
            for item in self.food_pantry:
                # Display the matched data
                content.add_widget(Label(text=f"Category: {item['category']}", font_size=16))
                content.add_widget(Label(text=f"Name: {item['name']}", font_size=16))
                content.add_widget(Label(text=f"Average Shelf Life: {item['avg_days']} days", font_size=16))
                content.add_widget(Label(text=f"Tips: {item['tips'] if item['tips'] else 'No tips available'}", font_size=16))
                # Add a blank line between items
                content.add_widget(Label(text="", size_hint_y=None, height=20))

        scroll_view.add_widget(content)
        self.add_widget(scroll_view)

        # Add a Back to Main Menu button
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
