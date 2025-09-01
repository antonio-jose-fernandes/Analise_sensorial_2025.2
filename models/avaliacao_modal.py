from sqlalchemy import Column, Float, Integer, String,Float,ForeignKey
from models.conexao import Base
from sqlalchemy.orm import relationship

class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id = Column(Integer, primary_key=True, autoincrement =True)
    numero = Column(Integer,nullable=False)
    status = Column(String(255), nullable=False)
    amostra_id = Column(Integer, ForeignKey("amostras.id"), nullable=False)
    testador_id = Column(Integer, ForeignKey("testadores.id"), nullable=True)
    
    # Atributos sensoriais
    numero_controle = Column(Integer,nullable=True)   
    impressao_global = Column(Integer,nullable=True)
    cor = Column(Integer,nullable=True)
    aroma = Column(Integer,nullable=True)
    textura = Column(Integer,nullable=True)
    sabor = Column(Integer,nullable=True)
    intencao_compra = Column(Integer, nullable=True)
    observacao = Column(String(255), nullable=True)

   
    amostra = relationship("Amostra", back_populates="avaliacoes")


    def __init__(self, numero, status,amostra_id, numero_controle):
        self.numero = numero
        self.status = status
        self.amostra_id = amostra_id   
        self.numero_controle = numero_controle    
         