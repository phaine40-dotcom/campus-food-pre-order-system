import sqlite3

#Connect to existing database
conn = sqlite3.connect('campus_food.db')

try:
    #Read the existing columns in the orders table
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]

    #Add status only if it does not already exist
    if "status" not in columns:
        cursor.execute("""
           ALTER TABLE orders
           ADD COLUMN status TEXT NOT NULL DEFAULT 'Pending'
        """)
        conn.commit()
        print("Success! The status column has been added.")
    else:
        print("The status column already exists. No changes needed.")

    #Display the updated column names
    cursor.execute("PRAGMA table_info(orders)")
    print("Orders columns:", [column[1] for column in cursor.fetchall()])

except sqlite3.Error as error:
    conn.rollback()
    print("Database error:", error)

finally:
    conn.close()