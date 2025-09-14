from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.conexao import *
from models.analise_model import *
from models.amostra_model import *
from models.testador_modal import *
from models.avaliacao_modal import *

from sqlalchemy.orm import sessionmaker
from main import app

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Rota para exibir o formulário sensorial
@app.route('/avaliacao/<int:id>', methods=['GET'])
def formulario_analise(id):
    db = SessionLocal()
    try:
        analise = db.query(Analise).filter_by(id=id).first()
        if not analise:
            return "Análise não encontrada", 404

        produto = analise.produto
        quantidade_amostras = len(analise.amostras)

        # Verificar se o usuário já está autenticado via session
        usuario_autenticado = session.get('google_authenticated', False)

        return render_template(
            "/avaliador/ficha.html",
            produto=produto,
            quantidade_amostras=quantidade_amostras,
            id=id,
            usuario_autenticado=usuario_autenticado
        )
    finally:
        db.close()

# Rota intermediária para login do Google
@app.route('/iniciar_avaliacao/<int:id>', methods=['GET'])
def iniciar_avaliacao(id):
    # Se já estiver autenticado, redireciona direto
    if session.get('google_authenticated'):
        return redirect(url_for('formulario_analise', id=id))
    
    # Salva o ID da análise na session e redireciona para login
    session['analise_id'] = id
    session['next_url'] = url_for('formulario_analise', id=id)
    return redirect(url_for('google_login'))


@app.route('/avaliacao/<int:id>', methods=['POST'])
def salvar_avaliacoes(id):
    # Verificar se o usuário está autenticado antes de salvar
    if not session.get('google_authenticated'):
        flash("Por favor, faça login com Google antes de enviar a avaliação.", "error")
        return redirect(url_for('iniciar_avaliacao', id=id))
    

    db = SessionLocal()
    try:
        # 1. Verificar se todas as amostras existem antes de salvar
        i = 1
        amostras_validas = []

        while True:
            numero_amostra = request.form.get(f"amostra_{i}")
            if not numero_amostra:
                break

            avaliacao = (
                db.query(Avaliacao)
                .join(Amostra)
                .filter(
                    Avaliacao.numero == int(numero_amostra),
                    Amostra.analise_id == id
                )
                .first()
            )

            if not avaliacao:
                flash(f"Amostra com número {numero_amostra} não encontrada. Nenhum dado foi salvo.", "error")
                return redirect(url_for('formulario_analise', id=id))

            amostras_validas.append((i, avaliacao))
            i += 1

        # 2. Se todas as amostras são válidas, salvar o testador
        testador = Testador(
            nome=request.form.get("nome"),
            email=session.get('google_email'),
            genero=request.form.get("genero"),
            faixa_etaria=request.form.get("faixa_etaria")
        )
        db.add(testador)
        db.commit()
        db.refresh(testador)

        # 3. Atualizar as avaliações com dados do form
        for i, avaliacao in amostras_validas:
            avaliacao.testador_id = testador.id
            avaliacao.impressao_global = request.form.get(f"impressao_global_{i}")
            avaliacao.cor = request.form.get(f"cor_{i}")
            avaliacao.aroma = request.form.get(f"aroma_{i}")
            avaliacao.textura = request.form.get(f"textura_{i}")
            avaliacao.sabor = request.form.get(f"sabor_{i}")
            avaliacao.intencao_compra = int(request.form.get(f"compra_{i}"))
            avaliacao.observacao = request.form.get(f"obs_{i}")
            db.add(avaliacao)

        db.commit()
        flash("Avaliação salva com sucesso!", "success")
        
        # Limpar a sessão de autenticação após envio bem-sucedido
        session.pop('google_authenticated', None)
        session.clear()
        
        return redirect(url_for('formulario_analise', id=id))

    except Exception as e:
        db.rollback()
        flash(f"Erro ao salvar avaliação: {str(e)}", "error")
        return redirect(url_for('formulario_analise', id=id))

    finally:
        db.close()