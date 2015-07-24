from flask import Flask
import json
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import mysql.connector
import collections
import datetime

app = Flask(__name__)

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

@app.route('/newnotification/<int:zoneid>/<type>/<value>/')
def new_notif(zoneid, type, value):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("INSERT INTO notifications "
                "(id, zoneid, type, value, description) "
                "VALUES (DEFAULT, %s, %s, %s, %s)")
    
    data = (zoneid, type, value, 'this is a test description')

    #execute query 
    cursor.execute(query, data)

    #commit all changes
    cnx.commit()

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("new notification created for zone " + str(zoneid) + " of type " + str(type) + " with value " + str(value))

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
    
    json = get_json(rows)    

    #close cursor and connection
    cursor.close
    cnx.close()

    #log event
    log_event("base list requested")

    #return json
    return json

@app.route('/getzones/<int:baseid>')
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
    
    jsonstring = get_json(rows)

    objects_list = []
    for row in rows:
        d = collections.OrderedDict()
        d['id'] = row[0]
        d['baseid'] = row[1]
        d['type'] = row[2]
        d['weight'] = row[3]
        d['initialweight'] = row[4]
        d['units'] = row[5]
        d['desc'] = row[6]
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
    query = ("SELECT id, baseid, type, weight, initialweight, units, description FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    json = get_json(rows)    

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return json

@app.route('/getweight/<int:baseid>/<int:zoneid>')
def get_weight(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT weight FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    json = get_json(rows)    

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return json

@app.route('/getinitialweight/<int:baseid>/<int:zoneid>')
def get_initialweight(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT initialweight FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    json = get_json(rows)    

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return json

@app.route('/getweights/<int:baseid>/<int:zoneid>')
def get_weights(baseid,zoneid):
    #create connection and cursor
    cnx = server_connect()
    cursor = cnx.cursor()

    #build query
    query = ("SELECT weight, initialweight FROM zones "
                 "WHERE baseid = %s AND id = %s")

    data = (baseid,zoneid)

    #execute query 
    cursor.execute(query, data)

    #build JSON string for return
    rows = cursor.fetchall()
    
    json = get_json(rows)    

    #close cursor and connection
    cursor.close
    cnx.close()    

    #return json
    return json

#----------------start server-------------------
print('starting server')
server_instance = HTTPServer(WSGIContainer(app))
server_instance.listen(5001)
print('server is now running')
IOLoop.instance().start()
    
    
