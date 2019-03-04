#!/usr/bin/env python

from db_setup import Base, User, Category, Item
from flask import Flask, render_template, redirect, url_for
from flask import jsonify, request, abort, g, make_response, flash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy import create_engine
from flask import session as login_session
import random, string, json, requests, httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps


app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(open(
            '/var/www/FlaskApp/FlaskApp/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Item Catalog'


#########
# Login #
#########

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)


@app.route('/gconnect', methods = ['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope = '')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
                    'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
            % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
                    "Token's user ID doesn't match given ID."), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
                    "Token's Client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                    'Current user is already connected.'), 200)
        response.headers['Content-type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params = params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1 style="color: white;">Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 100px; height: 100px; border-radius: 50px;">'
    flash("You're now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
                    'Current user not connected.'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-type'] = 'application/json'
        return redirect(url_for('catalog'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps(
                    'Failed to revoke token for given user.'), 400)
        response.headers['Content-type'] = 'application/json'
        return response


#########################
# User Helper Functions #
#########################

# Create a new user
def createUser(login_session):
    newUser = User(username = login_session['username'],
                   email = login_session['email'],
                   picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).first()
    return user.id


# Get user info via user_id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).first()
    return user


# Get user id via email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).first()
        return user.id
    except:
        return None


# Login decorater
def login_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You must log in first to access this page.")
            return redirect('/login')
    return decorated_func


# Show catalog
@app.route('/')
@app.route('/catalog')
def catalog():
    categories = session.query(Category).order_by(Category.name)
    items = session.query(Item).order_by(Item.id.desc())
    if 'username' not in login_session:
        return render_template('publiccatalog.html',
                                categories = categories,
                                items = items)
    else:
        return render_template('catalog.html',
                                categories = categories,
                                items = items)


# Create a new category
@app.route('/catalog/new/', methods = ['GET', 'POST'])
@login_required
def newCategory():
    if request.method == 'POST':
        if not request.form['name']:
            flash('Category must have a name.')
        if request.form['name']:
            if session.query(Category).filter_by(
                name = request.form['name']).count() > 0:
                flash('This category already exists. Please create a new one.')
            else:
                newCategory = Category(name = request.form['name'],
                                       user_id = login_session['user_id'])
                session.add(newCategory)
                session.commit()
                flash('New Category %s Successfully Created!'
                        % newCategory.name)
                return redirect(url_for('catalog'))
    return render_template('newcategory.html')


# Edit a category
@app.route('/catalog/<string:category_name>/edit/', methods = ['GET', 'POST'])
@login_required
def editCategory(category_name):
    editedCategory = session.query(Category).filter_by(
                        name = category_name).first()
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if not request.form['name']:
            flash('Please enter a new category name.')
        if request.form['name']:
            if session.query(Category).filter_by(
                    name = request.form['name']).count() > 0:
                flash('Category name already exists. Please choose a different name.')
            else:
                editedCategory.name = request.form['name']
                session.add(editedCategory)
                session.commit()
                flash('Category Successfully Edited!')
                return redirect(url_for('catalog'))
    return render_template('editcategory.html',
                            category_name = category_name,
                            category = editedCategory)


# Delete a category
@app.route('/catalog/<string:category_name>/delete/', methods = ['GET', 'POST'])
@login_required
def deleteCategory(category_name):
    categoryToDelete = session.query(Category).filter_by(
        name = category_name).first()
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category. Please create your own category in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('%s Successfully Deleted!' % categoryToDelete.name)
        return redirect(url_for('catalog'))
    else:
        return render_template('deletecategory.html',
                                category_name = category_name,
                                category = categoryToDelete)


# Show all the items of a given category
@app.route('/catalog/<string:category_name>/')
@app.route('/catalog/<string:category_name>/items')
def showItems(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name = category_name).first()
    items = session.query(Item).filter_by(category = category).all()
    itemCount = session.query(Item).filter_by(category = category).count()

    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitems.html',
                                items = items,
                                category_name = category_name,
                                category = category,
                                categories = categories,
                                count = itemCount)
    else:
        return render_template('items.html',
                                items = items,
                                category_name = category_name,
                                category = category,
                                categories = categories,
                                count = itemCount)


# Show information of a given item
@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItemInfo(category_name, item_name):
    category = session.query(Category).filter_by(name = category_name).first()
    item = session.query(Item).filter_by(category = category,
                                         name = item_name).first()
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publiciteminfo.html',
                                item = item,
                                category = category,
                                item_name = item_name,
                                category_name = category_name)
    else:
        return render_template('iteminfo.html',
                                item = item,
                                category = category,
                                item_name = item_name,
                                category_name = category_name)


# Create a new item
@app.route('/catalog/<string:category_name>/new', methods = ['GET', 'POST'])
@login_required
def newItem(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name = category_name).first()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        category = session.query(Category).filter_by(
                    name = request.form['category']).first()
        newItem = Item(name = request.form['name'],
                       description = request.form['description'],
                       category = category,
                       user_id = category.user_id)
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Created!' % newItem.name)
        return redirect(url_for('showItems', category_name = category_name))
    else:
        return render_template('newitem.html',
                                category_name = category_name,
                                categories = categories)


# Edit an item
@app.route('/catalog/<string:category_name>/<string:item_name>/edit/',
            methods = ['GET', 'POST'])
@login_required
def editItem(category_name, item_name):
    category = session.query(Category).filter_by(name = category_name).first()
    editedItem = session.query(Item).filter_by(name = item_name).first()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if not request.form['name'] or not request.form['description']:
            flash('Nothing has changed.')
        else:
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']

            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited!')

        return redirect(url_for('showItems', category_name = category_name))
    else:
        return render_template('edititem.html',
                                category_name = category_name,
                                item_name = item_name,
                                item = editedItem)


# Delete an item
@app.route('/catalog/<string:category_name>/<string:item_name>/delete/',
            methods = ['GET', 'POST'])
@login_required
def deleteItem(category_name, item_name):
    category = session.query(Category).filter_by(name = category_name).first()
    itemToDelete = session.query(Item).filter_by(name = item_name,
                                                 category = category).first()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own item in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted!')
        return redirect(url_for('showItems', category_name = category_name))
    else:
        return render_template('deleteitem.html',
                                category_name = category_name,
                                item_name = item_name,
                                item = itemToDelete)


#############
# JSON APIs #
#############

# View catalog information
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(catalog=[c.serialize for c in categories])

# View items of a given category
@app.route('/catalog/<string:category_name>/items/JSON')
def catItemsJSON(category_name):
    category = session.query(Category).filter_by(name = category_name).first()
    items = session.query(Item).filter_by(category = category).all()
    return jsonify(items=[i.serialize for i in items])


# View a given item
@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def itemJSON(category_name, item_name):
    category = session.query(Category).filter_by(name = category_name).first()
    item = session.query(Item).filter_by(
              category = category, name = item_name).first()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=8000, debug = True, threaded = False)
