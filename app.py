
# A very simple Flask Hello World app for you to get started with...
import datetime
import pandas as pd

from garminconnect import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

from garminconnect2 import (
    Garmin,
)

import json
import sqlite3

from flask import Flask, request, render_template

app = Flask(__name__, template_folder='./')

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/form', methods=['GET'])
def form():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = {'usuario' : request.get_json().get('usuario'),
                'password' : request.get_json().get('password'),
                'fecha' : request.get_json().get('fecha')}
    #con = create_connection('login.db')
    #cursor = con.cursor()
    #cursor.execute("CREATE TABLE IF NOT EXISTS login (usuario VARCHAR(255) NOT NULL, password CHAR(25) NOT NULL);")
    #con.execute("INSERT INTO login (usuario, password) VALUES (?, ?)",tuple(data.values()))
    return json.dumps(data)

@app.route('/cucu')
def cucu():
    usuario = "julianlatasa@gmail.com"
    password = "Julian80"
    today = datetime.date.today()
    today = datetime.datetime(2022, 2, 6).date()
    lastweek = today - datetime.timedelta(days=7)
    data = {'Usuario':[],'Actividades':[], 'Duracion':[]}
    act = 0
    dur= 0
    row=0

    date_list = [today - datetime.timedelta(days=x) for x in range(7)]
    dates = {'Usuario' : []}
    for d in date_list:
        dates[d] = []
    #dates = {date : [] for date in date_list}

    ## Initialize Garmin api with your credentials
    api = Garmin(usuario, password)

    ## Login to Garmin Connect portal
    api.login()

    activities = api.get_activities(1,25)
    dates['Usuario'].append(api.get_full_name())
    for d in date_list:
        dates[d].append(0)
    for activitie in activities:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (datetime_object.date() in dates):
            dates[datetime_object.date()][row] = dates[datetime_object.date()][row] + 1
        if (today >= datetime_object.date() > lastweek):
            act = act + 1
            dur = dur + activitie['duration']
    data['Usuario'].append(api.get_full_name())
    data['Actividades'].append(act)
    data['Duracion'].append(dur)

    connections = api.get_connections()
    for connection in connections['userConnections']:
        act = 0
        dur = 0
        row = row + 1
        dates['Usuario'].append(connection['fullName'])
        for d in date_list:
            dates[d].append(0)
        activities = api.get_connection_activities(connection['displayName'],1,25)
        for activitie in activities['activityList']:
            datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
            if (datetime_object.date() in dates):
                dates[datetime_object.date()][row] = dates[datetime_object.date()][row] + 1
            if (today >= datetime_object.date() > lastweek):
                act = act + 1
                dur = dur + activitie['duration']
        data['Usuario'].append(connection['fullName'])
        data['Actividades'].append(act)
        data['Duracion'].append(dur)

    api.logout()

    df = pd.DataFrame(data)
    df.sort_values(by=['Actividades','Duracion'], inplace=True, ascending=False)

    result = df.to_html()
    return result

@app.route('/query', methods=['POST'])
def query():
    usuario = ''
    password = ''
    if request.method == 'POST':
        usuario = request.get_json().get('usuario')
        password = request.get_json().get('password')
        fecha = request.get_json().get('fecha')
    
    if (usuario == ''):
        return 'El usuario o clave no son correctos'
    
    if (fecha is None):
        return "La fecha es invalida"
        
    today = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
    
    lastweek = today - datetime.timedelta(days=7)
    data = {'Usuario':[],'Actividades':[], 'Duracion':[]}
    act = 0
    dur= 0
    row=0

    date_list = [today - datetime.timedelta(days=x) for x in range(7)]
    dates = {'Usuario' : []}
    for d in date_list:
        dates[d] = []
    #dates = {date : [] for date in date_list}

    ## Initialize Garmin api with your credentials
    api = Garmin(usuario, password)

    ## Login to Garmin Connect portal
    api.login()

    activities = api.get_activities(1,25)
    dates['Usuario'].append(api.get_full_name())
    for d in date_list:
        dates[d].append(0)
    for activitie in activities:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (datetime_object.date() in dates):
            dates[datetime_object.date()][row] = dates[datetime_object.date()][row] + 1
        if (today >= datetime_object.date() > lastweek):
            act = act + 1
            dur = dur + activitie['duration']
    data['Usuario'].append(api.get_full_name())
    data['Actividades'].append(act)
    data['Duracion'].append(dur)

    connections = api.get_connections()
    for connection in connections['userConnections']:
        act = 0
        dur = 0
        row = row + 1
        dates['Usuario'].append(connection['fullName'])
        for d in date_list:
            dates[d].append(0)
        activities = api.get_connection_activities(connection['displayName'],1,25)
        for activitie in activities['activityList']:
            datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
            if (datetime_object.date() in dates):
                dates[datetime_object.date()][row] = dates[datetime_object.date()][row] + 1
            if (today >= datetime_object.date() > lastweek):
                act = act + 1
                dur = dur + activitie['duration']
        data['Usuario'].append(connection['fullName'])
        data['Actividades'].append(act)
        data['Duracion'].append(dur)

    api.logout()

    df = pd.DataFrame(data)
    df.sort_values(by=['Actividades','Duracion'], inplace=True, ascending=False)

    result = df.to_html()
    return result

if __name__ =="__main__":
    app.run(debug=True, port=8080)