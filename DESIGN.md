This document explains how this app works "under the hood"

app.py is the main Flask application file.  
It contains:
- Route definitions
- Session management
- Database connections
- Rating logic (create/update/delete)
- Shop + barber lookup logic
- JSON API endpoints for shop search
- Haircut photo upload

All SQL queries are run through helper functions to keep the code organized and reduce duplication.


Jinja2 templates - dynamically render HTML pages
Static files - provide styling and interactivity
Leaflet.js display an interactive map

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

All fetches for this page running a single route to keep the data consistent

In two separate routes:
/rate/<barber_id>
- If user already rated → UPDATE  
- If not → INSERT
to ensure that there is one rating per user and ratings can be edited without duplication

There is also a delete which deletes the rating of the logged in user

Route: '/upload_shop'

- GET: Displays a form to add a new shop.
- POST: Validates the form and inserts a new row into 'shops' with:
  - Name
  - Address
  - Latitude and longitude
  - Website
  - Description

The latitude and longitude are used later to place the shop on the map, while the address and description are displayed to users.

Route: '/upload_barber'

- GET: Displays a form with:
  - A field for barber name
  - A dropdown populated from the 'shops' table
- POST: Inserts a new row into 'barbers' linked to the selected 'shop_id'.

This design allows the shop list to grow over time, and new barbers can be added to any existing shop without changing the database structure.

Route: '/haircut_upload'

- GET: Displays a form where a user can:
  - Select or type a barber
  - Choose an image file to upload
- POST:
  - Validates that a file was provided.
  - Saves the file into a static images directory
  - Optionally associates the filename with a barber (depending on the implementation).

Files are served directly by Flask’s static file handling. This approach keeps images out of the database.

The map view uses Leaflet.js with OpenStreetMap tiles.

- The user types into a shop search input.
- A JavaScript `input` event handler sends a request to a backend endpoint
- The backend returns a JSON list of matching shops (name + coordinates).
- Suggestions are displayed in a dropdown.
- When the user clicks a suggestion:
  - The input is filled with that shop’s name.
  - A marker is added to the Leaflet map at the shop’s latitude and longitude.
  - The map view recenters and zooms on the selected shop.

Route: '/search_shops'

- Accepts a query string.
- Looks up shops in the database by name.
- Returns a JSON response with name and coordinates of matching shops.

This design cleanly separates the search API from the interactive UI (JavaScript + Leaflet on the frontend).

Sqlite DATABASE DESIGN:
users - to store user credentials
shops - to store shops data
barbers - to store barbers to each shop
ratings - to store all the ratings of each shop

Templates:
layout.hmtl: for navigation bar, site header and footer
barber_detail.html: for rating display, rating submission form and rating deletion form
CSS styling: Styling uses a dark theme with crimson red highlights, inspired by Harvard’s color scheme
barbers.html: displays shops and barbers grouped together
map.html: contains the Leaflet map container, includes the search input and suggestion dropdown, loads Leaflet CSS/JS and custom JavaScript for map interaction



ERROR HANDLING:
checking the user is signed in with session, flash messages when something wrong occurs, barber not found over 404 crash, all database connections use a shared helper, only the owner of a rating can delete or modify it.