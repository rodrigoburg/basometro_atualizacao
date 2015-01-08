#-*- coding: utf-8 -*-
#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
from pandas import DataFrame, read_csv
from unicodedata import normalize
import os
import csv

def traduz_nome(txt):
    #remove acentos
    saida = normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')

    #remove espaços extras
    saida = saida.strip()

    #muda nomes errados
    traducao = {
        "MANUELA D`AVILA":"MANUELA DAVILA",
        "MANUELA D'AVILA":"MANUELA DAVILA",
        "MANUELA D'ÁVILA":"MANUELA DAVILA",
        "CHICO D'ANGELO":"CHICO DANGELO",
        "BERNARDO SANTANA DE VASCONCELLO":"BERNARDO SANTANA DE VASCONCELLOS",
        "PROFESSORA DORINHA SEABRA REZENDEDE":"PROFESSORA DORINHA SEABRA REZENDE",
        "DRA. ELAINE ABISSAMRA":"DRA.ELAINE ABISSAMRA",
        "ELVINO BOHN GASS":"BOHN GASS",
        "CHICO D`ANGELO":"CHICO DANGELO",
        "AGNOLIN":"ANGELO AGNOLIN",
        "DR. FRANCISCO ARAUJO":"FRANCISCO ARAUJO",
        "FELIX JUNIOR":"FELIX MENDONCA JUNIOR",
        "ANTONIO CARLOS BIFFI":"BIFFI",
        "JOAO PAULO  LIMA":"JOAO PAULO LIMA",
        "JOSE DE FILIPPI JUNIOR":"JOSE DE FILIPPI",
    }

    if saida in traducao:
        return traducao[saida]
    else:
        return saida

def traduz_voto(voto):
    voto = voto.strip()
    traducao = {
        "NÃO":"NAO",
        "OBSTRUÇÃO":"OBSTRUCAO",
        "ABSTENÇÃO":"ABSTENCAO",
        "ART. 17":"PRESIDENTE"
    }
    if voto in traducao:
        return traducao[voto]
    else:
        return voto

def traduz_partido(partido):
    partido = partido.strip()
    traducao = {
        "Solidaried":"SDD",
        "PFL":"DEM"
    }
    if partido in traducao:
        return traducao[partido]
    else:
        return partido

def limpar_votos(mandato):
    path = os.path.dirname(os.path.abspath(__file__))

    votos = read_csv(path+"/"+mandato+"/votos.csv",sep=";", dtype=object)
    props = read_csv(path+"/"+mandato+"/proposicoes.csv",sep=";",dtype=object)

    #arruma nome dos deputados, partidos e votos
    votos["POLITICO"] = votos["POLITICO"].apply(traduz_nome)
    votos["VOTO"] = votos["VOTO"].apply(traduz_voto)
    votos["PARTIDO"] = votos["PARTIDO"].apply(traduz_partido)

    #se tiver a votação do senado no meio da Câmara, retira
    votos = votos[votos.ID_VOTACAO != "dd36cd4acaa5bf214f0e107c5ab0ec57"]
    props = props[props.ID_VOTACAO != "dd36cd4acaa5bf214f0e107c5ab0ec57"]


    #arruma o nome
    votos.to_csv(path+"/"+mandato+"/votos.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)
    props.to_csv(path+"/"+mandato+"/proposicoes.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

def checa_deputado(mandato):
    path = os.path.dirname(os.path.abspath(__file__))
    votos = read_csv(path+"/"+mandato+"/votos.csv",sep=";")
    try:
        politicos = read_csv(path+"/"+mandato+"/deputados.csv",sep=";")
    except OSError: #se não houver arquivo de deputados, cria um DF vazio
        colunas = ['POLITICO', 'NOME_CASA','PARTIDO',"UF",'ID',"ANO_MANDATO","LEGISLATURA","URL_FOTO"]
        politicos = DataFrame(columns=colunas)


    lista_politicos = []
    partido = {} #aqui é para guardar o partido de cada político

    for p in votos["POLITICO"]:
        if p not in list(politicos["NOME_CASA"]):
            lista_politicos.append(p)
            if p not in partido:
                sigla = list(votos[votos.POLITICO == p]["PARTIDO"])
                partido[p] = sigla[0]

    lista_politicos = list(set(lista_politicos))

    print(len(lista_politicos))

    print(partido)
    if (lista_politicos):
        adiciona_deputados(lista_politicos,politicos,partido,mandato)

def adiciona_deputados(lista_deputados,politicos,partido,mandato):
    #url principal e dados principais
    url = "http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    dados = BeautifulSoup(urlopen(url).read())
    deputados = dados.findAll("deputado")

    #for d in deputados:
        #print(d.nomeparlamentar.string)
        #print(lista_deputados)
        #print(lista_deputados[0] == d.nomeparlamentar.string)

    #endereço local do arquivo XML com deputados antigos
    #o link para o download deste arquivo é este:
    #http://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo/webservices/deputados
    path = os.path.dirname(os.path.abspath(__file__))
    
    url2 = "file://"+path+"/Deputados.xml"
    dados2 = BeautifulSoup(urlopen(url2).read())
    deputados2 = dados2.findAll("deputado")

    #para cada deputado fora do nosso arquivo
    for d in lista_deputados:
        deputado = {}
        #procura as infos desse deputado no site
        for i in deputados:
            dep_sem_acento = traduz_nome(i.nomeparlamentar.string)
            if (dep_sem_acento == d): #se esse deputado estiver no site
                deputado["POLITICO"] = i.nomeparlamentar.string
                deputado["NOME_CASA"] = dep_sem_acento
                deputado["PARTIDO"] = i.partido.string
                deputado["UF"] = i.uf.string
                deputado["ID"] = i.idparlamentar.string
                deputado["ANO_MANDATO"] = "2011"
                deputado["LEGISLATURA"] = "54"
                deputado["URL_FOTO"] = i.urlfoto.string

        #se esse deputado não estiver no site, procura no arquivo local:
        if not deputado:
            for i in deputados2:
                dep_sem_acento = traduz_nome(i.nomeparlamentar.string)
                if (dep_sem_acento == d):
                    deputado["POLITICO"] =  i.nomeparlamentar.string
                    deputado["NOME_CASA"] = dep_sem_acento
                    deputado["PARTIDO"] = i.legendapartidoeleito.string
                    deputado["UF"] = i.ufeleito.string
                    deputado["ID"] = i.idecadastro.string
                    deputado["LEGISLATURA"] = i.numlegislatura.string
                    deputado["ANO_MANDATO"] = "2011" if deputado["LEGISLATURA"] == "54" else "2007"
                    deputado["URL_FOTO"] = ""
        
        #se não tiver nem no arquivo local, só adicione um deputado incognita no arquivo de deputados
        
        if not deputado:
            deputado["POLITICO"] =  d
            deputado["NOME_CASA"] = d
            deputado["PARTIDO"] = partido[d]
            deputado["UF"] = "NA"
            deputado["ID"] = "NA"
            deputado["LEGISLATURA"] = "NA"
            deputado["ANO_MANDATO"] = "NA"
            deputado["URL_FOTO"] = ""
            
        if deputado:
            politicos = politicos.append(deputado,ignore_index=True)
            print("Político adicionado: "+deputado["NOME_CASA"])
        
    politicos.to_csv(path+"/"+mandato+"/deputados.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

def checa_proposicoes(mandato):
    votos = read_csv(path+"/"+mandato+"/votos.csv",sep=";")
    props = read_csv(path+"/"+mandato+"/proposicoes.csv",sep=";")
    for p in list(props["ID_VOTACAO"]):
        if not (p in list(votos["ID_VOTACAO"])):
            print(p)

    #for p in list(votos["ID_VOTACAO"]):
    #    if not (p in list(props["ID_VOTACAO"])):
    #        print("hue")


def descompactar_arquivos(mandato):
    os.system("bzip2 -d "+path+"/"+mandato+"/*")

def compactar_arquivos(mandato):
    os.system("bzip2 -z "+path+"/"+mandato+"/*")


#lista de mandatos: fhc2,lula1,lula2,dilma1,dilma2
mandato = "dilma1"
path = os.path.dirname(os.path.abspath(__file__))

descompactar_arquivos(mandato)
limpar_votos(mandato)
checa_proposicoes(mandato)
checa_deputado(mandato)
compactar_arquivos(mandato):