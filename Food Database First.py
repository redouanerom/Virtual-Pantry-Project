import sqlite3
con = sqlite3.connect("FoodData.db")

cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS Produce (Category, Name, Min days, Max days, Avg days, Tips)")

#Execute once to populate the data into the table
#If executed multiple times, the data will be duplicated 
 data = [
                 ('Fruit','Apples', 21, 21, 21, 'May extend life by one week in the refrigerator'),
                 ('Fruit', 'Bananas', 3, 3, 3, 'Skin may blacken'),
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
 ]

 cur.executemany("INSERT INTO Produce VALUES(?, ?, ?, ?, ?, ?)", data)
 con.commit()

for row in cur.execute("SELECT Name, Avg days, Tips FROM Produce"):
    print(row)

con.close()
