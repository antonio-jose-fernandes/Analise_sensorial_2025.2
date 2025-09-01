from sqlalchemy import desc
from main import app
from flask import redirect
from flask import request, render_template, redirect, url_for, flash, session
from models.analise_model import *
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
def lista_analises_andamento():
    db = SessionLocal()
    try:
        analises = (
            db.query(Analise)
            .join(Analise.amostras)
            .filter(Analise.status == 'Em andamento')
            .options(joinedload(Analise.responsavel), joinedload(Analise.amostras))
            .order_by(desc(Analise.id))
            .all()
        )

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

        return render_template("/usuario_aluno/analise_em_andamento.html", analises=analises)
    finally:
        db.close()


# Página inicial do aluno
@app.route("/aluno", methods=['GET'])
def aluno():
    return render_template("/aluno/painel_aluno.html")

# Dashboard do aluno com lista de análises
@app.route("/aluno/dashboard", methods=['GET'])
def aluno_dashboard():
   # return redirect(url_for('dashboard'))    
    db = SessionLocal()
    try:
        analises = (
            db.query(Analise)
            .join(Analise.amostras)
            .options(joinedload(Analise.responsavel), joinedload(Analise.amostras))
            .group_by(Analise.id)
            .order_by(desc(Analise.id))
            .all()    )

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
            medias_avaliacores ={}
            for linha in medias:
                medias_avaliacores[linha.amostra_id] = {
                'impressao_global': round(linha.media_impressao_global, 2)  if linha.media_impressao_global is not None else 0,
                'cor': round(linha.media_cor, 2)  if linha.media_cor is not None else 0,
                'aroma': round(linha.media_aroma, 2)  if linha.media_aroma is not None else 0,
                'textura': round(linha.media_textura, 2) if linha.media_textura is not None else 0,
                'sabor': round(linha.media_sabor, 2) if linha.media_sabor is not None else 0,
                'intencao_compra': round(linha.media_intencao_compra, 2) if linha.media_intencao_compra is not None else 0
            }

     
    
        return render_template("/usuario_aluno/dashboard.html", analises=analises, medias_avaliacores=medias_avaliacores )
       # return render_template("/usuario_aluno/dashboard_atualizado.html", analises=analises, medias_avaliacores=medias_avaliacores)
    finally:
        db.close()


# Rota simples para tela de análise do aluno
@app.route("/aluno/analise", methods=['GET'])
def aluno_analise():
    return render_template("/usuario_aluno/analise.html")

# Rota de teste que aponta para dashboard
@app.route("/teste", methods=['GET'])
def teste():
    return render_template("/usuario_aluno/dashboard.html")
