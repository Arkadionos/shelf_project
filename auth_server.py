from flask import Flask
from flask import jsonify
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from data_structures import User, Channel, Users, Connections, Channels

users = Users({'Mark': User('Mark', 'marksPass', 1),
               'Kevin': User('Kevin', 'kevinsPass', 2)})

connections = Connections()

channels = Channels({2: Channel(2, 'hdhomerun_13.1', '224.2.1.2', '1002')})


# Begin external API
external_auth = Flask(__name__)


@external_auth.route('/channel-info/<int:channel_num>/<string:username>/<string:password>/<string:device_id>')
def get_channel_watching_info(channel_num, username, password, device_id):
    credentials_result, credentials_reason = users.check_user_credentials(username, password)
    if not credentials_result:
        return jsonify({'error': credentials_result})
    user = users.get_user(username)
    if not connections.authorized_connection_available(user, device_id):
        return jsonify({'error': 'Too many authorized devices'})
    connections.add_connection(username, device_id)
    if not channels.channel_exists(channel_num):
        return jsonify({'error': 'Channel does not exist'})
    channel = channels.get_channel(channel_num)
    return jsonify({'ip': channel.ip, 'port': channel.port})  # TODO: Also return encryption key

# begin internal API
internal_auth = Flask(__name__)


@internal_auth.route('/connections/user/<string:username>')
def get_connections_by_user(username):
    return jsonify({username: connections.get_user_connections(username)})


@internal_auth.route('/channels/')
def get_channel_output_mappings():
    return jsonify({'channel_input_mappings': channels.get_json_ready_list()})


print 'starting'
external_server = HTTPServer(WSGIContainer(external_auth))
external_server.listen(5000)
print 'internal up'
internal_server = HTTPServer(WSGIContainer(internal_auth))
internal_server.listen(5001)
print 'external up'
IOLoop.instance().start()
