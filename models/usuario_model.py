from sqlalchemy import Boolean, Column, Integer, String, Date, ForeignKey
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from models.conexao import Base, engine  # Certifique-se de que a conexão com o banco está correta
from models.associacoes import analise_usuario

class Usuario(Base, UserMixin):
    __tablename__ = "usuarios"

    # Definindo a chave primária com autoincremento
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200))
    email = Column(String(100))
    telefone = Column(String(15))
    data_nascimento = Column(Date)
    login = Column(String(200))
    senha = Column(String(255)) # Aumentei o tamanho
    tipo = Column(String(20))  # Pode ser "aluno" ou "professor"
    ativo = Column(String(10), default="Ativo")  # Mudando para String com valores "Ativo" ou "Inativo"
    criado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criador = relationship("Usuario", remote_side=[id])
    analises_responsavel = relationship("Analise", back_populates="responsavel")
    analises = relationship(
        "Analise",
        secondary=analise_usuario,
        back_populates="participantes"
    )

    def __init__(self, nome, email, telefone, data_nascimento, login, senha, tipo, ativo="Ativo", criado_por=None):
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.data_nascimento = data_nascimento
        self.login = login
        self.senha = senha
        self.tipo = tipo
        self.ativo = ativo
        self.criado_por = criado_por