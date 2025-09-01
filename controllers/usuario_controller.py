from main import app
from flask import request, render_template, redirect, url_for, flash
from models.usuario_model import *
from models.conexao import *
from datetime import datetime  # Para converter a data corretamente
from sqlalchemy.orm import sessionmaker  # Importação da sessionmaker
import re

# Criando a sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.route("/", methods=['GET'])
def login():
    return render_template("/login.html")


@app.route("/admin", methods=['POST'])
def admin():
    login = request.form['username']
    senha = request.form['password']
    db = SessionLocal()
    usuarioLogado = db.query(Usuario).filter(
        Usuario.login == login,
        Usuario.senha == senha,
        Usuario.ativo == 'Ativo'
    ).first()

    if usuarioLogado:
        if usuarioLogado.tipo == 'professor':
            return render_template("/professor/painel_admin.html")
        else:
            return redirect(url_for('aluno_dashboard'))
           # return render_template("/usuario_aluno/dashboard_atualizado.html")

    flash('Login ou senha inválido')
    return redirect("/")


# Rota para exibir o formulário de cadastro
@app.route("/usuario/cadastro/inserir", methods=['GET'])
def cad_inserir():
    return render_template("/cadastro/aluno_professor.html")


# Rota para processar o formulário de cadastro
@app.route("/usuario/cadastro/inserir/create", methods=['POST'])
def create():
    if request.method == 'POST':
        # Captura os dados enviados pelo formulário
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        data_str = request.form['data_nascimento']  # Data como string
        login = request.form['login']
        senha = request.form['senha']
        tipo = request.form['tipo']

        # Validação do telefone (somente números com 10 ou 11 dígitos)
        if not re.match(r'^\d{10,11}$', telefone):
            flash("Telefone inválido. Use apenas números com DDD (10 ou 11 dígitos).")
            return redirect(url_for('cad_inserir'))

        # Convertendo a data do formato string para tipo Date
        try:
            data_nascimento = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Data de nascimento inválida.")
            return redirect(url_for('cad_inserir'))

        # Cria um novo cadastro
        new_usuario = Usuario(
            nome=nome,
            email=email,
            telefone=telefone,
            login=login,
            senha=senha,
            tipo=tipo,
            data_nascimento=data_nascimento,
            ativo='Ativo'  # Definindo o status como ativo por padrão
        )

        # Cria uma nova sessão para o banco de dados
        db = SessionLocal()

        # Adiciona o novo cadastro ao banco de dados
        db.add(new_usuario)
        db.commit()
        db.close()

        # Redireciona para a página de lista de cadastros
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for('lista'))


# Rota para exibir a lista de cadastros
@app.route("/usuario/cadastro/inserir/list")
def lista():
    db = SessionLocal()
    cadastros = db.query(Usuario).all()
    db.close()
    return render_template("/usuario/list_usuario.html", cadastros=cadastros)


# Rota para exibir o formulário de edição
@app.route("/usuario/cadastro/inserir/editar/<int:id>", methods=["GET"])
def editar(id):
    db = SessionLocal()
    cadastro = db.query(Usuario).filter(Usuario.id == id).first()
    db.close()
    return render_template("usuario/edit_usuario.html", cadastro=cadastro)


# Rota para processar a atualização
@app.route("/usuario/cadastro/inserir/update/<int:id>", methods=["POST"])
def update(id):
    db = SessionLocal()
    cadastro = db.query(Usuario).filter(Usuario.id == id).first()

    if cadastro:
        cadastro.nome = request.form['nome']
        cadastro.email = request.form['email']

        # Validação do telefone (somente números com 10 ou 11 dígitos)
        telefone = request.form['telefone']
        if not re.match(r'^\d{10,11}$', telefone):
            flash("Telefone inválido.")
            db.close()
            return redirect(url_for('editar', id=cadastro.id))

        cadastro.telefone = telefone
        cadastro.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
        cadastro.login = request.form['login']
        cadastro.senha = request.form['senha']
        cadastro.tipo = request.form['tipo']
        cadastro.ativo = request.form['ativo']  # Atualizando o status de Ativo/Inativo

        db.commit()
    db.close()

    flash("Usuário atualizado com sucesso!", "success")
    return redirect(url_for('lista'))


# Rota para excluir um cadastro
@app.route("/cadastro/excluir/<int:id>", methods=["GET"])
def excluir(id):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.id == id).first()

    if usuario:
        db.delete(usuario)
        db.commit()

    db.close()

    flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for('lista'))