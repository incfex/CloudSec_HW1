import datetime
import json
import hashlib
import secrets
import itertools
import os
import requests
import base64
from urllib.request import urlretrieve
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, Response, jsonify, send_from_directory, make_response, escape
from google.cloud import datastore

app = Flask(__name__)

DS = datastore.Client()
EVENT = 'event'
USER = 'user'
TOKEN = 'token'
ROOT = DS.key('Entities', 'root')
CLIENT_ID = '767668373655-aki39ngsk8o04a5n6mlqa92co00q64b0.apps.googleusercontent.com'
REDIRECT_DEV = 'http://127.0.0.1:8080/oidcauth'
REDIRECT_PRO = 'https://tensile-axiom-228621.du.r.appspot.com/oidcauth'
REDIRECT_URI = REDIRECT_PRO


def stretch(input):
    return hashlib.pbkdf2_hmac('sha256', input.encode('utf-8'), b'sugar',
                               100).hex()


@app.route("/error/<message>", methods=["GET"])
def print_err(message):
    return render_template('error.html', err_msg=message)


def query_usr(username):
    # query the user based on username
    usr_query = DS.query(kind=USER, ancestor=ROOT)
    usr_query.add_filter('username', '=', username)
    lst_iter = usr_query.fetch()
    # Duplicate the iterator
    lst_it, rtn_it = itertools.tee(lst_iter)
    # See how many user entities were found, if found, return iterator
    lst_usr = list(lst_it)
    if len(lst_usr) == 0:
        return 0
    elif len(lst_usr) == 1:
        return rtn_it
    else:
        return -1


def gen_sec(username):
    # Generate token
    token = secrets.token_urlsafe()
    # Create complete key for upsert
    key = DS.key('token', username, parent=ROOT)
    entity = datastore.Entity(key=key)
    entity.update({'username': username, 'secret': token})
    # Upsert the token
    DS.put(entity)
    return token


def get_sec(username=None, secret=None):
    tok_query = DS.query(kind=TOKEN, ancestor=ROOT)

    # Add filter based on which parameter given
    if username is not None:
        tok_query.add_filter('username', '=', username)
    elif secret is not None:
        tok_query.add_filter('secret', '=', secret)

    # Get and return the first entry of token
    tok_iter = iter(tok_query.fetch())
    tok_db = next(tok_iter, None)
    if tok_db is not None:
        return tok_db
    return None


def verify_token(req):
    # Get token from request
    token_in = req.cookies.get('session')
    if token_in is None:
        return 0

    # Get token from db
    token_db = get_sec(secret=token_in)
    if token_db is None:
        return 0

    # Compare the tokens
    if token_db['secret'] == token_in:
        return token_db

    return 0


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # Get info from the form
    req = request.form
    username = req.get('username')
    password = req.get('password')
    hashed_pass = stretch(password)

    # Query iterator for current user
    usr_itr = query_usr(username)
    if usr_itr == 0:
        # Register the user to db
        entity = datastore.Entity(key=DS.key(USER, parent=ROOT))
        entity.update({'username': username, 'password': hashed_pass})
        DS.put(entity)
    elif usr_itr == -1:
        return 'Weird!!!'
    else:
        return redirect('/error/User_already_exist')

    # Generate new token
    token = gen_sec(username)

    # Set the cookie and redirect user
    resp = make_response(redirect('/'))
    resp.set_cookie("session", token)
    return resp


def get_client_secret(client_id):
    secret = DS.get(DS.key('secret', 'oidc'))['client-secret']
    return secret


@app.route("/oidcauth", methods=["GET"])
def oidcauth():
    code = request.args['code']
    state = request.args['state']

    # Check state token
    if state != request.cookies.get('oidc_state', None):
        return redirect('/error/State_does_not_match')

    response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token", {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": get_client_secret(CLIENT_ID),
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        })

    # Extract JWT token
    id_token = response.json().get('id_token')
    _, body, _ = id_token.split('.')
    body += '=' * (-len(body) % 4)
    claims = json.loads(base64.urlsafe_b64decode(body.encode('utf-8')))

    # Check nonce
    if claims.get('nonce') != request.cookies.get('nonce'):
        return redirect('/error/Nonce_does_not_match')

    # Login/Register process
    username = claims.get('sub')
    usr_itr = query_usr(username)
    if usr_itr == 0:
        # Register the user to db
        entity = datastore.Entity(key=DS.key(USER, parent=ROOT))
        entity.update({
            'username': username,
            'email': claims.get('email', 'Error_Suppress')
        })
        DS.put(entity)
    elif usr_itr == -1:
        return 'Weird!!!'

    # Generate new token
    token = gen_sec(username)

    # Set the cookie and redirect user
    resp = make_response(redirect('/'))
    resp.set_cookie("session", token)
    # Clean up CSRF cookies, comment out for cookie debugging
    resp.set_cookie("oidc_state", '')
    resp.set_cookie("nonce", '')
    return resp


@app.route("/login", methods=["GET", "POST"])
def log_in():
    if request.method == 'GET':
        oidc_state = hashlib.sha256(os.urandom(1024)).hexdigest()
        nonce = hashlib.sha256(os.urandom(1024)).hexdigest()
        params = urlencode({
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'scope': 'openid email',
            'state': oidc_state,
            'nonce': nonce,
            'redirect_uri': REDIRECT_URI
        })
        g_link = "https://accounts.google.com/o/oauth2/v2/auth?%s" % params

        resp = make_response(render_template('login.html', google_login=g_link))
        resp.set_cookie("oidc_state", oidc_state)
        resp.set_cookie("nonce", nonce)
        return resp

    # Get info from the form
    req = request.form
    username = req.get('username')
    password = req.get('password')
    hashed_pass = stretch(password)

    # Query iterator for current user
    usr_itr = query_usr(username)
    if usr_itr == 0:
        return redirect('/error/User_not_found')
    elif usr_itr == -1:
        return 'Weird!!!'

    # Compare stretched password
    if hashed_pass != next(usr_itr)['password']:
        return redirect('/error/Wrong_password')

    # Generate new token and push to database
    token = gen_sec(username)

    # Set the cookie and redirect user
    resp = make_response(redirect('/'))
    resp.set_cookie("session", token)
    return resp


@app.route("/logout", methods=["POST"])
def log_out():
    # Get the username based on token
    tok_db = get_sec(secret=request.cookies.get('session'))
    if tok_db is not None:
        # Generate a new token for that user, thus invalid the previous one
        gen_sec(tok_db['username'])
    return redirect('/login')


@app.route("/event", methods=["POST"])
def add_event():
    if verify_token(request) == 0:
        return redirect('/login')
    username = get_sec(secret=request.cookies.get('session'))['username']
    parent_key = DS.key(USER, username)
    # Since context_type is not set on client side, force request to think context is json
    req = request.get_json(force=True)
    # extract event name and time from payload
    e_name = req["name"]
    e_time = req["time"]
    # create entry for datastore
    entity = datastore.Entity(key=DS.key(EVENT, parent=parent_key))
    entity.update({'name': e_name, 'time': e_time})
    # upload
    DS.put(entity)

    return ''


@app.route("/events", methods=["GET"])
def get_event():
    if verify_token(request) == 0:
        return redirect('/login')
    username = get_sec(secret=request.cookies.get('session'))['username']
    parent_key = DS.key(USER, username)
    # set rule for query
    query = DS.query(kind=EVENT, ancestor=parent_key)
    query.order = ['-time']
    # make query
    events = query.fetch()
    # contrust response that have entity_id, name, and time
    payload = []
    for val in events:
        pl = {'id': val.id, 'name': val['name'], 'time': val['time']}
        payload.append(pl)
    # send payload
    return jsonify(payload)


@app.route('/event/<int:event_id>', methods=['DELETE'])
def del_event(event_id):
    if verify_token(request) == 0:
        return redirect('/login')
    username = get_sec(secret=request.cookies.get('session'))['username']
    parent_key = DS.key(USER, username)
    # delete from datastore based on event_id
    DS.delete(DS.key(EVENT, event_id, parent=parent_key))
    return ''


@app.route('/')
def root():
    if verify_token(request) == 0:
        return redirect('/login')
    return render_template('index.html')


""" The following function are used to migrate
It basically get all the events, add them to the new user's children, then delete"""
#@app.route('/migrate')
#def migrate_data():
#    if verify_token(request) == 0:
#        return redirect('/login')
#    username = get_sec(secret=request.cookies.get('session'))['username']
#    parent_key = DS.key(USER, username)
#    query = DS.query(kind=EVENT, ancestor=ROOT)
#    query.order = ['-time']
#    # make query
#    events = query.fetch()
#    # contrust response that have entity_id, name, and time
#    for val in events:
#        entity = datastore.Entity(key=DS.key(EVENT, parent=parent_key))
#        entity.update({'name': val['name'], 'time': val['time']})
#        DS.put(entity)
#        DS.delete(DS.key(EVENT, val.id, parent=ROOT))
#
#    return redirect('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)