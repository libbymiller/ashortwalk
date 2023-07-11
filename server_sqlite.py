from flask import Flask, render_template, request, jsonify, redirect, url_for
from PIL import Image
import os.path
from os.path import exists
from os import listdir, mkdir, path
from os.path import isfile, join
import re
import random
from datetime import datetime
import sqlite3
from functools import wraps
import json
from waitress import serve


app = Flask(__name__)
app.config.from_file("config.json", load=json.load)

#print("got config",app.config)
geo = app.config["GEO"]
scale = app.config["SCALE"]
user = app.config["USER"]
passw = app.config["PASS"]
domain = app.config["DOMAIN"]

server_path = ""

# database
# create some tables

db = "db/asw.db"
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS walks(id integer primary key autoincrement, title, description, creator, mapdata, walklength integer, dt timestamp)")
cur.execute("CREATE TABLE IF NOT EXISTS completed_walks(person_id, walk_id integer, dt timestamp)")
cur.close()
con.close()

# "security"
# this is just basicauth. sorry!

def check_auth(username, password):
    return username == user and password == passw

def login_required(f):
    @wraps(f)
    def wrapped_view(**kwargs):
        auth = request.authorization
        if not (auth and check_auth(auth.username, auth.password)):
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })

        return f(**kwargs)
    return wrapped_view


# create some directories that are needed for a new person
def initialisePerson(fn, person_id):
    mkdir(fn)
    mkdir("static/people/"+person_id)
    mkdir("static/people/"+person_id+"/uploaded_images/")
    return

# get all the walks in the system
def getAllWalks():
    with sqlite3.connect(db) as con:
      cur = con.cursor()
      cur.execute("SELECT * FROM walks ORDER BY walklength");
      res = cur.fetchall()
      return res

# get walks person_id has done
def getMyWalks(person_id):
    with sqlite3.connect(db) as con:
      cur = con.cursor()
      cur.execute("SELECT id, title, description, creator, mapdata, walklength, completed_walks.dt FROM completed_walks,walks WHERE person_id=? AND completed_walks.walk_id=walks.id", (person_id,))
      res = cur.fetchall()
      return res

# get walks I've made
def getMyCreatedWalks(person_id):
    with sqlite3.connect(db) as con:
      cur = con.cursor()
      cur.execute("SELECT * FROM walks where creator=? ORDER BY id",(person_id,))
      res = cur.fetchall()
      return res

# get all the pictures I've made
def getMyPics(person_id):
    images_path = "static/people/"+person_id+"/uploaded_images/"
    all_pics = None
    if(exists(images_path)):
      all_pics = [f for f in listdir(images_path) if isfile(join(images_path, f))]
    return all_pics

# get a random walk
def getRandomWalk():
    all_walks = getAllWalks()
    if (len(all_walks)>0):
      r = random.choice(all_walks)
      return r
    else:
      return None

# get info about a walk
def getWalkData(walk_id):
    with sqlite3.connect(db) as con:
      cur = con.cursor()
      cur.execute("SELECT * FROM walks WHERE id=?",(walk_id,))
      res = cur.fetchone()
      return res

# save a map image when a walk is created
def saveMapImage(img, walk_id):
    path = "static/maps/map"+str(walk_id)+".jpg"
    saveImage(img, path, 400)
    return 1

# save a walk text description
def saveWalk(title,description,person_id,mapdata,walklength):
    with sqlite3.connect(db) as con:
      cur = con.cursor()
      cur.execute("INSERT INTO walks(title, description, creator, mapdata, walklength, dt) VALUES(?,?,?,?,?,?)", (title,description,person_id,mapdata,walklength,datetime.now()))
      con.commit()
      # return the last id
      cur.execute("SELECT MAX(id) FROM walks LIMIT 1")
      res = cur.fetchone()
      return res[0]

def getMyNextWalk(person_id):
    with sqlite3.connect(db) as con:
      cur = con.cursor()

      # return the longest walk done
      cur.execute("SELECT MAX(walklength) FROM completed_walks, walks WHERE person_id=? and walks.id=completed_walks.walk_id LIMIT 1", (person_id,))
      res = cur.fetchone()
      # now find the next longest walk (fixme: should not include ones done)
      longest_walk = res[0]
      if(longest_walk):
         cur.execute("SELECT * FROM walks WHERE walklength > ? LIMIT 1", (int(longest_walk),))
         next_w = cur.fetchone()
         return next_w


# add a new walk to my data
def saveMyWalk(person_id, walk_id):
    with sqlite3.connect(db) as con:
      cur = con.cursor()
      cur.execute("INSERT INTO completed_walks(person_id, walk_id, dt) VALUES(?,?,?)", (person_id, walk_id, datetime.now()))
      con.commit()


def saveImage(img, path, width):
    if not img.mode == 'RGB':
      img = img.convert('RGB')
    # https://stackoverflow.com/a/451580
    basewidth = width
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
    img.save(path, quality=95)
    return 1


# save an image I've made of a walk
def saveUserImage(img, person_id, walk_id):
    path = "static/people/"+person_id+"/uploaded_images/"
    fn = path + "walk_"+str(walk_id)+".jpg"

    if(exists(path)):
      pass
    else:
      mkdir("static/people/"+person_id)
      mkdir("static/people/"+person_id+"/uploaded_images/")

    saveImage(img, fn, 400)
    saveMyWalk(person_id, walk_id)
    return 1


# routes

@app.route('/test', methods=['GET'])
@login_required
def test():
   return render_template('splash.html')

@app.route('/', methods=['GET'])
@login_required
def splash():
   return render_template('splash.html')


# Various data about a person, a kind of home page

@app.route('/people/<person_id>', defaults={'walk_id': None}, methods=['GET'])
@app.route('/people/<person_id>/<walk_id>', methods=['GET'])
@login_required
def people(person_id, walk_id=None):

    next_walk = getMyNextWalk(person_id)
    if(next_walk == None):
      next_walk = getWalkData(1) # first walk. could be random

    all_walks = getAllWalks()

    walks_done = getMyWalks(person_id)

    my_created_walks = getMyCreatedWalks(person_id)

    all_my_pics = getMyPics(person_id)

    # only if we have a completed walk
    completed_walk_title = None
    if(walk_id):
      completed_walk_id, completed_walk_title, completed_walk_description, completed_walk_author, completed_walk_mapdata, completed_walk_walklength,completed_walk_dt = getWalkData(walk_id)

    return render_template('person.html', person_id=person_id, next_walk=next_walk, all_walks=all_walks, walks_done=walks_done, my_created_walks=my_created_walks,all_pics=all_my_pics,completed_walk_id=walk_id, completed_walk_title=completed_walk_title, server_path=server_path, domain=domain)

# A random walk

@app.route('/walks/random/<person_id>', methods=['GET', 'POST'])
@login_required
def randomWalk(person_id):
    tmp = getRandomWalk()
    if(tmp == None):
      return render_template('fail.html', person_id=person_id, server_path=server_path, err="No walks exist")
    else:
      walk_id, title, description, author, mapdata, walklength, dt = tmp
      return render_template('walk.html', walk_id=walk_id, title=title, description=description, author=author, mapdata=mapdata, walklength=walklength,person_id=person_id, server_path=server_path, geo=geo, scale=scale)

# Displays a walk

@app.route('/walks/<walk_id>/<person_id>', methods=['GET', 'POST'])
@login_required
def walk(walk_id, person_id):
    id, title, description, author, mapdata, walklength,dt = getWalkData(walk_id)
    return render_template('walk.html', walk_id=walk_id, title=title, description=description, author=author, mapdata=mapdata, walklength=walklength,person_id=person_id, server_path=server_path, geo=geo, scale=scale)

@app.route('/completedwalks/<walk_id>/<person_id>', methods=['GET', 'POST'])
@login_required
def completedWalk(walk_id, person_id):
    id, title, description, author, mapdata, walklength, dt = getWalkData(walk_id)
    return render_template('completedwalk.html', walk_id=walk_id, title=title, description=description, author=author, mapdata=mapdata, walklength=walklength,person_id=person_id, server_path=server_path, geo=geo, scale=scale, domain=domain)


# Show create walk page

@app.route('/createwalk/<person_id>', methods=['GET', 'POST'])
@login_required
def createWalk(person_id):

    return render_template('createwalk.html', person_id=person_id, server_path=server_path, geo=geo, scale=scale)


# Uploads and saves a walk

@app.route('/uploadwalk/<person_id>', methods=['POST'])
@login_required
def uploadWalk(person_id):
    print("request.files",request.files)
    base64_audio = request.files['audio_recording']
    suffix = request.form['suffix']

    title = request.form['title']
    description = request.form['description']
    mapdata = request.form['mapdata']
    walklength = request.form['walklength']

    walk_id = saveWalk(title,description,person_id,mapdata,walklength)

    base64_audio.save("static/audio/audio"+str(walk_id)+"."+suffix)
    cmd = "ffmpeg -y  -i static/audio/audio"+str(walk_id)+"."+suffix+" static/audio/audio"+str(walk_id)+".mp3"
    os.system(cmd)

    return render_template('newwalk.html', walk_id=walk_id, title=title, description=description, person_id=person_id, mapdata=mapdata,walklength=walklength,server_path=server_path, geo=geo, scale=scale);


# Upload an image to show you did the walk

@app.route('/upload/<person_id>', methods=['POST'])
@login_required
def uploadUserImage(person_id):
    file = request.files['image']
    walk_id = request.form['walk']
    img = Image.open(file.stream)

    result = saveUserImage(img, person_id, walk_id)
    if(result):
      return redirect(server_path+url_for("people",person_id=person_id,walk_id=walk_id))
    else:
      return render_template('fail.html', err=img.format, server_path=server_path);


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5001)
#    serve(app, host='0.0.0.0', port=5001)
