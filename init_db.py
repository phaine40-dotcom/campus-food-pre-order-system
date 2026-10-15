import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'campus_food.db')

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES students (id),
        FOREIGN KEY (item_id) REFERENCES menu_items (id)
    )
''')

menu_items = [
    ('Pancakes', 50),
    ('Toast', 30),
    ('Omelette', 65),
    ('Fruit Salad', 40),
    ('Tea', 20),
    ('Coffee', 25),
    ('Chicken Accompaniment', 180),
    ('Ugali and Beef', 100),
    ('Pilau', 120),
    ('Rice and Beans', 80),
    ('Fruit Juice', 35),
    ('Chapati and Ndengu', 90),
    ('Beef Stew and Rice/Ugali', 150),
    ('Chicken Curry', 160),
    ('Vegetable Stir Fry', 120),
    ('Fish Fillet', 200),
    ('Mashed Potatoes', 70),
    ('Rice and Lentils', 100),
    ('Soda', 80),
    ('Water', 50),
    ('Milkshake', 70),
    ('Delmonte', 210),
    ('Minute Maid', 80),
]

for name, price in menu_items:
    cursor.execute(
        '''
        INSERT INTO menu_items (name, price)
        SELECT ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM menu_items WHERE name = ?
        )
        ''',
        (name, price, name)
    )

conn.commit()
conn.close()
print("Database initialized and tables created successfully.")