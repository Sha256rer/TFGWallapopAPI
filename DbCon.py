import sqlite3


from Busqueda import Busqueda

class Connector:

    def __new__(cls):
        instance = super(Connector, cls).__new__(cls)
        return instance

    def __init__(self):

        self.conn = sqlite3.connect('instance/Busquedas.db')

    def inserta(self, row : Busqueda):
        query : str = "INSERT INTO Busqueda(Busqueda, Precio, Usuario) values (?,?,?)"
        data_tuple = (row.busqueda, row.precio, row.usuario)
        self.conn.execute(query, data_tuple)
        self.conn.commit()

    def selectall(self):
        query = "SELECT * FROM Busqueda"
        rows = self.conn.execute(query).fetchall()
        return rows

    def selectbyUser(self, user : str):
        query = "SELECT * FROM Busqueda where Usuario = " +str(user)
        rows = self.conn.execute(query).fetchall()
        return rows

    def deleteByUser(self, user: str):
        query = "DELETE FROM Busqueda where Usuario = " +  str(user)
        print(query)
        self.conn.execute(query)