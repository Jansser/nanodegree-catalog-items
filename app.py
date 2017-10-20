from flask import Flask
from flask import render_template, redirect, url_for
from flask import request, flash, jsonify
from flask import make_response
from flask import session as login_session
from werkzeug.routing import RequestRedirect
from flask_uploads import UploadSet, IMAGES, configure_uploads
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import requests
import httplib2
import json
import os

app = Flask(__name__)

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app.config["UPLOADS_DEFAULT_DEST"] = os.getcwd() + "/static"
app.config["UPLOADS_DEFAULT_URL"] = "http://localhost:8000/static"
app.config["UPLOADS_IMAGES_DEST"] = os.getcwd() + "/static"
app.config["UPLOADS_IMAGES_URL"] = "http://localhost:8000/static"

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

CLIENT_ID = json.loads(open("client_secrets.json", "r").read())[
    "web"]["client_id"]


@app.route("/login")
def show_login():
    state = "".join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session["state"] = state
    return render_template("login.html", STATE=state)


@app.route("/gconnect", methods=["POST"])
def gconnect():
    # Validate state token
    if request.args.get("state") != login_session["state"]:
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets("client_secrets.json", scope="")
        oauth_flow.redirect_uri = "postmessage"
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps("Failed to upgrade the authorization code."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token

    url = ("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s"
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, "GET")[1])

    # If there was an error in the access token info, abort.
    if result.get("error") is not None:
        response = make_response(json.dumps(result.get("error")), 500)
        response.headers["Content-Type"] = "application/json"
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token["sub"]
    if result["user_id"] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Verify that the access token is valid for this app.
    if result["issued_to"] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers["Content-Type"] = "application/json"
        return response

    stored_credentials = login_session.get("credentials")
    stored_gplus_id = login_session.get("gplus_id")
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps("Current user is already connected."),
            200)
        response.headers["Content-Type"] = "application/json"
        return response

    # Store the access token in the session for later use.
    login_session["access_token"] = credentials.access_token
    login_session["gplus_id"] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt": "json"}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]
    login_session["email"] = data["email"]

    user_id = get_user_id(login_session["email"])

    if not user_id:
        user_id = create_user(login_session)

    login_session["user_id"] = user_id

    flash("you are now logged in as %s" %
          login_session["username"], "positive")
    return "OK"


@app.route("/gdisconnect")
def gdisconnect():
    if "access_token" not in login_session:
        flash("Current user not connected.", "negative")
        return redirect("/")

    url = ("https://accounts.google.com/o/oauth2/revoke?token=%s"
           % login_session["access_token"])
    h = httplib2.Http()

    result = h.request(url, "GET")[0]

    if result["status"] == "200":
        del login_session["access_token"]
        del login_session["gplus_id"]
        del login_session["username"]
        del login_session["email"]
        del login_session["picture"]
        del login_session["user_id"]

        flash("Successfully disconnected.", "positive")
        return redirect("/")
    else:
        flash("Failed to revoke token for given user.", "negative")
        return redirect("/")


def create_user(login_session):
    newUser = User(name=login_session["username"],
                   email=login_session["email"],
                   picture=login_session["picture"])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session["email"]).one()
    return user.id


def get_user_info(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def get_category_by_name(name):
    return session.query(Category).filter_by(name=name).first()


def current_user_is_creator_of(item):
    return item.user_id == login_session["user_id"]


def redirect_when_user_not_logged():
    try:
        if "username" not in login_session:
            raise RequestRedirect("/login")
    except KeyError:
        pass


@app.route("/")
def list():
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(
        Item.created_at.desc()).limit(10)

    return render_template("latest.html", categories=categories,
                           latest_items=latest_items)


@app.route("/catalog/<string:category_name>")
def list_category_items(category_name):
    category = get_category_by_name(category_name)
    items = []

    if category:
        items = session.query(Item).filter_by(category_id=category.id).all()

        if not items:
            flash("There are no items for " + category.name, "warning")
    else:
        flash("Category " + category_name + " doesn't exists", "negative")

    categories = session.query(Category).all()

    return render_template("catalog.html", category=category,
                           items=items,
                           categories=categories)


@app.route("/catalog/new", methods=["GET", "POST"])
def new_item():
    redirect_when_user_not_logged()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        category_id = request.form["category"]
        image_filename = ""
        url_image = ""

        image = request.files["image"]

        if image:
            image_filename = images.save(image)
            url_image = images.url(image_filename)

        if not name:
            flash("Item should have a name!", "negative")

        if not description:
            flash("Item should have a description!", "negative")

        if not category_id:
            flash("Item should have a category!", "negative")

        if not name or not description or not category_id:
            categories = session.query(Category).all()
            return render_template("form.html",
                                   item=None,
                                   categories=categories,
                                   mode="Create")

        item = Item(name=name,
                    description=description,
                    category_id=category_id,
                    image_filename=image_filename,
                    image_url=url_image,
                    user_id=login_session["user_id"])

        session.add(item)
        session.commit()
        flash("New item created!", "positive")

        return render_template("item.html", item=item)
    else:
        categories = session.query(Category).all()
        return render_template("form.html",
                               item=None,
                               categories=categories,
                               mode="Create")


@app.route("/catalog/<string:category_name>/<string:item_name>")
def show_item(category_name, item_name):
    category = get_category_by_name(category_name)

    if category:
        item = session.query(Item).filter_by(name=item_name,
                                             category_id=category.id).first()

    # Else shows a error page
    return render_template("item.html", item=item)


def delete_item_image(item):
    if item.image_filename:
        path = images.path(item.image_filename)
        os.remove(path)


@app.route("/catalog/<string:category_name>/<string:item_name>/edit",
           methods=["GET", "POST"])
def edit_item(category_name, item_name):
    redirect_when_user_not_logged()

    category = get_category_by_name(category_name)

    if category:
        item = session.query(Item).filter_by(name=item_name,
                                             category_id=category.id).first()

    if not current_user_is_creator_of(item):
        return redirect(url_for("show_item", category_name=category_name,
                                item_name=item.name))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        category_id = request.form["category"]

        if not name:
            flash("Item should have a name!", "negative")

        if not description:
            flash("Item should have a description!", "negative")

        if not category_id:
            flash("Item should have a category!", "negative")

        if not name or not description or not category_id:
            categories = session.query(Category).all()
            return render_template("form.html",
                                   item=item,
                                   categories=categories,
                                   mode="Create")

        image_filename = ""
        url_image = ""

        image = request.files["image"]

        if image:
            delete_item_image(item)

            image_filename = images.save(image)
            url_image = images.url(image_filename)

            item.image_url = url_image
            item.image_filename = image_filename

        item.name = name
        item.description = description
        item.category_id = category_id
        session.add(item)
        session.commit()
        flash("Item updated!", "positive")

        return render_template("item.html", item=item)
    else:
        categories = session.query(Category).all()

        return render_template("form.html", item=item,
                               categories=categories,
                               mode="Edit")


@app.route("/catalog/<string:category_name>/<string:item_name>/delete",
           methods=["GET", "POST"])
def delete_item(category_name, item_name):
    redirect_when_user_not_logged()
    category = get_category_by_name(category_name)

    if category:
        item = session.query(Item).filter_by(name=item_name,
                                             category_id=category.id).first()

    if not current_user_is_creator_of(item):
        return redirect(url_for("show_item", category_name=category_name,
                                item_name=item.name))

    if request.method == "POST":
        delete_item_image(item)
        session.delete(item)
        session.commit()

        flash("Item was deleted!", "positive")
        return redirect(url_for("list_category_items",
                                category_name=category_name))
    else:
        return render_template("delete.html", item=item)


"""
    JSON ENDPOINTS
"""


@app.route("/catalog.json")
def catalog_json():
    categories = session.query(Category).all()
    return jsonify(catalog=[category.serialize for category in categories])


@app.route("/<string:category_name>/catalog.json")
def catalog_category_json(category_name):
    category = session.query(Category).filter_by(name=category_name).first()

    if category:
        return jsonify(catalog=[category.serialize])
    else:
        return jsonify(message="Category not found.")


@app.route("/<string:category_name>/<string:item_name>/catalog.json")
def catalog_item_json(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).first()

    if category:
        item = session.query(Item).filter_by(
            name=item_name, category_id=category.id).first()
        if item:
            return jsonify(catalog=[item.serialize])
        else:
            return jsonify(message="Item not found.")
    else:
        return jsonify(message="Category not found.")


if __name__ == "__main__":
    app.secret_key = "slimShady"
    app.debug = True
    app.run(host="0.0.0.0", port=8000)
