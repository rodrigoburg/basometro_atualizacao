#-*- coding: utf-8 -*-
#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv

def importa_proposicoes_antigas():
    with open("proposicoes_senado.csv","r") as file:
        prop_antigas = []
        arquivo = csv.reader(file, delimiter=";")
        next(arquivo, None)  # ignora o cabeçalho
        for row in arquivo:
            prop_antigas.append(row[0])
        return prop_antigas
        
def busca_proposicoes_novas():
    votacoes = {}
    days = [str('%02d' % d) for d in range(1,32)]
    months = [str('%02d' % m) for m in range(2,5)]

    for m in months:
        print("Procurando votações no mês: "+m)
        for d in days:
            url = "http://legis.senado.gov.br/dadosabertos/plenario/lista/votacao/2014"+m+d
    
            connection = urlopen(url)
            data = connection.read()
            bs = BeautifulSoup(data)
            lista_votacoes = bs.findAll("votacao")                    
            
            for v in lista_votacoes:
                
                lista_votos = v.votos.findAll("votoparlamentar")
                voto_lider_governo = [l.voto.string for l in lista_votos if l.nomeparlamentar.string == "Eduardo Braga"]
                if voto_lider_governo:
                    votacoes[v.codigosessaovotacao.string] = {}
                    votacoes[v.codigosessaovotacao.string]["data"] = "14"+m+d
                    votacoes[v.codigosessaovotacao.string]["hora"] = v.horainicio.string + ":00"
                    votacoes[v.codigosessaovotacao.string]["orientacao_governo"] = voto_lider_governo[0]
                    votacoes[v.codigosessaovotacao.string]["tipo"] = v.siglamateria.string
                    votacoes[v.codigosessaovotacao.string]["numero"] = v.numeromateria.string
                    votacoes[v.codigosessaovotacao.string]["ano"] = v.anomateria.string
                    votacoes[v.codigosessaovotacao.string]["ementa"],votacoes[v.codigosessaovotacao.string]["explicacao"] = consulta_ementa(v.codigomateria.string)
                    votacoes[v.codigosessaovotacao.string]["o que foi votado"] = v.descricaovotacao.string.replace("\"","\'")
                    votacoes[v.codigosessaovotacao.string]["politicos"] = []
                    votacoes[v.codigosessaovotacao.string]["votos"] = []
                    votacoes[v.codigosessaovotacao.string]["partidos"] = []
                    for l in lista_votos:
                        votacoes[v.codigosessaovotacao.string]["politicos"].append(l.nomeparlamentar.string)
                        votacoes[v.codigosessaovotacao.string]["votos"].append(l.voto.string)
                        votacoes[v.codigosessaovotacao.string]["partidos"].append(l.siglapartido.string)                     
    
    return votacoes

def consulta_ementa(codigo):
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

def escreve_votacoes():
    with open("senado_votacoes_novo.csv", "w", encoding='UTF8') as prop_saida,\
    open("senado_votos_novo.csv", "w", encoding='UTF8') as voto_saida:
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
                    
        votacoes = busca_proposicoes_novas()
        escreve_prop.writerow([
            "id_votacao",
            "data",
            "hora",
            "orientacao_governo",
            "tipo",
            "numero",
            "ano",
            "ementa",
            "o que foi votado",
            "explicacao"
            ])
        
        escreve_voto.writerow([
            "ID_VOTACAO",
            "POLITICO",
            "PARTIDO",
            "VOTO"
            ])
        
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

escreve_votacoes()