#-*- coding: utf-8 -*-
#!/usr/bin/python3

# SOBRE ESTE ARQUIVO
# Este script está dividido em várias pequenas funções, que são depois coordenadas pela função principal obter_proposicoes(ano). O objetivo final dessa função é consultar a API da Câmara para criar dois arquivos no diretório local: o proposicoes.csv, com a lista de todas as proposições votadas no ano em questão com suas informações principais (data da votação, ementa, orientação do governo, etc), e o votos.csv, com a lista de como cada deputado votou em cada uma dessas votações. 

# Se os arquivos já existirem, a função checa se há registros no proposicoes.csv para o ano em que se está atualizando. Se houver, ela irá acrescentar apenas os registros que estão no site da Câmara mas não no arquivo local de proposições. Se não houver registros para esse ano, a função irá simplesmente adicionar todos que retornarem da API da Câmara como votados em plenário no ano em questão. Os votos de cada deputado serão acrescentados no arquivo votos.csv para toda votação que for acrescentada seguindo os critérios descritos acima.

from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv

#checa se há arquivo de proposicoes no diretório local. se houver, ele já retorna esse arquivo
def existe_arquivo_proposicoes():
    try: 
        with open("proposicoes.csv","r") as file: 
            arquivo = csv.reader(file)
            print("Arquivo de votações no diretório local foi encontrado.")
            return True
    except FileNotFoundError:
        print("Não há arquivo de votações no diretório local. Criando arquivo em branco...")
        return False

#cria um arquivo vazio de proposicoes caso não exista no diretório local
def cria_arquivo_vazio_proposicoes():
    with open("proposicoes.csv", "w", encoding='UTF8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["codigo","tipo","numero","ano","data_votacao","hora_votacao","ementa","resumo","orientacao_governo","num_votacoes"])

#checa se há arquivo de votos no diretório local 
def existe_arquivo_votos():
    try: 
        with open("votos.csv","r") as arquivo:
            print("Arquivo de votos no diretório local foi encontrado.")
            return True
    except FileNotFoundError:
        print("Não há arquivo de votos no diretório local. Criando arquivo em branco...")
        return False

#cria um arquivo vazio de votos caso não exista no diretório local
def cria_arquivo_vazio_votos():
    with open("votos.csv", "w", encoding='UTF8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["codigo_votacao","id_deputado","nome_deputado","partido","voto"])

#retorna uma lista com os códigos de todas as proposições que estão no arquivo local, no ano pesquisado
def busca_proposicoes_antigas(ano):
    prop_antigas = []
    with open("proposicoes.csv","r") as file:
        arquivo = csv.reader(file) 
        next(arquivo, None) #ignora o cabeçalho
        for row in arquivo:
            if row[4][-4:] == ano: #só adiciona na lista as do mesmo ano que está sendo atualizado
                prop_antigas.append(row[0]) #a primeira coluna é a do codigo
        print("Há "+str(len(prop_antigas))+" votações de "+str(ano)+" no arquivo salvo.")
        return prop_antigas

#função que busca o API da Câmara e retorna o XML de todas as votações de um determinado ano
def pega_todas_proposicoes(ano):
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano="+ano+"&tipo="
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    return bs.findAll("proposicao")

#função que pega os dados extras de cada proposição, por meio de duas consultas diferentes
def obter_dados_proposicao(prop):
    prop = pega_dados_API_proposicao(prop)
    prop = pega_dados_API_votacoes(prop)
    return prop

#pega os dados da proposicao de acordo com a API de proposicoes
def pega_dados_API_proposicao(prop):
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ObterProposicaoPorID?IdProp="+prop["codigo"]    
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    prop["tipo"] = bs.proposicao["tipo"].strip()
    prop["numero"] = bs.proposicao["numero"]
    prop["ano"] = bs.proposicao["ano"]
    ## pega apenas a nova ementa nas proposições em que ela tiver sido atualizada
    if "NOVA EMENTA:" in bs.ementa.string:
        ementa = bs.ementa.string.split("NOVA EMENTA:")
        prop["ementa"] = ementa[1].strip()
    else:
        prop["ementa"] = bs.ementa.string.strip()
    return prop

#pega os dados da proposicao de acordo com a API de proposicoes
def pega_dados_API_votacoes(prop):
    url = "http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo="+prop["tipo"]+"&numero="+prop["numero"]+"&ano="+prop["ano"]
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
        if v["data"][-4:] == prop["ano_votacao"]: #retira votações de outros anos
            prop["num_votacoes"] += 1
            prop["data_votacao"].append(v["data"])
            prop["hora_votacao"].append(v["hora"])
            prop["resumo"].append(v["resumo"].strip())
            
            try: #testa se há ou não há orientações para essa votação e pega esses dados
                sigla = [o["sigla"].strip() for o in v.orientacaobancada.findAll("bancada")]
                orientacao = [o["orientacao"].strip() for o in v.orientacaobancada.findAll("bancada")]
                orientacoes = dict(zip(sigla, orientacao))
                prop["orientacao_governo"].append(orientacoes.get("GOV.","Não existe"))
                prop["orientacoes"].append(orientacoes)
            except: 
                prop["orientacao_governo"].append("Não existe")
                        
            try: #testa e pega dados das votações  
                votos["idecadastro"] = [v["idecadastro"] for v in v.votos.findAll("deputado")]
                votos["nome"] = [v["nome"] for v in v.votos.findAll("deputado")]
                votos["voto"]= [v["voto"].strip() for v in v.votos.findAll("deputado")]
                votos["partido"] = [v["partido"].strip() for v in v.votos.findAll("deputado")]
                prop["votos"].append(votos)
            except:
                pass
    return prop
        
#de acordo com a consulta na API, grava as novas proposicoes que não estiverem já listados no csv antigo
def adiciona_novas_proposicoes(proposicoes,prop_antigas,ano):
    contador = 0
    prop = {}
    #prepara os dois arquivos de saída
    with open("proposicoes.csv", "a", encoding='UTF8') as prop_saida, open("votos.csv", "a", encoding='UTF8') as voto_saida:
        escreve_prop = csv.writer(prop_saida, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        escreve_voto = csv.writer(voto_saida, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        
        #loop que escreve as votações e os votos
        for p in proposicoes:
            
            #se o id não estiver na lista atual, adicione uma nova linha com os seus dados
            if p.codproposicao.string not in prop_antigas:
                prop["ano_votacao"] = ano
                prop["codigo"] = p.codproposicao.string
                prop = obter_dados_proposicao(prop)
                
                #loop para adicionar todas as votacoes no mesmo ano
                for i in range(prop["num_votacoes"]): 
                    contador += 1
                    escreve_prop.writerow([prop["codigo"],prop["tipo"],prop["numero"],prop["ano"],prop["data_votacao"][i-1],prop["hora_votacao"][i-1],prop["ementa"],prop["resumo"][i-1],prop["orientacao_governo"][i-1],  prop["num_votacoes"]])
                    
                    #loop para adicionar uma linha para cada deputado no arquivo de votos
                    try: 
                        for d in range(len(prop["votos"][i-1]["voto"])):
                            escreve_voto.writerow([prop["codigo"],prop["votos"][i-1]["idecadastro"][d],prop["votos"][i-1]["nome"][d],prop["votos"][i-1]["partido"][d],prop["votos"][i-1]["voto"][d]])
                    except:
                        pass   

    print("Foram adicionadas "+str(contador)+" votações no arquivo local.")

#obtem todas as proposições votadas em um determinado ano articulando as funções anteriores
def obter_proposicoes(ano):
    prop_antigas = []
    
    if existe_arquivo_proposicoes():
        prop_antigas = busca_proposicoes_antigas(ano)
    else:
        cria_arquivo_vazio_proposicoes()
    
    if not existe_arquivo_votos():
        cria_arquivo_vazio_votos()
    
    proposicoes = pega_todas_proposicoes(ano)
    adiciona_novas_proposicoes(proposicoes,prop_antigas,ano)

    
obter_proposicoes("2013")