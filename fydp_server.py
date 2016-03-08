from flask import Flask
import json
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import mysql.connector
import collections
import datetime
import pyowm

app = Flask(__name__)
owm = pyowm.OWM('d5210053d4c8c2dff1d59bc1fcf3368b')
#today = pyowm.timeutils.today()
tomorrow = pyowm.timeutils.tomorrow()

#----------------server functions-------------------
@app.route('/')
def test_response():
    return "server is active"

def server_connect():
    #create connection to local database
    return mysql.connector.connect(user='Jared', password='heylookadatabasepassword', host='127.0.0.1', database='shelf_database_test')

def get_json(json_list):
    if (len(json_list) == 0):
        return "empty list"
    else:
        #return jsonify({'listtest',json_list})
        return json.dumps(json_list)

def log_event(log_entry):
    with open("serverlog.txt", "a") as logfile:
        logfile.write(str(datetime.datetime.now()) + ": " + str(log_entry) + "\n")
        logfile.close()
    print(str(log_event))
        

#----------------insert functions-------------------
@app.route('/newbase/<int:position>')
def new_base(position):    
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("INSERT INTO bases "
                "(id, position) "
                "VALUES (DEFAULT, %s)")
    
    data = (position,)

    #execute query
    cursor.execute(query,data)
    baseid = cursor.lastrowid

    #setup defaults for new base
    default_zones(baseid, cnx, cursor)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("new base created at position " + str(position))
    
    #return success
    return "success"

def default_zones(baseid, cnx, cursor):
    #build query
    query = ("INSERT INTO zones "
                "(id, baseid, type, weight, initialweight, units, description) "
                "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s),"
                "(DEFAULT, %s, %s, %s, %s, %s, %s),"
                "(DEFAULT, %s, %s, %s, %s, %s, %s),"
                "(DEFAULT, %s, %s, %s, %s, %s, %s)")

    default_type = 'scale'
    default_weight = 0
    default_units = 'kg'
    default_desc = 'Enter Description Here'
    
    data = (baseid, default_type,default_weight,default_weight,default_units,default_desc,
            baseid, default_type,default_weight,default_weight,default_units,default_desc,
            baseid, default_type,default_weight,default_weight,default_units,default_desc,
            baseid, default_type,default_weight,default_weight,default_units,default_desc)

    #execute query
    cursor.execute(query,data)

    #log event
    log_event("default zones created for base " + str(baseid))

@app.route('/newnotification/<int:baseid>/<int:zoneid>/<notiftype>/<checktype>/<checkvalue>/<description>/<pushflag>')
def new_notif(baseid, zoneid, notiftype, checktype, checkvalue, description, pushflag):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("INSERT INTO notifications "
                "(id, baseid, zoneid, notiftype, checktype, checkvalue, description, pushflag) "
                "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s)")
    
    data = (baseid, zoneid, notiftype, checktype, checkvalue, description, pushflag)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("new notification created for zone " + str(zoneid) + " of type " + str(notiftype) + ", " + str(checktype) + " with value " + str(checkvalue))

    #return success
    return "success"

#----------------update functions-------------------
@app.route('/updateweight/<int:baseid>/<int:zoneid>/<weight>/')
def update_weight(baseid, zoneid, weight):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE zones SET weight = %s "
                "WHERE id = %s AND baseid = %s")
    
    data = (weight, zoneid, baseid)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"

@app.route('/updateinitialweight/<int:baseid>/<int:zoneid>/<weight>/')
def update_initialweight(baseid, zoneid, weight):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE zones SET initialweight = %s "
                "WHERE id = %s AND baseid = %s")
    
    data = (weight, zoneid, baseid)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"

@app.route('/updateunits/<baseid>/<zoneid>/<units>/')
def update_units(baseid, zoneid, units):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE zones SET units = %s "
                "WHERE id = %s AND baseid = %s")
    
    data = (units, zoneid, baseid)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"

@app.route('/updatedescription/<int:baseid>/<int:zoneid>/<string:desc>/')
def update_desc(baseid, zoneid, desc):
    #check that description isnt too long
    if (len(desc) > 100):
        return "incorrect input"

    
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE zones SET description = %s "
                "WHERE id = %s AND baseid = %s")
    
    data = (desc, zoneid, baseid)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"


#----------------query functions-------------------
@app.route('/getbases/')
def get_bases():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, position FROM bases")

    #execute query 
    cursor.execute(query)

    #build JSON string for return
    rows = cursor.fetchall()    
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['position'] = row[1]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("base list requested")

    #return json
    return jsonstring

@app.route('/getzones/<int:baseid>')
def get_zones(baseid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, baseid, type, CAST(weight AS CHAR), "
                 "CAST(initialweight AS CHAR), units, description FROM zones "
                 "WHERE baseid = %s")

    data = (baseid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['baseid'] = row[1]
        d['type'] = row[2]
        d['weight'] = row[3]
        d['initialweight'] = row[4]
        d['units'] = row[5]
        d['description'] = row[6]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #jsonstring = jsonify({'test':jsonify({'test2':rows})})

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("zones for base " + str(baseid) + " requested")

    #return json
    return jsonstring

@app.route('/getzone/<int:baseid>/<int:zoneid>')
def get_zone(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, baseid, type, CAST(weight AS CHAR), "
             "CAST(initialweight AS CHAR), units, description FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['baseid'] = row[1]
        d['type'] = row[2]
        d['weight'] = row[3]
        d['initialweight'] = row[4]
        d['units'] = row[5]
        d['description'] = row[6]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("zone " + str(zoneid) + " for base " + str(baseid) + " requested")

    #return json
    return jsonstring

@app.route('/getweight/<int:baseid>/<int:zoneid>')
def get_weight(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT CAST(weight AS CHAR) FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['weight'] = row[0]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getinitialweight/<int:baseid>/<int:zoneid>')
def get_initialweight(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT CAST(initialweight AS CHAR) FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['initialweight'] = row[0]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getweights/<int:baseid>/<int:zoneid>')
def get_weights(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT CAST(weight AS CHAR), CAST(initialweight AS CHAR) FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)
    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['weight'] = row[0]
        d['initialweight'] = row[1]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getnotifications/')
def get_notifications():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, baseid, zoneid, notiftype, checktype, checkvalue, description, pushflag FROM notifications")

    #execute query 
    cursor.execute(query)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['baseid'] = row[1]
        d['zoneid'] = row[2]
        d['notiftype'] = row[3]
        d['checktype'] = row[4]
        d['checkvalue'] = row[5]
        d['description'] = row[6]
        d['pushflag'] = row[7]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getactivenotifications/')
def get_active_notifications():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, baseid, zoneid, type, value, message, notificationid, acknowledged FROM activenotifications")

    #execute query 
    cursor.execute(query)

    #build JSON string for return
    rows = cursor.fetchall()
    
    #jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['baseid'] = row[1]
        d['zoneid'] = row[2]
        d['type'] = row[3]
        d['value'] = row[4]
        d['message'] = row[5]
        d['notificationid'] = row[6]
        d['acknowledged'] = row[7]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

#----------------recurring functions-------------------
@app.route('/updatestatus')
def update_status():
    print("running recurring funcitons at " + str(get_today()))

    #get weather and forecast data
    weather = get_weather()
    forecast = get_forecast()
    forecasted_weather = forecast.get_forecast().get_weathers()[0]

    uv_index_json = json.loads(owm.self_call_API("http://api.owm.io/air/1.0/uvi/current?lat=43.5&lon=-80.5"))
    uv_index = uv_index_json['value'] if 'code' not in uv_index_json else (-1)
    
    #get list of defined notifications and active notifications
    notifications = get_notifications()
    activenotifications = get_active_notifications()

    notif_dict = "empty" if notifications == "empty list" else json.loads(notifications)
    active_notif_dict = "empty" if activenotifications == "empty list" else json.loads(activenotifications)
    
    #for each notification, check if it needs to be active and if it is in active notifications
    if notif_dict is not "empty":
        for notif in notif_dict:
            notif_id = notif['id']
            base_id = notif['baseid']
            zone_id = notif['zoneid']
            notif_type = notif['notiftype']
            check_type = notif['checktype']
            check_value = notif['checkvalue'] 
            description = notif['description']
            pushflag = notif['pushflag']
            #print(description)

            #check if notification should be active right now
            should_be_active = False            
            if (notif_type == "weather"): #notification based on weather data
                if (check_type == "temperature"):
                    cur_temp = weather.get_temperature('celsius')['temp']
                    min_temp = forecasted_weather.get_temperature('celsius')['min']
                    max_temp = forecasted_weather.get_temperature('celsius')['max']
                    operator = check_value[:1]
                    value = float(check_value[1:])
                    
                    if (operator == "="):
                        should_be_active = (cur_temp == value)
                        
                    elif (operator == ">"):
                        should_be_active = (max_temp >= value)
                        
                    elif (operator == "<"):
                        should_be_active = (min_temp <= value)
                        
                    else:
                        print("Unknown operator " +operator+ ", skipping...") 
                        
                elif (check_type == "uv"):
                    if (uv_index != -1):
                        operator = check_value[:1]
                        value = float(check_value[1:])

                        if (operator == "="):
                            should_be_active = (uv_index == value)
                        
                        elif (operator == ">"):
                            should_be_active = (uv_index >= value)
                        
                        elif (operator == "<"):
                            should_be_active = (uv_index <= value)
                        
                        else:
                            print("Unknown operator " +operator+ ", skipping...")
                        
                    else:
                        print("UV index data unavailable")
                    
                elif (check_type == "forecast"):
                    status = weather.get_status()
                    
                    if (check_value == "sun"):
                        should_be_active = (status == "sun" or forecast.will_have_sun())
                        
                    elif (check_value == "rain"):
                        should_be_active = (status == "rain" or forecast.will_have_rain())

                    elif (check_value == "fog"):
                        should_be_active = (status == "fog" or forecast.will_have_fog())

                    elif (check_value == "clouds"):
                        should_be_active = (status == "clouds" or forecast.will_have_clouds())

                    elif (check_value == "snow"):
                        should_be_active = (status == "snow" or forecast.will_have_snow())

                    else:
                        print("Unknown forecast " +check_value+ ", skipping...")
                        
                    
                else:
                    print("Unknown weather check type " +check_type+ ", skipping...")             
                
            elif (notif_type == "weight"): #notification based on weight data
                operator = check_value[:1]
                value = float(check_value[1:])/100
                weight_values = json.loads(get_weights(base_id, zone_id))
                weight = float(weight_values[0]['weight'])
                initialweight = float(weight_values[0]['initialweight'])
                    
                if (operator == "="):
                    should_be_active =(weight == value*initialweight)
                        
                elif (operator == ">"):
                    should_be_active = (weight >= value*initialweight)
                        
                elif (operator == "<"):
                     should_be_active = (weight <= value*initialweight)
                        
                else:
                    print("Unknown operator " +operator+ ", skipping...") 
                
            elif (notif_type == "time"): #notification based on a schedule
                today = get_today() #date object
                year = int(check_value[0:4])
                month = int(check_value[4:6])
                day = int(check_value[6:8])
                hour = int(check_value[8:10])
                minute = int(check_value[10:12])
                time_match = check_if_time_matches(today, hour, minute)
                notif_date = datetime.date(year, month, day)

                if (check_type == "repeatdaily"):
                    should_be_active = time_match
                    
                elif (check_type == "repeatweekly"):
                    should_be_active = time_match and (today.weekday() == notif_date.weekday()) and (today >= notif_date)
                    
                elif (check_type == "repeatmonth"):
                    should_be_active = time_match and (today.day == day) and (today >= notif_date)
                    
                elif (check_type == "repeatonce"):
                    should_be_active = time_match and (today.day == day) and (today.month == month) and (today.year == year)
                    
                else:
                    print("Unknown check type " +check_type+ ", skipping...")
                
            else: #ignore alternate types
                print("Unknown notification type " +notif_type+ ", skipping...")

            #activate notification if needed
            if (should_be_active):
                #check if notification is already in active notifications
                already_active = False
                for active_notif in active_notif_dict:
                    active_id = active_notif['notificationid']
                    acknowledged = active_notif['acknowledged']
                    if (id == active_id and acknowledged == "0"):
                        already_active = True
                        break

                if (not already_active):
                    print("activating " + description)
                    create_active_notification(notif_id, base_id, zone_id, notif_type, check_value, description)

                    if (pushflag == "1"): #TODO: PUSH NOTIFICATIONS
                        
            
                    


    return "success"

def get_weather():    
    return owm.weather_at_place('Waterloo,ca').get_weather()

def get_forecast():
    return owm.daily_forecast('Waterloo,ca', limit=1)
    #look at timeutils

def get_today():
    return datetime.datetime.now()

def check_if_time_matches(today, hour, minute):
    return (hour == today.hour) and (abs(minute-today.minute)<=5)

def create_active_notification(notif_id, base_id, zone_id, notif_type, value, message):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("INSERT INTO activenotifications "
                "(id, notificationid, baseid, zoneid, type, value, message, acknowledged) "
                "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, DEFAULT)")
    
    data = (notif_id, base_id, zone_id, notif_type, value, message)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()
    
    #return success
    return "success"

#----------------start server-------------------
print('starting server')
server_instance = HTTPServer(WSGIContainer(app))
server_instance.listen(5001)
print('server is now running')
IOLoop.instance().start()
    
    
