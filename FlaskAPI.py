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

    productos = run_scraper(producto_p, order_p, user_p)
    busquedaproducto = []
    producto_ids = []
    busqueda = Busqueda(busqueda=producto_p)

    dbalchemy.session.add(busqueda)
    dbalchemy.session.flush()

   # Hacer flush para que se asigne el ID de busqueda y de resultados sin hacer commit completo
    for p in  productos:
        #Usuamos funcion core, no sql alchemy para poder establecer el on conflict, si no da un fallo.
        #Si el producto ya esta guardado, lo actualiza
        stmt=insert(Producto).values(
            nombre=p.nombre,
            precio=p.precio,
            uuid= p.uuid
        ).on_conflict_do_update(
            index_elements=["uuid"],
            set_={"nombre": p.nombre, "precio": p.precio}
        ).returning(Producto.id) #Nos devolvera el id del producto que actualizamos
        #Guardamos las ids de producto en un array, no podemos pedirselas a un objeto como con busqueda
        result = dbalchemy.session.execute(stmt)
        prod_id = result.scalar()
        producto_ids.append(prod_id)


    for pid in producto_ids:
        curr = Busquedaproducto(productoid= pid, busquedaid = busqueda.id)
        busquedaproducto.append(curr)
    dbalchemy.session.add_all(busquedaproducto)

    dbalchemy.session.commit()
    return "Insertado con exito"


def usuario_existe(user_p) -> bool:
    user = dbalchemy.session.query(Usuario).filter(Usuario.name == user_p).first()
    if user is not None:
        return True
    else:
        return False

def busqueda_usuario(user_p, busqueda_p) -> bool:
    # None es como null, lo devuelve si no encuentra nada
    user = dbalchemy.session.query(Usuario).filter(Usuario.name == user_p).first()
    if usuario_existe(user_p):
        busqueda = dbalchemy.session.query(Busqueda).filter(Busqueda.busqueda == busqueda_p).first()
        if not busqueda:
        #No tenemos la busqueda pero el usuario existe, registrar la busqueda y asociarla al usuario
            return False
        else:
         curr = dbalchemy.session.query(Busquedausuario).filter(Busquedausuario.userid == user.id,
                                                               Busquedausuario.busquedaid == busqueda.id).first()
        if curr:
            #No hacer nada o update
            print("Ya tienes esta búsqueda hecha")
        else:
            #Asociar la busqueda al usuario
            print("Todavía no la has hecho")
        return user.str()
    else:
        return "El usuario no existe"
