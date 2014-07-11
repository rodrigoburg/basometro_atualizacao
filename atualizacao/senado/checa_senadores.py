#-*- coding: utf-8 -*-
#!/usr/bin/python3

from pandas import DataFrame, read_csv
from unicodedata import normalize

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
    votos = read_csv("senado_votos.csv",sep=";")
    votos["POLITICO"] = votos["POLITICO"].apply(remover_acentos)
    votos.to_csv("senado_votos.csv",sep=";",index=False)
    
def testa_voto():
    votos = read_csv("senado_votos.csv",sep=";")
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

