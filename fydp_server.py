from flask import Flask
from gcm import *
import json
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import mysql.connector
import collections
import datetime
import pyowm

app = Flask(__name__)
owm = pyowm.OWM('sanitize')
tomorrow = pyowm.timeutils.tomorrow()

#----------------server functions-------------------
@app.route('/')
def test_response():
    return "server is active"

def server_connect():
    #create connection to local database
    return mysql.connector.connect(user='Jared', password='sanitize', host='127.0.0.1', database='shelf_database_test')

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

def get_weather():    
    return owm.weather_at_place('Waterloo,ca').get_weather()

def get_forecast():
    return owm.daily_forecast('Waterloo,ca', limit=1)
    #look at timeutils

def get_today():
    return datetime.datetime.now()

def check_if_time_matches(today, hour, minute):
    return (hour == today.hour) and (abs(minute-today.minute)<=5)# and (minute-today.minute)<=5)

@app.route('/gettime')
def get_time_string(houroffset=0):
    today = get_today()+datetime.timedelta(hours=houroffset)
    return str(today.year)+str(today.month).zfill(2)+str(today.day).zfill(2)+str(today.hour).zfill(2)+str(today.minute).zfill(2)

@app.route('/converttime/<time_string>')
def convert_time_string_to_text(time_string):
    return time_string[6:8]+"/"+time_string[4:6]+"/"+time_string[0:4]+time_string[8:10]+":"+time_string[10:12]

@app.route('/testsend/<testing>/<test_string>/')
def test_send(testing, test_string):
    return test_string

#----------------insert functions-------------------
@app.route('/defaultbases/')
def default_bases():    
    new_base(1,0)
    new_base(2,0)
    new_base(3,0)
    
    #return success
    return "success"

@app.route('/newbase/<int:position>/<active>/')
def new_base(position, active):    
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("INSERT INTO bases "
                "(id, position, active) "
                "VALUES (DEFAULT, %s, %s)")
    
    data = (position,active)

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
    default_desc = 'EMPTY'
    
    data = (baseid, default_type,default_weight,default_weight,default_units,default_desc,
            baseid, default_type,default_weight,default_weight,default_units,default_desc,
            baseid, default_type,default_weight,default_weight,default_units,default_desc,
            baseid, default_type,default_weight,default_weight,default_units,default_desc)

    #execute query
    cursor.execute(query,data)

    #log event
    log_event("default zones created for base " + str(baseid))

@app.route('/newnotification/<int:baseid>/<int:zoneid>/<notiftype>/<checktype>/<checkvalue>/<description>/<pushflag>/')
def new_notif(baseid, zoneid, notiftype, checktype, checkvalue, description, pushflag):
    #generate autodescriptions if necessary
    if (checktype == "forecast"):
        if (check_value == "sun"):
            description = "When sunny"
                        
        elif (check_value == "rain"):
            description = "When rainy"

        elif (check_value == "fog"):
            description = "When foggy"

        elif (check_value == "clouds"):
            description = "When cloudy"

        elif (check_value == "snow"):
            description = "When snowy"
            
    elif (checktype == "temperature"):
        description = "When temperature " + ("<" if (checkvalue[:1] == "l") else ">") + checkvalue[1:] + " degrees"

    elif (checktype == "uv"):
        description = "When UV index " + ("<" if (checkvalue[:1] == "l") else ">") + checkvalue[1:]

    elif (checktype == "weight"):
        description = "When weight " + ("<" if (checkvalue[:1] == "l") else ">") + checkvalue[1:] + "%"
                
    
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
@app.route('/activatebase/<baseid>/<active>/')
def activate_base(baseid, active):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE bases SET active = %s "
                "WHERE id = %s")
    
    data = (active, baseid)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"

@app.route('/setinitialweight/<baseid>/<zoneid>/')
def set_initial_weight(baseid, zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE zones SET initialweight = weight "
                "WHERE baseid = %s "
                "AND id = %s")
    
    data = (baseid, zoneid)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"
    

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

#b stands for batchupdateweight, dont ask why...
@app.route('/b/<int:baseid>/<weight1>/<weight2>/<weight3>/<weight4>/')
def batch_update_weight(baseid, weight1, weight2, weight3, weight4):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    weightarray = []
    weightarray.extend([weight1, weight2, weight3, weight4])

    zoneid = 1 + 4*(baseid-1)

    for weight in weightarray:
        #build query
        query = ("UPDATE zones SET weight = %s "
                    "WHERE id = %s AND baseid = %s")
    
        data = (weight, zoneid, baseid)   
    
        #execute query 
        cursor.execute(query, data)

        zoneid += 1

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return success
    return "success"
6
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

@app.route('/resetzone/<int:zoneid>/')
def reset_zone(zoneid):   
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("UPDATE zones "
             "SET type = %s, weight = %s, initialweight = %s, units = %s, description = %s "
                "WHERE id = %s")
    
    data = ("scale", 0, 0, "kg", "EMPTY", zoneid)

    #execute query 
    cursor.execute(query, data)

    #build query
    query = ("DELETE FROM notifications "
                "WHERE zoneid = %s")
    
    data = (zoneid,)

    #execute query 
    cursor.execute(query, data)

    #build query
    query = ("DELETE FROM activenotifications "
                "WHERE zoneid = %s")
    
    data = (zoneid,)

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
    query = ("SELECT id, position, active FROM bases")

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
        d['active'] = row[2]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("base list requested")

    #return json
    return jsonstring

@app.route('/getactivebasesstring/')
def get_active_bases():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, position FROM bases "
             "WHERE active = %s")

    data = ("1",)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    activebasestring = ""
    
    for row in rows:
        activebasestring += (str(row[0]) + ",")
    activebasestring = activebasestring[:-1]

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("base list requested")

    #return json
    return activebasestring

@app.route('/getzones/<int:baseid>/')
def get_zones(baseid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, baseid, type, CAST(weight AS CHAR), "
                 "CAST(initialweight AS CHAR), units, description FROM zones "
                 "WHERE baseid = %s")

    data = (baseid,)

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

@app.route('/getzone/<int:baseid>/<int:zoneid>/')
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

@app.route('/getweight/<int:baseid>/<int:zoneid>/')
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

@app.route('/getinitialweight/<int:baseid>/<int:zoneid>/')
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

@app.route('/getweights/<int:baseid>/<int:zoneid>/')
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

@app.route('/getshelfmessages/')
def get_shelf_messages():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT baseid, zoneid, type, value FROM activenotifications WHERE (acknowledged = 0)")

    #execute query 
    cursor.execute(query)

    #build JSON string for return
    rows = cursor.fetchall()

    #objects_list = []
    custommessage = ""

    for row in rows:
        baseid = str(row[0])
        zoneid = str(row[1])
        type = str(row[2])
        checkvalue = str(row[3])
        
        #23 character limit, 5 line limit
        custommessage += "Base " + baseid + " Zone " + zoneid + ":\n"
        
        if (type == "temperature"):
            custommessage += "Temperature is\n"
            custommessage += ("<" if (checkvalue[:1] == "l") else ">") + checkvalue[1:]
            custommessage += " degrees"
            
        elif (type == "uv"):
            custommessage += "UV index is\n"
            custommessage += ("<" if (checkvalue[:1] == "l") else ">") + checkvalue[1:]
            
        elif (type == "forecast"):
            custommessage += "Forecast is\n"
            custommessage += "expected to be\n"
            
            if (checkvalue == "sun"):
                custommessage += "Sunny"
                        
            elif (checkvalue == "rain"):
                custommessage += "Rainy"

            elif (checkvalue == "fog"):
                custommessage += "Foggy"

            elif (checkvalue == "clouds"):
                custommessage += "Cloudy"

            elif (checkvalue == "snow"):
                custommessage += "Snowy"
            
            
        elif (type == "weight"):
            custommessage += "Weight is\n"
            custommessage += ("<" if (checkvalue[:1] == "l") else ">") + checkvalue[1:] + "% "
            custommessage += "of\ninitial value"

        elif (type == "repeatonce"):
            custommessage += "One-time\nReminder"
            
        elif (type == "repeatdaily"):
            custommessage += "Daily\nReminder"
            
        elif (type == "repeatweekly"):
            custommessage += "Weekly\nReminder"
            
        elif (type == "repeatmonthly"):
            custommessage += "Monthly\nReminder"
            
        else:
            custommessage += "Unknown notification\r\n"
            custommessage += "type: " + type 
        
        #d = collections.OrderedDict()
        #d['message'] = custommessage
        #objects_list.append(d)

        custommessage += ","
 
    #jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()

    jsonstring = custommessage[:-1]

    #return json
    return jsonstring

#get all active notifications of type weight and their weight/initial weights from zone table
@app.route('/getlowstock')
def get_low_stock():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT an.id, an.message, CAST(z.weight AS CHAR), CAST(z.initialweight AS CHAR), an.baseid, an.zoneid, z.description "
                "FROM activenotifications AS an "
                "INNER JOIN zones AS z "
                "ON an.baseid = z.baseid AND an.zoneid = z.id "
                "WHERE an.type = %s")

    data = ("weight",)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['activenotificationid'] = row[0]
        d['message'] = row[1]
        d['weight'] = row[2]
        d['initialweight'] = row[3]
        d['baseid'] = row[4]
        d['zoneid'] = row[5]
        d['description'] = row[6]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

#gets up to 5 time notifications (not active necessarily) in chrono order from now
#need date, time (24h), notification description, zone #, is active flag
@app.route('/getupcomingreminders/')
def get_upcoming_events():
    now_string = get_time_string()
    one_day_string = get_time_string(24)

    print("Now: " + now_string + " One day: " + one_day_string)

    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    args = (one_day_string,now_string)

    #execute store procedure
    cursor.callproc('getupcomingreminders', args)

    #build JSON string for return
    for result in cursor.stored_results():
        rows = result.fetchall()
    
    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        formatted_time = convert_time_string_to_text(row[0])
        d['date'] = formatted_time[:10]
        d['time'] = formatted_time[10:]
        d['description'] = row[1]
        d['zoneid'] = row[2]
        d['isactive'] = row[3]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

#gets all active weather notifications, show description
@app.route('/getactiveweather/')
def get_active_weather():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, baseid, zoneid, message "
                "FROM activenotifications "
                "WHERE type = %s "               
                "OR type = %s "             
                "OR type = %s")

    data = ("temperature","uv","forecast")

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['baseid'] = row[1]
        d['zoneid'] = row[2]
        d['message'] = row[3]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

#gets stock notifications (if they exist) for the specified baseid/zoneid
@app.route('/getstocknotifications/<baseid>/<zoneid>/')
def get_stock_notifications(baseid, zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT n.id, n.description, n.checkvalue, CAST(z.weight AS CHAR), CAST(z.initialweight AS CHAR) "
                "FROM notifications AS n "
                "INNER JOIN zones AS z "
                "ON n.baseid = z.baseid AND n.zoneid = z.id "
                "WHERE n.checktype = %s AND n.baseid = %s AND n.zoneid = %s")

    data = ("weight", baseid, zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['notificationid'] = row[0]
        d['description'] = row[1]
        d['threshold'] = row[2]
        d['weight'] = row[3]
        d['initialweight'] = row[3]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getreminders/<baseid>/<zoneid>/')
def get_reminders(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, checkvalue, description "
                "FROM notifications "
                "WHERE notiftype = %s "
                "AND zoneid = %s "
                "AND baseid = %s")

    data = ("time",zoneid, baseid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['notificationid'] = row[0]
        formatted_time = convert_time_string_to_text(row[1])
        d['date'] = formatted_time[:10]
        d['time'] = formatted_time[10:]        
        d['description'] = row[2]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getallreminders/')
def get_all_reminders():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, checkvalue, description, baseid, zoneid "
                "FROM notifications "
                "WHERE notiftype = %s")

    data = ("time",)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['notificationid'] = row[0]
        formatted_time = convert_time_string_to_text(row[1])
        d['date'] = formatted_time[:10]
        d['time'] = formatted_time[10:]        
        d['description'] = row[2]
        d['baseid'] = row[3]
        d['zoneid'] = row[4]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring

@app.route('/getweathernotifications/<baseid>/<zoneid>/')
def get_weather_notifications(baseid, zoneid):
    #notifid, checktype, checkvalue
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT id, checktype, checkvalue "
                "FROM notifications "
                "WHERE notiftype = %s "
                "AND baseid = %s "
                "AND zoneid = %s")

    data = ("weather",baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['notificationid'] = row[0]
        d['checktype'] = row[1] 
        d['checkvalue'] = row[2]
        objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return jsonstring
             
#----------------delete functions-------------------
@app.route('/deletenotification/<notification_id>/')
def delete_notification(notification_id):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("DELETE FROM notifications "
                "WHERE id = %s")
    
    data = (notification_id,)

    #execute query 
    cursor.execute(query, data)

    #build query
    query = ("DELETE FROM activenotifications "
                "WHERE notificationid = %s")
    
    data = (notification_id,)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()

    #TODO delete active notifications with this id as well
    
    return "success"

@app.route('/deleteactivenotification/<active_notif_id>/')
def delete_active_notification(active_notif_id):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("DELETE FROM activenotifications "
                "WHERE id = %s")
    
    data = (active_notif_id,)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    return "success"

@app.route('/clearactivenotifications/')
def clear_active_notifications():
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("DELETE FROM activenotifications ")
    
    #execute query 
    cursor.execute(query)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()    

    return "success"

#----------------recurring functions-------------------
@app.route('/updatestatus/')
def update_status():
    print("running recurring funcitons at " + str(get_today()))

    #get weather and forecast data
    weather = get_weather()
    forecast = get_forecast()
    forecasted_weather = forecast.get_forecast().get_weathers()[0]
    
    uv_index_json = json.loads(owm.self_call_API("http://api.owm.io/air/1.0/uvi/current?lat=43.5&lon=-80.5"))
    uv_index = uv_index_json['value'] if 'code' not in uv_index_json else (-1)

    if (uv_index == -1):
        uv_index = 2
    
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
                    
                    if (operator.lower() == "e"):
                        should_be_active = (cur_temp == value)
                        
                    elif (operator.lower() == "g"):
                        should_be_active = (max_temp >= value)
                        
                    elif (operator.lower() == "l"):
                        should_be_active = (min_temp <= value)
                        
                    else:
                        print("Unknown operator " +operator+ ", skipping...") 
                        
                elif (check_type == "uv"):
                    if (uv_index != -1):
                        operator = check_value[:1]
                        value = float(check_value[1:])

                        if (operator.lower() == "e"):
                            should_be_active = (uv_index == value)
                        
                        elif (operator.lower() == "g"):
                            should_be_active = (uv_index >= value)
                        
                        elif (operator.lower() == "l"):
                            should_be_active = (uv_index <= value)
                        
                        else:
                            print("Unknown operator " +operator+ ", skipping...")
                        
                    else:
                        print("UV index data unavailable")
                    
                elif (check_type == "forecast"):
                    status = weather.get_status()
                    
                    if (check_value.lower() == "sun"):
                        should_be_active = (status == "sun" or forecast.will_have_sun())
                        
                    elif (check_value.lower() == "rain"):
                        should_be_active = (status == "rain" or forecast.will_have_rain())

                    elif (check_value.lower() == "fog"):
                        should_be_active = (status == "fog" or forecast.will_have_fog())

                    elif (check_value.lower() == "clouds"):
                        should_be_active = (status == "clouds" or forecast.will_have_clouds())

                    elif (check_value.lower() == "snow"):
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
                    
                if (operator.lower() == "e"):
                    should_be_active =(weight == value*initialweight)
                        
                elif (operator.lower() == "g"):
                    should_be_active = (weight >= value*initialweight)
                        
                elif (operator.lower() == "l"):
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

            #check if notification is already in active notifications
            already_active = False
            for active_notif in active_notif_dict:
                active_id = active_notif['notificationid']
                acknowledged = active_notif['acknowledged']
                if ((notif_id == active_id) and (acknowledged != "1")):
                    already_active = True
                    break

            #print(description+ ", should be: " + str(should_be_active) + ", is: " + str(already_active))

            #activate notification if needed
            if (should_be_active and not already_active):
                print("activating " + description)
                create_active_notification(notif_id, base_id, zone_id, check_type, check_value, description)

                if (pushflag == 1): #TODO: PUSH NOTIFICATIONS
                    print("sending push notification")
                    send_push_notification(notif_id, base_id, zone_id, check_type, check_value, description)

            #elif (already_active and not should_be_active):
                #print("deactivating " + description)

                        
                        
    return "success"

def create_active_notification(notif_id, base_id, zone_id, notif_type, value, message):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("INSERT INTO activenotifications "
                "(id, notificationid, baseid, zoneid, type, value, message, acknowledged) "
                "VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, DEFAULT)")
    
    data = (notif_id, base_id, zone_id, notif_type, value, "Zone " +str(zone_id)+ ": " +message)

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()
    
    #return success
    return "success"

@app.route('/pingphone/')
def test_push_notif():
    API_KEY = "sanitize"
    gcm = GCM(API_KEY, debug=False)
    data = {'message': 'Just testing Neals id', 'title': 'Shelf-M8 Notification'}
    
    sean_reg_id = 'sanitize'
    neal_reg_id = 'sanitize'
    
    
    response = gcm.plaintext_request(registration_id = sean_reg_id, data = data)
    response = gcm.plaintext_request(registration_id = neal_reg_id, data = data)
    
    return "success"

def send_push_notification(notif_id, base_id, zone_id, notif_type, check_value, description):

    custommessage = ""
    if (notif_type == "temperature"):
        custommessage += "Temperature is "
        custommessage += ("<" if (check_value[:1] == "l") else ">") + check_value[1:]
        custommessage += " degrees"
        
    elif (notif_type == "uv"):
        custommessage += "UV index is"
        custommessage += ("<" if (check_value[:1] == "l") else ">") + check_value[1:]
        
    elif (notif_type == "forecast"):
        custommessage += "Forecast is expected "
        custommessage += "to be "
        
        if (check_value == "sun"):
            custommessage += "sunny"
                    
        elif (check_value == "rain"):
            custommessage += "rainy"

        elif (check_value == "fog"):
            custommessage += "foggy"

        elif (check_value == "clouds"):
            custommessage += "cloudy"

        elif (check_value == "snow"):
            custommessage += "snowy"
        
        
    elif (notif_type == "weight"):
        zone_json = get_zone(base_id,zone_id)
        zone_data = json.loads(zone_json)
        zone_description = zone_data[0]['description']
        
        custommessage += zone_description + " is low "
        custommessage += "(" + ("<" if (check_value[:1] == "l") else ">") + check_value[1:] + "% "
        custommessage += "of initial value)"

    if (custommessage != ""):
        description = custommessage
        
    
    API_KEY = "sanitize"


    gcm = GCM(API_KEY, debug=False)

    sean_reg_id = 'sanitize'
    neal_reg_id = 'sanitize'
    
    data = {'title': 'Shelf-M8 Notification', 'message': description}

    response = gcm.plaintext_request(registration_id = sean_reg_id, data = data)
    response = gcm.plaintext_request(registration_id = neal_reg_id, data = data)
    
    return "success"

@app.route('/getcurrentweather/')
def get_current_weather():
    weather = get_weather()
    status = weather.get_status()
    cur_temp = weather.get_temperature('celsius')['temp']

    objects_list = []
    d = collections.OrderedDict()
    d['status'] = status
    d['temperature'] = cur_temp
    objects_list.append(d)
 
    jsonstring = json.dumps(objects_list)
    
    return(jsonstring)

#----------------start server-------------------
print('starting server')
server_instance = HTTPServer(WSGIContainer(app))
server_instance.listen(5001)
print('server is now running')
IOLoop.instance().start()
    
    
