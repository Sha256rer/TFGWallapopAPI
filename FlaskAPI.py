from operator import truediv

import sqlalchemy
from flask import Flask, render_template, request
from flask import jsonify
from flask.cli import load_dotenv
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
from dotenv import load_dotenv
import os




class EstadoBusqueda(str, Enum):
    NO_EXISTE = "1"
    YA_ASOCIADA = "2"
    NO_ASOCIADA = "3"


app = Flask(__name__)
load_dotenv("connection.env")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DBNAME = os.getenv("DB_NAME")


app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
dbalchemy = SQLAlchemy(app)

@app.route("/Users/Updates", methods=['GET'])
def get__users_to_notify():
    busquedas_users = dbalchemy.session.query(Busquedausuario).all()
    busquedausuarios_a_notificar = []
    now = datetime.now(ZoneInfo("Europe/Madrid"))
    for b in busquedas_users:
        if b.last_notified:
            diferencia = now - b.last_notified
            diferencia_en_int = int(diferencia.total_seconds() // 60)
            if b.frequency:
                if b.frequency < diferencia_en_int:

                    busquedausuarios_a_notificar.append({
                        'id': b.id,
                        'userid': b.userid,
                        'busquedaid': b.busquedaid,
                        'last_notified': b.last_notified.isoformat(),
                        'frequency': b.frequency
                    })
                else:
                    print("Todavía no toca")
            else:
                print("Error, no hay frecuencia establecida")
        else:
            busquedausuarios_a_notificar.append({
                'id': b.id,
                'userid': b.userid,
                'busquedaid': b.busquedaid,
                'last_notified': b.last_notified.isoformat(),
                'frequency': b.frequency
            })

    return jsonify(busquedausuarios_a_notificar)


@app.route("/Users/Updates/<busquedausuario_id>", methods=['GET'])
def get_new_products_since_last_notified(busquedausuario_id):
    busquedausuario = dbalchemy.session.query(Busquedausuario).filter(Busquedausuario.id == busquedausuario_id).first()
    if not busquedausuario:
        return "Error: Busquedausuario not found", 404

    last_notified = busquedausuario.last_notified
    busqueda_id = busquedausuario.busquedaid


    productos = dbalchemy.session.query(Producto).join(Busquedaproducto).filter(
        Busquedaproducto.busquedaid == busqueda_id,
        Producto.created_at > last_notified
    ).all()
    user = dbalchemy.session.query(Usuario).filter(Usuario.id == busquedausuario.userid).first()
    busqueda = dbalchemy.session.query(Busqueda).filter(Busqueda.id == busquedausuario.busquedaid).first()
    result = {
        'user_info': {
            'username': user.name,
            'busqueda': busqueda.busqueda
        },
        'productos': []
    }
    for p in productos:
        result["productos"].append({
            'nombre': p.nombre,
            'precio': p.precio,
            'created_at': p.created_at.isoformat()
        })
    now = datetime.now(ZoneInfo("Europe/Madrid"))
    busquedausuario.last_notified = now
    dbalchemy.session.commit()
    print(result)
    return jsonify(result)


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

#Metodo que actualiza todas las busquedas utilizando la shortest_frequency, que es un campo calculado que vale
#lo que vale la frecuencia de actualización del usuario cuya frecuencia de actualización para la busqueda sea menor
@app.route("/Busquedas/Update/All", methods=['GET'])
def get_busquedas_to_update():
    last_updates = dbalchemy.session.query(Busqueda).all()
    now = datetime.now(ZoneInfo("Europe/Madrid"))
    result = []
    for b in last_updates:
        if b.last_updated and b.shortest_frequency:
            # Diferencia entre el momento actual y la ultima actualización
            diferencia = now - b.last_updated
            diferencia_en_int = int(diferencia.total_seconds() // 60)
            # Si la frecuencia de actualización mas corta es mas pequeña que la diferencia entre ahora y la última actualizacion
            #Debemos actualizar de nuevo
            print(diferencia_en_int)
            print(b.shortest_frequency)
            if b.shortest_frequency < diferencia_en_int:
                update_productos(b.busqueda)
                result.append(f"Busqueda ID {b.id} - Time difference: {diferencia}")
        else:
            print("last_updated o shortest_frequency son null")
            b.last_updated = now
    dbalchemy.session.commit()
    return result

#Funcion que actualiza una busqueda en concreto y nos devuelve los productos nuevos
@app.route("/Users/Busquedas/Update/<busqueda_p>", methods=['POST'])
def update_productos(busqueda_p : str):
    now = datetime.now(ZoneInfo("Europe/Madrid"))
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
    set_updated_busqueda(busqueda_p, now)
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


#Devuelve una lista de todos los usuarios
@app.route('/Users', methods=['GET'])
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

@app.route('/Users/<p_name>', methods=['GET'])
def get_user_id(p_name):
    usuario = dbalchemy.session.query(Usuario).filter(Usuario.name == p_name).first()
    return jsonify(usuario.id)
#Devuelve todos los productos de una busqueda
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
#Devuelve todas las busquedas de un usuario concreto
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

#Busca un producto utilizando un usuario y orden concreto
@app.route('/Buscar/<producto_p>', methods=['POST'])
def buscar_producto(producto_p):
    # Aquí podrías pedir el nombre o pasarlo desde Flask
    frequency = request.form.get("frequency", int)
    order_p = request.form.get("order", str)
    user_p = request.form.get("user", str)
    insert_user = get_user(user_p)
    if insert_user is None:
        return "El usuario no existe"
    elif frequency is None:
        return "No estableciste frecuencia"
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
            set_updated_busqueda(producto_p, now)
            asociar_busquedausuario(producto_p, insert_user, frequency)
            dbalchemy.session.commit()
            return "Insertado con exito"
        elif estado_busqueda ==  EstadoBusqueda.YA_ASOCIADA:
            #Actualizar productos cuando dividamos en funciones
            return "Ya has asociado esta búsqueda"
        # Asociamos una busqueda ya existente al usuario
        elif estado_busqueda == EstadoBusqueda.NO_ASOCIADA:
            set_updated_busqueda(producto_p, now)
            asociar_busquedausuario(producto_p, insert_user, frequency)
            dbalchemy.session.commit()
            return "Búsqueda asociada con éxito"

#Get user por nombre
def get_user(user_p)-> Usuario:
    return dbalchemy.session.query(Usuario).filter(Usuario.name == user_p).first()

#Encuentra si una busqueda existe o no, y también si esta vinculada a un usuario o no
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

#función para actualizar la tabla producto a partir de una lista de los mimsmo
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
#Función para asociar una búsqueda a un usuario
def asociar_busquedausuario(producto_p, insert_user, frequency):
    busqueda = dbalchemy.session.query(Busqueda).filter(Busqueda.busqueda == producto_p).first()
    newbusquedausuario = Busquedausuario(busquedaid=busqueda.id, userid=insert_user.id, frequency=frequency)
    dbalchemy.session.add(newbusquedausuario)
#Funcion para establecer la última ve que una búsqueda ha sido actualizada
def set_updated_busqueda(producto_p, curr_time):
    busqueda = dbalchemy.session.query(Busqueda).filter(Busqueda.busqueda == producto_p).first()
    if busqueda:
        busqueda.last_updated = curr_time   # Example update logic
        dbalchemy.session.commit()
#Devuelve todas las busquedas de un usuario
def get_busquedas_by_user(user_p: str):
    user = get_user(user_p)
    busqueda_usuario = dbalchemy.session.query(Busquedausuario).filter(Busquedausuario.userid == user.id).all()
    busqueda_ids = [bu.busquedaid for bu in busqueda_usuario]
    return dbalchemy.session.query(Busqueda).filter(Busqueda.id.in_(busqueda_ids)).all()
#Devuelve una búsqueda por el texto buscado
def get_busqueda(busqueda_p: str) -> Busqueda:
    return dbalchemy.session.query(Busqueda).filter(Busqueda.busqueda == busqueda_p).first()
#Devuelve todos los productos de una búsqueda
def get_productos_by_busqueda(busqueda_p: str) -> list[Producto]:
    busqueda = get_busqueda(busqueda_p)
    if not busqueda:
        return []
    busquedaproducto = dbalchemy.session.query(Busquedaproducto).filter(
        Busquedaproducto.busquedaid == busqueda.id).all()
    producto_ids = [bp.productoid for bp in busquedaproducto]
    productos = dbalchemy.session.query(Producto).filter(Producto.id.in_(producto_ids)).all()
    return productos