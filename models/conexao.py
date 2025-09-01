from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base


# URL de conexão com o banco de dados MySQL no XAMPP
DATABASE_URL = "mysql+pymysql://root:@localhost/analise_db"


# Conexão com o banco de dados MySQL usando SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)


# Classe base para os modelos
Base = declarative_base()
