from flask import Flask
from flask_login import LoginManager, current_user, login_required
from models.usuario_model import Usuario  # Ajuste conforme seu modelo de usuário
from sqlalchemy.orm import sessionmaker
from models.conexao import *
from werkzeug.security import generate_password_hash

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criação de uma instância do Flask
app = Flask(__name__)

# Chave secreta para criptografar a sessão
app.config['SECRET_KEY'] = 'minha_chave_secreta'

from controllers.aluno_controller import *
from controllers.usuario_controller import *
from controllers.analise_controller import *
from controllers.amostra_controller import *
from controllers.testador_controller import *
from controllers.admin_controller import *
from controllers.google_auth_controller import * 
from models.usuario_model import *
from models.testador_modal import *
from models.avaliacao_modal import *
from pdf_dos_relatorios.relatorios_controller import *

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # rota para redirecionar se não estiver logado
login_manager.login_message = "Você precisa estar logado para acessar esta página."
login_manager.login_message_category = "warning"  # para integrar com Bootstrap flash

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    return db.query(Usuario).get(int(user_id))

# Cria todas as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

def cria_usuario_padrao():
    db = SessionLocal()
    try:
        existe_usuario = db.query(Usuario).first()
        if not existe_usuario:
            usuario = Usuario(
                nome="Administrador",
                email="admin@teste.com",
                telefone="88999999999",
                data_nascimento="2000-01-01",
                login="admin",
                senha=generate_password_hash("123456"),
                tipo="professor", 
                ativo="Ativo"
            )
            db.add(usuario)
            db.commit()
        
    finally:
        db.close()

cria_usuario_padrao()

#Inicia o servidor de desenvolvimento.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')