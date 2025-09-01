from app import app
from flask import render_template
from models.conexao import db
from models.avaliacao_modal import Avaliacao
from sqlalchemy import func
import pandas as pd #instala pip install pandas no terminal - ele trabalha com as tabelas e os dataframes
import numpy as np  # instala pip install numpy no terminal - usado para cálculos numericos e estatisticas
from scipy import stats # instala pip install scipy no terminal - traz funçoes estatisticas como a ANOVA
from statsmodels.stats.libqsturng import qsturng # para Dunnett. instala no terminal pip install statsmodels . Ele importa o metodod qsturng que faz o calculo do teste dunnett

@app.route("/dashboard")
def dasboard():
   # busca todas as avaliações 
   avaliacoes = Avaliacao.query.all()
   if not avaliacoes:
      return "Sem dados no banco"

   #converte em Dataframe
   df = pd.DataFrame([{
      "amostra_id" : a.amostra_id,
      "sabor": a.sabor,
      "aroma": a.textura,
      "textura": a.textura,
      "cor": a.cor,
      "testador_id": a.testador_id
   } for a in avaliacoes])

   atributos =["sabor","aroma","textura","cor"]
   medias={}
   significancia={}
   resultados={}

   controle_id = 1 # ID fixo do controle
  

   #para cada atributo
   for atributo in atributos:
    # médias por amostra
      medias_attr=df.groupby("amostra_id")[atributo].mean()
      medias[atributo]= medias_attr.to_dict()
    
    #preparar dados p/ANOVA
      grupos = [df[df["amostra_id"] == amostra][atributo].dropna()
            for amostra in df["amostra_id"].unique()]
      f_valor , p_valor = stats.f_oneway(*grupos)

     # ANOVA
      grupos = [df[df["amostra_id"]==amostra][atributo].dropna()
      for amostra in df ["amostra_id"].unique()]
      f_valor , p_valor =stats.f_oneway(*grupos)
    
    # Cálculo Dunnett
      n = len(df["amostra_id"].unique()) # número de amostras
      total_obs = len(df[atributo].dropna())
      gl_res = total_obs - n
      qm_res = np.var(df[atributo], ddof=1)

      alpha = 0.05
      d = qsturng(1 - alpha, n, gl_res) / np.sqrt(2)
      mds = d * np.sqrt(qm_res / n)
    
    # Comparaçao com a amostra controle (ex: ID = 1 é controle) #controle_id = 1
      cores= []
      difs= {}
      for amostra_id, media_val in medias_attr.items():
         if amostra_id != controle_id:
            cores.append("gray")
         else:
            diff = abs(media_val - medias_attr[controle_id])
            eh_significativo  = diff >= mds
            cores.append("red" if eh_significativo else "blue")
            difs[amostra_id] = {
               "diferença": round(diff, 2),
               "significativo": eh_significativo
            }

      significancia[atributo] = cores
      resultados[atributo] = {
         "f" : round(f_valor, 3),
         "p" : round(p_valor, 4),
         "MDS" :round(mds, 3), 
         "comparações":difs
      }  

      # Resumo 
      total_testes = len(df)
      total_amostras = df["amostra_id"].nunique()
      total_painelistas= df["testador_id"].nunique()

   return render_template(
      "usuario_aluno/dashboard_atualizado.html",
      medias=medias,
      resultados=resultados,
      significancia=significancia,
      total_testes=total_testes,
      total_amostras=total_amostras,
      total_painelistas=total_painelistas
   )