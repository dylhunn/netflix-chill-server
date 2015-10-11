import os
import json
import datetime

from flask import Flask, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

from splinter import Browser

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://hbrvgdoavvrkzy:97AbqwFr_7XFVq1paXIOi0Xl_Y@ec2-54-225-201-25.compute-1.amazonaws.com:5432/d92htefnn65sr'

# BEGIN BACKEND DATABASE IMPLEMENTATION

db = SQLAlchemy(app)

class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer(), nullable=False, primary_key=True, unique=True, autoincrement=True)
  netflix_username = db.Column(db.String(80), unique=True)
  netflix_password = db.Column(db.String(80))

  def __init__(self, username, password):
    self.netflix_username = username
    self.netflix_password = password

def add_user(nf_un, nf_pw):
  new_user = User(nf_un, nf_pw)
  db.session.add(new_user)
  db.session.flush()
  db.session.commit()
  print 'User added successfully.'
  print 'User ID:', new_user.id
  return new_user.id

def get_user_by_username(nf_un):
  if len(User.query.filter_by(netflix_username=nf_un).all()) == 0:
    return None
  else:
    return User.query.filter_by(netflix_username=nf_un).all()[0]

def get_user_by_id(nf_id):
  return User.query.filter_by(user_id=nf_id).all()

def user_exists(nf_un):
  return (len(User.query.filter_by(netflix_username=nf_un).all()) != 0)

class ChillRequest(db.Model):
  __tablename__ = 'chill_requests'
  id = db.Column(db.Integer(), nullable=False, primary_key=True, unique=True, autoincrement=True)
  #id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  genre = db.Column(db.String(20))
  program_type = db.Column(db.Boolean())
  date = db.Column(db.Date())
  time_of_day = db.Column(db.String(20))
  latitude = db.Column(db.Float())
  longitude = db.Column(db.Float())

  def __init__(self, user_id, genre, program_type, date, time_of_day, latitude, longitude):
    self.user_id = user_id
    self.genre = genre
    self.program_type = program_type
    self.date = date
    self.time_of_day = time_of_day
    self.latitude = latitude
    self.longitude = longitude

def add_chill_request(user_id, genre, program_type, date, time_of_day, latitude, longitude):
  new_request = ChillRequest(user_id, genre, program_type, date, time_of_day, latitude, longitude)
  db.session.add(new_request)
  db.session.flush()
  print 'New Request:', new_request
  db.session.commit()
  print 'Chill Request added successfully.'
  return new_request.id

def get_chill_request_by_id(cr_id):
  requests = ChillRequest.query.filter_by(id=cr_id).all()
  if len(requests) == 0:
    return None
  else:
    return requests[0].id


def chill_request_exists(cr_id):
  return (len(ChillRequest.query.filter_by(id=cr_id).all()) != 0)

def verify_netflix_credentials(nf_un, nf_pw):
  """
  Super hacky patch.
  """
  return True
  """
  FIX THIS
  """
  BROWSER_DRIVER = 'django'
  NETLFIX_LOGIN_URL = 'https://www.netflix.com/Login?locale=en-US'
  NETFLIX_SUCCESS_URL = 'http://www.netflix.com/browse'
  EMAIL_FIELD_ID = 'email'
  PASSWORD_FIELD_ID = 'password'
  SIGN_IN_BUTTON_ID = 'login-form-contBtn'
  with Browser(BROWSER_DRIVER) as browser: 
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

def get_viewing_activity(user_id):
  NETFLIX_VIEWING_ACTIVITY_URL = 'https://www.netflix.com/WiViewingActivity'

# BEGIN API

@app.route('/')
def index():
  return 'Netflix and Chill API'

@app.route('/sign-in', methods=['POST'])
def sign_in():
  request_data = json.loads(request.data)
  # Error checking here
  nf_un = request_data['nf_un']
  nf_pw = request_data['nf_pw']
  INVALID_NETFLIX_CREDENTIALS = -1
  # Case 1: User exists
  if user_exists(nf_un):
    return create_user_id_response(get_user_by_username(nf_un).id)
  # Case 2: User doesn't exist, but has valid credentials
  if verify_netflix_credentials(nf_un, nf_pw):
    print 'Adding user.'
    add_user(nf_un, nf_pw)
    print 'Created user with id:', get_user_by_username(nf_un).id
    return create_user_id_response(get_user_by_username(nf_un).id)
  # Case 3: User doesn't exist, and has invalid credentials
  else:
    return create_user_id_response(INVALID_NETFLIX_CREDENTIALS)

@app.route('/create-chill-request', methods=['POST'])
def create_chill_request():
  print request.data
  request_data = json.loads(request.data)
  user_id = request_data['uid']
  genre = request_data['genre']
  program_type = request_data['type']
  date = process_date_from_string(request_data['day'])
  time = request_data['time']
  latitude = float(request_data['latitude'])
  longitude = float(request_data['longitude'])
  response = add_chill_request(user_id, genre, program_type, date, time, latitude, longitude)
  return create_chill_id_response(response)

# Takes in a string denoting a day of the week, and returns a date object representing
# the next occurence of that date
def process_date_from_string(date_string):
  today = datetime.date.today()
  current_weekday = today.weekday()
  target_weekday = get_weekday_int_from_string(date_string)
  day_delta = target_weekday-current_weekday
  if target_weekday < current_weekday:
    day_delta += 7
  delta = datetime.timedelta(days=target_weekday-current_weekday)
  return today + delta

# Returns a Python standard integer representing day of the week. Monday is 0. Sunday is 6.
def get_weekday_int_from_string(s):
  days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  if s not in days:
    raise ValueError('Day of week does not match any predefined names.')
  return days.index(s)

def create_user_id_response(user_id):
  return jsonify(**{'user_id': user_id})

def create_chill_id_response(chill_id):
  return jsonify(**{'chill_request_id': chill_id})

if __name__ == "__main__":
  app.run()

  #app.run()