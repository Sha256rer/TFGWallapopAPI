from operator import truediv

import sqlalchemy
from flask import Flask, render_template
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, String, Boolean
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from main import select_product, order_by, run_scraper
from models import *
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from enum import Enum
from datetime import datetime
from zoneinfo import ZoneInfo




class EstadoBusqueda(str, Enum):
    NO_EXISTE = "1"
    YA_ASOCIADA = "2"
    NO_ASOCIADA = "3"


app = Flask(__name__)
user = "postgres"
host = "db.ivzfgdyucmzelusjtuyn.supabase.co"
port = 5432
database = "postgres"
password = "4bfjDvxScyfNnFrh"

app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?sslmode=require"
dbalchemy = SQLAlchemy(app)


@app.route("/Testcon")
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
            'ID': b.id,
            'busqueda': b.Busqueda,
            'media': b.Media
        })
    return {"busquedas": result}


@app.route("/")
def starting_page():
    #Necesitas hacer carpeta templates y meter las html files alli
    return render_template('index.html')

@app.route("/Users/Busquedas/Update/<busqueda_p>", methods=['POST'])
def update_productos(busqueda_p : str):
    productos_actuales = get_productos_by_busqueda(busqueda_p)
    if not productos_actuales:
        return "La búsqueda no existe"
    productos_update = run_scraper(busqueda_p, int(1))
    #usuario de testing
    busquedaproducto = []
    producto_ids = process_productos(productos_update)
    busqueda = get_busqueda(busqueda_p)
    for pid in producto_ids:
        curr = Busquedaproducto(productoid=pid, busquedaid=busqueda.id)
        busquedaproducto.append(curr)
    dbalchemy.session.add_all(busquedaproducto)
    dbalchemy.session.commit()

    actual_uuids = {p.uuid for p in productos_actuales}
    nuevos_productos = [p for p in productos_update if p.uuid not in actual_uuids]
    result = []
    for p in nuevos_productos:
        result.append({
            'ID': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'uuid': p.uuid,
        })
    if not result:
        return "No new products"
    else:
        return {"productos": result}



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

@app.route('/Busquedas/<busqueda_p>', methods=['GET'])
def productos_by_busqueda(busqueda_p: str):
    productos = get_productos_by_busqueda(busqueda_p=busqueda_p)
    if productos.__len__() == 0:
        return "Error, la busqueda no tiene productos o no existe"
    result = []
    for p in productos:
        result.append({
            'ID': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'uuid': p.uuid,
        })
    return {"productos": result}

@app.route('/Users/Busquedas/<user_p>', methods=['GET'])
def busquedas_by_user(user_p: str):
    busquedas = get_busquedas_by_user(user_p)
    result = []
    for bu in busquedas:
        result.append({
            'ID': bu.id,
            'busqueda': bu.busqueda,
            'media': bu.media,
        })
    return {"busquedas": result}

@app.route('/Buscar/<producto_p>&<user_p>&<order_p>', methods=['POST'])
def buscar_producto(producto_p, order_p, user_p):
    # Aquí podrías pedir el nombre o pasarlo desde Flask
    insert_user = get_user(user_p)
    if insert_user is None:
        return "El usuario no existe"
    else:
        print(insert_user)
        now = datetime.now(ZoneInfo("Europe/Madrid"))
        estado_busqueda = buscar_usuario(user_object=insert_user, busqueda_p=producto_p)
        if estado_busqueda == EstadoBusqueda.NO_EXISTE:
            productos = run_scraper(producto_p, int(order_p))
            busquedaproducto = []
            producto_ids = process_productos(productos)
            busqueda = Busqueda(busqueda=producto_p)
            dbalchemy.session.add(busqueda)
            dbalchemy.session.flush()

            # Hacer flush para que se asigne el ID de busqueda y de resultados sin hacer commit completo

            for pid in producto_ids:
                curr = Busquedaproducto(productoid=pid, busquedaid=busqueda.id)
                busquedaproducto.append(curr)
            dbalchemy.session.add_all(busquedaproducto)

            asociar_busquedausuario(producto_p, insert_user, now)
            dbalchemy.session.commit()
            return "Insertado con exito"
        elif estado_busqueda ==  EstadoBusqueda.YA_ASOCIADA:
            #Actualizar productos cuando dividamos en funciones
            return "Ya has asociado esta búsqueda"
        # Asociamos una busqueda ya existente al usuario
        elif estado_busqueda == EstadoBusqueda.NO_ASOCIADA:
            asociar_busquedausuario(producto_p, insert_user, now)
            dbalchemy.session.commit()
            return "Búsqueda asociada con éxito"


def get_user(user_p)-> Usuario:
    return dbalchemy.session.query(Usuario).filter(Usuario.name == user_p).first()


def buscar_usuario(user_object: Usuario, busqueda_p) -> EstadoBusqueda:
    # None es como null, lo devuelve si no encuentra nada
    busqueda = get_busqueda(busqueda_p)

    if not busqueda:
        #No tenemos la busqueda pero el usuario existe, registrar la busqueda y asociarla al usuario
        return EstadoBusqueda.NO_EXISTE
    else:
        curr = dbalchemy.session.query(Busquedausuario).filter(Busquedausuario.userid == user_object.id,
                                                               Busquedausuario.busquedaid == busqueda.id).first()
        if curr:
            #No hacer nada o update
            return EstadoBusqueda.YA_ASOCIADA
        else:
            #Asociar la busqueda al usuario
            return EstadoBusqueda.NO_ASOCIADA

def process_productos(productos):
    # Lista para almacenar los IDs de los productos procesados
    producto_ids = []

    # Itera sobre los productos y los inserta o actualiza en la base de datos
    for p in productos:
        stmt = insert(Producto).values(
            nombre=p.nombre,
            precio=p.precio,
            uuid=p.uuid
        ).on_conflict_do_update(
            index_elements=["uuid"],  # Maneja conflictos por 'uuid'
            set_={"nombre": p.nombre, "precio": p.precio}  # Actualiza los campos en caso de conflicto
        ).returning(Producto.id)  # Devuelve el ID del producto

        # Ejecuta la consulta y guarda el ID en la lista
        result = dbalchemy.session.execute(stmt)
        producto_ids.append(result.scalar())

    # Devuelve los IDs procesados
    return producto_ids

def asociar_busquedausuario(producto_p, insert_user, curr_time):
    busqueda = dbalchemy.session.query(Busqueda).filter(Busqueda.busqueda == producto_p).first()
    newbusquedausuario = Busquedausuario(busquedaid=busqueda.id, userid=insert_user.id, last_updated= curr_time)
    dbalchemy.session.add(newbusquedausuario)

def get_busquedas_by_user(user_p: str):
    user = get_user(user_p)
    busqueda_usuario = dbalchemy.session.query(Busquedausuario).filter(Busquedausuario.userid == user.id).all()
    busqueda_ids = [bu.busquedaid for bu in busqueda_usuario]
    return dbalchemy.session.query(Busqueda).filter(Busqueda.id.in_(busqueda_ids)).all()

def get_busqueda(busqueda_p: str) -> Busqueda:
    return dbalchemy.session.query(Busqueda).filter(Busqueda.busqueda == busqueda_p).first()

def get_productos_by_busqueda(busqueda_p: str) -> list[Producto]:
    busqueda = get_busqueda(busqueda_p)
    if not busqueda:
        return []
    busquedaproducto = dbalchemy.session.query(Busquedaproducto).filter(
        Busquedaproducto.busquedaid == busqueda.id).all()
    producto_ids = [bp.productoid for bp in busquedaproducto]
    productos = dbalchemy.session.query(Producto).filter(Producto.id.in_(producto_ids)).all()
    return productos