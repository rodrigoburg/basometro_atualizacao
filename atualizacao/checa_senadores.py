#-*- coding: utf-8 -*-
#!/usr/bin/python3

from pandas import DataFrame, read_csv
from unicodedata import normalize
import os

os.chdir("/Users/rodrigoburgarelli/Documents/Estadão Dados/Basômetro")

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')

def limpar_votos():
    votos = read_csv("senado_votos_novo.csv",sep=";")
    votos["POLITICO"] = votos["POLITICO"].apply(remover_acentos)
    votos.to_csv("senado_votos_novo.csv",sep=";",index=False)
    
def testa_voto():
    votos = read_csv("senado_votos_novo.csv",sep=";")
    politicos = read_csv("senadores.csv",sep=";")
    lista_politicos = []

    for p in votos["POLITICO"]:
        if p not in list(politicos["NOME_CASA"]):
            lista_politicos.append(p)

    lista_politicos = list(set(lista_politicos))
    print(len(lista_politicos))
    print(lista_politicos)
limpar_votos()
testa_voto()