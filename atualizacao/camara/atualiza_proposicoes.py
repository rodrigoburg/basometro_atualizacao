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
import bz2
import codecs
import json
import io
import unicodedata

TIPOS_DE_VOTOS = {
        'NAO': 0,
        'SIM': 1,
        'ABSTENCAO': 2,
        'OBSTRUCAO': 3,
        'NAO VOTOU': 4,
        'PRESIDENTE': 5
    }

csv.register_dialect('basometro', delimiter=';', quoting=csv.QUOTE_NONNUMERIC)


def traduz_nome(txt):
    #remove acentos
    norm = unicodedata.normalize('NFKD', txt)
    saida = norm.encode('ASCII','ignore')

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


def existe_arquivo_proposicoes():
    """ Checa se há arquivo de proposicoes no diretório local. se houver,
        ele já retorna esse arquivo"""
    try:
        with open(path+"proposicoes.csv", "r") as file:
            return file
    except IOError:
        print("Não há arquivo de votações no diretório local.")
        return False


def cria_arquivo_vazio_proposicoes():
    """ Cria um arquivo vazio de proposicoes caso não exista
        no diretório local"""
    with open(path+"proposicoes.csv", "w", encoding='UTF8') as file:
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
    """ Checa se há arquivo de votos no diretório local"""
    try:
        with open(path+"votos.csv", "r") as arquivo:
            return arquivo
    except IOError:
        print("Não há arquivo de votos no diretório local.")
        return False


def cria_arquivo_vazio_votos():
    """ Cria um arquivo vazio de votos caso não exista no diretório local"""
    with open(path+"votos.csv", "w", encoding='UTF8') as file:
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
    """ Retorna uma lista com os códigos de todas as proposições que
        estão no arquivo local, no ano pesquisado"""

    prop_antigas = []
    with open(path+"proposicoes.csv", "r") as file:
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
    """ Função que busca o API da Câmara e retorna o XML
        de todas as votações de um determinado ano"""
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
    """Função que pega os dados extras de cada proposição,
        por meio de duas consultas diferentes"""
    prop = pega_dados_API_proposicao(prop)
    prop = pega_dados_API_votacoes(prop)
    return prop


def pega_dados_API_proposicao(prop):
    """Pega os dados da proposicao de acordo com a API de proposicoes"""
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
    """Pega os dados da proposicao de acordo com a API de proposicoes"""
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
        ano_votacao = votacao_["data"][-4:]
        #retira votações de outros anos
        if ano_votacao == proposicao["ano_votacao"]:
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
                #se for no 2o governo FHC, a orientação do govenro é a orientação do PSDB
                if ano_votacao in ["1999","2000","2001","2002"]:
                    #faz uma lista de um elemento com a orientação do PSDB (se houver)
                    orientacoes_PSDB = [votacao["orientacoes"][k] for k in votacao["orientacoes"].keys() if "PSDB" in k]
                    orientacao_governo = orientacoes_PSDB[0] if orientacoes_PSDB else "Não existe"
                else:
                    orientacao_governo = votacao["orientacoes"].get("GOV.", "Não existe")
                votacao["orientacao_governo"] = orientacao_governo
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
    """Gera um código único para cada votação"""
    return hashlib.md5((votacao["data_votacao"]+votacao["hora_votacao"]+votacao["resumo"]+codigo_proposicao).encode()).hexdigest()


def parse_data_votacao(votacao):
    """recupera a data da votação"""
    data = votacao["data_votacao"].split("/")
    data = data[2][2:4] + "%02d" % int(data[1]) + "%02d" % int(data[0])
    #cria código para a data e hora
    return data


def adiciona_novas_proposicoes(lista_proposicoes, prop_antigas, ano):
    """De acordo com a consulta na API, grava as novas proposicoes
        que não estiverem já listados no csv antigo"""
    contador = 0
    #prepara os dois arquivos de saída
    with open(path+"proposicoes.csv", "a", encoding='UTF8') as prop_saida,\
            open(path+"votos.csv", "a", encoding='UTF8') as voto_saida,\
            open(path+"orientacoes.csv","a",encoding='UTF8') as orientacao_saida:

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
    """obtem todas as proposições votadas em um determinado ano
        articulando as funções anteriores"""
    descompactar_arquivos()
    ano = str(ano)

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
    compactar_arquivos()


def acha_mandato(ano):
    if ano in [2003,2004,2005,2006]:
        return "lula1"
    elif ano in [2007,2008,2009,2010]:
        return "lula2"
    elif ano in [2011,2012,2013,2014]:
        return "dilma1"
    elif ano in [2015,2016,2017,2018]:
        return "dilma2"


def pega_deputados_atuais():
    """Pega a lista de deputados exercendo mandato atualmente"""
    url = "http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    deputados_atuais = [traduz_nome(deputado.findAll("nomeparlamentar")[0].string).decode('utf-8') for deputado in bs.findAll("deputado")]
    with open(path + "deputados_atuais.csv", 'w') as f:
        for dep in deputados_atuais:
            f.write(dep)
            f.write('\n')


def gera_json_basometro():
    descompactar_arquivos()
    saida = {'politicos':{},'votacoes':{},'votos':[]}

    politicos_nao_encontrados = set()
    votos_com_problema = set()
    politicos_atuais = []

    #Carregando lista de políticos atuais
    with open(path + "deputados_atuais.csv","r") as a:
        for line in a.readlines():
            politicos_atuais.append(line.rstrip('\n'))

    # Populando com a lista de políticos
    with open(path + 'deputados.csv', 'r') as p:
        reader = csv.DictReader(p, dialect='basometro')
        for row in reader:
            saida['politicos'][row['NOME_CASA']] = row
            if row['NOME_CASA'] in politicos_atuais:
                saida['politicos'][row['NOME_CASA']]['situacao'] = 'ativo'
            else:
                saida['politicos'][row['NOME_CASA']]['situacao'] = 'inativo'
            del saida['politicos'][row['NOME_CASA']]['NOME_CASA']

    #Populando com as votações
    with open(path + 'proposicoes.csv', 'r') as p:
        reader = csv.DictReader(p, dialect='basometro')
        for row in reader:
            saida['votacoes'][row['ID_VOTACAO']] = row
            del saida['votacoes'][row['ID_VOTACAO']]['ID_VOTACAO']

    #Populando Votos e verificando
    with open(path + 'votos.csv') as v:
        reader = csv.DictReader(v, dialect='basometro')
        for row in reader:
            if not saida['politicos'][row['POLITICO']]:
                politicos_nao_encontrados.add(row['POLITICO'])
            if row['VOTO'] not in TIPOS_DE_VOTOS:
                votos_com_problema.add(row)
            voto = [saida['politicos'][row['POLITICO']]['ID'],row['ID_VOTACAO'],row['PARTIDO'],TIPOS_DE_VOTOS[row['VOTO']]]
            saida['votos'].append(voto)

    if len(politicos_nao_encontrados) > 0:
        print("#############################################")
        print("Políticos não encontrados:")
        for pol in politicos_nao_encontrados:
            print(pol)

    if len(votos_com_problema) > 0:
        print("")
        print("#############################################")
        print("Votos com problemas")
        for voto in votos_com_problema:
            print(voto)

    with io.open(path + mandato + '_camara.json', 'w', encoding="utf8") as f:
        json.dump(saida, f, ensure_ascii=False)

    print("Geração de JSON termianda")

    compactar_arquivos()


def descompactar_arquivos():
    os.system("bunzip2 "+path+"*.bz2")


def compactar_arquivos():
    os.system("bzip2 -9 "+path+"*.csv "+path+"*.json")


#variaveis globais e chamada necessária
ano = 2015
mandato = acha_mandato(ano)
path = os.path.dirname(os.path.abspath(__file__))+'/'+mandato+"/"

#obter_proposicoes(ano)
#pega_deputados_atuais()
#gera_json_basometro()

#compactar_arquivos()
