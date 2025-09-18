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

from statsmodels.stats.multicomp import pairwise_tukeyhsd
import pandas as pd
import numpy as np
from scipy.stats import f as f_dist

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

  
  
  
  
  
  
  
  
  
  
    for atributo in colunas_avaliaveis:
        # Agrupar valores por amostra
        valores = []
        grupos_amostra = []
        grupos_avaliador = []
        for avaliacao in avaliacoes:
            try:
                v = float(getattr(avaliacao, atributo))
            except (TypeError, ValueError):
                continue
            valores.append(v)
            grupos_amostra.append(avaliacao.amostra_id)
            grupos_avaliador.append(avaliacao.testador_id)

        titulo_formatado = titulos_atributos.get(atributo, atributo.capitalize())
        elementos.append(Spacer(1, 12))
        elementos.append(Paragraph(f"<b>{titulo_formatado}</b>", estilos["Heading2"]))
        elementos.append(Spacer(1, 6))

        if len(valores) < 2 or len(set(grupos_amostra)) < 2:
            elementos.append(Paragraph("Sem dados suficientes para este atributo", estilos["Normal"]))
            continue

        # -------------------------------
        # 🔹 ANOVA de duas vias (Amostra e Avaliador)
        # -------------------------------
        df = pd.DataFrame({
            "valor": valores,
            "amostra": grupos_amostra,
            "avaliador": grupos_avaliador
        })

        medias = df.groupby("amostra")["valor"].mean()
        media_geral = df["valor"].mean()

        # SQ Amostra
        SQ_amostra = sum(df.groupby("amostra").size() * (medias - media_geral) ** 2)

        # SQ Avaliador
        medias_avaliador = df.groupby("avaliador")["valor"].mean()
        SQ_avaliador = sum(df.groupby("avaliador").size() * (medias_avaliador - media_geral) ** 2)

        # SQ Total
        SQ_total = sum((df["valor"] - media_geral) ** 2)

        # SQ Erro
        SQ_erro = SQ_total - SQ_amostra - SQ_avaliador

        # Graus de liberdade
        GL_amostra = df["amostra"].nunique() - 1
        GL_avaliador = df["avaliador"].nunique() - 1
        GL_total = len(df) - 1
        GL_erro = GL_total - GL_amostra - GL_avaliador

        # Quadrados médios
        QM_amostra = SQ_amostra / GL_amostra if GL_amostra > 0 else np.nan
        QM_avaliador = SQ_avaliador / GL_avaliador if GL_avaliador > 0 else np.nan
        QM_erro = SQ_erro / GL_erro if GL_erro > 0 else np.nan

        # F e p-valor
        F_amostra = QM_amostra / QM_erro if QM_erro > 0 else np.nan
        F_avaliador = QM_avaliador / QM_erro if QM_erro > 0 else np.nan
        p_amostra = f_dist.sf(F_amostra, GL_amostra, GL_erro) if not np.isnan(F_amostra) else ""
        p_avaliador = f_dist.sf(F_avaliador, GL_avaliador, GL_erro) if not np.isnan(F_avaliador) else ""

        # Montar tabela ANOVA
        dados_anova = [
            ["Causas de Variação (C.V)", "G.L.", "S.Q.", "Q.M.", "F", "p-valor"],
            ["Amostras", GL_amostra, round(SQ_amostra, 2), round(QM_amostra, 2), round(F_amostra, 3), f"{p_amostra:.4f}"],
            ["Avaliadores", GL_avaliador, round(SQ_avaliador, 2), round(QM_avaliador, 2), round(F_avaliador, 3), f"{p_avaliador:.4f}"],
            ["Resíduo", GL_erro, round(SQ_erro, 2), round(QM_erro, 2), "", ""],
            ["Total", GL_total, round(SQ_total, 2), "", "", ""],
        ]

        tabela_anova = Table(dados_anova, colWidths=[120, 40, 70, 70, 50, 60])
        tabela_anova.setStyle(TableStyle(estilo_base))
        elementos.append(tabela_anova)

        # -------------------------------
        # 🔹 Teste de Tukey (apenas para Amostras)
        # -------------------------------
        id_to_nome = {amostra.id: amostra.descricao for amostra in amostras}
        df["amostra_nome"] = df["amostra"].map(id_to_nome)

        if len(set(grupos_amostra)) > 1:
            tukey = pairwise_tukeyhsd(endog=df["valor"], groups=df["amostra_nome"], alpha=0.05)
            df_tukey = pd.DataFrame(data=tukey.summary().data[1:], columns=tukey.summary().data[0])
            dados_tukey = [df_tukey.columns.tolist()] + df_tukey.values.tolist()

            # substitui a primeira linha (cabeçalho) por português
            dados_tukey[0] = ["Grupo 1", "Grupo 2", "Diferença Média", "p-ajustado", "Limite Inferior", "Limite Superior", "Diferença Significativa"]


            tabela_tukey = Table(dados_tukey, repeatRows=1)
            tabela_tukey.setStyle(TableStyle(estilo_base))
            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph(f"<b>Teste de Tukey - {titulo_formatado}</b>", estilos["Heading3"]))
            elementos.append(tabela_tukey)





    
       

    doc.title = f"Resultados da análise de variância"
    doc.build(elementos)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=variancia.pdf'
    return response 
    
  