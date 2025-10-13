from main import app
from functools import wraps
from flask import abort
from flask import request, render_template, redirect, url_for, flash
from utils.decorators import role_required
from flask_login import login_user, logout_user, login_required
from models.usuario_model import *
from models.conexao import *
from datetime import datetime  # Para converter a data corretamente
from sqlalchemy.orm import sessionmaker  # Importação da sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

import re

# Criando a sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def formatar_telefone(telefone):
    if not telefone:
        return ""
    telefone = re.sub(r'\D', '', telefone)  # garante só dígitos
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    elif len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    return telefone  # se não bater, retorna como está

# registrar no Jinja
app.jinja_env.filters['telefone'] = formatar_telefone




@app.route("/", methods=['GET'])
def login():
    return render_template("/login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for("login"))

@app.route("/admin", methods=['POST'])
def admin():
    login = request.form['username']
    senha = request.form['password']
    db = SessionLocal()
    try:
        usuarioLogado = db.query(Usuario).filter(
            Usuario.login == login,
            Usuario.ativo == 'Ativo'
        ).first()

        if usuarioLogado and check_password_hash(usuarioLogado.senha, senha):
            login_user(usuarioLogado)
            
            if usuarioLogado.tipo == 'professor':
                return render_template("/professor/painel_admin.html")
            elif usuarioLogado.tipo == 'admin':
                return render_template("/admin/painel_admin.html")
            else:
                return redirect(url_for('aluno_dashboard'))
            # return render_template("/usuario_aluno/dashboard_atualizado.html")

        flash("Login e/ou senha inválidos", "danger")
        return redirect(url_for("login"))
    finally:
        db.close()


# Rota para exibir o formulário de cadastro
@app.route("/usuario/cadastro/inserir", methods=['GET'])
@login_required
@role_required(["admin", "professor"])
def cad_inserir():
    return render_template("/cadastro/aluno_professor.html")


# Rota para processar o formulário de cadastro
@app.route("/usuario/cadastro/inserir/create", methods=['POST'])
@login_required
@role_required(["admin", "professor"])
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

        # Limpa tudo que não for número
        telefone_limpo = re.sub(r'\D', '', telefone)

        # Validação do telefone (somente números com 10 ou 11 dígitos)
        if not re.match(r'^\d{10,11}$', telefone_limpo):
            flash("Telefone inválido. Use apenas números com DDD (10 ou 11 dígitos).")
            return redirect(url_for('cad_inserir'))

        # Convertendo a data do formato string para tipo Date
        try:
            data_nascimento = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Data de nascimento inválida.")
            return redirect(url_for('cad_inserir'))

        senha_hash = generate_password_hash(senha)  


        # Cria uma nova sessão para o banco de dados
        db = SessionLocal()

        # 🚨 Verifica se já existe login
        usuario_existente = db.query(Usuario).filter_by(login=login).first()
        if usuario_existente:
            flash("Já existe um usuário com este login. Escolha outro.", "warning")
            db.close()
            return redirect(url_for('cad_inserir'))

        # 🚨 Opcional: também impedir duplicação de email
        email_existente = db.query(Usuario).filter_by(email=email).first()
        if email_existente:
            flash("Já existe um usuário com este e-mail.", "warning")
            db.close()
            return redirect(url_for('cad_inserir'))

        # Cria um novo cadastro
        new_usuario = Usuario(
            nome=nome,
            email=email,
            telefone=telefone_limpo,
            login=login,
            senha=senha_hash,
            tipo=tipo,
            data_nascimento=data_nascimento,
            ativo='Ativo'  # Definindo o status como ativo por padrão
        )

        

        # Adiciona o novo cadastro ao banco de dados
        db.add(new_usuario)
        db.commit()
        db.close()

        # Redireciona para a página de lista de cadastros
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for('lista'))


# Rota para exibir a lista de cadastros
@app.route("/usuario/cadastro/inserir/list")
@login_required
@role_required(["admin", "professor"])
def lista():
    db = SessionLocal()

    try:
        # Pegando o número da página via query string (?page=2)
        page = request.args.get("page", 1, type=int)
        per_page = 10  # número de registros por página

        # Conta o total
        total = db.query(Usuario).count()

        # Faz a consulta paginada
        cadastros = (
            db.query(Usuario)
            .order_by(Usuario.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        total_pages = (total + per_page - 1) // per_page  # cálculo simples de total de páginas

        return render_template(
            "/usuario/list_usuario.html",
            cadastros=cadastros,
            page=page,
            total_pages=total_pages
        )
    finally:
        db.close()


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
        cadastro.login = request.form['login']

        email = request.form['email']   # <-- agora a variável existe
        login = request.form['login']   # <-- idem
        
        # Verifica duplicidade de login (exceto o atual)
        login_existente = (
            db.query(Usuario)
            .filter(Usuario.login == login, Usuario.id != id)
            .first()
        )
        if login_existente:
            flash("Já existe um usuário com este login.", "warning")
            db.close()
            return redirect(url_for('editar', id=id))

        # Verifica duplicidade de e-mail (exceto o atual)
        email_existente = (
            db.query(Usuario)
            .filter(Usuario.email == email, Usuario.id != id)
            .first()
        )
        if email_existente:
            flash("Já existe um usuário com este e-mail.", "warning")
            db.close()
            return redirect(url_for('editar', id=id))
        
        # Validação do telefone (somente números com 10 ou 11 dígitos)
        telefone = request.form['telefone']
        telefone_limpo = re.sub(r'\D', '', telefone)

        if not re.match(r'^\d{10,11}$', telefone_limpo):
            flash("Telefone inválido.", "warning")
            db.close()
            return redirect(url_for('editar', id=cadastro.id))

        cadastro.telefone = telefone_limpo  
        cadastro.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
        

        # Atualiza a senha somente se o campo não estiver vazio
        nova_senha = request.form['senha']
        if nova_senha.strip():
            cadastro.senha = generate_password_hash(nova_senha)

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