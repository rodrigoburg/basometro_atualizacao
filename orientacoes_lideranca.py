#-*- coding: utf-8 -*-
#!/usr/bin/python3

#Este arquivo calcula qual é o porcentual de vezes que cada uma das lideranças de bancadas na Câmara dos Deputados orientou as votações de acordo com a orientação do governo. O pré-requisito para rodá-lo é ter o arquivo "orientacoes.csv" - obtido por meio do script no arquivo atualiza_proposições.py - no diretório local. 

#A função principal que articula todas as outras é a faz_consulta(datas). O parâmetro "datas" deve ser uma lista contendo ao menos uma outra lista com a data de início e de fim do intervalo em que a fidelidade será calculada. Essa lista "datas" pode ter inúmeras listas com o intervalo dentro delas - o resultado final será mostrado de acordo com esses períodos passados como parâmetro. A única observação é que o script não funcionará se forem usados intervalos para os quais não existem registros no arquivo de orientações. 

#O resultado do script é dividido em duas partes: 1) o log que é impresso após a execução, mostrando uma tabela com as bancadas e os valores absolutos e porcentuais para a fidelidade em cada um dos intervalos; e 2) um arquivo "resultado.csv", onde é apresentada a fidelidade todas as bancadas que apareceram nos intervalos pesquisados (as bancadas são as linhas e os períodos as colunas)

#O script calcula a fidelidade seguindo os seguintes parâmetros: 1) se o governo não orientou a votação, ela não entra no cálculo; 2) se o governo orientou a votação como "Liberado", ela também não entra no cálculo; 2) se o governo orientou "Obstrução", a bancada é fiel se orientar "não" ou "obstrução"; e 4) se o governo orientar "sim ou não", a bancada é fiel se ela orientar exatamente a mesma coisa. Esta lógica pode ser modificada na função "testa_voto" neste arquivo

#OBS: os dados de orientações coletados pelo atualiza_proposições.py só estão disponíveis pela Câmara dos Deputados de 1998 em diante.

import csv
from datetime import datetime
from pandas import DataFrame
import re

#função que retorna um dicionário com todos os dados de todas as orientações que estão no diretório local
def pega_orientacoes():
    try: 
        #abre arquivo para leitura
        with open("orientacoes.csv","r") as file: 
            arquivo = csv.reader(file)
            #cria três listas vazias para serem preenchidas com os dados que precisamos
            cod_votacao = []
            bancada = []
            orientacao = []
            for row in arquivo:
                #o código da votação usado por este script para identicar cada uma delas é o código do projeto + a data da sua votação + a hora dessa votação (fazemos isso para diferenciar mais de uma votação que pode existir para cada projeto)
                cod_votacao.append(row[0]+"-"+row[1]+"-"+row[2]) 
                bancada.append(row[3])
                orientacao.append(row[4])         
            
            orientacoes = {}
            #agora preenche um dicionário onde as keys serão o código da votação e os valores serão um novo dicionário com duas keys: uma lista com o nome das bancadas e outra lista com a orientação de cada banada
            for i in range(len(cod_votacao)):
                #se a votação não existir no dicionário principal ("orientacoes"), cria-se essa key
                if not cod_votacao[i] in orientacoes:
                    orientacoes[cod_votacao[i]] = {} 
                    orientacoes[cod_votacao[i]]["bancadas"] = []
                    orientacoes[cod_votacao[i]]["orientacoes"] = []
                
                #descobre se a bancada em questão é composta por mais de um partido (ex: PrPtbPsc ou Pr/Ptb/Psc) ou se tem a expressão REPR. antes do nome do partido
                bloco = re.findall('P[a-z]+',bancada[i])
                repres = bancada[i].upper().split("REPR.")
                bloco_antigo = bancada[i].split("/")    
                
                #adiciona a bancada e a orientação de cada votação no dicionário principal de acordo com as divisões testadas acima
                if bloco:
                    for b in bloco:
                        orientacoes[cod_votacao[i]]["bancadas"].append(b.upper())
                        orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])
                elif len(repres)!=1:
                    orientacoes[cod_votacao[i]]["bancadas"].append(repres[1].upper())
                    orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])
                elif bloco_antigo:
                    for b in bloco_antigo:
                        orientacoes[cod_votacao[i]]["bancadas"].append(b.upper())
                        orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])                    
                else:
                    orientacoes[cod_votacao[i]]["bancadas"].append(bancada[i].upper())
                    orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])
                    
    except FileNotFoundError:
        print("Não há arquivo de orientações. Favor fazer a consulta na API da Câmara primeiro")
    
    return orientacoes

#retira do dicionário os dados das votações que estão fora do período a ser analisado
def retira_orientacoes(orientacoes,data_inicio,data_fim):
    votacoes_para_retirar = []
    
    #loop cria uma lista com todos os códigos das votações que estão fora do intervalo de análise
    for key in orientacoes:
        #o hífen separa a parte do código da votação que representa a data em que ela foi decidida no plenário
        data = key.split("-")[1]
        data = datetime.strptime(data,'%d/%m/%Y')
        if not data_inicio <= data <= data_fim:
            votacoes_para_retirar.append(key)
        if "GOV." not in orientacoes[key]["bancadas"]:
            votacoes_para_retirar.append(key)
    
    #retira as orientações fora do período desejado
    for k in votacoes_para_retirar: 
        if k in orientacoes:
            del orientacoes[k]
    
    return orientacoes

#função que retorna False se a orientação deve ser desconsiderada, 1 se a bancada orientou a favor do governo e 2 se orientou contra
def testa_voto(voto_gov,voto_bancada):
    if voto_gov == "Liberado":
        return False
    elif voto_gov == "Obstrução" and (voto_bancada == "Não" or voto_bancada == "Obstrução"):
        return 1
    elif voto_gov == voto_bancada:
        return 1
    else:
        return 2

#função recebe como parâmetro o dicionário "orientacoes" e retorna dois dicionários - em ambos, as keys são o nome das bancadas, e os valores no primeiro correspondem ao número de votações que serão consideradas para cada uma delas e no segundo às vezes em que essas bancadas orientaram a favor do governo
def calcula_fidelidade_governo(orientacoes):
    contagem_votos = {}
    contagem_votacoes = {}
    
    #para cada uma das votações
    for o in orientacoes:
        gov = orientacoes[o]["bancadas"].index("GOV.")
        voto_gov = orientacoes[o]["orientacoes"][gov]
        
        #para cada uma das bancadas dentro dessas orientações
        for i in range(len(orientacoes[o]["bancadas"])):
            #se a bancada ainda não estiver nos dicionários que compilarão o resultado, cria-se essa key e atribui o valor 0 ao número de votações total e também ao número de votações de acordo com o governo
            if orientacoes[o]["bancadas"][i] not in contagem_votos:
                contagem_votos[orientacoes[o]["bancadas"][i]] = 0
                contagem_votacoes[orientacoes[o]["bancadas"][i]] = 0
            
            #preenche os dicionários dos resultados
            voto = testa_voto(voto_gov,orientacoes[o]["orientacoes"][i])
            
            #se a votação é válida
            if voto:
                #adiciona 1 na contagem de votações
                contagem_votacoes[orientacoes[o]["bancadas"][i]] += 1
                #se governo e bancada votaram iguais, adiciona 1 também na contagem de votos 
                if voto == 1:
                    contagem_votos[orientacoes[o]["bancadas"][i]] += 1                
    
    return contagem_votos,contagem_votacoes

#pega os dicionários de votos e votações e retorna um dataframe com eles
def estrutura_contagem(contagem_votos,contagem_votacoes):
    resultado = DataFrame({"bancada":list(contagem_votos.keys()),"votos_com_governo":list(contagem_votos.values()),"votacoes":list(contagem_votacoes.values())})
    #calcula a fidelidade partidária (número de votos pró-governo dividido pelo número de votações válidas)
    resultado["fidelidade"] = 100*resultado["votos_com_governo"]/resultado["votacoes"]
    #retira o governo do dataframe
    resultado = resultado[resultado.bancada != "GOV."] 
    resultado = resultado.sort("fidelidade",ascending=False)
    return resultado    

#calcula a fidelidade da liderança de cada bancada para um intervalo específico, articulando as funções acima, retornando o dataframe "resultado" e imprimindo-o no output
def fidelidade_lideranca(intervalo):
    data_inicio = datetime.strptime(intervalo[0],'%d/%m/%Y')
    data_fim = datetime.strptime(intervalo[1],'%d/%m/%Y')
    orientaceos = pega_orientacoes()
    orientacoes = retira_orientacoes(orientaceos,data_inicio,data_fim)
    contagem_votos,contagem_votacoes = calcula_fidelidade_governo(orientacoes)
    resultado = estrutura_contagem(contagem_votos,contagem_votacoes)
    
    print("A tabela de fidelidade ao governo entre "+intervalo[0]+" e "+intervalo[1]+" é:\n")
    print(resultado)
    return resultado

#função para transformar o número de um dataframe em tipo float (será usada na função abaixo)
def conserta_numero(numero):
    if list(numero):
        return float(numero)
    else:
        return 0

#função principal que recebe como parâmetro uma lista composta por uma ou várias outras listas com dois elementos apenas: a data de início e de fim do intervalo em que se quer fazer a análise das orientações de cada bancada. além de imprimir essa análise no output (por meio da função fidelidade_lideranca), ela salva os resultados no arquivo resultados.csv
def faz_consulta(datas):
    #cria uma lista com os dataframes de resultados para cada intervalo
    resultados = []
    for i in range(len(datas)):
        resultados.append(fidelidade_lideranca(datas[i]))

    #cria uma outra lista com o nome de todos os partidos que apareceram nos intervalos analisados, sem valores duplicados
    todos_partidos = []
    for r in resultados:
        todos_partidos += list(r["bancada"])
    todos_partidos = set(todos_partidos)
    
    #arruma as datas para o arquivo de saída
    novas_datas = [d[0] + "-" + d[1] for d in datas]
    
    #escreve o arquivo de saída
    with open("resultado.csv", "w+", encoding='UTF8') as saida:
        linha = []
        header = ["bancada"] + novas_datas
        escreve_res = csv.writer(saida, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        escreve_res.writerow(header)
        #adiciona cada um dos partidos que foram listados no período na primeira coluna do arquivo e o resultado para cada intervalo nas outras colunas
        for p in todos_partidos:
            linha = [p]
            for r in resultados:
                linha.append(conserta_numero(r.fidelidade[r.bancada == p]))         
            escreve_res.writerow(linha)

#lista de datas que usamos para chamar a função principal faz_consulta(datas)            
datas = [
  ["01/01/1999","30/06/1999"],
  ["01/07/1999","31/12/1999"],
  ["01/01/2000","30/06/2000"],
  ["01/07/2000","31/12/2000"],
  ["01/01/2001","30/06/2001"],
  ["01/07/2001","31/12/2001"],
  ["01/01/2002","30/06/2002"],
  ["01/07/2002","31/12/2002"],
  ["01/01/2003","30/06/2003"],
  ["01/07/2003","31/12/2003"],
  ["01/01/2004","30/06/2004"],
  ["01/07/2004","31/12/2004"],
  ["01/01/2005","30/06/2005"],
  ["01/07/2005","31/12/2005"],
  ["01/01/2006","30/06/2006"],
  ["01/07/2006","31/12/2006"],
  ["01/01/2007","30/06/2007"],
  ["01/07/2007","31/12/2007"],
  ["01/01/2008","30/06/2008"],
  ["01/07/2008","31/12/2008"],
  ["01/01/2009","30/06/2009"],
  ["01/07/2009","31/12/2009"],
  ["01/01/2010","30/06/2010"],
  ["01/07/2010","31/12/2010"],
  ["01/01/2011","30/06/2011"],
  ["01/07/2011","31/12/2011"],
  ["01/01/2012","30/06/2012"],
  ["01/07/2012","31/12/2012"],
  ["01/01/2013","30/06/2013"],
    ["01/07/2013","31/12/2013"]
    ]
    

faz_consulta(datas)