import os
from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'CaveDuVin'
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

mongo = PyMongo(app)


@app.route('/')
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
    return render_template("index.html", results=mongo.db.wines.find( { "wine_name": namesearch } ))
    # return render_template("index.html", results=mongo.db.wines.find( {"$and": [ {"wine_name": namesearch}, {"vintage": vintagesearch}, {"colour": coloursearch}, {"country": countrysearch} , {"region": regionsearch} ] }))


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)