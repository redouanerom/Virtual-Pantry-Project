import pytesseract
from PIL import Image
import re
import pandas as pd
from tkinter import Tk, filedialog
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import os

# Load food names from the uploaded .xls file
data_file_path =  r"C:\Users\saz16\Virtual-Pantry\database\FoodKeeper-Data (1).xls"
food_names = []

# Check if the file exists
if not os.path.exists(data_file_path):
    raise FileNotFoundError(f"Excel file not found: {data_file_path}")

# Load food names from the Excel file
food_names = []
try:
    # Load Excel file into a DataFrame
    df = pd.read_excel(data_file_path)
    
    # Assuming the first column contains food names
    # Convert column to strings, drop NaN or invalid entries
    food_names = df.iloc[:, 0].dropna().astype(str).str.lower().tolist()
except Exception as e:
    print(f"Error loading food data: {e}")

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.food_pantry = []  # Store items with names and dates

        # Header
        self.header = Label(text="Virtual Pantry", font_size=24, size_hint_y=0.1)
        self.add_widget(self.header)

        # Menu Buttons
        menu_button = Button(text="View Pantry", size_hint_y=0.1)
        menu_button.bind(on_press=self.view_pantry)
        self.add_widget(menu_button)

        scan_button = Button(text="Scan Receipt", size_hint_y=0.1)
        scan_button.bind(on_press=self.scan_receipt)
        self.add_widget(scan_button)

        # Item Display
        self.item_list = BoxLayout(orientation='vertical')
        self.add_widget(self.item_list)

    def scan_receipt(self, instance):
        # Use tkinter file dialog to select the file
        root = Tk()
        root.withdraw()  # Hide the tkinter root window
        filepath = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if filepath:
            try:
                text = pytesseract.image_to_string(Image.open(filepath))
                self.extract_and_store_data(text)
            except Exception as e:
                self.show_error(str(e))

    def extract_and_store_data(self, text):
        # Search for dates (format: MM/DD/YYYY or DD/MM/YYYY)
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        found_date = re.search(date_pattern, text)
        purchase_date = found_date.group(0) if found_date else "Unknown"

        # Search for food names
        for line in text.splitlines():
            for food in food_names:
                if food in line.lower():
                    self.food_pantry.append({"name": food, "date": purchase_date})

        self.view_pantry()

    def view_pantry(self, instance=None):
        self.item_list.clear_widgets()
        for item in self.food_pantry:
            label = Label(text=f"{item['name']} - {item['date']}")
            self.item_list.add_widget(label)

    def show_error(self, message):
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()


class VirtualPantryApp(App):
    def build(self):
        return MainScreen()


if __name__ == "__main__":
    VirtualPantryApp().run()
