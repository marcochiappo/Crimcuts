This document explains how this app works "under the hood"

app.py is the main Flask application file.  
It contains:
- Route definitions
- Session management
- Database connections
- Rating logic (create/update/delete)
- Shop + barber lookup logic

@app.route("/") 
Displays login/register options or welcome message.

/register — creates hashed passwords using Werkzeug
/login — validates credentials; stores `user_id` + `username` in session
/logout — clears the session

Password hashing ensures student projects remain secure and follow best practice.

/barbers 
Runs a SQL JOIN between shops and barbers so the user interface can group barbers under shops.

/barbers/<id>  
Displays:
- Barber + shop info
- Ratings joined with users
- Average score

All fetches for this page runin a single route to keep the data consistent

In two separate routes:
/rate/<barber_id>
- If user already rated → UPDATE  
- If not → INSERT
to ensure that there is one rating per user and ratings can be edited without duplication

there is also a delete which deletes the rating of the logged in user

DATABASE DESIGN:
users - to store user credentials
shops - to store shops data
barbers - to store barbers to each shop
ratings - to store all the ratings of each shop

Templates:
layout.hmtl for navigation bar, site header and footer
barber_detail.html for rating display, rating submission form and rating deletion form
css styling lookin glike harvard with crimson red and black

ERROR HANDLING:
checking the user is signed in with session, flash messages when something wrong occurs, barber not found over 404 crash, all databse connections use a shared helper