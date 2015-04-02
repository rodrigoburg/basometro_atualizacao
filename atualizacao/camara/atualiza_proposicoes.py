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

import urllib.request
import hashlib
from urllib.request import urlopen
from bs4 import BeautifulSoup
import io
import unicodedata
import csv
from pandas import DataFrame, read_csv, Series
import os
import json
import math
import numpy as np

TIPOS_DE_VOTOS = {
        'NAO': 0,
        'SIM': 1,
        'ABSTENCAO': 2,
        'OBSTRUCAO': 3,
        'NAO VOTOU': 4,
        'PRESIDENTE': 5
    }

csv.register_dialect('basometro', delimiter=';', quoting=csv.QUOTE_NONNUMERIC)

def media_melhor(vetor):
    soma = 0.0
    tamanho = 0.0
    if (len(vetor) < 1):
        return None
    for i in vetor:
        if ( i != None ):
            soma += i
            tamanho += 1
    if ( soma == 0 and tamanho == 0):
        return None
    return(soma/tamanho)


def traduz_nome(txt):
    #remove acentos
    norm = unicodedata.normalize('NFKD', txt)

    #remove espaços extras
    saida = norm.strip()

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

def calcula_rice(vetor):
    if ( len(vetor) <= 1 ):
        return(0)
    n_one = 0
    n_zero = 0
    for i in vetor: # Calcula o numero de 1 e 0
        if i == 0:
            n_zero += 1
        elif i == 1:
            n_one += 1
        else:
            continue
    if ( n_one == 0 and n_zero == 0 ):
        return(0)
    rice = (n_one - n_zero)/(n_one + n_zero)
    return(abs(rice))


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
    deputados_atuais = [traduz_nome(deputado.findAll("nomeparlamentar")[0].string) for deputado in bs.findAll("deputado")]
    with open(path + "deputados_atuais.csv", 'w') as f:
        for dep in deputados_atuais:
            f.write(dep)
            f.write('\n')


def gera_json_basometro():
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


def descompactar_arquivos():
    os.system("bunzip2 "+path+"*.bz2")


def compactar_arquivos():
    os.system("bzip2 -9 "+path+"*.csv")


def pega_arquivos():
    props = []
    votos = []
    path = os.path.dirname(os.path.abspath(__file__))
    with open(path+"/atualizacao/camara/proposicoes.csv", "r") as prop, open(path+"/atualizacao/camara/votos.csv", "r") as voto:

        arquivo_prop = csv.reader(prop,delimiter = ";")
        next(arquivo_prop, None)  # ignora o cabeçalho
        for row in arquivo_prop:
            proposicao = {}
            proposicao["codigo"] = row[0]
            proposicao["data"] = row[1]
            proposicao["hora"] = row[2]
            proposicao["orientacao"] = row[3]
            proposicao["tipo"] = row[4]
            proposicao["numero"] = row[5]
            proposicao["ano"] = row[6]
            proposicao["ementa"] = row[7]
            proposicao["resumo"] = row[8]
            props.append(proposicao)

        arquivo_voto = csv.reader(voto,delimiter = ";")
        next(arquivo_voto, None)  # ignora o cabeçalho
        for row in arquivo_voto:
            este_voto = {}
            este_voto["codigo"] = row[0]
            este_voto["politico"] = row[1]
            este_voto["voto"] = row[2]
            este_voto["partido"] = row[3]
            votos.append(este_voto)
    return props,votos

def media(lista):
    return sum(lista) / float(len(lista))



def calcula_governismo(props,df_votos):
    #transforma DataFrame em lista de dicionários
    df_props = props.T.to_dict().values()

    resultado = []
    aux_variancia = []
    aux_rice = []
    num_votos = 0
    aux_deputados = []

    #para cada proposição dos dicionários
    for p in df_props:
        #subset do DataFrame de votos para aquela proposição
        subvotos = df_votos[df_votos["ID_VOTACAO"] == p["ID_VOTACAO"]]
        #subset do DataFrame de votos que são iguais à orientação do governo
        subvotos["ORIENTACAO_GOVERNO"] = p["ORIENTACAO_GOVERNO"].upper()
        try:
            subvotos["RESULTADO"] = subvotos.apply(lambda t:0 if t["VOTO"] != t["ORIENTACAO_GOVERNO"] else 1,axis=1)
        except ValueError:
            pass

        try:
            #faz a média da coluna resultado e passa isso para uma lista
            resultado.append(np.average(list(subvotos["RESULTADO"])))
            aux_variancia.append(np.var(list(subvotos["RESULTADO"])))
            aux_rice.append(calcula_rice(list(subvotos["RESULTADO"])))
            aux_deputados.append(len(subvotos))
            num_votos += len(subvotos)
        except KeyError:
            pass

    try:
        #faz a média do resultado, achando assim o governismo
        governismo = media(resultado)
        variancia = media_melhor(aux_variancia)
        num_deputados = media(aux_deputados)
        rice = media_melhor(aux_rice)
        return governismo, num_votos, variancia, num_deputados,rice

    except ZeroDivisionError:
        return None

def calcula_deputados(props,votos):
    df_votos = DataFrame(votos)
    df_props = DataFrame(props)
    lista_deputados = []
    for v in votos:
        lista_deputados.append(v["politico"])

    lista_deputados = list(set(lista_deputados))

    deputados = {}

    for d in lista_deputados:
        vota_junto = 0
        vota_contra = 0
        subvotos = df_votos[df_votos["politico"] == d]
        for v in list(subvotos["codigo"]):
            voto = subvotos[subvotos["codigo"] == v]["voto"].get_values()[0]
            orientacao = df_props[df_props["codigo"] == v]["orientacao"].get_values()[0]
            if voto.lower() == orientacao.lower():
                vota_junto += 1
            else:
                vota_contra += 1
        deputados[d] = {}
        deputados[d]["vota_junto"] = vota_junto
        deputados[d]["voto_total"] = vota_junto + vota_contra

    mais_de_90 = 0
    entre_50_e_90 = 0
    menos_de_50 = 0

    for d in deputados.keys():
        deputado = deputados[d]
        governismo = deputado["vota_junto"]/deputado["voto_total"]
        if governismo > 0.9:
            mais_de_90 += 1
        elif governismo > 0.5:
            entre_50_e_90 += 1
        else:
            menos_de_50 +=1

    #print("Número total de deputados: "+str(len(lista_deputados)))
    #print("% que votou + de 90% com o governo: "+str(mais_de_90*100/len(lista_deputados)))
    #print("% que votou entre 50% e 90% com o governo: "+str(entre_50_e_90*100/len(lista_deputados)))
    #print("% que votou menos de 50% com o governo: "+str(menos_de_50*100/len(lista_deputados)))


def conserta_voto(voto):
    voto = voto.upper()
    traducao = {
        "Sim":"SIM",
        "Não":"NAO",
        "OBSTRUÇÃO":"NAO",
        "OBSTRUCAO":"NAO",
        "NÃO":"NAO"
    }
    if voto in traducao:
        return traducao[voto]
    else:
        return voto

def acha_meses(datas):
    meses = list(set([d[0:4] for d in datas]))
    meses.sort()
    return meses

def calcula_historico():

    #pega arquivo de proposições e conserta maiúsculas/minúsculas/acento
    props = read_csv(mandato+"/proposicoes.csv",sep=";")
    props["ORIENTACAO_GOVERNO"] = props["ORIENTACAO_GOVERNO"].apply(conserta_voto)

    #transforma as datas em string e coloca zero na frente dos anos que perderam esse zero
    props["DATA"] = props["DATA"].apply(lambda d: "%06d" % d)

    #agora pega arquivo de orientações e faz parecido
    oris = read_csv(mandato+"/orientacoes.csv",sep=";")

    #acha lista de combinações ano/mês
    datas = list(set(list(props["DATA"])))
    meses = acha_meses(datas)

    #pega arquivo de votos e retira abstenções e presidente
    votos = read_csv(mandato+"/votos.csv",sep=";")
    votos = votos[votos.VOTO != 'ABSTENCAO']
    votos = votos[votos.VOTO != 'PRESIDENTE']
    votos['VOTO'] = votos['VOTO'].apply(conserta_voto)

    partidos = set(list(votos["PARTIDO"]))

    #declara viaráveis para saída do histórico e saída do gráfico de varianca
    aux_saida = {}

    proposicoes_por_mes = [["data","quantidade"]]

    #agora faz os cálculos para o total dos deputaods, sem filtrar por partido
    aux_saida["Geral"] = {}
    for mes in meses:
        props_temp = props
        props_temp["FILTRO"] = props_temp["DATA"].apply(lambda t: str(t).startswith(mes))
        props_temp = props_temp[props_temp.FILTRO == True]
        #se houver proposição neste período
        item = {}
        item["date"] = "20"+mes[0:2]+"-"+mes[2:4]+"-01"
        item["valor"] = -1
        item["num_votacoes"] = 0
        if len(props_temp) > 0:
            governismo = calcula_governismo(props_temp,votos)
            if (governismo):
                item["valor"] = int(round(governismo[0]*100,0))
                item["num_votacoes"] = governismo[1]
                item["variancia"] = governismo[2]
                item["num_deputados"] = governismo[3]
                item["rice"] = governismo[4]
        aux_saida["Geral"][mes] = item

        #"cálculo" do número de proposições existentes em cada mês
        proposicoes_por_mes.append([item["date"], len(props_temp)])

    #calcula o governismo e a variancia para cada partido
    for partido in partidos:
        aux_saida[partido] = {}
        temp = votos[votos.PARTIDO == partido]
        for mes in meses:
            #cria variável temporária de proposicoes, onde a data começa com o ano/mes da lista
            props_temp = props
            props_temp["FILTRO"] = props_temp["DATA"].apply(lambda t: str(t).startswith(mes))
            props_temp = props_temp[props_temp.FILTRO == True]

            item = {}
            item["date"] = "20"+mes[0:2]+"-"+mes[2:4]+"-01"
            item["valor"] = -1
            item["num_votacoes"] = 0
            #se houver proposição neste período
            if len(props_temp) > 0:
                governismo = calcula_governismo(props_temp,temp)
                #se houver governismo para esse partido, ou seja, algum voto
                if (governismo):
                    item["valor"] = int(round(governismo[0]*100))
                    item["num_votacoes"] = governismo[1]
                    item["variancia"] = int(round(governismo[2]*100))
                    item["num_deputados"] = int(round(governismo[3]))
                    item["rice"] = int(governismo[4]*100)

            aux_saida[partido][mes] = item

    saida = {}

    #Cálculo da média móvel
    #Para cada partido faça....
    for partido in aux_saida:
        if partido != "S.Part.":
            saida[partido] = []
            #Para cada mês da lista de meses faça...
            for mes in meses:
                indice = meses.index(mes) #Pega o índice do mês na lista
                item = {}
                #Se for o primeiro item da lista, só copia os valores
                #Salva a data no dicionário final
                item["date"] = aux_saida[partido][mes]["date"]
                #arruma as datas da década de 1990
                if item["date"][2] == "9":
                    item["date"] = "19" + item["date"][2:]
                #Inicializa um contador de "meses iterados"
                contador = 0
                soma_movel = 0
                variancia_movel = 0
                num_deputados_movel = 0
                rice_movel = 0
                total_local_votacoes = 0
                while contador < 6 and (indice - contador >= 0): #2 porque quero pegar os últimos 6 meses
                    #se existir governismo e variancia para esse partido nesse período...
                    if aux_saida[partido][meses[indice - contador]]["valor"] > 0:
                        soma_movel += aux_saida[partido][meses[indice - contador]]["valor"] * aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                        variancia_movel += aux_saida[partido][meses[indice - contador]]["variancia"] * aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                        rice_movel += aux_saida[partido][meses[indice - contador]]["rice"] * aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                        num_deputados_movel += aux_saida[partido][meses[indice - contador]]["num_deputados"] * aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                        total_local_votacoes += aux_saida[partido][meses[indice - contador]]["num_votacoes"]
                    contador+=1

                #Se o total_local_de_votacoes for maior que zero, ou seja, se tem votação considerada...
                if total_local_votacoes > 0:
                    item["valor"] = int(round((soma_movel / total_local_votacoes),0))
                    item["variancia"] = int(round((variancia_movel / total_local_votacoes),0))
                    item["num_deputados"] = int(round((num_deputados_movel / total_local_votacoes),0))
                    item["rice"] = int(round((rice_movel / total_local_votacoes),0))
                else:
                    item["valor"] = -1
                #print(partido,total_local_votacoes,soma_movel,aux_saida[partido][mes]["valor"], item["valor"])

                saida[partido].append(item)

    #escreve Json de saída
    with open (mandato+"/hist_"+mandato[:-1]+"_camara_"+mandato[-1]+".json","w",encoding='UTF8') as jsonfile:
        jsonfile.write(json.dumps(saida))
    print("Histórico do mandato " + mandato + " salvo")

    #agora fazemos a saída para o gráfico da variância
    aux_variancia = []
    for sigla in saida:
        if sigla != "Geral":
            item = {}
            item["name"] = sigla
            variancia = []
            governismo = []
            num_deputados = []
            rice = []
            for i in saida[sigla]:
                if "variancia" in i:
                    data = i["date"]
                    variancia.append([data, i["variancia"]])
                    governismo.append([data, i["valor"]])
                    num_deputados.append([data,i["num_deputados"]])
                    rice.append([data, i["rice"]])
            item["dispersao"] = variancia
            item["governismo"] = governismo
            item["num_deputados"] = num_deputados
            item["rice"] = rice
            aux_variancia.append(item)

    with open (mandato+"/variancia_"+mandato+"_camara.json","w",encoding='UTF8') as jsonfile:
        jsonfile.write(json.dumps(aux_variancia))
    print("JSON da variância do mandato " + mandato + " salvo")



def cruza_votacao(votos,partido):
    siglas = set(votos["PARTIDO"])

    temp = votos[votos.PARTIDO == partido]

    #se não estiver vazio
    if not temp.empty:
        votacao = {}
        #acha qual é o voto que a maior parte do partido em questão votou
        voto_maioria_partido = list(temp.groupby("VOTO").agg({"POLITICO":Series.nunique}).sort("POLITICO",ascending=0).index)[0]

        #acha qual é o padrão de votacao desse partido
        votos_contra = len(temp.index[temp.VOTO != voto_maioria_partido])
        votos_pro = len(temp.index[temp.VOTO == voto_maioria_partido])

        #agora calcula o mesmo padrão pra cada partido
        for s in siglas:
            temp = votos[votos.PARTIDO == s]
            votos_contra = len(temp.index[temp.VOTO != voto_maioria_partido])
            votos_pro = len(temp.index[temp.VOTO == voto_maioria_partido])
            votacao[s] = {"favor": votos_pro, "contra": votos_contra}

        return votacao

    #se estiver vazio, volta vazio
    return {}

#            total_votos = len(temp.index)
#            votos_pro = len(temp.index[temp.VOTO == voto_maioria_partido])
#            taxa_partido = votos_pro/total_votos

def adiciona_votacao(votacao,votacoes,partido):
    #se não existir esse partido no arquivo de votacoes, adicione
    if partido not in votacoes:
        votacoes[partido] = {}

    #para cada sigla existente na última votação
    for sigla in votacao:

        #se não existir essa sigla, adicione os votos a favor e contra
        if sigla not in votacoes[partido]:
            votacoes[partido][sigla] = {"favor":0,"contra":0}

        votacoes[partido][sigla]["favor"] = votacoes[partido][sigla]["favor"] + votacao[sigla]["favor"]
        votacoes[partido][sigla]["contra"] = votacoes[partido][sigla]["contra"] + votacao[sigla]["contra"]

    return votacoes

def calcula_semelhanca(votacoes):
    semelhanca = {}
    #para cada partido
    for partido in votacoes:
        semelhanca[partido] = {}
        #o padrão é o numero de votos a favor dividido pelo total de votos
        taxa_padrao = votacoes[partido][partido]["favor"] / (votacoes[partido][partido]["favor"] + votacoes[partido][partido]["contra"])
        for sigla in votacoes[partido]:
            #agora achamos a taxa da sigla, para depois compararmos ela com a padrão
            taxa_sigla = votacoes[partido][sigla]["favor"] / (votacoes[partido][sigla]["favor"] + votacoes[partido][sigla]["contra"])
            #a semelhança é uma regra de três da taxa da sigla com a taxa padrão, como se a padrão fosse 100% de semelhança
            semelhanca[partido][sigla] = math.fabs((taxa_sigla * 100 / taxa_padrao) - 100)

    return semelhanca


def matriz_semelhanca(mandato):
    #pega diretório do script para abrir os arquivos de votos e proposições
    path = os.path.dirname(os.path.abspath(__file__))

    #pega arquivo de votos e retira abstenções, obstruções e presidente
    votos = read_csv(path+"/atualizacao/camara/"+mandato+"/votos.csv.bz2",sep=";",compression = 'bz2')
    votos = votos[votos.VOTO != 'ABSTENCAO']
    votos = votos[votos.VOTO != 'OBSTRUCAO']
    votos = votos[votos.VOTO != 'PRESIDENTE']

    #cria um dicionário com o formato d[partido][outro_partido]["favor"] e ["contra"], em que contamos os votos desse outro_partido a favor ou contra o que a maioria do partido original decidiu
    votacoes = {}

    #para cada votacao
    for v in set(votos["ID_VOTACAO"]):
        temp = votos[votos.ID_VOTACAO == v]
        siglas = set(temp["PARTIDO"])
        #para cada sigla que participou dessa votacao
        for s in siglas:
            votacao = cruza_votacao(temp,s)
            if votacao:
                votacoes = adiciona_votacao(votacao,votacoes,s)

    #agora calculamos a semelhanca
    semelhanca = calcula_semelhanca(votacoes)

    saida = DataFrame.from_dict(semelhanca)
    saida.to_csv(path+"/matriz_semelhanca.csv")

def saida_indice_rice(mandato):
    props = read_csv(mandato+"/proposicoes.csv",sep=";")
    props = props.head(24) #só as 23 primeiras, para ficar igual à quantidade de votacoes de dilma2
    props["ORIENTACAO_GOVERNO"] = props["ORIENTACAO_GOVERNO"].apply(conserta_voto)

    #pega arquivo de votos e retira abstenções e presidente
    votos = read_csv(mandato+"/votos.csv",sep=";")
    votos = votos[votos.VOTO != 'ABSTENCAO']
    votos = votos[votos.VOTO != 'PRESIDENTE']

    #aqui corta as 23 primeiras também
    votacoes = list(props.ID_VOTACAO)
    votos = votos[votos.ID_VOTACAO.isin(votacoes)]
    votos['VOTO'] = votos['VOTO'].apply(conserta_voto)

    votos["ORIENTACAO_GOVERNO"] = votos.apply(lambda t:list(props[props.ID_VOTACAO == t["ID_VOTACAO"]]["ORIENTACAO_GOVERNO"])[0],axis=1)
    votos["RICE"] = votos.apply(lambda t:0 if t["ORIENTACAO_GOVERNO"] != t["VOTO"] else 1,axis=1)
    votos.to_csv("rice_"+mandato+".csv",index=False)

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

def limpar_votos():

    votos = read_csv(mandato+"/votos.csv",sep=";", dtype=object)
    props = read_csv(mandato+"/proposicoes.csv",sep=";",dtype=object)

    #arruma nome dos deputados, partidos e votos
    votos["POLITICO"] = votos["POLITICO"].apply(traduz_nome)
    votos["VOTO"] = votos["VOTO"].apply(traduz_voto)
    votos["PARTIDO"] = votos["PARTIDO"].apply(traduz_partido)

    #se tiver a votação do senado no meio da Câmara, retira
    votos = votos[votos.ID_VOTACAO != "dd36cd4acaa5bf214f0e107c5ab0ec57"]
    props = props[props.ID_VOTACAO != "dd36cd4acaa5bf214f0e107c5ab0ec57"]


    #arruma o nome
    votos.to_csv(mandato+"/votos.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)
    props.to_csv(mandato+"/proposicoes.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

def checa_deputado():
    votos = read_csv(mandato+"/votos.csv",sep=";")
    try:
        politicos = read_csv(mandato+"/deputados.csv",sep=";")
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

    print("ERRO EM: "+str(len(lista_politicos))+" POLÍTICOS")

    print(partido.keys())
    if (lista_politicos):
        adiciona_deputados(lista_politicos,politicos,partido)

def adiciona_deputados(lista_deputados,politicos,partido):
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

    url2 = "file://"+path.replace(mandato+"/","")+"Deputados.xml"
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
                deputado["URL_FOTO"] = ""

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
            print("Erro no deputado: "+d)
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

    politicos.to_csv(mandato+"/deputados.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

def checa_proposicoes():
    votos = read_csv(mandato+"/votos.csv",sep=";")
    props = read_csv(mandato+"/proposicoes.csv",sep=";")
    for p in list(props["ID_VOTACAO"]):
        if not (p in list(votos["ID_VOTACAO"])):
            print("Essa votação está no arquivo de votações mas não no de votos")
            print(p)

    #for p in list(votos["ID_VOTACAO"]):
    #    if not (p in list(props["ID_VOTACAO"])):
    #        print("hue")

def deputados_hoje():
#    url = "http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    url = "file://"+path+"/Deputados.xml"
    dados = BeautifulSoup(urlopen(url).read())
    deputados = dados.findAll("deputado")
    print(len(deputados))
    gabinetes = []
    for d in deputados:
        print(d)
        gab = d.gabinete.string
        if gab not in gabinetes:
            gabinetes.append(gab)
        else:
            print(gab)
            if gab:
                print("Gabinete repetido! "+gab)
    print(gabinetes)
    print(len(gabinetes))

def baixa_fotos():
    #ATENCAO: código pode ser usado tanto para baixar as fotos antigas de um governo que já estejam no arquivo de deputados quanto para baixar
    #fotos de deputados novos acrescentados na checagem de deputados rotineira. Comente a parte do código que você não for usar

    #cria diretório paras as fotos, se não houver
    if not os.path.isdir(mandato+"/fotos"):
        print("Criando diretório para as fotos")
        os.system("mkdir "+mandato+"/fotos")

    politicos = read_csv(mandato+"/deputados.csv",sep=";",dtype={'ID': 'str',"ANO_MANDATO":'str',"LEGISLATURA":'str'})

    #pega fotos antigas
    '''politicos.loc[politicos.URL_FOTO.isnull(),"URL_FOTO"] = "sem_foto.jpg"
    politicos["ID"] = politicos["ID"].apply(str)
    links = Series(politicos.URL_FOTO.values,index=politicos.ID).to_dict()
    for codigo in links:
        if links[codigo] != "sem_foto.jpg":
            try:
                urllib.request.urlretrieve(links[codigo], path+"/"+mandato+"/fotos/dep_"+codigo+".jpg")
                politicos.loc[politicos.ID == codigo,"URL_FOTO"] = "dep_"+codigo+".jpg"
                print(links[codigo])
            except (urllib.error.HTTPError):
                politicos.loc[politicos.ID == codigo,"URL_FOTO"] = "sem_foto.jpg"'''


    #pega fotos novas
    deps_sem_foto = politicos[politicos.URL_FOTO.isnull()]
    deps_sem_foto = list(deps_sem_foto["NOME_CASA"])
    #url = "file://"+path+"/Deputados.xml"
    url = "http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    dados = BeautifulSoup(urlopen(url).read())
    deputados = dados.findAll("deputado")
    for d in deputados:
        dep_sem_acento = traduz_nome(d.nomeparlamentar.string)
        if dep_sem_acento in deps_sem_foto:
            codigo = str(list(politicos[politicos.NOME_CASA == dep_sem_acento]["ID"])[0])
            try:
                urllib.request.urlretrieve(d.urlfoto.string, path+"/"+mandato+"/fotos/dep_"+codigo+".jpg")
                politicos.loc[politicos.NOME_CASA == dep_sem_acento,"URL_FOTO"] = "dep_"+codigo+".jpg"
                print(d.urlfoto.string)
            except: #se não achar foto
                print("falta_foto: "+dep_sem_acento)
                continue

    politicos.loc[politicos.URL_FOTO.isnull(),"URL_FOTO"] = "sem_foto.jpg"
    politicos.to_csv(path+"/deputados.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

def junta_variancia():
    mandatos = ["lula1","lula2","dilma1","dilma2"]
    variaveis = ["governismo","dispersao","num_deputados","rice"]
    partidos = {}
    for m in mandatos:
        with open(m+'/variancia_'+m+'_camara.json') as json_data:
            temp = json.load(json_data)
            for partido in temp:
                sigla = partido["name"]
                if sigla not in partidos:
                    partidos[sigla] = {}
                    for var in variaveis:
                        partidos[sigla][var] = []

                for var in variaveis:
                    partidos[sigla][var] += (partido[var])

    saida = []
    for p in partidos:
        item = {}
        item["name"] = p
        for var in variaveis:
            item[var] = partidos[p][var]

        saida.append(item)

    with open ("variancia_camara.json","w",encoding='UTF8') as jsonfile:
        jsonfile.write(json.dumps(saida))
    print("JSON da variância total salvo")

path = os.path.dirname(os.path.abspath(__file__))

#variaveis globais e chamada necessária
ano = 2004
mandato = acha_mandato(ano)
path = os.path.dirname(os.path.abspath(__file__))+'/'+mandato+"/"

#ATUALIZA O BASOMETRO
#
descompactar_arquivos()
#obter_proposicoes(ano)

#CHECA OS DEPUTADOS
#
#limpar_votos()
#checa_proposicoes()
#checa_deputado()
#baixa_fotos()
#print("AGORA NÃO SE ESQUEÇA DE COLOCAR A EXPLICAÇÃO PARA AS VOTAÇÕES")

#GERA SAÍDA E COMPACTA
#
#pega_deputados_atuais()
#gera_json_basometro()

#calcula_historico()
junta_variancia()

compactar_arquivos()

#OUTROS COMANDOS
#
#saida_indice_rice(mandato)
