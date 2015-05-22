#-*- coding: utf-8 -*-
#!/usr/bin/python3
from datetime import date, datetime, timedelta as td
import csv
import os
import json
import io
import unicodedata
from pandas import DataFrame, read_csv
from unicodedata import normalize
from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import os
import csv

TIPOS_DE_VOTOS = {
        'NAO': 0,
        'SIM': 1,
        'ABSTENCAO': 2,
        'OBSTRUCAO': 3,
        'NAO VOTOU': 4,
        'PRESIDENTE': 5
    }

csv.register_dialect('basometro', delimiter=';', quoting=csv.QUOTE_NONNUMERIC)

def traduz_partido(part):
    partidos = {
            'SD': 'SDD',
            'S/PARTIDO': 'S.Part.',
            "S/Partido": 'S.Part.'
            }
    if part in partidos:
        return partidos[part]
    else:
        return part

def traduz_nome(txt):
    #remove acentos
    norm = unicodedata.normalize('NFKD', txt)
    saida = norm.encode('ASCII','ignore')

    #remove espaços extras
    saida = saida.strip()

    #muda nomes errados
    traducao = {
        "Assis Gurgacz":"Acir Gurgacz",
        "assis gurgacz":"acir gurgacz",
    }

    if saida in traducao:
        return traducao[saida]
    else:
        return saida

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
            print(url)
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
                        voto["orientacao_governo"] = voto_lider_governo[0]
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
                            voto["partidos"].append(traduz_partido(l.siglapartido.string))

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
        "Abstenção":"ABSTENCAO"
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
    try:
        ementa = materias[0].ementa.string
    except AttributeError:
        ementa = materias[0].ementamateria.string

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
            quoting=csv.QUOTE_ALL)

        escreve_voto = csv.writer(
            voto_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)

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

        if v["orientacao_governo"] in ["Sim","Não"]:
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

    #cria lista com dias para se fazer a busca
    datas = cria_lista_datas(data_inicio, data_fim)

    #checa se há arquivo de votações. se não houver, cria
    prop_antigas = importa_proposicoes_antigas()
    if not prop_antigas:
        cria_arquivo_vazio()

    #busca as votações e escreve
    busca_novas_proposicoes(datas,prop_antigas)


def gera_json_basometro():
    saida = {'politicos':{},'votacoes':{},'votos':[]}

    politicos_nao_encontrados = set()
    votos_com_problema = set()

    # Pegando senados em exercício
    url = "http://www.senado.leg.br/senadores/"
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    politicos_atuais = [traduz_nome(item.string).decode('utf-8').lower() for item in bs.find_all("td","colNomeSenador")]

    # Populando com a lista de políticos
    with open(path + 'senadores.csv') as p:
        reader = csv.DictReader(p, dialect='basometro')
        for row in reader:
            pol = traduz_nome(row['NOME_CASA']).decode('utf-8')
            saida['politicos'][pol] = row
            if pol.lower() in politicos_atuais:
                saida['politicos'][pol]['situacao'] = 'ativo'
            else:
                saida['politicos'][pol]['situacao'] = 'inativo'
            del saida['politicos'][pol]['NOME_CASA']

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
            pol = traduz_nome(row['POLITICO']).decode('utf-8')
            if pol not in saida['politicos']:
                print(row['POLITICO'])
                politicos_nao_encontrados.add(pol)
            else:
                if row['VOTO'] not in TIPOS_DE_VOTOS:
                    votos_com_problema.add(row)
                else:
                    voto = [saida['politicos'][pol]['ID'],row['ID_VOTACAO'],row['PARTIDO'],TIPOS_DE_VOTOS[row['VOTO']]]
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
    votos = read_csv(path+"senado_votos.csv",sep=";")
    votos["POLITICO"] = votos["POLITICO"].apply(remover_acentos)
    votos["PARTIDO"] = votos["PARTIDO"].apply(traduz_partido)
    votos.to_csv(path+"senado_votos.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)

def testa_voto():
    votos = read_csv(path+"senado_votos.csv",sep=";")
    try:
        politicos = read_csv(path+"/senadores.csv",sep=";")
    except OSError: #se não houver arquivo de senadores, cria um DF vazio
        colunas = ['POLITICO', 'NOME_CASA','PARTIDO',"UF",'ID',"ANO_MANDATO","LEGISLATURA","URL_FOTO"]
        politicos = DataFrame(columns=colunas)

    lista_politicos = []

    for p in votos["POLITICO"]:
        if p not in list(politicos["NOME_CASA"]):
            lista_politicos.append(p)

    lista_politicos = list(set(lista_politicos))
    print("Estão faltando "+str(len(lista_politicos)) + " senadores no arquivo de políticos.")
    print(lista_politicos)

    if len(lista_politicos) > 0:
        acha_senador(lista_politicos,politicos)


def acha_senador(senadores,politicos):
    for l in legislaturas:
        url = "http://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/"+l
        bs = BeautifulSoup(urlopen(url).read())
        lista_senadores = bs.findAll("parlamentar")
        for sen in lista_senadores:
            nome = remover_acentos(sen.nomeparlamentar.string)
            if nome in senadores:
                senador = {}
                senador['POLITICO'] = nome
                senador['NOME_CASA'] = nome
                senador['PARTIDO'] = sen.siglapartido.string
                senador['UF'] = sen.siglauf.string
                senador['ID'] = sen.codigoparlamentar.string
                senador['ANO_MANDATO'] = "--"
                senador['LEGISLATURA'] = sen.legislaturainicio.string + "/" + sen.legislaturafim.string
                senador['URL_FOTO'] = ""
                politicos = politicos.append(senador,ignore_index=True)
                print("Adicionado político: "+nome)
    politicos.to_csv(path+"senadores.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)


def descompactar_arquivos():
    os.system("bunzip2 "+path+"*.bz2")

def compactar_arquivos():
    os.system("bzip2 -9 "+path+"*.csv "+path+"*.json")

def baixa_fotos():
    #cria diretório paras as fotos, se não houver
    if not os.path.isdir(path+"fotos"):
        print("Criando diretório para as fotos")
        os.system("mkdir "+path)
        os.system("mkdir "+path+"fotos")

    politicos = read_csv(path+"senadores.csv",sep=";")
    sen_sem_foto = politicos[politicos.URL_FOTO.isnull()]
    sen_sem_foto = list(sen_sem_foto["NOME_CASA"])
    sen_com_foto = []

    for l in legislaturas:
        url = "http://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/"+l
        bs = BeautifulSoup(urlopen(url).read())
        senadores = bs.findAll("parlamentar")

        for s in senadores:
            nome = remover_acentos(s.nomeparlamentar.string)
            if nome in sen_sem_foto:
                if nome not in sen_com_foto:
                    codigo = str(list(politicos[politicos.NOME_CASA == nome]["ID"])[0])
                    try:
                        urllib.request.urlretrieve(s.urlfotoparlamentar.string, path+"fotos/sen_"+codigo+".jpg")
                        politicos.loc[politicos.NOME_CASA == nome,"URL_FOTO"] = "sen_" + codigo+".jpg"
                        sen_com_foto.append(nome)
                    except urllib.error.HTTPError:
                        pass

                print(s.urlfotoparlamentar.string)
                #politicos.loc[politicos.POLITICO == dep_sem_acento]["URL_FOTO"] = d.urlfoto.string
    #    politicos["ANO_MANDATO"] = politicos["ANO_MANDATO"].apply(int)
    #    politicos["LEGISLATURA"] = politicos["LEGISLATURA"].apply(int)
    politicos.loc[politicos.URL_FOTO.isnull(),"URL_FOTO"] = "sem_foto.jpg"
    politicos.to_csv(path+"senadores.csv",sep=";",index=False, quoting=csv.QUOTE_ALL)


def descompactar_arquivos():
    os.system("bunzip2 "+path+"*.bz2")


def compactar_arquivos():
    os.system("bzip2 -9 "+path+"*.csv")

legislaturas = ["54","55","56"]

mandato = "dilma2"
path = os.path.dirname(os.path.abspath(__file__))+'/'+mandato+"/"
lider_governo = "Delcídio do Amaral" #"Eduardo Braga" #"Ideli Salvatti" #LIDER DO GOVERNO

descompactar_arquivos()
#atualiza_votacoes("01012015","30052015")

#limpar_votos()
#testa_voto()
#baixa_fotos()
#print("NAO ESQUECA DE DSCREVER AS VOTACOES")

gera_json_basometro()
compactar_arquivos()

