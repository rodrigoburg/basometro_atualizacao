#-*- coding: utf-8 -*-
#!/usr/bin/python3

from pandas import DataFrame, read_csv
from unicodedata import normalize
from urllib.request import urlopen
import urllib.request
from bs4 import BeautifulSoup
import os
import csv

def remover_acentos(txt):
    txt = txt.strip()
    txt = normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')
    traducao = {
        "Assis Gurgacz":"Acir Gurgacz"
    }
    if txt in traducao:
        return traducao[txt]
    else:
        return txt

def limpar_votos():
    votos = read_csv(path+"senado_votos.csv",sep=";")
    votos["POLITICO"] = votos["POLITICO"].apply(remover_acentos)
    votos.to_csv(path+"senado_votos.csv",sep=";",index=False)

def testa_voto():
    votos = read_csv(path+"senado_votos.csv",sep=";")
    politicos = read_csv(path+"senadores.csv",sep=";")
    lista_politicos = []

    for p in votos["POLITICO"]:
        if p not in list(politicos["NOME_CASA"]):
            lista_politicos.append(p)

    lista_politicos = list(set(lista_politicos))
    print("Estão faltando "+str(len(lista_politicos)) + " senadores no arquivo de políticos.")
    print(lista_politicos)

    if len(lista_politicos) > 0:
        acha_senador(lista_politicos)


def acha_senador(senadores):
    politicos = read_csv(path+"senadores.csv",sep=";")
    mandatos = ["54"]
    for m in mandatos:
        url = "http://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/"+m
        bs = BeautifulSoup(urlopen(url).read())
        lista_senadores = bs.findAll("parlamentar")
        for sen in lista_senadores:
            nome = remover_acentos(sen.nomeparlamentar.string)
            if nome in senadores:
                senador = {}
                senador['POLITICO'] = nome
                senador['NOME_CASA'] = nome
                senador['PARTIDO'] = sen.siglapartido.string
                senador['UF'] = sen.siglauf.string
                senador['ID'] = sen.codigoparlamentar.string
                senador['ANO_MANDATO'] = "--"
                senador['LEGISLATURA'] = sen.legislaturainicio.string + "/" + sen.legislaturafim.string
                senador['URL_FOTO'] = ""
                politicos = politicos.append(senador,ignore_index=True)
                print("Adicionado político: "+nome)
    politicos.to_csv(path+"senadores.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)


def descompactar_arquivos():
    os.system("bunzip2 "+path+"*.bz2")

def compactar_arquivos():
    os.system("bzip2 -9 "+path+"*.csv "+path+"*.json")

def baixa_fotos():
    #cria diretório paras as fotos, se não houver
    if not os.path.isdir(path+"/"+mandato+"/fotos"):
        print("Criando diretório para as fotos")
        os.system("mkdir "+path+"/"+mandato)
        os.system("mkdir "+path+"/"+mandato+"/fotos")

    politicos = read_csv(path+"senadores.csv",sep=";")
    sen_sem_foto = politicos[politicos.URL_FOTO.isnull()]
    sen_sem_foto = list(sen_sem_foto["NOME_CASA"])


    #url = "file://"+path+"/Deputados.xml"
    url = "http://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/54"
    bs = BeautifulSoup(urlopen(url).read())
    senadores = bs.findAll("parlamentar")
    for s in senadores:
        nome = remover_acentos(s.nomeparlamentar.string)
        if nome in sen_sem_foto:
            codigo = str(list(politicos[politicos.NOME_CASA == nome]["ID"])[0])
            try:
                urllib.request.urlretrieve(s.urlfotoparlamentar.string, path+"/"+mandato+"/fotos/"+codigo+".jpg")
                politicos.loc[politicos.NOME_CASA == nome,"URL_FOTO"] = "sen_" + codigo+".jpg"
            except urllib.error.HTTPError:
                politicos.loc[politicos.NOME_CASA == nome,"URL_FOTO"] = "sem_foto.jpg"


            print(s.urlfotoparlamentar.string)
            #politicos.loc[politicos.POLITICO == dep_sem_acento]["URL_FOTO"] = d.urlfoto.string
#    politicos["ANO_MANDATO"] = politicos["ANO_MANDATO"].apply(int)
#    politicos["LEGISLATURA"] = politicos["LEGISLATURA"].apply(int)
    politicos.loc[politicos.URL_FOTO.isnull(),"URL_FOTO"] = "sem_foto.jpg"
    politicos.to_csv(path+"/senadores.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

mandato = "dilma1"
path = os.path.dirname(os.path.abspath(__file__))+"/"

#descompactar_arquivos()
#limpar_votos()
#testa_voto()
#baixa_fotos()
compactar_arquivos()
