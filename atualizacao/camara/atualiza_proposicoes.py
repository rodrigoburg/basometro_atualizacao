#-*- coding: utf-8 -*-
#!/usr/bin/python3

# SOBRE ESTE ARQUIVO
# Este script está dividido em várias pequenas funções, que são
# depois coordenadas pela função principal obter_proposicoes(ano).
# O objetivo final dessa função é consultar a API da Câmara para
# criar dois arquivos no diretório local: o proposicoes.csv, com a
# lista de todas as proposições votadas no ano em questão com suas
# iformações principais (data da votação, ementa, orientação do
# governo, etc), e o votos.csv, com a lista de como cada deputado
# votou em cada uma dessas votações.

# Se os arquivos já existirem, a função checa se há registros no
# proposicoes.csv para o ano em que se está atualizando. Se houver,
# ela irá acrescentar apenas os registros que estão no site da Câmara
# mas não no arquivo local de proposições. Se não houver registros
# para esse ano, a função irá simplesmente adicionar todos que
# retornarem da API da Câmara como votados em plenário no ano ementa
# questão. Os votos de cada deputado serão acrescentados no arquivo
# votos.csv para toda votação que for acrescentada seguindo os
# critérios descritos acima.

import hashlib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime as dt
import os


def existe_arquivo_proposicoes():
    path = os.path.dirname(os.path.abspath(__file__))
    
    #""" Checa se há arquivo de proposicoes no diretório local. se houver,
    #    ele já retorna esse arquivo"""
    try:
        with open("proposicoes.csv", "r") as file:
            return file
    except IOError:
        print("Não há arquivo de votações no diretório local.")
        return False


def cria_arquivo_vazio_proposicoes():
    #""" Cria um arquivo vazio de proposicoes caso não exista
    #    no diretório local"""
    with open("proposicoes.csv", "w", encoding='UTF8') as file:
        writer = csv.writer(
            file,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)
        writer.writerow(
            ["ID_VOTACAO",
            "DATA",
            "HORA",
            "ORIENTACAO_GOVERNO",
            "TIPO",
            "NUMERO",
            "ANO",
            "EMENTA",
            "O_QUE_FOI_VOTADO",
            "LINGUAGEM_COMUM"])


def existe_arquivo_votos():
    #""" Checa se há arquivo de votos no diretório local"""
    try:
        with open("votos.csv", "r") as arquivo:
            return arquivo
    except IOError:
        print("Não há arquivo de votos no diretório local.")
        return False


def cria_arquivo_vazio_votos():
    #""" Cria um arquivo vazio de votos caso não exista no diretório local"""
    with open("votos.csv", "w", encoding='UTF8') as file:
        writer = csv.writer(
            file,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)
        writer.writerow(["ID_VOTACAO",
                         "POLITICO",
                         "VOTO",
                         "PARTIDO"])


def busca_proposicoes_antigas(ano):
    #""" Retorna uma lista com os códigos de todas as proposições que
    #    estão no arquivo local, no ano pesquisado"""

    prop_antigas = []
    with open("proposicoes.csv", "r") as file:
        arquivo = csv.reader(file,delimiter = ";")
        next(arquivo, None)  # ignora o cabeçalho
        for row in arquivo:
            # só adiciona na lista as do mesmo ano que está sendo atualizado
            if row[1][0:2] == ano[2:4]:
                # a segunda coluna é a do codigo
                prop_antigas.append(row[0])
        print("Há " + str(len(prop_antigas)) +
              " votações de " + str(ano) +
              " no arquivo salvo.")
        return prop_antigas

def pega_todas_proposicoes(ano):
    # Função que busca o API da Câmara e retorna o XML
    #    de todas as votações de um determinado ano"""
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano=" + ano + "&tipo="
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    proposicoes = bs.findAll("proposicao")
    lista_props = []
    for p in proposicoes:
        if p.codproposicao.string not in lista_props:
            lista_props.append(p.codproposicao.string)
    return lista_props


def obter_dados_proposicao(prop):
    #"""Função que pega os dados extras de cada proposição,
    #    por meio de duas consultas diferentes"""
    prop = pega_dados_API_proposicao(prop)
    prop = pega_dados_API_votacoes(prop)
    return prop


def pega_dados_API_proposicao(prop):
    #"""Pega os dados da proposicao de acordo com a API de proposicoes"""
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ObterProposicaoPorID?IdProp=" + prop["codigo"]
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    prop["tipo"] = bs.proposicao["tipo"].strip()
    prop["numero"] = bs.proposicao["numero"]
    prop["ano"] = bs.proposicao["ano"]
    # pega apenas a nova ementa nas proposições
    # em que ela tiver sido atualizada
    if "NOVA EMENTA:" in bs.ementa.string:
        ementa = bs.ementa.string.split("NOVA EMENTA:")
        prop["ementa"] = ementa[1].strip().replace("\"","\'").replace("\n"," - ")
    else:
        prop["ementa"] = bs.ementa.string.strip().replace("\"","\'").replace("\n"," - ")
    return prop


def pega_dados_API_votacoes(proposicao):
    #"""Pega os dados da proposicao de acordo com a API de proposicoes"""
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo=" + proposicao["tipo"] + "&numero=" + proposicao["numero"] + "&ano=" + proposicao["ano"]
    proposicao["votacoes"] = []
    try:
        connection = urlopen(url)
        data = connection.read()
    except:
        return proposicao
    bs = BeautifulSoup(data)
    votacoes = bs.findAll("votacao")

    #agora ele pega todas as informações para cada votação ocorrida no ano
    for votacao_ in votacoes:
        #retira votações de outros anos
        if votacao_["data"][-4:] == proposicao["ano_votacao"]:
            votacao = {}
            votacao["data_votacao"] = votacao_["data"]
            votacao["hora_votacao"] = votacao_["hora"]
            votacao["resumo"] = votacao_["resumo"].strip().replace("\"","\'").replace("\n"," - ")
            votacao["codigo"] = codigo_votacao(votacao,proposicao["codigo"])
            votacao["orientacao_governo"] = "Não existe"
            votacao["votos"] = []

            try:
                #testa se há ou não há orientações para
                #essa votação e pega esses dados
                votacao["orientacoes"] = { o["sigla"].strip() : o["orientacao"].strip()
                              for o in votacao_.orientacaobancada.findAll("bancada") }
                votacao["orientacao_governo"] = votacao["orientacoes"].get("GOV.", "Não existe")
            except:
                pass

            try:
                for voto_ in votacao_.votos.findAll("deputado"):
                    voto = {}
                    #testa e pega dados das votações
                    voto["idecadastro"] = voto_["idecadastro"]
                    voto["nome"] = voto_["nome"]
                    voto["voto"] = voto_["voto"].strip()
                    voto["partido"] = voto_["partido"].strip()
                    votacao["votos"].append(voto)
            except:
                pass

            proposicao["votacoes"].append(votacao)

    return proposicao

def media_algarismos(numero):
    soma = 0
    for i in numero:
        soma += int(i)
    return str(int(soma/len(numero)))

def codigo_votacao(votacao,codigo_proposicao):
    #Gera um código único para cada votação
    return hashlib.md5((votacao["data_votacao"]+votacao["hora_votacao"]+votacao["resumo"]+codigo_proposicao).encode()).hexdigest()

def parse_data_votacao(votacao):
    #recupera a data da votação
    data = votacao["data_votacao"].split("/")
    data = data[2][2:4] + "%02d" % int(data[1]) + "%02d" % int(data[0])
    #cria código para a data e hora
    return data

def adiciona_novas_proposicoes(lista_proposicoes, prop_antigas, ano):
    #"""De acordo com a consulta na API, grava as novas proposicoes
    #    que não estiverem já listados no csv antigo"""
    contador = 0
    #prepara os dois arquivos de saída
    with open("proposicoes.csv", "a", encoding='UTF8') as prop_saida,\
            open("votos.csv", "a", encoding='UTF8') as voto_saida,\
            open("orientacoes.csv","a",encoding='UTF8') as orientacao_saida:

        escreve_prop = csv.writer(
            prop_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)
        escreve_voto = csv.writer(
            voto_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)
        escreve_orientacao = csv.writer(
            orientacao_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)

        repeticoes = 0
        #loop que escreve as votações, votos e orientações
        for codigo_proposicao in lista_proposicoes:
            proposicao = {}
            proposicao["codigo"] = codigo_proposicao
            proposicao["ano_votacao"] = ano
            proposicao = obter_dados_proposicao(proposicao)

            #para cada uma das votações registradas
            if len(proposicao["votacoes"]) > 0:
                for votacao in proposicao["votacoes"]:
                    #cria o código para ver se a votação já foi registrada antess
                    data = parse_data_votacao(votacao)

                    #se não é repetido
                    if votacao["codigo"] not in prop_antigas:
                        #se existe orientação do governo
                        if votacao["orientacao_governo"] in ["Sim","Não"]:
                            prop_antigas.append(votacao["codigo"])
                            contador += 1
                            escreve_prop.writerow([votacao["codigo"],
                                                   data,
                                                   votacao["hora_votacao"] + ":00",
                                                   votacao["orientacao_governo"],
                                                   proposicao["tipo"],
                                                   proposicao["numero"],
                                                   proposicao["ano"],
                                                   proposicao["ementa"],
                                                   votacao["resumo"]])

                            #loop para adicionar uma linha para cada
                            # deputado no arquivo de votos
                            try:
                                for voto_ in votacao["votos"]:
                                    escreve_voto.writerow(
                                        [votacao["codigo"],
                                         voto_["nome"].upper(),
                                         voto_["voto"].upper(),
                                         voto_["partido"]])
                            except:
                                pass

                            #loop para adicionar orientações no arquivo de orientações
                            try:
                                for orientacao_ in votacao["orientacoes"]:
                                    escreve_orientacao.writerow(
                                        [votacao["codigo"],
                                        votacao["data_votacao"],
                                        votacao["hora_votacao"],
                                        orientacao_,
                                        votacao["orientacoes"][orientacao_]])
                            except:
                                pass
                    #se houver repeticao:
                    else:
                        repeticoes += 1

    print("Foram adicionadas " + str(contador) + " votações no arquivo local, com "+str(repeticoes)+" repeticoes.\n")


def obter_proposicoes(ano):
    #"""obtem todas as proposições votadas em um determinado ano
    #    articulando as funções anteriores"""
    print("Atualizando proposições de: "+ano)

    prop_antigas = []

    if existe_arquivo_proposicoes():
        prop_antigas = busca_proposicoes_antigas(ano)
    else:
        cria_arquivo_vazio_proposicoes()

    if not existe_arquivo_votos():
        cria_arquivo_vazio_votos()

    proposicoes = pega_todas_proposicoes(ano)
    adiciona_novas_proposicoes(proposicoes, prop_antigas, ano)

obter_proposicoes("2007")
obter_proposicoes("2008")
obter_proposicoes("2009")
obter_proposicoes("2010")
