from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import psycopg2
from psycopg2.extras import RealDictCursor
import os, hashlib, random

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "as9839511@gmail.com"   # 🔹 your Gmail
app.config['MAIL_PASSWORD'] = "otgq qpul cofg kpzi"      # 🔹 NOT Gmail password, use app password
app.config['MAIL_DEFAULT_SENDER'] = "as9839511@gmail.com"

mail = Mail(app)




DATABASE_URL = "postgresql://ayan_641e_user:Jgi7PNtvYaQawSp6EAlmWWsB0ADhXzdA@dpg-d34na0h5pdvs73b3va6g-a.oregon-postgres.render.com/ayan_641e"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Product {self.name}>"


# -------------------- ROUTES --------------------

@app.route('/',methods=['GET', 'POST'])
def front():
    if request.method == "POST":
        email = request.form.get("Email")



        if '@gmail.com' in email:
            session['subemail'] = email
            return redirect(url_for('menu1'))
        else:
            return "Invalid credentials, try again!"

    return render_template('ayan.html')

@app.route('/About')
def about():
    return render_template('about.html')

@app.route('/Menu', endpoint="menu")
def menu():
    return render_template('login.html')

@app.route('/Menu1')
def menu1():
     products = Product.query.all()
     return render_template('Menu.html')

@app.route('/Deals')
def deals():
    return render_template('deals.html')

@app.route('/Favourite')
def favourite():
    return render_template('favourite.html')

@app.route('/frontp')
def ayan1():
    return render_template('ayan1.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return "❌ Passwords do not match!"

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Save user with verified = False
            cur.execute("""
                INSERT INTO users (fullname, email, username, password, verified)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (fullname, email, username, hashed_pw, False))
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            # ✅ Generate OTP & save in session
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['pending_user'] = user_id
            session['pending_email'] = email
            session['pending_name'] = fullname

            # ✅ Send OTP email
            msg = Message(
                subject="Verify your De Cafe Account ☕",
                recipients=[email],
                body=f"Hello {fullname},\n\nYour OTP is: {otp}\n\nThis OTP is valid for 5 minutes.\n\n- De Cafe Team"
            )
            mail.send(msg)

            return redirect(url_for('verify_otp'))

        except Exception as e:
            return f"⚠️ Database Error: {e}"

    return render_template("register.html")


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form.get("otp")

        # ✅ Check if OTP matches
        if entered_otp == session.get('otp'):
            try:
                conn = get_db_connection()
                cur = conn.cursor()

                # Mark user as verified
                cur.execute("""
                    UPDATE users SET verified = TRUE WHERE id = %s
                """, (session['pending_user'],))

                conn.commit()
                cur.close()
                conn.close()

                # Cleanup session
                session.pop('otp', None)
                session.pop('pending_user', None)

                return redirect(url_for('ayan1'))

            except Exception as e:
                return f"⚠️ Database Error: {e}"
        else:
            return render_template("verify_otp.html", error="❌ Invalid OTP! Try again.")

    return render_template("verify_otp.html")




# -------------------- LOGIN LOGIC --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s",
                    (username, hashed_pw))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session['user'] = user['username']
            return redirect(url_for('ayan1'))
        else:
            return "❌ Invalid credentials!"

    return render_template("login.html")  # make login.html page

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('front'))

@app.route('/cart')
def cart():
    return render_template('cart.html')


# -------------------- CHECKOUT LOGIC --------------------

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user' not in session:   # 🔐 User not logged in
        return jsonify({"message": "Please login first before ordering!"}), 401

    data = request.get_json()
    print(f"Order by {session['user']}: {data}")

    # TODO: Save order into DB here (MySQL/Postgres)

    return jsonify({"message": "Order received successfully!"})

# -------------------- RUN APP --------------------

if __name__ == '__main__':
    app.run(debug=True)


