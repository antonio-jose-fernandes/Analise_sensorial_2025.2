from main import app
from flask import request, render_template, redirect, url_for, flash
from models.amostra_model import Amostra
from models.analise_model import Analise
from models.conexao import *
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.route("/analise/<int:id>/detalhes", methods=['GET'])
def detalhe_analise(id):
    db = SessionLocal()
    analise = db.query(Analise).filter_by(id=id).first()
    if not analise:
        db.close()
        flash("Análise não encontrada!", "error")
        return redirect(url_for('lista_analises'))

    amostras = analise.amostras
    db.close()
    return render_template("/analises/detalhe_analise.html", analise=analise, amostras=amostras)


@app.route("/analise/<int:id>/amostras", methods=['GET'])
def lista_amostras(id):
    db = SessionLocal()
    amostras = db.query(Amostra).filter_by(analise_id=id).all()
    db.close()
    return render_template("/amostra/nova_amostra.html", amostras=amostras, analise_id=id)


@app.route("/analise/<int:id>/nova_amostra", methods=['GET', 'POST'])
def nova_amostra(id):
    if request.method == 'POST':
        descricao = request.form['descricao']
        nova_amostra = Amostra(descricao=descricao, analise_id=id)

        db = SessionLocal()
        db.add(nova_amostra)
        db.commit()
        db.close()

        flash("Amostra criada com sucesso!", "success")
        return redirect(url_for('detalhe_analise', id=id))

    return render_template("analises/amostra/nova_amostra.html", analise_id=id)


@app.route("/analise/<int:id>/amostra/<int:amostra_id>/editar", methods=['GET'])
def form_editar_amostra(id, amostra_id):
    db = SessionLocal()
    amostra = db.query(Amostra).filter_by(id=amostra_id, analise_id=id).first()
    if not amostra:
        db.close()
        flash("Amostra não encontrada!", "error")
        return redirect(url_for('detalhe_analise', id=id))

    db.close()
    return render_template("analises/amostra/edit_amostra.html", amostra=amostra, analise_id=id)


@app.route("/analise/<int:id>/amostra/<int:amostra_id>/editar", methods=['POST'])
def editar_amostra(id, amostra_id):
    db = SessionLocal()
    amostra = db.query(Amostra).filter_by(id=amostra_id, analise_id=id).first()
    if not amostra:
        db.close()
        flash("Amostra não encontrada!", "error")
        return redirect(url_for('detalhe_analise', id=id))

    amostra.descricao = request.form['descricao']
    db.commit()
    db.close()

    flash("Amostra atualizada com sucesso!", "success")
    return redirect(url_for('detalhe_analise', id=id))


@app.route("/analise/<int:id>/amostra/<int:amostra_id>/excluir", methods=['GET'])
def excluir_amostra(id, amostra_id):
    db = SessionLocal()
    amostra = db.query(Amostra).filter_by(id=amostra_id, analise_id=id).first()
    if not amostra:
        db.close()
        flash("Amostra não encontrada!", "error")
        return redirect(url_for('detalhe_analise', id=id))

    db.delete(amostra)
    db.commit()
    db.close()

    flash("Amostra excluída com sucesso!", "success")
    return redirect(url_for('detalhe_analise', id=id))