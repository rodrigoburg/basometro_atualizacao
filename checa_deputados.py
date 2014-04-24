#-*- coding: utf-8 -*-
#!/usr/bin/python3

from pandas import DataFrame, read_csv
from unicodedata import normalize
import os
import csv

os.chdir("/Users/rodrigoburgarelli/Documents/Estadão Dados/Basômetro")

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')

def limpar_votos():
    votos = read_csv("votos.csv",sep=";")
    votos["POLITICO"] = votos["POLITICO"].apply(remover_acentos)
    votos["POLITICO"][votos.POLITICO == "MANUELA D`AVILA"] = "MANUELA DAVILA"
    votos["POLITICO"][votos.POLITICO == "BERNARDO SANTANA DE VASCONCELLO"] = "BERNARDO SANTANA DE VASCONCELLOS"
    votos["POLITICO"][votos.POLITICO == "PROFESSORA DORINHA SEABRA REZENDEDE"] = "PROFESSORA DORINHA SEABRA REZENDE"    
    votos["POLITICO"][votos.POLITICO == "ELVINO BOHN GASS"] = "BOHN GASS"
    votos["POLITICO"][votos.POLITICO == "CHICO D`ANGELO"] = "CHICO DANGELO"
    votos["POLITICO"][votos.POLITICO == "AGNOLIN"] = "ANGELO AGNOLIN"
    votos["POLITICO"][votos.POLITICO == "DR. FRANCISCO ARAUJO"] = "FRANCISCO ARAUJO"
    votos["POLITICO"][votos.POLITICO == "FELIX JUNIOR"] = "FELIX MENDONCA JUNIOR"
    votos["POLITICO"][votos.POLITICO == "ANTONIO CARLOS BIFFI"] = "BIFFI"
    votos["POLITICO"][votos.POLITICO == "JOAO PAULO  LIMA"] = "JOAO PAULO LIMA"
    votos["POLITICO"][votos.POLITICO == "JOSE DE FILIPPI JUNIOR"] = "JOSE DE FILIPPI"    
    
    votos.to_csv("votos.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)
    
def testa_voto():
    votos = read_csv("votos.csv",sep=";")
    politicos = read_csv("politicos_dilma.csv",sep=";")
    lista_politicos = []

    for p in votos["POLITICO"]:
        if p not in list(politicos["NOME_CASA"]):
            lista_politicos.append(p)

    lista_politicos = list(set(lista_politicos))
    print(len(lista_politicos))
    print(lista_politicos)

limpar_votos()
testa_voto()
