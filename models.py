from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, Numeric, Text, DateTime
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Numeric, ForeignKey, Table
from typing import List, Optional


class Busquedausuario(Base):
    __tablename__ = 'busquedauser'

    # Eliminamos id, la PK es busquedaid + userid
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    busquedaid: Mapped[int] = mapped_column(ForeignKey("busqueda.id"))
    userid : Mapped[int] = mapped_column(ForeignKey("user.id"))
    frequency: Mapped[int] = mapped_column(Integer)
    last_notified: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Relación hacia Busqueda
    busqueda: Mapped["Busqueda"] = relationship(back_populates="usuario_relaciones")
    # Relación hacia Usuario (ojo que aquí el atributo debe llamarse 'usuario' para coincidir con back_populates)
    usuario: Mapped["Usuario"] = relationship(back_populates="usuario_relaciones")


class Usuario(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    # Aquí el back_populates debe coincidir con el nombre en Busquedausuario que apunta a Usuario: 'usuario'
    usuario_relaciones: Mapped[List["Busquedausuario"]] = relationship(
        "Busquedausuario", back_populates="usuario"
    )


class Busqueda(Base):
    __tablename__ = 'busqueda'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    busqueda: Mapped[str] = mapped_column(Text)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    media: Mapped[float] = mapped_column(Numeric)
    shortest_frequency: Mapped[int] = mapped_column(Integer)
    # back_populates apunta a busqueda en Busquedausuario
    usuario_relaciones: Mapped[List["Busquedausuario"]] = relationship(
        "Busquedausuario", back_populates='busqueda'
    )

    producto_relaciones: Mapped[List["Busquedaproducto"]] = relationship(
        "Busquedaproducto", back_populates='busqueda'
    )


class Busquedaproducto(Base):
    __tablename__ = 'busquedaproducto'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    busquedaid: Mapped[int] = mapped_column(ForeignKey("busqueda.id"))
    productoid : Mapped[int] = mapped_column(ForeignKey("producto.id"))

    busqueda: Mapped["Busqueda"] = relationship(back_populates="producto_relaciones")
    producto: Mapped["Producto"] = relationship(back_populates="producto_relaciones")


class Producto(Base):
    __tablename__  = 'producto'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(Text)
    precio: Mapped[float] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    producto_relaciones: Mapped[List["Busquedaproducto"]] = relationship(
        "Busquedaproducto", back_populates='producto'
    )
