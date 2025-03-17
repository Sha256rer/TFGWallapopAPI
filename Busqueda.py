from decimal import Decimal

class Busqueda:
    def __init__(self ,busqueda : str, precio :float , usuario : str):
        self._busqueda = busqueda
        self._precio = precio
        self._usuario = usuario
    @property
    def busqueda(self):
        return self._busqueda
    @busqueda.setter
    def busqueda(self, value : str):
        self._busqueda = value
    @property
    def usuario(self):
        return self._usuario
    @usuario.setter
    def usuario(self, value : str):
        self._usuario = value
    @property
    def precio(self):
        return self._precio
    @precio.setter
    def precio(self, value):
        self._precio = value
