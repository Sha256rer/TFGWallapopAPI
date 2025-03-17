from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class Usuario(Base):
    __tablename__ = 'Usuario'

    ID = mapped_column(Integer, primary_key=True)
    Nombre = mapped_column(Text)
    Contraseña = mapped_column(Text)
    Tracking = mapped_column(Integer)

    Busqueda: Mapped[List['Busqueda']] = relationship('Busqueda', uselist=True, back_populates='Usuario1')


class Busqueda(Base):
    __tablename__ = 'Busqueda'

    ID = mapped_column(Integer, primary_key=True, unique=True)
    Busqueda = mapped_column(Text)
    Precio = mapped_column(Numeric)
    Usuario_ = mapped_column('Usuario', ForeignKey('Usuario.ID'))
    Media = mapped_column(Numeric)

    Usuario1: Mapped[Optional['Usuario']] = relationship('Usuario', back_populates='Busqueda')
