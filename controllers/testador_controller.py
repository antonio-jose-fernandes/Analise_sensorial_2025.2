from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from models.conexao import *
from models.analise_model import *
from models.amostra_model import *
from models.testador_modal import *
from models.avaliacao_modal import *
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from sqlalchemy.orm import sessionmaker
from main import app

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Rota para exibir o formulário sensorial
@app.route('/avaliacao/<int:id>', methods=['GET'])
def formulario_analise(id):

    if not session.get('google_authenticated'):
        flash("Sessão expirada. Obrigado por participar!", "info")
        return redirect(url_for('agradecimento'))
    

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



@app.route('/pdf_qrcode/<int:id>')
def pdf_qrcode(id):
    # URL que o QR Code vai abrir
    url = url_for('termo', id=id, _external=True)

    # Gerar QR Code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # Transformar QR Code em objeto compatível com ReportLab
    qr_io = BytesIO()
    img_qr.save(qr_io, format='PNG')
    qr_io.seek(0)
    qr_reader = ImageReader(qr_io)

    # Criar PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    # Definir título do PDF
    c.setTitle("QR Code Avaliação")
    largura, altura = A4
    

    # Parâmetros
    qr_tamanho = 500  # tamanho do QR Code
    margem_topo = 100  # espaço do topo para o título
    espacamento_texto = 20  # espaço entre QR Code e texto

    # Desenhar título centralizado
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(largura/2, altura - margem_topo, "QR Code da Avaliação")

    # Calcular posição Y do QR Code (logo abaixo do título)
    pos_y_qr = altura - margem_topo - 50 - qr_tamanho  # 50px abaixo do título
    c.drawImage(qr_reader, (largura - qr_tamanho)/2, pos_y_qr, width=qr_tamanho, height=qr_tamanho)

    # Texto explicativo abaixo do QR Code
    c.setFont("Helvetica", 12)
    c.drawCentredString(largura/2, pos_y_qr - espacamento_texto, "Escaneie para realizar a avaliação das amostras")

    # Finalizar PDF
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=False,  # abre no navegador
        download_name=f'qrcode_analise_{id}.pdf'
    )


# Rota intermediária para login do Google
@app.route('/iniciar_avaliacao/<int:id>', methods=['GET'])
def iniciar_avaliacao(id):
    session.clear()

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

        # Verificar se todas têm o mesmo numero_controle
        numeros_controle = {avaliacao.numero_controle for _, avaliacao in amostras_validas}
        if len(numeros_controle) > 1:
            flash("Erro: Você preencheu amostras de conjuntos diferentes. Preencha apenas com amostras do mesmo conjunto.", "error")
            return redirect(url_for('formulario_analise', id=id))

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
        #flash("Avaliação salva com sucesso!", "success")
        
        # Limpar a sessão de autenticação após envio bem-sucedido
        session.pop('google_authenticated', None)
        
        
        return redirect(url_for('logout_avaliador'))

    except Exception as e:
        db.rollback()
        flash(f"Erro ao salvar avaliação: {str(e)}", "error")
        return redirect(url_for('formulario_analise', id=id))

    finally:
        db.close()



@app.route("/avaliacao/termo/<int:id>")
def termo(id):
        db = SessionLocal()
        try:
            analise = db.query(Analise).filter_by(id=id).first()
            if not analise:
                return "Análise não encontrada", 404

            produto = analise.produto

            return render_template(
                "/avaliador/termo.html",
                produto=produto,
                id=id
            )
        finally:
            db.close()

    

@app.route('/agradecimento')
def agradecimento():
    return render_template("avaliador/agradecimento.html")