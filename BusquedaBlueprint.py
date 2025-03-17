from flask import Blueprint
from flask import jsonify
from DbCon import  Connector
busquedabp = Blueprint("busquedabp",__name__)
db = Connector()
busquedabp.route('/', defaults={'page': 'api/v1/'})
busquedabp.route('Busquedas', methods=['GET'])
def get_users(self):
    response = {'message': 'success'}
    return jsonify(response)

busquedabp.route('Busquedas/<id>', methods=['DELETE'])

def del_by_user(self, id):
    db.deleteByUser(id)
    response = {'message': 'success'}
    return jsonify(response)