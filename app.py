from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

# -------------------- APP CONFIG --------------------
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ✅ Mail Config (Gmail App Password required)
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="as9839511@gmail.com",     # your Gmail
    MAIL_PASSWORD="otgq qpul cofg kpzi",     # Gmail app password
    MAIL_DEFAULT_SENDER="as9839511@gmail.com"
)

mail = Mail(app)

# ✅ Database URL (Render)
DATABASE_URL = (
    "postgresql://ayan_641e_user:Jgi7PNtvYaQawSp6EAlmWWsB0ADhXzdA"
    "@dpg-d34na0h5pdvs73b3va6g-a.oregon-postgres.render.com/ayan_641e"
)

def get_db_connection():
    """Create and return a new DB connection"""
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# -------------------- ROUTES --------------------

@app.route("/", methods=["GET", "POST"])
def front():
    if request.method == "POST":
        email = request.form.get("Email")
        if email and email.endswith("@gmail.com"):
            session["subemail"] = email
            return redirect(url_for("menu1"))
        return "❌ Invalid email, try again!"
    return render_template("ayan.html")


@app.route("/About")
def about():
    return render_template("about.html")


@app.route("/Menu", endpoint="menu")
def menu():
    return render_template("login.html")


@app.route("/Menu1")
def menu1():
    return render_template("Menu.html")


@app.route("/Deals")
def deals():
    return render_template("deals.html")


@app.route("/Favourite")
def favourite():
    return render_template("favourite.html")


# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not all([fullname, email, username, password, confirm_password]):
            return "⚠️ All fields are required!"

        if password != confirm_password:
            return "❌ Passwords do not match!"

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO users (fullname, email, username, password)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (fullname, email, username, hashed_pw),
            )

            conn.commit()
            cur.close()
            conn.close()

            # ✅ Send Thank You Email
            msg = Message(
                subject="Thank You for Registering at De Cafe ☕",
                recipients=[email],
                body=(
                    f"Hello {fullname},\n\n"
                    f"Thank you for registering at De Cafe! 🎉\n\n"
                    f"We’re excited to serve you delicious coffee soon.\n\n"
                    f"- The De Cafe Team"
                ),
            )
            mail.send(msg)

            session["user"] = username
            return redirect(url_for("menu1"))

        except Exception as e:
            return f"⚠️ Database Error: {e}"

    return render_template("register.html")


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, hashed_pw),
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user"] = user["username"]
            return redirect(url_for("menu1"))
        return "❌ Invalid credentials!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("front"))


# -------------------- CART --------------------
@app.route("/cart")
def cart():
    return render_template("cart.html")


# -------------------- CHECKOUT --------------------
@app.route("/checkout", methods=["POST"])
def checkout():
    if "user" not in session:
        return jsonify({"message": "Please login first before ordering!"}), 401

    data = request.get_json()
    print(f"✅ Order by {session['user']}: {data}")

    # TODO: Save order into DB (orders table)
    return jsonify({"message": "Order received successfully!"})


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True)
