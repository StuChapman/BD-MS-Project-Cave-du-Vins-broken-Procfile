import os
from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt
import re
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
from azure.core.exceptions import ResourceExistsError
from werkzeug.utils import secure_filename

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'CaveDuVin'
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["IMAGE_UPLOADS"] = "./upload_images"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]

mongo = PyMongo(app)


# Start app on index.html
@app.route('/')
def index():
    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'
    return render_template('index.html',
                           user_name=user_return,
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           results_winename="",
                           results_vintage="",
                           results_colour="",
                           results_country="",
                           results_region="",
                           results_grape=""
                           )


# Log In/Out and Register routes
@app.route('/login_page')
def login_page():
    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'
    return render_template('login.html',
                           user_name=user_return)


# Credit: https://edubanq.com/programming/mongodb/
# creating-a-user-login-system-using-python-flask-and-mongodb/
@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'),
                         login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return render_template("login.html",
                        password_error='Invalid username/password combination')


# Credit: https://pythonbasics.org/flask-sessions/
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


# Credit: https://edubanq.com/programming/mongodb/
# creating-a-user-login-system-using-python-flask-and-mongodb/
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


    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'
    return render_template('register.html',
                           user_name=user_return)

    return ''


# Add/Delete Wine routes
@app.route('/add_wine_page')
def add_wine_page():
    return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find()
                           )


# Refresh Add Wine Form route
@app.route('/populate_form')
def populate_form():
    return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find()
                           )


@app.route('/add_wine', methods=["GET", "POST"])
def add_wine():
    nameadd = request.values.get("name")
    if not any(char.islower() for char in nameadd):
        flash('wine name must be populated')
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               colours=mongo.db.colours.find(),
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find())
    vintageadd = request.values.get("vintage")
    if not all(char.isdigit() for char in vintageadd):
        flash('vintage must be 4 numerals')
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               colours=mongo.db.colours.find(),
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find())
    colouradd = request.values.get("colour")
    countryadd = request.values.get("country")
    regionadd = request.values.get("region")
    grapeadd = request.values.get("grape")
    if nameadd == "" or vintageadd == "":
        flash('all fields must be populated')
        return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find())

    # Credit: https://pythonprogramming.net/flash-flask-tutorial/
    flash("The wine has been added")
    return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           insert=mongo.db.wines.insert_one({"wine_name": nameadd.title(),
                                                             "vintage": vintageadd,
                                                             "colour": colouradd,
                                                             "country": countryadd,
                                                             "region": regionadd,
                                                             "grape": grapeadd,
                                                             "photo_url": "",
                                                             "tasting_notes": ""}
                                                            ))


@app.route('/delete_wine/<wine_id>')
def delete_wine(wine_id):
    # Credit: https://pythonprogramming.net/flash-flask-tutorial/
    flash("The wine has been deleted")
    return render_template('index.html',
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           delete=mongo.db.wines.remove({'_id': ObjectId(wine_id)})
                           )


# Add/Deleted Documents to/from Collections routes
@app.route('/add_country', methods=["GET", "POST"])
def add_country():
    countryadd = request.values.get("addcountry")
    existing_country = mongo.db.country.find_one({'country': countryadd})
    if not any(char.islower() for char in countryadd):
        flash('country must be populated')
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find())

    # Credit: https://pythonprogramming.net/flash-flask-tutorial/
    flash(countryadd + " has been added")
    if existing_country is None:
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               colours=mongo.db.colours.find(),
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find(),
                               insert=mongo.db.country.insert_one(
                                    {"country": countryadd.title()}
                                    ))
    return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           )


@app.route('/add_region', methods=["GET", "POST"])
def add_region():
    regionadd = request.values.get("addregion")
    existing_region = mongo.db.region.find_one({'region': regionadd})
    if not any(char.islower() for char in regionadd):
        flash('region must be populated')
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find())

    # Credit: https://pythonprogramming.net/flash-flask-tutorial/
    flash(regionadd + " has been added")
    if existing_region is None:
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               colours=mongo.db.colours.find(),
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find(),
                               insert=mongo.db.region.insert_one(
                                    {"region": regionadd.title()}
                                    ))
    return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           )


@app.route('/add_grape', methods=["GET", "POST"])
def add_grape():
    grapeadd = request.values.get("addgrape")
    existing_grape = mongo.db.grape.find_one({'grape': grapeadd})
    if not any(char.islower() for char in grapeadd):
        flash('grape must be populated')
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find())

    # Credit: https://pythonprogramming.net/flash-flask-tutorial/
    flash(grapeadd + " has been added")
    if existing_grape is None:
        return render_template("add_wine.html",
                               user_name='User: ' + session['username'],
                               colours=mongo.db.colours.find(),
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find(),
                               insert=mongo.db.grape.insert_one(
                                    {"grape": grapeadd.title()}
                                    ))
    return render_template("add_wine.html",
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           )


@app.route('/delete_category_page/<category_id>')
def delete_category_page(category_id):
    return render_template('categories.html',
                           category_id=category_id,
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           )


@app.route('/delete_category/<category_id>', methods=["GET", "POST"])
def delete_category(category_id):
    category = request.values.get("category")

    # Credit: https://pythonprogramming.net/flash-flask-tutorial/
    flash(category + " has been deleted")
    if category_id == "country":
        return render_template('categories.html',
                               user_name='User: ' + session['username'],
                               country=mongo.db.country.find(),
                               category_id="country",
                               delete=mongo.db.country.delete_one({'country': category}))
    if category_id == "region":
        return render_template('categories.html',
                               user_name='User: ' + session['username'],
                               region=mongo.db.region.find(),
                               category_id="region",
                               delete=mongo.db.region.delete_one({'region': category}))
    if category_id == "grape":
        return render_template('categories.html',
                               user_name='User: ' + session['username'],
                               grape=mongo.db.grape.find(),
                               category_id="grape",
                               delete=mongo.db.grape.delete_one({'grape': category}))


# Browse Wines routes
@app.route('/search_page')
def search_page():
    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'
    return render_template('index.html',
                           user_name=user_return,
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           results_winename="",
                           results_vintage="",
                           results_colour="",
                           results_country="",
                           results_region="",
                           results_grape=""
                           )


@app.route('/populate_search')
def populate_search():
    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'
    return render_template("index.html",
                           user_name=user_return,
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           results_winename="",
                           results_vintage="",
                           results_colour="",
                           results_country="",
                           results_region="",
                           results_grape=""
                           )


@app.route("/search", methods=["GET", "POST"])
def search():
    # Credit: https://stackoverflow.com/questions/55617412/
    # how-to-perform-wildcard-searches-mongodb-in-python-with-pymongo
    if request.values.get("name") == "":
        namesearch = ".*.*"
        resultname = ""
    else:
        namesearch = request.values.get("name")
        resultname = namesearch

    if request.values.get("vintage") == "":
        vintagesearch = {'$regex': '.*'}
        resultvintage = ""
    else:
        vintagesearch = request.values.get("vintage")
        resultvintage = vintagesearch

    if request.values.get("colour") == "":
        coloursearch = {'$regex': '.*'}
        resultcolour = ""
    else:
        coloursearch = request.values.get("colour")
        resultcolour = coloursearch

    if request.values.get("country") == "":
        countrysearch = {'$regex': '.*'}
        resultcountry = ""
    else:
        countrysearch = request.values.get("country")
        resultcountry = countrysearch

    if request.values.get("region") == "":
        regionsearch = {'$regex': '.*'}
        resultregion = ""
    else:
        regionsearch = request.values.get("region")
        resultregion = regionsearch

    if request.values.get("grape") == "":
        grapesearch = {'$regex': '.*'}
        resultgrape = ""
    else:
        grapesearch = request.values.get("grape")
        resultgrape = grapesearch

    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'

    results_string = resultname + resultvintage + resultcolour + resultcountry + resultregion + resultgrape

    if results_string == "":
        return render_template("index.html",
                               user_name=user_return,
                               colours=mongo.db.colours.find(),
                               country=mongo.db.country.find(),
                               region=mongo.db.region.find(),
                               grape=mongo.db.grape.find(),
                               results_winename=resultname,
                               results_vintage=resultvintage,
                               results_colour=resultcolour,
                               results_country=resultcountry,
                               results_region=resultregion,
                               results_grape=resultgrape
                               )
    return render_template("index.html",
                           results=mongo.db.wines.find(
                                {"$and": [{"$or": [
                                    # Credit: https://stackoverflow.com/
                                    # questions/55617412/how-to-perform-wildcard
                                    # -searches-mongodb-in-python-with-pymongo
                                    {'wine_name': {'$regex': '.*' + namesearch + '.*'}},
                                    {'wine_name': {'$regex': '.*' + namesearch.title() + '.*'}}]},
                                    {"vintage": vintagesearch},
                                    {"colour": coloursearch},
                                    {"country": countrysearch},
                                    {"region": regionsearch},
                                    {"grape": grapesearch}
                                    ]}),
                           user_name=user_return,
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           results_winename=resultname,
                           results_vintage=resultvintage,
                           results_colour=resultcolour,
                           results_country=resultcountry,
                           results_region=resultregion,
                           results_grape=resultgrape
                           )


# Add tasting Note Routes
@app.route('/add_tasting_note_page/<wine_id>')
def add_tasting_note_page(wine_id):
    the_wine = mongo.db.wines.find_one({"_id": ObjectId(wine_id)})
    return render_template('add_tasting_note.html',
                           wine=the_wine,
                           user_name='User: ' + session['username'],
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find()
                           )


@app.route('/add_tasting_note', methods=["GET", "POST"])
def add_tasting_note():
    tastingnoteadd = request.values.get("add_tasting_note")
    wineid = request.values.get("wine_id")
    return render_template("index.html",
        user_name='User: ' + session['username'],
        colours=mongo.db.colours.find(),
        country=mongo.db.country.find(),
        region=mongo.db.region.find(),
        grape=mongo.db.grape.find(),
        results_winename="",
        results_vintage="",
        results_colour="",
        results_country="",
        results_region="",
        results_grape="",
        update=mongo.db.wines.update({'_id': ObjectId(wineid)},
                                     # Credit: https://stackoverflow.com/questions/10290621/
                                     # how-do-i-partially-update-an-object-in-mongodb-so-the-new-
                                     # object-will-overlay
                                     {"$set": {'tasting_notes': tastingnoteadd}}),
                                     results=mongo.db.wines.find({'_id': ObjectId(wineid)}))


# Upload Image
@app.route('/upload_image_page/<wine_id>')
def upload_image_page(wine_id):
    the_wine = mongo.db.wines.find_one({"_id": ObjectId(wine_id)})
    return render_template('image_upload.html',
                           wine=the_wine,
                           user_name='User: ' + session['username']
                           )

# Check For Image Extension
def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


# Upload Image
@app.route('/upload_image/<wine_id>', methods=["GET", "POST"])
def upload_image(wine_id):
    # Credit: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python

    # Retrieve the connection string for use with the application. The storage
    # connection string is stored in an environment variable on the machine
    # running the application called AZURE_STORAGE_CONNECTION_STRING. If the environment variable is
    # created after the application is launched in a console or with Visual Studio,
    # the shell or application needs to be closed and reloaded to take the
    # environment variable into account.

    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

    # Get the user unput image file Credit: https://pythonise.com/series/learning-flask/flask-uploading-files
    if request.method == "POST":
        if request.files:
            image = request.files["filename"]
            if image.filename == "":
                the_wine = mongo.db.wines.find_one({"_id": ObjectId(wine_id)})
                return render_template('image_upload.html',
                                       wine=the_wine,
                                       upload_error='No image selected',
                                       user_name='User: ' + session['username']
                                       )

            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
            else:
                print("That file extension is not allowed")
                the_wine = mongo.db.wines.find_one({"_id": ObjectId(wine_id)})
                return render_template('image_upload.html',
                                       wine=the_wine,
                                       upload_error='Incorrect file type selected - must be: "JPEG", "JPG", "PNG" or "GIF"',
                                       user_name='User: ' + session['username']
                                       )

    # Get static file and save to upload_images directory to upload
    local_path = "./upload_images"
    local_file_name = filename
    upload_file_path = os.path.join(local_path, local_file_name)

    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Set the name for the container
    container_name = "caveduvins"
    container_client = ContainerClient.from_connection_string(conn_str=connect_str, container_name=container_name)

    # Set the upload file name
    upload_file_name = wine_id + str(uuid.uuid4()) + ".jpg"

    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=upload_file_name)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)

    # Delete the file from upload_images directory
    os.remove(upload_file_path)

    # create a url for the image
    image_url = "https://mystorageacct180671.blob.core.windows.net/" + container_name + "/" + upload_file_name
    wineid = wine_id

    flash("Image uploaded")

    if 'username' in session:
        user_return = 'User: ' + session['username']
    else:
        user_return = 'Cave du Vins'

    return render_template("index.html", 
                           update=mongo.db.wines.update({'_id': ObjectId(wineid)},
                           # Credit: https://stackoverflow.com/questions/10290621/
                           # how-do-i-partially-update-an-object-in-mongodb-so-the-new-
                           # object-will-overlay
                           {"$set": {'photo_url': image_url}}),
                           user_name=user_return,
                           colours=mongo.db.colours.find(),
                           country=mongo.db.country.find(),
                           region=mongo.db.region.find(),
                           grape=mongo.db.grape.find(),
                           results_winename="",
                           results_vintage="",
                           results_colour="",
                           results_country="",
                           results_region="",
                           results_grape="",
                           results=mongo.db.wines.find({'_id': ObjectId(wineid)})
                           )


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)
