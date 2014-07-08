#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 Fondazione Bruno Kessler
# Author: Cristian Consonni
# Released under the MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# --------------------------------------------------------------------------- #

import os
import json
import pymongo
import requests
import arrow
from flask import Flask
from flask import request
from flask import g
from flask import render_template
from flask import redirect
from flask import send_from_directory
from flask_cors import cross_origin
from werkzeug.datastructures import MultiDict
from bson import json_util
from recaptcha.client import captcha
from bson.objectid import ObjectId

# --------------------------------------------------------------------------- #
# Application setup
# --------------------------------------------------------------------------- #

app = Flask(__name__)

# set the secret key
app.secret_key = os.urandom(24)

#add this so that flask doesn't swallow error messages
app.config['PROPAGATE_EXCEPTIONS'] = True

# Mailgun settings
with open('mailgun_conf.json', 'r') as configfile:
    mailgun_config = json.load(configfile)

MAILGUN_BASE_URL = "https://api.mailgun.net/v2/"
MAILGUN_DOMAIN = mailgun_config['MAILGUN_DOMAIN']
MAILGUN_API_KEY = mailgun_config['MAILGUN_API_KEY']
MAILGUN_FROM = mailgun_config['MAILGUN_FROM']
MAILGUN_TO = mailgun_config['MAILGUN_TO']
MAILGUN_URL = MAILGUN_BASE_URL + MAILGUN_DOMAIN + '/messages'

# ReCAPTCHA settings
if __name__ == "__main__":
    # private key for localhost (dev version)
    with open('dev_recaptcha_conf.json', 'r') as configfile:
        recaptcha_config = json.load(configfile)
else:
    # private key for production version
    with open('recaptcha_conf.json', 'r') as configfile:
        recaptcha_config = json.load(configfile)

RECAPTCHA_PRIVATE_KEY = recaptcha_config['RECAPTCHA_PRIVATE_KEY']


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #

# Prepare DB connection
@app.before_request
def setup_conn():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
        g.db = g.conn[os.environ['OPENSHIFT_APP_NAME']]


# --------------------------------------------------------------------------- #
# Geopoi utilities
# --------------------------------------------------------------------------- #

# This could also be implemented as a non-redirecting proxy
# https://stackoverflow.com/questions/10261378/
#    routes-in-bottle-which-proxy-to-another-server
# has the basic idea.
GEOPOI_SERVER_BASEURL = 'http://{s}.geopoi.it/geopoiAPI/tms/base.php?' + \
                        'tx={x}&ty={y}&vd={z}'

SERVERS = {'a': 'ts0',
           'b': 'ts1',
           'c': 'ts2'
           }

BASE_OFFSET_X = 156542.198409392
BASE_OFFSET_Y = 156543.588665743


def convert_zoom(z):
    # ZOOM = {18: 128,
    #         17: 256,
    #         16: 512,
    #         15: 1024
    #         }
    return pow(2, -z+25)


def convert_x_with_zoom(z):

    def convert_x(x):

        # BASE_OFFSET_X * float(convert_zoom(18))/float(convert_zoom(z))
        offset_x = BASE_OFFSET_X * 128./float(convert_zoom(z))

        # with zoom 18, i.e 128
        # geopoi_x = round(1.19432301*osm_x-156542.198409392)
        return int(round(1.19432301*int(x)-offset_x))

    return convert_x


def convert_y_with_zoom(z):

    def convert_y(y):

        # BASE_OFFSET_Y * float(convert_zoom(18))/float(convert_zoom(z))
        offset_y = BASE_OFFSET_Y * 128./float(convert_zoom(z))

        # geopoi_y = round(-1.1943348744*osm_y+156542.588665743)
        #
        # Minus sign is needed because it is a tms
        # See:
        # https://wiki.openstreetmap.org/wiki/TMS#The_Y_coordinate_flipped
        # also, leaflet has a specific option for TMS:
        # http://leafletjs.com/reference.html#tilelayer-options
        return int(-round(-1.1943348744*int(y)+offset_y))

    return convert_y


def unconvert_y_with_zoom(z):

    def unconvert_y(y):

        # BASE_OFFSET_Y * float(convert_zoom(18))/float(convert_zoom(z))
        offset_y = BASE_OFFSET_Y * 128./float(convert_zoom(z))

        # osm_y = round((geopoy_y-156542.588665743)/(-1.1943348744))
        return int(round((-int(y)-offset_y)/(-1.1943348744)))

    return unconvert_y


def get_parameters(xtile, ytile, zoom):

    xtile = int(xtile)
    ytile = int(ytile)

    zoom = int(zoom)

    xdiff = xtile - convert_x_with_zoom(zoom)(xtile)

    # tms has a negative sign, so we convert our central tile get the
    # converted number (which is negative), make it positive and calculate
    # back the tms tile value.
    tms_ytile = unconvert_y_with_zoom(zoom)(-convert_y_with_zoom(zoom)(ytile))

    # as above
    ydiff = tms_ytile - convert_y_with_zoom(zoom)(tms_ytile)

    def convert_parameters(s, z, x, y):

        s = SERVERS[s]

        z = convert_zoom(int(z))

        #  old formula, works for Trento
        # x = int(x) - 129498
        # y = int(y) - 123709

        x = int(x) - xdiff
        y = int(y) - ydiff

        return s, z, x, y

    return convert_parameters

# --------------------------------------------------------------------------- #
# Main app
# --------------------------------------------------------------------------- #


@app.route("/rmap/errors")
@cross_origin(headers=['Content-Type'])
def list_errors():

    try:
        result = list(g.db.reportmap.find().sort('$natural', -1).limit(1))[0]
        return str(json.dumps({"type": result['type'],
                               "features": result['features'],
                               "id": str(result['_id']),
                               "timestamp": result['timestamp']
                               },
                              default=json_util.default))
    except Exception as e:
        return json.dumps({'status': 1, 'statusmessage': e.message})


@app.route("/rmap/history")
@cross_origin(headers=['Content-Type'])
def list_history():

    perpage = request.args.get('perPage', 10)
    page = request.args.get('page', 1)
    offset = request.args.get('offset', 0)
    sort_id = request.args.get('sorts[id]', 0)
    sort_timestamp = request.args.get('sorts[timestamp]', 0)

    try:
        perpage = int(perpage)
    except:
        perpage = 10
    if perpage < 0:
        perpage = 10

    try:
        page = int(page)
    except:
        page = 1
    if page < 1:
        page = 1

    try:
        offset = int(offset)
    except:
        offset = 0
    if offset < 0:
        offset = 0

    try:
        sort_id = int(sort_id)
        sort_timestamp = int(sort_timestamp)
    except:
        sort_id = 0
        sort_timestamp = 0

    if sort_id:
        sort_param = '_id'
        if sort_id > 0:
            sort = 1
        else:
            sort = -1
    elif sort_timestamp:
        sort_param = 'timestamp'
        if sort_timestamp > 0:
            sort = 1
        else:
            sort = -1
    else:
        sort_param = ''
        sort = 0

    total_offset = (page - 1)*perpage + offset

    try:
        if sort_param:
            query_result = g.db.reportmap.find()\
                                         .sort(sort_param, sort)\
                                         .limit(perpage)\
                                         .skip(total_offset)
        else:
            query_result = g.db.reportmap.find()\
                                         .limit(perpage)\
                                         .skip(total_offset)

        result = [{'id': str(item['_id']),
                   'timestamp': item['timestamp']
                   }
                  for item in query_result]

        item_total = g.db.reportmap.count()

        return json.dumps({"records": result,
                           "queryRecordCount": len(result),
                           "totalRecordCount": item_total
                           })

    except Exception as e:
        return json.dumps({"records": [{'timestamp': e.message,
                                        'id': "Errore dal server"
                                        }],
                           "queryRecordCount": 1,
                           "totalRecordCount": 1
                           })


@app.route("/rmap/history2")
@cross_origin(headers=['Content-Type'])
def list_history2():
    try:
        query_result = g.db.reportmap.find()

        result = [[str(item['_id']),
                   item['timestamp']
                   ]
                  for item in query_result]

        item_total = g.db.reportmap.count()

        return json.dumps({"data": result,
                           "queryRecordCount": len(result),
                           "totalRecordCount": item_total
                           })

    except Exception as e:
        return json.dumps({"data": ["Errore dal server",
                                    e.message
                                    ],
                           "queryRecordCount": 1,
                           "totalRecordCount": 1
                           })


@app.route("/rmap/history/<version>")
@cross_origin(headers=['Content-Type'])
def get_history(version):

    try:
        result = g.db.reportmap.find_one({'_id': ObjectId(version)})
        return str(json.dumps({"type": result['type'],
                               "features": result['features'],
                               "id": str(result['_id']),
                               "timestamp": result['timestamp']
                               },
                              default=json_util.default))

    except Exception as e:
        return json.dumps({'status': 1, 'statusmessage': e.message})


@app.route("/rmap/error/delete", methods=['POST'])
@cross_origin(headers=['Content-Type'])
def delete_error():
    item = request.form.get('item')
    map_id = request.form.get('map_id')

    result = list(g.db.reportmap.find().sort('$natural', -1).limit(1))[0]

    try:
        # remove from DB, set second parameter to true to limit
        # to one deletion
        # (item for item in result['features']  if item["id"] == deleted_id)

        thing = json.loads(item)
        result['features'].remove(thing)

        g.db.reportmap.insert({"type": result['type'],
                               "features": result['features'],
                               "timestamp": str(arrow.utcnow())
                               })

        statusmessage = 'Object {0} successfully '\
                        'removed from map {1}'.format(thing['id'], map_id)

        return json.dumps({'status': 0, 'statusmessage': statusmessage})

    except Exception as e:
        return json.dumps({'status': 1, 'statusmessage': e.message})


@app.route("/rmap/error/insert", methods=['POST'])
@cross_origin(headers=['Content-Type'])
def insert_error():

    try:
        lat = float(request.form.get('lat'))
    except:
        return json.dumps({'status': 1, 'statusmessage': 'Invalid latitude'})

    try:
        lon = float(request.form.get('lon'))
    except:
        return json.dumps({'status': 1, 'statusmessage': 'Invalid longitude'})

    _id = request.form.get('id')

    map_id = request.form.get('map_id')

    text = request.form.get('text')

    result = list(g.db.reportmap.find().sort('$natural', -1).limit(1))[0]

    try:
        thing = {"type": "Feature",
                 "id": _id,
                 "properties": {"text": text},
                 "geometry": {"type": "Point", "coordinates": [lon, lat]}
                 }

        result['features'].append(thing)

        g.db.reportmap.insert({"type": result['type'],
                               "features": result['features'],
                               "timestamp": str(arrow.utcnow())
                               })

        statusmessage = 'Object {0} successfully '\
                        'added to map {1}'.format(_id, map_id)

        return json.dumps({'status': 0, 'statusmessage': statusmessage})

    except Exception as e:
        return json.dumps({'status': 1, 'statusmessage': e.message})


@app.route("/contacts/send-form", methods=['POST'])
@cross_origin(headers=['Content-Type'])
def send_form():
    data = MultiDict()
    data['name'] = request.form['name']
    data['email'] = request.form['email']
    data['message'] = request.form['message']

    text = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

    response = captcha.submit(
        request.form['recaptcha_challenge_field'],
        request.form['recaptcha_response_field'],
        RECAPTCHA_PRIVATE_KEY,
        request.remote_addr)

    if not response.is_valid:
        # Invalid ReCAPTCHA
        data['status'] = 1
        data['statusmessage'] = "Il codice antispam che hai inserito " + \
                                "non è valido."
        return json.dumps(data)

    else:
        # valid ReCAPTCHA
        res = requests.post(MAILGUN_URL,
                            auth=("api", MAILGUN_API_KEY),
                            data={"from": MAILGUN_FROM,
                                  "to": MAILGUN_TO,
                                  "subject": "Form di contatto da AEmap",
                                  "text": text
                                  })
        try:
            if res.json()['message'] == u'Queued. Thank you.':
                #  Message successfully delivered
                data['status'] = 0
                data['statusmessage'] = "Il messaggio è stato inviato " + \
                                        "con successo."
                return json.dumps(data)

            else:
                # Some error from Mailgun
                data['status'] = 1
                data['statusmessage'] = json.dumps(res.json())
                return json.dumps(data)

        except Exception as e:
            # Some strange Exception
            data['status'] = 1
            data['statusmessage'] = e.message
            return json.dumps(data)


@app.route('/map/<xtile>/<ytile>/<s>/<z>/<x>/<y>.png')
def redirecting_proxy(xtile, ytile, s, z, x, y):
    # http://b.tile.osm.org/18/139168/93186.png
    # http://ts2.geopoi.it/geopoiAPI/tms/base.php?tx=9670&ty=45248&vd=128

    s, z, x, y = get_parameters(xtile, ytile, z)(s, z, x, y)

    url = GEOPOI_SERVER_BASEURL.format(s=s, z=z, x=x, y=y)

    return redirect(url)


# --------------------------------------------------------------------------- #
# Web pages
# --------------------------------------------------------------------------- #

@app.route("/reportmap")
def show_map():
    return render_template("reportmap.html", title='Report Map')


@app.route("/aemap")
def show_aemap():
    return render_template("aemap.html", title='AE Map')


@app.route("/sync")
def show_sync():
    return render_template("sync.html", title='Map Compare')


#need this in a scalable app so that HAProxy thinks the app is up
@app.route("/")
def homepage():
    return render_template("index.html", title='Worst Nightmare')


@app.route("/test")
def test():
    return 'It works!'


if __name__ == "__main__":

    @app.route("/static/img/<filename>")
    def serve_image(filename):
        path = os.path.realpath(os.path.join('static/img', filename))
        print path
        return send_from_directory('static/img', filename)

    app.run(host='localhost', port=5500)
