from flask import Flask, render_template, request, redirect, url_for, session, g, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import difflib

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "supersecretkey"

@app.route("/")
def index():
    # if user is logged in, get username from session
    user=session.get("username")
    return render_template("index.html", user=session.get("username"))

@app.route("/haircut_upload", methods=["GET", "POST"])
def haircut_upload():
    db = get_db_connection()
    if request.method == "POST":
        haircut_photo = request.files.get("photo")
        img = None

        # Save uploaded photo if present
        if haircut_photo and haircut_photo.filename:
            img_path = "static/barber_images/" + haircut_photo.filename
            haircut_photo.save(img_path)
            img = img_path

        barber_of_choice = request.form.get("barber", "").strip()

        # Validate barber exists
        barber_row = db.execute(
            "SELECT id FROM barbers WHERE name = ?",
            (barber_of_choice,)
        ).fetchone()

        # If barber not found, return error
        if barber_row is None:
            error = "Please enter a valid barber: format is First_name Last_name"
            db.close()
            return render_template("haircut_upload.html", error=error)

        barber_id = barber_row["id"]

        # Insert uploaded haircut photo with associated barber_id
        db.execute(
            "INSERT INTO haircut_photos (barber_id, photo) VALUES (?, ?)",
            (barber_id, img)
        )
        db.commit()
        db.close()
        return redirect(url_for("barbers"))

    db.close()
    return render_template("haircut_upload.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # validate input
        if not username or not password or not confirm_password:
            error = "All fields are required."
            return render_template("register.html", error=error)
        
        # check if passwords match
        if password != confirm_password:
            error = "Passwords do not match. Please try again."
            return render_template("register.html", error=error)
        
        if len(password) < 8:
            error = "Password must be at least 8 characters long."
            return render_template("register.html", error=error)
        
        if not any(char.isdigit() for char in password):
            error = "Password must contain at least one number."
            return render_template("register.html", error=error)
        
        if not any(char.isupper() for char in password):
            error = "Password must contain at least one uppercase letter."
            return render_template("register.html", error=error)
        
        if not any (char.islower() for char in password):
            error = "Password must contain at least one lowercase letter."
            return render_template("register.html", error=error)
        
        if not any (char.isalpha() for char in password):
            error = "Password must contain at least one letter."
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

        # validate input
        if not username or not password:
            error = "All fields are required."
            return render_template("login.html", error=error)

        # fetch user from database
        conn = sqlite3.connect("crimcuts.db")
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        # returns a single row from the result
        row = row.fetchone()
        conn.close()

        # check if user exists and password is correct
        if row is None or not check_password_hash(row["password"], password):
            error = "Invalid username or password."
            return render_template("login.html", error=error)
        # remember user
        session["user_id"] = row["id"]
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

# Barbers listing page
@app.route("/barbers")
def barbers():
    db = get_db_connection()
    shops = db.execute("""SELECT id, name, location, website, description FROM shops ORDER BY name ASC""").fetchall()
    result = []
    # For each shop, get its barbers
    for shop in shops:
        shop_barbers = db.execute("""
            SELECT id, name FROM barbers
            WHERE shop_id = ?
            ORDER BY name ASC
        """, (shop["id"],)).fetchall()
        
        # Append shop and its barbers to result
        result.append({
            "shop": shop,
            "barbers": shop_barbers
        })

    return render_template("barbers.html", shops = result, user=session.get("username"))

# Barber detail page with ratings
@app.route("/barbers/<int:barber_id>")
def barber_detail(barber_id):
    db = get_db_connection()

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

    # If barber not found, return 404
    if barber is None:
        return "Barber not found", 404

    # Ratings for this barber
    ratings = db.execute("""
        SELECT
            ratings.rating  AS rating_value,
            ratings.comment AS rating_comment,
            ratings.photo   AS photo,
            users.username  AS username
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

    # Handle case with no ratings
    if avg_row is None:
        avg_rating = None
        count_ratings = 0
    else:
        avg_rating = avg_row["avg_rating"]
        count_ratings = avg_row["count_ratings"]

    # Render the barber detail template
    return render_template(
        "barber_detail.html",
        barber=barber,
        ratings=ratings,
        avg_rating=avg_rating,
        count_ratings=count_ratings,
        user=session.get("username")
    )


# Rate a barber
@app.route("/rate/<int:barber_id>", methods=["POST"])
def rate_barber(barber_id):
    if "user_id" not in session:
        flash("You must be logged in to rate a barber.")
        return redirect(url_for("login"))
    
    # Get rating and comment from form submission
    rating_str = request.form.get("rating")
    if not rating_str:
        flash("Please select a rating.")
        return redirect(url_for("barber_detail", barber_id=barber_id))

    # Convert rating to integer and get comment
    rating = int(rating_str)
    comment = request.form.get("comment", "").strip()
    user_id = session["user_id"]

    # Upload Image of Haircut
    haircut_photo = request.files.get("photo")
    photo_path = None
    
    if haircut_photo and haircut_photo.filename:
        # Save uploaded photo
        filename = f"{barber_id}_{user_id}_{haircut_photo.filename}"
        photo_path = "static/barber_images/" + filename
        haircut_photo.save(photo_path)

    db = get_db_connection()
    # Check if user has already rated this barber
    existing = db.execute("""
        SELECT id FROM ratings
        WHERE user_id = ? AND barber_id = ?
    """, (user_id, barber_id)).fetchone()
    # If so, update the existing rating; otherwise, insert a new one
    if existing:
        db.execute("""
            UPDATE ratings
            SET rating = ?, comment = ?, photo = ?
            WHERE id = ?
        """, (rating, comment, photo_path, existing["id"]))
        flash("Your rating has been updated!")
    # New rating
    else:
        db.execute("""
            INSERT INTO ratings (user_id, barber_id, rating, comment, photo)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, barber_id, rating, comment, photo_path))
        flash("Thanks for your rating g!")
    
    db.commit()
    db.close()
    
    return redirect(url_for("barber_detail", barber_id=barber_id))


# Delete a rating
@app.route("/rate/<int:barber_id>/delete", methods=["POST"])
def delete_rating(barber_id):
    if "user_id" not in session:
        flash("You must be logged in to delete a rating.")
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    db = get_db_connection()
    
    # Check if user has rated this barber
    existing = db.execute("""
                          SELECT id FROM ratings WHERE user_id = ? AND barber_id = ?
                          """, (user_id, barber_id)).fetchone()
    
    # If so, delete the rating
    if existing:
        db.execute("DELETE FROM ratings WHERE user_id = ? AND barber_id = ?", (user_id, barber_id))
        flash("Your rating has been deleted.")
    else:
        flash("No rating found to delete.")
    
    db.commit()
    db.close()
    
    flash("Your rating has been deleted.")
    return redirect(url_for("barber_detail", barber_id=barber_id))

# About page
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/map_page")
def map_page():
    return render_template("map.html")

@app.route("/search_shops")
def search_shops():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify([])

    conn = get_db_connection()
    shops_data = conn.execute("SELECT name, latitude, longitude FROM shops WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    conn.close()

    # Convert to {"name": ..., "location": "lat,lon"} format
    all_shops = [
        {"name": row["name"], "location": f"{row['latitude']},{row['longitude']}"}
        for row in shops_data
    ]

    query_lower = query.lower()
    result = [shop for shop in all_shops if query_lower in shop["name"].lower()]
    return jsonify(result)

@app.route("/upload_shop", methods=["GET", "POST"])
def upload_shop():
    #The goal of this function is to allow barbers to upload their shop information to the database.
    if request.method == "POST":
        name = request.form["shop"]
        address = request.form["address"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        website = request.form["website"]
        description = request.form["description"]
        db = get_db_connection()
        db.execute(
            "INSERT INTO shops (name, location, latitude, longitude, website, description) VALUES (?, ?, ?, ?, ?, ?)",
            (name, address, latitude, longitude, website, description)
        )
        db.commit()
        db.close()
        return redirect(url_for("barbers"))
    return render_template("Upload_shop.html")


@app.route("/upload_barber", methods=["GET", "POST"])
def upload_barber():
    """Render a barber upload form and handle submissions.

    The form expects 'barber' (name) and 'shop_id' (id of chosen shop).
    Requires user to be logged in.
    """
    if "user_id" not in session:
        flash("You must be logged in to upload a barber profile.")
        return redirect(url_for("login"))
    
    db = get_db_connection()
    if request.method == "POST":
        barber_name = request.form.get("barber", "").strip()
        shop_id = request.form.get("shop_id")

        if not barber_name or not shop_id:
            error = "Barber name and shop are required."
            # load shops for re-rendering the form with an error
            shops = db.execute("SELECT id, name FROM shops ORDER BY name ASC").fetchall()
            db.close()
            return render_template("Upload_barber.html", shops=shops, error=error)

        # insert into barbers table
        db.execute(
            "INSERT INTO barbers (name, shop_id) VALUES (?, ?)",
            (barber_name, shop_id)
        )
        db.commit()
        db.close()
        return redirect(url_for("barbers"))

    # GET - render form with shops list
    shops = db.execute("SELECT id, name FROM shops ORDER BY name ASC").fetchall()
    db.close()
    return render_template("Upload_barber.html", shops=shops)

if __name__== "__main__":
    app.run(debug=True)

