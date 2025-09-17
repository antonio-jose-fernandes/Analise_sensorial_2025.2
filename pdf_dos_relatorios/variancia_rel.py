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
from sqlalchemy.inspection import inspect
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle

from statistics import mean
from scipy.stats import f
try:
    from scipy.stats import f as f_dist
except Exception:
    f_dist = None

# Criando a sessão para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
   

@app.route("/relatorio/<int:analise_id>/variancia", methods=['GET'])
def gerar_pdf_variancia(analise_id):
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
    titulo = Paragraph(f"<b>{analise.produto}</b><br/> <b>Resultados da análise de variância </b>", estilos["Title"])
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
       'impressao_global','cor','aroma','textura','sabor','intencao_compra'
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
    largura_total_disponivel = 480  # valor aproximado para caber em A4 (margens consideradas)
    coluna_controle_largura = 60
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
        'intencao_compra': 'Intenção de Compra'       
    }

  
  
  
  
  
  
  
  
  
  
    # map para buscar descrições rápido (opcional)
    amostra_map = {a.id: a.descricao for a in amostras}

    for atributo in colunas_avaliaveis:
        # agrupar apenas valores numéricos por amostra
        valores_por_amostra = {}
        for avaliacao in avaliacoes:
            try:
                v = float(getattr(avaliacao, atributo))
            except (TypeError, ValueError):
                continue
            valores_por_amostra.setdefault(avaliacao.amostra_id, []).append(v)

        # filtrar amostras com pelo menos 1 observação
        grupos = {aid: vals for aid, vals in valores_por_amostra.items() if len(vals) > 0}
        geral = [v for vals in grupos.values() for v in vals]

        # título do atributo
        titulo_formatado = titulos_atributos.get(atributo, atributo.capitalize())
        elementos.append(Spacer(1, 12))
        elementos.append(Paragraph(f"<b>{titulo_formatado}</b>", estilos["Heading2"]))
        elementos.append(Spacer(1, 6))

        # se não houver dados suficientes, mostra linha informativa
        if not geral or len(grupos) < 2:
            dados = [["Causas de Variação (C.V)", "G.L.", "S.Q.", "Q.M.", "F"],
                    ["Sem dados numéricos suficientes para este atributo", "", "", "", ""]]
        else:
            k = len(grupos)                     # número de grupos (amostras com dados)
            N = sum(len(vals) for vals in grupos.values())  # total de observações
            media_geral = sum(geral) / len(geral)

            # SQ entre (amostras): sum n_j * (mean_j - media_geral)^2
            SQ_amostra = 0.0
            for vals in grupos.values():
                mean_j = sum(vals) / len(vals)
                SQ_amostra += len(vals) * (mean_j - media_geral) ** 2

            # SQ dentro (erro): soma das variâncias dentro de cada grupo
            SQ_erro = 0.0
            for vals in grupos.values():
                mean_j = sum(vals) / len(vals)
                SQ_erro += sum((v - mean_j) ** 2 for v in vals)

            SQ_total = sum((v - media_geral) ** 2 for v in geral)

            GL_amostra = k - 1
            GL_erro = N - k
            GL_total = N - 1

            QM_amostra = SQ_amostra / GL_amostra if GL_amostra > 0 else None
            QM_erro = SQ_erro / GL_erro if GL_erro > 0 else None

            if QM_amostra is not None and QM_erro and QM_erro > 0:
                Fcalc = QM_amostra / QM_erro
                if f_dist is not None:
                    try:
                        p_valor = f_dist.sf(Fcalc, GL_amostra, GL_erro)
                    except Exception:
                        p_valor = ""
                else:
                    p_valor = ""
            else:
                Fcalc = ""
                p_valor = ""

            dados = [
                ["Causas de Variação (C.V)", "G.L.", "S.Q.", "Q.M.", "F"],
                ["Amostras", GL_amostra, round(SQ_amostra, 2),
                round(QM_amostra, 2) if QM_amostra is not None else "",
                round(Fcalc, 3) if Fcalc != "" else ""],
                ["Resíduo", GL_erro, round(SQ_erro, 2),
                round(QM_erro, 2) if QM_erro is not None else "", ""],
                ["Total", GL_total, round(SQ_total, 2), "", ""],
            ]

        # construir a tabela (mesma estilização que você usa)
        colWidths = [120, 40, 70, 70, 50]
        tabela = Table(dados, colWidths=colWidths, repeatRows=1)

        estilo = list(estilo_base)
        for i in range(1, len(dados)):
            cor_fundo = verde_claro if i % 2 == 0 else verde_mais_claro
            estilo.append(('BACKGROUND', (0, i), (-1, i), cor_fundo))
            estilo.append(('TEXTCOLOR', (0, i), (-1, i), verde_texto))
            estilo.append(('ALIGN', (0, i), (-1, i), 'CENTER'))

        tabela.setStyle(TableStyle(estilo))
        elementos.append(tabela)





    
       

    doc.title = f"Resultados da análise de variância"
    doc.build(elementos)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=variancia.pdf'
    return response 
    
  