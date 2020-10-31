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


@app.route('/')
def index():
    if 'username' in session:
        return 'You are logged in as ' + session['username']

    return render_template('login.html')


@app.route('/login')
def login():
    return ''


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


@app.route('/populate_search')
def populate_search():
    return render_template("index.html", colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())


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


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    usernameinput = request.values.get("username")
    passwordinput = request.values.get("password")
    users = mongo.db.users
    users.insert_one({"username": usernameinput, "password": passwordinput})
    return redirect(url_for('populate_search'))


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    usernamefind = request.values.get("usernamelog")
    passwordfind = request.values.get("passwordlog")
    return render_template("index.html", logintest = mongo.db.users.find({"username": usernamefind, "password": passwordfind}))


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)