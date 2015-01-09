#-*- coding: utf-8 -*-
#!/usr/bin/python3
from datetime import date, datetime, timedelta as td
from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv
import os

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
        "Sim":"SIM",
        "Não":"NAO",
        "P-NRV":"NAO VOTOU",
        "LS":"NAO VOTOU",
        "LP":"NAO VOTOU",
        "AP":"NAO VOTOU",
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
            quoting=csv.QUOTE_ALL)

        escreve_voto = csv.writer(
            voto_saida,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_ALL)
    
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
    

def descompactar_arquivos():
    os.system("bzip2 -d "+path+"*")

def compactar_arquivos():
    os.system("bzip2 -z "+path+"*.csv")    

path = os.path.dirname(os.path.abspath(__file__))+"/"
lider_governo = "Eduardo Braga" #"Ideli Salvatti" #LIDER DO GOVERNO
atualiza_votacoes("01012011","31122014")
#descompactar_arquivos()
    
