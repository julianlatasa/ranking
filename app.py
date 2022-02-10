
# A very simple Flask Hello World app for you to get started with...
import datetime
import pandas as pd

from garminconnect import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

from garminconnect2 import (
    Garmin
)

from singletonGarmin import SingletonGarmin

from flask import Flask, request, render_template, jsonify, session

from time import sleep
from math import sqrt

app = Flask(__name__, template_folder='./')
apiGarmin = SingletonGarmin()
app.secret_key = 'GarminConnect'
cache = {}


@app.route("/stream")
def stream():
    def generate():
        for i in range(500):
            yield "{}\n".format(sqrt(i))
            sleep(1)

    return app.response_class(generate(), mimetype="text/plain")

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/form', methods=['GET'])
def form():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        params = request.get_json()
        usuario, password = params['usuario'].strip(), params['password'].strip()
        fecha = params.get('fecha', "").strip()
        
    if ((not usuario) or (not password)):
        return "No se ingreso un usuario o una clave",403 
    
    if (not fecha):
        return "No se ingreso una fecha",403

    try:
        today = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    except:
        return "La fecha tiene un formato no valido", 403
    

    apiGarmin.setParams(usuario, password)
    
    api = apiGarmin.getApi()
    try:
        if (api.login() == False):
            return "Error al loguearse a Garmin", 403
    except:
        return "Error inesperado al loguearse a Garmin" + apiGarmin.getParams(), 403

    if not('today' in session):
        session['today'] = today
    return 'Login Ok! - Buscando contactos'

@app.route('/logout', methods=['GET'])
def logout():
    api = apiGarmin.getApi()
    api.logout
    return "Logout!"

@app.route('/contacts', methods=['GET'])
def contacts():
    api = apiGarmin.getApi()
    try:
        connections = api.get_connections()
    except:
        return "Error al obtener contactos", 403
    if (not(connections) or not(len(connections)>0) or not('userConnections' in connections) ):
        return "Error al procesar contactos", 403

    apiGarmin.setConnections(connections['userConnections'])
    result = {'mensaje' : 'Contactos obtenidos! - Buscando datos personales',
              'contactos' : len(connections['userConnections'])}
    return jsonify(result)

@app.route('/procesarme', methods=['GET'])
def procesarme():
    api = apiGarmin.getApi()
    fecha = session['today']

    #Sun, 06 Feb 2022 00:00:00 GMT 
    if isinstance(fecha, str):
        today = datetime.datetime.strptime(fecha, "%a, %d %b %Y %H:%M:%S %Z").date()
    else:
        today = fecha.date()

    lastweek = today - datetime.timedelta(days=7)
    data = {'Usuario':'','Actividades':0, 'Duracion':0}

    date_list = [today - datetime.timedelta(days=x) for x in range(7)]
    dates = {'Usuario' : ''}
    for d in date_list:
        dates[d] = 0

    try:
        activities = api.get_activities(1,25)
    except:
        return "Error al obtener mis actividades", 403
    if (not(activities) or not(len(activities)>0)):
        return "Error al comenzar a procesar actividades", 403

    try:
        data['Usuario'] = api.get_full_name()
        dates['Usuario'] = api.get_full_name()
    except:
        return "Error al obtener mi nombre completo", 403
    
    dur = 0
    for activitie in activities:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (datetime_object.date() in dates):
            dates[datetime_object.date()] = dates[datetime_object.date()] + 1
        if (today >= datetime_object.date() > lastweek):
            data['Actividades'] = data['Actividades'] + 1
            dur = dur + activitie['duration']

    data['Duracion'] = datetime.timedelta(seconds=dur)

    if 'dates' in cache:
        cache['dates'].append(dates)
    else:
        cache['dates'] = []
        cache['dates'].append(dates)

    if 'data' in cache:
        cache['data'].append(data)
    else:
        cache['data'] = []
        cache['data'].append(data)
    session['today'] = today
    return "Mi usuario fue procesado "

@app.route('/procesarusuario', methods=['GET','POST'])
def procesarusuario():
    if request.method == 'POST':
        params = request.get_json()
        usuarionumero = params['usuarionumero']

    api = apiGarmin.getApi()
    fecha = session['today']
    if isinstance(fecha, str):
        today = datetime.datetime.strptime(fecha, "%a, %d %b %Y %H:%M:%S %Z").date()
    else:
        today = fecha.date()

    connections = apiGarmin.getConnections()
    
    lastweek = today - datetime.timedelta(days=7)
    data = {'Usuario':'','Actividades':0, 'Duracion':0}

    date_list = [today - datetime.timedelta(days=x) for x in range(7)]
    dates = {'Usuario' : ''}
    for d in date_list:
        dates[d] = 0

    try:
        connection = connections[usuarionumero]
        data['Usuario'] = connection['fullName']
        dates['Usuario'] = connection['fullName']
    except:
        return "Error al obtener nombre completo del usuario numero " + str(usuarionumero), 403

    try:
        activities = api.get_connection_activities(connection['displayName'],1,25)
    except:
        return "Error al obtener actividades de " + connection['fullName'], 403

    if (not(activities) or not(len(activities)>0) or not('activityList' in activities) ):
        return "Error al comenzar a procesar actividades de " + connection['fullName'], 403

    dur = 0    
    for activitie in activities['activityList']:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (datetime_object.date() in dates):
            dates[datetime_object.date()] = dates[datetime_object.date()] + 1
        if (today >= datetime_object.date() > lastweek):
            data['Actividades'] = data['Actividades'] + 1
            dur = dur + activitie['duration']

    data['Duracion'] = datetime.timedelta(seconds=dur)
    
    cache['dates'].append(dates)
    cache['data'].append(data)
    session['today'] = today
    return connection['fullName'] + " fue procesado "

@app.route('/resultados', methods=['GET'])
def resultados():
    data = cache['data']
    df = pd.DataFrame(data)
    df.sort_values(by=['Actividades','Duracion'], inplace=True, ascending=False)

    result = df.to_html()
    session.pop('today')
    cache['data'] = []
    return result


@app.route('/query', methods=['POST'])
def query():
    if request.method == 'POST':
        params = request.get_json()
        usuario, password = params['usuario'].strip(), params['password'].strip()
        fecha = params.get('fecha', "").strip()
        
    if ((not usuario) or (not password)):
        return "No se ingreso un usuario o una clave",403 
    
    if (not fecha):
        return "No se ingreso una fecha",403

    try:
        today = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
    except:
        return "La fecha tiene un formato no valido", 403

    apiGarmin.setParams(usuario, password)
    
    api = apiGarmin.getApi()
    try:
        if (api.login() == False):
            return "Error al loguearse a Garmin", 403
    except:
        return "Error inesperado al loguearse a Garmin" + apiGarmin.getParams(), 403

    try:
        connections = api.get_connections()
    except:
        return "Error al obtener contactos", 403

    if (not(connections) or not(len(connections)>0) or not('userConnections' in connections) ):
        return "Error al procesar contactos", 403

    userConnections = connections['userConnections']

    lastweek = today - datetime.timedelta(days=7)
    data = {'Usuario':'','Actividades':0, 'Duracion':0}

    date_list = [today - datetime.timedelta(days=x) for x in range(7)]
    dates = {'Usuario' : ''}
    for d in date_list:
        dates[d] = 0

    try:
        activities = api.get_activities(1,25)
    except:
        return "Error al obtener mis actividades", 403

    if (not(activities) or not(len(activities)>0)):
        return "Error al comenzar a procesar actividades", 403

    try:
        data['Usuario'] = api.get_full_name()
        dates['Usuario'] = api.get_full_name()
    except:
        return "Error al obtener mi nombre completo", 403
    
    dur = 0
    for activitie in activities:
        datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
        if (datetime_object.date() in dates):
            dates[datetime_object.date()] = dates[datetime_object.date()] + 1
        if (today >= datetime_object.date() > lastweek):
            data['Actividades'] = data['Actividades'] + 1
            dur = dur + activitie['duration']

    data['Duracion'] = datetime.timedelta(seconds=dur)

    cache['dates'] = []
    cache['dates'].append(dates)

    cache['data'] = []
    cache['data'].append(data)

    for user in userConnections:    

        data = {'Usuario':'','Actividades':0, 'Duracion':0}
    
        date_list = [today - datetime.timedelta(days=x) for x in range(7)]
        dates = {'Usuario' : ''}
        for d in date_list:
            dates[d] = 0

        try:
            data['Usuario'] = user['fullName']
            dates['Usuario'] = user['fullName']
        except:
            return "Error al obtener nombre completo del usuario numero " + str(user), 403

        try:
            activities = api.get_connection_activities(user['displayName'],1,25)
        except:
            return "Error al obtener actividades de " + user['fullName'], 403

        if (not(activities) or not(len(activities)>0) or not('activityList' in activities) ):
            return "Error al comenzar a procesar actividades de " + user['fullName'], 403

        dur = 0    
        for activitie in activities['activityList']:
            datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
            if (datetime_object.date() in dates):
                dates[datetime_object.date()] = dates[datetime_object.date()] + 1
            if (today >= datetime_object.date() > lastweek):
                data['Actividades'] = data['Actividades'] + 1
                dur = dur + activitie['duration']
    
        data['Duracion'] = datetime.timedelta(seconds=dur)
        
        cache['dates'].append(dates)
        cache['data'].append(data)

    api.logout

    data = cache['data']
    df = pd.DataFrame(data)
    df.sort_values(by=['Actividades','Duracion'], inplace=True, ascending=False)

    result = df.to_html()
    cache['data'] = []

    return result


@app.route('/ranking', methods=['POST'])
def ranking():
    if request.method == 'POST':
        params = request.get_json()
        usuario, password = params['usuario'].strip(), params['password'].strip()
        fecha = params.get('fecha', "").strip()
    def generate():
        yield "Iniciando consulta\n" 
            
        if ((not usuario) or (not password)):
            return "No se ingreso un usuario o una clave",403 
        
        if (not fecha):
            return "No se ingreso una fecha",403

        try:
            today = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
        except:
            return "La fecha tiene un formato no valido", 403
    
        apiGarmin.setParams(usuario, password)
        
        api = apiGarmin.getApi()
        try:
            if (api.login() == False):
                return "Error al loguearse a Garmin", 403
        except:
            return "Error inesperado al loguearse a Garmin" + apiGarmin.getParams(), 403
    
        yield "Obteniendo contactos\n"
        
        try:
            connections = api.get_connections()
        except:
            return "Error al obtener contactos", 403
    
        if (not(connections) or not(len(connections)>0) or not('userConnections' in connections) ):
            return "Error al procesar contactos", 403
    
        userConnections = connections['userConnections']

        lastweek = today - datetime.timedelta(days=7)
        data = {'Usuario':'','Actividades':0, 'Duracion':0}
    
        date_list = [today - datetime.timedelta(days=x) for x in range(7)]
        dates = {'Usuario' : ''}
        for d in date_list:
            dates[d] = 0
    
        yield "Obteniendo actividades del usuario"
        
        try:
            activities = api.get_activities(1,25)
        except:
            return "Error al obtener mis actividades", 403
    
        if (not(activities) or not(len(activities)>0)):
            return "Error al comenzar a procesar actividades", 403
    
        try:
            data['Usuario'] = api.get_full_name()
            dates['Usuario'] = api.get_full_name()
        except:
            return "Error al obtener mi nombre completo", 403

        dur = 0
        for activitie in activities:
            datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
            if (datetime_object.date() in dates):
                dates[datetime_object.date()] = dates[datetime_object.date()] + 1
            if (today >= datetime_object.date() > lastweek):
                data['Actividades'] = data['Actividades'] + 1
                dur = dur + activitie['duration']
    
        data['Duracion'] = datetime.timedelta(seconds=dur)
    
        cache['dates'] = []
        cache['dates'].append(dates)
    
        cache['data'] = []
        cache['data'].append(data)

        for user in userConnections:    
    
            data = {'Usuario':'','Actividades':0, 'Duracion':0}
        
            date_list = [today - datetime.timedelta(days=x) for x in range(7)]
            dates = {'Usuario' : ''}
            for d in date_list:
                dates[d] = 0
    
            try:
                data['Usuario'] = user['fullName']
                dates['Usuario'] = user['fullName']
            except:
                return "Error al obtener nombre completo del usuario numero " + str(user), 403
    
            yield "Obteniendo actividades de " + user['fullName']
            
            try:
                activities = api.get_connection_activities(user['displayName'],1,25)
            except:
                return "Error al obtener actividades de " + user['fullName'], 403
    
            if (not(activities) or not(len(activities)>0) or not('activityList' in activities) ):
                return "Error al comenzar a procesar actividades de " + user['fullName'], 403
    
            dur = 0    
            for activitie in activities['activityList']:
                datetime_object = datetime.datetime.strptime(activitie['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
                if (datetime_object.date() in dates):
                    dates[datetime_object.date()] = dates[datetime_object.date()] + 1
                if (today >= datetime_object.date() > lastweek):
                    data['Actividades'] = data['Actividades'] + 1
                    dur = dur + activitie['duration']
        
            data['Duracion'] = datetime.timedelta(seconds=dur)
            
            cache['dates'].append(dates)
            cache['data'].append(data)

        api.logout
    
        data = cache['data']
        df = pd.DataFrame(data)
        df.sort_values(by=['Actividades','Duracion'], inplace=True, ascending=False)
    
        result = df.to_html()
        cache['data'] = []

        yield result   

    return app.response_class(generate(), mimetype="text/plain")
    

if __name__ =="__main__":
    app.run(debug=True, port=8080)
    
    
@app.route('/test')
def test():
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


