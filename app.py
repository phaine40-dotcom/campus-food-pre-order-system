import os
import json
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'campus_food.db')

app.secret_key = "campus-food-secret-key"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema():
    conn = get_db_connection()
    try:
        student_columns = {
            row['name']
            for row in conn.execute("PRAGMA table_info(students)").fetchall()
        }
        if 'student_id' not in student_columns:
            conn.execute("ALTER TABLE students ADD COLUMN student_id TEXT")

        order_columns = {
            row['name']
            for row in conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        if 'user_id' not in order_columns:
            conn.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER")
        if 'order_ref' not in order_columns:
            conn.execute("ALTER TABLE orders ADD COLUMN order_ref TEXT")
        if 'status' not in order_columns:
            conn.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'Pending'")
        conn.commit()
    finally:
        conn.close()


ensure_schema()


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        student_id = request.form.get("student_id", "").strip()

        if not full_name or not email or not password:
            return "Please fill in all required fields.", 400
        if password != confirm_password:
            return "Passwords do not match.", 400

        password_hash = generate_password_hash(password)
        conn = get_db_connection()

        try:
            existing_student = conn.execute(
                "SELECT id FROM students WHERE email = ? OR student_id = ?",
                (email, student_id or None)
            ).fetchone()
            if existing_student is not None:
                return "This email or student ID is already registered. Please use another one.", 400

            cursor = conn.execute(
                """INSERT INTO students
                (full_name, email, password_hash, student_id)
                VALUES(?,?,?,?)""",
                (full_name, email, password_hash, student_id or None)
            )
            conn.commit()
            return f"""
               <h2>Registration successful!</h2>
               <p>Welcome, {full_name}!</p>
               <p>Your Student ID is: {cursor.lastrowid}</p>
               <a href="/login">Go to login</a>
               """
        except sqlite3.IntegrityError:
            return "This email or student ID is already registered. Please use another one.", 400
        finally:
            conn.close()

    return render_template("registration.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        student = conn.execute(
            "SELECT * FROM students WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if student and check_password_hash(student["password_hash"], password):
            session.clear()
            session["user_id"] = student["id"]
            session["full_name"] = student["full_name"]
            return redirect(url_for('menu'))

        return "Invalid email or password. Please try again.", 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')


@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = session.get('user_id')
    if user_id is None:
        return "Please log in before placing an order.", 401

    cart_data = request.form.get('cart_data', '')
    try:
        cart = json.loads(cart_data)
    except (json.JSONDecodeError, TypeError):
        return "Invalid cart data.", 400

    if not isinstance(cart, list) or not cart:
        return "Your cart is empty or invalid.", 400

    conn = get_db_connection()

    try:
        columns = {
            row['name']
            for row in conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        if 'user_id' not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER")
        if 'order_ref' not in columns:
            conn.execute("ALTER TABLE orders ADD COLUMN order_ref TEXT")

        items = []
        total_price = 0
        for entry in cart:
            if not isinstance(entry, dict):
                return "Invalid cart item.", 400

            food = entry.get('food')
            quantity = entry.get('quantity')
            if not isinstance(food, str) or not food.strip():
                return "Invalid food item.", 400
            if not isinstance(quantity, int) or quantity < 1:
                return "Invalid quantity.", 400

            item = conn.execute(
                "SELECT id, name, price FROM menu_items WHERE name = ?",
                (food.strip(),)
            ).fetchone()
            if item is None:
                return f"Food item is not found: {food}", 400

            line_total = float(item['price']) * quantity
            total_price += line_total
            items.append({
                'item_id': item['id'],
                'name': item['name'],
                'quantity': quantity,
                'price': item['price'],
                'total': line_total
            })

        order_ref = uuid.uuid4().hex[:10].upper()
        for item in items:
            conn.execute(
                """
                INSERT INTO orders
                    (user_id, item_id, quantity, total_price, order_ref)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, item['item_id'], item['quantity'], item['total'], order_ref)
            )
        conn.commit()

        return render_template(
            'order_confirmation.html',
            order_id=order_ref,
            items=items,
            total_price=total_price
        )
    except sqlite3.Error:
        conn.rollback()
        app.logger.exception("Checkout database error")
        return "Checkout could not be completed. Please try again.", 500
    finally:
        conn.close()


@app.route('/staff/orders')
def staff_orders():
    conn = get_db_connection()

    try:
        orders = conn.execute("""
        SELECT
            orders.id,
            students.full_name,
            menu_items.name AS food_name,
            orders.quantity,
            orders.total_price,
            orders.order_date,
            orders.status
        FROM orders
        JOIN students ON orders.user_id = students.id
        JOIN menu_items ON orders.item_id = menu_items.id
        ORDER BY orders.id DESC
        """).fetchall()
    finally:
        conn.close()

    return render_template('staff_orders.html', orders=orders)


if __name__ == '__main__':
    app.run(debug=True)