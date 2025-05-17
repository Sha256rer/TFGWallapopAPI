from flask import Flask, render_template
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, String

from main import select_product, order_by, run_scraper
from models import *
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
user = "postgres"
host = "db.ivzfgdyucmzelusjtuyn.supabase.co"
port = 5432
database = "postgres"
password = "4bfjDvxScyfNnFrh"

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?sslmode=require"
dbalchemy = SQLAlchemy(app)


@app.route("/testcon")
def test_connection():
    try:
        result = dbalchemy.session.execute(text("SELECT 1"))
        return "Database Connection: Success ✅"
    except Exception as e:
        return f"Database Connection: Error ❌ - {str(e)}"

@app.route("/Busquedas", methods=['GET'])
def get_allbusquedas():
    busqueda = dbalchemy.session.query(Busqueda).all()
    result = []
    for b in busqueda:
            result.append({
            'ID': b.ID,
            'busqueda': b.Busqueda,
            'media': b.Media
            })
    return {"busquedas": result}
@app.route("/")
def starting_page():
    #Necesitas hacer carpeta templates y meter las html files alli
    return render_template('index.html')


@app.route('/users', methods=['GET'])
def get_allusers():
    usuarios = dbalchemy.session.query(Usuario).all()
    result = []
    for u in usuarios:
        result.append({
            'ID': u.id,
            'nombre': u.name,  # Creo que quieres el nombre aquí, no 'busqueda'
            'password': u.passw  # Ojo con exponer contraseñas, generalmente no se recomienda
        })
    return {"usuarios": result}


@app.route('/Busquedas/<user>', methods=['GET'])
def busquedas_by_user(user : String):
    busqueda = dbalchemy.session.query(Busqueda).filter(Busqueda.usuario.has(name=user)).all()
    result = []
    for b in busqueda:
        result.append({
            'ID': b.ID,
            'busqueda': b.Busqueda,
            'media': b.Media
        })
    return {"busquedas": result}

@app.route('/Buscar/<producto_p>&<user_p>&<order_p>', methods=['POST'])
def buscar_producto(producto_p, user_p, order_p):
   # Aquí podrías pedir el nombre o pasarlo desde Flask
    resultados = run_scraper(producto_p, order_p, user_p)
    dbalchemy.session.add_all(resultados)
    dbalchemy.session.commit()
    return {"rest": resultados}