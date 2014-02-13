#-*- coding: utf-8 -*-
#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv

#checa se há arquivo de deputados no diretório local. se houver, ele já retorna esse arquivo
def existe_arquivo_deputados():
    try: 
        arquivo = csv.reader(open("deputados.csv","r"))
        return arquivo
    except FileNotFoundError:
        return False

#cria um arquivo vazio de deputados caso não exista no diretório local
def cria_arquivo_vazio():
    output  = open("deputados.csv", "w", encoding='UTF8')
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(["id","nome","partido"])
    output.close()

#retorna uma lista com os códigos de todos os deputados que estão no arquivo local
def busca_deputados_antigos(arquivo):
    dep_antigos = []
    next(arquivo, None) #ignora o cabeçalho
    for row in arquivo:
        dep_antigos.append(row[0]) #a primeira coluna é a do ID
    return dep_antigos

#consulta a API da Câmara para os deputados e retorna o XML só com os campos de deputado
def consulta_API_camara():
    url = "http://www.camara.gov.br/sitcamaraws/deputados.asmx/ObterDeputados"
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    return bs.findAll("deputado")

#de acordo com a consulta na API, grava os novos deputados que não estiverem já listados no csv antigo
def adiciona_novos_deputados(deputados,dep_antigos):
    #prepara o arquivo de saída
    output  = open("deputados.csv", "a", encoding='UTF8')
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
    #se o id não estiver na lista atual, adicione uma nova linha com os seus dados
    for d in deputados:
        if d.idparlamentar.string not in dep_antigos:
            writer.writerow([d.idparlamentar.string,d.nome.string,d.partido.string])
    output.close()

#função que articula todas as anteriores e faz todo o processo de atualização
def atualiza_deputados():
    
    dep_antigos = []
    arquivo = existe_arquivo_deputados()

    if (arquivo):
        dep_antigos = busca_deputados_antigos(arquivo)
    else:
        cria_arquivo_vazio()
    
    deputados = consulta_API_camara()
    
    adiciona_novos_deputados(deputados,dep_antigos)
                    
    
atualiza_deputados()