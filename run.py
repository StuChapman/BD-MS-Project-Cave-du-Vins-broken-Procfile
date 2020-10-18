import os
from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'CaveDuVin'
app.config["MONGO_URI"] = 'mongodb+srv://root:r00tUser@cluster0.5zsef.mongodb.net/CaveDuVin?retryWrites=true&w=majority'

mongo = PyMongo(app)


@app.route('/')
@app.route('/populate_search')
def populate_search():
    return render_template("index.html", colours=mongo.db.colours.find(), country=mongo.db.country.find(), region=mongo.db.region.find())


@app.route('/filter_region')
def filter_region():
    return render_template("index.html", region=mongo.db.region.find("country: France"))


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)