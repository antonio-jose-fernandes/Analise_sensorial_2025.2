from flask import Flask, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
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
from sqlalchemy.inspection import inspect
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle

# Criando a sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
   

@app.route("/relatorio/<int:analise_id>/avaliacoes", methods=['GET'])
def gerar_pdf_avaliacoes_realizadas(analise_id):
    # Dados do banco
    db = SessionLocal()
    avaliacoes = db.execute(
        select(Avaliacao)
        .join(Avaliacao.amostra)
        .join(Amostra.analise)
        .where(Analise.id == analise_id)
        .where(Avaliacao.testador_id.isnot(None))
        .order_by(Avaliacao.id) 
    ).scalars().all()
    analise = db.query(Analise).filter_by(id=analise_id).first()

    amostras = db.query(Amostra).filter_by(analise_id=analise_id).all()
    
    qtd_colunas_por_amostras = len(amostras)    
    db.close()

    # PDF com platypus
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []
    estilos = getSampleStyleSheet()

    # Título
    titulo = Paragraph(f"<b>{analise.produto}</b><br/> <b>Avaliações realizadas </b>", estilos["Title"])
    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    # Dados formatados em tabela cabecalho    
    cabecalho = ['Controle']  
    for amostra2 in amostras:
       textoCabecalho = 'Amostra: '+ str(amostra2.descricao)
       cabecalho.append(textoCabecalho)
    estilo_texto = estilos["Normal"]
    estilo_centralizado = ParagraphStyle(
        'Centralizado',
        parent=estilos['Normal'],
        alignment=TA_CENTER
    )
 
    # Descobrir os atributos avaliáveis dinamicamente
    colunas_avaliaveis = [
       'impressao_global','cor','aroma','textura','sabor','intencao_compra','observacao'
    ]

    # Estilo base e cores
    verde_claro = colors.HexColor('#d4edda')
    verde_mais_claro = colors.HexColor('#eaf5ec')
    verde_texto = colors.HexColor('#155724')
    verde_cabecalho = colors.HexColor('#28a745')

    estilo_base = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), verde_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]

    #ajustando a tabela conforme a quantidade de amostras
    largura_total_disponivel = 1000  # valor aproximado para caber em A4 (margens consideradas)
    coluna_controle_largura = 50
    largura_restante = largura_total_disponivel - coluna_controle_largura
    if(qtd_colunas_por_amostras == 0):
        qtd_colunas_por_amostras = 1
    largura_colunas_amostras = largura_restante / qtd_colunas_por_amostras
    colWidths = [coluna_controle_largura] + [largura_colunas_amostras] * qtd_colunas_por_amostras

    # Mapeamento dos nomes dos atributos para títulos formatados
    titulos_atributos = {
        'impressao_global': 'Impressão Global',
        'cor': 'Cor',
        'aroma': 'Aroma',
        'textura': 'Textura',
        'sabor': 'Sabor',
        'intencao_compra': 'Intenção de Compra',
        'observacao': 'Observação'
    }


    # Cabeçalho dinâmico
    cabecalho = ["Controle"]
   
    for amostra in amostras:
        # Cabeçalho: Controle + atributos
        cabecalho = ["Controle"] + [titulos_atributos.get(attr, attr.capitalize()) for attr in colunas_avaliaveis]
        dados = [cabecalho]

        # Preencher dados das avaliações dessa amostra
        avaliacoes_amostra = [a for a in avaliacoes if a.amostra_id == amostra.id]
        for avaliacao in avaliacoes_amostra:
            linha = [avaliacao.numero_controle]
            for atributo in colunas_avaliaveis:

                valor = getattr(avaliacao, atributo)
                if atributo == "observacao":
                    linha.append(Paragraph(str(valor), estilo_centralizado))
                else:
                    linha.append(str(valor) if valor is not None else "")               
            dados.append(linha)

        # Criar título da amostra
        titulo_amostra = Paragraph(f"<b>Amostra: {amostra.descricao}</b>", estilos["Heading2"])
        elementos.append(Spacer(1, 12))
        elementos.append(titulo_amostra)
        elementos.append(Spacer(1, 6))

        # Criar tabela
        colWidths = [80] + [100] * len(colunas_avaliaveis)  # ajusta largura das colunas
        tabela = Table(dados, colWidths=colWidths, repeatRows=1)

        estilo = list(estilo_base)
        for i in range(1, len(dados)):
            cor_fundo = verde_claro if i % 2 == 0 else verde_mais_claro
            estilo.append(('BACKGROUND', (0, i), (-1, i), cor_fundo))
            estilo.append(('TEXTCOLOR', (0, i), (-1, i), verde_texto))

        tabela.setStyle(TableStyle(estilo))
        elementos.append(tabela)


    
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    doc.title = f"Avaliações realizadas"
    doc.build(elementos)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=avaliacoes_realizadas.pdf'
    return response 
    
  