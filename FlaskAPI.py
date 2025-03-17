from flask import Flask, render_template
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from models import Busqueda
from DbCon import Connector
from sqlalchemy import text
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Busquedas.db'
db = Connector()
dbalchemy = SQLAlchemy(app)


@app.route("/testcon")
def test_connection():
    try:
        result = dbalchemy.session.execute(text("SELECT 1"))
        return "Database Connection: Success ✅"
    except Exception as e:
        return f"Database Connection: Error ❌ - {str(e)}"

@app.route("/ref")
def test_reflection():
    busqueda = dbalchemy.session.query(Busqueda).all()
    result = []
    for b in busqueda:
            result.append({
            'ID': b.ID,
            'Busqueda': b.Busqueda,
            'Precio': b.Precio,
            'Media': b.Media
            })
    return {"busquedas": result}
@app.route("/")
def starting_page():
    #Necesitas hacer carpeta templates y meter las html files alli
    return render_template('index.html')

@app.route('/Busquedas', methods=['GET'])
def get_busquedas():
    db.selectall()
    response = {'message': 'success'}
    return  jsonify(response)
@app.route('/Busquedas/<id>', methods=['DELETE'])
def del_by_user(id):
    response = {'message': 'success'}
    return  jsonify(response)