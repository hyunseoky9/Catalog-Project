from flask import Flask, render_template, url_for
from flask import request, redirect, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, Items, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(open('client_secrets.json',
							'r').read())['web']['client_id']


app = Flask(__name__)

engine = create_engine('sqlite:///kittycat.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

most_recent = []

# gives user_id when put in email from login_session
def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

# gives user object when put in user id.
def getUserInfo(user_id):
	try:
		user = session.query(User).filter_by(id=user_id).one()
	except:
		user = None
	return user

# creates user data when put in login_session data.
def createUser(login_session):
	newUser = User(name=login_session['username'],
					email=login_session['email'],
					picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	print 'NEW USER CREATED'
	return user.id


# Login page
@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase +
		string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)


# temporary page for google connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json',
        									scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
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
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is\
         already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserID(login_session['email'])
    if not user_id:
    	user = createUser(login_session)
    print 'NEW USER CREATED'

    output = '' #html for notifying successful signin.
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# temporary page for disconnecting user
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user \
        						not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2\
    /revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash('Successfully disconnected!')
        return redirect('/')
    else:
        response = make_response(json.dumps('Failed to revoke \
        									token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# main page
@app.route('/')
@app.route('/kittycat')
def kittycat():
	cats = session.query(Catalog).all()
	return render_template('main.html', cats=cats, login_session=login_session)

# JSON object for all the categories.
@app.route('/kittycat/JSON')
def kittycatJSON():
	cats = session.query(Catalog).all()
	return jsonify(catalogs=[cat.serialize for cat in cats])

# page for adding new cats.
@app.route('/kittycat/newcat', methods=['GET', 'POST'])
def newcat():
	# this if statements are found in all the pages where it creates, edits,
	# or deletes an item or a catalog. Checks if the user is logged in.
	if 'username' not in login_session:
		flash('This option requires you to log in!')
		return redirect('/login')
	if request.method == 'POST':
		if request.form['name']:
			newcat = Catalog(name=request.form['name'],
							user_id=getUserID(login_session['email']))
			session.add(newcat)
			session.commit()
			flash('NEW CAT %s IS IN THE HAUS' %request.form['name'])
			return redirect('/kittycat')
		else:
			return render_template('401.html')
	return render_template('newcat.html', login_session=login_session)

# page for editing cat names
@app.route('/kittycat/<int:id>/edit', methods=['GET', 'POST'])
def editcat(id):
	if 'username' not in login_session:
		flash('This option requires you to log in!')
		return redirect('/login')
	cat = session.query(Catalog).filter_by(id=id).one()
	# make sure the signed user is the creator of the cat.
	if getUserID(login_session['email']) != cat.user_id:
		flash('Sorry you are not authorized to edit this cat!')
		return redirect('/')
	if request.method == 'POST':
		if request.form['catname']:
			cat.name = request.form['catname']
			session.add(cat)
			session.commit()
			return redirect('/kittycat')
		else:
			return render_template('401.html')
	return render_template('editcat.html', cat=cat)

# page for deleting cats. Its items are also deleted.
@app.route('/kittycat/<int:id>/delete', methods=['GET', 'POST'])
def deletecat(id):
	if 'username' not in login_session:
		flash('This option requires you to log in!')
		return redirect('/login')
	cat = session.query(Catalog).filter_by(id=id).one()
	try:
		items = session.query(Items).filter_by(catalog_id=id).all()
	except:
		items = []

	if not items:
		print 'hey'
	else:
		print items
	if getUserID(login_session['email']) != cat.user_id:
		flash('Sorry you are not authorized to delete this cat!')
		return redirect('/')
	if request.method == 'POST':
		session.delete(cat)
		# if the cat had items, all its items, also delete its items.
		if items:
			for item in items:
				session.delete(item)
		session.commit()
		return redirect('/kittycat')
	return render_template('deletecat.html', cat=cat)

# page for items that a cat has.
@app.route('/kittycat/<int:id>/items')
def catitems(id):
	cat = session.query(Catalog).filter_by(id = id).one()
	items = session.query(Items).filter_by(catalog_id=id).all()
	return render_template('items.html', items=items, cat=cat)

# JSON object for the items of a cat.
@app.route('/kittycat/<int:id>/items/JSON')
def itemsJSON(id):
	items = session.query(Items).filter_by(catalog_id = id).all()
	return jsonify(Items=[i.serialize for i in items])

# Page for creating new item for the cat.
@app.route('/kittycat/<int:id>/items/new', methods=['GET', 'POST'])
def catnewitems(id):
	if 'username' not in login_session:
		flash('This option requires you to log in!')
		return redirect('/login')
	cat = session.query(Catalog).filter_by(id=id).one()
	if request.method == 'POST':
		if request.form['newitem'] and request.form['description']:
			new_item = Items(name=request.form['newitem'],
							description=request.form['description'],
							catalog_id=cat.id,
							user_id=getUserID(login_session['email']))
			session.add(new_item)
			session.commit()
			return redirect(url_for('catitems', id = cat.id))
		else:
			return render_template('401.html')
	return render_template('newitem.html', cat=cat)

# Page for editing an item
@app.route('/kittycat/<int:id>/items\
	/<int:item_id>/edit', methods=['GET', 'POST'])
def catitemedit(id, item_id):
	if 'username' not in login_session:
		flash('This option requires you to log in!')
		return redirect('/login')
	cat = session.query(Catalog).filter_by(id=id).one()
	item = session.query(Items).filter_by(id=item_id).one()
	if getUserID(login_session['email']) != item.user_id:
		flash('Sorry you are not authorized to edit this item!')
		return redirect('/kittycat/%s/items' % cat.id)
	if request.method == 'POST':
		if request.form['itemname']:
			item.name = request.form['itemname']
			item.description = request.form['newdesc']
			session.add(item)
			session.commit()
			return redirect(url_for('catitems', id=cat.id))
		else:
			return render_template('401.html')
	return render_template('edititem.html', cat=cat, item=item)

# Page for deleting an item
@app.route('/kittycat/<int:id>/items/<int:item_id>/delete',
			methods=['GET', 'POST'])
def catitemdelete(id, item_id):
	if 'username' not in login_session:
		flash('This option requires you to log in!')
		return redirect('/login')
	cat = session.query(Catalog).filter_by(id=id).one()
	item = session.query(Items).filter_by(id=item_id).one()
	if getUserID(login_session['email']) != item.user_id:
		flash('Sorry you are not authorized to delete this item!')
		return redirect('/kittycat/%s/items' % cat.id)
	if request.method == 'POST':
		session.delete(item)
		session.commit()
		return redirect(url_for('catitems', id=cat.id))
	return render_template('deleteitem.html', cat=cat, item=item)

# error page.
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=8000)
