from sqlalchemy import Table, Column, Integer, ForeignKey
from models.conexao import Base

analise_usuario = Table(
    'analise_usuario',
    Base.metadata,
    Column('analise_id', Integer, ForeignKey('analises.id'), primary_key=True),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True)
)