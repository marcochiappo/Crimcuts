from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route("/")
def index():
    # if user is logged in, get username from session
    user=session.get("username")
    return render_template("index.html", user=user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not username or not password or not confirm_password:
            error = "All fields are required."
            return render_template("register.html", error=error)
        
        if password != confirm_password:
            error = "Passwords do not match. Please try again."
            return render_template("register.html", error=error)
        
        try:
            # insert user into the database
            conn = sqlite3.connect("crimcuts.db")
            # hash password before storing
            pw_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, pw_hash),)
            # permanently save all changes made during the connection
            conn.commit()
            # close the connection
            conn.close()

        except sqlite3.IntegrityError:
            # if username already exists, return error
            error = "Username already exists. Please choose a different one."
            return render_template("register.html", error=error)
        
        # remember user
        session["username"] = username
        
        # on successful registration, redirect to home page
        return redirect(url_for("index"))
    else:
    
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            error = "All fields are required."
            return render_template("login.html", error=error)

        conn = sqlite3.connect("crimcuts.db")
        row = conn.execute("SELECT password FROM users WHERE username = ?", (username,))
        # returns a single row from the result
        row = row.fetchone()
        conn.close()

        if row is None or not check_password_hash(row[0], password):
            error = "Invalid username or password."
            return render_template("login.html", error=error)
        
        # remember user
        session["username"] = username

        # on successful login, redirect to home page
        return redirect(url_for("index"))
    else:

        return render_template("login.html")

@app.route("/logout")
def logout():
    # clear the session to log out the user
    session.clear()
    return redirect(url_for("index"))

# connecting to the database
def get_db_connection():
    """
    Return a database connection for the current request.

    - If this is the first time we ask for a connection in this request,
      we open one and store it in 'g.db'.
    - If we've already opened one, we just reuse it.
    """
    if "db" not in g:
        # connect to the database file
        g.db = sqlite3.connect("crimcuts.db")
        # make rows behave like dictionaries: row["username"] instead of row[0]
        g.db.row_factory = sqlite3.Row
    return g.db

# when the request is over, if we opened a database connection, close it
@app.teardown_appcontext
def close_db_connection(error):
    # Remove "db" from g if it exists, else return None
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/barbers")
def barbers():
    db = get_db_connection()
    # fetch all barbers from the database
    barbers = db.execute("""
        SELECT
            barbers.id AS barber_id,
            barbers.name AS barber_name,
            shops.name AS shop_name,
            shops.location AS shop_location,
            shops.website AS shop_website,
            shops.description AS shop_description
        FROM barbers
        JOIN shops ON barbers.shop_id = shops.id
        ORDER BY shops.name, barbers_name ASC;
        """).fetchall()
    return render_template("barbers.html", barbers=barbers, user=session.get("username"))

@app.route("/barbers/<int:barber_id>", methods=["GET", "POST"])
def barber_detail(barber_id):
    db = get_db_connection()

    # If user submits a rating (POST)
    if request.method == "POST":
        # Must be logged in to rate
        if "username" not in session:
            # not logged in, send to login page
            return redirect(url_for("login"))

        rating_value = request.form.get("rating")
        comment = request.form.get("comment", "").strip()

        # Rating must exist and be between 1 and 5
        if not rating_value or rating_value not in ["1", "2", "3", "4", "5"]:
            error = "Please select a rating between 1 and 5."
        else:
            # Find current user id
            user_row = db.execute(
                "SELECT id FROM users WHERE username = ?",
                (session["username"],)
            ).fetchone()

            if user_row is None:
                # Logged-in session but user not in database
                error = "User not found."
            else:
                user_id = user_row["id"]

                # Insert rating
                db.execute(
                    "INSERT INTO ratings (user_id, barber_id, rating, comment) VALUES (?, ?, ?, ?)",
                    (user_id, barber_id, int(rating_value), comment)
                )
                # Permanently save all changes made
                db.commit()
                return redirect(url_for("barber_detail", barber_id=barber_id))

    # GET request - fetch barber details and ratings

    # Barber and shop info
    barber = db.execute("""
        SELECT
            barbers.id        AS barber_id,
            barbers.name      AS barber_name,
            shops.name        AS shop_name,
            shops.location    AS shop_location,
            shops.website     AS shop_website,
            shops.description AS shop_description
        FROM barbers
        JOIN shops ON barbers.shop_id = shops.id
        WHERE barbers.id = ?
    """, (barber_id,)).fetchone()

    if barber is None:
        # Simple 404 page
        return "Barber not found", 404

    # Ratings for this barber (joined with users for username)
    ratings = db.execute("""
        SELECT
            ratings.rating      AS rating_value,
            ratings.comment     AS rating_comment,
            users.username      AS username
        FROM ratings
        JOIN users ON ratings.user_id = users.id
        WHERE ratings.barber_id = ?
        ORDER BY ratings.id DESC
    """, (barber_id,)).fetchall()

    # Average rating
    avg_row = db.execute("""
        SELECT AVG(rating) AS avg_rating, COUNT(*) AS count_ratings
        FROM ratings
        WHERE barber_id = ?
    """, (barber_id,)).fetchone()

    avg_rating = avg_row["avg_rating"]
    count_ratings = avg_row["count_ratings"]

    return render_template(
        "barber_detail.html",
        barber=barber,
        ratings=ratings,
        avg_rating=avg_rating,
        count_ratings=count_ratings,
        user=session.get("username")
    )


if __name__== "__main__":
    app.run(debug=True)
