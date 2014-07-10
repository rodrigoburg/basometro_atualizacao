from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv

#importa a atual lista de deputados, checa se há algum deputado novo pelo ID e salva os novos no mesmo arquivo .csv se houver
def atualiza_deputados():
    #verifica se já há o arquivo de deputados local. se houver, pega o arquivo local de deputados e guarda a primeira coluna (id) em uma lista
    try: 
        mycsv = csv.reader(open("deputados.csv","r"))
        dep_antigos = []
        next(mycsv, None) #ignora o cabeçalho
        for row in mycsv:
            dep_antigos.append(row[0])
                
    except FileNotFoundError: #se o arquivo não existir, cria um zerado só com o cabeçalho
        output  = open("deputados.csv", "w", encoding='UTF8')
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(["id","nome","partido"])
        output.close()
        dep_antigos = []
    
    #agora faz a consulta na API da Câmara pela lista atual de deputados       
    url = "http://www.camara.gov.br/sitcamaraws/deputados.asmx/ObterDeputados"
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    deputados = bs.findAll("deputado")
                    
    #prepara o arquivo de saída
    output  = open("deputados.csv", "a", encoding='UTF8')
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    
    #se o id não estiver na lista atual, adicione uma nova linha com os seus dados
    for d in deputados:
        if d.idparlamentar.string not in dep_antigos:
            writer.writerow([d.idparlamentar.string,d.nome.string,d.partido.string])
    output.close()

atualiza_deputados()
