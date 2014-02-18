#-*- coding: utf-8 -*-
#!/usr/bin/python3

from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv


def busca_deputados_registrados():
    """Retorna uma lista com os códigos de todos os deputados
        que estão no arquivo local"""
    with open("deputados.csv", "r") as file:
        arquivo = csv.reader(file)
        arquivo.next()  # ignora o cabeçalho
        # a primeira coluna é a do ID
        dep_antigos = [row[0] for row in arquivo]
        print("Há " + str(len(dep_antigos)) + " deputados registrados \
              no arquivo salvo.")
        return dep_antigos


def consulta_API_deputados():
    """Consulta a API da Câmara para os deputados e retorna o XML \
        só com os campos de deputado"""
    url = "http://www.camara.gov.br/sitcamaraws/deputados.asmx/ObterDeputados"
    connection = urlopen(url)
    data = connection.read()
    bs = BeautifulSoup(data)
    return bs.findAll("deputado")


def salva_deputados(deputados):
    """De acordo com a consulta na API, grava os novos deputados que não \
        estiverem já listados no csv antigo"""
    #prepara o arquivo de saída
    contador = 0
    with open("deputados.csv", "a+") as arquivo:
        reader = csv.reader(arquivo)
        writer = csv.writer(arquivo,
                            delimiter=',',
                            quotechar='"',
                            quoting=csv.QUOTE_ALL)

        #Verificando de o arquivo já existe.
            # Se não existe, ele será automaticamente criado, daí basta
            # adicionarmos o "header" da primeira linha.
        arquivo.seek(0)  # garante que a leitura está no começo do arquivo
        primeiro_caractere = arquivo.readline()
        if not primeiro_caractere:
            # Escreve a primeira linha com o cabeçalho caso o
                # arquivo esteja vazio.
            writer.writerow(["id", "nome", "partido"])
        else:
            print("Arquivo de deputados no diretório local foi encontrado.")
            arquivo.seek(0)  # volta o leitor para o início do arquivo

        # gera uma lista com todos os ids constantes do arquivo
        lista_ids_salvos = [row[0] for row in reader]
        print("Há " + str(len(lista_ids_salvos)) + "\
              deputados registrados no arquivo salvo.")

        # iterando na lista de deputados enviada pela API
        for d in deputados:
            # se o id não estiver na lista atual, adicione uma nova
                # linha com os seus dados
            if d.idparlamentar.string not in lista_ids_salvos:
                writer.writerow([d.idparlamentar.string,
                                 d.nome.string,
                                 d.partido.string])
                contador += 1

    print("Foram adicionados " + str(contador) + "\
          deputados no arquivo local.")


def atualiza_deputados():
    """Função que articula todas as anteriores e faz todo o
        processo de atualização"""
    deputados = consulta_API_deputados()
    salva_deputados(deputados)


atualiza_deputados()
