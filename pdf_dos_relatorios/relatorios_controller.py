from flask import Flask, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os
from main import app

from models.analise_model import Analise
from models.amostra_model import Amostra
from models.avaliacao_modal import Avaliacao
from models.conexao import *
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle,Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Criando a sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.route("/relatorio/<int:analise_id>/distribuicao", methods=['GET'])
def gerar_pdf_distribuicao_avaliacao(analise_id):
    # Dados do banco
    db = SessionLocal()
    avaliacoes = db.execute(
        select(Avaliacao)
        .join(Avaliacao.amostra)
        .join(Amostra.analise)
        .where(Analise.id == analise_id)
        .order_by(Avaliacao.id) 
    ).scalars().all()
    analise = db.query(Analise).filter_by(id=analise_id).first()

    amostras = db.query(Amostra).filter_by(analise_id=analise_id).all()
    descricao_das_amostras = [obj.descricao for obj in amostras]
    qtd_colunas_por_amostras = len(amostras)    
    db.close()

    # PDF com platypus
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []
    estilos = getSampleStyleSheet()

    # Título
    titulo = Paragraph(f"<b>Distribuição da análise: {analise.produto}</b>", estilos["Title"])
    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    # Dados formatados em tabela
    cabecalho = ['Controle']  
    dados = [cabecalho]  

    #organizando o tamanho do texto na celula da tabela
    estilo_texto = estilos["Normal"]

    linha_atual = []
    numero_linha = 1

    for i, avaliacao in enumerate(avaliacoes, start=1):
        amostra = db.query(Amostra).get(avaliacao.amostra_id)
        avalicaoExibido = str(avaliacao.numero) + "  - Amostra: " + amostra.descricao
        linha_atual.append(Paragraph(avalicaoExibido, estilo_texto))
        if len(linha_atual) == qtd_colunas_por_amostras:
            dados.append([str(numero_linha)] + linha_atual)
            linha_atual = []
            numero_linha += 1

    if linha_atual:
        while len(linha_atual) < qtd_colunas_por_amostras:
            linha_atual.append("")
        dados.append([str(numero_linha)] + linha_atual)

    # Criar tabela com estilo verde (tipo Bootstrap table-success)
    # Cores em tons de verde
    verde_claro = colors.HexColor('#d4edda')  # cor de fundo clara (Bootstrap success)
    verde_mais_claro = colors.HexColor('#eaf5ec')  # variação para listras alternadas
    verde_texto = colors.HexColor('#155724')  # texto verde escuro
    verde_cabecalho = colors.HexColor('#28a745')  # verde escuro para cabeçalho



    #ajustando a tabela conforme a quantidade de amostras
    largura_total_disponivel = 480  # valor aproximado para caber em A4 (margens consideradas)
    coluna_controle_largura = 60
    largura_restante = largura_total_disponivel - coluna_controle_largura
    if(qtd_colunas_por_amostras == 0):
        qtd_colunas_por_amostras = 1
    largura_colunas_amostras = largura_restante / qtd_colunas_por_amostras
    colWidths = [coluna_controle_largura] + [largura_colunas_amostras] * qtd_colunas_por_amostras

    tabela = Table(dados, colWidths=colWidths)
    # Estilo base
    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), verde_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ]

    # Linhas com fundo alternado
    for i in range(1, len(dados)):  # pula o cabeçalho (linha 0)
        cor_fundo = verde_claro if i % 2 == 0 else verde_mais_claro
        estilo.append(('BACKGROUND', (0, i), (-1, i), cor_fundo))
        estilo.append(('TEXTCOLOR', (0, i), (-1, i), verde_texto))
        estilo.append(('ALIGN', (0, i), (-1, i), 'LEFT'))

    # Aplicar o estilo
    tabela.setStyle(TableStyle(estilo))

    elementos.append(tabela)

    doc.title = f"Distribuição das amostras"
    doc.build(elementos)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=distribuicao_avaliacoes.pdf'
    return response 
    

  