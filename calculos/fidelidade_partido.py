#-*- coding: utf-8 -*-
#!/usr/bin/python3

import csv
from datetime import datetime
from pandas import DataFrame
import re

def pega_orientacoes():
    try: 
        with open("orientacoes.csv","r") as file:
            arquivo = csv.reader(file)
            cod_votacao = []
            bancada = []
            orientacao = []
            data = []
            
            for row in arquivo:
                cod_votacao.append(row[0])
                data.append(row[1])
                bancada.append(row[3])
                orientacao.append(row[4])         
            
            orientacoes = {}
            for i in range(len(cod_votacao)):
                if not cod_votacao[i] in orientacoes:
                    orientacoes[cod_votacao[i]] = {} 
                    orientacoes[cod_votacao[i]]["bancadas"] = []
                    orientacoes[cod_votacao[i]]["orientacoes"] = []
                
                bloco = re.findall('P[a-z]+',bancada[i])
                repres = bancada[i].upper().split("REPR.")
                bloco_antigo = bancada[i].split("/")    
                bancada_invalida = ["GOV.","APOIO AO GOVERNO","MAIORIA","MINORIA"]
                
                orientacoes[cod_votacao[i]]["data"] = data[i]
                
                if bloco:
                    for b in bloco:
                        orientacoes[cod_votacao[i]]["bancadas"].append(b.upper())
                        orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])
                elif len(repres)!=1:
                    orientacoes[cod_votacao[i]]["bancadas"].append(repres[1].upper())
                    orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])
                elif len(bloco_antigo)!=1:
                    for b in bloco_antigo:
                        orientacoes[cod_votacao[i]]["bancadas"].append(b.upper())
                        orientacoes[cod_votacao[i]]["orientacoes"].append(orientacao[i])                    
                else:
                    if bancada[i].upper() not in bancada_invalida:
                        orientacoes[cod_votacao[i]]["bancadas"].append(conserta_bancada(bancada[i]))
                        orientacoes[cod_votacao[i]]["orientacoes"].append(conserta_bancada(orientacao[i]))
    
        return orientacoes
                    
    except FileNotFoundError:
        print("Não há arquivo de orientações. Favor fazer a consulta na API da Câmara primeiro")

def conserta_bancada(bancada):
    if bancada.upper() == "SOLIDARIED":
        return "SDD"
    elif bancada.upper() == "PFL":
        return "DEM"
    else:
        return bancada.upper()
            
def pega_votos():
    try:
        with open("votos.csv","r") as file:
            arquivo = csv.reader(file)
            next(arquivo, None)  # ignora o cabeçalho
            
            cod_votacao = []
            partido = []
            voto = []
            
            for row in arquivo:
                cod_votacao.append(row[0])
                partido.append(row[3])
                voto.append(row[4])
            
            votos = {}
            
            for i in range(len(cod_votacao)):
                if not cod_votacao[i] in votos:
                    votos[cod_votacao[i]] = {} 
                    votos[cod_votacao[i]]["partidos"] = []
                    votos[cod_votacao[i]]["votos"] = []
                
                votos[cod_votacao[i]]["partidos"].append(conserta_bancada(partido[i].upper()))
                votos[cod_votacao[i]]["votos"].append(conserta_bancada(voto[i]))
        
        return votos
        
    except FileNotFoundError:
        print("Não há arquivo de votos. Favor fazer a consulta na API da Câmara primeiro")
        
def junta_votos_orientacoes(votos, orientacoes, data_inicio, data_fim):
    votacoes = {}
    
    for key in orientacoes:
        data = datetime.strptime(orientacoes[key]["data"],'%d/%m/%Y')
        
        if data_inicio <= data <= data_fim:
            if key in votos:
                votacoes[key] = {}
                votacoes[key]["bancadas"] = orientacoes[key]["bancadas"]    
                votacoes[key]["orientacao"] = orientacoes[key]["orientacoes"]
                votacoes[key]["partido"] = votos[key]["partidos"]
                votacoes[key]["votos"] = votos[key]["votos"]
    return votacoes

def calcula_fidelidade(votacoes):
    resultado = {}
    num_votacoes = {}
    
    for key in votacoes:
        v = votacoes[key]
        for b in range(len(v["bancadas"])):
            bancada = v["bancadas"][b]
            orientacao = v["orientacao"][b]
            partidos = v["partido"]
            votos = v["votos"]
            if orientacao != "Liberado":
                if bancada not in resultado:
                    resultado[bancada] = []
                    num_votacoes[bancada] = 0
                voto = calcula_voto(key,bancada,orientacao,partidos,votos)
                if voto:
                    resultado[bancada].append(voto)
                    num_votacoes[bancada] +=1
    
    for key in resultado:
        resultado[key] = mean("baba",resultado[key])

    return resultado,num_votacoes

def calcula_voto(key,bancada,orientacao,partidos,votos):
    lista_votos=[]
    for p in range(len(partidos)):
        if partidos[p] == bancada:
            if votos[p].upper() == orientacao.upper():
                lista_votos.append(1)
            else:
                lista_votos.append(0)
    
    if not lista_votos:
        return False
    else:
        return mean(bancada,lista_votos)

def mean(bancada,lista):
    if(lista):
        return float(sum(lista))/len(lista)
    else:
        return 0 
def arruma_resultado(resultado_velho,num_votacoes):
    resultado = DataFrame({"partido":list(resultado_velho.keys()),"fidelidade_interna":list(resultado_velho.values()),"num_votacoes":list(num_votacoes.values())})
    resultado = resultado.sort("fidelidade_interna",ascending=False)
    return resultado    
    
#função para transformar o número de um dataframe em tipo float (será usada na função abaixo)
def conserta_numero(numero):
    if list(numero):
        return float(numero)
    else:
        return 0

def fidelidade_partido(intervalo):
    data_inicio = datetime.strptime(intervalo[0],'%d/%m/%Y')
    data_fim = datetime.strptime(intervalo[1],'%d/%m/%Y')
    orientacoes = pega_orientacoes()
    votos = pega_votos()
    votacoes = junta_votos_orientacoes(votos,orientacoes,data_inicio,data_fim)
    resultado,num_votacoes = calcula_fidelidade(votacoes)
    resultado = arruma_resultado(resultado,num_votacoes)
    print("A tabela de fidelidade dentro de cada partido entre "+intervalo[0]+" e "+intervalo[1]+" é:\n")
    print(resultado)
    return resultado
    
def faz_consulta(datas):
    resultados = []
    for i in range(len(datas)):
        resultados.append(fidelidade_partido(datas[i]))
    
    todos_partidos = []
    for r in resultados:
        todos_partidos += list(r["partido"])
    todos_partidos = set(todos_partidos)
    
    novas_datas = [d[0] + "-" + d[1] for d in datas]
    
    with open("analise_fidelidade_interna.csv", "w+", encoding='UTF8') as saida:
        linha = []
        header = ["partido"] + novas_datas
        escreve_res = csv.writer(saida, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        escreve_res.writerow(header)
        for p in todos_partidos:
            linha = [p]
            for r in resultados:
                linha.append(conserta_numero(r.fidelidade_interna[r.partido == p]))         
            escreve_res.writerow(linha)
        
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