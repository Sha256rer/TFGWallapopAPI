from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Numeric, ForeignKey
from typing import List, Optional

class Usuario(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    passw: Mapped[str] = mapped_column(Text, name="pass")

    busquedas: Mapped[List['Busqueda']] = relationship(
        'Busqueda',
        back_populates='usuario',
        uselist=True
    )
class Producto(Base):
    __tablename__  = 'producto'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(Text)
    precio: Mapped[float] = mapped_column(Numeric)


class Busqueda(Base):
    __tablename__ = 'busqueda'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    busqueda: Mapped[str] = mapped_column(Text)

    usuario_id: Mapped[int] = mapped_column(ForeignKey('user.id'), name="user")
    #Se utiliza name para poner el nombre distinto a la columna orignal
    media: Mapped[float] = mapped_column(Numeric)

    usuario: Mapped[Optional['Usuario']] = relationship(
        'Usuario',
        back_populates='busquedas'
    )
    #https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    #Forma de vincular tabla padre e hija bidireccionalmente, para q cuando actualicemos en una se actualice la otra