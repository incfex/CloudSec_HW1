import datetime
import json

from flask import Flask, render_template, request, redirect, Response, jsonify, send_from_directory, make_response
from google.cloud import datastore

app = Flask(__name__)
DS = datastore.Client()
EVENT = 'event'
ROOT = DS.key('Entities', 'root')


@app.route("/event", methods=["POST"])
def add_event():
    # Since context_type is not set on client side, force request to think context is json
    req = request.get_json(force=True)
    # extract info from payload
    e_name = req["name"]
    e_time = req["time"]
    # create entry for datastore
    entity = datastore.Entity(key=DS.key(EVENT, parent=ROOT))
    entity.update({'name': e_name, 'time': e_time})
    # upload
    DS.put(entity)

    return ''


@app.route("/events", methods=["GET"])
def get_event():
    # set rule for query
    query = DS.query(kind=EVENT, ancestor=ROOT)
    query.order = ['-time']
    # make query
    events = query.fetch()
    # contrust response
    payload = []
    for val in events:
        pl = {
            'id': val.id,
            'name': val['name'],
            'time': val['time']
        }
        payload.append(pl)
    # send payload
    return jsonify(payload)

@app.route('/event/<int:event_id>', methods=['DELETE'])
def del_event(event_id):
    # delete from datastore based on event_id
    DS.delete(DS.key('event', event_id, parent=ROOT))
    return ''

@app.route('/')
def root():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)