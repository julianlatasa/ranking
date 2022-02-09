# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 15:44:06 2022

@author: U54979
"""

import datetime
import pandas as pd

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

# Example dates
usuario = "julianlatasa@gmail.com"
password = "Julian80"
#usuario = input('Usuario Garmin (tipo mail): ')
#password = input('Clave de usuario de Garmin: ')
desde = input('Fecha desde (AAAA-MM-DD) [en blanco para fecha actual]: ')
try:
    if (desde == '') :
        today = datetime.date.today()
    else :
        today = datetime.datetime.strptime(desde, "%Y-%m-%d").date()
except ValueError:
    today = None

if ((today is None) or (usuario == '') or (password == '')):
    exit()
    

lastweek = today - datetime.timedelta(days=7)


## Initialize Garmin api with your credentials
api = Garmin(usuario, password)

## Login to Garmin Connect portal
api.login()

data = {'Usuario':[],'Actividades':[], 'Duracion':[]}
act = 0
dur= 0

print("Procesando: " + str(api.get_full_name()))
activities = api.get_activities(1,25)
for activitie in activities:
    datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
    if (today >= datetime_object.date() >= lastweek):
        act = act + 1
        dur = dur + activitie['duration']
#print(act)
data['Usuario'].append(api.get_full_name())
data['Actividades'].append(act)
data['Duracion'].append(dur)


connections = api.get_connections()
for connection in connections['userConnections']:
    print("Procesando: " + str(connection['fullName']))
    act = 0
    dur = 0
    activities = api.get_connection_activities(connection['displayName'],1,25)
    for activitie in activities['activityList']:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (today >= datetime_object.date() >= lastweek):
            act = act + 1
            dur = dur + activitie['duration']
    #print(act)
    data['Usuario'].append(connection['fullName'])
    data['Actividades'].append(act)
    data['Duracion'].append(dur)

    
api.logout()

df = pd.DataFrame(data)
df.sort_values(by=['Actividades','Duracion'], inplace=True, ascending=False)
df.to_excel('ranking_semanal.xlsx')