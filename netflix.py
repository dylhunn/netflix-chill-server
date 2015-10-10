import os

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy

from splinter import Browser

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]

# BEGIN BACKEND DATABASE IMPLEMENTATION

db = SQLAlchemy(app)

class User(db.Model):
  __tablename__ = 'users'
  user_id = db.Column(db.Integer, primary_key=True)
  netflix_username = db.Column(db.String(80), unique=True)
  netflix_password = db.Column(db.String(80))

def add_user(nf_un, nf_pw):
  new_user = User()
  new_user.netflix_username = nf_un
  new_user.netflix_password = nf_pw
  db.session.add(new_user)
  db.session.commit()

def get_user_by_username(nf_un):
  return User.query.filter_by(netflix_username=nf_un).all()

def get_user_by_id(nf_id):
  return User.query.filter_by(user_id=nf_id).all()

def verify_netflix_credentials(nf_un, nf_pw):
  BROWSER_DRIVER = 'chrome'
  NETLFIX_LOGIN_URL = 'https://www.netflix.com/Login?locale=en-US'
  NETFLIX_SUCCESS_URL = 'http://www.netflix.com/browse'
  EMAIL_FIELD_ID = 'email'
  PASSWORD_FIELD_ID = 'password'
  SIGN_IN_BUTTON_ID = 'login-form-contBtn'
  with Browser() as browser: 
    browser.visit(NETLFIX_LOGIN_URL)
    browser.fill(EMAIL_FIELD_ID, nf_un)
    browser.fill(PASSWORD_FIELD_ID, nf_pw)
    browser.find_by_id(SIGN_IN_BUTTON_ID).click()
    if browser.url == NETFLIX_SUCCESS_URL:
      print 'Netflix login valid.'
      return True
    else:
      print 'Netflix login invalid.'
      return False

def user_exists(nf_un, fb_un):
  return (User.query.filter_by(netflix_username=nf_un, facebook_username=fb_un).count() != 0)

def get_viewing_activity(user_id):
  NETFLIX_VIEWING_ACTIVITY_URL = 'https://www.netflix.com/WiViewingActivity'

# BEGIN API

@app.route('/')
def index():
  return 'Netflix and Chill API'

@app.route('/sign-in', methods=['POST'])
def sign_in():
  INVALID_NETFLIX_CREDENTIALS = -1
  nf_un = request.args.get('nfun') 
  nf_pw = request.args.get('nfpw')
  # Case 1: User exists
  if user_exists(nf_un, nf_pw):
    print get_user_by_username(nf_un)
  # Case 2: User doesn't exist, but has valid credentials
  if verify_netflix_credentials(nf_un, nf_pw):
    add_user(nf_un, nf_pw)
    print get_user_by_username(nf_un)
  # Case 3: User doesn't exist, and has invalid credentials
  else:
    return INVALID_NETFLIX_CREDENTIALS

if __name__ == "__main__":
  app.run()

  #app.run()