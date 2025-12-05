CrimCutz is a Flask-based website that lets users browse barbershops in the Cambridge/Boston area, view individual barbers, and leave ratings and comments. The app is designed to be simple, clean, and easy to navigate. Users can create accounts, log in, submit reviews, update their reviews, and delete them. All data is stored in a SQLite database bundled with the project.

To install project:
Download the project folder onto your computer, or clone it using:

```bash
git clone <your repo link>

To configurate it simply write 
python3 -m venv venv
source venv/bin/activate   # Mac/Linux

and also install flask

Using the application you should be able to get into the homepage, where you will see a welcome banner, navigation menu, login/register and option to browse barbers.

Register:
users must choose a unique username and passwords, passwords are automatically hashed using Werkzeug before being stored.

Login:
Users provide their username and password to access:
Barber listing, individual barber pages, rating features

Barbers page:
Shows all barbershops grouped by shop, each shop section expands to show its barbers.

Clicking a barber will open their detail page.

Barber Detail Page displays:
Barber name, shop details, average rating, full list of ratings + comments, 

Logged-in users can:
Leave a new rating, update their existing rating delete their rating

Logout:
Logs the user out and returns them to the homepage.

sql database is in the form: 
users(id, username, password)
shops(id, name, location, website)
barbers(id, name, shop_id)
ratings(id, user_id, barber_id, rating, comment)
