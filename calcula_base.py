import csv
from pandas import DataFrame, read_csv
import os
import json

def pega_arquivos():
    props = []
    votos = []
    path = os.path.dirname(os.path.abspath(__file__))
    with open(path+"/atualizacao/camara/proposicoes.csv", "r") as prop, open(path+"/atualizacao/camara/votos.csv", "r") as voto:
        
        arquivo_prop = csv.reader(prop,delimiter = ";")
        next(arquivo_prop, None)  # ignora o cabeçalho
        for row in arquivo_prop:
            proposicao = {}
            proposicao["codigo"] = row[0]
            proposicao["data"] = row[1]
            proposicao["hora"] = row[2]
            proposicao["orientacao"] = row[3]
            proposicao["tipo"] = row[4]
            proposicao["numero"] = row[5]
            proposicao["ano"] = row[6]
            proposicao["ementa"] = row[7]
            proposicao["resumo"] = row[8]
            props.append(proposicao)

        arquivo_voto = csv.reader(voto,delimiter = ";")
        next(arquivo_voto, None)  # ignora o cabeçalho
        for row in arquivo_voto:
            este_voto = {}
            este_voto["codigo"] = row[0]
            este_voto["politico"] = row[1]
            este_voto["voto"] = row[2]
            este_voto["partido"] = row[3]
            votos.append(este_voto)
    return props,votos

def media(lista):
    return sum(lista) / float(len(lista))
    
def calcula_governismo(props,df_votos):
    #transforma DataFrame em lista de dicionários
    df_props = props.T.to_dict().values()
    
    resultado = []
    
    #para cada proposição dos dicionários
    for p in df_props:
        #subset do DataFrame de votos para aquela proposição
        subvotos = df_votos[df_votos["ID_VOTACAO"] == p["ID_VOTACAO"]]
        #subset do DataFrame de votos que são iguais à orientação do governo
        temp = subvotos[subvotos.VOTO == p["ORIENTACAO_GOVERNO"].upper()]

        try: 
            #faz a relação entre o tamanho dos dois subsets e adiciona isso para uma lista
            resultado.append(len(temp)/len(subvotos))
        except ZeroDivisionError:
            pass

    try:
        #faz a média do resultado, achando assim o governismo para os dois arquivos processados
        governismo = media(resultado)
        return governismo
        
    except ZeroDivisionError:
        return None
    
#    print("Número de votações: "+str(len(resultado)))
#    print("Taxa de governismo: "+str(governismo))
          

def calcula_deputados(props,votos):
    df_votos = DataFrame(votos)
    df_props = DataFrame(props)
    lista_deputados = []
    for v in votos:
        lista_deputados.append(v["politico"])
    
    lista_deputados = list(set(lista_deputados))
    
    deputados = {}
    
    for d in lista_deputados:
        vota_junto = 0
        vota_contra = 0
        subvotos = df_votos[df_votos["politico"] == d] 
        for v in list(subvotos["codigo"]):
            voto = subvotos[subvotos["codigo"] == v]["voto"].get_values()[0]
            orientacao = df_props[df_props["codigo"] == v]["orientacao"].get_values()[0]
            if voto.lower() == orientacao.lower():
                vota_junto += 1
            else:
                vota_contra += 1
        deputados[d] = {}
        deputados[d]["vota_junto"] = vota_junto 
        deputados[d]["voto_total"] = vota_junto + vota_contra
    
    mais_de_90 = 0
    entre_50_e_90 = 0
    menos_de_50 = 0
    
    for d in deputados.keys():
        deputado = deputados[d]
        governismo = deputado["vota_junto"]/deputado["voto_total"]
        if governismo > 0.9:
            mais_de_90 += 1
        elif governismo > 0.5:
            entre_50_e_90 += 1
        else:
            menos_de_50 +=1
        
    print("Número total de deputados: "+str(len(lista_deputados)))
    print("% que votou + de 90% com o governo: "+str(mais_de_90*100/len(lista_deputados)))
    print("% que votou entre 50% e 90% com o governo: "+str(entre_50_e_90*100/len(lista_deputados)))
    print("% que votou menos de 50% com o governo: "+str(menos_de_50*100/len(lista_deputados)))
    
def faz_analise():
    props,votos = pega_arquivos()
    calcula_governismo(props,votos)
    calcula_deputados(props,votos)
    
    lista_codigos = []
    for v in votos:
        lista_codigos.append(v["codigo"])
    
    lista_codigos_votos = list(set(lista_codigos))

    lista_codigos = []
    for p in props:
        lista_codigos.append(p["codigo"])
    
    lista_codigos_props = list(set(lista_codigos))
    
    for p in lista_codigos:
        if p not in lista_codigos_votos:
            print(p)
    print("******")
    for p in lista_codigos_votos:
        if p not in lista_codigos:
            print(p)

def conserta_voto(voto):
    if voto == "Sim":
        return "SIM"
    elif voto == "Não":
        return "NAO"
    else:        
        return voto 

def acha_meses(datas):
    return set([str(d)[0:4] for d in datas])

        
def governismo_partido():
    #pega diretório do script para abrir os arquivos de votos e proposições
    path = os.path.dirname(os.path.abspath(__file__))
    
    #pega arquivo de proposições e conserta maiúsculas/minúsculas/acento
    props = read_csv(path+"/atualizacao/camara/proposicoes.csv",sep=";")
    props["ORIENTACAO_GOVERNO"] = props["ORIENTACAO_GOVERNO"].apply(conserta_voto)
    
    #acha lista de combinações ano/mês
    datas = list(set(list(props["DATA"])))
    meses = acha_meses(datas)
    
    #pega arquivo de votos e retira abstenções e presidente
    votos = read_csv(path+"/atualizacao/camara/votos.csv",sep=";")
    votos = votos[votos.VOTO != 'ABSTENCAO']
    votos = votos[votos.VOTO != 'PRESIDENTE']    
    votos['VOTO'] = votos['VOTO'].apply(conserta_voto)
    
    partidos = set(list(votos["PARTIDO"]))
    saida = {}
    
    #calcula o governismo para cada partido
    for p in partidos:
        saida[p] = []
        temp = votos[votos.PARTIDO == p]
        for m in meses: 
            #cria variável temporária de proposicoes, onde a data começa com o ano/mes da lista
            props_temp = props
            props_temp["FILTRO"] = props_temp["DATA"].apply(lambda t: str(t).startswith(m))
            props_temp = props_temp[props_temp.FILTRO == True]
            
            #se houver proposição neste período
            if len(props_temp) > 0:                
                governismo = calcula_governismo(props_temp,temp)
                #se houver governismo para esse partido, ou seja, algum voto
                if (governismo):
                    item = {}
                    item["data"] = "20"+m[0:2]+"-"+m[2:4]+"-01"
                    item["valor"] = int(round(governismo*100,0))
                    saida[p].append(item)

    #agora faz os cálculos para o total dos deputaods, sem filtrar por partido
    saida["Geral"] = []
    for m in meses: 
        props_temp = props
        props_temp["FILTRO"] = props_temp["DATA"].apply(lambda t: str(t).startswith(m))
        props_temp = props_temp[props_temp.FILTRO == True]
        #se houver proposição neste período
        if len(props_temp) > 0:                
            governismo = calcula_governismo(props_temp,votos)
            if (governismo):
                item = {}
                item["data"] = "20"+m[0:2]+"-"+m[2:4]+"-01"
                item["valor"] = int(round(governismo*100,0))
                saida["Geral"].append(item)
        
    #escreve Json de saída    
    with open ("medias_partido_mes.json","w",encoding='UTF8') as file:
        file.write(json.dumps(saida))
    
governismo_partido()

