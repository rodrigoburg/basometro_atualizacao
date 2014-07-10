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

from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime as dt


def existe_arquivo_proposicoes():
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
            "O_QUE_FOI_VOTADO"])


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
        prop["ementa"] = ementa[1].strip().replace("\"","\'")
    else:
        prop["ementa"] = bs.ementa.string.strip().replace("\"","\'")
    return prop


def pega_dados_API_votacoes(prop):
    #"""Pega os dados da proposicao de acordo com a API de proposicoes"""
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo=" + prop["tipo"] + "&numero=" + prop["numero"] + "&ano=" + prop["ano"]
    try:
        connection = urlopen(url)
        data = connection.read()
    except:
        return prop
    bs = BeautifulSoup(data)
    votacoes = bs.findAll("votacao")
    prop["num_votacoes"] = 0
    prop["data_votacao"] = []
    prop["hora_votacao"] = []
    prop["orientacao_governo"] = []
    prop["resumo"] = []
    prop["orientacoes"] = []
    prop["votos"] = []
    votos = {}

    #agora ele pega todas as informações para cada votação ocorrida no ano
    for v in votacoes:
        #retira votações de outros anos
        if v["data"][-4:] == prop["ano_votacao"]:
            prop["num_votacoes"] += 1
            prop["data_votacao"].append(v["data"])
            prop["hora_votacao"].append(v["hora"])
            prop["resumo"].append(v["resumo"].strip().replace("\"","\'"))

            try:
                #testa se há ou não há orientações para
                #essa votação e pega esses dados
                sigla = [o["sigla"].strip()
                         for o in v.orientacaobancada.findAll("bancada")]
                orientacao = [o["orientacao"].strip()
                              for o in v.orientacaobancada.findAll("bancada")]
                orientacoes = dict(zip(sigla, orientacao))
                prop["orientacao_governo"].append(
                    orientacoes.get("GOV.", "Não existe"))
                prop["orientacoes"].append(orientacoes)
            except:
                prop["orientacao_governo"].append("Não existe")

            try:
                #testa e pega dados das votações
                votos["idecadastro"] = [v["idecadastro"]
                                        for v in v.votos.findAll("deputado")]
                votos["nome"] = [v["nome"]
                                 for v in v.votos.findAll("deputado")]
                votos["voto"] = [v["voto"].strip()
                                 for v in v.votos.findAll("deputado")]
                votos["partido"] = [v["partido"].strip()
                                    for v in v.votos.findAll("deputado")]
                prop["votos"].append(votos)
            except:
                pass
    return prop

def media_algarismos(numero):
    soma = 0
    for i in numero:
        soma += int(i)
    return str(int(soma/len(numero)))
    
def cria_novo_codigo(data_votacao,hora_votacao,codigo,resumo):    
    #cria código para a data e hora
    data = data_votacao.split("/")
    codigo_data = media_algarismos(data[2][2:4] + "%02d" % int(data[1])) + media_algarismos("%02d" % int(data[0])) + hora_votacao.replace(":","") 
    data = data[2][2:4] + "%02d" % int(data[1]) + "%02d" % int(data[0])
                    
    #normaliza o número de caracteres em 8 para o código normal da proposição
    codigo_codigo = "%07d" % int(codigo)
    
    #cria código para o resumo (número que representa matematicamente o
    #resumo para diferenciar as votações registradas na mesma hora)
    tamanho = len(resumo)
    if tamanho == 0:
        codigo_resumo = "000"
    else:
        codigo_resumo = "%03d" % int((ord(resumo[int(tamanho/2)]) + ord(resumo[int(tamanho/3)]) + ord(resumo[int(tamanho/4)])) / 3)
    
    #junta os códigos
    return codigo_data + codigo_codigo + codigo_resumo,data
    

def adiciona_novas_proposicoes(proposicoes, prop_antigas, ano):
    #"""De acordo com a consulta na API, grava as novas proposicoes
    #    que não estiverem já listados no csv antigo"""
    contador = 0
    prop = {}
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
        for p in proposicoes:
            prop["codigo"] = p
            prop["ano_votacao"] = ano
            prop = obter_dados_proposicao(prop)
            
            #para cada uma das votações registradas
            for i in range(prop["num_votacoes"]):
                #cria o código para ver se a votação já foi registrada antess    
                novo_codigo,data = cria_novo_codigo(prop["data_votacao"][i],prop["hora_votacao"][i],prop["codigo"],prop["resumo"][i])
                
                #se não é repetido
                if novo_codigo not in prop_antigas:
                    #se existe orientação do governo
                    if prop["orientacao_governo"][i] in ["Sim","Não"]:
                        prop_antigas.append(novo_codigo)
                        contador += 1
                        escreve_prop.writerow([novo_codigo,
                                               data,
                                               prop["hora_votacao"][i] + ":00",
                                               prop["orientacao_governo"][i],
                                               prop["tipo"],
                                               prop["numero"],
                                               prop["ano"],
                                               prop["ementa"],
                                               prop["resumo"][i]])

                    #loop para adicionar uma linha para cada
                    # deputado no arquivo de votos
                        try:
                            for d in range(len(prop["votos"][i]["voto"])):
                                escreve_voto.writerow(
                                    [novo_codigo,
                                     prop["votos"][i]["nome"][d].upper(),
                                     prop["votos"][i]["voto"][d].upper(),
                                     prop["votos"][i]["partido"][d]])
                        except:
                            pass
                    
                    #loop para adicionar orientações no arquivo de orientações
                        try:
                            for o in range(len(prop["orientacoes"][i])):
                                escreve_orientacao.writerow(
                                [novo_codigo,
                                prop["data_votacao"][i],
                                prop["hora_votacao"][i],
                                list(prop["orientacoes"][i].keys())[o],
                                list(prop["orientacoes"][i].values())[o]])
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

obter_proposicoes("2011")
obter_proposicoes("2012")
obter_proposicoes("2013")
obter_proposicoes("2014")
