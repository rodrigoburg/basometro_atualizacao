#-*- coding: utf-8 -*-
#!/usr/bin/python3
from datetime import date, datetime, timedelta as td
from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv

def busca_novas_proposicoes(datas,prop_antigas):
    votacoes = {}
    #para cada data
    for d in datas:
        print("Procurando votações em: "+d)
        url = "http://legis.senado.gov.br/dadosabertos/plenario/lista/votacao/"+d
        bs = BeautifulSoup(urlopen(url).read())
        lista_votacoes = bs.findAll("votacao")                    
        #para cada votação
        for v in lista_votacoes:
            #vê se há voto do líder do governo
            lista_votos = v.votos.findAll("votoparlamentar")
            voto_lider_governo = [l.voto.string for l in lista_votos if l.nomeparlamentar.string == "Eduardo Braga"]
            #se houver
            if voto_lider_governo:
                codigo = v.codigosessaovotacao.string
                #vê se a votação já está no arquivo antigo. se não estiver, adicione os dados
                if codigo not in prop_antigas:
                    votacoes[codigo] = {}
                    votacoes[codigo]["data"] = d[2:]
                    votacoes[codigo]["hora"] = v.horainicio.string + ":00"
                    votacoes[codigo]["orientacao_governo"] = voto_lider_governo[0]
                    votacoes[codigo]["tipo"] = v.siglamateria.string
                    votacoes[codigo]["numero"] = v.numeromateria.string
                    votacoes[codigo]["ano"] = v.anomateria.string
                    votacoes[codigo]["ementa"],votacoes[codigo]["explicacao"] = consulta_ementa(v.codigomateria.string)
                    votacoes[codigo]["o que foi votado"] = v.descricaovotacao.string.replace("\"","\'")
                    votacoes[codigo]["politicos"] = []
                    votacoes[codigo]["votos"] = []
                    votacoes[codigo]["partidos"] = []
                    for l in lista_votos:
                        votacoes[codigo]["politicos"].append(l.nomeparlamentar.string)
                        votacoes[codigo]["votos"].append(traduz_voto(l.voto.string))
                        votacoes[codigo]["partidos"].append(l.siglapartido.string)

                    prop_antigas.append(codigo)                    

    return votacoes

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
    try: 
        explicacao = materias[0].explicacaoementa.string
    except:
        explicacao = ""
    return ementa, explicacao 

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
        with open("senado_votacoes.csv","r") as file:
            arquivo = csv.reader(file, delimiter=";")
            next(arquivo, None)  # ignora o cabeçalho
            for row in arquivo:
                prop_antigas.append(row[0])
    except: 
        pass
    
    return prop_antigas

def cria_arquivo_vazio():
    with open("senado_votacoes.csv", "w", encoding='UTF8') as prop_saida,\
    open("senado_votos.csv", "w", encoding='UTF8') as voto_saida:
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
            "explicacao"
            ])
        
        escreve_voto.writerow([
            "ID_VOTACAO",
            "POLITICO",
            "PARTIDO",
            "VOTO"
            ])
            
def escreve_resultado(votacoes):
    with open("senado_votacoes.csv", "a", encoding='UTF8') as prop_saida,\
    open("senado_votos.csv", "a", encoding='UTF8') as voto_saida:
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
    
        contador = 0
        for key in votacoes:
            v = votacoes[key]
            if v["orientacao_governo"] in ["Sim","Não"]:
                contador = contador + 1
            
                #escreve no arquivo de proposiçÕes
                escreve_prop.writerow([
                    key,
                    v["data"],
                    v["hora"],
                    v["orientacao_governo"],
                    v["tipo"],
                    v["numero"],
                    v["ano"],
                    v["ementa"],
                    v["o que foi votado"],
                    v["explicacao"]
                    ])
            
                #escreve no arquivo de votos
                for l in range(len(v["votos"])):
                    escreve_voto.writerow([
                        key,
                        v["politicos"][l],
                        v["partidos"][l],
                        v["votos"][l]
                        ])
            
        print("Foram adicionadas "+str(contador)+" votações para o período selecionado")                                        
    
def atualiza_votacoes(data_inicio,data_fim):

    #cria lista com dias para se fazer a busca
    datas = cria_lista_datas(data_inicio, data_fim)
        
    #checa se há arquivo de votações. se não houver, cria
    prop_antigas = importa_proposicoes_antigas()
    if not prop_antigas:
        cria_arquivo_vazio()   

    #busca as votações
    votacoes = busca_novas_proposicoes(datas,prop_antigas)
    
    #escreve o resultado
    escreve_resultado(votacoes)


atualiza_votacoes("08022011","10072014")
    
