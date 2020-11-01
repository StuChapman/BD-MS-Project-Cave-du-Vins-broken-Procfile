import os
from flask import Flask, render_template, redirect, request, url_for, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt

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
        return render_template('index.html', user_name = 'User: ' + session['username'])
    return render_template('index.html')


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

    return 'Invalid username/password combination'


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

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))

        return 'That username already exists'

    return render_template('register.html')

    return ''


# Add Wine routes
@app.route('/add_wine_page')
def add_wine_page():
    return render_template("add_wine.html", user_name = 'User: ' + session['username'])


@app.route('/add_wine', methods=["GET", "POST"])
def add_wine():
    nameadd = request.values.get("name")
    vintageadd = request.values.get("vintage")
    colouradd = request.values.get("colour")
    countryadd = request.values.get("country")
    regionadd = request.values.get("region")
    return render_template("add_wine.html", user_name = 'User: ' + session['username'], insert=mongo.db.wines.insert_one( {"wine_name": nameadd, "vintage": vintageadd, "colour": colouradd, "country": countryadd , "region": regionadd, "grape": "", "photo_url": "", "tasting_notes": ""} ))


@app.route('/populate_form')
def populate_form():
    return render_template("add_wine.html", user_name = 'User: ' + session['username'], colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())


# Browse Wines routes
@app.route('/populate_search')
def populate_search():
    return render_template("index.html", user_name = 'User: ' + session['username'], colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())


@app.route("/search", methods=["GET", "POST"])
def search():
    namesearch = request.values.get("name")
    vintagesearch = request.values.get("vintage")
    coloursearch = request.values.get("colour")
    countrysearch = request.values.get("country")
    regionsearch = request.values.get("region")
    return render_template("index.html", results=mongo.db.wines.find({"$text": {"$search": namesearch}}))
    # return render_template("index.html", results=mongo.db.wines.find( {"$and": [ {"wine_name": namesearch}, {"vintage": vintagesearch}, {"colour": coloursearch}, {"country": countrysearch} , {"region": regionsearch} ] }))
    redirect(url_for('populate_search'))


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)