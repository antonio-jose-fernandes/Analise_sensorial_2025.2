from sqlalchemy import desc
from main import app
from flask import redirect
from flask_login import login_required, current_user
from utils.decorators import role_required
from flask import request, render_template, redirect, url_for, flash, session
from models.analise_model import *
from models.usuario_model import *
from models.amostra_model import *
from models.avaliacao_modal import *
from models.conexao import *
from sqlalchemy.orm import sessionmaker, joinedload
from collections import defaultdict
from sqlalchemy import func

# Criando a sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Lista análises em andamento com suas amostras e quantidade de avaliações feitas
@app.route("/aluno/analise/andamento", methods=['GET'])
@login_required
@role_required(["admin", "aluno"])
def lista_analises_andamento():
    db = SessionLocal()
    try:
        # Captura a página atual (padrão = 1)
        page = request.args.get("page", 1, type=int)
        per_page = 10  # número de registros por página

        # Consulta total de análises
        query = (
            db.query(Analise)
            .join(Analise.participantes)
            .filter(Usuario.id == current_user.id)
            .filter(Analise.status == 'Em andamento')
            .options(joinedload(Analise.responsavel), joinedload(Analise.amostras))
            .order_by(desc(Analise.id))
        )

        total = query.count()  # total de registros
        analises = query.offset((page - 1) * per_page).limit(per_page).all()

        # Processa as informações adicionais
        for analise in analises:
            analise.quantidade_amostras = len(analise.amostras)

            testadores_unicos = (
                db.query(Avaliacao.testador_id)
                .join(Avaliacao.amostra)
                .filter(Amostra.analise_id == analise.id, Avaliacao.testador_id != None)
                .distinct()
                .count()
            )
            analise.quantidade_avaliacoes = testadores_unicos

        # Calcula páginas totais
        total_pages = (total + per_page - 1) // per_page

        return render_template(
            "/usuario_aluno/analise_em_andamento.html",
            analises=analises,
            page=page,
            total_pages=total_pages
        )

    finally:
        db.close()

# Página inicial do aluno

@app.route("/aluno", methods=['GET'])
@login_required
@role_required("aluno")
def aluno():
    return render_template("/aluno/painel_aluno.html")

# Dashboard do aluno com lista de análises

@app.route("/aluno/dashboard", methods=['GET'])
@login_required
@role_required("aluno")
def aluno_dashboard():
   # return redirect(url_for('dashboard'))    
    db = SessionLocal()
    try:        
        analises = (
            db.query(Analise)
            .join(Analise.participantes)  # faz o join com a tabela analise_usuario
            .filter_by(id=current_user.id)  # filtra pelo usuário logado
            .options(joinedload(Analise.responsavel), joinedload(Analise.amostras))
            .order_by(desc(Analise.id))
            .all())
        
        medias_avaliacores ={}

        for analise in analises:
            analise.quantidade_amostras = len(analise.amostras)
            #pegando as medias dos dados das analises
            medias = (
                db.query(
                    Avaliacao.amostra_id,
                    func.avg(Avaliacao.impressao_global).label('media_impressao_global'),
                    func.avg(Avaliacao.cor).label('media_cor'),
                    func.avg(Avaliacao.aroma).label('media_aroma'),
                    func.avg(Avaliacao.textura).label('media_textura'),
                    func.avg(Avaliacao.sabor).label('media_sabor'),
                    func.avg(Avaliacao.intencao_compra).label('media_intencao_compra'),
                )
                .group_by(Avaliacao.amostra_id)
                .all()) 
            
            for linha in medias:
                medias_avaliacores[linha.amostra_id] = {
                'impressao_global': round(linha.media_impressao_global, 2)  if linha.media_impressao_global is not None else 0,
                'cor': round(linha.media_cor, 2)  if linha.media_cor is not None else 0,
                'aroma': round(linha.media_aroma, 2)  if linha.media_aroma is not None else 0,
                'textura': round(linha.media_textura, 2) if linha.media_textura is not None else 0,
                'sabor': round(linha.media_sabor, 2) if linha.media_sabor is not None else 0,
                'intencao_compra': round(linha.media_intencao_compra, 2) if linha.media_intencao_compra is not None else 0
            }

           #calcula a quantidade de testes realizados      
            testadores_unicos = (
                db.query(Avaliacao.testador_id)
                .join(Avaliacao.amostra)
                .filter(Amostra.analise_id == analise.id, Avaliacao.testador_id != None)
                .distinct()
                .count()
            )
            analise.quantidade_avaliacoes = testadores_unicos

     
      
        return render_template("usuario_aluno/dashboard.html", analises=analises, medias_avaliacores=medias_avaliacores )
       # return render_template("/usuario_aluno/dashboard_atualizado.html", analises=analises, medias_avaliacores=medias_avaliacores)    
    finally:
        db.close()
       


# Rota simples para tela de análise do aluno
@app.route("/aluno/analise", methods=['GET'])
@login_required
@role_required("aluno")
def aluno_analise():
    return render_template("/usuario_aluno/analise.html")




# Lista análises em andamento com suas amostras e quantidade de avaliações feitas
@app.route("/aluno/analise/extrair", methods=['GET'])
@login_required
@role_required("aluno")
def extrair_dados_analise():
    db = SessionLocal()
    try:
        # Obtém o número da página atual da URL (padrão = 1)
        page = request.args.get('page', 1, type=int)
        per_page = 10  # número de análises por página

        # Consulta paginada
        query = (
            db.query(Analise)
            .join(Analise.participantes)  # Join com a tabela analise_usuario
            .filter(Usuario.id == current_user.id)  # Apenas análises do aluno logado
            .filter(Analise.status == 'Em andamento')
            .options(joinedload(Analise.responsavel), joinedload(Analise.amostras))
            .order_by(desc(Analise.id))
        )

        # Conta o total e aplica limites
        total = query.count()
        analises = (
            query.offset((page - 1) * per_page)
                 .limit(per_page)
                 .all()
        )

        # Calcula dados adicionais
        for analise in analises:
            analise.quantidade_amostras = len(analise.amostras)

            testadores_unicos = (
                db.query(Avaliacao.testador_id)
                .join(Avaliacao.amostra)
                .filter(Amostra.analise_id == analise.id, Avaliacao.testador_id != None)
                .distinct()
                .count()
            )
            analise.quantidade_avaliacoes = testadores_unicos

        # Calcula o total de páginas
        total_pages = (total + per_page - 1) // per_page

        return render_template(
            "/usuario_aluno/extrair_dados_analise.html",
            analises=analises,
            page=page,
            total_pages=total_pages
        )
    finally:
        db.close()




# Rota de teste que aponta para dashboard
@app.route("/teste", methods=['GET'])
@login_required
@role_required("aluno")
def teste():
    return render_template("/usuario_aluno/dashboard.html")

