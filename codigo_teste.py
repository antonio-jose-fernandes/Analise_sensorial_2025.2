import itertools

def exibir_permutacoes(n):
    idsdasAmostras = [2,3,5]
    amostras = [f"Amostra {i}" for i in idsdasAmostras]
    permutacoes = list(itertools.permutations(amostras))

    cont = 0
    for idx, p in enumerate(permutacoes, start=1):       
        for i in range(len(p)):
          cont = cont+1        
          print(f"{cont} : {p[i]} {i}")
        print("\n")
        #nesta linha salvar a avaliacao
      
exibir_permutacoes(3)