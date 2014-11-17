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

def calcula_governismo(props,df_votos,tamanho=False):
    #transforma DataFrame em lista de dicionários
    df_props = props.T.to_dict().values()

    resultado = []
    total_de_votacoes = 0

    #para cada proposição dos dicionários
    for p in df_props:
        #subset do DataFrame de votos para aquela proposição
        subvotos = df_votos[df_votos["ID_VOTACAO"] == p["ID_VOTACAO"]]
        #subset do DataFrame de votos que são iguais à orientação do governo
        temp = subvotos[subvotos.VOTO == p["ORIENTACAO_GOVERNO"].upper()]

        try:
            #faz a relação entre o tamanho dos dois subsets e adiciona isso para uma lista
            resultado.append(len(temp)/len(subvotos))
            total_de_votacoes += len(subvotos)
        except ZeroDivisionError:
            pass

    try:
        #faz a média do resultado, achando assim o governismo para os dois arquivos processados
        governismo = media(resultado)
        if tamanho:
            return governismo, total_de_votacoes
        else:
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

    #print("Número total de deputados: "+str(len(lista_deputados)))
    #print("% que votou + de 90% com o governo: "+str(mais_de_90*100/len(lista_deputados)))
    #print("% que votou entre 50% e 90% com o governo: "+str(entre_50_e_90*100/len(lista_deputados)))
    #print("% que votou menos de 50% com o governo: "+str(menos_de_50*100/len(lista_deputados)))

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

    #for p in lista_codigos:
        #if p not in lista_codigos_votos:
            #print(p)
    #print("******")
    #for p in lista_codigos_votos:
        #if p not in lista_codigos:
            #print(p)

def conserta_voto(voto):
    if voto == "Sim":
        return "SIM"
    elif voto == "Não":
        return "NAO"
    else:
        return voto

def acha_meses(datas):
    meses = list(set([d[0:4] for d in datas]))
    meses.sort()
    return meses

#chame a função governismo_partido com 4 opções: fhc2, lula1, lula2 e dilma1
def governismo_partido(mandato):
    #pega diretório do script para abrir os arquivos de votos e proposições
    path = os.path.dirname(os.path.abspath(__file__))

    #pega arquivo de proposições e conserta maiúsculas/minúsculas/acento
    props = read_csv(path+"/atualizacao/camara/"+mandato+"/proposicoes.csv",sep=";")
    props["ORIENTACAO_GOVERNO"] = props["ORIENTACAO_GOVERNO"].apply(conserta_voto)

    #transforma as datas em string e coloca zero na frente dos anos que perderam esse zero
    props["DATA"] = props["DATA"].apply(lambda d: "%06d" % d)

    #acha lista de combinações ano/mês
    datas = list(set(list(props["DATA"])))
    meses = acha_meses(datas)

    #pega arquivo de votos e retira abstenções e presidente
    votos = read_csv(path+"/atualizacao/camara/"+mandato+"/votos.csv",sep=";")
    votos = votos[votos.VOTO != 'ABSTENCAO']
    votos = votos[votos.VOTO != 'PRESIDENTE']
    votos['VOTO'] = votos['VOTO'].apply(conserta_voto)

    partidos = set(list(votos["PARTIDO"]))
    aux_saida = {}

    proposicoes_por_mes = [["data","quantidade"]]

    #agora faz os cálculos para o total dos deputaods, sem filtrar por partido
    aux_saida["Geral"] = {}
    for mes in meses:
        props_temp = props
        props_temp["FILTRO"] = props_temp["DATA"].apply(lambda t: str(t).startswith(mes))
        props_temp = props_temp[props_temp.FILTRO == True]
        #se houver proposição neste período
        item = {}
        item["date"] = "20"+mes[0:2]+"-"+mes[2:4]+"-01"
        item["valor"] = -1
        item["num_votacoes"] = 0
        if len(props_temp) > 0:
            governismo = calcula_governismo(props_temp,votos,True)
            if (governismo):
                item["valor"] = int(round(governismo[0]*100,0))
                item["num_votacoes"] = governismo[1]
        aux_saida["Geral"][mes] = item

        #"cálculo" do número de proposições existentes em cada mês
        proposicoes_por_mes.append([item["date"], len(props_temp)])

    #calcula o governismo para cada partido
    for partido in partidos:
        aux_saida[partido] = {}
        temp = votos[votos.PARTIDO == partido]
        for mes in meses:
            #cria variável temporária de proposicoes, onde a data começa com o ano/mes da lista
            props_temp = props
            props_temp["FILTRO"] = props_temp["DATA"].apply(lambda t: str(t).startswith(mes))
            props_temp = props_temp[props_temp.FILTRO == True]

            item = {}
            item["date"] = "20"+mes[0:2]+"-"+mes[2:4]+"-01"
            item["valor"] = -1
            item["num_votacoes"] = 0
            #se houver proposição neste período
            if len(props_temp) > 0:
                governismo = calcula_governismo(props_temp,temp,True)
                #se houver governismo para esse partido, ou seja, algum voto
                if (governismo):
                    item["valor"] = int(round(governismo[0]*100,0))
                    item["num_votacoes"] = governismo[1]
            aux_saida[partido][mes] = item

    saida = {}

    #Cálculo da média móvel
    #Para cada partido faça....
    for partido in aux_saida:
        saida[partido] = []
        #Para cada mês da lista de meses faça...
        for mes in meses:
            indice = meses.index(mes) #Pega o índice do mês na lista
            item = {}
            #Se for o primeiro item da lista, só copia os valores
            #Salva a data no dicionário final
            item["date"] = aux_saida[partido][mes]["date"]
            #arruma as datas da década de 1990
            if item["date"][2] == "9":
                item["date"] = "19" + item["date"][2:]
            #Inicializa um contador de "meses iterados"
            contador = 0
            soma_movel = 0
            total_local_votacoes = 0
            while contador < 6 and (indice - contador >= 0): #2 porque quero pegar os últimos 6 meses
                soma_movel += aux_saida[partido][meses[indice - contador]]["valor"] * aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                total_local_votacoes += aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                contador+=1
            #Se o total_local_de_votacoes for maior que zero, ou seja, se tem votação considerada...
            if total_local_votacoes > 0:
                item["valor"] = int(round((soma_movel / total_local_votacoes),0))
            else:
                item["valor"] = -1
            #print(partido,total_local_votacoes,soma_movel,aux_saida[partido][mes]["valor"], item["valor"])

            saida[partido].append(item)

    #escreve Json de saída
    with open (path+"/atualizacao/camara/"+mandato+"/hist_"+mandato[:-1]+"_camara_"+mandato[-1]+".json","w",encoding='UTF8') as jsonfile:
        jsonfile.write(json.dumps(saida))
    print("Histórico do mandato " + mandato + " salvo")

    with open (path+"/atualizacao/camara/"+mandato+"/hist_totais_"+mandato[:-1]+"_camara_"+mandato[-1]+".csv","w",encoding='UTF8') as afile:
        csvfile = csv.writer(afile, delimiter=',')
        csvfile.writerows(proposicoes_por_mes)
    print("Total de votações mensal do mandato " + mandato + " salvo")

#chame a função governismo_partido com 4 opções: fhc2, lula1, lula2 e dilma1
governismo_partido("fhc2")
governismo_partido("lula1")
governismo_partido("lula2")
governismo_partido("dilma1")

