from flask import Flask, render_template, url_for, request, redirect, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, Items

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']


app = Flask(__name__)

engine = create_engine('sqlite:///kittycat.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

most_recent = []

@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase +
		string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

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
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
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
        response = make_response(json.dumps('Current user is already connected.'),
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

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/')
@app.route('/kittycat')
def kittycat():
	cats = session.query(Catalog).all()
	return render_template('main.html', cats = cats)

@app.route('/kittycat/JSON')
def kittycatJSON():
	cats = session.query(Catalog).all()
	return jsonify(catalogs = [cat.serialize for cat in cats])


@app.route('/kittycat/newcat', methods=['GET', 'POST'])
def newcat():
	if request.method == 'POST':
		if request.form['name']:
			newcat = Catalog(name = request.form['name'])
			session.add(newcat)
			session.commit()
			flash('NEW CAT %s IS IN THE HAUS' %request.form['name'])
			return redirect('/kittycat')
		else:
			return render_template('401.html')
	return render_template('newcat.html')

@app.route('/kittycat/<int:id>/edit', methods=['GET', 'POST'])
def editcat(id):
	cat = session.query(Catalog).filter_by(id = id).one()
	if request.method == 'POST':
		if request.form['catname']:
			cat.name = request.form['catname']
			session.add(cat)
			session.commit()
			return redirect('/kittycat')
		else:
			return render_template('401.html')
	return render_template('editcat.html', cat = cat)

@app.route('/kittycat/<int:id>/delete', methods=['GET', 'POST'])
def deletecat(id):
	cat = session.query(Catalog).filter_by(id = id).one()
	if request.method == 'POST':
		session.delete(cat)
		session.commit()
		return redirect('/kittycat')
	return render_template('deletecat.html', cat = cat)

@app.route('/kittycat/<int:id>/items')
def catitems(id):
	cat = session.query(Catalog).filter_by(id = id).one()
	items = session.query(Items).filter_by(catalog_id = id).all()
	return render_template('items.html', items = items, cat = cat)

@app.route('/kittycat/<int:id>/items/JSON')
def itemsJSON(id):
	items = session.query(Items).filter_by(catalog_id = id).all()
	return jsonify(Items=[i.serialize for i in items])


@app.route('/kittycat/<int:id>/items/new', methods=['GET', 'POST'])
def catnewitems(id):
	cat = session.query(Catalog).filter_by(id = id).one()
	if request.method == 'POST':
		if request.form['newitem'] and request.form['description']:
			new_item = Items(name = request.form['newitem'],
				description = request.form['description'],
				catalog_id = cat.id)
			session.add(new_item)
			session.commit()
			return redirect(url_for('catitems', id = cat.id))
		else:
			return render_template('401.html')
	return render_template('newitem.html', cat= cat)

@app.route('/kittycat/<int:id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def catitemedit(id, item_id):
	cat = session.query(Catalog).filter_by(id = id).one()
	item = session.query(Items).filter_by(id = item_id).one()
	if request.method == 'POST':
		if request.form['itemname']:
			item.name = request.form['itemna me']
			item.description = request.form['newdesc']
			session.add(item)
			session.commit()
			return redirect(url_for('catitems', id = cat.id))
		else:
			return render_template('401.html')
	return render_template('edititem.html', cat= cat, item= item)

@app.route('/kittycat/<int:id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def catitemdelete(id, item_id):
	cat = session.query(Catalog).filter_by(id = id).one()
	item = session.query(Items).filter_by(id = item_id).one()
	if request.method == 'POST':
		session.delete(item)
		session.commit()
		return redirect(url_for('catitems', id = cat.id))
	return render_template('deleteitem.html', cat= cat, item= item)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)

