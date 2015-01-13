#-*- coding: utf-8 -*-
#!/usr/bin/python3
from datetime import date, datetime, timedelta as td
from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv
import os
import json
import io

TIPOS_DE_VOTOS = {
        'NAO': 0,
        'SIM': 1,
        'ABSTENCAO': 2,
        'OBSTRUCAO': 3,
        'NAO VOTOU': 4,
        'PRESIDENTE': 5
    }

csv.register_dialect('basometro', delimiter=';', quoting=csv.QUOTE_NONNUMERIC)


def busca_novas_proposicoes(datas,prop_antigas):
    contador = 0
    #para cada data
    for d in datas:
        print("Procurando votações em: "+d)
        url = "http://legis.senado.gov.br/dadosabertos/plenario/lista/votacao/"+d
        bs = BeautifulSoup(urlopen(url).read())
        lista_votacoes = bs.findAll("votacao")
        num_votacoes = len(lista_votacoes)
        if num_votacoes > 0:
            print("Há "+str(num_votacoes)+ "votacoes")
        #para cada votação
        for v in lista_votacoes:
            try:
                #vê se há voto do líder do governo
                lista_votos = v.votos.findAll("votoparlamentar")
            except:
                print("Erro na votação!")
                print(url)
                continue
            voto_lider_governo = [l.voto.string for l in lista_votos if l.nomeparlamentar.string == lider_governo]
            #se houver
            if voto_lider_governo:
                codigo = v.codigosessaovotacao.string
                #vê se a votação já está no arquivo antigo. se não estiver, adicione os dados
                if codigo not in prop_antigas:
                    #se a votação não é secreta:
                    if v.secreta.string != 'S':
                        voto = {}
                        voto["codigo"] = codigo
                        voto["data"] = d[2:]
                        voto["hora"] = v.horainicio.string + ":00"
                        voto["orientacao_governo"] = traduz_voto(voto_lider_governo[0])
                        voto["tipo"] = v.siglamateria.string
                        voto["numero"] = v.numeromateria.string
                        voto["ano"] = v.anomateria.string
                        voto["ementa"] = consulta_ementa(v.codigomateria.string)
                        voto["o que foi votado"] = v.descricaovotacao.string.replace("\"","\'").strip()
                        voto["politicos"] = []
                        voto["votos"] = []
                        voto["partidos"] = []
                        for l in lista_votos:
                            voto["politicos"].append(l.nomeparlamentar.string)
                            voto["votos"].append(traduz_voto(l.voto.string))
                            voto["partidos"].append(l.siglapartido.string)

                        prop_antigas.append(codigo)

                        #escreve o resultado
                        escreveu = escreve_resultado(voto)
                        if escreveu:
                            contador = contador + 1
                            print("Prop adicionada!")

    print("Foram adicionadas "+str(contador)+" novas proposições ao arquivo.")


def traduz_voto(voto):
    voto = voto.strip()
    traducao = {
        "Presidente (art. 51 RISF)":"PRESIDENTE",
        "Sim - Presidente Art.48 inciso XXIII":"SIM",
        "Sim":"SIM",
        "Não":"NAO",
        "P-NRV":"NAO VOTOU",
        "LS":"NAO VOTOU",
        "NA":"NAO VOTOU",
        "LP":"NAO VOTOU",
        "AP":"NAO VOTOU",
        "LAP":"NAO VOTOU",
        "MIS":"NAO VOTOU",
        "NCom":"NAO VOTOU",
        "Obstrução":"OBSTRUCAO",
        "P-OD":"OBSTRUCAO",
        "PSF":"NAO VOTOU",
        "REP":"NAO VOTOU",
        "Abstenção":"NAO VOTOU"
    }

    if voto in traducao:
        return traducao[voto]
    else:
        return voto

def consulta_ementa(codigo):
    #a ementa na API do Senado está em um site diferente. por isso essa função é necessária
    url = "http://legis.senado.gov.br/dadosabertos/materia/"+codigo
    print(url)
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    materias = bs.findAll("materia")
    ementa = materias[0].ementa.string
    return ementa.strip()

def cria_lista_datas(data_inicio,data_fim):
    data_inicio = datetime.strptime(data_inicio, "%d%m%Y").date()
    data_fim = datetime.strptime(data_fim, "%d%m%Y").date()
    delta = data_fim - data_inicio
    datas = []
    for i in range(delta.days + 1):
        datas.append((data_inicio + td(days=i)).strftime("%Y%m%d"))
    return datas

def importa_proposicoes_antigas():
    prop_antigas = []
    try:
        with open(path+"senado_votacoes.csv","r") as file:
            arquivo = csv.reader(file, delimiter=";")
            next(arquivo, None)  # ignora o cabeçalho
            for row in arquivo:
                prop_antigas.append(row[0])
    except:
        pass

    return prop_antigas

def cria_arquivo_vazio():
    with open(path+"senado_votacoes.csv", "w", encoding='UTF8') as prop_saida,\
    open(path+"senado_votos.csv", "w", encoding='UTF8') as voto_saida:
        escreve_prop = csv.writer(
            prop_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC)

        escreve_voto = csv.writer(
            voto_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC)

        escreve_prop.writerow([
            "ID_VOTACAO",
            "DATA",
            "HORA",
            "ORIENTACAO_GOVERNO",
            "TIPO",
            "NUMERO",
            "ANO",
            "EMENTA",
            "O_QUE_FOI_VOTADO",
            "LINGUAGEM_COMUM"
            ])

        escreve_voto.writerow([
            "ID_VOTACAO",
            "POLITICO",
            "PARTIDO",
            "VOTO"
            ])

def escreve_resultado(v):
    escreveu = False
    with open(path+"senado_votacoes.csv", "a", encoding='UTF8') as prop_saida,\
    open(path+"senado_votos.csv", "a", encoding='UTF8') as voto_saida:
        escreve_prop = csv.writer(
            prop_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC)

        escreve_voto = csv.writer(
            voto_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC)

        if v["orientacao_governo"] in ["SIM","NAO"]:
            escreveu = True

            #escreve no arquivo de proposiçÕes
            escreve_prop.writerow([
                v["codigo"],
                v["data"],
                v["hora"],
                v["orientacao_governo"],
                v["tipo"],
                v["numero"],
                v["ano"],
                v["ementa"],
                v["o que foi votado"],
                ""
                ])

            #escreve no arquivo de votos
            for l in range(len(v["votos"])):
                escreve_voto.writerow([
                    v["codigo"],
                    v["politicos"][l],
                    v["partidos"][l],
                    v["votos"][l]
                    ])
    #diz se a votacao entrou ou não
    return escreveu

def atualiza_votacoes(data_inicio,data_fim):
    descompactar_arquivos()

    #cria lista com dias para se fazer a busca
    datas = cria_lista_datas(data_inicio, data_fim)

    #checa se há arquivo de votações. se não houver, cria
    prop_antigas = importa_proposicoes_antigas()
    if not prop_antigas:
        cria_arquivo_vazio()

    #busca as votações e escreve
    votacoes = busca_novas_proposicoes(datas,prop_antigas)
    compactar_arquivos()


def gera_json_basometro():
    descompactar_arquivos()
    saida = {'politicos':{},'votacoes':{},'votos':[]}

    politicos_nao_encontrados = set()
    votos_com_problema = set()

    # Populando com a lista de políticos
    with open(path + 'senadores.csv', 'r') as p:
        reader = csv.DictReader(p, dialect='basometro')
        for row in reader:
            saida['politicos'][row['NOME_CASA']] = row
            del saida['politicos'][row['NOME_CASA']]['NOME_CASA']

    #Populando com as votações
    with open(path + 'senado_votacoes.csv', 'r') as p:
        reader = csv.DictReader(p, dialect='basometro')
        for row in reader:
            saida['votacoes'][row['ID_VOTACAO']] = row
            del saida['votacoes'][row['ID_VOTACAO']]['ID_VOTACAO']

    #Populando Votos e verificando
    with open(path + 'senado_votos.csv') as v:
        reader = csv.DictReader(v, dialect='basometro')
        for row in reader:
            print(row)
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

    with io.open(path + mandato + '_senado.json', 'w', encoding="utf8") as f:
        json.dump(saida, f, ensure_ascii=False)

    print("Geração de JSON termianda")

    compactar_arquivos()


def descompactar_arquivos():
    os.system("bunzip2 "+path+"*.bz2")

def compactar_arquivos():
    os.system("bzip2 -9 "+path+"*.csv *.json")

path = os.path.dirname(os.path.abspath(__file__))+"/"
mandato = "dilma_1"
lider_governo = "Eduardo Braga" #"Ideli Salvatti" #LIDER DO GOVERNO
#atualiza_votacoes("01012011","31122014")
#compactar_arquivos()
gera_json_basometro()
