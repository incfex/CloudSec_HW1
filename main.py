import datetime

from flask import Flask, render_template, request, redirect
from google.cloud import datastore

app = Flask(__name__)
datastore_client = datastore.Client()

@app.route("/event", methods=["POST"])
def add_event():
  req = request.form
  print(req)
  e_name = req.get("event-name")
  e_time = req.get("event-time")

  entity = datastore.Entity(key=datastore_client.key('event'))
  entity.update({
      'name': e_name,
      'time': e_time
  })
  datastore_client.put(entity)

  return redirect('/')

@app.route("/events", methods=["GET"])
def get_event():
  return redirect('/')

def fetch_times(limit):
    query = datastore_client.query(kind='visit')
    query.order = ['-timestamp']

    times = query.fetch(limit=limit)

    return times

@app.route('/')
def root():
    # Store the current access time in Datastore.
    #store_time(datetime.datetime.now())

    # Fetch the most recent 10 access times from Datastore.
    times = fetch_times(10)

    return render_template(
        'index.html', times=times)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)