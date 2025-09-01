from sqlalchemy import Column, Integer, String
from models.conexao import Base, engine

class Testador(Base):
    __tablename__ = "testadores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    faixa_etaria = Column(String(255), nullable=False)
    genero = Column(String(255), nullable=False)

def __init__(self, nome, email, faixa_etaria, genero):
        self.nome = nome
        self.email = email
        self.faixa_etaria = faixa_etaria
        self.genero = genero