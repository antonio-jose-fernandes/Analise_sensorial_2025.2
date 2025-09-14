from flask import Flask
from flask_login import LoginManager, current_user, login_required
from models.usuario_model import Usuario  # Ajuste conforme seu modelo de usuário


# Criação de uma instância do Flask
app = Flask(__name__)

# Chave secreta para criptografar a sessão
app.config['SECRET_KEY'] = 'minha_chave_secreta'

from controllers.aluno_controller import *
from controllers.usuario_controller import *
from controllers.analise_controller import *
from controllers.amostra_controller import *
from controllers.testador_controller import *
from controllers.google_auth_controller import * 
from models.usuario_model import *
from models.testador_modal import *
from models.avaliacao_modal import *
from pdf_dos_relatorios.relatorios_controller import *

# Cria todas as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

#Inicia o servidor de desenvolvimento.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')