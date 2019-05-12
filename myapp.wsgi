import os
from flask import Flask, render_template, url_for, \
    request, redirect, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Category, Category_Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('postgresql+psycopg2:///catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
conn = DBSession()

# create state token to prevent request forgery
# store state token in session for later validation


@app.route('/login')
def showLogin():
    # generate random state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the '
                                            'authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # if error abort login
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        response = make_response(json.dumps("Token's user id does not match "
                                            "given user id."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # verify access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match"
                                            " this application's ID."), 401)
        print "Token's client ID does not match this application."
        response.headers['Content-Type'] = 'application/json'
        return response
    # check if logged in
    stored_creds = login_session.get('credentials')
    stored_g_id = login_session.get('g_id')
    if stored_creds is not None and g_id == stored_g_id:
        response = make_response(json.dumps('Current user already signed '
                                            'in!'), 200)
        response.headers['Content-Type'] = 'application/json'
    # store access token in session
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = g_id

    # get info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius: ' \
              '150px;-webkit-border-radius: 150px;-moz-border-radius: ' \
              '150px;"> '
    flash("Success! You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# disconnect method
@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect current user
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['g_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        success = 'You have successfully disconnected from the application!'
        flash('%s' % success)
        return redirect(url_for('catalog'))
    else:
        response = make_response(json.dumps('Failed to delete session '
                                            'and revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


def getUserID(email):
    try:
        user = conn.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user= conn.query(User).filter_by(id=user_id).one()
    return user


# create a new user
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    conn.add(newUser)
    conn.commit()
    user = conn.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/')
@app.route('/catalog')
def catalog():
    cats = conn.query(Category).order_by(Category.name)
    items = conn.query(Category_Item).order_by(Category_Item.id.desc())\
        .limit(5)
    return render_template('catalog.html',
                           cats=cats,
                           items=items)


@app.route('/catalog/<int:category_id>/items',
           methods=['GET', 'POST'])
def categoryItems(category_id):
    cat = conn.query(Category).filter_by(id=category_id).one()
    cats = conn.query(Category).order_by(Category.id)
    items = conn.query(Category_Item).filter_by(category_id=category_id).all()
    itemcount = conn.query(Category_Item)\
        .filter_by(category_id=category_id).count()
    if 'username' not in login_session:
        return render_template('publicCategory.html',
                               cat=cat,
                               items=items,
                               cats=cats,
                               itemcount=itemcount)
    else:
        return render_template('category.html',
                               cat=cat,
                               items=items,
                               cats=cats,
                               itemcount=itemcount)


@app.route('/catalog/<int:category_id>/<int:item_id>/info',
           methods=['GET', 'POST'])
def categoryItem(category_id, item_id):
    item = conn.query(Category_Item).filter_by(id=item_id).one()
    cat = conn.query(Category).filter_by(id=category_id).one()
    author = getUserInfo(item.user_id)
    if 'username' not in login_session or author.id != login_session['user_id']:
        return render_template('publicItem.html',
                               item=item,
                               cat=cat,
                               category_id=category_id)
    else:
        return render_template('item.html',
                               item=item,
                               cat=cat,
                               category_id=category_id)


@app.route('/catalog/<int:category_id>/item/add', methods=['GET', 'POST'])
def addItem(category_id):
    cat = conn.query(Category).filter_by(id=category_id)
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Category_Item(name=request.form['name'],
                                description=request.form['desc'],
                                category_id=category_id,
                                user_id=login_session['user_id'])
        conn.add(newItem)
        conn.commit()
        flash("%s Added!" % newItem.name)
        return redirect(url_for('categoryItems',
                                category_id=category_id))
    else:
        return render_template('addItem.html',
                               category_id=category_id,
                               cat=cat)


@app.route('/catalog/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    itemUpdate = conn.query(Category_Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    # if user does not own item, alert and redirect
    if itemUpdate.user_id != login_session['user_id']:
        return "<script>function alertUser() {alert('You are not " \
               "authorized to make any edits to this item! " \
               "Please create your own " \
               "items to make changes!'); window.location = '/'}" \
               "</script><body onload='alertUser()'>"
    if request.method == 'POST':
        if request.form['name'] and request.form['desc']:
            itemUpdate.name = request.form['name']
            itemUpdate.description = request.form['desc']
        elif request.form['name']:
            itemUpdate.name = request.form['name']
        elif request.form['desc']:
            itemUpdate.description = request.form['desc']
        conn.add(itemUpdate)
        conn.commit()
        flash('%s updated!' % itemUpdate.name)
        return redirect(url_for('categoryItems',
                                category_id=category_id))
    else:
        return render_template('editItem.html',
                               item=itemUpdate,
                               category_id=category_id,
                               item_id=item_id)


@app.route('/catalog/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    itemToDelete = conn.query(Category_Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    # if user does not own item, alert and redirect
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function alertUser() {alert('You are not " \
               "authorized to delete this item! Please create your own " \
               "items to delete!'); window.location = '/'}" \
               "</script><body onload='alertUser()'>"
    if request.method == 'POST':
        conn.delete(itemToDelete)
        conn.commit()
        flash("Category item deleted!")
        return redirect(url_for('categoryItems',
                                category_id=category_id))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete,
                               category_id=category_id)


"""API Endpoints"""
@app.route('/api/categories')
def allCategoriesJSON():
    categories = conn.query(Category).order_by(Category.name).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/api/category/<int:category_id>/items')
def categoryItemsJSON(category_id):
    category = conn.query(Category).filter_by(id=category_id).one()
    items = conn.query(Category_Item).filter_by(category_id=category_id).all()
    return jsonify(CategoryName=category.serialize,
                   CategoryItems=[i.serialize for i in items])


@app.route('/api/category/<int:category_id>/item/<int:item_id>')
def categoryItemJSON(category_id, item_id):
    item = conn.query(Category_Item).filter_by(id=item_id).one()
    return jsonify(Category_Item=item.serialize)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.debug = True
    app.run(True, port=80)
