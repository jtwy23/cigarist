import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

# Gets DB Name
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
# Connection to DB
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# Secret Key
app.secret_key = os.environ.get("SECRET_KEY")

# Creating Mongo App
mongo = PyMongo(app)


@app.route("/")
@app.route("/get_cigars")
def get_cigars():
    # Displays all posts
    tastingNotes = mongo.db.tastingNotes.find()
    return render_template("cigar_posts.html", tastingNotes=tastingNotes)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    # Checks if the search returns 0
    tastingNotes_count = (
        mongo.db.tastingNotes.count_documents({"$text": {"$search": query}}))

    print(f"Count: {tastingNotes_count}")
    # If no results flash message
    if tastingNotes_count == 0:
        flash("No Posts Found")
        return redirect(url_for("get_cigars"))
    # Display posts if there is a result
    tastingNotes = mongo.db.tastingNotes.find({"$text": {"$search": query}})
    result = mongo.db.tastingNotes.count({"$text": {"$search": query}})
    return render_template(
        "cigar_posts.html", tastingNotes=tastingNotes,
        result=result, tastingNotes_count=tastingNotes_count)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            # Takes user back to register page
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        # New users added to DB
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("You are registered")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                # If correct flash message
                flash("Hello, {}".format(
                    request.form.get("username")))
                # Open up into users profile page
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # If user name or password in incorrect flash message
                flash("Your Username and/or Passward is incorrect.")
                return redirect(url_for("login"))

        else:
            # If user name or password in incorrect flash message
            flash("Your Username and/or Passward is incorrect.")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    # stops users from getting on to other users profile
    try:
        if session["user"]:
            # Lists users own posts
            tastingNotes = list(
                mongo.db.tastingNotes.find({"created_by": session["user"]}))
            return render_template(
                "profile.html", username=session["user"],
                tastingNotes=tastingNotes)
    except:
        flash("You must login to view your profile!")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # When user logs out
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_post", methods=["GET", "POST"])
def add_post():
    try:
        # User posts
        if request.method == "POST":
            tastingNotes = {
                "cigarImage": request.form.get("cigarImage"),
                "cigarBrand": request.form.get("cigarBrand"),
                "vitola": request.form.get("vitola"),
                "ringGauge": request.form.get("ringGauge"),
                "handMade": request.form.get("handMade"),
                "cigarStrength": request.form.get("cigarStrength"),
                "cigarDraw": request.form.get("cigarDraw"),
                "cigarFlavour": request.form.get("cigarFlavour"),
                "cigarAroma": request.form.get("cigarAroma"),
                "cigarBurn": request.form.get("cigarBurn"),
                "price": request.form.get("price"),
                "notes": request.form.get("notes"),
                "created_by": session["user"]
            }
            # Added into db
            mongo.db.tastingNotes.insert_one(tastingNotes)
            flash("You Have Made A Post!")
            return redirect(url_for("profile"))

        return render_template("add_post.html")
    except:
        flash("You must login to post!")
        return redirect(url_for("login"))


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    # Allows users to submit edits and populates the current edit information
    if request.method == "POST":
        submit = {
            "cigarImage": request.form.get("cigarImage"),
            "cigarBrand": request.form.get("cigarBrand"),
            "vitola": request.form.get("vitola"),
            "ringGauge": request.form.get("ringGauge"),
            "handMade": request.form.get("handMade"),
            "cigarStrength": request.form.get("cigarStrength"),
            "cigarDraw": request.form.get("cigarDraw"),
            "cigarFlavour": request.form.get("cigarFlavour"),
            "cigarAroma": request.form.get("cigarAroma"),
            "cigarBurn": request.form.get("cigarBurn"),
            "price": request.form.get("price"),
            "notes": request.form.get("notes"),
            "created_by": session["user"]
        }
        # Edited posts added to DB
        mongo.db.tastingNotes.update({"_id": ObjectId(post_id)}, submit)
        flash("Your Post is Updated!")
        return redirect(url_for("profile"))

    tastingNotes = mongo.db.tastingNotes.find_one(
        {"_id": ObjectId(post_id)})
    return render_template("edit_post.html", tastingNotes=tastingNotes)


@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    # Finds the correct ID and deletes post
    mongo.db.tastingNotes.remove({"_id": ObjectId(post_id)})
    flash("Your post has been removed")
    return redirect(url_for("profile"))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")), debug=False)
