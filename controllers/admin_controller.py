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

# Dashboard do aluno com lista de análises

@app.route("/admin/dashboard", methods=['GET'])
@login_required
@role_required("admin")
def admin_dashboard():
   # return redirect(url_for('dashboard'))    
    db = SessionLocal()
    try:        
        analises = (
                db.query(Analise)
                .options(joinedload(Analise.responsavel), joinedload(Analise.amostras))
                .order_by(desc(Analise.id))
                .all()
            )
        
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

     
      
        return render_template("admin/dashboard_admin.html", analises=analises, medias_avaliacores=medias_avaliacores )
       # return render_template("/usuario_aluno/dashboard_atualizado.html", analises=analises, medias_avaliacores=medias_avaliacores)    
    finally:
        db.close()
       

@app.route("/admin/cadastro/inserir/list")
@login_required
@role_required(["admin", "professor"])
def admin_lista():
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
            "/admin/list_usuario_admin.html",
            cadastros=cadastros,
            page=page,
            total_pages=total_pages
        )
    finally:
        db.close()
