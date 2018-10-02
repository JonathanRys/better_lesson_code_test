#!flask/bin/python
from flask import Flask, jsonify, make_response, abort, request
import requests
from jinja2 import Template

import sqlite3
import json
import hashlib
import os

api_key = os.environ.get("BETTER_LESSON_SENDMAIL_KEY");

# store template in DB?
template = Template('Hello {{ name }},<br/><br/>     Thanks for doing this exercise!<br/><br/><a href="{{ url }}">View in browser</a>')

DB_NAME = 'test.db'
TABLE_NAME = 'customers'

# Define functions for DB interaction
def create_table(table_name):
    """Function to create a table in a SQLite database"""
    # Open a connection to the DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + table_name + "'")
    if bool(c.fetchone()):
        print("Table '" + table_name + "' already exists.")
    else:
        # Create the table
        c.execute('CREATE TABLE ' + table_name + ' (id text, name text, email text)')
    # commit and close
    conn.commit()
    conn.close()

def save_data(table_name, name, email):
    """Function to save name and email to a table in the SQLite database"""
    # Open a connection to the DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # create a hash for a key
    currentHash = hashlib.sha224((name + DB_NAME + email).encode('utf-8')).hexdigest()
    # add the record to the DB
    c.execute("INSERT INTO " + table_name + " VALUES ('" + currentHash + "', '" + name + "', '" + email + "')")
    # commit and close
    conn.commit()
    conn.close()
    return currentHash

def fetch_data(table_name, page_id):
    """Function to fetch records from a table in the SQLite database"""
    # Open a connection to the DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # select the record from the DB
    user_name = c.execute("SELECT name FROM " + table_name + " WHERE id='" + page_id + "'").fetchone()
    # close the connection
    conn.close()
    print("USER NAME: " + user_name[0])
    return user_name[0]

app = Flask(__name__)

@app.route('/')
def index():
    """Base route handler"""
    # get passed params
    name = request.args.get('name')
    email = request.args.get('email_address')

    if name == None:
        return make_response(jsonify({'error': "Please prodive a name."}), 404)
    if email == None:
        return make_response(jsonify({'error': "Please prodive an email_address."}), 404)

    # create a request
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }

    pageHash = save_data(TABLE_NAME, name, email)

    url = "http://localhost:5000/email?id=" + pageHash

    body_content = template.render(name=name, url=url)

    data = {"personalizations": [{"to": [{"email": email}]}],"from": {"email": "jonathan.rk.rys@gmail.com"},"subject": "Hello!","content": [{"type": "text/html", "value": body_content}]}

    # POST to sendMail API
    response = requests.post("https://api.sendgrid.com/v3/mail/send", headers=headers, data=json.dumps(data))

    print("RESPONSE:" + str(response))
    # if response fails, roll back last transaction?  Do we care since the hash will just overwrite itself?
    
    return jsonify({'success':  "Email sent to " + name + "<" + email + ">"})

@app.route('/email')
def show_email():
    """Function to display a webpage version of the email"""
    page_id = request.args.get('id')
    name = fetch_data(TABLE_NAME, page_id)
    return template.render(name=name, url="#")

def run_app():
    create_table(TABLE_NAME)
    app.run()

if __name__ == "__main__":
    run_app()
