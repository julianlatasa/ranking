
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


from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/cucu')
def cucu():
    usuario = "julianlatasa@gmail.com"
    password = "Julian80"
    today = datetime.date.today()
    lastweek = today - datetime.timedelta(days=7)
    data = {'Usuario':[],'Actividades':[], 'Duracion':[]}
    act = 3
    dur= 3600

    ## Initialize Garmin api with your credentials
    api = Garmin(usuario, password)

    ## Login to Garmin Connect portal
    api.login()

    activities = api.get_activities(1,25)
    for activitie in activities:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (today >= datetime_object.date() >= lastweek):
            act = act + 1
            dur = dur + activitie['duration']
    data['Usuario'].append(api.get_full_name())
    data['Actividades'].append(act)
    data['Duracion'].append(dur)

    connections = api.get_connections()
    for connection in connections['userConnections']:
        act = 0
        dur = 0
        activities = api.get_connection_activities(connection['displayName'],1,25)
        for activitie in activities['activityList']:
            datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
            if (today >= datetime_object.date() >= lastweek):
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

