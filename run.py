import os
from flask import Flask, render_template, redirect, request, url_for, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt
import re

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'CaveDuVin'
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

mongo = PyMongo(app)


# Start app on index.html
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', 
            user_name = 'User: ' + session['username'], 
            colours=mongo.db.colours.find(), 
            country=mongo.db.country.find(), 
            region=mongo.db.region.find(), 
            grape=mongo.db.grape.find()
            )
    return render_template('index.html', 
            colours=mongo.db.colours.find(), 
            country=mongo.db.country.find(), 
            region=mongo.db.region.find(), 
            grape=mongo.db.grape.find()
            )


# Log In/Out and Register routes
@app.route('/login_page')
def login_page():
    return render_template('login.html')


# Credit: https://edubanq.com/programming/mongodb/creating-a-user-login-system-using-python-flask-and-mongodb/
@app.route('/login', methods =['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return render_template("login.html", password_error = 'Invalid username/password combination')


# Credit: https://pythonbasics.org/flask-sessions/
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


# Credit: https://edubanq.com/programming/mongodb/creating-a-user-login-system-using-python-flask-and-mongodb/
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        SpecialSym =['$', '@', '#', '%', '!'] 

        userVal = request.form['username']
        if re.match("^[a-zA-Z0-9*]+$", userVal): # Credit: https://stackoverflow.com/questions/15580917/python-data-validation-using-regular-expression
            passVal = request.form['pass']
            # Credit: https://www.geeksforgeeks.org/password-validation-in-python/#:~:text=Conditions%20for%20a%20valid%20password%20are%3A%201%20Should,be%20between%206%20to%2020%20characters%20long.%20
            if len(passVal) < 6: 
                return render_template("register.html", register_error = 'password should be at least 6 characters')
            if len(passVal) > 10: 
                return render_template("register.html", register_error = 'password should be no more than 10 characters')
            if not any(char.isdigit() for char in passVal): 
                return render_template("register.html", register_error = 'password should have at least one numeral')
            if not any(char.isupper() for char in passVal):
                return render_template("register.html", register_error = 'password should have at least one uppercase letter')
            if not any(char.islower() for char in passVal):
                return render_template("register.html", register_error = 'password should have at least one lowercase letter')
            if not any(char in SpecialSym for char in passVal):
                return render_template("register.html", register_error = 'password should have at least one of the symbols $, @, #, % or !')
            else:
                if existing_user is None:
                    hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
                    users.insert({'name' : request.form['username'], 'password' : hashpass})
                    session['username'] = request.form['username']
                    return redirect(url_for('index'))

                return render_template("register.html", register_error = 'That username already exists')

        else:
            return render_template("register.html", register_error = 'Please enter a valid username of text and numbers, with no spaces')



    return render_template('register.html')

    return ''


# Add Wine routes
@app.route('/add_wine_page')
def add_wine_page():
    return render_template("add_wine.html", 
        user_name = 'User: ' + session['username'], 
        colours=mongo.db.colours.find(), 
        country=mongo.db.country.find(), 
        region=mongo.db.region.find(), 
        grape=mongo.db.grape.find()
        )


@app.route('/add_wine', methods=["GET", "POST"])
def add_wine():
    nameadd = request.values.get("name")
    vintageadd = request.values.get("vintage")
    colouradd = request.values.get("colour")
    countryadd = request.values.get("country")
    regionadd = request.values.get("region")
    grapeadd = request.values.get("grape")
    return render_template("add_wine.html", 
        user_name = 'User: ' + session['username'], 
        insert=mongo.db.wines.insert_one( 
            {"wine_name": nameadd, 
            "vintage": vintageadd, 
            "colour": colouradd, 
            "country": countryadd , 
            "region": regionadd, 
            "grape": grapeadd, 
            "photo_url": "", 
            "tasting_notes": ""} 
            ))


@app.route('/add_grape', methods=["GET", "POST"])
def add_grape():
    grapeadd = request.values.get("addgrape")
    return render_template("add_wine.html", 
        user_name = 'User: ' + session['username'], 
        colours=mongo.db.colours.find(), 
        country=mongo.db.country.find(), 
        region=mongo.db.region.find(), 
        grape=mongo.db.grape.find(), 
        insert=mongo.db.grape.insert_one( 
            {"grape": grapeadd} 
            ))


# Refresh Search Form route
@app.route('/populate_form')
def populate_form():
    return render_template("add_wine.html", user_name = 'User: ' + session['username'], colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())


# Browse Wines routes
@app.route('/search_page')
def search_page():
    if 'username' in session:
        return render_template('index.html', user_name = 'User: ' + session['username'], colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())
    return render_template('index.html', colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())


@app.route('/populate_search')
def populate_search():
    if 'username' in session:
        return render_template("index.html", user_name = 'User: ' + session['username'], colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find(), grape=mongo.db.grape.find())
    return render_template("index.html", colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find(), grape=mongo.db.grape.find())


@app.route("/search", methods=["GET", "POST"])
def search():
    namesearch = request.values.get("name")
    vintagesearch = request.values.get("vintage")
    coloursearch = request.values.get("colour")
    countrysearch = request.values.get("country")
    regionsearch = request.values.get("region")
    # return render_template("index.html", results=mongo.db.wines.find({"$text": {"$search": namesearch}}))
    return render_template("index.html", results=mongo.db.wines.find( 
                                            {"$and": 
                                            [ 
                                            {"$text": {"$search": namesearch}}, 
                                            {"vintage": vintagesearch}, 
                                            {"colour": coloursearch}, 
                                            {"country": countrysearch} , 
                                            {"region": regionsearch} 
                                            ] }), 
                                            colours=mongo.db.colours.find(), 
                                            country=mongo.db.country.find(), 
                                            region=mongo.db.region.find(), 
                                            grape=mongo.db.grape.find()
                                            )
    redirect(url_for('populate_search'))


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)